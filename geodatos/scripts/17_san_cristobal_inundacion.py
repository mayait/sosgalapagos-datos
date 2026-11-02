"""Estudio hidrológico preliminar de San Cristóbal: Puerto Baquerizo Moreno, El Progreso y la quebrada del campus USFQ / GSC.

Reutiliza los métodos de 12_cascada_analisis.py (La Cascada):
  - D8 (pysheds) sobre el DSM Copernicus GLO-30 con las quebradas IGM quemadas (−3 m), depresiones rellenadas y planos resueltos;
    sensibilidad con el DSM sin quemar.
  - Vasos (depresiones cerradas) y cota de rebose por relleno global tipo «priority-flood» desde el mar (equivale al camino de
    mínimo umbral, minimax, de cada celda hasta el mar). Al ser global no hay bordes de ventana. Robustez con el «proxy de suelo»
    (mínimo 3×3 del DSM).
  - SCS-CN (Ia = 0,2 S) + hidrograma unitario adimensional SCS (Tlag = 0,6 tc); tormenta SCS tipo II de 24 h; tc de Témez y de
    Kirpich (más SCS lag y velocidades TR-55 / Manning como contraste).
  - Contraste del DSM con los puntos acotados IGM 1:25 000.

Encargo:
  1. Cuencas que drenan a Puerto Baquerizo Moreno, a El Progreso y a otras huellas pobladas: llegadas de quebradas, área, cotas,
     pendientes, cauce principal, tc (rango de métodos) y dependencia del relleno de depresiones.
  2. Puntos potenciales de inundación: vasos con cota de rebose, volumen y exposición; llegadas de quebradas a la zona poblada;
     salidas al mar con o sin cauce cartografiado. Ranking con criterios explícitos (CRITERIOS).
  3. Quebrada que llega al campus USFQ / Galapagos Science Center (−0,8955; −89,6089): cuenca, perfil, entrada al campus, edificios
     expuestos, salida al mar y caudales de orden de magnitud (50/100/150 mm; CN 60–80).
  4. Contraste DSM − puntos acotados IGM en San Cristóbal.

Uso:  .venv/bin/python -I scripts/17_san_cristobal_inundacion.py      (desde geodatos/)
      Después, scripts/27_canadas_oficiales_san_cristobal.py añade a cuencas.geojson y puntos_inundacion.geojson la propiedad
      «cañada_oficial» (Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal).
Salidas: estudios/san-cristobal/datos/  cuencas.geojson, puntos_inundacion.geojson, vasos.geojson, quebrada_usfq.geojson,
         perfil_quebrada_usfq.csv, resumen.json

Limitación principal: modelo digital de SUPERFICIE de 30 m (incluye vegetación y techos), error vertical ±2–4 m. Las cotas
absolutas del DSM no deben usarse como umbrales. Todas las cifras son de orden de magnitud para priorizar estudios de campo.
"""
import csv, heapq, json, math, pathlib, tempfile, collections
import numpy as np, rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy import ndimage
from shapely.geometry import shape, mapping, LineString, Point, MultiPoint
from shapely.ops import unary_union, transform as stransform
from shapely.strtree import STRtree
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "estudios/san-cristobal/datos"
DEM_CRUDO = ROOT / "descargas/dem_recortes/san_cristobal_dem.tif"
DEM_QUEMADO = ROOT / "descargas/dem_recortes/san_cristobal_dem_quemado.tif"
CAMPUS_OSM = OUT / "insumos/campus_usfq_osm.geojson"        # polígono OSM «GAIAS Campus USFQ» (w62287405), Overpass 2-nov-2026
LLUVIAS_DIR = OUT / "lluvias"                                # datos del meteorólogo (si existen)
ISLA = "San Cristóbal"

# ---------------------------------------------------------------- parámetros
EPSG_UTM = 32716            # UTM 16S (San Cristóbal está al este de −90°)
CELDA = 30.0
AREA_MIN_LLEGADA_KM2 = 0.05  # llegada de quebrada: entrada a la zona poblada con al menos esta área aportante
AREA_CUENCA_PRINCIPAL_KM2 = 0.20
BUF_ZONA_VASOS_M = 100      # vasos que tocan la zona poblada + este margen
VOL_MIN_VASO_M3 = 300
PROF_ROBUSTA_M = 1.0        # profundidad mínima para considerar el vaso por encima del ruido del DSM (con persistencia en el proxy)
FRANJA_M = 20               # franja a cada lado del recorrido D8 para contar edificios (como el criterio CGREG de 20 m)
FRANJA_INCERT_M = 45        # franja ampliada: incertidumbre de posición de la línea D8 en un DSM de 30 m (±1,5 celdas)
DIST_CAUCE_MAPEADO_M = 30   # el recorrido D8 «tiene cauce» si hay quebrada IGM/OSM o franja CGREG a menos de esta distancia
RADIO_EVENTOS_M = 250
USFQ_LONLAT = (-89.6089, -0.8955)
RADIO_BUSQUEDA_USFQ_M = 400
CALLE_ANCHO_M = 8.0; CALLE_N = 0.02
MC_N = 100; MC_SEMILLA = 17; MC_VENTANA_M = 2400
MC_ESCENARIOS = ((1.0, 2.0), (2.0, 0.0), (2.0, 2.0), (3.0, 2.0))   # (desv. típica del error en m, radio de correlación en celdas)
LLUVIAS_MM = (50, 100, 150)
CN_ESCENARIOS = (60, 70, 80)
IA_RATIO = 0.2
DURACION_SIM_H = 30
CN_CLASE = {"parque / vegetación natural sobre lava": 60, "zona agrícola": 76, "urbano": 90}

T = Transformer.from_crs(4326, EPSG_UTM, always_xy=True).transform
TI = Transformer.from_crs(EPSG_UTM, 4326, always_xy=True).transform
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)
N8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def _fix(g):
    return g.buffer(0) if g.geom_type.endswith("Polygon") else g


def feats(rel, cond=lambda p: True, isla=ISLA):
    out = []
    for f in json.loads((ROOT / rel).read_text())["features"]:
        if not f.get("geometry"): continue
        if isla and f["properties"].get("isla", isla) != isla: continue
        if cond(f["properties"]): out.append((stransform(T, _fix(shape(f["geometry"]))), f["properties"]))
    return out


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


def fc(features):
    return {"type": "FeatureCollection", "features": features}


def guardar_json(nombre, obj):
    (OUT / nombre).write_text(json.dumps(obj, ensure_ascii=False, indent=1 if nombre == "resumen.json" else None,
                                         default=lambda o: o.item() if hasattr(o, "item") else str(o)))


def guardar_csv(nombre, cab, filas):
    with open(OUT / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(filas)


def lonlat(r, c):
    return TI(*(TR * (c + 0.5, r + 0.5)))


def ll(r, c):
    return [round(v, 5) for v in lonlat(r, c)]


def rc(lon, lat):
    c, r = ~TR * T(lon, lat); return int(r), int(c)


def a_utm(src_path):
    src = rasterio.open(src_path)
    tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG_UTM}", src.width, src.height, *src.bounds, resolution=CELDA)
    arr = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), arr, src_transform=src.transform, src_crs=src.crs, dst_transform=tr,
              dst_crs=f"EPSG:{EPSG_UTM}", resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    return arr, tr


def poligono(m):
    return unary_union([shape(s) for s, _ in shapes(m.astype("uint8"), mask=m, transform=TR)])


def rnd(x, n=2):
    return None if x is None else round(float(x), n)


OUT.mkdir(parents=True, exist_ok=True)
R = {"estudio": "San Cristóbal: inundación pluvial, análisis preliminar con DSM de 30 m", "parametros": {
    "dem": "Copernicus GLO-30 (DSM) reproyectado a UTM 16S, 30 m, bilineal", "epsg": EPSG_UTM,
    "area_min_llegada_km2": AREA_MIN_LLEGADA_KM2, "franja_edificios_m": FRANJA_M, "franja_incertidumbre_m": FRANJA_INCERT_M,
    "dist_cauce_mapeado_m": DIST_CAUCE_MAPEADO_M, "prof_robusta_vaso_m": PROF_ROBUSTA_M, "vol_min_vaso_m3": VOL_MIN_VASO_M3,
    "cn_por_clase_supuesto": CN_CLASE}}

# ---------------------------------------------------------------- 0. DEM, mar y relleno global
dem, TR = a_utm(DEM_CRUDO)
demq, _ = a_utm(DEM_QUEMADO)
H, W = dem.shape
nod = dem == -9999
sea = nod | (dem <= 0.5)          # incluye los huecos interiores sin dato (lagunas costeras de 1–4 m de entorno)
land = ~sea
rr, cc = np.indices((H, W))
pend = np.hypot(*np.gradient(np.where(nod, np.nan, dem), CELDA)) * 100
dist_mar = ndimage.distance_transform_edt(~sea) * CELDA


def relleno_global(sup, vecinos=8):
    """Priority-flood desde el mar: cota mínima de lámina para que el agua de cada celda llegue al mar (minimax)."""
    nb = N8 if vecinos == 8 else [(a, b) for a, b in N8 if not (a and b)]
    out = np.where(sea, 0.0, np.inf)
    vis = sea.copy()
    borde = sea & ndimage.binary_dilation(land, structure=np.ones((3, 3)))
    h = [(0.0, int(r), int(c)) for r, c in zip(*np.where(borde))]
    heapq.heapify(h)
    supf = sup.astype("float64")
    while h:
        e, r, c = heapq.heappop(h)
        for a, b in nb:
            r2, c2 = r + a, c + b
            if 0 <= r2 < H and 0 <= c2 < W and not vis[r2, c2]:
                vis[r2, c2] = True
                e2 = max(e, supf[r2, c2]); out[r2, c2] = e2
                heapq.heappush(h, (e2, r2, c2))
    # celdas de tierra en el borde del ráster no alcanzadas (no debería haber)
    out[~vis] = supf[~vis]
    return out


lleno = relleno_global(dem)
prof_dep = np.where(land, lleno - dem, 0.0)
proxy = ndimage.minimum_filter(np.where(nod, 9999, dem), size=3)          # «proxy de suelo»: mínimo 3×3 del DSM
proxy = np.where(sea, dem, proxy)
lleno_proxy = relleno_global(proxy)
prof_proxy = np.where(land, lleno_proxy - proxy, 0.0)
print("Relleno global listo; celdas en depresión >1 m:", int((prof_dep > 1).sum()))

# ---------------------------------------------------------------- 1. flujo D8
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td)
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=f"EPSG:{EPSG_UTM}", transform=TR, nodata=-9999)
    for n, a in (("q.tif", demq), ("c.tif", dem)):
        with rasterio.open(p / n, "w", **prof) as d: d.write(np.where(sea, -9999, a).astype("float32"), 1)
    g = Grid.from_raster(str(p / "q.tif")); dq = g.read_raster(str(p / "q.tif"))
    fdir = g.flowdir(g.resolve_flats(g.fill_depressions(g.fill_pits(dq))), dirmap=DIRMAP)
    F = np.asarray(fdir); A = np.asarray(g.accumulation(fdir, dirmap=DIRMAP)).astype("float64")
    g2 = Grid.from_raster(str(p / "c.tif")); dc_ = g2.read_raster(str(p / "c.tif"))
    F_crudo = np.asarray(g2.flowdir(g2.resolve_flats(g2.fill_depressions(g2.fill_pits(dc_))), dirmap=DIRMAP))
A[sea] = 0
AKM = A * CELDA ** 2 / 1e6


def siguiente(Fx):
    nr, nc = rr.copy(), cc.copy()
    for k, (a, b) in OFF.items():
        m = Fx == k; nr[m] += a; nc[m] += b
    ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W) & np.isin(Fx, list(OFF)) & land
    return (np.where(ok, nr, rr) * W + np.where(ok, nc, cc)).ravel()


nxt = siguiente(F); nxt_crudo = siguiente(F_crudo)
NN = H * W


def aguas_arriba(mask, nx):
    """Celdas de tierra fuera de mask cuyo flujo D8 llega a mask (salto de punteros)."""
    tg = np.where(mask.ravel(), np.arange(NN), -1); jj = nx.copy()
    for _ in range(int(np.ceil(np.log2(NN))) + 1):
        un = tg == -1; tg[un] = tg[jj[un]]; jj = jj[jj]
    return ((tg >= 0) & ~mask.ravel() & land.ravel()).reshape(H, W)


def aguas_abajo(r, c, parar=None, nx=None):
    nx = nxt if nx is None else nx
    p_ = [(r, c)]; i = r * W + c
    while True:
        j = nx[i]
        if j == i: break
        i = j; p_.append(divmod(i, W))
        if sea.ravel()[i] or (parar is not None and parar.ravel()[i]) or len(p_) > 20000: break
    return p_


def cauce(r, c):
    """Desde (r, c) hacia aguas arriba por la celda de mayor acumulación; devuelve de la cabecera a (r, c)."""
    path = [(r, c)]
    while True:
        best, ba = None, -1
        for k, (a, b) in OFF.items():
            ur, uc = r - a, c - b
            if 0 <= ur < H and 0 <= uc < W and F[ur, uc] == k and land[ur, uc] and A[ur, uc] > ba:
                best, ba = (ur, uc), A[ur, uc]
        if best is None: break
        r, c = best; path.append(best)
    return path[::-1]


def longitudes(path):
    return np.concatenate([[0], np.cumsum([CELDA * math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1)])])


def tiempos(path, pend_cuenca_pct):
    """Tiempos de concentración (h) por varios métodos para un cauce (de la cabecera al punto de control)."""
    z_ = np.array([float(dem[p_]) for p_ in path])
    dl = np.diff(longitudes(path))
    L = float(dl.sum()); Hh = float(z_[0] - z_[-1]); S = max(Hh / max(L, 1), 1e-4)
    k = 5
    sl = np.array([(z_[max(0, i - k)] - z_[min(len(z_) - 1, i + k + 1)]) / max(dl[max(0, i - k):i + k + 1].sum(), 1) for i in range(len(dl))]) if len(dl) else np.array([S])
    sl = np.clip(sl, 0.005, None)
    v_sup = 4.918 * np.sqrt(sl)                                       # TR-55, flujo concentrado sin pavimentar
    v_cau = (1 / 0.045) * 0.5 ** (2 / 3) * np.sqrt(sl)                # Manning n = 0,045, R = 0,5 m
    L_ft = L * 3.2808
    scs = {f"CN{cn}": round(L_ft ** 0.8 * ((1000 / cn - 10) + 1) ** 0.7 / (1900 * max(pend_cuenca_pct, 0.5) ** 0.5) / 0.6, 2) for cn in CN_ESCENARIOS}
    return {"L_km": round(L / 1000, 2), "desnivel_m": round(Hh, 1), "S_pct": round(S * 100, 2),
            "kirpich_h": round(0.0195 * L ** 0.77 * S ** -0.385 / 60, 3), "temez_h": round(0.3 * ((L / 1000) / S ** 0.25) ** 0.76, 3),
            "scs_lag_h": scs,
            "tr55_flujo_concentrado_h": round(float((dl / v_sup[:len(dl)]).sum() / 3600), 3) if len(dl) else 0.0,
            "manning_cauce_h": round(float((dl / v_cau[:len(dl)]).sum() / 3600), 3) if len(dl) else 0.0}


# ---------------------------------------------------------------- 2. capas vectoriales
zp = feats("capas/final/zonas_pobladas.geojson")
manz = feats("capas/final/manzanas_inec.geojson")
t_manz = STRtree([g for g, _ in manz])
edif = feats("capas/final/edificios_exposicion.geojson")
t_edif = STRtree([g for g, _ in edif])
queb = feats("capas/final/quebradas.geojson")
franja_cgreg = feats("capas/final/quebradas_franja20m_cgreg.geojson")
riesgos = feats("capas/final/riesgos_cgreg.geojson")
lodo = [g for g, p in riesgos if "lodo" in (p.get("tipo") or "").lower()]
eventos_todos = feats("capas/final/eventos_historicos.geojson")
_rep = collections.Counter((round(g.centroid.x), round(g.centroid.y)) for g, _ in eventos_todos)
# coordenadas repetidas ≥ 3 veces = ubicación genérica (centroide de la parroquia): no sirven para asociar el evento a un sitio
eventos = [(g, p) for g, p in eventos_todos if p.get("evento") in ("Inundación", "Deslizamiento", "Socavamiento")
           and _rep[(round(g.centroid.x), round(g.centroid.y))] < 3]
eventos_genericos = sum(1 for g, p in eventos_todos if p.get("evento") in ("Inundación", "Deslizamiento", "Socavamiento")
                        and _rep[(round(g.centroid.x), round(g.centroid.y))] >= 3)
poblados_igm = feats("capas/igm/poblado.geojson")
vias = feats("export/galapagos/vias.geojson")
t_vias = STRtree([g for g, _ in vias])
cauce_mapeado = unary_union([g for g, _ in queb] + [g for g, _ in franja_cgreg])
pa = feats("capas/igm/punto_acotado_p.geojson")
zfl = np.where(nod, np.nan, dem)


def zbil(x, y):
    c, r = ~TR * (x, y)
    return float(ndimage.map_coordinates(zfl, [[r - 0.5], [c - 0.5]], order=1)[0])


def exposicion(geom):
    ids = t_edif.query(geom, predicate="intersects")
    pob = viv = 0.0
    for i in t_manz.query(geom, predicate="intersects"):
        gm, pm = manz[i]
        fr = gm.intersection(geom).area / gm.area if gm.area else 0
        pob += fr * (pm.get("pob_estimada") or 0); viv += fr * (pm.get("viviendas") or 0)
    cen = sum(1 for i in ids if geom.contains(edif[i][0].centroid))
    return {"edificios_intersecan": len(ids), "edificios_centroide": cen, "poblacion": round(pob), "viviendas": round(viv)}


def eventos_cerca(geom, radio=RADIO_EVENTOS_M):
    out = []
    for g_, p_ in eventos:
        if g_.distance(geom) <= radio:
            out.append(f"{p_.get('evento')} {p_.get('año') or p_.get('anio') or ''}-{p_.get('mes') or ''} {str(p_.get('sector') or '').strip()[:40]}")
    return out


# zonas pobladas objetivo
pbm_parts = [g for g, p in zp if p.get("nombre") == "Puerto Baquerizo Moreno"]
pbm_parts += [g for g, p in zp if p.get("tipo") == "Huella edificada" and TI(*g.centroid.coords[0])[0] < -89.59]
pbm_parts += [g for g, p in manz if p["codigo"].startswith("200150")]
prog_pt = Point(T(-89.5547, -0.9091))
huellas = [g for g, p in zp if p.get("tipo") == "Huella edificada"]
prog_huella = min(huellas, key=lambda g: g.distance(prog_pt))
prog_parts = [prog_huella] + [g for g, p in manz if p["codigo"].startswith("200151")]
ZONAS = {"Puerto Baquerizo Moreno": unary_union(pbm_parts).buffer(0), "El Progreso": unary_union(prog_parts).buffer(0)}
for g in huellas:
    if g.intersects(ZONAS["Puerto Baquerizo Moreno"]) or g.intersects(ZONAS["El Progreso"]): continue
    cerca = min(poblados_igm, key=lambda gp: gp[0].distance(g))
    nm = cerca[1].get("nam") if cerca[0].distance(g) < 1500 else None
    base = f"Huella edificada cerca de {nm}" if nm else "Huella edificada sin nombre"
    k = base; i = 2
    while k in ZONAS: k = f"{base} ({i})"; i += 1
    ZONAS[k] = g
CODIGO = {k: ("PBM" if k.startswith("Puerto") else "PRO" if k == "El Progreso" else f"Z{i}") for i, k in enumerate(ZONAS, -1)}
R["codigos_zonas"] = CODIGO
zmask = {k: rasterize([(v, 1)], out_shape=(H, W), transform=TR, all_touched=True).astype(bool) & land for k, v in ZONAS.items()}
pob_any = np.zeros((H, W), bool)
for m in zmask.values(): pob_any |= m

# coberturas para el CN
agr = rasterize([(g, 1) for g, _ in feats("export/galapagos/zona_agricola.geojson")], out_shape=(H, W), transform=TR).astype(bool)


def cn_compuesto(m):
    f_urb = float((m & pob_any).sum() / m.sum()); f_agr = float((m & agr & ~pob_any).sum() / m.sum()); f_par = 1 - f_urb - f_agr
    cn = f_par * CN_CLASE["parque / vegetación natural sobre lava"] + f_agr * CN_CLASE["zona agrícola"] + f_urb * CN_CLASE["urbano"]
    return {"f_natural": round(f_par, 3), "f_agricola": round(f_agr, 3), "f_urbano": round(f_urb, 3), "cn_amc_ii": round(cn, 1),
            "cn_amc_iii": round(23 * cn / (10 + 0.13 * cn), 1)}


# ---------------------------------------------------------------- 3. hidrología SCS-CN + HU SCS
TII_H = [0, 2, 4, 6, 7, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 11.75, 12, 12.5, 13, 13.5, 14, 16, 20, 24]
TII_F = [0, .022, .048, .080, .098, .120, .133, .147, .163, .181, .204, .235, .283, .357, .663, .735, .772, .799, .820, .880, .952, 1.0]
UH_T = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5]
UH_Q = [0, .03, .1, .19, .31, .47, .66, .82, .93, .99, 1, .99, .93, .86, .78, .68, .56, .46, .39, .33, .28, .207, .147, .107, .077, .055, .04, .029, .021, .015, .011, .005, 0]


def hidrograma(area_km2, cn, tc_h, P=None, Pc_fun=None):
    """Caudal (m³/s) con SCS-CN y HU adimensional SCS. P: tormenta tipo II de 24 h; Pc_fun(t) → lluvia acumulada (mm)."""
    dt = min(1 / 6, max(tc_h / 6, 1 / 60))                       # paso ≤ tc/6 (cuencas pequeñas)
    t = np.arange(0, DURACION_SIM_H + 1e-9, dt)
    Pc = P * np.interp(t, TII_H, TII_F) if Pc_fun is None else Pc_fun(t)
    S = 25400 / cn - 254; Ia = IA_RATIO * S
    Q = np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0)
    exc = np.diff(Q, prepend=0)
    tp = dt / 2 + 0.6 * tc_h
    tt = np.arange(0, 5 * tp + dt, dt)
    u = np.interp(tt / tp, UH_T, UH_Q); u = u / (u.sum() * dt * 3600) * area_km2 * 1e6 / 1000
    q = np.convolve(exc, u)[: len(t)]
    return q, float(Q[-1]), t


def tabla_caudales(area_km2, tc_t, tc_k):
    filas = []
    for P in LLUVIAS_MM:
        for cn in CN_ESCENARIOS:
            q1, Qmm, _ = hidrograma(area_km2, cn, tc_t, P); q2, _, _ = hidrograma(area_km2, cn, tc_k, P)
            filas.append({"lluvia_24h_mm": P, "CN": cn, "escorrentia_mm": round(Qmm, 1), "coef_escorrentia": round(Qmm / P, 3),
                          "volumen_m3": int(Qmm / 1000 * area_km2 * 1e6), "q_pico_m3s_tc_temez": round(float(q1.max()), 2),
                          "q_pico_m3s_tc_kirpich": round(float(q2.max()), 2)})
    return filas


# ---------------------------------------------------------------- 4. cuencas y llegadas a cada zona poblada
cuencas_f, llegadas = [], []
R["zonas"] = {}
for zn, zm in zmask.items():
    up = aguas_arriba(zm, nxt)
    up_c = aguas_arriba(zm, nxt_crudo)
    entrada = up & zm.ravel()[nxt].reshape(H, W)
    er, ec = np.where(entrada)
    eid = np.zeros(NN, np.int32); eid[er * W + ec] = np.arange(1, len(er) + 1)
    lab = eid.copy(); j = nxt.copy(); upf = up.ravel()
    for _ in range(int(np.ceil(np.log2(NN))) + 1):
        un = upf & (lab == 0); lab[un] = lab[j[un]]; j = j[j]
    lab = np.where(upf, lab, 0).reshape(H, W)
    ids, cnt = np.unique(lab[lab > 0], return_counts=True)
    zinfo = {"area_zona_ha": round(ZONAS[zn].area / 1e4, 1), "area_aportante_total_km2": round(up.sum() * 900 / 1e6, 2),
             "sensibilidad_sin_quemar_km2": round(up_c.sum() * 900 / 1e6, 2),
             "celdas_comunes_con_y_sin_quemar_km2": round((up & up_c).sum() * 900 / 1e6, 2),
             "fraccion_en_depresiones_>1m": round(float((up & (prof_dep > 1)).sum() / max(up.sum(), 1)), 4),
             "cota_min_zona_m": rnd(dem[zm].min(), 1), "cota_mediana_zona_m": rnd(np.median(dem[zm]), 1), "cota_max_zona_m": rnd(dem[zm].max(), 1),
             "exposicion_zona": exposicion(ZONAS[zn]), "llegadas": []}
    resto = np.zeros((H, W), bool)
    ocupado = {}                                    # celda del recorrido en zona -> id de la llegada (mayor) que ya pasa por ella
    for e, n_ in sorted(zip(ids, cnt), key=lambda x: -x[1]):
        a_km2 = n_ * 900 / 1e6
        m = lab == e
        if a_km2 < AREA_MIN_LLEGADA_KM2:
            resto |= m; continue
        r0, c0 = er[e - 1], ec[e - 1]
        k_ll = f"{CODIGO[zn]}-L{len(zinfo['llegadas']) + 1:02d}"
        props = {"id": k_ll, "zona": zn, "tipo": "cuenca de llegada", "area_km2": round(a_km2, 3),
                 "cota_max_m": rnd(dem[m].max(), 1), "cota_min_m": rnd(dem[m].min(), 1), "cota_entrada_m": rnd(dem[r0, c0], 1),
                 "pendiente_media_pct": rnd(np.nanmean(pend[m]), 1), "pendiente_mediana_pct": rnd(np.nanmedian(pend[m]), 1),
                 "entrada_lonlat": ll(r0, c0), "fraccion_en_depresiones_>1m": round(float((m & (prof_dep > 1)).sum() / m.sum()), 4),
                 "fraccion_tambien_sin_quemar": round(float((m & up_c).sum() / m.sum()), 3), **cn_compuesto(m)}
        path = cauce(r0, c0)
        tc = tiempos(path, props["pendiente_media_pct"])
        props.update({"cauce_longitud_km": tc["L_km"], "cauce_cota_cabecera_m": rnd(dem[path[0]], 1), "cauce_pendiente_pct": tc["S_pct"],
                      "tc_kirpich_h": tc["kirpich_h"], "tc_temez_h": tc["temez_h"], "tc_scs_lag_h": tc["scs_lag_h"],
                      "tc_tr55_h": tc["tr55_flujo_concentrado_h"], "tc_manning_h": tc["manning_cauce_h"]})
        tcs = [tc["kirpich_h"], tc["temez_h"], tc["tr55_flujo_concentrado_h"], tc["manning_cauce_h"], *tc["scs_lag_h"].values()]
        props["tc_rango_h"] = [round(min(tcs), 2), round(max(tcs), 2)]
        q100 = tabla_caudales(a_km2, max(tc["temez_h"], 0.05), max(tc["kirpich_h"], 0.05))
        props["q_pico_100mm_CN70_m3s"] = [x for x in q100 if x["lluvia_24h_mm"] == 100 and x["CN"] == 70][0]["q_pico_m3s_tc_temez"]
        props["q_pico_100mm_CN60_80_rango_m3s"] = [min(x["q_pico_m3s_tc_temez"] for x in q100 if x["lluvia_24h_mm"] == 100),
                                                   max(x["q_pico_m3s_tc_kirpich"] for x in q100 if x["lluvia_24h_mm"] == 100)]
        # recorrido dentro de la zona y hasta el mar
        rec = aguas_abajo(r0, c0)
        in_z = [p_ for p_ in rec if zm[p_]]
        ln_tot = LineString([TR * (b + .5, a + .5) for a, b in rec]) if len(rec) > 1 else None
        ln_z = LineString([TR * (b + .5, a + .5) for a, b in in_z]) if len(in_z) > 1 else None
        llega_mar = bool(sea[rec[-1]])
        if ln_z is not None and ln_z.length > 0:
            pts = [ln_z.interpolate(s_) for s_ in np.arange(0, ln_z.length + 1, 15)]
            f_cauce = float(np.mean([cauce_mapeado.distance(q_) <= DIST_CAUCE_MAPEADO_M for q_ in pts]))
        else:
            f_cauce = None
        # tramo propio: recorrido en zona hasta unirse al de una llegada mayor (evita contar dos veces la misma calle o cauce)
        propio, une_a = [], None
        for p_ in in_z:
            if p_ in ocupado: une_a = ocupado[p_]; break
            propio.append(p_)
        for p_ in in_z: ocupado.setdefault(p_, k_ll)
        ln_p = LineString([TR * (b + .5, a + .5) for a, b in propio]) if len(propio) > 1 else (Point(TR * (propio[0][1] + .5, propio[0][0] + .5)) if propio else None)
        if ln_p is not None and ln_p.length > 0:
            pts_p = [ln_p.interpolate(s_) for s_ in np.arange(0, ln_p.length + 1, 15)]
            f_cauce_p = float(np.mean([cauce_mapeado.distance(q_) <= DIST_CAUCE_MAPEADO_M for q_ in pts_p]))
        else:
            f_cauce_p = None
        inicio = LineString([TR * (b + .5, a + .5) for a, b in rec[:11]]) if len(rec) > 1 else Point(TR * (c0 + .5, r0 + .5))
        tramo_final = LineString([TR * (b + .5, a + .5) for a, b in rec[-6:]]) if len(rec) >= 2 else None
        salida_con_cauce = bool(tramo_final is not None and cauce_mapeado.distance(tramo_final) <= DIST_CAUCE_MAPEADO_M)
        rec_props = {"recorrido_total_m": round(ln_tot.length) if ln_tot else 0, "recorrido_en_zona_m": round(ln_z.length) if ln_z else 0,
                     "edificios_franja_20m_en_zona": len(t_edif.query(ln_z.buffer(FRANJA_M), predicate="intersects")) if ln_z else 0,
                     "edificios_franja_45m_en_zona": len(t_edif.query(ln_z.buffer(FRANJA_INCERT_M), predicate="intersects")) if ln_z else 0,
                     "fraccion_recorrido_en_zona_con_cauce_mapeado": rnd(f_cauce, 2), "llega_al_mar": llega_mar,
                     "salida_mar_lonlat": ll(*rec[-1]), "salida_mar_con_cauce_mapeado": salida_con_cauce,
                     "zonas_atravesadas_aguas_abajo": sorted({z2 for z2, m2 in zmask.items() if z2 != zn and any(m2[p_] for p_ in rec)}),
                     "tramo_propio_en_zona_m": round(ln_p.length) if ln_p is not None else 0, "se_une_a": une_a,
                     "edificios_franja_20m_tramo_propio": len(t_edif.query(ln_p.buffer(FRANJA_M), predicate="intersects")) if ln_p is not None else 0,
                     "edificios_franja_45m_tramo_propio": len(t_edif.query(ln_p.buffer(FRANJA_INCERT_M), predicate="intersects")) if ln_p is not None else 0,
                     "fraccion_tramo_propio_con_cauce_mapeado": rnd(f_cauce_p, 2),
                     "inicio_en_flujo_lodo_o_franja_cgreg": bool(any(g_.intersects(inicio) for g_ in lodo) or any(g_.intersects(inicio) for g_, _ in franja_cgreg)),
                     "pendiente_entrada_pct": rnd(np.nanmean([pend[p_] for p_ in path[-5:]]), 1),
                     "eventos_sngr_250m": eventos_cerca(ln_p if ln_p is not None else Point(TR * (c0 + .5, r0 + .5)))}
        props.update(rec_props)
        geom = poligono(m)
        cuencas_f.append({"type": "Feature", "properties": dict(props), "geometry": r6(geom)})
        cuencas_f.append({"type": "Feature", "properties": {"id": k_ll, "zona": zn, "tipo": "cauce principal (D8)", "longitud_km": tc["L_km"]},
                          "geometry": r6(LineString([TR * (b + .5, a + .5) for a, b in path]))})
        if ln_tot is not None:
            cuencas_f.append({"type": "Feature", "properties": {"id": k_ll, "zona": zn, "tipo": "recorrido D8 hasta el mar",
                                                                 "longitud_m": round(ln_tot.length), "con_cauce_mapeado_en_zona": rnd(f_cauce, 2)},
                              "geometry": r6(ln_tot)})
        props["_rec"] = rec; props["_lnz"] = ln_z; props["_lnp"] = ln_p; props["_mask"] = m; props["_tabla_q"] = q100
        llegadas.append(props)
        zinfo["llegadas"].append({k_: v for k_, v in props.items() if not k_.startswith("_")})
    zinfo["escorrentia_de_ladera_km2"] = round(resto.sum() * 900 / 1e6, 3)
    zinfo["n_llegadas"] = len(zinfo["llegadas"])
    R["zonas"][zn] = zinfo
    print(f"{zn}: aporte {zinfo['area_aportante_total_km2']} km², {zinfo['n_llegadas']} llegadas ≥ {AREA_MIN_LLEGADA_KM2} km²")
    for l_ in zinfo["llegadas"][:6]:
        print("   ", l_["id"], l_["area_km2"], "km²", l_["entrada_lonlat"], "tc", l_["tc_rango_h"], "edif20", l_["edificios_franja_20m_en_zona"],
              "cauce", l_["fraccion_recorrido_en_zona_con_cauce_mapeado"], "salida", l_["salida_mar_lonlat"], l_["salida_mar_con_cauce_mapeado"])
guardar_json("cuencas.geojson", fc(cuencas_f))

# ---------------------------------------------------------------- 5. vasos (depresiones cerradas) en y junto a las zonas pobladas
lb_dep, n_dep = ndimage.label(prof_dep > 0.001, structure=np.ones((3, 3)))
zona_buf = rasterize([(g.buffer(BUF_ZONA_VASOS_M), 1) for g in ZONAS.values()], out_shape=(H, W), transform=TR, all_touched=True).astype(bool)
sel_ids = sorted(set(np.unique(lb_dep[zona_buf & (lb_dep > 0)]).tolist()))
vasos, vasos_f = [], []
objs = ndimage.find_objects(lb_dep)
for i in sel_ids:
    sl_ = objs[i - 1]
    r_a, r_b = max(sl_[0].start - 2, 0), min(sl_[0].stop + 2, H); c_a, c_b = max(sl_[1].start - 2, 0), min(sl_[1].stop + 2, W)
    sub = lb_dep[r_a:r_b, c_a:c_b] == i
    m = np.zeros((H, W), bool); m[r_a:r_b, c_a:c_b] = sub
    vol = float(prof_dep[m].sum() * 900)
    if vol < VOL_MIN_VASO_M3: continue
    rebose = float(lleno[m].max())
    fondo_idx = np.argmin(np.where(m, dem, np.inf)); fr_, fc_ = divmod(int(fondo_idx), W)
    anillo = ndimage.binary_dilation(m, structure=np.ones((3, 3))) & ~m
    ar, ac = np.where(anillo); k_ = int(np.argmin(dem[ar, ac])); sr_, sc_ = ar[k_], ac[k_]       # punto de vertido
    geom = poligono(m)
    ex = exposicion(geom)
    spill_pt = Point(TR * (sc_ + .5, sr_ + .5))
    edif_umbral = len(t_edif.query(spill_pt.buffer(20), predicate="intersects"))
    via_umbral = len(t_vias.query(spill_pt.buffer(20), predicate="intersects"))
    pmax = float(prof_dep[m].max())
    persiste = float(prof_proxy[ndimage.binary_dilation(m, structure=np.ones((3, 3)))].max())
    robusto = bool(pmax >= PROF_ROBUSTA_M and persiste >= 0.3)
    zonas_v = sorted(z for z, g_ in ZONAS.items() if g_.buffer(BUF_ZONA_VASOS_M).intersects(geom))
    aporte = float(AKM[m].max())
    props = {"id": None, "tipo": "vaso", "zonas": zonas_v, "area_ha": round(m.sum() * 900 / 1e4, 2), "volumen_m3": int(vol),
             "prof_max_m": round(pmax, 2), "cota_fondo_m": rnd(dem[fr_, fc_]), "cota_rebose_m": round(rebose, 2),
             "fondo_lonlat": ll(fr_, fc_), "vertido_lonlat": ll(sr_, sc_), "area_aportante_km2": round(aporte, 3),
             "edificios_a_20m_del_vertido": edif_umbral, "vias_a_20m_del_vertido": via_umbral,
             "prof_max_proxy_suelo_m": round(persiste, 2), "robusto": robusto, **ex,
             "eventos_sngr_250m": eventos_cerca(geom), "en_flujo_lodo_o_franja_cgreg": bool(any(g_.intersects(geom) for g_ in lodo) or any(g_.intersects(geom) for g_, _ in franja_cgreg)),
             "dist_cauce_mapeado_m": round(cauce_mapeado.distance(geom))}
    if not robusto:
        props["nota"] = ("Profundidad < 1 m o no persiste con el proxy de suelo: dentro del ruido del DSM.")
    elif edif_umbral or via_umbral:
        props["nota"] = ("El umbral de vertido está junto a edificios o vías: puede ser un techo/terraplén del DSM (artefacto) "
                         "o un cierre real con alcantarilla. Verificar en campo.")
    props["_mask"] = m
    vasos.append(props)
vasos.sort(key=lambda v: -v["volumen_m3"])
for k, v in enumerate(vasos, 1):
    v["id"] = f"V{k:02d}"
    vasos_f.append({"type": "Feature", "properties": {k_: v_ for k_, v_ in v.items() if not k_.startswith("_")}, "geometry": r6(poligono(v["_mask"]))})
guardar_json("vasos.geojson", fc(vasos_f))
R["vasos"] = {"metodo": "Relleno global priority-flood desde el mar sobre el DSM crudo (8 vecinos); vaso = componente con lámina > 1 mm. "
                        "Robusto si prof. máx. ≥ 1 m y persiste (≥ 0,3 m) con el proxy de suelo (mínimo 3×3). Sin ventana: no hay "
                        "bordes artificiales. Exposición solo bajo la cota de rebose.",
              "n": len(vasos), "n_robustos": sum(v["robusto"] for v in vasos),
              "nota_eventos": f"{eventos_genericos} eventos SNGR de inundación/deslizamiento con coordenada genérica excluidos de la proximidad",
              "lista": [{k_: v_ for k_, v_ in v.items() if not k_.startswith("_")} for v in vasos]}
print("Vasos:", len(vasos), "robustos:", R["vasos"]["n_robustos"])
for v in vasos[:12]:
    print("   ", v["id"], v["zonas"], v["volumen_m3"], "m3 prof", v["prof_max_m"], "rob", v["robusto"], "edif", v["edificios_intersecan"], v["fondo_lonlat"], "aporte", v["area_aportante_km2"])

# ---------------------------------------------------------------- 6. puntos potenciales de inundación y ranking
CRITERIOS = {
    "A_area_aportante": "0: < 0,1 km²; 1: 0,1–0,5; 2: 0,5–2; 3: ≥ 2 km²",
    "E_exposicion": "edificios en la franja de 20 m del tramo propio dentro de la zona poblada (llegadas: hasta unirse a una llegada mayor), "
                    "a ≤ 45 m del tramo final (salidas) o que intersecan el vaso: "
                    "0: < 5; 1: 5–24; 2: 25–99; 3: ≥ 100",
    "C_confinamiento": "1 si la llegada recorre su tramo propio sin cauce cartografiado en más de la mitad, si la salida al mar no tiene "
                       "cauce cartografiado, o si el vaso es robusto (≥ 1 m y persiste con el proxy de suelo)",
    "H_antecedente": "1 si hay un evento SNGR de inundación, deslizamiento o socavamiento a ≤ 250 m (reportado, no verificado; se "
                     "excluyen los eventos con coordenada genérica repetida)",
    "L_cgreg": "1 si los primeros ~300 m del recorrido (llegadas), el tramo final (salidas) o el vaso tocan una zona CGREG de flujos de "
               "lodo y escombros por El Niño o una franja CGREG de quebrada",
    "total": "suma A + E + C + H + L (máximo 9); desempate por área aportante × edificios",
}


def pts_area(a):
    return 0 if a < 0.1 else (1 if a < 0.5 else (2 if a < 2 else 3))


def pts_expo(n):
    return 0 if n < 5 else (1 if n < 25 else (2 if n < 100 else 3))


puntos = []
for l_ in llegadas:
    fz = l_["fraccion_tramo_propio_con_cauce_mapeado"]
    crit = {"A": pts_area(l_["area_km2"]), "E": pts_expo(l_["edificios_franja_20m_tramo_propio"]),
            "C": int(fz is not None and fz < 0.5), "H": int(bool(l_["eventos_sngr_250m"])), "L": int(l_["inicio_en_flujo_lodo_o_franja_cgreg"])}
    puntos.append({"id": l_["id"], "tipo": "llegada de quebrada", "zona": l_["zona"], "lonlat": l_["entrada_lonlat"],
                   "area_aportante_km2": l_["area_km2"], "edificios": l_["edificios_franja_20m_tramo_propio"],
                   "edificios_franja_45m": l_["edificios_franja_45m_tramo_propio"],
                   "descripcion": (f"Entrada D8 a la zona poblada; tramo propio de {l_['tramo_propio_en_zona_m']} m "
                                   f"({'sin cauce cartografiado' if not fz else f'{round(100 * fz)} % con cauce cartografiado'})"
                                   + (f", luego se une a {l_['se_une_a']}" if l_["se_une_a"] else "")
                                   + (f"; sale al mar en {l_['salida_mar_lonlat']}" if l_["llega_al_mar"] else "") + "."),
                   "salida_mar_lonlat": l_["salida_mar_lonlat"], "salida_mar_con_cauce": l_["salida_mar_con_cauce_mapeado"],
                   "q_pico_100mm_CN70_m3s": l_["q_pico_100mm_CN70_m3s"], "tc_rango_h": l_["tc_rango_h"],
                   "eventos_sngr_250m": l_["eventos_sngr_250m"], "criterios": crit, "puntuacion": sum(crit.values()),
                   "_geom": Point(T(*l_["entrada_lonlat"]))})
# salidas al mar de las llegadas de Puerto Baquerizo Moreno: una por desembocadura
salidas = collections.defaultdict(list)
for l_ in llegadas:
    if l_["llega_al_mar"] and l_["zona"] == "Puerto Baquerizo Moreno": salidas[tuple(l_["_rec"][-2] if len(l_["_rec"]) > 1 else l_["_rec"][-1])].append(l_)
for k, (cel, ls_) in enumerate(sorted(salidas.items(), key=lambda kv: -AKM[kv[0]]), 1):
    rec_ = ls_[0]["_rec"]; j = rec_.index(cel)
    fin = LineString([TR * (b + .5, a + .5) for a, b in rec_[max(0, j - 5):j + 2]])
    con = bool(cauce_mapeado.distance(fin) <= DIST_CAUCE_MAPEADO_M)
    ne = len(t_edif.query(fin.buffer(FRANJA_INCERT_M), predicate="intersects"))
    crit = {"A": pts_area(float(AKM[cel])), "E": pts_expo(ne), "C": int(not con), "H": int(bool(eventos_cerca(fin))),
            "L": int(any(g_.intersects(fin) for g_ in lodo))}
    st_s = cauce(*cel); m_s = np.zeros((H, W), bool); m_s[cel] = True
    t_s = tiempos(st_s, float(np.nanmean(pend[aguas_arriba(m_s, nxt) | m_s])))
    q_s = tabla_caudales(float(AKM[cel]), max(t_s["temez_h"], 1 / 60), max(t_s["kirpich_h"], 1 / 60))
    q100 = [x for x in q_s if x["lluvia_24h_mm"] == 100]
    puntos.append({"id": f"PBM-S{k:02d}", "tipo": "salida al mar " + ("con cauce cartografiado" if con else "sin cauce cartografiado"),
                   "tc_kirpich_h": t_s["kirpich_h"], "tc_temez_h": t_s["temez_h"], "cauce_longitud_km": t_s["L_km"],
                   "q_pico_100mm_CN70_m3s": [x for x in q100 if x["CN"] == 70][0]["q_pico_m3s_tc_temez"],
                   "q_pico_100mm_CN60_80_rango_m3s": [min(x["q_pico_m3s_tc_temez"] for x in q100), max(x["q_pico_m3s_tc_kirpich"] for x in q100)],
                   "caudales_tormenta_tipo_II": q_s,
                   "zona": "Puerto Baquerizo Moreno", "lonlat": ll(*cel), "area_aportante_km2": round(float(AKM[cel]), 3), "edificios": ne,
                   "llegadas": [x["id"] for x in ls_],
                   "descripcion": (f"Último tramo (≈150 m) del recorrido D8 antes del mar; edificios a ≤ {FRANJA_INCERT_M} m. "
                                   f"Recibe las llegadas {', '.join(x['id'] for x in ls_)}."),
                   "eventos_sngr_250m": eventos_cerca(fin), "criterios": crit, "puntuacion": sum(crit.values()), "_geom": Point(TR * (cel[1] + .5, cel[0] + .5))})
for v in vasos:
    if v["edificios_intersecan"] == 0 and not v["robusto"]: continue
    crit = {"A": pts_area(v["area_aportante_km2"]), "E": pts_expo(v["edificios_intersecan"]), "C": int(v["robusto"]),
            "H": int(bool(v["eventos_sngr_250m"])), "L": int(v["en_flujo_lodo_o_franja_cgreg"])}
    puntos.append({"id": v["id"], "tipo": "vaso (depresión cerrada)", "zona": ", ".join(v["zonas"]), "lonlat": v["fondo_lonlat"],
                   "area_aportante_km2": v["area_aportante_km2"], "edificios": v["edificios_intersecan"],
                   "descripcion": (f"Depresión de {v['area_ha']} ha, {v['volumen_m3']} m³ y {v['prof_max_m']} m de profundidad máxima; "
                                   f"vierte en {v['vertido_lonlat']}. {'Robusta.' if v['robusto'] else 'Dentro del ruido del DSM.'}"),
                   "volumen_m3": v["volumen_m3"], "poblacion": v["poblacion"], "robusto": v["robusto"],
                   "eventos_sngr_250m": v["eventos_sngr_250m"], "criterios": crit, "puntuacion": sum(crit.values()),
                   "_geom": Point(T(*v["fondo_lonlat"]))})
rank = sorted([p_ for p_ in puntos if p_["puntuacion"] is not None],
              key=lambda p_: (-p_["puntuacion"], -(p_["area_aportante_km2"] or 0) * max(p_["edificios"] or 0, 1)))
for k, p_ in enumerate(rank, 1): p_["ranking"] = k
pfeats = [{"type": "Feature", "properties": {k_: v_ for k_, v_ in p_.items() if not k_.startswith("_")}, "geometry": r6(p_["_geom"])} for p_ in puntos]
guardar_json("puntos_inundacion.geojson", fc(pfeats))
R["puntos_inundacion"] = {"criterios": CRITERIOS,
                          "salidas_al_mar": [{k_: v_ for k_, v_ in p_.items() if not k_.startswith("_")} for p_ in puntos if p_["tipo"].startswith("salida")],
                          "ranking": [{k_: p_[k_] for k_ in ("ranking", "id", "tipo", "zona", "lonlat", "area_aportante_km2",
                                                                                      "edificios", "puntuacion", "criterios", "eventos_sngr_250m")} for p_ in rank]}
print("Ranking:")
for p_ in rank[:15]:
    print("   ", p_["ranking"], p_["id"], p_["tipo"], p_["zona"], p_["lonlat"], p_["area_aportante_km2"], p_["edificios"], p_["puntuacion"], p_["criterios"])

# ---------------------------------------------------------------- 7. quebrada del campus USFQ / GSC
ux, uy = T(*USFQ_LONLAT)
upt = Point(ux, uy)
campus_osm = [stransform(T, shape(f["geometry"])) for f in json.loads(CAMPUS_OSM.read_text())["features"]] if CAMPUS_OSM.exists() else []
edif_univ = [(g, p) for g, p in edif if p.get("tipo") == "university" and g.distance(upt) < 150]
campus = unary_union(campus_osm + [g for g, _ in edif_univ]).convex_hull.buffer(15)
campus_edif = [(i, g, p) for i, (g, p) in enumerate(edif) if g.intersects(campus)]
cm = rasterize([(campus, 1)], out_shape=(H, W), transform=TR, all_touched=True).astype(bool) & land
R["usfq"] = {"punto": USFQ_LONLAT, "campus_aproximado": {
    "definicion": "Envolvente convexa del polígono OSM «GAIAS Campus USFQ» y de los edificios OSM con building=university a < 150 m "
                  "(USFQ Extension Galapagos, Galapagos Science Center, Laboratorio de Salud Animal) + 15 m. El límite real del campus "
                  "no está cartografiado.", "area_ha": round(campus.area / 1e4, 2),
    "edificios_universitarios": [p.get("nombre") for _, p in edif_univ], "edificios_en_campus": len(campus_edif),
    "cota_dsm_edificios_m": [rnd(min(zbil(*g.centroid.coords[0]) for _, g, _ in campus_edif)), rnd(max(zbil(*g.centroid.coords[0]) for _, g, _ in campus_edif))],
    "dist_mar_m": round(min(dist_mar[rc(*TI(*g.centroid.coords[0]))] for _, g, _ in campus_edif))}}


def lineas_cercanas(a_min):
    """Recorridos D8 con área ≥ a_min que pasan a ≤ RADIO_BUSQUEDA_USFQ_M del campus, agrupados por desembocadura."""
    r_u, c_u = rc(*USFQ_LONLAT); rad = int(RADIO_BUSQUEDA_USFQ_M / CELDA) + 2
    grupos = collections.defaultdict(list)
    for r in range(r_u - rad, r_u + rad + 1):
        for c in range(c_u - rad, c_u + rad + 1):
            if not land[r, c] or AKM[r, c] < a_min: continue
            d_ = Point(TR * (c + .5, r + .5)).distance(campus)
            if d_ <= RADIO_BUSQUEDA_USFQ_M: grupos[aguas_abajo(r, c)[-1]].append((d_, -AKM[r, c], r, c))
    out = []
    for sal, lst in grupos.items():
        d_min, a_neg, r_m, c_m = min(lst)
        out.append({"salida_mar_lonlat": ll(*sal), "dist_min_al_campus_m": round(d_min), "area_en_punto_mas_cercano_km2": round(-a_neg, 3),
                    "area_en_desembocadura_km2": round(float(AKM[aguas_abajo(r_m, c_m)[-2]]), 3), "punto_mas_cercano_lonlat": ll(r_m, c_m), "_rc": (r_m, c_m)})
    return sorted(out, key=lambda x: x["dist_min_al_campus_m"])


contexto = lineas_cercanas(0.05)
principales = lineas_cercanas(AREA_CUENCA_PRINCIPAL_KM2)
q_sel = principales[0]                            # la quebrada (≥ 0,2 km²) que pasa más cerca del campus
r_in, c_in = np.unravel_index(np.argmax(np.where(cm, AKM, -1)), AKM.shape)
R["usfq"]["recorridos_d8_a_menos_de_400m"] = [{k_: v_ for k_, v_ in x.items() if not k_.startswith("_")} for x in contexto]
R["usfq"]["criterio_seleccion"] = (f"Quebrada del campus = recorrido D8 con ≥ {AREA_CUENCA_PRINCIPAL_KM2} km² que pasa más cerca del campus aproximado. "
                                   "Dos puntos de control: (1) celda más cercana al campus; (2) última celda en tierra antes del mar.")
r_q, c_q = q_sel["_rc"]
stem = cauce(r_q, c_q)
abajo = aguas_abajo(r_q, c_q)
full = stem + abajo[1:]
dl = longitudes(full)
ctrl_k = len(stem) - 1
r_o, c_o = abajo[-2] if sea[abajo[-1]] else abajo[-1]         # última celda en tierra
ctrl = {"1_mas_cercano_al_campus": (r_q, c_q), "2_desembocadura": (r_o, c_o)}
qinfo, cuencas_q = {}, {}
for nm, (r_, c_) in ctrl.items():
    m1 = np.zeros((H, W), bool); m1[r_, c_] = True
    upm = aguas_arriba(m1, nxt) | m1
    upc = aguas_arriba(m1, nxt_crudo) | m1
    a_ = float(upm.sum() * 900 / 1e6); pm_ = float(np.nanmean(pend[upm]))
    st_ = cauce(r_, c_)
    tq = tiempos(st_, pm_)
    tcs = [tq["kirpich_h"], tq["temez_h"], tq["tr55_flujo_concentrado_h"], tq["manning_cauce_h"], *tq["scs_lag_h"].values()]
    cuencas_q[nm] = (upm, st_)
    qinfo[nm] = {"lonlat": ll(r_, c_), "cota_m": rnd(dem[r_, c_], 1), "area_km2": round(a_, 3), "area_sin_quemar_km2": round(float(upc.sum() * 900 / 1e6), 3),
                 "cota_max_cuenca_m": rnd(dem[upm].max(), 1), "pendiente_media_cuenca_pct": round(pm_, 1),
                 "fraccion_en_depresiones_>1m": round(float((upm & (prof_dep > 1)).sum() / upm.sum()), 4), "cauce": tq,
                 "tc_rango_h": [round(min(tcs), 3), round(max(tcs), 3)], "cn": cn_compuesto(upm),
                 "caudales_tormenta_tipo_II": tabla_caudales(a_, max(tq["temez_h"], 1 / 60), max(tq["kirpich_h"], 1 / 60))}
ln_full = LineString([TR * (b + .5, a + .5) for a, b in full])
ln_stem = LineString([TR * (b + .5, a + .5) for a, b in stem]) if len(stem) > 1 else None
ln_abajo = LineString([TR * (b + .5, a + .5) for a, b in abajo]) if len(abajo) > 1 else None
k_ent = next((k for k, p_ in enumerate(full) if Point(TR * (p_[1] + .5, p_[0] + .5)).distance(campus) <= 0), None)
edif_franja = {buf: [i for i in t_edif.query(ln_full.buffer(buf), predicate="intersects") if edif[i][0].intersects(campus)] for buf in (FRANJA_M, FRANJA_INCERT_M)}
# desnivel de cada edificio del campus sobre la quebrada (proxy de suelo en el edificio − DSM en la celda más cercana del cauce)
celdas_full = np.array([TR * (b + .5, a + .5) for a, b in full])
desn = []
for i, g, p in campus_edif:
    x, y = g.centroid.coords[0]
    k = int(np.argmin(np.hypot(celdas_full[:, 0] - x, celdas_full[:, 1] - y)))
    r_e, c_e = rc(*TI(x, y))
    desn.append({"edificio": p.get("nombre") or p.get("osm_id") or "Open Buildings", "dist_quebrada_m": round(float(np.hypot(*(celdas_full[k] - (x, y))))),
                 "cota_proxy_suelo_m": rnd(proxy[r_e, c_e], 1), "cota_cauce_mas_cercano_m": rnd(dem[full[k]], 1),
                 "desnivel_sobre_cauce_m": rnd(proxy[r_e, c_e] - dem[full[k]], 1)})
vasos_campus = [v["id"] for v in vasos if poligono(v["_mask"]).distance(campus) <= 150]
# escorrentía local que llega al campus (máxima acumulación dentro del polígono)
st_loc = cauce(r_in, c_in); t_loc = tiempos(st_loc, float(np.nanmean(pend[aguas_arriba(np.eye(1, NN, r_in * W + c_in, dtype=bool).reshape(H, W), nxt)]))) if len(st_loc) > 1 else None
loc_area = float(AKM[r_in, c_in])
cruces_via = sorted({str(p.get("nombre") or p.get("tipo_osm")) for gv, p in vias if ln_abajo is not None and gv.intersects(ln_abajo)})
puente_osm = [p for g, p in feats("capas/final/puntos_clave.geojson", lambda p: p.get("subtipo") == "puente") if g.distance(ln_full) < 150]
edif_aguas_abajo = len(t_edif.query(ln_abajo.buffer(FRANJA_M), predicate="intersects")) if ln_abajo else 0
fr_cauce_abajo = (float(np.mean([cauce_mapeado.distance(ln_abajo.interpolate(s_)) <= DIST_CAUCE_MAPEADO_M for s_ in np.arange(0, ln_abajo.length + 1, 15)]))
                  if ln_abajo else None)
R["usfq"]["quebrada"] = {
    "puntos_de_control": qinfo, "dist_minima_al_campus_m": q_sel["dist_min_al_campus_m"],
    "entra_al_campus_segun_d8": k_ent is not None, "entrada_al_campus_lonlat": ll(*full[k_ent]) if k_ent is not None else None,
    "edificios_campus_franja_20m": [edif[i][1].get("nombre") or edif[i][1].get("osm_id") or "Open Buildings" for i in edif_franja[FRANJA_M]],
    "edificios_campus_franja_45m": [edif[i][1].get("nombre") or edif[i][1].get("osm_id") or "Open Buildings" for i in edif_franja[FRANJA_INCERT_M]],
    "desnivel_edificios_campus_sobre_cauce": desn,
    "vasos_a_menos_de_150m_del_campus": vasos_campus,
    "franjas_quebrada_cgreg_dist_al_campus_m": sorted(round(g.distance(campus)) for g, _ in franja_cgreg if g.distance(campus) < 400),
    "flujos_lodo_cgreg_dist_al_campus_m": sorted(round(g.distance(campus)) for g in lodo if g.distance(campus) < 400),
    "quebrada_toca_franja_o_lodo_cgreg": bool(any(g.intersects(ln_full) for g in lodo) or any(g.intersects(ln_full) for g, _ in franja_cgreg)),
    "aguas_abajo_del_campus": {"recorrido_hasta_el_mar_m": round(ln_abajo.length) if ln_abajo else 0,
                               "pendiente_media_pct": rnd((dem[abajo[0]] - dem[r_o, c_o]) / max(ln_abajo.length, 1) * 100, 1) if ln_abajo else None,
                               "fraccion_con_cauce_mapeado": rnd(fr_cauce_abajo, 2), "edificios_franja_20m": edif_aguas_abajo,
                               "salida_mar_lonlat": ll(r_o, c_o), "cruces_de_vias": cruces_via, "puentes_osm_igm_a_150m": len(puente_osm),
                               "eventos_sngr_250m": eventos_cerca(ln_abajo) if ln_abajo else []},
    "escorrentia_local_que_entra_al_campus": {"area_km2": round(loc_area, 4), "lonlat": ll(r_in, c_in), "tc_h": t_loc,
                                              "caudales_100mm": [x for x in tabla_caudales(max(loc_area, 0.0009), 1 / 12, 1 / 12) if x["lluvia_24h_mm"] == 100]}}
# --- sensibilidad del trazado al error del DSM: Monte Carlo con ruido espacialmente correlacionado
rng = np.random.default_rng(MC_SEMILLA)
k0 = next(k for k, p_ in enumerate(stem) if AKM[p_] >= 0.05)            # inicio de la parte encauzada (≥ 0,05 km²)
s0 = stem[k0]
rv = int(MC_VENTANA_M / CELDA)
ra_, rb_ = max(r_q - rv, 0), min(r_q + rv, H); ca_, cb_ = max(c_q - rv, 0), min(c_q + rv, W)
sub_q = demq[ra_:rb_, ca_:cb_]; sub_sea = sea[ra_:rb_, ca_:cb_]; sub_cm = ndimage.binary_dilation(cm, iterations=1)[ra_:rb_, ca_:cb_]
mc = {}
with tempfile.TemporaryDirectory() as td:
    pth_ = pathlib.Path(td) / "mc.tif"
    for sd, corr in MC_ESCENARIOS:
        cruza, sal_, ent_ = 0, collections.Counter(), collections.Counter()
        for it in range(MC_N):
            ruido = rng.normal(0, 1, sub_q.shape)
            if corr > 0:
                ruido = ndimage.gaussian_filter(ruido, corr); ruido /= ruido.std()
            z_ = np.where(sub_sea, -9999, sub_q + sd * ruido).astype("float32")
            prof_ = dict(driver="GTiff", height=z_.shape[0], width=z_.shape[1], count=1, dtype="float32", crs=f"EPSG:{EPSG_UTM}",
                         transform=TR * rasterio.Affine.translation(ca_, ra_), nodata=-9999)
            with rasterio.open(pth_, "w", **prof_) as d: d.write(z_, 1)
            g_ = Grid.from_raster(str(pth_)); d_ = g_.read_raster(str(pth_))
            Fm = np.asarray(g_.flowdir(g_.resolve_flats(g_.fill_depressions(g_.fill_pits(d_))), dirmap=DIRMAP))
            r_, c_ = s0[0] - ra_, s0[1] - ca_; toca = False
            for _ in range(5000):
                if sub_cm[r_, c_] and not toca:
                    toca = True; ent_[tuple(ll(r_ + ra_, c_ + ca_))] += 1
                k_ = Fm[r_, c_]
                if k_ not in OFF: break
                a_, b_ = OFF[k_]; r2, c2 = r_ + a_, c_ + b_
                if not (0 <= r2 < z_.shape[0] and 0 <= c2 < z_.shape[1]) or sub_sea[r2, c2]: break
                r_, c_ = r2, c2
            cruza += toca
            sal_[tuple(ll(r_ + ra_, c_ + ca_))] += 1
        mc[f"sd{sd}m_corr{int(corr * CELDA)}m"] = {"corridas": MC_N, "fraccion_que_cruza_el_campus": round(cruza / MC_N, 3),
                                                   "desembocaduras_mas_frecuentes": [[list(k_), v_] for k_, v_ in sal_.most_common(4)],
                                                   "entradas_al_campus_mas_frecuentes": [[list(k_), v_] for k_, v_ in ent_.most_common(3)]}
        print("   MC", sd, corr, mc[f"sd{sd}m_corr{int(corr * CELDA)}m"])
R["usfq"]["quebrada"]["monte_carlo_trazado"] = {
    "metodo": (f"{MC_N} realizaciones por escenario: DSM quemado + ruido gaussiano (desv. típica sd, suavizado con filtro gaussiano de "
               f"radio «corr» y reescalado), D8 recalculado en una ventana de ±{MC_VENTANA_M} m; se sigue el flujo desde el inicio de "
               "la parte encauzada (≥ 0,05 km²) y se anota si pasa por el campus aproximado (+1 celda) y dónde llega al mar."),
    "inicio_lonlat": ll(*s0), "resultados": mc}

# --- sensibilidad a la rejilla: D8 en la rejilla geográfica nativa del DSM (1″, sin reproyectar), como en el análisis urbano
g_n = Grid.from_raster(str(DEM_QUEMADO)); d_n = g_n.read_raster(str(DEM_QUEMADO))
Fn_r = g_n.flowdir(g_n.resolve_flats(g_n.fill_depressions(g_n.fill_pits(d_n))), dirmap=DIRMAP)
Fn = np.asarray(Fn_r); An = np.asarray(g_n.accumulation(Fn_r, dirmap=DIRMAP))
with rasterio.open(DEM_QUEMADO) as src_n: trn = src_n.transform; zn_ = src_n.read(1)
campus_ll = stransform(TI, campus)
cmn = rasterize([(campus_ll, 1)], out_shape=zn_.shape, transform=trn, all_touched=True).astype(bool)
cn_, rn_ = ~trn * lonlat(*s0); rn_, cn_ = int(rn_), int(cn_)
w_ = An[rn_ - 1:rn_ + 2, cn_ - 1:cn_ + 2]; a_, b_ = np.unravel_index(np.argmax(w_), w_.shape); rn_, cn_ = rn_ - 1 + a_, cn_ - 1 + b_
pn, toca_n = [], False
for _ in range(5000):
    pn.append(trn * (cn_ + .5, rn_ + .5)); toca_n |= bool(cmn[rn_, cn_])
    k_ = Fn[rn_, cn_]
    if k_ not in OFF: break
    a_, b_ = OFF[k_]; rn_, cn_ = rn_ + a_, cn_ + b_
    if not (0 <= rn_ < zn_.shape[0] and 0 <= cn_ < zn_.shape[1]) or zn_[rn_, cn_] <= 0.5: break
ln_n = stransform(T, LineString(pn))
R["usfq"]["quebrada"]["sensibilidad_rejilla_nativa"] = {
    "metodo": "Mismo DSM quemado y mismo algoritmo D8 (pysheds), pero en la rejilla geográfica original de 1″ (≈31 m) en vez de UTM 16S a 30 m.",
    "cruza_el_campus": toca_n, "dist_min_al_campus_m": round(ln_n.distance(campus)), "salida_mar_lonlat": [round(v, 5) for v in pn[-1]],
    "longitud_desde_inicio_m": round(ln_n.length)}
print("   rejilla nativa:", R["usfq"]["quebrada"]["sensibilidad_rejilla_nativa"])

perfil = []
for k, ((r, c), d_) in enumerate(zip(full, dl)):
    if sea[r, c]: continue
    x, y = TR * (c + .5, r + .5); pt_ = Point(x, y)
    perfil.append([round(float(d_)), *[round(v, 6) for v in lonlat(r, c)], round(float(dem[r, c]), 2), round(float(demq[r, c]), 2),
                   round(float(AKM[r, c]), 4), "" if np.isnan(pend[r, c]) else round(float(pend[r, c]), 1),
                   "aguas arriba" if k < ctrl_k else ("control 1 (más cercano al campus)" if k == ctrl_k else ("control 2 (desembocadura)" if (r, c) == (r_o, c_o) else "aguas abajo")),
                   round(pt_.distance(campus)), len(t_edif.query(pt_.buffer(FRANJA_M), predicate="intersects")),
                   round(cauce_mapeado.distance(pt_)), round(float(prof_dep[r, c]), 2)])
guardar_csv("perfil_quebrada_usfq.csv", ["distancia_m", "lon", "lat", "cota_dsm_m", "cota_dsm_quemado_m", "area_acumulada_km2", "pendiente_local_pct",
                                         "tramo", "dist_campus_m", "edificios_20m", "dist_cauce_mapeado_m", "lamina_depresion_m"], perfil)
uf = []
for nm, (upm, st_) in cuencas_q.items():
    uf.append({"type": "Feature", "properties": {"elemento": f"cuenca hasta el punto de control {nm}", **{k_: qinfo[nm][k_] for k_ in ("area_km2", "pendiente_media_cuenca_pct", "tc_rango_h")}},
               "geometry": r6(poligono(upm))})
    uf.append({"type": "Feature", "properties": {"elemento": f"punto de control {nm}", "area_km2": qinfo[nm]["area_km2"]}, "geometry": r6(Point(TR * (ctrl[nm][1] + .5, ctrl[nm][0] + .5)))})
uf.append({"type": "Feature", "properties": {"elemento": "cauce D8 (cabecera → punto más cercano al campus → mar)", "longitud_m": round(ln_full.length)}, "geometry": r6(ln_full)})
uf.append({"type": "Feature", "properties": {"elemento": "recorrido D8 en la rejilla geográfica nativa (sensibilidad)",
                                             "cruza_el_campus": toca_n}, "geometry": r6(ln_n)})
uf.append({"type": "Feature", "properties": {"elemento": "campus aproximado", "area_ha": round(campus.area / 1e4, 2)}, "geometry": r6(campus)})
for x in contexto:
    if x["salida_mar_lonlat"] == q_sel["salida_mar_lonlat"]: continue
    rr_, cc_ = x["_rc"]; pth = cauce(rr_, cc_) + aguas_abajo(rr_, cc_)[1:]
    if len(pth) > 1:
        uf.append({"type": "Feature", "properties": {"elemento": "otro recorrido D8 a ≤ 400 m del campus", **{k_: v_ for k_, v_ in x.items() if not k_.startswith("_")}},
                   "geometry": r6(LineString([TR * (b + .5, a + .5) for a, b in pth]))})
guardar_json("quebrada_usfq.geojson", fc(uf))
# transecto recto del punto de control 1 al Galapagos Science Center: ¿hay una divisoria entre la quebrada y el campus?
gsc = next((g for g, p in edif_univ if p.get("nombre") == "Galapagos Science Center"), campus)
x0_, y0_ = TR * (c_q + .5, r_q + .5); x1_, y1_ = gsc.centroid.coords[0]
Lt = math.hypot(x1_ - x0_, y1_ - y0_); ss = np.arange(0, Lt + 1, 15)
zt = np.array([zbil(x0_ + (x1_ - x0_) * s_ / Lt, y0_ + (y1_ - y0_) * s_ / Lt) for s_ in ss])
R["usfq"]["quebrada"]["transecto_control1_a_gsc"] = {
    "longitud_m": round(Lt), "cota_inicio_m": rnd(zt[0], 1), "cota_fin_m": rnd(zt[-1], 1), "pendiente_media_pct": rnd((zt[0] - zt[-1]) / Lt * 100, 1),
    "barrera_max_sobre_inicio_m": rnd(max(0.0, float(zt[1:].max() - zt[0])), 1), "cotas_cada_15m": [round(float(v), 1) for v in zt],
    "pendiente_d8_en_el_tramo_de_control_pct": rnd(np.mean([pend[p_] for p_ in full[max(0, ctrl_k - 2):ctrl_k + 3]]), 1),
    "nota": "Si el terreno baja del cauce al campus sin barrera, solo la elección D8 (ruido de ±2 m) separa la quebrada del campus."}


def calado_calle(Q, S, b=CALLE_ANCHO_M, n=CALLE_N):
    """Calado y velocidad de Manning en una sección rectangular de ancho b (ilustrativo: calle sin bordillos ni sumideros)."""
    for h_ in np.arange(0.01, 3, 0.01):
        A_ = b * h_; R_ = A_ / (b + 2 * h_)
        if A_ * R_ ** (2 / 3) * S ** 0.5 / n >= Q: return round(float(h_), 2), round(float(Q / A_), 1)
    return None, None


S_ab = max(R["usfq"]["quebrada"]["aguas_abajo_del_campus"]["pendiente_media_pct"] or 1, 0.5) / 100
R["usfq"]["quebrada"]["calado_ilustrativo_en_calle"] = {
    "supuesto": f"Calle rectangular de {CALLE_ANCHO_M} m, n = {CALLE_N}, pendiente {S_ab * 100:.1f} % (tramo D8 aguas abajo del campus); "
                "sin red pluvial ni obstrucciones. Solo para dar escala.",
    "casos": {f"Q {q_} m³/s": dict(zip(("calado_m", "velocidad_ms"), calado_calle(q_, S_ab))) for q_ in (1, 2, 4, 8, 14, 25)}}
area_q = qinfo["2_desembocadura"]["area_km2"]
tc_t = max(qinfo["2_desembocadura"]["cauce"]["temez_h"], 1 / 60); tc_k = max(qinfo["2_desembocadura"]["cauce"]["kirpich_h"], 1 / 60)
print("USFQ:", json.dumps({k_: v_ for k_, v_ in R["usfq"]["quebrada"].items() if k_ != "puntos_de_control"}, ensure_ascii=False, default=str))
for nm, v in qinfo.items(): print("  ", nm, {k_: v_ for k_, v_ in v.items() if k_ != "caudales_tormenta_tipo_II"})
print("   contexto:", R["usfq"]["recorridos_d8_a_menos_de_400m"])
print("   campus:", R["usfq"]["campus_aproximado"])

# --- lluvia modelada del meteorólogo (si existe): hietograma horario en el punto usfq_gsc
fh = LLUVIAS_DIR / "modelos_horaria.csv"
if fh.exists():
    import datetime as _dt
    serie = collections.defaultdict(list)
    for f in csv.DictReader(open(fh, encoding="utf-8")):
        if f.get("punto") == "usfq_gsc":
            serie[f["modelo"]].append((f["fecha_hora_local_fin"], float(f["mm"] or 0)))
    ev = {}
    for mod, v in serie.items():
        v.sort(); mm = np.array([a for _, a in v])
        if len(mm) < 24: continue
        s24 = np.convolve(mm, np.ones(24), "valid"); k = int(np.argmax(s24))
        Pc_h = np.concatenate([[0], np.cumsum(mm[k:k + 24])])
        fun = lambda t_, Pc_h=Pc_h: np.interp(t_, np.arange(len(Pc_h)), Pc_h)
        row = {"inicio_ventana_24h": v[k][0], "max_24h_mm": round(float(s24[k]), 1), "max_1h_mm": round(float(mm.max()), 1),
               "total_serie_mm": round(float(mm.sum()), 1), "serie": f"{v[0][0]} a {v[-1][0]}"}
        for cn in CN_ESCENARIOS:
            q1, Qmm, _ = hidrograma(area_q, cn, tc_t, Pc_fun=fun); q2, _, _ = hidrograma(area_q, cn, tc_k, Pc_fun=fun)
            row[f"CN{cn}"] = {"escorrentia_mm": round(Qmm, 1), "q_pico_m3s_temez": round(float(q1.max()), 2), "q_pico_m3s_kirpich": round(float(q2.max()), 2)}
        ev[mod] = row
    R["usfq"]["lluvia_modelada_meteorologo"] = {"fuente": str(fh.relative_to(ROOT)), "nota": "Lluvia de MODELO (Open-Meteo), no medida. "
                                                "Ventana de 24 h de máxima lluvia en la celda del punto usfq_gsc; caudal en la desembocadura de la quebrada.",
                                                "area_km2": area_q, "por_modelo": ev}
    print("   lluvia modelada:", {k_: (v_["max_24h_mm"], v_["CN70"]["q_pico_m3s_temez"]) for k_, v_ in ev.items()})

# ---------------------------------------------------------------- 8. contraste del DSM con los puntos acotados IGM
pbm_c = ZONAS["Puerto Baquerizo Moreno"].centroid
grupos_pa = {"isla": [], "pbm_5km": [], "pbm_zona": [], "progreso_2km": [], "fuera_zonas_5km": []}
for g, p in pa:
    if not p.get("z"): continue
    zz = zbil(*g.coords[0])
    if np.isnan(zz) or zz <= 0.5: continue
    d_ = zz - p["z"]
    grupos_pa["isla"].append(d_)
    if g.distance(pbm_c) <= 5000:
        grupos_pa["pbm_5km"].append(d_)
        (grupos_pa["pbm_zona"] if ZONAS["Puerto Baquerizo Moreno"].contains(g) else grupos_pa["fuera_zonas_5km"]).append(d_)
    if g.distance(prog_pt) <= 2000: grupos_pa["progreso_2km"].append(d_)


def est(v):
    v = np.array(v)
    return {"n": int(v.size), "media_m": round(float(v.mean()), 2), "mediana_m": round(float(np.median(v)), 2), "desv_tipica_m": round(float(v.std()), 2),
            "rmse_m": round(float(np.sqrt((v ** 2).mean())), 2), "p05_m": round(float(np.percentile(v, 5)), 2),
            "p95_m": round(float(np.percentile(v, 95)), 2)} if v.size else None


R["validacion_dsm"] = {"nota": "DSM (bilineal) − punto acotado IGM 1:25 000 (z entero). El punto IGM tiene su propio error.",
                       **{k: est(v) for k, v in grupos_pa.items()}}
print("Validación DSM:", R["validacion_dsm"])

guardar_json("resumen.json", R)
print("Listo:", OUT)
