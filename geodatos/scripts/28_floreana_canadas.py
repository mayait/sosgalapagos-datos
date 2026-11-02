"""Floreana (Puerto Velasco Ibarra): cauces D8 que llegan a la costa del poblado y coherencia topográfica de una conexión de
≈500 m entre cañadas para proteger Playa Negra (Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal). EXPLORATORIO.

  - DSM Copernicus GLO-30 (tile S02 W091), reproyectado a UTM 15S, 30 m; D8 (pysheds) con depresiones rellenadas.
  - No hay cartografía IGM ni OSM de las cañadas «La Hormiga» y «La Varonesa / Lobería»: los nombres NO se asignan aquí.
  - Para el cauce que desemboca en Playa Negra (OSM) se buscan, en cada celda de su red (≥ 0,05 km²), conexiones rectas de
    ≤ LONG_MAX_M hasta las redes vecinas (norte y sur): desnivel, pendiente y corte máximo bajo una rasante recta.

Uso:  .venv/bin/python -I scripts/28_floreana_canadas.py     (desde geodatos/)
Salidas: estudios/san-cristobal/datos/floreana/cauces_floreana.geojson y floreana.json
"""
import json, pathlib, tempfile
import numpy as np, rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy import ndimage
from shapely.geometry import LineString, Point, mapping
from shapely.ops import transform as stransform
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
TILE = ROOT / "descargas/dem/Copernicus_DSM_COG_10_S02_00_W091_00_DEM.tif"
OUT = ROOT / "estudios/san-cristobal/datos/floreana"
EPSG = 32715; CELDA = 30.0
BBOX = (-90.56, -1.36, -90.36, -1.20)
PLAYA_NEGRA = (-90.48847, -1.27649)          # OSM relation 2045693
POBLADO = (-90.48654, -1.27511)              # OSM node 249596983
LONG_MAX_M = 550
A_RED_KM2 = 0.05
PEND_MIN = 0.5; CORTE_MAX_M = 3.0
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)
T = Transformer.from_crs(4326, EPSG, always_xy=True).transform
TI = Transformer.from_crs(EPSG, 4326, always_xy=True).transform

src = rasterio.open(TILE)
w = from_bounds(*BBOX, src.transform)
a = src.read(1, window=w); trw = src.window_transform(w)
TR, W, H = calculate_default_transform(src.crs, f"EPSG:{EPSG}", a.shape[1], a.shape[0], *BBOX, resolution=CELDA)
z = np.full((H, W), -9999, "float32")
reproject(a, z, src_transform=trw, src_crs=src.crs, dst_transform=TR, dst_crs=f"EPSG:{EPSG}", resampling=Resampling.bilinear,
          src_nodata=-32767, dst_nodata=-9999)
sea = (z <= 0.5) | (z == -9999)
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td) / "f.tif"
    with rasterio.open(p, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=f"EPSG:{EPSG}", transform=TR, nodata=-9999) as d:
        d.write(np.where(sea, -9999, z).astype("float32"), 1)
    g = Grid.from_raster(str(p)); dd = g.read_raster(str(p))
    fd = g.flowdir(g.resolve_flats(g.fill_depressions(g.fill_pits(dd))), dirmap=DIRMAP)
    F = np.asarray(fd); A = np.asarray(g.accumulation(fd, dirmap=DIRMAP)).astype(float) * CELDA ** 2 / 1e6
A[sea] = 0


def ll(r, c):
    return [round(v, 5) for v in TI(*(TR * (c + .5, r + .5)))]


# desembocaduras (A ≥ 0,1 km²) en la costa del poblado
salidas = []
for r, c in zip(*np.where((A >= 0.1) & ~sea)):
    k = F[r, c]
    if k in OFF and sea[r + OFF[k][0], c + OFF[k][1]]:
        lo, la = ll(r, c)
        if -1.292 < la < -1.262 and lo < -90.47: salidas.append((r, c, lo, la, float(A[r, c])))
pn = min(salidas, key=lambda s: Point(T(s[2], s[3])).distance(Point(T(*PLAYA_NEGRA))))
norte = max([s for s in salidas if s[3] > pn[3] + 0.003 and s[3] < pn[3] + 0.009], key=lambda s: s[4])   # la mayor 0,3–1 km al norte
sur = max([s for s in salidas if s[3] < pn[3] - 0.003 and s[3] > pn[3] - 0.009], key=lambda s: s[4])     # la mayor 0,3–1 km al sur


def red(r, c):
    m = np.zeros((H, W), bool); st = [(r, c)]
    while st:
        r, c = st.pop(); m[r, c] = True
        for k, (a_, b_) in OFF.items():
            ur, uc = r - a_, c - b_
            if 0 <= ur < H and 0 <= uc < W and F[ur, uc] == k and not sea[ur, uc] and A[ur, uc] >= A_RED_KM2 and not m[ur, uc]:
                st.append((ur, uc))
    return m


R = {"metodo": __doc__.split("Uso:")[0].strip(), "salidas": {}}
redes = {"Playa Negra": (pn, red(pn[0], pn[1])), "norte": (norte, red(norte[0], norte[1])), "sur": (sur, red(sur[0], sur[1]))}
feats = []
for nm, (s, m) in redes.items():
    R["salidas"][nm] = {"lonlat": [s[2], s[3]], "area_km2": round(s[4], 2), "cota_max_red_m": round(float(z[m].max()), 1),
                        "dist_a_playa_negra_m": round(Point(T(s[2], s[3])).distance(Point(T(*PLAYA_NEGRA))))}
    for r, c in zip(*np.where(m)):
        k = F[r, c]
        if k in OFF:
            r2, c2 = r + OFF[k][0], c + OFF[k][1]
            feats.append({"type": "Feature", "properties": {"cauce": nm, "area_km2": round(float(A[r, c]), 3)},
                          "geometry": mapping(stransform(TI, LineString([TR * (c + .5, r + .5), TR * (c2 + .5, r2 + .5)])))})
mpn = redes["Playa Negra"][1]
ra, ca = np.where(mpn)
for nm in ("norte", "sur"):
    mb = redes[nm][1]; rb, cb = np.where(mb)
    D = np.hypot(ra[:, None] - rb[None, :], ca[:, None] - cb[None, :]) * CELDA
    opciones = []
    for i in range(len(ra)):
        j = int(np.argmin(D[i] + np.where(z[rb, cb] < z[ra[i], ca[i]], 0, 1e6)))      # destino más cercano y más bajo
        dist = D[i, j]
        if dist > LONG_MAX_M or z[rb[j], cb[j]] >= z[ra[i], ca[i]]: continue
        n = max(int(dist / 7.5), 4)
        zz = ndimage.map_coordinates(z, [np.linspace(ra[i], rb[j], n), np.linspace(ca[i], cb[j], n)], order=1)
        ras = np.linspace(z[ra[i], ca[i]], z[rb[j], cb[j]], n)
        opciones.append({"toma_lonlat": ll(ra[i], ca[i]), "destino_lonlat": ll(rb[j], cb[j]), "longitud_m": round(float(dist)),
                         "area_captada_km2": round(float(A[ra[i], ca[i]]), 2), "fraccion_de_la_cuenca_de_playa_negra": round(float(A[ra[i], ca[i]] / pn[4]), 2),
                         "cota_toma_m": round(float(z[ra[i], ca[i]]), 1), "desnivel_m": round(float(z[ra[i], ca[i]] - z[rb[j], cb[j]]), 1),
                         "pendiente_pct": round(float((z[ra[i], ca[i]] - z[rb[j], cb[j]]) / dist * 100), 2), "corte_max_m": round(float(max(0, (zz - ras).max())), 1)})
    viables = [o for o in opciones if o["pendiente_pct"] >= PEND_MIN and o["corte_max_m"] <= CORTE_MAX_M]
    viables.sort(key=lambda o: (-o["area_captada_km2"], o["longitud_m"]))
    opciones.sort(key=lambda o: (-o["area_captada_km2"], o["corte_max_m"]))
    R[f"conexion_hacia_{nm}"] = {"n_opciones_<=550m_que_bajan": len(opciones), "n_viables": len(viables),
                                 "criterio_viable": f"pendiente ≥ {PEND_MIN} % y corte ≤ {CORTE_MAX_M} m bajo una rasante recta",
                                 "mejores_viables_por_area": viables[:3], "mejores_por_area_sin_criterio": opciones[:2],
                                 "area_max_captable_viable_km2": viables[0]["area_captada_km2"] if viables else 0}
    opciones = viables
    for o in opciones[:1]:
        feats.append({"type": "Feature", "properties": {"elemento": f"conexión candidata hacia el cauce {nm}", **o},
                      "geometry": mapping(LineString([o["toma_lonlat"], o["destino_lonlat"]]))})
    print(nm, R["salidas"][nm], R[f"conexion_hacia_{nm}"]["n_viables"], opciones[:2])
print("Playa Negra:", R["salidas"]["Playa Negra"])
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "cauces_floreana.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False))
(OUT / "floreana.json").write_text(json.dumps(R, ensure_ascii=False, indent=1))
