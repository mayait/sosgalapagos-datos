"""Estudio hidrológico preliminar del barrio La Cascada (Puerto Ayora, Santa Cruz).

Reúne en un solo proceso reproducible:
  1. Cuenca que drena hacia el barrio (D8 sobre Copernicus GLO-30 con quebradas IGM quemadas), separada
     en las dos ramas principales y la escorrentía local; cauce principal y su perfil.
  2. Secciones transversales N-S y E-O por el centro del barrio (±600 m).
  3. Depresión de La Cascada: curva cota-área-volumen y manchas de llenado tipo «bathtub» (todas las celdas
     por debajo de la cota h conectadas en 8 vecinos con el punto más bajo del barrio, dentro de un radio
     RADIO_MANCHA_M). No es un modelo hidráulico: no hay caudal, tiempo ni pérdidas.
  4. Búsqueda de corredores de desvío por gravedad hacia el mar sin cruzar zonas pobladas.
  5. Hidrogramas preliminares SCS-CN + hidrograma unitario adimensional SCS: tormentas SCS tipo II de 24 h y escenario
     del evento del 31-oct-2026 con el hietograma horario ECMWF (estudios/la-cascada/datos/lluvia_evento_ecmwf_horaria.csv).
  6. Salida natural por rebose (camino de mínimo umbral hasta el mar).
  7. Perfil del cauce OSM al pie del escarpe hacia el este (perfil_cauce_este.csv).
  8. Contraste del DSM con los puntos acotados IGM 1:25 000.

Uso:  .venv/bin/python -I scripts/12_cascada_analisis.py   (después de 03, 06, 07 y 08)
Salidas: estudios/la-cascada/datos/

Limitación principal: el DEM es un modelo digital de SUPERFICIE de 30 m (incluye vegetación y edificios,
error vertical del orden de ±2–4 m). Todas las cifras son de orden de magnitud para priorizar estudios.
"""
import csv, heapq, json, math, pathlib, tempfile
import numpy as np, rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy import ndimage
from shapely.geometry import shape, mapping, LineString, Point
from shapely.ops import unary_union, transform as stransform
from shapely.strtree import STRtree
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "estudios/la-cascada/datos"
DEM_CRUDO = ROOT / "descargas/dem_recortes/santa_cruz_dem.tif"
DEM_QUEMADO = ROOT / "descargas/dem_recortes/santa_cruz_dem_quemado.tif"

# ---------------------------------------------------------------- parámetros
EPSG_UTM = 32715            # UTM 15S
CELDA = 30.0                # m
RADIO_MANCHA_M = 600        # ventana de las manchas de llenado alrededor del centroide del barrio
COTAS_CURVA = np.arange(11.0, 20.01, 0.5)
COTAS_MANCHA = (13, 14, 15, 16)
SECCION_SEMI_M = 600; SECCION_OFFSETS_M = (-150, 0, 150); SECCION_PASO_M = 30
# desvío
PENDIENTE_MIN = 0.005       # 0,5 %
CORTES_MAX_M = (3.0, 6.0)   # excavación máxima admitida bajo el terreno (rasante del canal, sin calado)
RELLENO_MAX_M = 1.0         # la rasante puede ir hasta 1 m sobre el terreno (terraplén pequeño)
COTAS_TOMA = (20, 30, 40, 60, 80, 120)
BUFFER_POBLADO_M = 30
LON_OESTE, LON_ESTE = -90.318, -90.303   # salida al mar: oeste / frente urbano / este
RUTA_PRINCIPAL = ("rama 2", 40, 3.0, "ESTE")  # interceptor documentado en perfil_interceptor_este.csv
# hidrología
LLUVIAS_MM = (50, 100, 150, 200)          # lluvia total en 24 h
CN_ESCENARIOS = (60, 70, 80)
LLUVIA_EVENTO_MM = None                   # lluvia del evento (mm en 24 h) para una tormenta tipo II; None = usar el hietograma de EVENTO_CSV
EVENTO_CSV = OUT / "lluvia_evento_ecmwf_horaria.csv"   # hietograma horario modelado (Open-Meteo, ECMWF IFS); columnas costa_*/alta_*
EVENTO_INICIO = "2026-10-30T23:00"        # la lluvia de la etiqueta hh:00 cae en la hora anterior (convención Open-Meteo)
EVENTO_HORAS = 24                         # 31-oct-2026 (etiquetas 00:00–23:00), igual que el total diario de Open-Meteo
DESFASE_A_GALAPAGOS_H = -1                # las etiquetas se pidieron en America/Guayaquil (UTC-5); Galápagos es UTC-6
PUNTO_COSTA = (-90.28259, -0.73814)       # centro de la celda ECMWF IFS 9 km devuelta para «puerto_ayora» (JSON de Open-Meteo)
PUNTO_ALTA = (-90.35294, -0.66784)        # centro de la celda ECMWF IFS 9 km devuelta para «bellavista» y «santa_rosa»
CN_EVENTO = ("AMC_II_III", "AMC_III", "AMC_II")   # central: intermedio II–III (criterio de 5 días ambiguo); sensibilidad: III y II
LLUVIA_DIARIA_CSV = OUT / "lluvia_modelos_diaria.csv"   # lluvia diaria de modelos (Open-Meteo), costa/alta, 15-oct a 1-nov
AMC_UMBRALES_MM = {"estacion_de_crecimiento": (35.6, 53.3), "estacion_latente": (12.7, 27.9)}   # SCS (NEH-4): lluvia de 5 días previos
RESGUARDO_M = 0.5
OBS_LAMINA_M = (1.5, 2.0); OBS_FONDO_M = (10.5, 11.0)   # prensa: agua «hasta dos metros» (por validar)
VERTEDERO_C = 1.7; VERTEDERO_L_M = (30, 100, 300)       # vertedero de cresta ancha en el umbral de rebose (longitud efectiva supuesta)
# --- evento MEDIDO 30-oct-2026 (red IERSE-WSN, Universidad del Azuay; hora de Galápagos UTC-6; registros ~5 min)
IERSE_CSV = OUT / "lluvia_ierse_30oct_5min.csv"         # copia de clima/datos/ierse-wsn/serie_5min.csv.gz (30–31 oct)
IERSE_EST = OUT / "estaciones_ierse.geojson"
MEDIDO_INICIO = "2026-10-30T00:00"; MEDIDO_HORAS_SIM = 48
COTA_G, COTA_SR = 178.0, 416.0                          # Los Guayabillos y Santa Rosa (altitud DEM de la red)
CONTINUACION_MIN = 30                                   # sensibilidad: la lluvia siguió tras el corte de transmisión (~21:30)
ARF = 0.85                                              # factor de reducción areal (TP-29: ~0,85–0,90 para 1–3 h y ~40 km²): cota inferior
IERSE_DIARIO = OUT / "lluvia_ierse_diaria.csv"          # copia de clima/datos/ierse-wsn/diario.csv (23-abr a 2-nov-2026)
L_ROUTING_M = (100, 300, 1000)                          # longitud efectiva del frente de desborde para el tránsito por el vaso
HITOS_CSV = ROOT / "estudios/santa-cruz/datos/hitos_hidrologicos.csv"
DT_H = 1 / 6                              # paso de 10 min
DURACION_SIM_H = 48
IA_RATIO = 0.2                            # abstracción inicial Ia = 0,2 S (TR-55)
CN_CLASE = {"parque (lava, suelo somero)": 55, "zona agrícola (suelos más profundos, pastos)": 76, "urbano": 90}
MANNING_N = 0.035; CANAL_TALUD = 1.0; CANAL_CALADO_M = 2.5

T = Transformer.from_crs(4326, EPSG_UTM, always_xy=True).transform
TI = Transformer.from_crs(EPSG_UTM, 4326, always_xy=True).transform
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)


def _fix(g):
    return g.buffer(0) if g.geom_type.endswith("Polygon") else g      # buffer(0) solo repara polígonos (vacía las líneas)


def feats(rel, cond=lambda p: True):
    return [(stransform(T, _fix(shape(f["geometry"]))), f["properties"])
            for f in json.loads((ROOT / rel).read_text())["features"]
            if f["properties"].get("isla", "Santa Cruz") == "Santa Cruz" and cond(f["properties"])]


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


def fc(features):
    return {"type": "FeatureCollection", "features": features}


def guardar_json(nombre, obj):
    (OUT / nombre).write_text(json.dumps(obj, ensure_ascii=False, indent=1 if nombre == "resumen.json" else None))


def guardar_csv(nombre, cab, filas):
    with open(OUT / nombre, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(filas)


def lonlat(r, c):
    return TI(*(TR * (c + 0.5, r + 0.5)))


def a_utm(src_path):
    src = rasterio.open(src_path)
    tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG_UTM}", src.width, src.height, *src.bounds, resolution=CELDA)
    arr = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), arr, src_transform=src.transform, src_crs=src.crs, dst_transform=tr,
              dst_crs=f"EPSG:{EPSG_UTM}", resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    return arr, tr


OUT.mkdir(parents=True, exist_ok=True)
R = {"metodo": {}, "parametros": {}}
R["parametros"] = {"dem": "Copernicus GLO-30 (DSM) reproyectado a UTM 15S, 30 m, bilineal",
                   "pendiente_min_canal": PENDIENTE_MIN, "cortes_max_m": CORTES_MAX_M, "relleno_max_m": RELLENO_MAX_M,
                   "buffer_poblado_m": BUFFER_POBLADO_M, "radio_mancha_m": RADIO_MANCHA_M, "lluvia_evento_mm": LLUVIA_EVENTO_MM}

# ---------------------------------------------------------------- 0. DEM y barrio
dem, TR = a_utm(DEM_CRUDO)
demq, _ = a_utm(DEM_QUEMADO)
H, W = dem.shape
nod = dem == -9999
sea = nod | (dem <= 0.5)
casc = unary_union([g for g, _ in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("nombre") == "La Cascada")] +
                   [g for g, _ in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") == "LA CASCADA")])
mask = rasterize([(casc, 1)], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool)
cx, cy = casc.centroid.coords[0]
dist_mar = ndimage.distance_transform_edt(~sea) * CELDA
R["barrio"] = {"area_ha": round(casc.area / 1e4, 2), "centroide_lonlat": [round(v, 5) for v in TI(cx, cy)],
               "cota_min_m": round(float(dem[mask].min()), 2), "cota_mediana_m": round(float(np.median(dem[mask])), 2),
               "cota_max_m": round(float(dem[mask].max()), 2),
               "dist_mar_m": [round(float(dist_mar[mask].min())), round(float(dist_mar[mask].max()))],
               "poligono": "unión de OSM «La Cascada» (zonas_pobladas) y CGREG «LA CASCADA» (barrios)"}
anillo = ndimage.binary_dilation(mask, iterations=10) & ~mask & ~nod
R["barrio"]["cota_mediana_anillo_300m"] = round(float(np.median(dem[anillo])), 2)
print("Barrio:", R["barrio"])

# ---------------------------------------------------------------- 1. flujo D8 y cuenca
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td)
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=f"EPSG:{EPSG_UTM}", transform=TR, nodata=-9999)
    for n, a in (("q.tif", demq), ("c.tif", dem)):
        with rasterio.open(p / n, "w", **prof) as d: d.write(a, 1)
    g = Grid.from_raster(str(p / "q.tif")); dq = g.read_raster(str(p / "q.tif"))
    fdir = g.flowdir(g.resolve_flats(g.fill_depressions(g.fill_pits(dq))), dirmap=DIRMAP)
    F = np.asarray(fdir); A = np.asarray(g.accumulation(fdir, dirmap=DIRMAP))
    g2 = Grid.from_raster(str(p / "c.tif")); dc_ = g2.read_raster(str(p / "c.tif"))
    lleno = np.asarray(g2.fill_depressions(g2.fill_pits(dc_)))
    F_crudo = np.asarray(g2.flowdir(g2.resolve_flats(g2.fill_depressions(g2.fill_pits(dc_))), dirmap=DIRMAP))   # sensibilidad sin quemar
rr, cc = np.indices((H, W))


def aguas_arriba(Fx):
    """Celdas (fuera del barrio) cuyo flujo D8 llega al barrio, por salto de punteros."""
    nr_, nc_ = rr.copy(), cc.copy()
    for k_, (a_, b_) in OFF.items():
        m_ = Fx == k_; nr_[m_] += a_; nc_[m_] += b_
    ok_ = (nr_ >= 0) & (nr_ < H) & (nc_ >= 0) & (nc_ < W) & np.isin(Fx, list(OFF)) & ~nod
    nx_ = (np.where(ok_, nr_, rr) * W + np.where(ok_, nc_, cc)).ravel()
    tg = np.where(mask.ravel(), np.arange(H * W), -1); jj = nx_.copy()
    for _ in range(int(np.ceil(np.log2(H * W))) + 1):
        un_ = tg == -1; tg[un_] = tg[jj[un_]]; jj = jj[jj]
    return ((tg >= 0) & ~mask.ravel()).reshape(H, W)

nr, nc = rr.copy(), cc.copy()
for k, (a, b) in OFF.items():
    m = F == k; nr[m] += a; nc[m] += b
ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W) & np.isin(F, list(OFF)) & ~nod
nr = np.where(ok, nr, rr); nc = np.where(ok, nc, cc)
nxt = (nr * W + nc).ravel()
N = H * W
# salto de punteros: primera celda del barrio aguas abajo
target = np.where(mask.ravel(), np.arange(N), -1)
j = nxt.copy()
for _ in range(int(np.ceil(np.log2(N))) + 1):
    un = target == -1; target[un] = target[j[un]]; j = j[j]
up = ((target >= 0) & ~mask.ravel()).reshape(H, W)
# celdas de entrada: fuera del barrio, con la siguiente dentro
entrada = up & mask.ravel()[nxt].reshape(H, W)
eid = np.zeros(N, np.int32); er, ec = np.where(entrada); eid[er * W + ec] = np.arange(1, len(er) + 1)
# cada celda aguas arriba hereda la entrada por la que llega primero al barrio
lab = eid.copy(); j = nxt.copy()
upf = up.ravel()
for _ in range(int(np.ceil(np.log2(N))) + 1):
    un = upf & (lab == 0); lab[un] = lab[j[un]]; j = j[j]
lab = np.where(upf, lab, 0).reshape(H, W)
ids, cnt = np.unique(lab[lab > 0], return_counts=True)
orden = ids[np.argsort(-cnt)]
ramas = {}
pend = np.hypot(*np.gradient(np.where(nod, np.nan, dem), CELDA)) * 100
for i, e in enumerate(orden[:2]):
    ramas[f"rama {i + 1}"] = int(e)
sub = np.zeros((H, W), np.uint8)
sub[up] = 3
for i, (nm, e) in enumerate(ramas.items()):
    sub[lab == e] = i + 1
area_up = up.sum() * CELDA ** 2 / 1e6
R["cuenca"] = {"area_aportante_km2": round(area_up, 2), "area_total_con_barrio_km2": round((up | mask).sum() * 900 / 1e6, 2),
               "cota_max_m": round(float(dem[up].max()), 1), "pendiente_media_pct": round(float(np.nanmean(pend[up])), 1),
               "pendiente_mediana_pct": round(float(np.nanmedian(pend[up])), 1),
               "fraccion_en_depresiones_rellenadas_>1m": round(float((up & (lleno - dem > 1)).sum() / up.sum()), 4),
               "metodo": "D8 (pysheds) sobre DSM con quebradas IGM quemadas, depresiones rellenadas y planos resueltos"}
up_crudo = aguas_arriba(F_crudo)
R["cuenca"]["sensibilidad_sin_quemar"] = {"area_aportante_km2": round(up_crudo.sum() * 900 / 1e6, 2),
                                          "celdas_comunes_km2": round((up_crudo & up).sum() * 900 / 1e6, 2),
                                          "solo_quemado_km2": round((up & ~up_crudo).sum() * 900 / 1e6, 3),
                                          "solo_sin_quemar_km2": round((up_crudo & ~up).sum() * 900 / 1e6, 3)}
cfeats = []
for v, nm in [(1, "rama 1"), (2, "rama 2"), (3, "escorrentía local")]:
    m = sub == v
    if not m.any(): continue
    geom = unary_union([shape(s) for s, _ in shapes(m.astype("uint8"), mask=m, transform=TR)])
    props = {"subcuenca": nm, "area_km2": round(m.sum() * 900 / 1e6, 2), "cota_max_m": round(float(dem[m].max()), 1),
             "cota_min_m": round(float(dem[m].min()), 1), "pendiente_media_pct": round(float(np.nanmean(pend[m])), 1)}
    if nm in ramas:
        r0, c0 = er[ramas[nm] - 1], ec[ramas[nm] - 1]
        props["entrada_lonlat"] = [round(x, 5) for x in lonlat(r0, c0)]
        props["cota_entrada_m"] = round(float(dem[r0, c0]), 1)
        gx, gy = geom.centroid.coords[0]
        az = (math.degrees(math.atan2(gx - cx, gy - cy)) + 360) % 360
        props["rumbo_desde_barrio"] = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][int((az + 22.5) // 45) % 8]
    cfeats.append({"type": "Feature", "properties": props, "geometry": r6(geom)})
    R["cuenca"][nm] = props
guardar_json("cuenca_cascada.geojson", fc(cfeats))
print("Cuenca:", R["cuenca"])

# cauces principales: desde la entrada de cada rama, aguas arriba por la celda de mayor acumulación
def cauce(r, c):
    path = [(r, c)]
    while True:
        best, ba = None, -1
        for k, (a, b) in OFF.items():
            ur, uc = r - a, c - b
            if 0 <= ur < H and 0 <= uc < W and F[ur, uc] == k and A[ur, uc] > ba:
                best, ba = (ur, uc), A[ur, uc]
        if best is None: break
        r, c = best; path.append(best)
    return path[::-1]          # de la cabecera a la entrada

perfil, lfeats = [], []
for nm, e in ramas.items():
    path = cauce(er[e - 1], ec[e - 1])
    d = np.concatenate([[0], np.cumsum([CELDA * math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1)])])
    L = float(d[-1]); zt, zb = float(dem[path[0]]), float(dem[path[-1]]); S = (zt - zb) / L
    tc_kirpich_h = 0.0195 * L ** 0.77 * S ** -0.385 / 60
    tc_temez_h = 0.3 * ((L / 1000) / S ** 0.25) ** 0.76
    props = {"rama": nm, "longitud_km": round(L / 1000, 2), "cota_cabecera_m": round(zt, 1), "cota_entrada_m": round(zb, 1),
             "pendiente_media_pct": round(S * 100, 2), "tc_kirpich_h": round(tc_kirpich_h, 2), "tc_temez_h": round(tc_temez_h, 2)}
    R["cuenca"][f"cauce_{nm}"] = props
    lfeats.append({"type": "Feature", "properties": props, "geometry": r6(LineString([TR * (c + .5, r + .5) for r, c in path]))})
    for (r, c), dd in zip(path, d):
        perfil.append([nm, round(float(dd)), round(float(dem[r, c]), 2), round(float(demq[r, c]), 2), round(float(A[r, c]) * 900 / 1e6, 3),
                       *[round(v, 6) for v in lonlat(r, c)]])
guardar_json("cauce_principal.geojson", fc(lfeats))
guardar_csv("perfil_cauce.csv", ["rama", "distancia_m", "cota_m", "cota_dem_quemado_m", "area_acumulada_km2", "lon", "lat"], perfil)
CAUCE = R["cuenca"]["cauce_rama 1"]
R["cuenca"]["nota_cauces"] = ("Las dos ramas miden ~13,0 km por coincidencia geométrica: ambas nacen en la divisoria de la cumbre "
                              "(cabeceras distintas, a 773 y 806 m, y trazas distintas); no es un error de cálculo.")
print("Cauce principal:", CAUCE)

# ---------------------------------------------------------------- 2. secciones transversales
def muestrear(xs, ys):
    cols, rows = ~TR * (np.asarray(xs), np.asarray(ys))
    z = ndimage.map_coordinates(np.where(nod, np.nan, dem), [rows - 0.5, cols - 0.5], order=1, mode="nearest")
    return z
sec = []
s = np.arange(-SECCION_SEMI_M, SECCION_SEMI_M + 1, SECCION_PASO_M)
for o in SECCION_OFFSETS_M:
    for nombre, xs, ys in ((f"N-S x{o:+d}m", np.full(s.shape, cx + o), cy - s),     # distancia + hacia el sur
                           (f"E-O y{o:+d}m", cx - s, np.full(s.shape, cy + o))):    # distancia + hacia el oeste
        z = muestrear(xs, ys)
        for dd, x, y, zz in zip(s, xs, ys, z):
            lo, la = TI(x, y)
            sec.append([nombre, int(dd), round(lo, 6), round(la, 6), round(float(zz), 2)])
guardar_csv("secciones_barrio.csv", ["perfil", "distancia_m", "lon", "lat", "cota_m"], sec)
R["secciones"] = {"nota": "N-S: distancia negativa = norte; E-O: distancia negativa = este. Interpolación bilineal del DSM.",
                  "N-S centro": [r[4] for r in sec if r[0] == "N-S x+0m"][::4], "E-O centro": [r[4] for r in sec if r[0] == "E-O y+0m"][::4]}

# ---------------------------------------------------------------- 3. depresión, curva cota-volumen y manchas
prof_dep = lleno - dem; prof_dep[nod] = 0
lbl_dep, _ = ndimage.label(prof_dep > 0.3)
deps = []
for i in np.unique(lbl_dep[mask & (lbl_dep > 0)]):
    m = lbl_dep == i
    deps.append({"area_ha": round(m.sum() * 900 / 1e4, 2), "prof_max_m": round(float(prof_dep[m].max()), 2),
                 "volumen_m3": int(prof_dep[m].sum() * 900), "cota_rebose_m": round(float(lleno[m].max()), 2),
                 "fraccion_dentro_barrio": round(float((m & mask).sum() / m.sum()), 2)})
r_lo, c_lo = np.argwhere(mask)[np.argmin(np.where(mask, dem, np.inf)[mask])]
cota_rebose = float(lleno[r_lo, c_lo])
R["depresion"] = {"punto_bajo_lonlat": [round(v, 5) for v in lonlat(r_lo, c_lo)], "cota_punto_bajo_m": round(float(dem[r_lo, c_lo]), 2),
                  "cota_rebose_m": round(cota_rebose, 2), "depresiones_dsm": deps,
                  "volumen_total_depresiones_m3": int(sum(d["volumen_m3"] for d in deps)),
                  "area_total_depresiones_ha": round(sum(d["area_ha"] for d in deps), 2)}
ventana = (np.hypot(*(np.array(TR * (cc + .5, rr + .5)) - np.array([cx, cy])[:, None, None])) <= RADIO_MANCHA_M) & ~nod
borde = ventana & ~ndimage.binary_erosion(ventana)
edif = feats("capas/final/edificios_exposicion.geojson")
t_edif = STRtree([g for g, _ in edif])
manz = feats("capas/final/manzanas_inec.geojson")
t_manz = STRtree([g for g, _ in manz])


def exposicion(geom):
    ne = len(t_edif.query(geom, predicate="intersects"))
    pob = viv = 0.0
    for i in t_manz.query(geom, predicate="intersects"):
        gm, pm = manz[i]
        fr = gm.intersection(geom).area / gm.area if gm.area else 0
        pob += fr * (pm.get("pob_estimada") or 0); viv += fr * (pm.get("viviendas") or 0)
    return ne, pob, viv


ne_b, pob_b, viv_b = exposicion(casc)
R["barrio"].update({"edificios_en_poligono": ne_b, "poblacion_estimada_manzanas": round(pob_b), "viviendas_manzanas": round(viv_b)})
curva, manchas = [], {}
for h in COTAS_CURVA:
    lab_h, _ = ndimage.label((dem <= h) & ventana, structure=np.ones((3, 3)))
    if dem[r_lo, c_lo] > h:
        curva.append([h, 0, 0, 0, 0, 0, False, False]); continue
    m = lab_h == lab_h[r_lo, c_lo]
    geom = unary_union([shape(s_) for s_, _ in shapes(m.astype("uint8"), mask=m, transform=TR)])
    ne, pob, viv = exposicion(geom)
    vol = float(((h - dem) * m).sum() * 900)
    abierta = bool((m & borde).any())
    curva.append([round(float(h), 1), int(m.sum() * 900), int(vol), ne, round(pob), round(viv), bool(h > cota_rebose), abierta])
    if h in COTAS_MANCHA:
        manchas[int(h)] = {"type": "Feature", "geometry": r6(geom), "properties": {
            "cota_m": float(h), "area_m2": int(m.sum() * 900), "volumen_m3": int(vol), "edificios": ne, "poblacion_estimada": round(pob),
            "sobre_cota_rebose": bool(h > cota_rebose), "toca_borde_ventana": abierta,
            "metodo": f"Llenado tipo bathtub: celdas del DSM con cota <= {h} m conectadas (8 vecinos) con el punto bajo del barrio, "
                      f"dentro de {RADIO_MANCHA_M} m del centroide. Sin hidráulica. Por encima de la cota de rebose ({cota_rebose:.2f} m) "
                      f"no es un volumen almacenado: solo describe qué quedaría bajo esa lámina si la salida estuviera obstruida o en remanso."}}
guardar_csv("curva_cota_volumen.csv", ["cota_m", "area_inundada_m2", "volumen_m3", "edificios_afectados", "poblacion_estimada",
                                       "viviendas_estimadas", "sobre_cota_rebose", "toca_borde_ventana"], curva)
for h, ft in manchas.items():
    guardar_json(f"mancha_{h}m.geojson", fc([ft]))
R["depresion"]["curva_resumen"] = {str(c[0]): {"area_m2": c[1], "volumen_m3": c[2], "edificios": c[3], "poblacion": c[4]} for c in curva if c[0] in (12.5, 13, 13.5, 14, 15, 16)}
print("Depresión:", {k: v for k, v in R["depresion"].items() if k != "curva_resumen"})
# vaso cerrado hasta el rebose. Se define sin umbral de profundidad (prof > 1 mm); el único parámetro que lo cambia es la
# conectividad: con 8 vecinos se unen dos pozas por un paso diagonal a ~12,85 m que el DSM de 30 m no resuelve.
ESTR = {8: np.ones((3, 3)), 4: None}


def edif_centroide(geom):
    return sum(1 for i in t_edif.query(geom) if geom.contains(edif[i][0].centroid))


vaso = {}
for k_, st_ in ESTR.items():
    lb0, _ = ndimage.label(prof_dep > 0.001, structure=st_)
    m0 = lb0 == lb0[r_lo, c_lo]
    g0 = unary_union([shape(s_) for s_, _ in shapes(m0.astype("uint8"), mask=m0, transform=TR)])
    ne_i, pob0, viv0 = exposicion(g0)
    vaso[k_] = {"area_ha": round(m0.sum() * 900 / 1e4, 2), "volumen_m3": int(prof_dep[m0].sum() * 900),
                "edificios_intersecan": ne_i, "edificios_centroide": edif_centroide(g0), "poblacion": round(pob0), "viviendas": round(viv0)}
R["depresion"]["vaso_del_punto_bajo"] = {"8_vecinos": vaso[8], "4_vecinos": vaso[4],
    "nota": "Depresión rellenada que contiene el punto bajo, prof > 1 mm, sin ventana. Con 8 vecinos incluye una segunda poza unida por un "
            "paso diagonal a ~12,85 m; con 4 vecinos, no. Coincide con el llenado conectado a cota de rebose − 1 cm."}
# exposición dentro del vaso por cota, sin ventana (no puede tocar bordes: está por debajo del rebose)
expo_vaso = []
for k_, st_ in ESTR.items():
    for h in (12.5, 12.6, 12.7, 12.8, 12.9, round(cota_rebose - 0.01, 2)):
        lab_h, _ = ndimage.label((dem <= h) & ~nod, structure=st_)
        m = lab_h == lab_h[r_lo, c_lo]
        if (m & sea).any(): continue
        g_ = unary_union([shape(s_) for s_, _ in shapes(m.astype("uint8"), mask=m, transform=TR)])
        ne_i, pob_h, viv_h = exposicion(g_)
        expo_vaso.append({"conectividad": k_, "cota_m": float(h), "area_ha": round(m.sum() * 900 / 1e4, 2), "volumen_m3": int(((h - dem) * m).sum() * 900),
                          "edificios_intersecan": ne_i, "edificios_centroide": edif_centroide(g_), "poblacion": round(pob_h), "viviendas": round(viv_h)})
R["depresion"]["exposicion_en_vaso_12.5_a_rebose"] = expo_vaso
# sensibilidad del criterio de depresión: umbral de profundidad × dominio espacial (4 vecinos, como el criterio alternativo).
# Solo sirve para conciliar cifras; el volumen del vaso se toma de vaso_del_punto_bajo.
buf400 = rasterize([(casc.buffer(400), 1)], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool)
sens = []
for umbral in (0.001, 0.1, 0.2, 0.3, 0.5):
    lb, _ = ndimage.label(prof_dep > umbral)
    for dominio, sel in (("componente del punto bajo", {int(lb[r_lo, c_lo])}), ("componentes que tocan el barrio", set(np.unique(lb[mask]).tolist())),
                         ("componentes a <400 m del barrio", set(np.unique(lb[buf400]).tolist()))):
        sel = sorted(sel - {0})
        if not sel: continue
        m = np.isin(lb, sel)
        reb = ndimage.maximum(lleno, lb, index=sel)
        sens.append({"conectividad": 4, "umbral_prof_m": umbral, "dominio": dominio, "n_componentes": len(sel), "area_ha": round(m.sum() * 900 / 1e4, 2),
                     "volumen_m3": int(prof_dep[m].sum() * 900), "cota_rebose_min_m": round(float(np.min(reb)), 2), "cota_rebose_max_m": round(float(np.max(reb)), 2),
                     "edificios": exposicion(unary_union([shape(s_) for s_, _ in shapes(m.astype("uint8"), mask=m, transform=TR)]))[0]})
R["depresion"]["sensibilidad_criterio"] = sens
vol_curva = {c[0]: c[2] for c in curva}
s_grd = next(s_ for s_ in sens if s_["umbral_prof_m"] == 0.2 and s_["dominio"] == "componentes a <400 m del barrio")
ev_top = [e_ for e_ in expo_vaso if e_["cota_m"] == round(cota_rebose - 0.01, 2)]
ev_low = [e_ for e_ in expo_vaso if e_["cota_m"] == 12.5]
R["depresion"]["rango_volumen_m3"] = {
    "almacenamiento_cerrado_hasta_rebose": [vaso[4]["volumen_m3"], vaso[8]["volumen_m3"]],
    "almacenamiento_cerrado_area_ha": [vaso[4]["area_ha"], vaso[8]["area_ha"]],
    "exposicion_12.5m_a_rebose": {"edificios": [min(e_["edificios_centroide"] for e_ in ev_low), max(e_["edificios_intersecan"] for e_ in ev_top)],
                                  "poblacion": [min(e_["poblacion"] for e_ in ev_low), max(e_["poblacion"] for e_ in ev_top)],
                                  "viviendas": [min(e_["viviendas"] for e_ in ev_low), max(e_["viviendas"] for e_ in ev_top)],
                                  "nota": "mínimo: 12,5 m, edificios con el centroide dentro; máximo: rebose − 1 cm, 8 vecinos, edificios que intersecan"},
    "lamina_sostenida_13.5_a_14m_ventana": [vol_curva.get(13.5), vol_curva.get(14.0)],
    "criterio_alternativo_reproducido": {k_: s_grd[k_] for k_ in ("umbral_prof_m", "dominio", "n_componentes", "area_ha", "volumen_m3", "cota_rebose_min_m", "cota_rebose_max_m")},
    "superior_bathtub_14m": vol_curva.get(14.0),
    "nota": "Almacenamiento cerrado: vaso del punto bajo hasta la cota de rebose; el rango 4–8 vecinos refleja si la segunda poza se une. "
            "No usar umbrales de profundidad para el volumen (recortan los bordes someros). Lámina sostenida: volumen bajo 13,5–14 m dentro "
            "de la ventana, solo posible con la salida en remanso u obstruida. El criterio alternativo suma vasos independientes."}
print("   vaso", vaso, "\n   expo_vaso", expo_vaso)

# ---------------------------------------------------------------- 4. corredores de desvío
pob_geoms = [g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")]
pob_geoms += [g for g, _ in manz] + [g for g, _ in feats("capas/final/barrios.geojson")]
pobm = rasterize([(g.buffer(BUFFER_POBLADO_M), 1) for g in pob_geoms], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool)
vias = feats("export/galapagos/vias.geojson")
zonif = feats("export/galapagos/parque_zonificacion.geojson")
parque = rasterize([(g, 1) for g, _ in feats("export/galapagos/parque_nacional.geojson")], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool)
N8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def ruta(r0, c0, corte_max):
    """Máxima cota de rasante alcanzable en cada celda con pendiente >= PENDIENTE_MIN (Dijkstra de máximo)."""
    best = np.full(dem.shape, -np.inf, "float32"); par = -np.ones(dem.shape, "int64"); dist = np.zeros(dem.shape, "float32")
    best[r0, c0] = dem[r0, c0]; h = [(-float(dem[r0, c0]), r0, c0)]; llegadas = []
    while h:
        nL, r, c = heapq.heappop(h); L = -nL
        if L < best[r, c]: continue
        if sea[r, c]: llegadas.append((r, c)); continue
        for a, b in N8:
            r2, c2 = r + a, c + b
            if not (0 <= r2 < H and 0 <= c2 < W) or pobm[r2, c2]: continue
            paso = CELDA * (math.sqrt(2) if a and b else 1)
            z = 0.0 if sea[r2, c2] else float(dem[r2, c2])
            Lc = L - PENDIENTE_MIN * paso
            if Lc < z - corte_max: continue
            L2 = min(Lc, z + RELLENO_MAX_M)
            if L2 > best[r2, c2]:
                best[r2, c2] = L2; par[r2, c2] = r * W + c; dist[r2, c2] = dist[r, c] + paso
                heapq.heappush(h, (-L2, r2, c2))
    return llegadas, best, par, dist


def lado(lon):
    return "OESTE" if lon < LON_OESTE else ("ESTE" if lon > LON_ESTE else "FRENTE URBANO")


up_idx = np.flatnonzero(upf)


def area_captada(path):
    cap = np.zeros(N, bool)
    pm = np.zeros((H, W), bool)
    for p_ in path: pm[p_] = True
    pm = ndimage.binary_dilation(pm, structure=ndimage.generate_binary_structure(2, 1))
    cap[pm.ravel() & upf] = True
    for _ in range(3000):
        new = cap[up_idx] | cap[nxt[up_idx]]
        if (new == cap[up_idx]).all(): break
        cap[up_idx] = new
    return cap.sum() * 900 / 1e6


rutas_f, perfil_int, tabla_rutas = [], None, []
for nm, e in ramas.items():
    stem = cauce(er[e - 1], ec[e - 1])[::-1]       # de la entrada hacia la cabecera
    for hz in COTAS_TOMA:
        k = next((i for i, p_ in enumerate(stem) if dem[p_] >= hz), None)
        if k is None: continue
        r0, c0 = stem[k]
        for cmax in CORTES_MAX_M:
            llegadas, best, par, dist = ruta(r0, c0, cmax)
            mejores = {}
            for (r, c) in llegadas:
                sd = lado(lonlat(r, c)[0])
                if sd not in mejores or dist[r, c] < dist[mejores[sd]]: mejores[sd] = (r, c)
            fila = {"rama": nm, "cota_toma_m": hz, "toma_lonlat": [round(v, 5) for v in lonlat(r0, c0)], "corte_max_m": cmax,
                    "area_en_toma_km2": round(float(A[r0, c0]) * 900 / 1e6, 2), "salidas": {}}
            for sd, (r, c) in mejores.items():
                path = []; i = r * W + c
                while i >= 0:
                    a_, b_ = divmod(i, W); path.append((a_, b_)); i = par[a_, b_]
                path = path[::-1]
                ln = LineString([TR * (c_ + .5, r_ + .5) for r_, c_ in path])
                tierra = [p_ for p_ in path if not sea[p_]]
                cortes = [max(0.0, float(dem[p_] - best[p_])) for p_ in tierra]
                zz = {}
                for gz, pz in zonif:
                    li = gz.intersection(ln).length
                    if li > 0: zz[pz.get("zona")] = zz.get(pz.get("zona"), 0) + round(li)
                props = {"rama": nm, "cota_toma_m": hz, "corte_max_admitido_m": cmax, "lado": sd,
                         "longitud_km": round(ln.length / 1000, 2), "corte_max_m": round(max(cortes), 1), "corte_medio_m": round(float(np.mean(cortes)), 1),
                         "area_captada_km2": round(area_captada(path), 2),
                         "pct_parque": round(100 * float(np.mean([parque[p_] for p_ in tierra]))),
                         "zonificacion_png_m": zz, "cruces_vias": sorted({str(p.get("nombre") or p.get("tipo_osm")) for gv, p in vias if gv.intersects(ln)}),
                         "edificios_a_menos_de_20m": len(t_edif.query(ln.buffer(20), predicate="intersects")),
                         "dist_min_edificio_m": round(min(edif[i][0].distance(ln) for i in t_edif.query(ln.buffer(500)))) if len(t_edif.query(ln.buffer(500))) else None,
                         "salida_mar_lonlat": [round(v, 5) for v in lonlat(*path[-1])]}
                fila["salidas"][sd] = props
                rutas_f.append({"type": "Feature", "properties": props, "geometry": r6(ln)})
                if (nm, hz, cmax, sd) == RUTA_PRINCIPAL:
                    perfil_int = [[round(float(dist[p_])), *[round(v, 6) for v in lonlat(*p_)], round(float(0 if sea[p_] else dem[p_]), 2),
                                   round(float(best[p_]), 2), round(max(0.0, float(dem[p_] - best[p_])) if not sea[p_] else 0.0, 2)] for p_ in path]
                    R["interceptor_este"] = props
            tabla_rutas.append(fila)
            print(f"  {nm} toma {hz} m corte<={cmax}:", {k_: (v["longitud_km"], v["area_captada_km2"]) for k_, v in fila["salidas"].items()} or "sin salida")
guardar_json("rutas_desvio.geojson", fc(rutas_f))
if perfil_int:
    guardar_csv("perfil_interceptor_este.csv", ["distancia_m", "lon", "lat", "cota_terreno_m", "cota_canal_m", "corte_m"], perfil_int)
    # como canal: si la rasante es el fondo, los cajeros quedan a rasante + calado + resguardo
    d_ = np.array([f[0] for f in perfil_int], float); zt_ = np.array([f[3] for f in perfil_int]); zc_ = np.array([f[4] for f in perfil_int])
    seg_ = np.diff(d_, append=d_[-1]); tierra_ = zt_ > 0.5
    canal = {"corte_medio_m_rasante": round(float(np.maximum(0, zt_ - zc_)[tierra_].mean()), 2)}
    for prof_c in (CANAL_CALADO_M, CANAL_CALADO_M + RESGUARDO_M):
        hb = zc_ + prof_c - zt_
        canal[f"prof_{prof_c:.1f}m"] = {
            "terraplen_longitud_m": {f">{u}m": int(seg_[tierra_ & (hb > u)].sum()) for u in (0, 1, 2)},
            "terraplen_altura_max_m": round(float(hb[tierra_].max()), 2), "longitud_total_m": int(seg_[tierra_].sum()),
            "alternativa_sin_terraplen_excavacion_media_m": round(float(np.clip(zt_ - zc_ + prof_c, 0, None)[tierra_].mean()), 2),
            "alternativa_sin_terraplen_excavacion_max_m": round(float((zt_ - zc_ + prof_c)[tierra_].max()), 2)}
    R["interceptor_este"]["como_canal"] = canal
    print("   interceptor como canal:", canal)
R["desvio"] = {"metodo": "Dijkstra de máxima cota de rasante: la rasante baja al menos PENDIENTE_MIN por metro, puede ir hasta "
                         "RELLENO_MAX_M sobre el terreno o corte_max bajo él; prohibidas las celdas pobladas (+buffer). "
                         "area_captada = celdas de la cuenca cuyo flujo D8 cruza la traza antes de llegar al barrio.",
               "tabla": tabla_rutas}

# ---------------------------------------------------------------- 5. hidrología SCS-CN + HU SCS
area_km2 = (up | mask).sum() * 900 / 1e6
# fracciones de cobertura para justificar el CN
agr = rasterize([(g, 1) for g, _ in feats("export/galapagos/zona_agricola.geojson")], out_shape=dem.shape, transform=TR, all_touched=False).astype(bool)
pob_c = rasterize([(g, 1) for g in pob_geoms], out_shape=dem.shape, transform=TR, all_touched=False).astype(bool)
cu = up | mask
f_urb = float((cu & pob_c).sum() / cu.sum()); f_agr = float((cu & agr & ~pob_c).sum() / cu.sum()); f_par = 1 - f_urb - f_agr
cn_ii = (f_par * CN_CLASE["parque (lava, suelo somero)"] + f_agr * CN_CLASE["zona agrícola (suelos más profundos, pastos)"] + f_urb * CN_CLASE["urbano"])
cn_iii = 23 * cn_ii / (10 + 0.13 * cn_ii); cn_i = 4.2 * cn_ii / (10 - 0.058 * cn_ii)
# tormenta SCS tipo II (TR-55), fracción acumulada vs hora
TII_H = [0, 2, 4, 6, 7, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 11.75, 12, 12.5, 13, 13.5, 14, 16, 20, 24]
TII_F = [0, .022, .048, .080, .098, .120, .133, .147, .163, .181, .204, .235, .283, .357, .663, .735, .772, .799, .820, .880, .952, 1.0]
t = np.arange(0, DURACION_SIM_H + 1e-9, DT_H)
frac = np.interp(t, TII_H, TII_F)
# hidrograma unitario adimensional SCS
UH_T = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5]
UH_Q = [0, .03, .1, .19, .31, .47, .66, .82, .93, .99, 1, .99, .93, .86, .78, .68, .56, .46, .39, .33, .28, .207, .147, .107, .077, .055, .04, .029, .021, .015, .011, .005, 0]


def hu(tc_h):
    tp = DT_H / 2 + 0.6 * tc_h
    tt = np.arange(0, 5 * tp + DT_H, DT_H)
    q = np.interp(tt / tp, UH_T, UH_Q)
    return q / (q.sum() * DT_H * 3600) * area_km2 * 1e6 / 1000     # m3/s por mm de exceso (volumen exacto)


def escorrentia(P, cn, Pc=None):
    """P: lluvia total (tormenta tipo II); o Pc: lluvia acumulada (mm) en cada paso de t (hietograma propio)."""
    S = 25400 / cn - 254; Ia = IA_RATIO * S
    Pc = P * frac if Pc is None else Pc
    Q = np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0)
    return np.diff(Q, prepend=0), Q[-1]


def hidrograma(P, cn, tc_h, Pc=None):
    exc, Qmm = escorrentia(P, cn, Pc)
    q = np.convolve(exc, hu(tc_h))[: len(t)]
    return q, Qmm


tc_c = CAUCE["tc_temez_h"]; tc_k = CAUCE["tc_kirpich_h"]
# --- tiempos de concentración y de viaje con varios métodos
def tiempos(path):
    """path: celdas de aguas arriba hacia el barrio. Devuelve L, H y tiempos (h) por método."""
    z_ = np.array([float(dem[p_]) for p_ in path])
    dl = np.array([CELDA * math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1)])
    L = float(dl.sum()); Hh = float(z_[0] - z_[-1]); S = max(Hh / L, 1e-4)
    k = 5                                                              # pendiente local sobre ±150 m (suaviza el ruido del DSM)
    sl = np.array([(z_[max(0, i - k)] - z_[min(len(z_) - 1, i + k + 1)]) / max(dl[max(0, i - k):i + k + 1].sum(), 1) for i in range(len(dl))])
    sl = np.clip(sl, 0.005, None)
    v_sup = 4.918 * np.sqrt(sl)                                        # TR-55: flujo concentrado superficial, sin pavimentar (m/s)
    v_cau = (1 / 0.045) * 0.5 ** (2 / 3) * np.sqrt(sl)                 # cauce definido: Manning n = 0,045, R = 0,5 m
    return {"L_km": round(L / 1000, 2), "H_m": round(Hh, 1), "S_pct": round(S * 100, 2),
            "kirpich_h": round(0.0195 * L ** 0.77 * S ** -0.385 / 60, 2),
            "temez_h": round(0.3 * ((L / 1000) / S ** 0.25) ** 0.76, 2),
            "velocidad_flujo_superficial_TR55_h": round(float((dl / v_sup).sum() / 3600), 2),
            "velocidad_cauce_manning_h": round(float((dl / v_cau).sum() / 3600), 2)}


def hasta_barrio(r, c):
    p_ = [(r, c)]; i = r * W + c
    while not mask.ravel()[i] and nxt[i] != i and len(p_) < 50000:
        i = nxt[i]; p_.append(divmod(i, W))
    return p_ if mask.ravel()[i] else None


def snap(lon, lat, radio=10):
    c, r = ~TR * T(lon, lat); r, c = int(r), int(c)
    w_ = np.where(up[r - radio:r + radio + 1, c - radio:c + radio + 1], A[r - radio:r + radio + 1, c - radio:c + radio + 1], -1)
    a, b = np.unravel_index(np.argmax(w_), w_.shape); return r - radio + a, c - radio + b


bv = [g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("nombre") == "Bellavista" and p.get("tipo") == "Límite urbano IGM")]
origenes = {}
if bv:
    origenes["Bellavista (centro del límite urbano IGM, ajustado al cauce)"] = snap(*TI(*bv[0].centroid.coords[0]))
stem1 = cauce(er[ramas["rama 1"] - 1], ec[ramas["rama 1"] - 1])
origenes["cabecera rama 1"] = stem1[0]
for nm, e in ramas.items():
    st_ = cauce(er[e - 1], ec[e - 1])[::-1]
    k = next((i for i, p_ in enumerate(st_) if dem[p_] >= 40), None)
    if k is not None: origenes[f"{nm}, cota 40 m"] = st_[k]
viajes = {}
for nm, (r, c) in origenes.items():
    p_ = hasta_barrio(r, c)
    if p_ is None: viajes[nm] = "no drena al barrio según D8"; continue
    viajes[nm] = {"lonlat": [round(v, 5) for v in lonlat(r, c)], "cota_m": round(float(dem[r, c]), 1),
                  "area_drenada_km2": round(float(A[r, c]) * 900 / 1e6, 2), **tiempos(p_)}
L_ft = CAUCE["longitud_km"] * 3280.8; Y = R["cuenca"]["pendiente_media_pct"]
scs_lag = {f"CN{cn}": round(L_ft ** 0.8 * ((1000 / cn - 10) + 1) ** 0.7 / (1900 * Y ** 0.5) / 0.6, 2) for cn in CN_ESCENARIOS}
R["tiempos"] = {"tc_intervalo_defendible_h": [tc_k, max(scs_lag.values())], "tc_central_h": tc_c, "tc_cuenca_h": {"kirpich": tc_k, "temez": tc_c, "scs_lag_por_CN": scs_lag,
                                **{k_: v for k_, v in viajes.get("cabecera rama 1", {}).items() if k_.endswith("_h") and "velocidad" in k_}},
                "nota": "California Culverts Practice (1942) es algebraicamente la fórmula de Kirpich; no se cuenta como método independiente. "
                        "Kirpich se calibró en cuencas agrícolas < 0,5 km² (Tennessee): fuera de rango para 42 km². "
                        "El SCS lag se desarrolló para cuencas < ~8 km². Témez se usa en cuencas naturales de hasta ~3000 km².",
                "viajes_hasta_el_barrio": viajes}
print("Tiempos:", json.dumps(R["tiempos"], ensure_ascii=False))
vol_rebose = vaso[8]["volumen_m3"]
vol_sup = R["depresion"]["rango_volumen_m3"]["superior_bathtub_14m"]
vols = {c[0]: c[2] for c in curva}
escen = [(P, cn, f"P{P}mm_CN{cn}") for P in LLUVIAS_MM for cn in CN_ESCENARIOS]
if LLUVIA_EVENTO_MM:
    escen += [(LLUVIA_EVENTO_MM, cn, f"EVENTO{LLUVIA_EVENTO_MM}mm_CN{cn}") for cn in CN_ESCENARIOS]
cols, tabla_h = [], []


def b_canal(Q, S):
    """Ancho de base de canal trapecial (calado CANAL_CALADO_M, talud 1:1) para conducir Q con Manning."""
    for b in np.arange(0.5, 200, 0.5):
        Aa = (b + CANAL_TALUD * CANAL_CALADO_M) * CANAL_CALADO_M; Pm = b + 2 * CANAL_CALADO_M * math.sqrt(1 + CANAL_TALUD ** 2)
        if Aa * (Aa / Pm) ** (2 / 3) * S ** 0.5 / MANNING_N >= Q: return float(b)
    return None


for P, cn, nm in escen:
    q, Qmm = hidrograma(P, cn, tc_c); qk, _ = hidrograma(P, cn, tc_k)
    V = Qmm / 1000 * area_km2 * 1e6
    cum = np.cumsum(q) * DT_H * 3600
    t_llena = float(t[np.argmax(cum >= vol_rebose)]) if cum[-1] >= vol_rebose else None
    cols.append((nm, q))
    tabla_h.append({"escenario": nm, "lluvia_mm": P, "CN": cn, "escorrentia_mm": round(float(Qmm), 1), "coef_escorrentia": round(float(Qmm / P), 3),
                    "volumen_escorrentia_m3": int(V), "q_pico_m3s_tc_temez": round(float(q.max()), 1), "t_pico_h": round(float(t[q.argmax()]), 2),
                    "q_pico_m3s_tc_kirpich": round(float(qk.max()), 1),
                    "veces_volumen_vaso_hasta_rebose": round(V / vol_rebose, 1) if vol_rebose else None,
                    "veces_volumen_bathtub_14m": round(V / vol_sup, 1) if vol_sup else None,
                    "hora_en_que_se_llena_la_depresion": t_llena,
                    "ancho_base_canal_m_S0.5pct": b_canal(float(q.max()), 0.005), "ancho_base_canal_m_S0.5pct_tc_kirpich": b_canal(float(qk.max()), 0.005)})
# --- escenario del evento 31-oct-2026 con el hietograma horario ECMWF (modelo, no medición)
if EVENTO_CSV.exists() and not LLUVIA_EVENTO_MM:
    import datetime as _dt
    filas_ev = list(csv.DictReader(open(EVENTO_CSV)))
    t0 = _dt.datetime.fromisoformat(EVENTO_INICIO)
    sel_ev = [f for f in filas_ev if t0 < _dt.datetime.fromisoformat(f["fecha_hora_local"]) <= t0 + _dt.timedelta(hours=EVENTO_HORAS)]
    # Thiessen entre la celda costa y la celda alta (centro de Bellavista)
    pc_xy = np.array(T(*PUNTO_COSTA)); pa_xy = np.array(T(*PUNTO_ALTA))
    xy = np.array(TR * (cc[cu] + .5, rr[cu] + .5))
    w_alta = float((np.hypot(*(xy - pa_xy[:, None])) < np.hypot(*(xy - pc_xy[:, None]))).mean())
    w_alta_200 = float((dem[cu] >= 200).mean())
    cn_ev = {"AMC_III": round(cn_iii, 1), "AMC_II_III": round((cn_ii + cn_iii) / 2, 1), "AMC_II": round(cn_ii, 1)}
    curva_v = np.array([[c[0], c[2]] for c in curva])
    R["evento_31oct"] = {"fuente": "Open-Meteo, ECMWF IFS 9 km (y 0,25° como sensibilidad); pronóstico/análisis de modelo, sin medición en tierra",
                         "peso_celda_alta_thiessen": round(w_alta, 3), "peso_alta_por_cota_>=200m": round(w_alta_200, 3),
                         "inicio_etiqueta_utc-5": EVENTO_INICIO, "nota_horas": "etiquetas Open-Meteo en America/Guayaquil (UTC-5); las horas de resultados se dan en hora de Galápagos (UTC-6)",
                         "celdas_ecmwf_9km": {"costa": PUNTO_COSTA, "alta": PUNTO_ALTA}, "observacion_referencia": {"lamina_m": OBS_LAMINA_M, "fondo_m": OBS_FONDO_M,
                         "cota_agua_m": [OBS_FONDO_M[0] + OBS_LAMINA_M[0], OBS_FONDO_M[1] + OBS_LAMINA_M[1]], "fuente": "prensa (testigo), por validar"},
                         "escenarios": []}
    pesos = {"cota200": w_alta_200, "thiessen": w_alta}       # central: fracción de la cuenca >= 200 m recibe la serie «alta»
    combos = [("ecmwf_ifs_9km", "cota200"), ("ecmwf_ifs_9km", "thiessen"), ("ecmwf_ifs025", "cota200")]
    if LLUVIA_DIARIA_CSV.exists():
        fd_ = [f for f in csv.DictReader(open(LLUVIA_DIARIA_CSV)) if "2026-10-26" <= f["fecha"] <= "2026-10-30"]
        amc = {}
        for col in sorted({k_[k_.index("_") + 1:] for k_ in fd_[0] if k_ != "fecha"}):
            c5 = sum(float(f.get(f"costa_{col}") or 0) for f in fd_); a5 = sum(float(f.get(f"alta_{col}") or 0) for f in fd_)
            w5 = (1 - w_alta_200) * c5 + w_alta_200 * a5
            cls = {}
            for est, (u1, u2) in AMC_UMBRALES_MM.items():
                cls[est] = {nm_: ("I" if v_ < u1 else ("II" if v_ <= u2 else "III")) for nm_, v_ in (("costa", c5), ("alta", a5), ("ponderada", w5))}
            amc[col.replace("_mm", "")] = {"costa_mm": round(c5, 1), "alta_mm": round(a5, 1), "ponderada_mm": round(w5, 1), "clase": cls}
        R["evento_31oct"]["amc_5dias_26_30oct"] = amc
        R["evento_31oct"]["cn_eleccion"] = ("Central CN intermedio II–III: con ECMWF 9 km la lluvia de 5 días ponderada es AMC II con los umbrales "
                                            "de la estación de crecimiento y AMC III con los de la estación latente; los demás modelos dan AMC I–II. "
                                            "CN 83 (AMC III) y CN 68 (AMC II) quedan como sensibilidad.")
        print("   AMC 5 días:", {k_: (v_["costa_mm"], v_["alta_mm"], v_["ponderada_mm"]) for k_, v_ in amc.items()})
    for modelo, peso in combos:
        h_c = np.array([float(f[f"costa_{modelo}_mm"] or 0) for f in sel_ev]); h_a = np.array([float(f[f"alta_{modelo}_mm"] or 0) for f in sel_ev])
        h_w = (1 - pesos[peso]) * h_c + pesos[peso] * h_a
        Pc_h = np.concatenate([[0], np.cumsum(h_w)])
        Pc = np.interp(t, np.arange(len(Pc_h)), Pc_h)             # lluvia uniforme dentro de cada hora
        for tag in CN_EVENTO:
            cn = cn_ev[tag]; nm = f"EVENTO31oct_{modelo}_{peso}_CN{cn:.0f}"
            q, Qmm = hidrograma(None, cn, tc_c, Pc); qk, _ = hidrograma(None, cn, tc_k, Pc)
            V = Qmm / 1000 * area_km2 * 1e6
            cum = np.cumsum(q) * DT_H * 3600
            t_ll = float(t[np.argmax(cum >= vol_rebose)]) if cum[-1] >= vol_rebose else None
            cota_sin_salida = float(np.interp(V, curva_v[:, 1], curva_v[:, 0])) if V <= curva_v[-1, 1] else None
            verted = {f"L{L}m": {"carga_m_temez": round((q.max() / (VERTEDERO_C * L)) ** (2 / 3), 2), "carga_m_kirpich": round((qk.max() / (VERTEDERO_C * L)) ** (2 / 3), 2),
                                 "cota_agua_m_temez": round(cota_rebose + (q.max() / (VERTEDERO_C * L)) ** (2 / 3), 2),
                                 "cota_agua_m_kirpich": round(cota_rebose + (qk.max() / (VERTEDERO_C * L)) ** (2 / 3), 2)} for L in VERTEDERO_L_M}
            hora = lambda x: (t0 + _dt.timedelta(hours=float(x) + DESFASE_A_GALAPAGOS_H)).strftime("%d-%b %H:%M") + " (UTC-6)"
            row = {"escenario": nm, "modelo": modelo, "ponderacion": peso, "peso_alta": round(pesos[peso], 3), "amc": tag, "CN": cn, "lluvia_costa_mm": round(float(h_c.sum()), 1), "lluvia_alta_mm": round(float(h_a.sum()), 1),
                   "lluvia_ponderada_mm": round(float(h_w.sum()), 1), "max_horaria_ponderada_mm": round(float(h_w.max()), 1),
                   "escorrentia_mm": round(float(Qmm), 1), "coef_escorrentia": round(float(Qmm / h_w.sum()), 3) if h_w.sum() else None,
                   "volumen_escorrentia_m3": int(V), "q_pico_m3s_tc_temez": round(float(q.max()), 1), "q_pico_m3s_tc_kirpich": round(float(qk.max()), 1),
                   "hora_pico_local_temez": hora(t[q.argmax()]), "hora_pico_local_kirpich": hora(t[qk.argmax()]),
                   "hora_local_vaso_lleno": hora(t_ll) if t_ll is not None else None, "veces_volumen_vaso": round(V / vol_rebose, 1),
                   "cota_si_no_hubiera_salida_m": round(cota_sin_salida, 2) if cota_sin_salida else f"> {curva_v[-1, 0]:.0f}",
                   "vertedero_en_umbral_de_rebose": verted}
            R["evento_31oct"]["escenarios"].append(row); cols.append((nm, q))
            print("   evento", nm, {k_: row[k_] for k_ in ("lluvia_ponderada_mm", "escorrentia_mm", "volumen_escorrentia_m3", "q_pico_m3s_tc_temez", "q_pico_m3s_tc_kirpich", "hora_pico_local_temez", "hora_local_vaso_lleno")}, verted)
# --- evento MEDIDO 30-oct-2026: lluvia areal desde las estaciones IERSE y tránsito por el vaso
if IERSE_CSV.exists():
    import datetime as _dt
    est = {f["properties"]["nombre"]: (f["geometry"]["coordinates"], f["properties"]["altitud_m_dem"]) for f in json.loads(IERSE_EST.read_text())["features"]}
    t0m = _dt.datetime.fromisoformat(MEDIDO_INICIO)
    tm = np.arange(0, MEDIDO_HORAS_SIM + 1e-9, DT_H)
    nb_ = len(tm)
    serie = {}
    ultimo = {}
    for f in csv.DictReader(open(IERSE_CSV)):
        ts = _dt.datetime.fromisoformat(f["fecha_hora_local"]); k = int((ts - t0m).total_seconds() // (DT_H * 3600))
        if 0 <= k < nb_:
            serie.setdefault(f["estacion"], np.zeros(nb_))[k] += float(f["lluvia_mm"] or 0)
            if ts.date() == t0m.date(): ultimo[f["estacion"]] = (ts, float(f["lluvia_mm"] or 0))
    G_, C_, SR_ = serie["Los Guayabillos"], serie["Cerro Crocker"], serie["Santa Rosa"]
    # pesos sobre la cuenca
    xy_c = np.array(TR * (cc[cu] + .5, rr[cu] + .5))
    exy = {n_: np.array(T(*v_[0][:2])) for n_, v_ in est.items()}
    dmat = np.array([np.hypot(*(xy_c - exy[n_][:, None])) for n_ in est])
    near = np.array(list(est))[dmat.argmin(0)]
    w_th = {n_: float((near == n_).mean()) for n_ in est}
    alfa = float(np.clip((dem[cu] - COTA_G) / (COTA_SR - COTA_G), 0, 1).mean())
    areal = {"G_uniforme": G_.copy(),
             "G_ARF": ARF * G_,
             "thiessen_con_Crocker": sum(w_th[n_] * serie[n_] for n_ in est),
             "gradiente_cota_G_SR": (1 - alfa) * G_ + alfa * SR_}
    # sensibilidad: continuación de la tormenta tras el corte, al ritmo de los últimos 3 registros de Los Guayabillos
    cont = areal["G_uniforme"].copy()
    tg_, _ = ultimo["Los Guayabillos"]; kk = int((tg_ - t0m).total_seconds() // (DT_H * 3600)) + 1
    tasa = float(np.mean(G_[kk - 3:kk]))                          # mm por paso de 10 min
    cont[kk:kk + int(CONTINUACION_MIN / 60 / DT_H)] += tasa
    areal["G_uniforme_mas_continuacion"] = cont
    R["evento_30oct_medido"] = {
        "fuente": "Red IERSE-WSN, Universidad del Azuay (pluviómetros de balancín, 0,2 mm). Totales MÍNIMOS: las estaciones dejan de transmitir hacia las 21:25–21:30.",
        "totales_estacion_30oct_mm": {n_: round(float(serie[n_][:int(24 / DT_H)].sum()), 1) for n_ in serie},
        "ultimo_registro": {n_: v_[0].strftime("%H:%M") for n_, v_ in ultimo.items()},
        "pesos_thiessen_cuenca": {n_: round(v_, 3) for n_, v_ in w_th.items()},
        "fraccion_gradiente_alfa": round(alfa, 3),
        "metodos_lluvia_areal": {"G_uniforme": "central: Los Guayabillos (178 m, a 370 m del límite oeste de la cuenca; cota cercana a la mediana de la cuenca, 225 m)",
                                 "G_ARF": f"cota inferior: Los Guayabillos × factor de reducción areal {ARF} (TP-29, tormenta de 1–3 h sobre ~40 km²)",
                                 "thiessen_con_Crocker": "solo si Crocker fuera correcto (casi seguro falla desde agosto: 9 y 18 mm en sep y oct frente a 140 y 340 en Los Guayabillos)",
                                 "gradiente_cota_G_SR": "interpolación lineal con la cota entre Los Guayabillos y Santa Rosa, constante fuera de 178–416 m (Crocker descartado)",
                                 "G_uniforme_mas_continuacion": f"sensibilidad: {CONTINUACION_MIN} min más al ritmo de los últimos registros ({tasa:.1f} mm/10 min)"},
        "pluviometros_calidad": {},
        "crocker": "Registra 0,2–0,8 mm/h de forma casi constante antes, durante y después de la tormenta (también el 31-oct), sin respuesta "
                   "a los pulsos de 43–66 mm/h de las otras estaciones y sin caída térmica. Compatible con una tormenta de cotas medias bajo la "
                   "inversión o con un embudo obstruido que drena lento; no se puede decidir con dos días de datos.",
        "escenarios": []}
    if IERSE_DIARIO.exists():
        dd_ = list(csv.DictReader(open(IERSE_DIARIO)))
        mes = {}
        for f in dd_: mes.setdefault((f["estacion"], f["fecha"][:7]), 0.0); mes[(f["estacion"], f["fecha"][:7])] += float(f["lluvia_mm"] or 0)
        r5 = {n_: round(sum(float(f["lluvia_mm"] or 0) for f in dd_ if f["estacion"] == n_ and "2026-10-25" <= f["fecha"] <= "2026-10-29"), 1) for n_ in est}
        R["evento_30oct_medido"]["pluviometros_calidad"] = {
            "mensual_mm": {f"{n_} {m_}": round(v_, 1) for (n_, m_), v_ in sorted(mes.items()) if m_ >= "2026-06"},
            "crocker": "casi seguro falla desde agosto (jun 297 mm; sep 9 y oct 18 mm frente a 140 y 340 mm en Los Guayabillos)",
            "los_guayabillos": "marca 0 mm del 31-oct al 2-nov con cobertura completa mientras Santa Rosa mide 13–43 mm/día: probable obstrucción o daño durante el evento; no afecta al 30-oct",
            "lluvia_5_dias_previos_25_29oct_mm": r5,
            "amc": "5 días previos ≈10–12 mm (AMC I–II por el criterio SCS), pero octubre fue húmedo (340 mm en Los Guayabillos) y el 30-oct ya habían caído ~25 mm antes del pulso principal: CN 76 central; 68 igual de defendible; 83 sin respaldo."}
    # curva de almacenamiento para el tránsito (llenado conectado; por encima del rebose, ventana de RADIO_MANCHA_M)
    cv = sorted({(round(c_[0], 3), c_[2]) for c_ in curva} | {(round(cota_rebose, 3), vaso[8]["volumen_m3"])})
    cv_h = np.array([a_ for a_, _ in cv]); cv_v = np.array([b_ for _, b_ in cv], float)
    fondo = float(dem[r_lo, c_lo])
    hora_m = lambda x: (t0m + _dt.timedelta(hours=float(x))).strftime("%d-%b %H:%M")
    filas_hid = {}
    for met, hy in areal.items():
        Pc = np.cumsum(hy)
        for cn in (round(cn_ii, 1), round((cn_ii + cn_iii) / 2, 1), round(cn_iii, 1)):
            for tc_nm, tc_v in (("temez", tc_c), ("kirpich", tc_k)):
                exc, Qmm = escorrentia(None, cn, Pc)
                q = np.convolve(exc, hu(tc_v))[:nb_]
                nm = f"MEDIDO30oct_{met}_CN{cn:.0f}_{tc_nm}"
                filas_hid[nm] = q
                V = float(Qmm) / 1000 * area_km2 * 1e6
                # tránsito por el vaso (paso de 1 min)
                ruteo = {}
                tt = np.arange(0, tm[-1], 1 / 60); qi = np.interp(tt, tm, q)
                for Lw in L_ROUTING_M:
                    S_ = 0.0; hs = np.empty_like(tt); qo = np.empty_like(tt)
                    for i_, qin in enumerate(qi):
                        h_ = float(np.interp(S_, cv_v, cv_h)) if S_ > 0 else fondo
                        qout = VERTEDERO_C * Lw * max(0.0, h_ - cota_rebose) ** 1.5
                        S_ = max(0.0, S_ + (qin - qout) * 60); hs[i_] = h_; qo[i_] = qout
                    im = int(hs.argmax())
                    lleno = np.argmax(hs >= cota_rebose - 0.005) if (hs >= cota_rebose - 0.005).any() else None
                    baja = im + int(np.argmax(hs[im:] <= cota_rebose + 0.05)) if (hs[im:] <= cota_rebose + 0.05).any() else None
                    ruteo[f"L{Lw}m"] = {"cota_max_m": round(float(hs.max()), 2), "lamina_max_sobre_fondo_m": round(float(hs.max()) - fondo, 2),
                                        "hora_lamina_max": hora_m(tt[im]), "hora_vaso_lleno": hora_m(tt[lleno]) if lleno is not None else None,
                                        "hora_baja_a_rebose_mas_5cm": hora_m(tt[baja]) if baja is not None else None,
                                        "q_salida_max_m3s": round(float(qo.max()), 1)}
                sig = np.argmax(q > 1.0) if (q > 1.0).any() else None
                R["evento_30oct_medido"]["escenarios"].append({
                    "escenario": nm, "lluvia_areal": met, "CN": cn, "tc": tc_nm, "lluvia_mm": round(float(Pc[-1]), 1),
                    "max_10min_mm": round(float(hy.max()), 1), "escorrentia_mm": round(float(Qmm), 1), "coef_escorrentia": round(float(Qmm) / float(Pc[-1]), 3),
                    "volumen_m3": int(V), "veces_vaso": round(V / vol_rebose, 1), "q_pico_m3s": round(float(q.max()), 1), "hora_pico": hora_m(tm[q.argmax()]),
                    "hora_inicio_escorrentia_q>1m3s": hora_m(tm[sig]) if sig is not None else None, "transito_vaso": ruteo})
    guardar_csv("hidrogramas_evento_30oct.csv", ["fecha_hora_utc6"] + list(filas_hid),
                [[hora_m(x_)] + [round(float(v_[i_]), 2) for v_ in filas_hid.values()] for i_, x_ in enumerate(tm)])
    guardar_csv("lluvia_areal_30oct_10min.csv", ["fecha_hora_utc6"] + list(areal), [[hora_m(x_)] + [round(float(v_[i_]), 2) for v_ in areal.values()] for i_, x_ in enumerate(tm) if x_ < 24])
    esc = {e_["escenario"]: e_ for e_ in R["evento_30oct_medido"]["escenarios"]}
    for e_ in R["evento_30oct_medido"]["escenarios"]:
        print("   medido", e_["escenario"], e_["lluvia_mm"], e_["escorrentia_mm"], e_["q_pico_m3s"], e_["hora_pico"], e_["hora_inicio_escorrentia_q>1m3s"],
              {k_: (v_["cota_max_m"], v_["lamina_max_sobre_fondo_m"], v_["hora_lamina_max"], v_["hora_vaso_lleno"], v_["hora_baja_a_rebose_mas_5cm"]) for k_, v_ in e_["transito_vaso"].items()})
    # hitos (escenario central: G uniforme, CN intermedio; rangos con Témez–Kirpich, CN 68–83 y L 100–1000 m)
    cn_c = round((cn_ii + cn_iii) / 2); base = f"MEDIDO30oct_G_uniforme_CN{cn_c}"
    sel_ = [e_ for e_ in R["evento_30oct_medido"]["escenarios"] if e_["lluvia_areal"] == "G_uniforme"]
    ct, ck = esc[base + "_temez"], esc[base + "_kirpich"]
    rng = lambda key: sorted({e_[key] for e_ in sel_ if e_[key]})
    tv = lambda e_, k_: [v_[k_] for v_ in e_["transito_vaso"].values() if v_[k_]]
    hitos = [
        [ck["hora_inicio_escorrentia_q>1m3s"], "Inicio de escorrentía significativa en la entrada al barrio (Q > 1 m³/s)", "",
         f"{min(rng('hora_inicio_escorrentia_q>1m3s'))} a {max(rng('hora_inicio_escorrentia_q>1m3s'))} según CN y tc"],
        [ct["transito_vaso"]["L300m"]["hora_vaso_lleno"], "Vaso de La Cascada lleno hasta el rebose (≈12,95 m DSM)", f"{vol_rebose} m³",
         f"{min(tv(ck, 'hora_vaso_lleno') + tv(ct, 'hora_vaso_lleno'))} a {max(tv(ck, 'hora_vaso_lleno') + tv(ct, 'hora_vaso_lleno'))} (Kirpich–Témez); volumen 42 000–62 000 m³"],
        [ck["hora_pico"], "Caudal pico en la entrada al barrio (tc Kirpich)", f"{ck['q_pico_m3s']} m³/s", f"CN 68–83: {min(e_['q_pico_m3s'] for e_ in sel_ if e_['tc'] == 'kirpich')}–{max(e_['q_pico_m3s'] for e_ in sel_ if e_['tc'] == 'kirpich')} m³/s"],
        [ct["hora_pico"], "Caudal pico en la entrada al barrio (tc Témez)", f"{ct['q_pico_m3s']} m³/s", f"CN 68–83: {min(e_['q_pico_m3s'] for e_ in sel_ if e_['tc'] == 'temez')}–{max(e_['q_pico_m3s'] for e_ in sel_ if e_['tc'] == 'temez')} m³/s"],
        [ct["transito_vaso"]["L300m"]["hora_lamina_max"], "Lámina máxima en el barrio (tránsito por el vaso, frente de desborde 300 m)",
         f"{ct['transito_vaso']['L300m']['lamina_max_sobre_fondo_m']} m sobre el fondo DSM (cota {ct['transito_vaso']['L300m']['cota_max_m']} m)",
         "frente 100–1000 m y Kirpich–Témez: " + ", ".join(f"{v_['lamina_max_sobre_fondo_m']} m" for e_ in (ct, ck) for v_ in e_["transito_vaso"].values()) + "; DSM ±2–4 m"],
        [ct["transito_vaso"]["L300m"]["hora_baja_a_rebose_mas_5cm"], "La lámina vuelve a la cota de rebose (+5 cm); por debajo, el vaso solo se vacía por infiltración o bombeo",
         f"{vol_rebose} m³ retenidos", "sin salida por gravedad bajo el rebose; la SNGR anunció que se drenaría el sector"]]
    HITOS_CSV.parent.mkdir(parents=True, exist_ok=True)
    previos = []
    if HITOS_CSV.exists():
        previos = [r_ for r_ in csv.reader(open(HITOS_CSV)) if r_ and not r_[1].startswith(("Inicio de escorrentía significativa en la entrada al barrio", "Vaso de La Cascada", "Caudal pico en la entrada al barrio", "Lámina máxima en el barrio", "La lámina vuelve a la cota"))][1:]
    with open(HITOS_CSV, "w", newline="") as fh:
        w_ = csv.writer(fh); w_.writerow(["fecha_hora_utc6", "hito", "valor", "incertidumbre"])
        for h_ in hitos: w_.writerow(["2026-" + _dt.datetime.strptime(h_[0], "%d-%b %H:%M").strftime("%m-%dT%H:%M") if h_[0] else "", "La Cascada: " + h_[1], h_[2], h_[3]])
        for r_ in previos: w_.writerow(r_)
guardar_csv("hidrogramas.csv", ["tiempo_h"] + [c[0] for c in cols],
            [[round(float(tt), 3)] + [round(float(c[1][i]), 2) for c in cols] for i, tt in enumerate(t)])
R["hidrologia"] = {
    "metodo": "SCS-CN (Ia = 0,2 S) + hidrograma unitario adimensional SCS (Tlag = 0,6 tc, dt = 10 min); tormenta SCS tipo II de 24 h; "
              "cuenca agregada, lluvia uniforme, sin flujo base ni tránsito por depresiones.",
    "area_km2": round(area_km2, 2), "tc_temez_h (central)": tc_c, "tc_kirpich_h (sensibilidad)": tc_k,
    "coberturas": {"parque": round(f_par, 3), "agricola": round(f_agr, 3), "urbano": round(f_urb, 3)},
    "cn_por_clase_supuesto": CN_CLASE, "cn_compuesto_AMC_I": round(cn_i, 1), "cn_compuesto_AMC_II": round(cn_ii, 1), "cn_compuesto_AMC_III": round(cn_iii, 1),
    "volumen_almacenable_depresion_hasta_rebose_m3": vol_rebose, "volumen_bathtub_14m_m3": vol_sup, "escenarios": tabla_h,
    "canal_referencia": {"n_manning": MANNING_N, "calado_m": CANAL_CALADO_M, "talud": CANAL_TALUD}}
for row in tabla_h:
    print("  ", row["escenario"], "Q mm", row["escorrentia_mm"], "Qp", row["q_pico_m3s_tc_temez"], "/", row["q_pico_m3s_tc_kirpich"], "V m3", row["volumen_escorrentia_m3"])

# ---------------------------------------------------------------- 6. salida de rebose de la depresión (camino de mínimo umbral)
def minimax(r0, c0, sup=None, vecinos=8):
    """Para cada celda: cota mínima que debe alcanzar la lámina para llegar desde (r0, c0); desempate por longitud."""
    sup = dem if sup is None else sup
    nb = N8 if vecinos == 8 else [(a, b) for a, b in N8 if not (a and b)]
    best = np.full(dem.shape, np.inf); Lg = np.full(dem.shape, np.inf); par = -np.ones(dem.shape, "int64")
    best[r0, c0] = sup[r0, c0]; Lg[r0, c0] = 0; h = [(float(sup[r0, c0]), 0.0, r0, c0)]
    while h:
        e, l, r, c = heapq.heappop(h)
        if (e, l) > (best[r, c], Lg[r, c]) or sea[r, c]: continue
        for a, b in nb:
            r2, c2 = r + a, c + b
            if 0 <= r2 < H and 0 <= c2 < W:
                e2 = max(e, 0.0 if sea[r2, c2] else float(sup[r2, c2])); l2 = l + CELDA * (math.sqrt(2) if a and b else 1)
                if (e2, l2) < (best[r2, c2], Lg[r2, c2]):
                    best[r2, c2], Lg[r2, c2], par[r2, c2] = e2, l2, r * W + c; heapq.heappush(h, (e2, l2, r2, c2))
    return best, Lg, par


def camino(par, r, c):
    p = []; i = r * W + c
    while i >= 0: a, b = divmod(i, W); p.append((a, b)); i = par[a, b]
    return p[::-1]


mm_best, mm_L, mm_par = minimax(r_lo, c_lo)
pob_union = unary_union(pob_geoms[:len(pob_geoms)])
sr, sc = np.where(sea & np.isfinite(mm_best))
slon = np.array([lonlat(r, c)[0] for r, c in zip(sr, sc)])
reb_f, R["rebose"] = [], {"metodo": "Camino de mínimo umbral (minimax) desde el punto bajo del barrio hasta el mar sobre el DSM; desempate por longitud."}
for nm, sel in (("SUR (bahía, frente urbano)", slon < LON_ESTE), ("ESTE", slon >= LON_ESTE)):
    cand = np.where(sel, mm_best[sr, sc] + 1e-6 * mm_L[sr, sc], np.inf)
    if not np.isfinite(cand).any(): continue
    i = int(np.argmin(cand)); p = camino(mm_par, sr[i], sc[i])
    zs = [0.0 if sea[q] else float(dem[q]) for q in p]; k = int(np.argmax(zs))
    ln = LineString([TR * (b + .5, a + .5) for a, b in p])
    props = {"salida": nm, "umbral_m": round(zs[k], 2), "umbral_lonlat": [round(v, 5) for v in lonlat(*p[k])],
             "longitud_m": round(ln.length), "fraccion_en_zona_poblada": round(ln.intersection(pob_union).length / ln.length, 2),
             "edificios_a_menos_de_20m": len(t_edif.query(ln.buffer(20), predicate="intersects")),
             "llegada_mar_lonlat": [round(v, 5) for v in lonlat(*p[-1])]}
    R["rebose"][nm] = props
    reb_f.append({"type": "Feature", "properties": props, "geometry": r6(ln)})
guardar_json("salidas_rebose.geojson", fc(reb_f))
# definiciones de la cota de rebose: superficie (DSM o «proxy de suelo» = mínimo 3×3 del DSM) × conectividad
proxy = ndimage.minimum_filter(np.where(nod, 9999, dem), size=3)
defs = []
for sup_nm, sup in (("DSM", dem), ("proxy de suelo (mín. 3×3)", proxy)):
    for vec in (8, 4):
        rr0, cc0 = (r_lo, c_lo) if sup is dem else np.unravel_index(np.argmin(np.where(mask, proxy, 9999)), dem.shape)
        bst, _, pr_ = minimax(rr0, cc0, sup, vec)
        srr, scc = np.where(sea); i = int(np.argmin(bst[srr, scc]))
        pth = camino(pr_, srr[i], scc[i]); zs = [0.0 if sea[q] else float(sup[q]) for q in pth]; k = int(np.argmax(zs))
        defs.append({"superficie": sup_nm, "vecinos": vec, "cota_fondo_m": round(float(sup[rr0, cc0]), 2), "cota_rebose_m": round(zs[k], 2),
                     "punto_de_control_lonlat": [round(v, 5) for v in lonlat(*pth[k])], "dsm_en_punto_de_control_m": round(float(dem[pth[k]]), 2)})
R["rebose"]["definiciones"] = defs
R["rebose"]["definicion_adoptada"] = ("Cota de rebose: mínima cota de lámina a la que el agua conectada al punto bajo del barrio alcanza el mar "
                                      "(camino minimax). Referencia: DSM con 8 vecinos. Las demás variantes acotan la incertidumbre.")
print("Rebose, definiciones:", defs)
print("Rebose:", R["rebose"])

# ---------------------------------------------------------------- 7. cauce cartografiado al pie del escarpe, hacia el este
cands = [(g, p) for g, p in feats("capas/final/quebradas.geojson") if g.distance(casc) < 100 and g.length > 2000]
g_este, p_este = max(cands, key=lambda gp: max(x for x, _ in gp[0].coords))
tags_osm = None
raw = ROOT / "descargas/osm/santa_cruz_hidro.osm.json"
if raw.exists():
    for e in json.loads(raw.read_text()).get("elements", []):
        if e.get("type") == "way" and e.get("geometry") and len(e["geometry"]) > 1:
            gl = stransform(T, LineString([(q["lon"], q["lat"]) for q in e["geometry"]]))
            if gl.hausdorff_distance(g_este) < 30: tags_osm = {"osm_way_id": e["id"], "tags": e.get("tags")}
# sentido: del extremo cercano al barrio al extremo oriental
coords = list(g_este.coords)
if coords[0][0] > coords[-1][0]: coords = coords[::-1]
g_este = LineString(coords)
pa = feats("capas/igm/punto_acotado_p.geojson"); t_pa = STRtree([g for g, _ in pa])
vias_todas = vias + feats("capas/igm/via.geojson"); t_via = STRtree([g for g, _ in vias_todas])
veg = [g for n in ("matorral", "vegetacion_diversa", "pastizal") for g, _ in feats(f"capas/igm/{n}.geojson") if g.geom_type.endswith("Polygon")]
t_veg = STRtree(veg) if veg else None
grietas = [g for g, _ in feats("capas/igm/grieta_l.geojson")]
zfl = np.where(nod, np.nan, dem)


def zbil(x, y):
    c, r = ~TR * (x, y)
    return float(ndimage.map_coordinates(zfl, [[r - 0.5], [c - 0.5]], order=1)[0])


filas_e = []
Lg_e = g_este.length
for s_ in np.arange(0, Lg_e + 1, CELDA):
    p_ = g_este.interpolate(s_); x, y = p_.coords[0]
    p1, p2 = g_este.interpolate(max(0, s_ - 15)), g_este.interpolate(min(Lg_e, s_ + 15))
    dx, dy = p2.x - p1.x, p2.y - p1.y; n_ = math.hypot(dx, dy) or 1
    nx_, ny_ = -dy / n_, dx / n_                                         # normal izquierda (norte para un trazado O→E)
    trans = [(k, zbil(x + k * nx_, y + k * ny_)) for k in range(-90, 91, 15)]
    kmin, zmin = min(trans, key=lambda t_: t_[1])
    near_pa = sorted((pa[i][0].distance(p_), pa[i][1]["z"]) for i in t_pa.query(p_.buffer(150)))
    c_, r_ = ~TR * (x, y)
    filas_e.append([int(s_), *[round(v, 6) for v in TI(x, y)], round(zbil(x, y), 2), round(zmin, 2), round(zbil(x, y) - zmin, 2),
                    "S" if kmin < 0 else ("N" if kmin > 0 else "eje"), round(max(t_[1] for t_ in trans), 2),
                    round(min(gv.distance(p_) for gv in (vias_todas[i][0] for i in t_via.query(p_.buffer(2000))))) if len(t_via.query(p_.buffer(2000))) else None,
                    len(t_edif.query(p_.buffer(60), predicate="intersects")),
                    bool(t_veg is not None and len(t_veg.query(p_, predicate="intersects"))),
                    round(float(dist_mar[int(r_), int(c_)])),
                    round(near_pa[0][0]) if near_pa else None, near_pa[0][1] if near_pa else None])
cab_e = ["distancia_m", "lon", "lat", "cota_dsm_m", "cota_min_franja_180m_m", "trazado_sobre_minimo_m", "lado_del_minimo",
         "cota_max_franja_180m_m", "dist_via_m", "edificios_60m", "vegetacion_igm", "dist_mar_m", "dist_punto_acotado_igm_m", "z_punto_acotado_igm_m"]
# umbral acumulado: cota mínima de lámina para recorrer el corredor (franja ±90 m) desde el punto más cercano al barrio
i0 = int(np.argmin([g_este.interpolate(f[0]).distance(Point(TR * (c_lo + .5, r_lo + .5))) for f in filas_e]))
umb = []
for i, f in enumerate(filas_e):
    umb.append(round(max(ff[4] for ff in filas_e[i0:i + 1]), 2) if i >= i0 else None)
filas_e = [f + [u] for f, u in zip(filas_e, umb)]
guardar_csv("perfil_cauce_este.csv", cab_e + ["umbral_acumulado_desde_barrio_m"], filas_e)
from scipy.signal import find_peaks
zmin_arr = np.array([f[4] for f in filas_e])
pk, prop_pk = find_peaks(zmin_arr, prominence=3)
umbrales = []
for k, prom in zip(pk, prop_pk["prominences"]):
    f = filas_e[k]
    umbrales.append({"distancia_m": f[0], "lonlat": [f[1], f[2]], "cota_min_franja_m": f[4], "prominencia_m": round(float(prom), 1),
                     "dist_via_m": f[8], "edificios_60m": f[9], "vegetacion_igm": f[10], "z_punto_acotado_igm_cercano": f[13]})
R["cauce_este"] = {"fuente": p_este.get("fuente"), "atributos": p_este, "osm": tags_osm, "longitud_m": round(Lg_e),
                   "extremo_oriental_lonlat": [round(v, 5) for v in TI(*coords[-1])], "cota_extremo_oriental_m": round(zbil(*coords[-1]), 1),
                   "dist_mar_extremo_oriental_m": filas_e[-1][11], "distancia_al_punto_mas_cercano_al_barrio_m": filas_e[i0][0],
                   "umbral_para_recorrer_todo_el_trazado_m": umb[-1], "cota_rebose_barrio_m": round(cota_rebose, 2),
                   "trazado_sobre_minimo_franja_mediana_m": round(float(np.median([f[5] for f in filas_e])), 1),
                   "umbrales_detectados": umbrales,
                   "quebradas_igm_en_el_trazado_m": round(sum(g.intersection(g_este.buffer(60)).length for g, p in feats("capas/final/quebradas.geojson", lambda p: p.get("fuente", "").startswith("IGM")))),
                   "grietas_igm_a_menos_de_200m": sum(1 for g in grietas if g.distance(g_este) < 200)}
print("Cauce este:", {k: v for k, v in R["cauce_este"].items() if k != "umbrales_detectados"}, umbrales)

# ---------------------------------------------------------------- 8. contraste del DSM con los puntos acotados IGM 1:25 000
dif, dif_pob = [], []
for g, p in pa:
    if g.distance(Point(cx, cy)) > 5000 or not p.get("z"): continue
    zz = zbil(*g.coords[0])
    if np.isnan(zz) or zz <= 0: continue
    dif.append(zz - p["z"]); dif_pob.append(bool(pob_union.contains(g)))
dif = np.array(dif); dif_pob = np.array(dif_pob)
def est(v):
    return {"n": int(v.size), "media_m": round(float(v.mean()), 2), "mediana_m": round(float(np.median(v)), 2), "rmse_m": round(float(np.sqrt((v ** 2).mean())), 2),
            "p05_m": round(float(np.percentile(v, 5)), 2), "p95_m": round(float(np.percentile(v, 95)), 2)} if v.size else None
R["validacion_dsm"] = {"nota": "DSM − punto acotado IGM (z entero). Radio 5 km del barrio. El punto acotado IGM tiene su propio error (cartografía 1:25 000).",
                       "todos": est(dif), "en_zona_poblada": est(dif[dif_pob]), "fuera_zona_poblada": est(dif[~dif_pob])}
print("Validación DSM:", R["validacion_dsm"])

guardar_json("resumen.json", R)
print("Listo:", OUT)
