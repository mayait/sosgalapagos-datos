"""Animaciones 3D para video (reels 9:16 y YouTube 16:9) sobre las inundaciones del 30-oct-2026 en Galápagos.

Motor: PyVista/VTK fuera de pantalla (GPU), terreno Copernicus GLO-30 (y, en Santa Cruz, el DTM de 1 m de la SGIAR como relieve
de detalle: fuente «santa-cruz-dtm»; «santa-cruz-cop» es el DSM puro para comparar) con textura hipsométrica, edificios 3D y capas
rasterizadas, mar con leve oleaje animado, cámara por fotogramas clave con suavizado (easing) y ffmpeg (H.264).
Sin texto incrustado: los rótulos se ponen en edición. Para las animaciones con hora se escribe una pista CSV
por fotograma y una capa de reloj con alfa (ProRes 4444) aparte.

Uso, desde geodatos/:
  .venv/bin/python -I scripts/31_animaciones_video.py --lista
  .venv/bin/python -I scripts/31_animaciones_video.py sc_sobrevuelo_cuenca [otra …]
  .venv/bin/python -I scripts/31_animaciones_video.py sc_llenado_cascada_sur --prueba   # 6 fotogramas sueltos a baja resolución
  .venv/bin/python -I scripts/31_animaciones_video.py sc_vaso_dtm --formato 4k-ambos --crf 15   # 3840×2160 y 2160×3840
  Opciones: --formato 16x9|9x16|4k|4k9x16|4k-ambos (por defecto 16x9 y 9x16), --salida DIR, --crf N,
            --prores (ProRes 422 HQ .mov de 10 bits, para edición), --fps N (30 por defecto).
  Las del DTM (sc_dtm_revela, sc_vaso_dtm, sc_30oct_dtm) necesitan datos/dtm_sgiar/ y la máscara de mar de 03_dem.py.
  Al usarlas, cite «DTM 1 m: SGIAR (Vricon/Maxar)». Los edificios 3D tienen una altura ilustrativa de 3,5 m.

Salida: ~/Desktop/SOS_Galapagos_videos/animaciones/<isla>/<nombre>_<formato>.mp4 (o .mov) + <nombre>_<formato>.png (portada), <nombre>_pista.csv y, si aplica, <nombre>_reloj.mov.
"""
import argparse, csv, datetime as dt, json, math, os, pathlib, subprocess, sys, time
import numpy as np, rasterio
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy.ndimage import zoom, distance_transform_edt, gaussian_filter, map_coordinates, label as ndi_label
from scipy.interpolate import PchipInterpolator
from shapely.geometry import shape, box, Point, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union, transform as stransform
from pyproj import Transformer
from PIL import Image, ImageDraw, ImageFont
import pyvista as pv
import shapely

pv.OFF_SCREEN = True
ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIMA = ROOT.parent / "clima"
SALIDA = pathlib.Path.home() / "Desktop/SOS_Galapagos_videos/animaciones"
LC = ROOT / "estudios/la-cascada/datos"; SCZ = ROOT / "estudios/santa-cruz/datos"; SCB = ROOT / "estudios/san-cristobal/datos"
FPS = 30
ISLAS = {"santa-cruz": dict(epsg=32715, dem=ROOT / "descargas/dem_recortes/santa_cruz_dem.tif", nombre="Santa Cruz"),
         "san-cristobal": dict(epsg=32716, dem=ROOT / "descargas/dem_recortes/san_cristobal_dem.tif", nombre="San Cristóbal"),
         # archipelago completo (mapa de situación): mosaico de teselas GLO-30 remuestreado a ≈140 m (descargas/dem_situacion/)
         "galapagos-15": dict(epsg=32715, dem=ROOT / "descargas/dem_situacion/mosaico_galapagos_140m.tif", nombre="Galápagos", res=150),
         "galapagos-16": dict(epsg=32716, dem=ROOT / "descargas/dem_situacion/mosaico_galapagos_140m.tif", nombre="Galápagos", res=150)}


def mosaico_situacion():
    from rasterio.merge import merge
    dest = ISLAS["galapagos-15"]["dem"]
    if dest.exists(): return dest
    fs = [rasterio.open(p) for p in sorted(dest.parent.glob("Copernicus_DSM_COG_10_*_DEM.tif"))]
    arr, tr = merge(fs, res=(1 / 800, 1 / 800), resampling=Resampling.average, nodata=-9999)
    with rasterio.open(dest, "w", driver="GTiff", height=arr.shape[1], width=arr.shape[2], count=1, dtype="float32", crs="EPSG:4326",
                       transform=tr, nodata=-9999, compress="deflate") as d:
        d.write(np.where((arr[0] < -100) | (arr[0] > 2000), -9999, arr[0]).astype("float32"), 1)
    return dest
FORMATOS = {"16x9": (1920, 1080), "9x16": (1080, 1920), "4k": (3840, 2160), "4k9x16": (2160, 3840)}
CODEC = {"prores": False}      # --prores: ProRes 422 HQ (.mov) para edición, en lugar de H.264

# DTM de 1 m de la SGIAR (Santa Cruz: Puerto Ayora, escarpe y Bellavista) y el DSM Copernicus puro, para comparar
DTM_VRT = ROOT / "datos/dtm_sgiar/dtm_sgiar_1m.vrt"
DTM_MAR = ROOT / "descargas/dem_recortes/santa_cruz_dtm_mar_5m.tif"
ISLAS["santa-cruz-dtm"] = dict(epsg=32715, dtm=True, res=2.0, base="santa-cruz", nombre="Santa Cruz")
ISLAS["santa-cruz-cop"] = dict(epsg=32715, dem=ROOT / "descargas/dem/Copernicus_DSM_COG_10_S01_00_W091_00_DEM.tif", nombre="Santa Cruz")

# ---------------------------------------------------------------- paleta: marca USFQ Galápagos (rojo, negro y blanco).
# El azul solo lo pone el mar; cauces y agua del modelo en blanco (translúcido) sobre relieve oscurecido; rojo solo para lo que hay que mirar.
ROJO = (225, 27, 34)            # #E11B22 USFQ
NEGRO = (20, 20, 20); BLANCO = (255, 255, 255)
HIPSO = [(-5, "#d9d3bd"), (0, "#d9d3bd"), (40, "#cfc6a6"), (120, "#b9b48b"), (220, "#9fa874"), (350, "#7f975c"),
         (500, "#66854c"), (650, "#5a7746"), (800, "#66704f"), (1000, "#7b7b64")]
MAR_SOMERO, MAR_MEDIO, MAR_HONDO = "#86bcc4", "#4b8ba3", "#2c5f7c"
CIELO_ARRIBA, CIELO_HORIZONTE = "#c3c7ca", "#eceded"
AGUA_CMAP = [(0.0, "#dfe4e6"), (0.5, "#f2f4f5"), (1.5, "#ffffff"), (5.0, "#ffffff")]
QUEBRADA = "#ffffff"; EDIF = "#efebe2"; EDIF_BORDE = "#8e8574"; VIA = "#f7f5ef"
EDIF_OSC = "#8f8a82"; VIA_OSC = "#77726b"     # sobre relieve oscurecido, para que el agua blanca destaque


def hex2rgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], "float32") / 255


def rampa(v, tabla):
    xs = np.array([a for a, _ in tabla], "float32"); cs = np.array([hex2rgb(c) for _, c in tabla])
    return np.stack([np.interp(v, xs, cs[:, k]) for k in range(3)], -1).astype("float32")


def suave(t):                                   # easing coseno-quíntico (velocidad y aceleración nulas en los extremos)
    t = np.clip(t, 0, 1); return t * t * t * (t * (t * 6 - 15) + 10)


def rampa01(t, a, b):
    return float(suave((t - a) / max(b - a, 1e-9)))


# ---------------------------------------------------------------- datos
def gj(p):
    p = pathlib.Path(p)
    return [f for f in json.loads(p.read_text())["features"] if f.get("geometry")] if p.exists() else []


_dem = {}


def dtm_utm(cfg):
    """DTM SGIAR promediado a cfg['res'] m en su UTM nativa (mar del DTM = nan)."""
    from affine import Affine
    with rasterio.open(DTM_VRT) as d:
        r = cfg["res"]; h, w = int(d.height // r), int(d.width // r)
        z = d.read(1, out_shape=(h, w), resampling=Resampling.average if r > 1 else Resampling.nearest).astype("float32")
        tr = d.transform * Affine.scale(d.width / w, d.height / h)
        z[z == d.nodata] = np.nan
    with rasterio.open(DTM_MAR) as m:
        mar = m.read(1).astype(bool); mt = m.transform
    cs = np.clip(((tr.c + tr.a * (np.arange(w) + .5)) - mt.c) / mt.a, 0, mar.shape[1] - 1).astype(int)
    rs = np.clip(((tr.f + tr.e * (np.arange(h) + .5)) - mt.f) / mt.e, 0, mar.shape[0] - 1).astype(int)
    z[mar[rs][:, cs]] = np.nan
    return z, tr


def dem_utm(isla):
    """DEM reproyectado a UTM a 30 m (mar = nan)."""
    if isla not in _dem:
        cfg = ISLAS[isla]
        if cfg.get("dtm"):
            _dem[isla] = dtm_utm(cfg); return _dem[isla]
        if isla.startswith("galapagos"): mosaico_situacion()
        with rasterio.open(cfg["dem"]) as s:
            tr, w, h = calculate_default_transform(s.crs, f"EPSG:{cfg['epsg']}", s.width, s.height, *s.bounds, resolution=cfg.get("res", 30))
            z = np.full((h, w), np.nan, "float32")
            reproject(s.read(1).astype("float32"), z, src_transform=s.transform, src_crs=s.crs, src_nodata=-9999,
                      dst_transform=tr, dst_crs=f"EPSG:{cfg['epsg']}", dst_nodata=np.nan, resampling=Resampling.bilinear)
        _dem[isla] = (z, tr)
    return _dem[isla]


_zf = {}


def muestrear(isla, X, Y, orden=3):
    """Cota del DEM (m) en coordenadas UTM X, Y (arrays); mar = -3 m. Con el DTM, fuera de su cobertura se usa la isla base."""
    Z, TR = dem_utm(isla)
    if isla not in _zf: _zf[isla] = np.where(np.isnan(Z) | (Z <= 0.3), -3.0, Z).astype("float32")
    zf = _zf[isla]
    X = np.asarray(X, "float64"); Y = np.asarray(Y, "float64")
    c = (X - TR.c) / TR.a - 0.5; r = (Y - TR.f) / TR.e - 0.5
    out = map_coordinates(zf, [r, c], order=orden, mode="nearest").astype("float32")
    base = ISLAS[isla].get("base")
    if base:
        fuera = (c < 2) | (r < 2) | (c > Z.shape[1] - 3) | (r > Z.shape[0] - 3)
        if fuera.any(): out[fuera] = muestrear(base, X[fuera], Y[fuera], orden=min(orden, 1))
    return out


class Geo:
    def __init__(self, isla):
        self.isla = isla; self.epsg = ISLAS[isla]["epsg"]
        self.T = Transformer.from_crs(4326, self.epsg, always_xy=True); self.TI = Transformer.from_crs(self.epsg, 4326, always_xy=True)

    def xy(self, lon, lat):
        return self.T.transform(lon, lat)

    def utm(self, g):
        return shapely.transform(g, lambda a: np.column_stack(self.T.transform(a[:, 0], a[:, 1])))


# ---------------------------------------------------------------- textura
class Lienzo:
    """Imagen RGB (norte arriba) que cubre [x0,x1]×[y0,y1] en UTM a `px` m por texel."""

    def __init__(self, x0, y0, x1, y1, px):
        self.x0, self.y0, self.x1, self.y1, self.px = x0, y0, x1, y1, px
        self.W = int(round((x1 - x0) / px)); self.H = int(round((y1 - y0) / px))
        self.tr = from_origin(x0, y1, px, px)
        xs = x0 + px * (np.arange(self.W) + .5); ys = y1 - px * (np.arange(self.H) + .5)
        self.xs, self.ys = xs, ys

    def mascara(self, geoms, ancho_m=None, todo=False, sigma=0.7):
        gs = [g for g in geoms if g is not None and not g.is_empty]
        if not gs: return np.zeros((self.H, self.W), "float32")
        if ancho_m: gs = [g.buffer(ancho_m / 2, cap_style=1, join_style=1) for g in gs]
        bb = box(self.x0, self.y0, self.x1, self.y1); gs = [g.intersection(bb) for g in gs]; gs = [g for g in gs if not g.is_empty]
        if not gs: return np.zeros((self.H, self.W), "float32")
        m = features.rasterize([(g, 1) for g in gs], out_shape=(self.H, self.W), transform=self.tr, all_touched=todo).astype("float32")
        return gaussian_filter(m, sigma) if sigma else m

    def contorno(self, geoms, ancho_m):
        ls = []
        for g in geoms:
            for p in getattr(g, "geoms", [g]):
                if p.geom_type == "Polygon": ls += [p.exterior] + list(p.interiors)
                elif "Line" in p.geom_type: ls.append(p)
        return self.mascara(ls, ancho_m)


def sombreado(z, px, az=315, alt=42, vex=1.5):
    gy, gx = np.gradient(z * vex, px)
    sl = np.pi / 2 - np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    a, b = np.radians(az), np.radians(alt)
    return np.clip(np.sin(b) * np.sin(sl) + np.cos(b) * np.cos(sl) * np.cos(a - asp), 0, 1)


def mezclar(img, m, color, alfa=1.0):
    a = (m * alfa)[..., None]; img *= 1 - a; img += a * np.asarray(color, "float32"); return img


# ---------------------------------------------------------------- escena
class Escena:
    """Terreno (base insular + parche de detalle opcional), mar animado, cielo y luz."""

    def __init__(self, isla, centro, ancho, alto, vexag=2.0, res=None, tex_px=10, parche=None, mar_px=20, marea=0.0):
        res = res or ISLAS[isla].get("res", 30)
        self.g = Geo(isla); self.isla = isla; self.vexag = vexag
        cx, cy = self.g.xy(*centro); self.cx, self.cy = cx, cy
        self.capas = []        # (nombre, actor, lienzo, base_rgb, {capa: (mask, color)})
        self.bloques = []
        self.mar_nivel = marea
        self._terreno(cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2, res, tex_px, "base", agujero=parche)
        if parche:
            (pcx, pcy), pw, ph, pres, ppx = parche[:5]
            px_, py_ = self.g.xy(pcx, pcy)
            self._terreno(px_ - pw / 2, py_ - ph / 2, px_ + pw / 2, py_ + ph / 2, pres, ppx, "detalle", fuente=parche[5] if len(parche) > 5 else None)
        self._mar(cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2, mar_px)
        self.dinamicos = []

    # coordenadas locales (m, z exagerada)
    def loc(self, lon, lat, dz=0.0):
        x, y = self.g.xy(lon, lat); return (x - self.cx, y - self.cy, self.z(x, y) * self.vexag + dz)

    def z(self, x, y):
        return float(muestrear(self.isla, np.array([x]), np.array([y]))[0])

    def _terreno(self, x0, y0, x1, y1, res, tex_px, nombre, agujero=None, fuente=None):
        fuente = fuente or self.isla
        nx = int(round((x1 - x0) / res)) + 1; ny = int(round((y1 - y0) / res)) + 1
        xs = np.linspace(x0, x1, nx); ys = np.linspace(y1, y0, ny)
        X, Y = np.meshgrid(xs, ys)
        Z = muestrear(fuente, X, Y, orden=3)
        Zr = Z.copy()
        if agujero:
            (pcx, pcy), pw, ph = agujero[:3]
            px_, py_ = self.g.xy(pcx, pcy)
            dentro = (np.abs(X - px_) < pw / 2 - 2 * res) & (np.abs(Y - py_) < ph / 2 - 2 * res)
            Zr[dentro] -= 60
        grid = pv.StructuredGrid(); grid.dimensions = (nx, ny, 1)
        grid.points = np.c_[(X - self.cx).ravel(), (Y - self.cy).ravel(), (Zr * self.vexag).ravel()].astype("float64")
        grid.point_data["Normals"] = normales(X, Y, Zr * self.vexag); grid.point_data.active_normals_name = "Normals"
        lz = Lienzo(x0, y0, x1, y1, tex_px)
        grid.active_texture_coordinates = np.c_[((X - x0) / (x1 - x0)).ravel(), ((Y - y0) / (y1 - y0)).ravel()].astype("float32")
        Zt = muestrear(fuente, *np.meshgrid(lz.xs, lz.ys), orden=3)
        base = rampa(Zt, HIPSO)
        hs = 0.6 * sombreado(Zt, tex_px, 315, 38, 2.5) + 0.4 * sombreado(Zt, tex_px, 250, 50, 2.5)
        base *= (0.55 + 0.55 * hs)[..., None]
        tierra = Zt > 0.3
        base[~tierra] = hex2rgb(MAR_SOMERO)
        self.bloques.append(dict(nombre=nombre, grid=grid, lz=lz, base=np.clip(base, 0, 1), Z=Z, xs=xs, ys=ys, tierra=tierra,
                                 capas={}, estado=None, actor=None))

    def _mar(self, x0, y0, x1, y1, px):
        # malla rectilínea: densa sobre la zona de interés, cada vez más gruesa hacia el horizonte (±90 km)
        def eje(a, b):
            dentro = np.arange(a - 3000, b + 3000, max(60.0, (x1 - x0) / 2500))
            lim = max(90000, 1.6 * max(x1 - x0, y1 - y0))
            fuera = 3000 * 1.25 ** np.arange(1, 40); fuera = fuera[fuera < lim]
            return np.concatenate([a - 3000 - fuera[::-1], dentro, dentro[-1] + fuera])
        xs = eje(x0, x1); ys = eje(y0, y1)[::-1]
        X, Y = np.meshgrid(xs, ys)
        g = pv.StructuredGrid(); g.dimensions = (len(xs), len(ys), 1)
        g.points = np.c_[(X - self.cx).ravel(), (Y - self.cy).ravel(), np.zeros(X.size)]
        # textura del mar: somero cerca de la costa, hondo lejos; se extiende por «clamp» fuera del recuadro
        lz = Lienzo(x0 - 3000, y0 - 3000, x1 + 3000, y1 + 3000, px)
        Zt = muestrear(self.isla, *np.meshgrid(lz.xs, lz.ys), orden=1)
        d = distance_transform_edt(Zt <= 0.3) * px
        f = np.clip(d / 2500, 0, 1)[..., None]
        col = (1 - np.clip(d / 350, 0, 1))[..., None] * hex2rgb(MAR_SOMERO) + np.clip(d / 350, 0, 1)[..., None] * hex2rgb(MAR_MEDIO)
        col = col * (1 - f) + f * hex2rgb(MAR_HONDO)
        borde = np.zeros_like(f[..., 0]); m = 40
        borde[:m] = borde[-m:] = 1; borde[:, :m] = borde[:, -m:] = 1
        borde = gaussian_filter(borde, 15)[..., None]
        col = col * (1 - borde) + borde * hex2rgb(MAR_HONDO)
        rng = np.random.default_rng(3)
        ruido = gaussian_filter(rng.standard_normal(Zt.shape), 6) * 0.25
        col = np.clip(col * (1 + 0.06 * ruido[..., None]), 0, 1)
        g.active_texture_coordinates = np.c_[((X - lz.x0) / (lz.x1 - lz.x0)).ravel(), ((Y - lz.y0) / (lz.y1 - lz.y0)).ravel()].astype("float32")
        self.mar = dict(grid=g, X=X - self.cx, Y=Y - self.cy, img=(col * 255).astype("uint8"))

    def olas(self, t, amp=0.12):
        """Superficie del mar en t (s): marea + oleaje leve (m reales, luego exagerado)."""
        X, Y = self.mar["X"], self.mar["Y"]
        ondas = [(0.55, 140, 20, 0.35), (0.3, 90, 75, 0.5), (0.2, 55, 140, 0.8), (0.12, 33, 200, 1.1)]
        z = np.zeros_like(X); dzx = np.zeros_like(X); dzy = np.zeros_like(X)
        for a, L, ang, w in ondas:
            k = 2 * np.pi / L; ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            fase = k * (X * ux + Y * uy) - w * t
            z += a * np.sin(fase); c = a * k * np.cos(fase); dzx += c * ux; dzy += c * uy
        e = self.vexag * amp
        n = np.stack([-dzx * e, -dzy * e, np.ones_like(X)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
        return (self.mar_nivel + amp * z) * self.vexag, n.reshape(-1, 3).astype("float32")

    # capas rasterizadas sobre la textura (se mezclan por fotograma con un alfa)
    def capa(self, nombre, geoms_utm, color, ancho_m=None, contorno=None, alfa=1.0, oscurecer_fuera=None, sigma=0.7, solo=None):
        for b in self.bloques:
            if solo and b["nombre"] != solo: continue
            lz = b["lz"]
            if oscurecer_fuera is not None:
                m = 1 - lz.mascara(geoms_utm, sigma=6)
                b["capas"][nombre] = (m, np.asarray(color, "float32"), oscurecer_fuera)
                continue
            m = lz.contorno(geoms_utm, contorno) if contorno else lz.mascara(geoms_utm, ancho_m, sigma=sigma)
            b["capas"][nombre] = (m, np.asarray(color, "float32"), alfa)

    def morph(self, nombre, fuente_b):
        """Prepara el bloque `nombre` para pasar de su relieve a `fuente_b` (alfa «_morph» 0→1: geometría y textura)."""
        b = next(b for b in self.bloques if b["nombre"] == nombre)
        X, Y = np.meshgrid(b["xs"], b["ys"])
        b["Zb"] = muestrear(fuente_b, X, Y, orden=3)
        lz = b["lz"]; Zt = muestrear(fuente_b, *np.meshgrid(lz.xs, lz.ys), orden=3)
        base = rampa(Zt, HIPSO)
        hs = 0.6 * sombreado(Zt, lz.px, 315, 38, 2.5) + 0.4 * sombreado(Zt, lz.px, 250, 50, 2.5)
        base *= (0.55 + 0.55 * hs)[..., None]; base[Zt <= 0.3] = hex2rgb(MAR_SOMERO)
        b["base_b"] = np.clip(base, 0, 1); b["X"], b["Y"] = X, Y; b["_m"] = None

    def _aplicar_morph(self, b, a):
        if "Zb" not in b or b["_m"] == round(a, 3): return
        b["_m"] = round(a, 3)
        Z = (1 - a) * b["Z"] + a * b["Zb"]
        b["grid"].points[:, 2] = (Z * self.vexag).ravel()
        b["grid"].point_data["Normals"][:] = normales(b["X"], b["Y"], Z * self.vexag); b["grid"].Modified()

    def textura(self, b, alfas):
        clave = tuple(sorted((k, round(v, 3)) for k, v in alfas.items() if k in b["capas"] or k == "_morph"))
        if clave == b["estado"]: return None
        img = b["base"].copy()
        if "base_b" in b:
            mm = float(alfas.get("_morph", 0.0)); img = (1 - mm) * img + mm * b["base_b"]
        for k, (m, col, a0) in b["capas"].items():
            a = alfas.get(k, 0.0)
            if a > 0.001: mezclar(img, m, col, a * a0)
        b["estado"] = clave
        t = pv.Texture((np.clip(img, 0, 1) * 255).astype("uint8")); t.interpolate = True; t.mipmap = True
        return t

    def montar(self, pl):
        self.pl = pl
        for b in self.bloques:
            t = self.textura(b, {})
            b["actor"] = pl.add_mesh(b["grid"], texture=t, ambient=0.32, diffuse=0.78, specular=0.0)
        m = self.mar
        zt, n = self.olas(0)
        m["grid"].points[:, 2] = zt.ravel(); m["grid"].point_data["Normals"] = n; m["grid"].point_data.active_normals_name = "Normals"
        tex = pv.Texture(m["img"]); tex.repeat = False; tex.edge_clamp = True; tex.interpolate = True; tex.mipmap = True
        m["actor"] = pl.add_mesh(m["grid"], texture=tex, ambient=0.35, diffuse=0.7, specular=0.55, specular_power=40)
        for d in self.dinamicos: d.montar(pl, self)

    def actualizar(self, t, alfas):
        for b in self.bloques:
            self._aplicar_morph(b, float(alfas.get("_morph", 0.0)))
            tx = self.textura(b, alfas)
            if tx is not None: b["actor"].texture = tx
        m = self.mar
        zt, n = self.olas(t)
        m["grid"].points[:, 2] = zt.ravel(); m["grid"].point_data["Normals"][:] = n; m["grid"].Modified()


def normales(X, Y, Z):
    gy, gx = np.gradient(Z, Y[:, 0], X[0, :])
    n = np.stack([-gx, -gy, np.ones_like(Z)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n.reshape(-1, 3).astype("float32")


# ---------------------------------------------------------------- elementos dinámicos
class AguaModelo:
    """Lámina de agua del modelo 2D sobre el terreno, interpolada entre cuadros de 10 min."""

    def __init__(self, esc, cuadros, horas, transform, epsg, res=10.0, bbox=None, umbral=0.10, alfa=0.9, desfase=0.25, fuente=None):
        self.esc, self.C, self.h = esc, cuadros, np.asarray(horas, float)
        fuente = fuente or esc.isla
        a, b_, c, d, e, f = transform[:6]
        H, W = cuadros.shape[1:]
        x0, y1 = c, f; x1, y0 = c + a * W, f + e * H
        if bbox:
            bx0, by0, bx1, by1 = bbox; x0, y0, x1, y1 = max(x0, bx0), max(y0, by0), min(x1, bx1), min(y1, by1)
        nx = int((x1 - x0) / res) + 1; ny = int((y1 - y0) / res) + 1
        xs = np.linspace(x0, x1, nx); ys = np.linspace(y1, y0, ny); X, Y = np.meshgrid(xs, ys)
        self.cc = (X - c) / a - 0.5; self.rr = (Y - f) / e - 0.5
        # cota del modelo en su malla (bilineal del mismo DEM) y del terreno renderizado (cúbica)
        mx = c + a * (np.arange(W) + .5); my = f + e * (np.arange(H) + .5)
        MX, MY = np.meshgrid(mx, my)
        self.zm = muestrear(esc.isla, MX, MY, orden=1)
        self.zt = muestrear(fuente, X, Y, orden=3)
        self.umbral, self.alfa, self.desfase = umbral, alfa, desfase
        g = pv.StructuredGrid(); g.dimensions = (nx, ny, 1)
        g.points = np.c_[(X - esc.cx).ravel(), (Y - esc.cy).ravel(), (self.zt * esc.vexag).ravel()]
        g.point_data["rgba"] = np.zeros((X.size, 4), "uint8")
        g.point_data["Normals"] = np.tile(np.array([0, 0, 1], "float32"), (X.size, 1)); g.point_data.active_normals_name = "Normals"
        self.grid, self.X, self.Y = g, X, Y

    def calado(self, hora):
        i = np.searchsorted(self.h, hora) - 1; i = int(np.clip(i, 0, len(self.h) - 2))
        w = float(np.clip((hora - self.h[i]) / (self.h[i + 1] - self.h[i]), 0, 1))
        return (1 - w) * self.C[i].astype("float32") + w * self.C[i + 1].astype("float32")

    def montar(self, pl, esc):
        self.actor = pl.add_mesh(self.grid, scalars="rgba", rgba=True, ambient=0.45, diffuse=0.6, specular=0.35, specular_power=30,
                                 show_scalar_bar=False)

    def poner(self, hora, factor=1.0):
        h = np.nan_to_num(self.calado(hora)); h[h < 0] = 0
        wse = self.zm + h
        wse_t = map_coordinates(wse, [self.rr, self.cc], order=1, mode="nearest")
        h_t = map_coordinates(h, [self.rr, self.cc], order=1, mode="nearest")
        prof = np.minimum(np.maximum(wse_t - self.zt, 0), h_t * 1.5 + 0.2)
        prof = np.where(h_t > self.umbral, np.maximum(prof, h_t * 0.6), 0)
        z = np.maximum(self.zt + prof, self.zt) * self.esc.vexag + self.desfase * self.esc.vexag
        col = rampa(prof, AGUA_CMAP)
        a = np.clip((prof - self.umbral) / 0.15, 0, 1) * (0.42 + 0.53 * np.clip(prof / 1.5, 0, 1)) * self.alfa * factor
        rgba = np.concatenate([col * 255, a[..., None] * 255], -1).astype("uint8").reshape(-1, 4)
        self.grid.points[:, 2] = z.ravel(); self.grid.point_data["rgba"][:] = rgba
        gy, gx = np.gradient(z, 1.0)
        self.grid.Modified()
        return prof


class Lineas:
    """Polilíneas 3D pegadas al terreno que se dibujan progresivamente (fracción 0–1)."""

    def __init__(self, esc, geoms_utm, color, ancho_px=4, dz=3.0, paso=15.0, opacidad=1.0, orden=None, z_min=None, fuente=None):
        self.esc = esc; self.trazos = []; fuente = fuente or esc.isla
        for g in geoms_utm:
            for p in getattr(g, "geoms", [g]):
                if p.geom_type == "Polygon": p = p.exterior
                if "Line" not in p.geom_type and p.geom_type != "LinearRing": continue
                p = LineString(p.coords).segmentize(paso); a = np.array(p.coords)[:, :2]
                z = muestrear(fuente, a[:, 0], a[:, 1], orden=1)
                z = np.maximum(z, 0) + dz
                if z_min is not None: z = np.maximum(z, z_min)
                self.trazos.append(np.c_[a[:, 0] - esc.cx, a[:, 1] - esc.cy, z * esc.vexag])
        self.color, self.ancho, self.op = color, ancho_px, opacidad
        self.L = [np.r_[0, np.cumsum(np.linalg.norm(np.diff(t, axis=0), axis=1))] for t in self.trazos]
        self.actor = None

    def poly(self, frac, modo="todas"):
        pts, lines, n = [], [], 0
        for t, L in zip(self.trazos, self.L):
            if len(t) < 2: continue
            k = int(np.searchsorted(L, frac * L[-1])) + 1 if frac < 1 else len(t)
            k = max(min(k, len(t)), 0)
            if k < 2: continue
            seg = t[:k]
            pts.append(seg); lines.append(np.r_[k, np.arange(n, n + k)]); n += k
        if not pts: return pv.PolyData()
        return pv.PolyData(np.vstack(pts), lines=np.concatenate(lines))

    def montar(self, pl, esc):
        self.pl = pl; self.actor = None; self._frac = None

    def poner(self, frac, opacidad=None):
        if self.actor is not None: self.pl.remove_actor(self.actor, render=False); self.actor = None
        op = self.op if opacidad is None else opacidad
        if frac <= 0 or op <= 0.01: return
        p = self.poly(frac)
        if p.n_points:
            self.actor = self.pl.add_mesh(p, color=self.color, line_width=self.ancho, render_lines_as_tubes=True, opacity=op,
                                          lighting=False, reset_camera=False)


# ---------------------------------------------------------------- cámara
class Camara:
    """Fotogramas clave: (t 0–1, dict(x, y [UTM o lon/lat], z?, dist, mira [rumbo hacia donde mira], elev [°], va [°]))."""

    def __init__(self, esc, claves, ease=True):
        self.esc = esc; ts = [k[0] for k in claves]; self.ease = ease
        P = []
        prev = None
        for _, k in claves:
            if "lon" in k: x, y, z = esc.loc(k["lon"], k["lat"])
            else: x, y, z = k["x"], k["y"], esc.z(k["x"] + esc.cx, k["y"] + esc.cy) * esc.vexag
            z = k.get("z", max(z, 0))
            m = k["mira"]
            if prev is not None:
                while m - prev > 180: m -= 360
                while m - prev < -180: m += 360
            prev = m
            P.append([x, y, z, math.log(k["dist"]), m, k["elev"], k.get("va", 30)])
        P = np.array(P)
        if len(ts) == 1: ts = [0, 1]; P = np.vstack([P, P])
        self.f = PchipInterpolator(ts, P, axis=0)

    def en(self, u, vertical=None):
        u = suave(u) if self.ease else u
        x, y, z, ld, m, el, va = self.f(u)
        d = math.exp(ld)
        if vertical: d *= vertical.get("dist", 1.0); va = vertical.get("va", va)
        m_, e_ = math.radians(m), math.radians(el)
        dirv = np.array([math.sin(m_) * math.cos(e_), math.cos(m_) * math.cos(e_), -math.sin(e_)])
        foc = np.array([x, y, z]); pos = foc - d * dirv
        return pos, foc, va, d


# ---------------------------------------------------------------- render y codificación
class Animacion:
    def __init__(self, nombre, isla, dur, escena, camara, actualizar=None, portada=0.6, vertical=None, pista=None, reloj=None,
                 nota="", bruma=5.0, claves_v=None):
        self.nombre, self.isla, self.dur, self.esc, self.cam = nombre, isla, dur, escena, camara
        self.actualizar = actualizar or (lambda t, u: {})
        self.portada, self.vertical, self.pista, self.reloj = portada, vertical or {}, pista, reloj
        self.bruma = bruma
        self.cam_v = Camara(escena, claves_v, ease=camara.ease) if claves_v else None


BRUMA = """//VTK::TAG
  {
    float dist_ = length(vertexVC.xyz);
    float f_ = 1.0 - exp(-pow(dist_ * brumaK, 1.35));
    fragOutput0.rgb = mix(fragOutput0.rgb, brumaColor, clamp(f_ * brumaMax, 0.0, 1.0));
  }
"""


def bruma(actor, k, color=CIELO_HORIZONTE, maximo=0.85):
    sp = actor.GetShaderProperty()
    tag = "//VTK::TCoord::Impl" if actor.GetTexture() is not None else "//VTK::Light::Impl"
    sp.AddFragmentShaderReplacement(tag, True, BRUMA.replace("//VTK::TAG", tag), False)
    u = sp.GetFragmentCustomUniforms()
    u.SetUniformf("brumaK", float(k)); u.SetUniform3f("brumaColor", [float(v) for v in hex2rgb(color)]); u.SetUniformf("brumaMax", float(maximo))
    u.SetUniformf("brumaK", float(k))
    return u


def nuevo_plotter(w, h, esc):
    pl = pv.Plotter(off_screen=True, window_size=(w, h), lighting="none")
    pl.set_background(CIELO_HORIZONTE, top=CIELO_ARRIBA)
    sol = pv.Light(position=(-0.55, 0.45, 0.70), focal_point=(0, 0, 0), light_type="scene light", intensity=1.0)
    sol.positional = False
    pl.add_light(sol)
    rel = pv.Light(position=(0.6, -0.5, 0.6), focal_point=(0, 0, 0), light_type="scene light", intensity=0.25); rel.positional = False
    pl.add_light(rel)
    try: pl.enable_anti_aliasing("ssaa")
    except Exception: pass
    esc.montar(pl)
    esc.uniformes = []
    for act in list(pl.actors.values()):
        try: esc.uniformes.append(bruma(act, 1 / 40000))
        except Exception as ex: print("bruma:", ex)
    return pl


def ffmpeg_proc(ruta, w, h, crf=17):
    if CODEC["prores"]:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
               "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(ruta.with_suffix(".mov"))]
        return subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-tune", "film",
           "-movflags", "+faststart", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(ruta)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def fotograma(pl, an, t, fmt):
    u = t / an.dur
    alfas = an.actualizar(t, u) or {}
    an.esc.actualizar(t, alfas)
    vert = fmt.endswith("9x16")
    if vert and an.cam_v is not None: pos, foc, va, d = an.cam_v.en(u)
    else: pos, foc, va, d = an.cam.en(u, an.vertical if vert else None)
    c = pl.camera
    c.position = tuple(pos); c.focal_point = tuple(foc); c.up = (0, 0, 1); c.view_angle = va
    c.clipping_range = (max(d * 0.02, 5.0), d * 60 + 200000)
    k = 1.0 / (an.bruma * d)
    for u_ in getattr(an.esc, "uniformes", []): u_.SetUniformf("brumaK", k)
    pl.render()
    return pl.screenshot(return_img=True)


def renderizar(an, formatos=("16x9", "9x16"), prueba=False, crf=17, salida=None):
    carpeta = (salida or SALIDA) / an.isla; carpeta.mkdir(parents=True, exist_ok=True)
    n = int(round(an.dur * FPS))
    for fmt in formatos:
        w, h = FORMATOS[fmt]
        if prueba: w, h = w // 2, h // 2
        pl = nuevo_plotter(w, h, an.esc)
        t0 = time.time()
        if prueba:
            fr = []
            for u in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
                fr.append(fotograma(pl, an, min(u * an.dur, an.dur - 1 / FPS), fmt))
            hoja = np.concatenate([np.concatenate(fr[:3], 1), np.concatenate(fr[3:], 1)], 0)
            p = carpeta / "_pruebas" / f"{an.nombre}_{fmt}.jpg"; p.parent.mkdir(exist_ok=True)
            Image.fromarray(hoja).save(p, quality=85); print("  prueba →", p)
        else:
            ruta = carpeta / f"{an.nombre}_{fmt}.mp4"
            pr = ffmpeg_proc(ruta, w, h, crf)
            ip = int(round(an.portada * (n - 1)))
            for i in range(n):
                img = fotograma(pl, an, i / FPS, fmt)
                pr.stdin.write(np.ascontiguousarray(img[:, :, :3]).tobytes())
                if i == ip:
                    Image.fromarray(img[:, :, :3]).save(carpeta / f"{an.nombre}_{fmt}.png")
                if i % 60 == 0: print(f"   {fmt} {i}/{n}  {time.time() - t0:.0f}s", flush=True)
            pr.stdin.close(); pr.wait()
            print(f"  → {ruta.with_suffix('.mov') if CODEC['prores'] else ruta}  ({time.time() - t0:.0f} s)")
        pl.close()
        # reiniciar el estado de las texturas para el siguiente formato
        for b in an.esc.bloques: b["estado"] = None
    if not prueba:
        if an.pista: escribir_pista(an, carpeta, n)
        if an.reloj: escribir_reloj(an, carpeta, n)


def escribir_pista(an, carpeta, n):
    filas = [an.pista(i / FPS, i / FPS / an.dur) for i in range(n)]
    with open(carpeta / f"{an.nombre}_pista.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fotograma", "t_s"] + list(filas[0].keys())); w.writeheader()
        for i, r in enumerate(filas): w.writerow({"fotograma": i, "t_s": round(i / FPS, 3), **r})


def fuente(peso="ExtraBold", tam=64):
    for p in [pathlib.Path.home() / f"Library/Fonts/ZalandoSansExpanded-{peso}.ttf", pathlib.Path("/System/Library/Fonts/HelveticaNeue.ttc")]:
        if p.exists(): return ImageFont.truetype(str(p), tam)
    return ImageFont.load_default()


def escribir_reloj(an, carpeta, n):
    """Capa de reloj con alfa (ProRes 4444, 640×200): «30 OCT · HH:MM» en blanco con sombra suave. Hora local UTC−6."""
    W, H = 640, 200
    f1, f2 = fuente("ExtraBold", 92), fuente("Regular", 34)
    ruta = carpeta / f"{an.nombre}_reloj.mov"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(ruta)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cache = {}
    for i in range(n):
        hora = an.reloj(i / FPS, i / FPS / an.dur)
        if hora is None: img = np.zeros((H, W, 4), "uint8")
        else:
            k = hora.strftime("%d %H:%M")
            if k not in cache:
                im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
                meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
                t1 = hora.strftime("%H:%M"); t2 = f"{hora.day} {meses[hora.month - 1]} 2026 · UTC−6"
                sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sombra)
                ds.text((24, 6), t1, font=f1, fill=(0, 0, 0, 150)); ds.text((26, 128), t2, font=f2, fill=(0, 0, 0, 150))
                from PIL import ImageFilter
                sombra = sombra.filter(ImageFilter.GaussianBlur(5))
                im = Image.alpha_composite(sombra, im); d = ImageDraw.Draw(im)
                d.text((20, 2), t1, font=f1, fill=(255, 255, 255, 255)); d.text((22, 124), t2, font=f2, fill=(255, 255, 255, 235))
                cache[k] = np.array(im)
            img = cache[k]
        pr.stdin.write(img.tobytes())
    pr.stdin.close(); pr.wait(); print("  reloj →", ruta)


# ================================================================ capas comunes
def cuenca_cascada(geo):
    return geo.utm(unary_union([shape(f["geometry"]).buffer(1e-5) for f in gj(LC / "cuenca_cascada.geojson")]))


def quebradas(geo, isla_nombre, bb=None):
    out = []
    for f in gj(ROOT / "capas/final/quebradas.geojson"):
        if f["properties"].get("isla") != isla_nombre: continue
        out.append(geo.utm(shape(f["geometry"])))
    return out


def drenaje(geo, isla_nombre, area_min=0.5):
    return [geo.utm(shape(f["geometry"])) for f in gj(ROOT / "capas/final/drenaje_derivado.geojson")
            if f["properties"].get("isla") == isla_nombre and (f["properties"].get("area_drenada_km2") or 0) >= area_min]


def edificios(geo, isla_nombre):
    return [geo.utm(shape(f["geometry"])) for f in gj(ROOT / "capas/final/edificios_exposicion.geojson") if f["properties"].get("isla") == isla_nombre]


def vias(geo, bb_lonlat):
    b = box(*bb_lonlat)
    out = []
    for f in gj(ROOT / "capas/osm/vias.geojson"):
        g = shape(f["geometry"])
        if g.intersects(b): out.append(geo.utm(g))
    return out


def zonas(geo, isla_nombre):
    return [geo.utm(shape(f["geometry"]).buffer(0)) for f in gj(ROOT / "capas/final/zonas_pobladas.geojson") if f["properties"].get("isla") == isla_nombre]


def barrio_cascada(geo):
    a = [shape(f["geometry"]) for f in gj(ROOT / "capas/final/zonas_pobladas.geojson") if f["properties"].get("nombre") == "La Cascada"]
    b = [shape(f["geometry"]) for f in gj(ROOT / "capas/final/barrios.geojson") if f["properties"].get("nombre") == "LA CASCADA"]
    return geo.utm(unary_union([g.buffer(0) for g in a + b]))


def capas_urbanas(esc, isla_nombre, bb_lonlat, con_vias=True, oscuro=False):
    g = esc.g
    esc.capa("edificios", edificios(g, isla_nombre), hex2rgb(EDIF_OSC if oscuro else EDIF), sigma=0.5)
    esc.capa("edificios_borde", edificios(g, isla_nombre), hex2rgb("#4a463f" if oscuro else EDIF_BORDE), contorno=max(esc.bloques[-1]["lz"].px * 0.9, 1.5), alfa=0.6)
    if con_vias:
        esc.capa("vias", vias(g, bb_lonlat), hex2rgb(VIA_OSC if oscuro else VIA), ancho_m=max(6, esc.bloques[-1]["lz"].px * 1.2), alfa=0.85)


def capa_oscura(esc, alfa=0.45, nombre="oscuro"):
    """Oscurece todo el relieve (para que el agua blanca del modelo sea legible)."""
    for b in esc.bloques:
        b["capas"][nombre] = (np.ones((b["lz"].H, b["lz"].W), "float32"), np.zeros(3, "float32"), alfa)


# ================================================================ registro
ANIMS = {}


def anim(f):
    ANIMS[f.__name__] = f; return f


# ---------------------------------------------------------------- modelo 2D Santa Cruz
_m2d = {}


def modelo_sc(esc="b_central"):
    if esc not in _m2d:
        d = np.load(SCZ / f"modelo2d/{esc}/cuadros_10min.npz")
        _m2d[esc] = (d["calado"], d["horas_desde_12h"], d["transform"], int(d["epsg"]))
    return _m2d[esc]


def hora_sc(h):
    return dt.datetime(2026, 10, 30, 12, 0) + dt.timedelta(hours=float(h))


LA_CASCADA = (-90.3137, -0.7340); BELLAVISTA = (-90.3245, -0.6928); PTO_AYORA = (-90.3135, -0.7460)
TOMAS_B = (-90.3198, -0.7109)


@anim
def sc_sobrevuelo_cuenca():
    """Dron virtual: del mar frente a Puerto Ayora hacia la parte alta; se revela la cuenca de unos 40 km² que drena a La Cascada."""
    esc = Escena("santa-cruz", (-90.33, -0.67), 34000, 36000, vexag=2.0, res=30, tex_px=8)
    g = esc.g
    cu = cuenca_cascada(g)
    esc.capa("fuera", [cu], np.zeros(3), oscurecer_fuera=0.42)
    esc.capa("cuenca_borde", [cu], np.array([1, 1, 1]), contorno=40, alfa=1.0)
    esc.capa("quebradas", quebradas(g, "Santa Cruz"), hex2rgb(QUEBRADA), ancho_m=12, alfa=0.55)
    esc.capa("edificios", edificios(g, "Santa Cruz"), hex2rgb(EDIF), sigma=0.4)
    esc.capa("barrio", [barrio_cascada(g)], np.array(ROJO) / 255, contorno=26, alfa=1.0)
    cauce = [g.utm(shape(f["geometry"])) for f in gj(LC / "cauce_principal.geojson")]
    lin = Lineas(esc, cauce, "#ffffff", ancho_px=6, dz=4)
    esc.dinamicos.append(lin)
    cam = Camara(esc, [
        (0.00, dict(lon=-90.306, lat=-0.752, dist=3600, mira=-10, elev=15, va=34)),
        (0.30, dict(lon=-90.313, lat=-0.736, dist=3900, mira=-12, elev=20, va=34)),
        (0.62, dict(lon=-90.322, lat=-0.705, dist=9000, mira=-25, elev=30, va=32)),
        (1.00, dict(lon=-90.330, lat=-0.700, dist=17500, mira=-35, elev=48, va=30)),
    ])

    def act(t, u):
        a = rampa01(u, 0.42, 0.78)
        lin.poner(rampa01(u, 0.62, 0.97), opacidad=0.95)
        return {"fuera": a, "cuenca_borde": a, "quebradas": 0.5 + 0.5 * a, "edificios": 1.0, "barrio": rampa01(u, 0.18, 0.32)}
    return Animacion("sc_sobrevuelo_cuenca", "santa-cruz", 18, esc, cam, act, portada=0.92, vertical=dict(dist=1.35, va=44),
                     pista=lambda t, u: {"cuenca_visible": round(rampa01(u, 0.42, 0.78), 3), "cauce_principal_dibujado": round(rampa01(u, 0.62, 0.97), 3),
                                         "barrio_la_cascada_visible": round(rampa01(u, 0.18, 0.32), 3)})


def _cascada(nombre, mira0, mira1, elev, dist, dur=16, h0=3.5, h1=11.0, portada=0.8, motor="b_central", h_off=0.0):
    """h0/h1 en horas desde las 12:00; h_off = hora de inicio del archivo de cuadros respecto de las 12:00 (ANUGA: 5 h)."""
    esc = Escena("santa-cruz", LA_CASCADA, 16000, 16000, vexag=3.0, res=30, tex_px=8,
                 parche=(LA_CASCADA, 4200, 4200, 3, 1.2, "santa-cruz-dtm"))
    g = esc.g
    bb = (-90.345, -0.765, -90.285, -0.705)
    capa_oscura(esc, 0.42)
    capas_urbanas(esc, "Santa Cruz", bb, oscuro=True)
    esc.capa("quebradas", quebradas(g, "Santa Cruz"), hex2rgb(QUEBRADA), ancho_m=5, alfa=0.45)
    lin_b = Lineas(esc, [barrio_cascada(g)], "#E11B22", ancho_px=4, dz=0.6, paso=5, z_min=17.0, fuente="santa-cruz-dtm")
    esc.dinamicos.append(lin_b)
    C, H, TRf, ep = modelo_sc(motor)
    cx, cy = esc.cx, esc.cy
    agua = AguaModelo(esc, C, H, TRf, ep, res=4.0, bbox=(cx - 2000, cy - 2000, cx + 2000, cy + 2000), desfase=0.15, fuente="santa-cruz-dtm")
    esc.dinamicos.append(agua)
    cam = Camara(esc, [(0.0, dict(lon=LA_CASCADA[0], lat=LA_CASCADA[1], dist=dist, mira=mira0, elev=elev, va=30)),
                       (1.0, dict(lon=LA_CASCADA[0], lat=LA_CASCADA[1], dist=dist * 0.86, mira=mira1, elev=elev + 4, va=30))], ease=False)
    hora = lambda u: h0 + (h1 - h0) * suave(np.clip((u - 0.06) / 0.88, 0, 1))

    def act(t, u):
        agua.poner(hora(u) - h_off)
        if lin_b.actor is None: lin_b.poner(1.0)
        return {"oscuro": 1, "edificios": 1, "edificios_borde": 1, "vias": 1, "quebradas": 1}
    return Animacion(nombre, "santa-cruz", dur, esc, cam, act, portada=portada, vertical=dict(dist=1.45, va=42),
                     pista=lambda t, u: {"hora_local_utc6": hora_sc(hora(u)).strftime("%Y-%m-%d %H:%M"), "horas_desde_12h": round(float(hora(u)), 3)},
                     reloj=lambda t, u: hora_sc(hora(u)))


@anim
def sc_llenado_cascada_sur():
    """Llenado del vaso de La Cascada (modelo 2D, juego b central) visto desde el sur, 15:30 → 23:00."""
    return _cascada("sc_llenado_cascada_sur", 2, -14, 30, 2100)


@anim
def sc_llenado_cascada_noreste():
    """Llenado de La Cascada visto desde el noreste, por encima del escarpe."""
    return _cascada("sc_llenado_cascada_noreste", 222, 206, 34, 2100)


@anim
def sc_llenado_cascada_oeste():
    """Llenado de La Cascada visto desde el oeste: escarpe norte, vaso y salida hacia la bahía."""
    return _cascada("sc_llenado_cascada_oeste", 95, 80, 26, 2200)


@anim
def sc_llenado_cascada_sur_anuga():
    """Contraste de motor: el mismo llenado desde el sur con ANUGA (malla triangular, arranque a las 17:00), 17:30 → 23:00."""
    return _cascada("sc_llenado_cascada_sur_anuga", 2, -14, 30, 2100, h0=5.5, h1=11.0, motor="b_central_desde17h_anuga", h_off=5.0)


@anim
def sc_crecida_cuenca():
    """Mapa 2.5D: la crecida del modelo 2D (calado) se propaga por toda la cuenca, de las 14:30 a las 00:30."""
    C, H, TRf, ep = modelo_sc("b_central")
    a, _, c, _, e, f = TRf[:6]; Hh, Ww = C.shape[1:]
    x0, x1, y1, y0 = c, c + a * Ww, f, f + e * Hh
    geo = Geo("santa-cruz"); lon, lat = geo.TI.transform((x0 + x1) / 2, (y0 + y1) / 2)
    esc = Escena("santa-cruz", (lon, lat), 30000, 30000, vexag=2.0, res=30, tex_px=6)
    g = esc.g
    cu = cuenca_cascada(g)
    capa_oscura(esc, 0.40)
    esc.capa("fuera", [cu], np.zeros(3), oscurecer_fuera=0.30)
    esc.capa("cuenca_borde", [cu], np.array([1, 1, 1]), contorno=28, alfa=0.8)
    esc.capa("edificios", edificios(g, "Santa Cruz"), hex2rgb(EDIF_OSC), sigma=0.4)
    esc.capa("barrio", [barrio_cascada(g)], np.array(ROJO) / 255, contorno=24, alfa=1.0)
    agua = AguaModelo(esc, C, H, TRf, ep, res=10.0, desfase=0.6, umbral=0.06, alfa=1.0)
    esc.dinamicos.append(agua)
    cam = Camara(esc, [(0.0, dict(x=-200, y=-300, dist=13500, mira=-52, elev=46, va=30)),
                       (1.0, dict(x=-500, y=-1500, dist=11800, mira=-64, elev=41, va=30))], ease=False)
    hora = lambda u: 2.5 + 10.0 * float(np.clip((u - 0.04) / 0.92, 0, 1))

    def act(t, u):
        agua.poner(hora(u)); return {"oscuro": 1, "fuera": 1, "cuenca_borde": 1, "edificios": 1, "barrio": 1}
    return Animacion("sc_crecida_cuenca", "santa-cruz", 20, esc, cam, act, portada=0.62, vertical=dict(dist=1.45, va=46), claves_v=[(0.0, dict(x=-300, y=200, dist=17500, mira=-6, elev=50, va=46)),
                     (1.0, dict(x=-500, y=-900, dist=15500, mira=-14, elev=46, va=46))],
                     pista=lambda t, u: {"hora_local_utc6": hora_sc(hora(u)).strftime("%Y-%m-%d %H:%M"), "horas_desde_12h": round(hora(u), 3)},
                     reloj=lambda t, u: hora_sc(hora(u)))



# ================================================================ más animaciones de Santa Cruz
class Puntos:
    """Puntos (esferas de tamaño fijo en píxeles) que se pueden mostrar parcialmente."""

    def __init__(self, esc, lonlat, color, tam=9, dz=8.0, opacidad=1.0):
        self.esc = esc; self.P = np.array([esc.loc(lo, la, dz * esc.vexag) for lo, la in lonlat]) if len(lonlat) else np.zeros((0, 3))
        self.color, self.tam, self.op = color, tam, opacidad; self.actor = None; self._n = None

    def montar(self, pl, esc):
        self.pl = pl; self.actor = None; self._n = None

    def poner(self, n, color=None, tam=None):
        n = int(n)
        if n == self._n and color is None: return
        if self.actor is not None: self.pl.remove_actor(self.actor, render=False); self.actor = None
        self._n = n
        if n <= 0: return
        self.actor = self.pl.add_mesh(pv.PolyData(self.P[:n]), color=color or self.color, point_size=tam or self.tam,
                                      render_points_as_spheres=True, lighting=False, opacity=self.op, reset_camera=False)


class Mallas:
    """Contenedor de mallas que se regeneran en cada fotograma (columnas, halos, gotas)."""

    def __init__(self):
        self.actores = []

    def montar(self, pl, esc):
        self.pl = pl; self.actores = []

    def limpiar(self):
        for a in self.actores: self.pl.remove_actor(a, render=False)
        self.actores = []

    def poner(self, malla, **kw):
        kw.setdefault("reset_camera", False)
        self.actores.append(self.pl.add_mesh(malla, **kw))


class Edificios3D:
    """Edificios extruidos (huellas OSM + Google Open Buildings) apoyados en el terreno. Altura ilustrativa: el dato no la trae."""

    def __init__(self, esc, geoms_utm, bbox, fuente, alto=3.5, color=EDIF, opacidad=1.0):
        bx = box(*bbox); partes = []
        for g in geoms_utm:
            if not g.intersects(bx): continue
            for p in getattr(g, "geoms", [g]):
                if p.geom_type != "Polygon" or p.area < 6: continue
                p = p.simplify(0.4, preserve_topology=True)
                xy = np.array(p.exterior.coords)[:-1, :2]
                if len(xy) < 3: continue
                z0 = float(muestrear(fuente, xy[:, 0], xy[:, 1], orden=1).min()) - 0.6
                pts = np.c_[xy[:, 0] - esc.cx, xy[:, 1] - esc.cy, np.full(len(xy), z0 * esc.vexag)]
                cara = pv.PolyData(pts, faces=np.r_[len(xy), np.arange(len(xy))]).triangulate()
                partes.append(cara.extrude((0, 0, (alto + 0.6) * esc.vexag), capping=True))
        self.malla = pv.merge(partes) if partes else None
        self.n = len(partes); self.color, self.op = color, opacidad

    def montar(self, pl, esc):
        self.pl = pl; self.actor = None
        if self.malla is not None:
            self.actor = pl.add_mesh(self.malla, color=self.color, ambient=0.35, diffuse=0.75, specular=0.05, opacity=self.op,
                                     smooth_shading=False, reset_camera=False)

    def poner(self, opacidad):
        if self.actor is not None:
            self.actor.prop.opacity = opacidad; self.actor.SetVisibility(opacidad > 0.01)


class AguaNivel:
    """Llenado estático («bañera») sobre el terreno: agua conectada con el punto bajo hasta un nivel dado (m, EGM2008)."""

    def __init__(self, esc, fuente, bbox, res, punto_bajo, alfa=0.92, desfase=0.05):
        x0, y0, x1, y1 = bbox
        nx = int((x1 - x0) / res) + 1; ny = int((y1 - y0) / res) + 1
        X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y1, y0, ny))
        self.zt = muestrear(fuente, X, Y, orden=1)
        px, py = punto_bajo
        r0 = int(round((y1 - py) / res)); c0 = int(round((px - x0) / res))
        win = self.zt[max(r0 - 15, 0):r0 + 16, max(c0 - 15, 0):c0 + 16]
        rr, cc = np.unravel_index(np.argmin(win), win.shape)
        self.r0, self.c0 = max(r0 - 15, 0) + rr, max(c0 - 15, 0) + cc
        self.z0 = float(self.zt[self.r0, self.c0])
        self.esc, self.alfa, self.desfase = esc, alfa, desfase
        g = pv.StructuredGrid(); g.dimensions = (nx, ny, 1)
        g.points = np.c_[(X - esc.cx).ravel(), (Y - esc.cy).ravel(), (self.zt * esc.vexag).ravel()]
        g.point_data["rgba"] = np.zeros((X.size, 4), "uint8")
        g.point_data["Normals"] = np.tile(np.array([0, 0, 1], "float32"), (X.size, 1)); g.point_data.active_normals_name = "Normals"
        self.grid = g; self.mar = self.zt <= -2.9

    def montar(self, pl, esc):
        self.actor = pl.add_mesh(self.grid, scalars="rgba", rgba=True, ambient=0.5, diffuse=0.55, specular=0.6, specular_power=50,
                                 show_scalar_bar=False, reset_camera=False)

    def poner(self, nivel):
        if nivel <= self.z0:
            m = np.zeros_like(self.zt, bool)
        else:
            lab, _ = ndi_label((self.zt <= nivel) & ~self.mar, structure=np.ones((3, 3)))
            m = lab == lab[self.r0, self.c0]
        prof = np.where(m, nivel - self.zt, 0.0)
        z = np.where(m, nivel, self.zt) * self.esc.vexag + self.desfase * self.esc.vexag
        col = rampa(prof, AGUA_CMAP)
        a = np.where(m, (0.55 + 0.4 * np.clip(prof / 1.2, 0, 1)) * self.alfa, 0)
        self.grid.points[:, 2] = z.ravel()
        self.grid.point_data["rgba"][:] = np.concatenate([col * 255, a[..., None] * 255], -1).astype("uint8").reshape(-1, 4)
        self.grid.Modified()
        return m

def ruta_d8(lon, lat, max_pasos=4000):
    """Recorrido D8 (direcciones_d8.tif de Santa Cruz) desde un punto hasta el mar o una depresión."""
    with rasterio.open(SCZ / "direcciones_d8.tif") as s:
        fd = s.read(1); tr = s.transform
    geo = Geo("santa-cruz"); x, y = geo.xy(lon, lat)
    c, r = ~tr * (x, y); r, c = int(r), int(c)
    dm = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
    pts = []
    for _ in range(max_pasos):
        pts.append(tr * (c + .5, r + .5))
        d = dm.get(int(fd[r, c]))
        if d is None: break
        r, c = r + d[0], c + d[1]
        if not (0 <= r < fd.shape[0] and 0 <= c < fd.shape[1]): break
    return LineString(pts)


def a_lo_largo(linea, f):
    p = linea.interpolate(float(np.clip(f, 0, 1)), normalized=True); return p.x, p.y


@anim
def sc_gota_lluvia():
    """«Gota de lluvia»: el agua que cae en la parte alta (rama norte, rama este y Bellavista) baja por los cauces D8 hasta La Cascada."""
    esc = Escena("santa-cruz", (-90.322, -0.700), 26000, 30000, vexag=2.5, res=30, tex_px=6)
    g = esc.g
    cu = cuenca_cascada(g)
    esc.capa("fuera", [cu], np.zeros(3), oscurecer_fuera=0.42)
    esc.capa("cuenca_borde", [cu], np.array([1, 1, 1]), contorno=30, alfa=0.9)
    esc.capa("quebradas", quebradas(g, "Santa Cruz"), hex2rgb(QUEBRADA), ancho_m=10, alfa=0.35)
    esc.capa("edificios", edificios(g, "Santa Cruz"), hex2rgb(EDIF), sigma=0.4)
    rutas = []
    for f in gj(LC / "cauce_principal.geojson"):
        ln = g.utm(shape(f["geometry"]))
        a = np.array(ln.coords)
        if muestrear("santa-cruz", a[:1, 0], a[:1, 1])[0] < muestrear("santa-cruz", a[-1:, 0], a[-1:, 1])[0]: ln = LineString(a[::-1])
        rutas.append(ln)
    bv = ruta_d8(*BELLAVISTA)
    cx_, cy_ = g.xy(*LA_CASCADA)
    a = np.array(bv.coords); dd = np.hypot(a[:, 0] - cx_, a[:, 1] - cy_)
    if dd.min() < 600: rutas.append(LineString(a[:int(dd.argmin()) + 1]))
    rutas.sort(key=lambda l: -l.length)
    estelas = [Lineas(esc, [r], "#ffffff", ancho_px=6 if i == 0 else 4, dz=5, paso=20) for i, r in enumerate(rutas)]
    gotas = Mallas(); esc.dinamicos += estelas + [gotas]
    guia = rutas[0]
    fs = np.linspace(0, 1, 9); claves = []
    for k, f in enumerate(fs):
        x, y = a_lo_largo(guia, f); x2, y2 = a_lo_largo(guia, min(f + 0.12, 1)); x1, y1 = a_lo_largo(guia, max(f - 0.12, 0))
        rumbo = math.degrees(math.atan2(x2 - x1, y2 - y1))
        claves.append((0.06 + 0.80 * f, dict(x=x - esc.cx, y=y - esc.cy, dist=3200, mira=rumbo, elev=34, va=32)))
    xe, ye = g.xy(*LA_CASCADA)
    claves = [(0.0, dict(claves[0][1], dist=5200, elev=42))] + claves + [(1.0, dict(x=xe - esc.cx, y=ye - esc.cy + 2500, dist=9000, mira=claves[-1][1]["mira"], elev=48, va=32))]
    cam = Camara(esc, claves)
    fr = lambda u: float(np.clip((suave(u) - 0.06) / 0.80, 0, 1))

    def act(t, u):
        f = fr(u); gotas.limpiar()
        for i, (r, e) in enumerate(zip(rutas, estelas)):
            e.poner(f)
            x, y = a_lo_largo(r, f); z = esc.z(x, y)
            gotas.poner(pv.Sphere(radius=55 if i == 0 else 40, center=(x - esc.cx, y - esc.cy, (max(z, 0) + 12) * esc.vexag)),
                        color="white", ambient=0.6, diffuse=0.5, specular=0.6, specular_power=40)
        return {"fuera": 1, "cuenca_borde": 1, "quebradas": 1, "edificios": 1}
    return Animacion("sc_gota_lluvia", "santa-cruz", 20, esc, cam, act, portada=0.5, vertical=dict(dist=1.4, va=44),
                     pista=lambda t, u: {"fraccion_recorrida": round(fr(u), 3),
                                         "cota_gota_principal_m": round(esc.z(*a_lo_largo(rutas[0], fr(u))), 1),
                                         "km_recorridos_rama_principal": round(rutas[0].length * fr(u) / 1000, 2)})


def lluvia_estaciones():
    filas = list(csv.DictReader(open(SCZ / "lluvias/hietograma_5min.csv")))
    est = {r["estacion"]: r for r in csv.DictReader(open(SCZ / "lluvias/resumen_estaciones.csv"))}
    out = {}
    t0 = dt.datetime(2026, 10, 30, 0, 0)
    for nm, q in est.items():
        rr = [r for r in filas if r["estacion"] == nm and r["fecha_hora_local"].startswith("2026-10-30")]
        ts = np.array([(dt.datetime.fromisoformat(r["fecha_hora_local"]) - t0).total_seconds() / 3600 for r in rr])
        mm = np.array([max(float(r["lluvia_mm"] or 0), 0) for r in rr])
        o = np.argsort(ts); ts, mm = ts[o], mm[o]
        out[nm] = dict(lon=float(q["lon"]), lat=float(q["lat"]), ts=ts, acum=np.cumsum(mm), mm=mm, fin=float(ts.max()))
    return out


@anim
def sc_lluvia_columnas():
    """Lluvia MEDIDA el 30-oct (IERSE-WSN): columnas de lluvia acumulada y halos de intensidad sobre la isla, de 12:00 a 23:30."""
    esc = Escena("santa-cruz", (-90.34, -0.61), 46000, 50000, vexag=2.0, res=30, tex_px=12)
    g = esc.g
    esc.capa("edificios", edificios(g, "Santa Cruz"), hex2rgb(EDIF), sigma=0.5)
    esc.capa("cuenca_borde", [cuenca_cascada(g)], np.array([1, 1, 1]), contorno=60, alfa=0.55)
    E = lluvia_estaciones(); m = Mallas(); esc.dinamicos.append(m)
    ESC_H = 17.0                                   # unidades de escena por mm (ilustrativo)
    hora = lambda u: 12.0 + 11.5 * float(np.clip((u - 0.05) / 0.88, 0, 1))
    cam = Camara(esc, [(0.0, dict(lon=-90.350, lat=-0.640, dist=30000, mira=14, elev=28, va=30)),
                       (1.0, dict(lon=-90.350, lat=-0.640, dist=26500, mira=-12, elev=25, va=30))], ease=False)

    def valores(h):
        out = {}
        for nm, e in E.items():
            ac = float(np.interp(h, e["ts"], e["acum"], left=0)) if h <= e["fin"] else float(e["acum"][-1])
            ven = (e["ts"] > h - 0.25) & (e["ts"] <= h)
            it = float(e["mm"][ven].sum()) / 3 if h <= e["fin"] else 0.0
            out[nm] = (ac, it, h <= e["fin"] + 0.05)
        return out

    def act(t, u):
        h = hora(u); m.limpiar()
        for nm, (ac, it, ok) in valores(h).items():
            e = E[nm]; x, y, z = esc.loc(e["lon"], e["lat"])
            dudoso = "Crocker" in nm
            hh = max(ac * ESC_H, 6)
            col = "#bdbdbd" if dudoso else "white"
            m.poner(pv.Cylinder(center=(x, y, z + hh / 2), direction=(0, 0, 1), radius=420, height=hh, resolution=48),
                    color=col, opacity=0.92 if ok else 0.55, ambient=0.45, diffuse=0.7, specular=0.2)
            m.poner(pv.Disc(center=(x, y, z + 3), inner=380, outer=520, normal=(0, 0, 1), c_res=64), color="black", opacity=0.55, lighting=False)
            if it > 0.05:
                r = 600 + 330 * it
                m.poner(pv.Disc(center=(x, y, z + 60), inner=r * 0.82, outer=r, normal=(0, 0, 1), c_res=96), color="white", opacity=0.55, lighting=False)
        return {"edificios": 1, "cuenca_borde": 1}

    def pista(t, u):
        h = hora(u); v = valores(h); d = {"hora_local_utc6": hora_sc(h - 12).strftime("%Y-%m-%d %H:%M")}
        for nm, (ac, it, ok) in v.items():
            k = nm.split(" (")[0].lower().replace(" ", "_")
            d[f"{k}_acumulado_mm"] = round(ac, 1); d[f"{k}_mm_5min_media15"] = round(it, 2); d[f"{k}_transmite"] = int(ok)
        return d
    return Animacion("sc_lluvia_columnas", "santa-cruz", 18, esc, cam, act, portada=0.86, vertical=dict(dist=1.5, va=46), pista=pista,
                     reloj=lambda t, u: hora_sc(hora(u) - 12), bruma=3.5)


@anim
def sc_tomas_de_berlanga():
    """Tomás de Berlanga: el cauce que el modelo del terreno (D8) dibuja y que no está en el mapa oficial, cruzando la vía Puerto Ayora–Bellavista."""
    esc = Escena("santa-cruz", TOMAS_B, 14000, 14000, vexag=3.0, res=30, tex_px=8, parche=(TOMAS_B, 3600, 3600, 5, 1.5))
    g = esc.g
    capas_urbanas(esc, "Santa Cruz", (-90.34, -0.73, -90.30, -0.69))
    esc.capa("quebradas", quebradas(g, "Santa Cruz"), hex2rgb(QUEBRADA), ancho_m=6, alfa=0.85)
    cau = [g.utm(shape(f["geometry"])) for f in gj(SCZ / "urbano/tomas_de_berlanga_cauces.geojson")]
    lin = Lineas(esc, cau, "#E11B22", ancho_px=6, dz=1.5, paso=6)
    esc_p = Puntos(esc, [TOMAS_B], "white", tam=22, dz=8)
    esc.dinamicos += [lin, esc_p]
    cam = Camara(esc, [(0.0, dict(lon=TOMAS_B[0], lat=TOMAS_B[1], dist=2600, mira=25, elev=36, va=30)),
                       (0.5, dict(lon=TOMAS_B[0], lat=TOMAS_B[1] + 0.001, dist=2100, mira=0, elev=33, va=30)),
                       (1.0, dict(lon=TOMAS_B[0], lat=TOMAS_B[1], dist=2300, mira=-30, elev=38, va=30))])

    def act(t, u):
        lin.poner(rampa01(u, 0.30, 0.75)); esc_p.poner(1)
        return {"edificios": 1, "edificios_borde": 1, "vias": 1, "quebradas": 1}
    return Animacion("sc_tomas_de_berlanga", "santa-cruz", 16, esc, cam, act, portada=0.85, vertical=dict(dist=1.45, va=42),
                     pista=lambda t, u: {"cauce_d8_dibujado": round(rampa01(u, 0.30, 0.75), 3)})


@anim
def sc_cruces_quebradas_vias():
    """Cruces de quebradas con vías: aparecen todos los cruces (de la parte alta a la costa) y se resaltan en rojo los de prioridad alta."""
    esc = Escena("santa-cruz", (-90.335, -0.690), 26000, 28000, vexag=2.0, res=30, tex_px=6)
    g = esc.g
    capa_oscura(esc, 0.30)
    esc.capa("vias", vias(g, (-90.45, -0.77, -90.25, -0.60)), np.array([0.08, 0.08, 0.08]), ancho_m=14, alfa=0.75)
    esc.capa("quebradas", quebradas(g, "Santa Cruz") + drenaje(g, "Santa Cruz", 0.1), hex2rgb(QUEBRADA), ancho_m=9, alfa=0.45)
    esc.capa("edificios", edificios(g, "Santa Cruz"), hex2rgb(EDIF_OSC), sigma=0.4)
    fs = gj(SCZ / "cruces.geojson"); fs.sort(key=lambda f: -(f["properties"].get("cota_dsm_m") or 0))
    todos = Puntos(esc, [f["geometry"]["coordinates"][:2] for f in fs], "white", tam=8, dz=6)
    alta = Puntos(esc, [f["geometry"]["coordinates"][:2] for f in fs if f["properties"].get("prioridad") == "alta"], "#E11B22", tam=13, dz=9)
    puente = Puntos(esc, [f["geometry"]["coordinates"][:2] for f in fs if "puente" in str(f["properties"].get("estructura"))], "black", tam=16, dz=12)
    esc.dinamicos += [todos, alta, puente]
    n_t, n_a = len(todos.P), len(alta.P)
    cam = Camara(esc, [(0.0, dict(lon=-90.322, lat=-0.712, dist=17000, mira=-30, elev=44, va=30)),
                       (1.0, dict(lon=-90.322, lat=-0.718, dist=13500, mira=-45, elev=40, va=30))], ease=False)

    def act(t, u):
        todos.poner(n_t * rampa01(u, 0.08, 0.55)); alta.poner(n_a * rampa01(u, 0.62, 0.80)); puente.poner(2 if u > 0.86 else 0)
        return {"oscuro": 1, "vias": 1, "quebradas": 1, "edificios": 1}
    return Animacion("sc_cruces_quebradas_vias", "santa-cruz", 16, esc, cam, act, portada=0.84, vertical=dict(dist=1.45, va=46),
                     pista=lambda t, u: {"cruces_visibles": int(n_t * rampa01(u, 0.08, 0.55)), "prioridad_alta_visibles": int(n_a * rampa01(u, 0.62, 0.80)),
                                         "puentes_cartografiados_visibles": 2 if u > 0.86 else 0})


def nivel_mar(serie="puerto_ayora"):
    f = ROOT / f"datos/mareas/nivel_mar_{serie}_10min.csv"
    rr = list(csv.DictReader(open(f)))
    t0 = dt.datetime(2026, 10, 30, 12, 0)
    ts, zs = [], []
    for r in rr:
        t = dt.datetime.fromisoformat(r["fecha_hora_utc6"])
        v = r.get("obs_m") or r.get("est_m") or r.get("pred_m")
        try: v = float(v)
        except (TypeError, ValueError): continue
        if not -3 < v < 3: continue
        ts.append((t - t0).total_seconds() / 3600); zs.append(v)
    return np.array(ts), np.array(zs)


@anim
def sc_mar_marea():
    """Marea OBSERVADA en Puerto Ayora (30-oct 12:00 → 31-oct 06:00) y agua del modelo que llega a la costa por la ciudad, sin cauce."""
    centro = (-90.3115, -0.7455)
    esc = Escena("santa-cruz", centro, 14000, 14000, vexag=3.0, res=30, tex_px=8, parche=(centro, 4400, 4400, 5, 1.5))
    g = esc.g
    capa_oscura(esc, 0.38)
    capas_urbanas(esc, "Santa Cruz", (-90.34, -0.77, -90.28, -0.72), oscuro=True)
    C, H, TRf, ep = modelo_sc("b_central")
    agua = AguaModelo(esc, C, H, TRf, ep, res=5.0, bbox=(esc.cx - 2200, esc.cy - 2200, esc.cx + 2200, esc.cy + 2200), desfase=0.15)
    esc.dinamicos.append(agua)
    ts, zs = nivel_mar()
    hora = lambda u: 0.0 + 18.0 * float(np.clip((u - 0.03) / 0.94, 0, 1))
    cam = Camara(esc, [(0.0, dict(lon=-90.3105, lat=-0.7440, dist=2900, mira=-20, elev=24, va=30)),
                       (1.0, dict(lon=-90.3125, lat=-0.7430, dist=2500, mira=12, elev=27, va=30))], ease=False)

    def act(t, u):
        h = hora(u); esc.mar_nivel = float(np.interp(h, ts, zs)); agua.poner(h)
        return {"oscuro": 1, "edificios": 1, "edificios_borde": 1, "vias": 1}
    return Animacion("sc_mar_marea", "santa-cruz", 18, esc, cam, act, portada=0.5, vertical=dict(dist=1.45, va=42),
                     pista=lambda t, u: {"hora_local_utc6": hora_sc(hora(u)).strftime("%Y-%m-%d %H:%M"),
                                         "nivel_mar_obs_m_sobre_nmm_2017_2024": round(float(np.interp(hora(u), ts, zs)), 3)},
                     reloj=lambda t, u: hora_sc(hora(u)))


# ================================================================ crecimiento urbano (datos abiertos)
CU_DESC = ROOT / "descargas/crecimiento_urbano"          # crudos no versionados (datos no confiables)
CU_OUT = ROOT / "datos/crecimiento_urbano"
GHSL_EPOCAS = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030]
GHSL_OBSERVADAS = [e for e in GHSL_EPOCAS if e <= 2020]   # 2025 y 2030 son proyecciones del propio GHSL
CU_ZONA = {"santa-cruz": (-90.420, -0.765, -90.280, -0.615), "san-cristobal": (-89.640, -0.935, -89.500, -0.880)}


def _ghsl_epoca(e, dst_tr, shp, epsg):
    out = np.zeros(shp, "float32")
    for col in ("C9", "C10"):
        z = CU_DESC / f"ghsl/GHS_BUILT_S_E{e}_GLOBE_R2023A_54009_100_V1_0_R10_{col}.zip"
        if not z.exists(): continue
        with rasterio.open(f"zip://{z}!GHS_BUILT_S_E{e}_GLOBE_R2023A_54009_100_V1_0_R10_{col}.tif") as s:
            tmp = np.full(shp, np.nan, "float32")
            reproject(s.read(1).astype("float32"), tmp, src_transform=s.transform, src_crs=s.crs, src_nodata=s.nodata if s.nodata is not None else 65535,
                      dst_transform=dst_tr, dst_crs=f"EPSG:{epsg}", dst_nodata=np.nan, resampling=Resampling.nearest)
            ok = np.isfinite(tmp) & (tmp >= 0) & (tmp <= 10000)            # validación de rango (m² por celda de 100 m)
            out[ok] = np.maximum(out[ok], tmp[ok] / 10000.0)
    return out


def zonas_agua(isla, geo, lz):
    """Máscaras (10 m) de las zonas de agua: vasos, franja de 20 m a cada lado de cauces (IGM+OSM y D8 ≥ 0,5 km²),
    franja CGREG de 20 m y, si existe, calado máximo > 0,3 m del modelo 2D."""
    nombre = ISLAS[isla]["nombre"]; D = SCZ if isla == "santa-cruz" else SCB
    m = {}
    m["vasos"] = lz.mascara([geo.utm(shape(f["geometry"]).buffer(0)) for f in gj(D / "vasos.geojson")], sigma=0) > 0.5
    cau = quebradas(geo, nombre) + drenaje(geo, nombre, 0.5)
    m["franja_cauce_20m"] = lz.mascara(cau, ancho_m=40, sigma=0) > 0.5
    m["franja_cgreg_20m"] = lz.mascara([geo.utm(shape(f["geometry"]).buffer(0)) for f in gj(ROOT / "capas/final/quebradas_franja20m_cgreg.geojson")
                                         if f["properties"].get("isla") == nombre], sigma=0) > 0.5
    tif = (SCZ / "modelo2d/b_central/calado_max_m.tif") if isla == "santa-cruz" else (SCB / "modelo2d/guayabillos_15m_calado_max.tif")
    if tif.exists():
        with rasterio.open(tif) as s:
            tmp = np.zeros((lz.H, lz.W), "float32")
            reproject(s.read(1).astype("float32"), tmp, src_transform=s.transform, src_crs=s.crs, src_nodata=s.nodata,
                      dst_transform=lz.tr, dst_crs=f"EPSG:{geo.epsg}", dst_nodata=0, resampling=Resampling.nearest)
        m["modelo2d_calado_max_0_3m"] = tmp > 0.3
    m["cualquier_zona_de_agua"] = np.logical_or.reduce(list(m.values()))
    return m


def zonas_pobl(isla, geo, lz):
    nombre = ISLAS[isla]["nombre"]; out = {}
    for f in gj(ROOT / "capas/final/zonas_pobladas.geojson"):
        q = f["properties"]
        if q.get("isla") == nombre and q.get("tipo") == "Límite urbano IGM":
            out[q["nombre"] + " (límite urbano IGM)"] = lz.mascara([geo.utm(shape(f["geometry"]).buffer(0))], sigma=0) > 0.5
    if isla == "san-cristobal":
        x, y = geo.xy(-89.5565, -0.9120)
        out["El Progreso (círculo de 1 km; sin límite IGM)"] = lz.mascara([Point(x, y).buffer(1000)], sigma=0) > 0.5
    out["todo el recuadro de estudio"] = np.ones((lz.H, lz.W), bool)
    return out


def crecimiento_procesar():
    CU_OUT.mkdir(parents=True, exist_ok=True)
    resumen = {"generado": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "fuentes": {
        "GHSL": "GHS-BUILT-S R2023A (JRC, Comisión Europea), superficie construida por celda de 100 m, épocas 1975–2030 cada 5 años; "
                "2025 y 2030 son PROYECCIONES del GHSL, no observaciones. Licencia CC BY 4.0.",
        "WSF": "World Settlement Footprint Evolution v1 (DLR), año de primera detección 1985–2015, 30 m. La tesela que cubre Santa Cruz "
               "(-92,-2) llega vacía (sin detecciones): solo se usa para San Cristóbal, como contraste.",
        "OSM": "Huellas de edificios de OpenStreetMap (capas/final/edificios_exposicion.geojson), estado actual (2026)."},
        "metodo": "Rejilla UTM de 10 m sobre el recuadro de estudio; el GHSL se replica por vecino más próximo (cada celda de 100 m reparte "
                  "su fracción construida) y se suma dentro de cada zona. A 100 m las cifras en franjas de 20 m y vasos pequeños son "
                  "aproximadas (orden de magnitud), no catastro.", "islas": {}}
    filas = []
    for isla, bb in CU_ZONA.items():
        geo = Geo(isla)
        x0, y0 = geo.xy(bb[0], bb[1]); x1, y1 = geo.xy(bb[2], bb[3])
        lz = Lienzo(math.floor(x0 / 100) * 100, math.floor(y0 / 100) * 100, math.ceil(x1 / 100) * 100, math.ceil(y1 / 100) * 100, 10.0)
        shp = (lz.H, lz.W)
        F = np.stack([_ghsl_epoca(e, lz.tr, shp, geo.epsg) for e in GHSL_EPOCAS])
        prof = dict(driver="GTiff", height=lz.H, width=lz.W, count=len(GHSL_EPOCAS), dtype="uint8", crs=f"EPSG:{geo.epsg}",
                    transform=lz.tr, compress="deflate", nodata=255)
        with rasterio.open(CU_OUT / f"ghsl_fraccion_construida_{isla}_10m.tif", "w", **prof) as d:
            d.write(np.round(F * 100).astype("uint8"))
            for i, e in enumerate(GHSL_EPOCAS): d.set_band_description(i + 1, f"E{e} fraccion construida (%)" + (" PROYECCION" if e > 2020 else ""))
        za = zonas_agua(isla, geo, lz); zp = zonas_pobl(isla, geo, lz)
        osm = lz.mascara(edificios(geo, ISLAS[isla]["nombre"]), sigma=0) > 0.5
        wsf = None
        if isla == "san-cristobal":
            wsf = np.zeros(shp, "float32")
            for t in ("-90_-2", "-92_-2"):
                p = CU_DESC / f"wsf/WSFevolution_v1_{t}.tif"
                if not p.exists(): continue
                with rasterio.open(p) as s:
                    tmp = np.zeros(shp, "float32")
                    reproject(s.read(1).astype("float32"), tmp, src_transform=s.transform, src_crs=s.crs, src_nodata=None,
                              dst_transform=lz.tr, dst_crs=f"EPSG:{geo.epsg}", dst_nodata=0, resampling=Resampling.nearest)
                    tmp[(tmp < 1985) | (tmp > 2015)] = 0; wsf = np.maximum(wsf, tmp)
            with rasterio.open(CU_OUT / f"wsf_evolucion_ano_{isla}_10m.tif", "w", **dict(prof, count=1, dtype="uint16", nodata=0)) as d:
                d.write(wsf.astype("uint16"), 1)
        res_i = {}
        for zn, zm in list(zp.items()):
            for an_, am in [("total", None)] + list(za.items()):
                mm = zm if am is None else (zm & am)
                fila = {"isla": ISLAS[isla]["nombre"], "zona_poblada": zn, "zona_de_agua": an_,
                        "area_zona_ha": round(mm.sum() * 0.01, 1)}
                for i, e in enumerate(GHSL_EPOCAS):
                    fila[f"ghsl_{e}_ha" + ("_proyeccion" if e > 2020 else "")] = round(float(F[i][mm].sum()) * 0.01, 2)
                fila["osm_2026_huella_ha"] = round(float(osm[mm].sum()) * 0.01, 2)
                if wsf is not None:
                    for y in (1985, 1990, 1995, 2000, 2005, 2010, 2015):
                        fila[f"wsf_{y}_ha"] = round(float(((wsf > 0) & (wsf <= y) & mm).sum()) * 0.01, 2)
                filas.append(fila)
                res_i.setdefault(zn, {})[an_] = {k: v for k, v in fila.items() if k.endswith("_ha") or k.endswith("_proyeccion") or k == "area_zona_ha"}
        resumen["islas"][isla] = res_i
        print(f"  {isla}: GHSL 1975 → 2020 en el recuadro:",
              round(float(F[0].sum()) * 0.01, 1), "→", round(float(F[GHSL_EPOCAS.index(2020)].sum()) * 0.01, 1), "ha")
    campos = []
    for f in filas:
        for k in f:
            if k not in campos: campos.append(k)
    with open(CU_OUT / "crecimiento_urbano_por_zona.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); [w.writerow(f) for f in filas]
    (CU_OUT / "crecimiento_urbano_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print("  →", CU_OUT)


# ================================================================ crecimiento urbano: animaciones
def _epocas_en_lienzo(isla, lz, sigma_m=35):
    p = CU_OUT / f"ghsl_fraccion_construida_{isla}_10m.tif"
    out = []
    with rasterio.open(p) as s:
        for i in range(s.count):
            tmp = np.zeros((lz.H, lz.W), "float32")
            reproject(s.read(i + 1).astype("float32") / 100, tmp, src_transform=s.transform, src_crs=s.crs, src_nodata=255,
                      dst_transform=lz.tr, dst_crs=s.crs, dst_nodata=0, resampling=Resampling.bilinear)
            out.append(gaussian_filter(tmp, sigma_m / lz.px))
    return np.stack(out)


def _crecimiento(nombre, isla, centro, ancho, alto, claves, claves_v, doc):
    if not (CU_OUT / f"ghsl_fraccion_construida_{isla}_10m.tif").exists(): crecimiento_procesar()
    esc = Escena(isla, centro, ancho, alto, vexag=2.5, res=30, tex_px=5)
    g = esc.g; nombre_isla = ISLAS[isla]["nombre"]
    obs = [GHSL_EPOCAS.index(e) for e in GHSL_OBSERVADAS]
    for b in esc.bloques:
        lz = b["lz"]; F = _epocas_en_lienzo(isla, lz)
        prev = np.zeros_like(F[0])
        for i in obs:
            m = np.clip(F[i] * 1.6, 0, 1); inc = np.clip(m - prev, 0, 1); prev = np.maximum(prev, m)
            b["capas"][f"e{GHSL_EPOCAS[i]}"] = (inc, np.array([0.07, 0.07, 0.07], "float32"), 0.85)
        osm = lz.mascara(edificios(g, nombre_isla), sigma=0.5)
        b["capas"]["osm2026"] = (np.clip(osm - prev * 0.6, 0, 1), np.array([0.07, 0.07, 0.07], "float32"), 0.9)
        za = zonas_agua(isla, g, lz)["cualquier_zona_de_agua"].astype("float32")
        b["capas"]["zonas_agua"] = (gaussian_filter(za, 0.8), np.ones(3, "float32"), 0.55)
        constr = np.maximum(np.clip(F[GHSL_EPOCAS.index(2020)] * 1.6, 0, 1), osm)
        b["capas"]["construido_en_agua"] = (gaussian_filter((constr > 0.35) & (za > 0.5), 0.8).astype("float32"), np.array(ROJO, "float32") / 255, 0.95)
    cam = Camara(esc, claves)
    n = len(obs)
    def ano(u):
        f = np.clip((u - 0.08) / 0.54, 0, 1) * (n - 1); return GHSL_OBSERVADAS[0] + 5 * f

    def act(t, u):
        a = {}
        f = np.clip((u - 0.08) / 0.54, 0, 1) * (n - 1)
        for k, i in enumerate(obs): a[f"e{GHSL_EPOCAS[i]}"] = float(np.clip(f - k + 1, 0, 1)) if k > 0 else rampa01(u, 0.03, 0.08)
        a["osm2026"] = rampa01(u, 0.64, 0.72); a["zonas_agua"] = rampa01(u, 0.75, 0.83); a["construido_en_agua"] = rampa01(u, 0.86, 0.93)
        return a

    def pista(t, u):
        y = ano(u)
        etapa = ("GHSL " + str(int(round(y)))) if u < 0.64 else "OSM 2026" if u < 0.75 else "zonas de agua" if u < 0.86 else "construido en zonas de agua"
        return {"ano_ghsl": round(float(y), 2), "etapa": etapa}
    an = Animacion(nombre, isla, 20, esc, cam, act, portada=0.95, claves_v=claves_v, pista=pista)
    return an


@anim
def sc_crecimiento_urbano():
    """Crecimiento de la superficie construida (GHSL 1975–2020 + OSM 2026) en Puerto Ayora y Bellavista, y lo que cae en zonas de agua."""
    return _crecimiento("sc_crecimiento_urbano", "santa-cruz", (-90.318, -0.715), 18000, 20000,
                        [(0.0, dict(lon=-90.315, lat=-0.722, dist=9500, mira=-12, elev=48, va=30)),
                         (1.0, dict(lon=-90.314, lat=-0.730, dist=7200, mira=-22, elev=44, va=30))],
                        [(0.0, dict(lon=-90.318, lat=-0.718, dist=14500, mira=-6, elev=56, va=46)),
                         (1.0, dict(lon=-90.317, lat=-0.724, dist=11500, mira=-12, elev=52, va=46))], "")


# ================================================================ San Cristóbal
PBM = (-89.6100, -0.9010); EL_PROGRESO = (-89.5565, -0.9120); USFQ = (-89.6089, -0.8955)


@anim
def scb_sobrevuelo_canadas():
    """San Cristóbal: del mar frente a Puerto Baquerizo Moreno a El Progreso; se dibujan las cañadas oficiales (Barrio Frío/Galápagos, Divino Niño, Manzanillo…)."""
    esc = Escena("san-cristobal", (-89.575, -0.905), 30000, 24000, vexag=2.5, res=30, tex_px=6)
    g = esc.g
    esc.capa("edificios", edificios(g, "San Cristóbal"), hex2rgb(EDIF), sigma=0.4)
    esc.capa("quebradas", quebradas(g, "San Cristóbal"), hex2rgb(QUEBRADA), ancho_m=10, alfa=0.30)
    esc.capa("vias", vias(g, (-89.66, -0.95, -89.45, -0.85)), np.array([0.15, 0.15, 0.15]), ancho_m=10, alfa=0.35)
    fs = gj(SCB / "cañadas_oficiales.geojson")
    orden = {"alta": 0, "alta (salida) / media (trazado)": 1, "media": 2, "media-baja": 3, "baja": 4}
    fs.sort(key=lambda f: orden.get(f["properties"].get("confianza"), 5))
    lin = [Lineas(esc, [g.utm(shape(f["geometry"]))], "#ffffff", ancho_px=6 if i < 2 else 4, dz=4, paso=15, opacidad=1.0 if i < 2 else 0.8)
           for i, f in enumerate(fs)]
    esc.dinamicos += lin
    cam = Camara(esc, [(0.00, dict(lon=-89.6230, lat=-0.9080, dist=3800, mira=72, elev=17, va=34)),
                       (0.35, dict(lon=-89.6080, lat=-0.9030, dist=4600, mira=78, elev=24, va=34)),
                       (0.70, dict(lon=-89.5850, lat=-0.9070, dist=7800, mira=88, elev=34, va=32)),
                       (1.00, dict(lon=-89.5800, lat=-0.9080, dist=12500, mira=60, elev=46, va=30))])

    def act(t, u):
        for i, l in enumerate(lin): l.poner(rampa01(u, 0.25 + 0.05 * i, 0.55 + 0.05 * i))
        return {"edificios": 1, "quebradas": 1, "vias": 1}
    return Animacion("scb_sobrevuelo_canadas", "san-cristobal", 18, esc, cam, act, portada=0.95, vertical=dict(dist=1.4, va=44),
                     pista=lambda t, u: {**{f"cañada_{i + 1}_{f['properties']['cañada_oficial']}": round(rampa01(u, 0.25 + 0.05 * i, 0.55 + 0.05 * i), 3)
                                            for i, f in enumerate(fs)}})


def hora_scb(h):
    return dt.datetime(2026, 10, 30, 0, 0) + dt.timedelta(hours=float(h))


@anim
def scb_modelo2d_trasladada():
    """ESCENARIO: la tormenta medida en Los Guayabillos (Santa Cruz) el 30-oct, trasladada a Puerto Baquerizo Moreno (modelo 2D, 15 m), 14:00 → 02:00."""
    d = np.load(SCB / "modelo2d/guayabillos_15m_cuadros_ciudad.npz")
    C = d["calado_cm"].astype("float32") / 100; H = d["t_s"] / 3600; TRf = d["transform"]; ep = int(d["epsg"])
    a, _, c, _, e, f = TRf[:6]; Hh, Ww = C.shape[1:]
    geo = Geo("san-cristobal"); lon, lat = geo.TI.transform(c + a * Ww / 2, f + e * Hh / 2)
    esc = Escena("san-cristobal", (lon, lat), 14000, 14000, vexag=3.0, res=30, tex_px=8, parche=((lon, lat), 3600, 3600, 5, 1.5))
    capa_oscura(esc, 0.40)
    capas_urbanas(esc, "San Cristóbal", (-89.63, -0.92, -89.59, -0.88), oscuro=True)
    agua = AguaModelo(esc, C, H, TRf, ep, res=5.0, desfase=0.15)
    esc.dinamicos.append(agua)
    hora = lambda u: 14.0 + 12.0 * float(np.clip((u - 0.04) / 0.92, 0, 1))
    cam = Camara(esc, [(0.0, dict(lon=lon - 0.001, lat=lat - 0.0025, dist=4000, mira=50, elev=34, va=30)),
                       (1.0, dict(lon=lon - 0.001, lat=lat - 0.0025, dist=3500, mira=32, elev=38, va=30))], ease=False)

    def act(t, u):
        agua.poner(hora(u)); return {"oscuro": 1, "edificios": 1, "edificios_borde": 1, "vias": 1}
    return Animacion("scb_modelo2d_trasladada", "san-cristobal", 18, esc, cam, act, portada=0.62, vertical=dict(dist=1.45, va=42),
                     pista=lambda t, u: {"hora_escenario_utc6": hora_scb(hora(u)).strftime("%Y-%m-%d %H:%M"), "horas_desde_00h": round(hora(u), 3)},
                     reloj=lambda t, u: hora_scb(hora(u)))


@anim
def scb_tomas_agua():
    """Tomas de agua del acueducto en la parte alta (Cerro Gato, Los Americanos, La Toma, El Chino) y las conducciones hacia la ciudad."""
    esc = Escena("san-cristobal", (-89.52, -0.905), 24000, 18000, vexag=2.5, res=30, tex_px=6)
    g = esc.g
    esc.capa("edificios", edificios(g, "San Cristóbal"), hex2rgb(EDIF), sigma=0.4)
    esc.capa("quebradas", quebradas(g, "San Cristóbal"), hex2rgb(QUEBRADA), ancho_m=9, alfa=0.35)
    esc.capa("cuencas_tomas", [g.utm(shape(f["geometry"]).buffer(0)) for f in gj(SCB / "agua/cuencas_tomas.geojson")], np.ones(3), contorno=22, alfa=0.7)
    cond = [g.utm(shape(f["geometry"])) for f in gj(SCB / "agua/conducciones.geojson")]
    lc = Lineas(esc, cond, "#ffffff", ancho_px=4, dz=4, paso=15)
    tomas = [f for f in gj(SCB / "agua/tomas.geojson")]
    principales = [f["geometry"]["coordinates"][:2] for f in tomas if f["properties"]["id"] in ("AG-01", "AG-02", "AG-03", "AG-04")]
    otras = [f["geometry"]["coordinates"][:2] for f in tomas if f["properties"]["id"] not in ("AG-01", "AG-02", "AG-03", "AG-04")]
    pt = Puntos(esc, principales, "#E11B22", tam=15, dz=10); po = Puntos(esc, otras, "white", tam=10, dz=8)
    esc.dinamicos += [lc, pt, po]
    cam = Camara(esc, [(0.0, dict(lon=-89.490, lat=-0.912, dist=9000, mira=-5, elev=40, va=30)),
                       (0.55, dict(lon=-89.505, lat=-0.910, dist=8500, mira=-25, elev=38, va=30)),
                       (1.0, dict(lon=-89.540, lat=-0.905, dist=12500, mira=-55, elev=40, va=30))])

    def act(t, u):
        pt.poner(len(principales) if u > 0.12 else 0); po.poner(len(otras) if u > 0.22 else 0); lc.poner(rampa01(u, 0.35, 0.85))
        return {"edificios": 1, "quebradas": 1, "cuencas_tomas": rampa01(u, 0.05, 0.2)}
    return Animacion("scb_tomas_agua", "san-cristobal", 18, esc, cam, act, portada=0.5, vertical=dict(dist=1.45, va=44),
                     pista=lambda t, u: {"tomas_visibles": int(u > 0.12), "conducciones_dibujadas": round(rampa01(u, 0.35, 0.85), 3)})


@anim
def scb_campus_usfq():
    """Campus USFQ / Galapagos Science Center y la quebrada que llega desde arriba (análisis NO CONCLUYENTE; vista neutra)."""
    esc = Escena("san-cristobal", USFQ, 10000, 10000, vexag=3.0, res=30, tex_px=6, parche=(USFQ, 3200, 3200, 5, 1.5))
    g = esc.g
    capas_urbanas(esc, "San Cristóbal", (-89.63, -0.91, -89.59, -0.88))
    esc.capa("vias", vias(g, (-89.63, -0.91, -89.59, -0.88)), hex2rgb("#a39e95"), ancho_m=7, alfa=0.8)
    fs = gj(SCB / "quebrada_usfq.geojson")
    cuencas = [g.utm(shape(f["geometry"])) for f in fs if f["geometry"]["type"] == "Polygon" and "cuenca" in f["properties"]["elemento"]]
    campus = [g.utm(shape(f["geometry"])) for f in fs if "campus aproximado" in f["properties"]["elemento"]]
    cauce = [g.utm(shape(f["geometry"])) for f in fs if f["properties"]["elemento"].startswith("cauce D8")]
    esc.capa("cuencas", cuencas, np.ones(3), contorno=6, alfa=0.7)
    esc.capa("campus", campus, np.zeros(3), contorno=7, alfa=0.85)
    lin = Lineas(esc, cauce, "#ffffff", ancho_px=5, dz=1.5, paso=5)
    esc.dinamicos.append(lin)
    cam = Camara(esc, [(0.0, dict(lon=USFQ[0], lat=USFQ[1], dist=2300, mira=110, elev=30, va=30)),
                       (1.0, dict(lon=USFQ[0], lat=USFQ[1], dist=2000, mira=70, elev=34, va=30))], ease=False)

    def act(t, u):
        lin.poner(rampa01(u, 0.25, 0.75))
        return {"edificios": 1, "edificios_borde": 1, "vias": 1, "campus": rampa01(u, 0.05, 0.2), "cuencas": rampa01(u, 0.55, 0.8)}
    return Animacion("scb_campus_usfq", "san-cristobal", 15, esc, cam, act, portada=0.85, vertical=dict(dist=1.45, va=42),
                     pista=lambda t, u: {"cauce_d8_dibujado": round(rampa01(u, 0.25, 0.75), 3), "cuencas_visibles": round(rampa01(u, 0.55, 0.8), 3)})


@anim
def scb_crecimiento_urbano():
    """Crecimiento de la superficie construida (GHSL 1975–2020 + OSM 2026) en Puerto Baquerizo Moreno y El Progreso, y lo que cae en zonas de agua."""
    return _crecimiento("scb_crecimiento_urbano", "san-cristobal", (-89.585, -0.905), 20000, 16000,
                        [(0.0, dict(lon=-89.596, lat=-0.902, dist=8000, mira=55, elev=48, va=30)),
                         (1.0, dict(lon=-89.603, lat=-0.901, dist=6200, mira=68, elev=44, va=30))],
                        [(0.0, dict(lon=-89.592, lat=-0.904, dist=12500, mira=62, elev=56, va=46)),
                         (1.0, dict(lon=-89.598, lat=-0.903, dist=10000, mira=72, elev=52, va=46))], "")



# ================================================================ mapa de situación (archipiélago → isla → barrio)
def _situacion(nombre, isla, gal, destino, claves, claves_v, zonas_isla, rojo=None):
    esc = Escena(gal, (-90.55, -0.55), 330000, 300000, vexag=2.0, tex_px=90, mar_px=250,
                 parche=(destino["centro"], destino["ancho"], destino["alto"], 30, 9, isla))
    g = esc.g
    esc.capa("zonas", zonas_isla, np.ones(3), contorno=40, alfa=0.85, solo="detalle")
    esc.capa("edificios", edificios(g, ISLAS[isla]["nombre"]), hex2rgb(EDIF), sigma=0.4, solo="detalle")
    if rojo is not None: esc.capa("rojo", [rojo], np.array(ROJO) / 255, contorno=36, alfa=1.0, solo="detalle")
    cam = Camara(esc, claves)

    def act(t, u):
        return {"zonas": rampa01(u, 0.55, 0.75), "edificios": 1, "rojo": rampa01(u, 0.75, 0.88)}
    return Animacion(nombre, isla, 14, esc, cam, act, portada=0.0, claves_v=claves_v, bruma=6.0,
                     pista=lambda t, u: {"zonas_pobladas_visibles": round(rampa01(u, 0.55, 0.75), 3), "destacado_rojo": round(rampa01(u, 0.75, 0.88), 3)})


@anim
def sc_situacion():
    """Mapa de situación 3D: el archipiélago de Galápagos → Santa Cruz → Puerto Ayora y el barrio La Cascada (rojo)."""
    g = Geo("santa-cruz")
    zon = [g.utm(shape(f["geometry"]).buffer(0)) for f in gj(ROOT / "capas/final/zonas_pobladas.geojson")
           if f["properties"].get("isla") == "Santa Cruz" and f["properties"].get("tipo") == "Límite urbano IGM"]
    k = [(0.00, dict(lon=-90.72, lat=-0.38, dist=420000, mira=0, elev=72, va=30)),
         (0.25, dict(lon=-90.42, lat=-0.60, dist=230000, mira=-2, elev=66, va=30)),
         (0.50, dict(lon=-90.35, lat=-0.66, dist=60000, mira=-5, elev=55, va=30)),
         (1.00, dict(lon=-90.315, lat=-0.738, dist=6500, mira=-10, elev=42, va=30))]
    kv = [(0.00, dict(lon=-90.72, lat=-0.38, dist=520000, mira=0, elev=75, va=46)),
          (0.25, dict(lon=-90.42, lat=-0.60, dist=290000, mira=-2, elev=68, va=46)),
          (0.50, dict(lon=-90.35, lat=-0.66, dist=80000, mira=-5, elev=58, va=46)),
          (1.00, dict(lon=-90.316, lat=-0.738, dist=9000, mira=-10, elev=46, va=46))]
    return _situacion("sc_situacion", "santa-cruz", "galapagos-15", dict(centro=(-90.35, -0.62), ancho=48000, alto=46000), k, kv, zon,
                      rojo=barrio_cascada(g))


@anim
def scb_situacion():
    """Mapa de situación 3D: el archipiélago de Galápagos → San Cristóbal → Puerto Baquerizo Moreno y El Progreso."""
    g = Geo("san-cristobal")
    zon = [g.utm(shape(f["geometry"]).buffer(0)) for f in gj(ROOT / "capas/final/zonas_pobladas.geojson")
           if f["properties"].get("isla") == "San Cristóbal" and f["properties"].get("tipo") in ("Límite urbano IGM", "Huella edificada")]
    k = [(0.00, dict(lon=-90.72, lat=-0.38, dist=420000, mira=0, elev=72, va=30)),
         (0.25, dict(lon=-89.65, lat=-0.78, dist=230000, mira=15, elev=66, va=30)),
         (0.50, dict(lon=-89.47, lat=-0.82, dist=55000, mira=40, elev=55, va=30)),
         (1.00, dict(lon=-89.585, lat=-0.905, dist=9000, mira=60, elev=42, va=30))]
    kv = [(0.00, dict(lon=-90.72, lat=-0.38, dist=520000, mira=0, elev=75, va=46)),
          (0.25, dict(lon=-89.65, lat=-0.78, dist=290000, mira=15, elev=68, va=46)),
          (0.50, dict(lon=-89.47, lat=-0.82, dist=75000, mira=40, elev=58, va=46)),
          (1.00, dict(lon=-89.585, lat=-0.905, dist=12500, mira=60, elev=46, va=46))]
    return _situacion("scb_situacion", "san-cristobal", "galapagos-16", dict(centro=(-89.45, -0.82), ancho=50000, alto=36000), k, kv, zon)


# ================================================================ Santa Cruz con el DTM de 1 m de la SGIAR (4K)
DTM = "santa-cruz-dtm"
_vdtm = {}


def vaso_dtm():
    """Resultados de 37_cascada_dtm.py: punto bajo, umbral, cotas y curva cota–volumen a 1 m."""
    if not _vdtm:
        r = json.loads((LC / "dtm1m/resumen_dtm.json").read_text())["referencia"]
        cv = np.array([[float(f["cota_m"]), float(f["volumen_m3"]), float(f["area_m2"])]
                       for f in csv.DictReader(open(LC / "dtm1m/curva_cota_volumen_dtm.csv"))])
        _vdtm.update(r, curva=cv)
    return _vdtm


def salida_urbana(geo):
    return [geo.utm(shape(f["geometry"])) for f in gj(LC / "urbano/ruta_salida_urbana.geojson")]


@anim
def sc_dtm_revela():
    """Del DSM al terreno: sobre La Cascada, el relieve de 30 m con techos y árboles (Copernicus) se transforma en el DTM de 1 m de la SGIAR y aparecen los edificios."""
    esc = Escena("santa-cruz", LA_CASCADA, 14000, 14000, vexag=2.2, res=30, tex_px=8,
                 parche=(LA_CASCADA, 3600, 3600, 3, 1.2, "santa-cruz-cop"))
    esc.morph("detalle", DTM)
    g = esc.g
    bb_utm = (esc.cx - 1500, esc.cy - 1500, esc.cx + 1500, esc.cy + 1500)
    esc.capa("vias", vias(g, (-90.33, -0.75, -90.30, -0.72)), hex2rgb(VIA), ancho_m=5, alfa=0.0, solo="detalle")
    edif = Edificios3D(esc, edificios(g, "Santa Cruz"), bb_utm, DTM, alto=3.5)
    borde = Lineas(esc, [barrio_cascada(g)], "#E11B22", ancho_px=5, dz=1.5, paso=4, fuente=DTM)
    esc.dinamicos += [edif, borde]
    cam = Camara(esc, [(0.00, dict(lon=LA_CASCADA[0], lat=LA_CASCADA[1], dist=2600, mira=20, elev=34, va=30)),
                       (0.50, dict(lon=LA_CASCADA[0], lat=LA_CASCADA[1] - 0.001, dist=2200, mira=-10, elev=30, va=30)),
                       (1.00, dict(lon=LA_CASCADA[0], lat=LA_CASCADA[1] - 0.0015, dist=1800, mira=-42, elev=33, va=30))])
    mo = lambda u: rampa01(u, 0.28, 0.58)

    def act(t, u):
        a = mo(u); e = rampa01(u, 0.64, 0.80)
        edif.poner(e)
        borde.poner(rampa01(u, 0.84, 0.97))
        return {"_morph": a, "vias": rampa01(u, 0.58, 0.70)}
    return Animacion("sc_dtm_revela", "santa-cruz", 22, esc, cam, act, portada=0.9, vertical=dict(dist=1.5, va=44), bruma=14,
                     pista=lambda t, u: {"relieve": "DSM Copernicus 30 m" if mo(u) < 0.5 else "DTM SGIAR 1 m", "transicion_dsm_a_dtm": round(mo(u), 3),
                                         "edificios_visibles": round(rampa01(u, 0.64, 0.80), 3), "barrio_la_cascada": round(rampa01(u, 0.84, 0.97), 3)})


@anim
def sc_vaso_dtm():
    """La Cascada con el DTM de 1 m: el agua llena el vaso desde el punto bajo (13,4 m) hasta el umbral de rebose (15,05 m); por encima, sale por la salida natural hacia el mar."""
    v = vaso_dtm()
    esc = Escena("santa-cruz", LA_CASCADA, 10000, 10000, vexag=2.0, res=30, tex_px=8,
                 parche=(LA_CASCADA, 2600, 2600, 2, 1.0, DTM))
    g = esc.g
    capa_oscura(esc, 0.40)
    esc.capa("vias", vias(g, (-90.33, -0.75, -90.30, -0.72)), hex2rgb(VIA_OSC), ancho_m=5, alfa=0.9, solo="detalle")
    bb = (esc.cx - 1200, esc.cy - 1200, esc.cx + 1200, esc.cy + 1200)
    edif = Edificios3D(esc, edificios(g, "Santa Cruz"), bb, DTM, alto=3.5, color="#8f8a82")
    pb = g.xy(*v["punto_bajo_lonlat"])
    agua = AguaNivel(esc, DTM, (esc.cx - 900, esc.cy - 900, esc.cx + 900, esc.cy + 900), 2.0, pb)
    umbral = Puntos(esc, [tuple(v["umbral_lonlat"])], "#E11B22", tam=26, dz=3)
    salida = Lineas(esc, salida_urbana(g), "#E11B22", ancho_px=6, dz=2.0, paso=4, fuente=DTM)
    esc.dinamicos += [edif, agua, umbral, salida]
    z0, zr = v["cota_punto_bajo_m"], v["cota_rebose_m"]
    cv = v["curva"]

    def nivel(u):            # sobre el rebose el agua ya no se acumula: sale por el umbral (se dibuja la salida natural)
        if u < 0.08: return z0 - 0.05
        if u < 0.66: return z0 + (zr - z0) * suave((u - 0.08) / 0.58)
        return zr - 0.01
    pbl = v["punto_bajo_lonlat"]
    cam = Camara(esc, [(0.00, dict(lon=pbl[0] + 0.0010, lat=pbl[1] - 0.0004, dist=1150, mira=-30, elev=50, va=30)),
                       (0.62, dict(lon=pbl[0] + 0.0012, lat=pbl[1] - 0.0002, dist=950, mira=-8, elev=48, va=30)),
                       (1.00, dict(lon=pbl[0] + 0.0030, lat=pbl[1] - 0.0045, dist=1700, mira=12, elev=52, va=30))])

    def act(t, u):
        agua.poner(nivel(u)); edif.poner(1.0)
        umbral.poner(1 if u > 0.62 else 0)
        salida.poner(rampa01(u, 0.78, 0.98))
        return {"oscuro": 1, "vias": 1}

    def pista(t, u):
        n = nivel(u)
        return {"nivel_agua_m_egm2008": round(n, 2), "profundidad_max_m": round(max(n - z0, 0), 2),
                "volumen_m3": int(np.interp(n, cv[:, 0], cv[:, 1], left=0)) if n <= zr else None,
                "salida_dibujada": round(rampa01(u, 0.78, 0.98), 3), "umbral_visible": int(u > 0.62)}
    return Animacion("sc_vaso_dtm", "santa-cruz", 24, esc, cam, act, portada=0.74, vertical=dict(dist=1.55, va=44), pista=pista, bruma=14)


@anim
def sc_30oct_dtm():
    """El 30 de octubre en una toma: la lluvia medida cae en la parte alta, la crecida del modelo 2D baja por la cuenca y llena La Cascada (relieve con el DTM de 1 m)."""
    esc = Escena("santa-cruz", (-90.322, -0.705), 28000, 30000, vexag=2.2, res=30, tex_px=6,
                 parche=((-90.318, -0.722), 6500, 7500, 5, 2.0, DTM))
    g = esc.g
    cu = cuenca_cascada(g).buffer(45).buffer(-45).simplify(12)      # sin la escalera de la malla de 30 m
    capa_oscura(esc, 0.30)
    esc.capa("fuera", [cu], np.zeros(3), oscurecer_fuera=0.30)
    esc.capa("cuenca_borde", [cu], np.array([1, 1, 1]), contorno=18, alfa=0.85)
    esc.capa("edificios", edificios(g, "Santa Cruz"), hex2rgb(EDIF_OSC), sigma=0.4)
    esc.capa("barrio", [barrio_cascada(g)], np.array(ROJO) / 255, contorno=14, alfa=1.0)
    C, H, TRf, ep = modelo_sc("b_central")
    agua = AguaModelo(esc, C, H, TRf, ep, res=8.0, desfase=0.4, umbral=0.06, alfa=1.0, fuente=DTM)
    E = lluvia_estaciones(); m = Mallas()
    esc.dinamicos += [agua, m]
    ESC_H = 14.0
    hora = lambda u: 1.5 + 10.5 * float(np.clip((u - 0.03) / 0.90, 0, 1))      # 13:30 → 00:00
    cam = Camara(esc, [(0.00, dict(lon=-90.335, lat=-0.665, dist=16000, mira=-8, elev=38, va=30)),
                       (0.35, dict(lon=-90.330, lat=-0.680, dist=12500, mira=-2, elev=36, va=30)),
                       (0.70, dict(lon=-90.320, lat=-0.712, dist=6500, mira=6, elev=34, va=30)),
                       (1.00, dict(lon=-90.3140, lat=-0.7340, dist=2600, mira=10, elev=36, va=30))])

    def act(t, u):
        h = hora(u); m.limpiar()
        for nm, e in E.items():
            hh_ = 12 + h
            ac = float(np.interp(hh_, e["ts"], e["acum"], left=0)) if hh_ <= e["fin"] else float(e["acum"][-1])
            if ac <= 0.5: continue
            x, y, z = esc.loc(e["lon"], e["lat"])
            alto = ac * ESC_H; ok = hh_ <= e["fin"] + 0.05
            col = "#bdbdbd" if "Crocker" in nm else "white"
            m.poner(pv.Cylinder(center=(x, y, z + alto / 2), direction=(0, 0, 1), radius=260, height=alto, resolution=64),
                    color=col, opacity=(0.9 if ok else 0.5) * (1 - rampa01(u, 0.80, 0.92)), ambient=0.45, diffuse=0.7, specular=0.2)
        agua.poner(h)
        return {"oscuro": 1, "fuera": 1 - 0.6 * rampa01(u, 0.70, 0.90), "cuenca_borde": 1 - 0.75 * rampa01(u, 0.70, 0.90), "edificios": 1, "barrio": 1}
    return Animacion("sc_30oct_dtm", "santa-cruz", 36, esc, cam, act, portada=0.86, vertical=dict(dist=1.5, va=46),
                     pista=lambda t, u: {"hora_local_utc6": hora_sc(hora(u)).strftime("%Y-%m-%d %H:%M"), "horas_desde_12h": round(hora(u), 3)},
                     reloj=lambda t, u: hora_sc(hora(u)))


# ================================================================ principal
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("nombres", nargs="*")
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--prueba", action="store_true")
    ap.add_argument("--formato", choices=list(FORMATOS) + ["4k-ambos"])
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--prores", action="store_true", help="ProRes 422 HQ (.mov, 10 bits) para edición en lugar de H.264")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--salida", type=pathlib.Path)
    ap.add_argument("--crecimiento", action="store_true", help="procesa GHSL/WSF/OSM → datos/crecimiento_urbano/")
    a = ap.parse_args()
    FPS = a.fps; CODEC["prores"] = a.prores
    if a.crecimiento:
        crecimiento_procesar(); sys.exit(0)
    if a.lista or not a.nombres:
        for k, f in ANIMS.items(): print(f"{k:32s} {(f.__doc__ or '').strip().splitlines()[0]}")
        sys.exit(0)
    for nm in a.nombres:
        print("→", nm, flush=True); t0 = time.time()
        an = ANIMS[nm]()
        print(f"  escena lista en {time.time() - t0:.0f} s", flush=True)
        fmts = ("4k", "4k9x16") if a.formato == "4k-ambos" else (a.formato,) if a.formato else ("16x9", "9x16")
        renderizar(an, fmts, prueba=a.prueba, crf=a.crf, salida=a.salida)
