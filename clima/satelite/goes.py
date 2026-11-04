"""Acceso mínimo a GOES-19 (ABI y GLM) en el archivo abierto de NOAA en AWS.

- Sin clave. La raíz del bucket va en la variable de entorno CLIMA_GOES_S3
  (privado/fuentes.env); aquí no se escribe ningún endpoint.
- Lee los netCDF4/HDF5 **por rangos HTTP**: solo baja los bloques que necesita
  (metadatos y los trozos del recorte). No guarda archivos completos.
- Dependencias: numpy y h5py.
"""
from __future__ import annotations

import http.client
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import h5py
import numpy as np

AQUI = Path(__file__).resolve().parent
UA = "sosgalapagos-clima-satelite/0.1"

# Producto -> prefijo en el bucket. CMIP de la banda 13 (10,3 µm, «ventana limpia»).
PRODUCTOS = {
    "c13": ("ABI-L2-CMIPF", r"-M\dC13_"),  # cualquier modo de barrido (M3, M4, M6)
    "rrqpe": ("ABI-L2-RRQPEF", ""),
    "glm": ("GLM-L2-LCFA", ""),
}

RE_INICIO = re.compile(r"_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})(\d)")


def raiz_bucket() -> str:
    raiz = os.environ.get("CLIMA_GOES_S3", "").rstrip("/")
    if not raiz:
        # Para correr a mano desde clima/: lee privado/fuentes.env si existe.
        env = AQUI.parent / "privado" / "fuentes.env"
        if env.exists():
            for linea in env.read_text().splitlines():
                if linea.startswith("CLIMA_GOES_S3="):
                    raiz = linea.split("=", 1)[1].strip().rstrip("/")
    if not raiz:
        raise SystemExit("Falta CLIMA_GOES_S3 (ver clima/fuentes.env.ejemplo)")
    return raiz


def inicio_de(nombre: str) -> datetime:
    """Hora de inicio del barrido (UTC) a partir del nombre del archivo."""
    m = RE_INICIO.search(nombre)
    a, d, h, mi, s, _ = (int(x) for x in m.groups())
    return datetime(a, 1, 1, h, mi, s, tzinfo=timezone.utc) + timedelta(days=d - 1)


_CONEXIONES: dict[str, http.client.HTTPSConnection] = {}


TIMEOUT_S = 15


def _http(url: str, rango: tuple[int, int] | None = None, intentos: int = 3) -> bytes:
    """GET con conexión persistente por host (una por proceso; no compartir entre hilos)."""
    u = urllib.parse.urlsplit(url)
    ruta = u.path + (f"?{u.query}" if u.query else "")
    cab = {"User-Agent": UA}
    if rango:
        cab["Range"] = f"bytes={rango[0]}-{rango[1]}"
    for i in range(intentos):
        con = _CONEXIONES.get(u.netloc)
        if con is None:
            con = _CONEXIONES[u.netloc] = http.client.HTTPSConnection(u.netloc, timeout=TIMEOUT_S)
        try:
            con.request("GET", ruta, headers=cab)
            r = con.getresponse()
            datos = r.read()
            if r.status in (200, 206):
                return datos
            if r.status in (403, 404):
                raise FileNotFoundError(f"HTTP {r.status} {u.path}")
            raise ConnectionError(f"HTTP {r.status}")
        except FileNotFoundError:
            raise
        except (OSError, http.client.HTTPException) as e:
            con.close()
            _CONEXIONES.pop(u.netloc, None)
            if i == intentos - 1:
                raise ConnectionError(f"{u.path}: {e}") from e
            time.sleep(1.0 * (i + 1))
    raise RuntimeError("inalcanzable")


SUBIDO: dict[str, datetime] = {}  # clave -> hora de subida al bucket (LastModified), para la latencia


def listar(producto: str, hora: datetime) -> list[tuple[str, int]]:
    """Archivos (clave, tamaño) de un producto para una hora UTC. Anota la hora de subida en SUBIDO."""
    prefijo, filtro = PRODUCTOS[producto]
    pref = f"{prefijo}/{hora:%Y}/{hora.timetuple().tm_yday:03d}/{hora:%H}/"
    raiz = raiz_bucket()
    salida, token = [], None
    ns = "{*}"  # cualquier espacio de nombres XML
    while True:
        q = {"list-type": "2", "prefix": pref}
        if token:
            q["continuation-token"] = token
        xml = ET.fromstring(_http(f"{raiz}/?{urllib.parse.urlencode(q)}"))
        for c in xml.findall(f"{ns}Contents"):
            clave = c.find(f"{ns}Key").text
            if filtro and not re.search(filtro, clave):
                continue
            salida.append((clave, int(c.find(f"{ns}Size").text)))
            lm = c.find(f"{ns}LastModified")
            if lm is not None:
                SUBIDO[clave] = datetime.fromisoformat(lm.text.replace("Z", "+00:00"))
        t = xml.find(f"{ns}NextContinuationToken")
        if t is None:
            break
        token = t.text
    return sorted(salida)


class ArchivoRemoto:
    """Objeto tipo archivo de solo lectura sobre HTTP con rangos y caché por bloques.

    h5py lo acepta como archivo (driver «fileobj»). Cuenta los bytes bajados.
    """

    def __init__(self, url: str, tamano: int, bloque: int = 256 * 1024):
        self.url, self.tamano, self.bloque = url, tamano, bloque
        self.pos = 0
        self.cache: dict[int, bytes] = {}
        self.bajado = 0
        self.peticiones = 0

    def _bloques(self, ini: int, fin: int) -> None:
        faltan = [b for b in range(ini // self.bloque, fin // self.bloque + 1) if b not in self.cache]
        # agrupa bloques consecutivos en una sola petición
        while faltan:
            a = b = faltan.pop(0)
            while faltan and faltan[0] == b + 1:
                b = faltan.pop(0)
            r0, r1 = a * self.bloque, min((b + 1) * self.bloque, self.tamano) - 1
            datos = _http(self.url, (r0, r1))
            self.bajado += len(datos)
            self.peticiones += 1
            for k in range(a, b + 1):
                o = (k - a) * self.bloque
                self.cache[k] = datos[o:o + self.bloque]

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.tamano - self.pos
        n = max(0, min(n, self.tamano - self.pos))
        if n == 0:
            return b""
        ini, fin = self.pos, self.pos + n - 1
        self._bloques(ini, fin)
        partes = []
        for k in range(ini // self.bloque, fin // self.bloque + 1):
            b0 = k * self.bloque
            partes.append(self.cache[k][max(ini - b0, 0): fin - b0 + 1])
        self.pos += n
        return b"".join(partes)

    def readinto(self, buf) -> int:
        datos = self.read(len(buf))
        buf[: len(datos)] = datos
        return len(datos)

    def seek(self, off: int, whence: int = 0) -> int:
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.tamano + off)
        return self.pos

    def tell(self) -> int:
        return self.pos

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True


def abrir(clave: str, tamano: int, bloque: int = 256 * 1024) -> tuple[h5py.File, ArchivoRemoto]:
    fo = ArchivoRemoto(f"{raiz_bucket()}/{clave}", tamano, bloque)
    return h5py.File(fo, "r"), fo


# ---------------------------------------------------------------- proyección ABI

def _proy(f: h5py.File) -> dict:
    p = f["goes_imager_projection"].attrs
    return {
        "h": float(p["perspective_point_height"][0]) + float(p["semi_major_axis"][0]),
        "req": float(p["semi_major_axis"][0]),
        "rpol": float(p["semi_minor_axis"][0]),
        "lon0": math.radians(float(p["longitude_of_projection_origin"][0])),
    }


def latlon_a_xy(lat, lon, pr: dict):
    """Lat/lon (grados) -> ángulos de barrido x, y (radianes) del ABI (GOES-R PUG §4.2.8)."""
    lat, lon = np.radians(lat), np.radians(lon)
    req, rpol, H = pr["req"], pr["rpol"], pr["h"]
    e2 = 1 - rpol**2 / req**2
    phic = np.arctan((rpol**2 / req**2) * np.tan(lat))
    rc = rpol / np.sqrt(1 - e2 * np.cos(phic) ** 2)
    sx = H - rc * np.cos(phic) * np.cos(lon - pr["lon0"])
    sy = -rc * np.cos(phic) * np.sin(lon - pr["lon0"])
    sz = rc * np.sin(phic)
    x = np.arcsin(-sy / np.sqrt(sx**2 + sy**2 + sz**2))
    y = np.arctan(sz / sx)
    return x, y


def xy_a_latlon(x, y, pr: dict):
    """Ángulos de barrido -> lat/lon (grados)."""
    req, rpol, H = pr["req"], pr["rpol"], pr["h"]
    a = np.sin(x) ** 2 + np.cos(x) ** 2 * (np.cos(y) ** 2 + (req**2 / rpol**2) * np.sin(y) ** 2)
    b = -2 * H * np.cos(x) * np.cos(y)
    c = H**2 - req**2
    rs = (-b - np.sqrt(b**2 - 4 * a * c)) / (2 * a)
    sx = rs * np.cos(x) * np.cos(y)
    sy = -rs * np.sin(x)
    sz = rs * np.cos(x) * np.sin(y)
    lat = np.arctan((req**2 / rpol**2) * (sz / np.sqrt((H - sx) ** 2 + sy**2)))
    lon = pr["lon0"] - np.arctan(sy / (H - sx))
    return np.degrees(lat), np.degrees(lon)


def _escala(var) -> tuple[float, float]:
    a = var.attrs
    return float(a.get("scale_factor", [1.0])[0]), float(a.get("add_offset", [0.0])[0])


def _sin_signo(var, crudo: np.ndarray) -> np.ndarray:
    """Los netCDF de GOES guardan enteros sin signo como int con _Unsigned="true"."""
    u = var.attrs.get("_Unsigned")
    if u is not None and (u.decode() if isinstance(u, bytes) else str(u)).lower() == "true" \
            and crudo.dtype.kind == "i":
        return crudo.view(crudo.dtype.str.replace("i", "u"))
    return crudo


def _fisico(var, crudo: np.ndarray) -> np.ndarray:
    """Entero crudo -> valor físico (float64), con NaN en el _FillValue."""
    fill = var.attrs.get("_FillValue")
    s, o = _escala(var)
    datos = _sin_signo(var, crudo).astype("float64") * s + o
    if fill is not None:
        datos[crudo == np.asarray(fill).astype(crudo.dtype)[0]] = np.nan
    return datos


def ventana(f: h5py.File, bbox: list[float], margen: int = 1) -> dict:
    """Índices de fila/columna que cubren un bbox [lon0, lat0, lon1, lat1]."""
    pr = _proy(f)
    lons = np.array([bbox[0], bbox[2], bbox[0], bbox[2]])
    lats = np.array([bbox[1], bbox[1], bbox[3], bbox[3]])
    x, y = latlon_a_xy(lats, lons, pr)
    sxs, oxs = _escala(f["x"])
    sys_, oys = _escala(f["y"])
    cols = (x - oxs) / sxs
    filas = (y - oys) / sys_
    c0, c1 = int(math.floor(cols.min())) - margen, int(math.ceil(cols.max())) + margen
    r0, r1 = int(math.floor(filas.min())) - margen, int(math.ceil(filas.max())) + margen
    return {"r0": r0, "r1": r1 + 1, "c0": c0, "c1": c1 + 1, "pr": pr,
            "sx": sxs, "ox": oxs, "sy": sys_, "oy": oys}


def recorte(f: h5py.File, var: str, v: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Recorte de una variable 2D en unidades físicas, con lat/lon de cada píxel."""
    d = f[var]
    datos = _fisico(d, d[v["r0"]:v["r1"], v["c0"]:v["c1"]]).astype("float32")
    cols = np.arange(v["c0"], v["c1"])
    filas = np.arange(v["r0"], v["r1"])
    X, Y = np.meshgrid(cols * v["sx"] + v["ox"], filas * v["sy"] + v["oy"])
    lat, lon = xy_a_latlon(X, Y, v["pr"])
    return datos, lat, lon


def leer_abi(producto: str, clave: str, tamano: int, bbox: list[float]) -> dict:
    """Recorte de CMIP C13 (Tb, K) o RRQPE (mm/h) sobre un bbox amplio."""
    var = {"c13": "CMI", "rrqpe": "RRQPE"}[producto]
    f, fo = abrir(clave, tamano, bloque=128 * 1024)
    try:
        v = ventana(f, bbox)
        datos, lat, lon = recorte(f, var, v)
        dqf = None
        if "DQF" in f:
            dqf = f["DQF"][v["r0"]:v["r1"], v["c0"]:v["c1"]].astype("int16")
            datos = np.where(dqf_valido(producto, dqf), datos, np.nan).astype("float32")
        lon_sat = math.degrees(v["pr"]["lon0"])
    finally:
        f.close()
    return {"datos": datos, "lat": lat, "lon": lon, "dqf": dqf, "lon_sat": lon_sat,
            "inicio": inicio_de(clave), "bytes": fo.bajado, "peticiones": fo.peticiones}


def dqf_valido(producto: str, dqf: np.ndarray) -> np.ndarray:
    """Banda 13: 0 bueno, 1 utilizable con reservas; 2–4 y relleno, no.
    RRQPE (máscara de bits): 0 bueno y 2 (degradado por ángulo o latitud) valen; 1 y 4–64 son inválidos."""
    dqf = dqf.astype("int16")
    if producto == "c13":
        return (dqf == 0) | (dqf == 1)
    return (dqf != 255) & ((dqf & (1 | 4 | 8 | 16 | 32 | 64)) == 0)


# ---------------------------------------------------------------- paralaje

LON_SAT_GOES19 = -75.2
R_TIERRA_KM = 6371.0
H_SAT_KM = 35786.0


def altura_tope_km(tb: np.ndarray) -> np.ndarray:
    """Altura aproximada del tope a partir de su Tb: (300 K − Tb) / 6,5 K/km, entre 0 y 16 km.
    Es una aproximación (221 K ≈ 12 km; 200 K ≈ 15 km), suficiente para corregir el paralaje."""
    return np.clip((300.0 - np.asarray(tb, dtype="float64")) / 6.5, 0.0, 16.0)


def corregir_paralaje(lat, lon, h_km, lon_sat: float = LON_SAT_GOES19):
    """Posición real (bajo la nube) de un píxel visto en (lat, lon) con un tope a h_km de altura.

    Desde un satélite geoestacionario, un tope alto se ve desplazado en sentido contrario al punto
    subsatelital. En Galápagos (ángulo cenital ~18°), un tope de 14 km se ve ~4,5 km al oeste de su sitio.
    Tierra esférica: el error es despreciable para este desplazamiento.
    """
    la, lo = np.radians(lat), np.radians(lon)
    h = np.nan_to_num(np.asarray(h_km, dtype="float64"), nan=0.0)
    R = R_TIERRA_KM
    P = np.stack([R * np.cos(la) * np.cos(lo), R * np.cos(la) * np.sin(lo), R * np.sin(la)])
    ls = math.radians(lon_sat)
    S = np.array([(R + H_SAT_KM) * math.cos(ls), (R + H_SAT_KM) * math.sin(ls), 0.0]).reshape(3, *([1] * la.ndim))
    n = P / R
    u = S - P
    u = u / np.linalg.norm(u, axis=0)
    t = h / np.sum(u * n, axis=0)          # distancia por la línea de visión hasta la altura h
    C = P + t * u                           # tope de la nube (en 3D)
    G = C / np.linalg.norm(C, axis=0) * R   # punto de la superficie bajo el tope
    lat2 = np.degrees(np.arcsin(G[2] / R))
    lon2 = np.degrees(np.arctan2(G[1], G[0]))
    return lat2, lon2


def bajar(clave: str) -> bytes:
    """Archivo completo en memoria (para los GLM, de ~300 KB). Seguro en hilos: conexión nueva."""
    with urllib.request.urlopen(urllib.request.Request(f"{raiz_bucket()}/{clave}",
                                                       headers={"User-Agent": UA}), timeout=TIMEOUT_S) as r:
        return r.read()


def leer_glm(clave: str, tamano: int, bbox: list[float] | None = None, datos: bytes | None = None) -> dict:
    """Destellos (flashes) del GLM: lat, lon, hora (UTC) y energía. Filtra por bbox si se da.

    Sin `datos`, lee por rangos (bloques de 2 KB: ~55 KB de ~320 KB); con `datos`, desde memoria.
    """
    if datos is not None:
        import io
        fo = ArchivoRemoto.__new__(ArchivoRemoto)
        fo.bajado, fo.peticiones = len(datos), 1
        f = h5py.File(io.BytesIO(datos), "r")
    else:
        f, fo = abrir(clave, tamano, bloque=2048)
    try:
        lat = _fisico(f["flash_lat"], f["flash_lat"][:])
        lon = _fisico(f["flash_lon"], f["flash_lon"][:])
        t = f["flash_time_offset_of_first_event"]
        dt = _fisico(t, t[:])
        e = f["flash_energy"]
        ene = _fisico(e, e[:])
        q = f["flash_quality_flag"][:] if "flash_quality_flag" in f else np.zeros(lat.shape, "int16")
        t0 = f["product_time"][()]
        base = datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(seconds=float(t0))
    finally:
        f.close()
    buenos = q == 0  # solo destellos de calidad buena (flash_quality_flag = 0)
    lat, lon, dt, ene = lat[buenos], lon[buenos], dt[buenos], ene[buenos]
    if bbox is not None and lat.size:
        m = (lon >= bbox[0]) & (lon <= bbox[2]) & (lat >= bbox[1]) & (lat <= bbox[3])
        lat, lon, dt, ene = lat[m], lon[m], dt[m], ene[m]
    return {"lat": lat, "lon": lon, "dt": dt, "energia": ene, "base": base,
            "inicio": inicio_de(clave), "bytes": fo.bajado, "peticiones": fo.peticiones}


def zonas() -> dict:
    """Zonas de vigilancia: clima/recolector/zonas_geo.json."""
    return json.loads((AQUI.parent / "recolector" / "zonas_geo.json").read_text())["zonas"]
