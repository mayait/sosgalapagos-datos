"""Contraste con el Plan de Acción SC-4-09-2026 (Unidad de Gestión de Riesgos del GAD San Cristóbal).

  1. Correspondencia entre las cuencas, cauces y puntos del análisis (scripts 17 y 25) y las encañadas OFICIALES del plan.
     Añade la propiedad «cañada_oficial» (y «cañada_oficial_confianza») a cuencas.geojson y puntos_inundacion.geojson y crea
     datos/cañadas_oficiales.geojson con el cauce D8 de cada encañada.
  2. Bifurcaciones: el plan dice que Divino Niño «se separa de la Galápagos» y que Alvear «recoge aguas de Divino Niño». Un D8 no
     puede bifurcar; aquí se mide la ALTURA DE DESBORDE LATERAL: para cada celda del cauce urbano A, la mínima lámina sobre el
     DSM que permite al agua llegar a la red del cauce B sin volver a pasar por A (camino de mínimo umbral, Dijkstra).
  3. Validación: calado máximo del modelo 2D (script 25) y ranking de puntos (script 17) en los sectores de máxima prioridad del plan.

Uso:  .venv/bin/python -I scripts/27_canadas_oficiales_san_cristobal.py     (después de 17 y 25; desde geodatos/)
Salidas: estudios/san-cristobal/datos/cañadas_oficiales.geojson, contraste_plan_ugr.json; actualiza cuencas.geojson y puntos_inundacion.geojson
"""
import heapq, json, math, pathlib, tempfile
import numpy as np, rasterio
from rasterio.features import rasterize
from rasterio.warp import reproject, Resampling, calculate_default_transform
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, transform as stransform
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
DAT = ROOT / "estudios/san-cristobal/datos"
M2D = DAT / "modelo2d"
DEM_CRUDO = ROOT / "descargas/dem_recortes/san_cristobal_dem.tif"
DEM_QUEMADO = ROOT / "descargas/dem_recortes/san_cristobal_dem_quemado.tif"
FUENTE = "Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal"
EPSG = 32716; CELDA = 30.0
T = Transformer.from_crs(4326, EPSG, always_xy=True).transform
TI = Transformer.from_crs(EPSG, 4326, always_xy=True).transform
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)
N8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

# ---------------------------------------------------------------- 1. correspondencia (id del script 17 → encañada oficial, confianza, motivo)
GAL, CQ, DN, ALV, PM, MZ, PA, LP, CGRS, PART = ("Galápagos / Barrio Frío", "Cerro Quemado / Don García", "Divino Niño", "Alejandro Alvear",
                                                "Playa Mann", "Manzanillo – El Manantial", "Palmeras – Arrayanes", "La Planada",
                                                "Centro de Gestión de Residuos Sólidos (CGRS)", "Parque Artesanal")
CORR = {
    "PBM-L01": (GAL, "alta", "Mayor cuenca (5,4 km²) que nace en la zona rural y llega al Malecón; el plan la describe como la principal."),
    "PBM-L02": (LP + " → " + MZ, "media", "Entra por La Planada (registro SNGR de 2025 a 210 m) y baja por El Manzanillo (registros de 2019 y 2023): "
                "el plan dice que El Manzanillo tiene «ramificaciones que bajan desde La Planada»."),
    "PBM-L03": (DN, "alta", "Desemboca en Playa de Oro (OSM), como dice el plan; pasa a 200 m del Hospital Oskar Jandl."),
    "PBM-L04": (ALV, "media", "Nace en el Parque y baja junto a la E. E. B. Alejandro Alvear (Playa Mann); alternativa: rama de Playa Mann."),
    "PBM-L05": (PM, "media", "Quebrada del campus: pasa junto a las oficinas del PNG y, en la rejilla original y en el 2D, llega a Playa Mann."),
    "PBM-L06": (CQ, "baja", "Ladera sur (Estación Terrena); según el D8 drena a Barrio Frío y no a la mina de Cerro Quemado."),
    "PBM-L07": (PA, "baja", "Llega del Parque al este, entre Las Palmeras (IGM) y la entrada de la Galápagos, y se une a ella."),
    "PBM-L08": (MZ, "media-baja", "Ramal sur que baja desde La Planada hacia El Manzanillo."),
    "PBM-L09": (MZ, "media-baja", "Ramal que baja al barrio Manzanillo (IGM) y se une a la Galápagos."),
    "PBM-L10": (CQ, "baja", "Ladera junto a las canteras de Cerro Quemado (IGM/OSM)."),
    "PBM-L11": (DN, "media", "Ramal sur de Divino Niño, junto al Colegio Ignacio Hernández y la vía Jaime Roldós."),
    "PBM-L12": (PM, "baja", "Cauce pequeño al norte de Playa Mann; puede ser otro ramal de Playa Mann."),
    "PBM-L13": (ALV, "media-baja", "Afluente del ramal de Alvear."),
    "PBM-L14": (LP, "media-baja", "Ramal alto de La Planada."),
    "PBM-S01": (GAL, "alta", "Desembocadura en Bahía Naufragio, en la playa de Barrio Frío (Poza de las Garzas)."),
    "PBM-S02": (DN, "alta", "Playa de Oro (OSM, a 60 m)."),
    "PBM-S03": (ALV, "media", "Pasa junto a la E. E. B. Alejandro Alvear y desemboca a 115 m de una pasarela de muelle (OSM)."),
    "PBM-S04": (PM, "baja", "Desemboca al norte de Playa Mann."),
    "V22": (GAL, "alta", "Boca de la Galápagos en la playa de Barrio Frío."),
    "V12": (GAL, "baja", "Zona baja del centro, entre las bocas de la Galápagos y de Divino Niño."),
    "V13": (GAL, "baja", "Zona baja del centro (registro SNGR de Barrio Frío de 2024)."),
    "V24": (GAL, "baja", "Zona baja del centro."),
    "V15": (LP, "media", "Sector La Planada (registro SNGR de 2025)."),
    "V16": (MZ, "media-baja", "Ladera de El Manzanillo (registro SNGR de 2023)."),
    "V19": (CQ, "baja", "Ladera suroeste, cerca de Estación Terrena."),
    "V21": (DN, "baja", "Ramal sur de Divino Niño."),
    "PRO-L01": (GAL + " (cabecera rural, El Progreso)", "media", "El D8 lleva esta quebrada de El Progreso a la cuenca de la Galápagos."),
    "PRO-L02": ("Recintos de El Progreso", "baja", "Ladera sur de El Progreso."),
}
for v in ("V01", "V02", "V03", "V05", "V06", "V07", "V08", "V09", "V10", "V11", "V17", "V18", "V23"):
    CORR[v] = ("El Progreso, zona urbana (cunetas y bordillos)", "media", "Depresión dentro del poblado o a menos de 100 m.")
for v in ("Z1-L01", "Z2-L01"):
    CORR[v] = ("Recintos de El Progreso: Cerro Verde", "media", "Huella edificada de Cerro Verde (IGM).")
for v in ("Z3-L01", "Z3-L02", "Z3-L03", "V04", "V14", "V20"):
    CORR[v] = ("Recintos de El Progreso", "baja", "Huella edificada al noreste de El Progreso; recinto no identificado.")

# sectores de máxima prioridad del plan (punto aproximado y radio de búsqueda)
SECTORES = {
    "Barrio Frío: playa y Poza de las Garzas": ((-89.61315, -0.90261), 150, "Boca D8 de la Galápagos (S01)"),
    "Manzanillo: desbordamiento a 100 m del puente (abr-2026)": ((-89.6058, -0.90835), 150, "Puente IGM/OSM de la vía perimetral sobre la Galápagos"),
    "Manzanillo (barrio)": ((-89.5997, -0.9106), 200, "Topónimo IGM"),
    "La Planada": ((-89.59404, -0.91131), 200, "Registro SNGR de 2025"),
    "Divino Niño: Playa de Oro (desembocadura tapada)": ((-89.60951, -0.89986), 120, "Playa de Oro (OSM)"),
    "Divino Niño: muro del Hospital Oskar Jandl": ((-89.60523, -0.89986), 100, "Hospital (OSM)"),
    "Divino Niño: Colegio Ignacio Hernández / vía Jaime Roldós": ((-89.60401, -0.90199), 100, "Colegio (OSM)"),
    "Playa Mann (rejillas, vía adoquinada, playa)": ((-89.6085, -0.8970), 200, "Barrio entre Playa Mann y la E. E. B. Alvear"),
    "Los Arrayanes / La Picada (ubicación supuesta)": ((-89.59376, -0.90805), 200, "SUPUESTA: entrada de PBM-L07; no hay topónimo cartografiado"),
    "San Francisco, Fragata y Estación Terrena": ((-89.6090, -0.9070), 250, "Panadería «Fragata» (OSM) y registros SNGR de Estación Terrena"),
}
ESCENARIOS_2D = ("scs100", "guayabillos", "guayabillos_15m")


def feats(rel):
    out = []
    for f in json.loads((ROOT / rel).read_text())["features"]:
        if f.get("geometry") and f["properties"].get("isla", "San Cristóbal") == "San Cristóbal":
            out.append((stransform(T, shape(f["geometry"])), f["properties"]))
    return out


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


def a_utm(p):
    src = rasterio.open(p)
    tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG}", src.width, src.height, *src.bounds, resolution=CELDA)
    arr = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), arr, src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs=f"EPSG:{EPSG}",
              resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    return arr, tr


R = {"fuente": FUENTE, "nota": "Fuente interna del GAD; se cita, no se reproduce."}

# ---------------------------------------------------------------- 1a. propiedad cañada_oficial en las capas del script 17
for nombre in ("cuencas.geojson", "puntos_inundacion.geojson"):
    d = json.loads((DAT / nombre).read_text())
    for f in d["features"]:
        pid = f["properties"].get("id")
        c = CORR.get(pid)
        f["properties"]["cañada_oficial"] = c[0] if c else None
        f["properties"]["cañada_oficial_confianza"] = c[1] if c else None
        f["properties"]["cañada_oficial_fuente"] = FUENTE if c else None
    (DAT / nombre).write_text(json.dumps(d, ensure_ascii=False))
R["correspondencia"] = {k: {"cañada_oficial": v[0], "confianza": v[1], "motivo": v[2]} for k, v in CORR.items()}

# ---------------------------------------------------------------- D8 (igual que el script 17)
dem, TR = a_utm(DEM_CRUDO); demq, _ = a_utm(DEM_QUEMADO)
H, W = dem.shape
sea = (dem == -9999) | (dem <= 0.5)
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td) / "q.tif"
    with rasterio.open(p, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=f"EPSG:{EPSG}", transform=TR, nodata=-9999) as d:
        d.write(np.where(sea, -9999, demq).astype("float32"), 1)
    g = Grid.from_raster(str(p)); dq = g.read_raster(str(p))
    fdir = g.flowdir(g.resolve_flats(g.fill_depressions(g.fill_pits(dq))), dirmap=DIRMAP)
    F = np.asarray(fdir); AKM = np.asarray(g.accumulation(fdir, dirmap=DIRMAP)).astype(float) * CELDA ** 2 / 1e6
AKM[sea] = 0


def rc(lon, lat):
    c, r = ~TR * T(lon, lat); return int(r), int(c)


def abajo(r, c, n=3000):
    path = [(r, c)]
    for _ in range(n):
        k = F[r, c]
        if k not in OFF: break
        a, b = OFF[k]; r, c = r + a, c + b
        path.append((r, c))
        if sea[r, c]: break
    return path


def linea(path):
    return LineString([TR * (c + .5, r + .5) for r, c in path])


# ---------------------------------------------------------------- 1b. cañadas oficiales: cauce D8 asociado
cu = json.loads((DAT / "cuencas.geojson").read_text())["features"]
lineas = {}
for f in cu:
    pid, tp = f["properties"]["id"], f["properties"]["tipo"]
    if tp in ("cauce principal (D8)", "recorrido D8 hasta el mar"):
        lineas.setdefault(pid, []).append(stransform(T, shape(f["geometry"])))
areas = {f["properties"]["id"]: f["properties"]["area_km2"] for f in cu if f["properties"]["tipo"] == "cuenca de llegada"}
OFICIALES = {
    GAL: (["PBM-L01"], "alta", "Cauce D8 principal desde la cabecera hasta la playa de Barrio Frío."),
    DN: (["PBM-L03", "PBM-L11"], "alta (salida) / media (trazado)", "El D8 le da cuenca propia (≈1 km²); el plan dice que se separa de la Galápagos."),
    ALV: (["PBM-L04", "PBM-L13"], "media", "En el D8 en UTM recoge también la quebrada del campus (Playa Mann)."),
    PM: (["PBM-L05", "PBM-L12"], "media", "Quebrada del campus y cauce pequeño del norte de Playa Mann."),
    MZ: (["PBM-L02", "PBM-L08", "PBM-L09"], "media-baja", "Ramales que bajan desde La Planada hacia El Manzanillo."),
    LP: (["PBM-L02", "PBM-L14"], "media", "Tramo alto de PBM-L02 y ramal PBM-L14."),
    PA: (["PBM-L07"], "baja", "Hipótesis: no hay topónimo «Arrayanes» ni «La Picada» cartografiado."),
    CQ: (["PBM-L06", "PBM-L10"], "baja", "El D8 no lleva estas laderas a la mina de Cerro Quemado (ver «mina»)."),
}
feats_of, R["cañadas_oficiales"] = [], {}
for nm, (ids, conf, nota) in OFICIALES.items():
    gs = [g_ for i in ids for g_ in lineas.get(i, [])]
    if not gs: continue
    u = unary_union(gs)
    props = {"cañada_oficial": nm, "ids_d8": ids, "confianza": conf, "nota": nota, "fuente_nombres": FUENTE,
             "area_d8_km2": round(max(areas.get(i, 0) for i in ids), 3), "longitud_d8_km": round(u.length / 1000, 2)}
    feats_of.append({"type": "Feature", "properties": props, "geometry": r6(u)})
    R["cañadas_oficiales"][nm] = props
# Cerro Quemado: ¿qué drena a la mina? / CGRS: ¿adónde va el agua del antiguo vertedero (IGM)?
mina = {}
for nm_, (lo, la) in {"mina Cerro Quemado (OSM)": (-89.61238, -0.91412), "cantera IGM este": (-89.61078, -0.91355), "cantera IGM oeste": (-89.61361, -0.91404)}.items():
    r, c = rc(lo, la)
    w = AKM[r - 2:r + 3, c - 2:c + 3]
    p_ = abajo(r, c)
    mina[nm_] = {"area_d8_max_60m_km2": round(float(w.max()), 3), "cota_dsm_m": round(float(dem[r, c]), 1),
                 "salida_d8_lonlat": [round(v, 5) for v in TI(*(TR * (p_[-1][1] + .5, p_[-1][0] + .5)))], "recorrido_m": round(linea(p_).length) if len(p_) > 1 else 0}
r, c = rc(-89.6090, -0.9090); p_ = abajo(r, c)
mina["recorrido D8 desde Estación Terrena"] = {"salida_lonlat": [round(v, 5) for v in TI(*(TR * (p_[-1][1] + .5, p_[-1][0] + .5)))],
                                              "pasa_a_menos_de_150m_de_la_mina": bool(linea(p_).distance(Point(T(-89.61238, -0.91412))) < 150) if len(p_) > 1 else False}
R["cerro_quemado"] = mina
r, c = rc(-89.58585, -0.90881); p_ = abajo(r, c)
lp = linea(p_)
gal = unary_union(lineas["PBM-L01"])
R["cgrs_hipotesis_vertedero_igm"] = {"punto": [-89.58585, -0.90881], "area_d8_km2": round(float(AKM[r, c]), 3),
                                    "se_une_a_la_galapagos": bool(lp.distance(gal) < 45), "recorrido_hasta_la_galapagos_m": None,
                                    "nota": "Ubicación del CGRS no confirmada: se usa el antiguo vertedero del IGM como hipótesis."}
feats_of.append({"type": "Feature", "properties": {"cañada_oficial": CGRS, "ids_d8": [], "confianza": "baja",
                                                   "nota": "Hipótesis: recorrido D8 desde el antiguo vertedero del IGM; ubicación del CGRS no confirmada.",
                                                   "fuente_nombres": FUENTE}, "geometry": r6(lp)})
R["parque_artesanal"] = "No localizado: no hay topónimo ni objeto cartografiado; queda pendiente."
(DAT / "cañadas_oficiales.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats_of}, ensure_ascii=False))
print("Cerro Quemado:", mina); print("CGRS:", R["cgrs_hipotesis_vertedero_igm"])

# ---------------------------------------------------------------- 2. bifurcaciones: altura de desborde lateral entre cauces
win = (-89.6200, -0.9180, -89.5850, -0.8920)
x0, y0 = T(*win[:2]); x1, y1 = T(*win[2:])
c0, r1 = ~TR * (x0, y0); c1, r0 = ~TR * (x1, y1)
r0, r1, c0, c1 = int(r0), int(r1) + 1, int(c0), int(c1) + 1
Z = dem[r0:r1, c0:c1].astype(float); SEA = sea[r0:r1, c0:c1]
h_, w_ = Z.shape


def red(ids, solo_recorrido=True):
    gs = []
    for f in cu:
        if f["properties"]["id"] in ids and f["properties"]["tipo"] == ("recorrido D8 hasta el mar" if solo_recorrido else f["properties"]["tipo"]):
            gs.append(stransform(T, shape(f["geometry"])))
    m = rasterize([(g_, 1) for g_ in gs], out_shape=(H, W), transform=TR, all_touched=False).astype(bool)[r0:r1, c0:c1]
    return m & ~SEA


def desborde(A_, B_):
    """Para cada celda de A: lámina mínima sobre el DSM para llegar a B sin pasar por A ni por el mar."""
    best = np.full(Z.shape, np.inf)
    hp = []
    for r, c in zip(*np.where(B_)):
        best[r, c] = Z[r, c]; hp.append((Z[r, c], r, c))
    heapq.heapify(hp)
    libre = ~SEA & ~A_
    while hp:
        e, r, c = heapq.heappop(hp)
        if e > best[r, c]: continue
        for a, b in N8:
            r2, c2 = r + a, c + b
            if 0 <= r2 < h_ and 0 <= c2 < w_ and libre[r2, c2]:
                e2 = max(e, Z[r2, c2])
                if e2 < best[r2, c2]:
                    best[r2, c2] = e2; heapq.heappush(hp, (e2, r2, c2))
    out = []
    for r, c in zip(*np.where(A_)):
        vec = [best[r + a, c + b] for a, b in N8 if 0 <= r + a < h_ and 0 <= c + b < w_ and not A_[r + a, c + b]]
        sp = max(min(vec), Z[r, c]) if vec else np.inf
        out.append((sp - Z[r, c], r, c))
    out.sort()
    return out


from scipy import ndimage
DMAR = ndimage.distance_transform_edt(~SEA) * CELDA
DMAR_MIN = 200          # se excluye la franja costera (≤ 200 m del mar), donde todas las bocas se conectan por la playa
rr_all, cc_all = np.indices((H, W))
_nr, _nc = rr_all.copy(), cc_all.copy()
for k, (a, b) in OFF.items():
    m_ = F == k; _nr[m_] += a; _nc[m_] += b
_ok = (_nr >= 0) & (_nr < H) & (_nc >= 0) & (_nc < W) & np.isin(F, list(OFF)) & ~sea
NXT = (np.where(_ok, _nr, rr_all) * W + np.where(_ok, _nc, cc_all)).ravel()


def cuenca_de(lonlats):
    """Celdas cuyo flujo D8 pasa por alguno de los puntos (cuenca vertiente a esas salidas), recortada a la ventana."""
    NN = H * W; mask = np.zeros(NN, bool)
    for lo, la in lonlats:
        r, c = rc(lo, la); mask[r * W + c] = True
    tg = np.where(mask, np.arange(NN), -1); jj = NXT.copy()
    for _ in range(int(np.ceil(np.log2(NN))) + 1):
        un = tg == -1; tg[un] = tg[jj[un]]; jj = jj[jj]
    return ((tg >= 0).reshape(H, W) & ~sea)[r0:r1, c0:c1]


SALIDAS = {"Galápagos": [(-89.61315, -0.90234)], "Divino Niño": [(-89.60965, -0.89936)], "Alvear": [(-89.60965, -0.89800)]}
CUENCAS = {k: cuenca_de(v) for k, v in SALIDAS.items()}
REDES = {"Galápagos": ["PBM-L01", "PBM-L02"], "Divino Niño": ["PBM-L03", "PBM-L11"], "Alvear": ["PBM-L04", "PBM-L05"]}


def muestra_tif(f, lo, la, r=2):
    if not f.exists(): return None
    with rasterio.open(f) as src:
        a = src.read(1); c, rr_ = ~src.transform * T(lo, la); rr_, c = int(rr_), int(c)
        w = a[max(rr_ - r, 0):rr_ + r + 1, max(c - r, 0):c + r + 1]
        return round(float(max(w.max(), 0)), 2)


def resumen_desborde(nombre, A_nm, B_nm):
    """Aproximación mínima entre los cauces urbanos A y B fuera de la franja costera, y perfil recto del DSM entre ambos:
    el «resalte» es lo que el terreno sube por encima del lecho de A antes de bajar a B. Se añade el calado máximo del 2D y la
    lámina máxima de agua marcada (trazadores) en el punto de A."""
    A_ = red(REDES[A_nm]) & (DMAR > DMAR_MIN); B_ = red(REDES[B_nm]) & ~red(REDES[A_nm]) & (DMAR > DMAR_MIN)
    ra, ca = np.where(A_); rb, cb = np.where(B_)
    d = np.hypot(ra[:, None] - rb[None, :], ca[:, None] - cb[None, :])
    i, j = np.unravel_index(np.argmin(d), d.shape)
    n_ = max(int(d[i, j] * 4), 4)
    z_ = ndimage.map_coordinates(Z, [np.linspace(ra[i], rb[j], n_), np.linspace(ca[i], cb[j], n_)], order=1)
    lo, la = TI(*(TR * (ca[i] + c0 + .5, ra[i] + r0 + .5)))
    lo2, la2 = TI(*(TR * (cb[j] + c0 + .5, rb[j] + r0 + .5)))
    out = {"distancia_entre_cauces_m": round(float(d[i, j] * CELDA)), "punto_cauce_origen_lonlat": [round(lo, 5), round(la, 5)],
           "punto_cauce_destino_lonlat": [round(lo2, 5), round(la2, 5)], "cota_origen_dsm_m": round(float(Z[ra[i], ca[i]]), 1),
           "cota_destino_dsm_m": round(float(Z[rb[j], cb[j]]), 1), "resalte_sobre_el_lecho_de_origen_m": round(float(max(0.0, z_.max() - Z[ra[i], ca[i]])), 1),
           "calado_max_2d_en_origen_m": {e: muestra_tif(M2D / f"{e}_calado_max.tif", lo, la) for e in ("scs100", "guayabillos_15m")},
           "agua_marcada_max_en_destino_m": {e: muestra_tif(M2D / f"{e}_agua_marcada_max.tif", lo2, la2) for e in ("traz_galapagos_15m", "traz_divinonino_15m")}}
    R.setdefault("bifurcaciones", {})[nombre] = out
    print(nombre, out)


resumen_desborde("Galápagos → Divino Niño", "Galápagos", "Divino Niño")
resumen_desborde("Galápagos → Alvear", "Galápagos", "Alvear")
resumen_desborde("Divino Niño → Alvear", "Divino Niño", "Alvear")
resumen_desborde("Alvear → Divino Niño", "Alvear", "Divino Niño")
R["bifurcaciones_nota"] = (f"Fuera de la franja costera (≤ {DMAR_MIN} m del mar), donde todas las bocas se conectan por la playa. Resalte: lo que sube el DSM "
                           "sobre el lecho del cauce de origen en la recta hasta el cauce de destino. Si es menor que el calado de crecida más el error del "
                           "DSM (±2–4 m), la bifurcación por desborde es topográficamente posible.")
# perfil de la vía perimetral Jaime Roldós entre el puente sobre la Galápagos y el hospital (¿lleva agua de la Galápagos a Divino Niño?)
from shapely.ops import linemerge
jr = linemerge(unary_union([g_ for g_, p_ in feats("export/galapagos/vias.geojson") if "Roldós" in str(p_.get("nombre"))]))
perf = []
for g_ in getattr(jr, "geoms", [jr]):
    if g_.distance(Point(T(-89.6058, -0.90835))) < 80 or g_.distance(Point(T(-89.60523, -0.89986))) < 150:
        for d_ in np.arange(0, g_.length + 1, 75):
            q_ = g_.interpolate(d_); lo, la = TI(q_.x, q_.y); c_, r_ = ~TR * (q_.x, q_.y)
            perf.append([round(lo, 5), round(la, 5), round(float(ndimage.map_coordinates(dem, [[r_ - .5], [c_ - .5]], order=1)[0]), 1)])
perf.sort(key=lambda x: x[1])
R["perfil_via_jaime_roldos_sur_a_norte"] = {"nota": "lon, lat, cota DSM (m), de sur (puente sobre la Galápagos, −0,9084) a norte (hospital, −0,8999)",
                                           "puntos": [x for x in perf if -0.9090 <= x[1] <= -0.8995]}

# ---------------------------------------------------------------- 3. validación con el 2D y el ranking
pts = [(stransform(T, shape(f["geometry"])), f["properties"]) for f in json.loads((DAT / "puntos_inundacion.geojson").read_text())["features"]]
edif = feats("capas/final/edificios_exposicion.geojson")
r2d = json.loads((M2D / "resumen_modelo2d.json").read_text())
val = {}
for nm, ((lo, la), rad, ref) in SECTORES.items():
    pt = Point(T(lo, la)); zona = pt.buffer(rad)
    cerca = sorted([(p_.get("ranking") or 999, p_["id"], p_["tipo"]) for g_, p_ in pts if g_.distance(pt) <= rad])
    fila = {"referencia_ubicacion": ref, "radio_m": rad,
            "puntos_del_ranking_cercanos": [{"ranking": a if a < 999 else None, "id": b, "tipo": c_} for a, b, c_ in cerca[:4]]}
    for esc in ESCENARIOS_2D:
        f_ = M2D / f"{esc}_calado_max.tif"
        if not f_.exists(): continue
        with rasterio.open(f_) as src:
            hm = src.read(1); trm = src.transform
        mk = rasterize([(zona, 1)], out_shape=hm.shape, transform=trm).astype(bool) & (hm > -9000)
        if not mk.any(): continue
        ne = 0; ntot = 0
        for gb, _ in edif:
            if gb.centroid.distance(pt) > rad: continue
            ntot += 1
            c, r = ~trm * gb.centroid.coords[0]
            if 0 <= int(r) < hm.shape[0] and 0 <= int(c) < hm.shape[1] and hm[int(r), int(c)] >= 0.3: ne += 1
        fila[esc] = {"calado_max_m": round(float(hm[mk].max()), 2), "area_calado_>=0.3m_ha": round(float((hm[mk] >= 0.3).sum() * trm.a ** 2 / 1e4), 2),
                     "edificios_con_calado_>=0.3m": ne, "edificios_en_el_radio": ntot}
    q = r2d["escenarios"].get("guayabillos_15m", {}).get("puntos", {})
    val[nm] = fila
    print(nm, {k: v for k, v in fila.items() if k in ESCENARIOS_2D}, fila["puntos_del_ranking_cercanos"][:2])
R["validacion_sectores_plan"] = val
for k in ("traz_galapagos_15m", "traz_divinonino_15m", "traz_galapagos_100mm_15m"):
    if k in r2d.get("escenarios", {}):
        R.setdefault("trazadores_2d", {})[k] = r2d["escenarios"][k]["salidas_al_mar"]
(DAT / "contraste_plan_ugr.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("Listo")
