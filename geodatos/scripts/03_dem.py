"""Procesa el relieve de cada isla: recorte, relieve sombreado, curvas de nivel, red de drenaje derivada (quebradas),
cuencas, HAND (susceptibilidad a inundación), zonas costeras bajas y pendientes.

Relieve:
  - San Cristóbal e Isabela: Copernicus GLO-30 (DSM, 30 m).
  - Santa Cruz: relieve FUSIONADO (relieve_sgiar.py): DTM de 1 m de la SGIAR en Puerto Ayora, el escarpe y Bellavista y
    Copernicus fuera, con una transición de 300 m. Además, dentro de la cobertura del DTM se repiten HAND, drenaje,
    costa baja y curvas en una malla de 5 m («alta resolución») y se empalman con las capas de 30 m: dentro de la
    cobertura (menos la franja de transición) mandan las de 5 m; fuera, las de 30 m. Cada entidad dice su relieve.
Uso: .venv/bin/python -I scripts/03_dem.py
"""
import json, glob, pathlib, math
import numpy as np, rasterio
from scipy.ndimage import median_filter, distance_transform_edt
from rasterio.merge import merge
from rasterio import features
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from shapely.geometry import shape, mapping, LineString
from shapely.ops import unary_union
import contourpy
import matplotlib
from matplotlib import colors
from PIL import Image
from pysheds.grid import Grid
from pysheds.sview import Raster
import importlib.util

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("relieve_sgiar", ROOT / "scripts/relieve_sgiar.py")
relieve_sgiar = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(relieve_sgiar)
DEM = sorted(glob.glob(str(ROOT / "descargas/dem/*.tif")))
OUT = ROOT / "capas" / "dem"; OUT.mkdir(parents=True, exist_ok=True)
RAS = ROOT / "capas" / "raster"; RAS.mkdir(parents=True, exist_ok=True)
TMP = ROOT / "descargas" / "dem_recortes"; TMP.mkdir(parents=True, exist_ok=True)

REGIONES = {  # oeste, sur, este, norte
    "santa_cruz":    ("Santa Cruz",    (-90.56, -0.80, -90.15, -0.42)),
    "san_cristobal": ("San Cristóbal", (-89.66, -0.97, -89.22, -0.66)),
    "isabela_sur":   ("Isabela",       (-91.25, -1.08, -90.85, -0.70)),
}
CELDA_M = 30.87              # celda de 1 arcosegundo en el ecuador ≈ 30.9 m
UMBRAL_KM2 = 0.10            # área drenada mínima para dibujar un cauce
# Alta resolución sobre el DTM SGIAR (solo Santa Cruz): malla de 1/6 de arcosegundo (≈ 5,1 m) en EPSG:4326
ALTA_RES_GRADOS = 1 / 3600 / 6
ALTA_MARGEN_GRADOS = 0.02    # ≈ 2,2 km alrededor de la cobertura, para que el área drenada que entra por los bordes cuente
FUENTE_COP = "Copernicus GLO-30"
FUENTE_FUSION = "Copernicus GLO-30 + DTM 1 m SGIAR (30 m)"
FUENTE_ALTA = "DTM 1 m SGIAR (malla de 5 m)"

def fc(feats): return {"type": "FeatureCollection", "features": feats}
def save(name, feats):
    (OUT / name).write_text(json.dumps(fc(feats), ensure_ascii=False, separators=(",", ":")))
    print(f"   {name}: {len(feats)}")

def png(arr_rgba, name):
    Image.fromarray(arr_rgba, "RGBA").save(RAS / name, optimize=True)

def hillshade(z, dx, dy, az=315, alt=45):
    gy, gx = np.gradient(z, dy, dx)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    a, b = math.radians(alt), math.radians(az)
    return np.sin(a) * np.cos(slope) + np.cos(a) * np.sin(slope) * np.cos(b - aspect), np.degrees(slope)


def curvas(z, sea, tr, isla, simp=0.00008, fuente=None):
    H, W = z.shape
    xs = tr.c + tr.a * (np.arange(W) + 0.5); ys = tr.f + tr.e * (np.arange(H) + 0.5)
    cg = contourpy.contour_generator(xs, ys, np.where(sea, -1, z).astype("float64"), line_type="Separate")
    feats = []
    extra = {"relieve": fuente} if fuente else {}
    zmax = float(z[~sea].max())
    for lv in range(20, int(zmax) + 1, 20):
        for seg in cg.lines(lv):
            if len(seg) < 4: continue
            ls = LineString(seg).simplify(simp)
            feats.append({"type": "Feature", "geometry": mapping(ls),
                          "properties": {"isla": isla, "elev_m": lv, "maestra": lv % 100 == 0, **extra}})
    for seg in cg.lines(1.0):   # línea de costa aproximada del DEM
        if len(seg) >= 4:
            feats.append({"type": "Feature", "geometry": mapping(LineString(seg).simplify(simp)),
                          "properties": {"isla": isla, "elev_m": 0, "maestra": True, **extra}})
    return feats


def costa_baja(z, sea, tr, isla, simp=0.00008, fuente=None):
    land = ~sea
    feats = []
    extra = {"relieve": fuente} if fuente else {}
    for lim, lab in [(3, "0–3 m"), (5, "3–5 m"), (10, "5–10 m")]:
        lo = {3: 0, 5: 3, 10: 5}[lim]
        m = median_filter((land & (z > lo) & (z <= lim)).astype(np.uint8), size=3).astype(bool)
        u = unary_union([shape(g_) for g_, _ in features.shapes(m.astype(np.uint8), mask=m, transform=tr)])
        for geom in [p_.simplify(simp, preserve_topology=True) for p_ in getattr(u, "geoms", [u]) if p_.area * 1.19e10 >= 3000]:
            feats.append({"type": "Feature", "geometry": mapping(geom),
                          "properties": {"isla": isla, "clase": lab, "max_m": lim, **extra}})
    return feats


def hidrologia(z, sea, tr, prof, isla, key, sufijo, celda_m, fuente, simp_dren=0.00005, simp_hand=0.00007, cuencas=True):
    """Quemado, D8, drenaje, cuencas y HAND. Devuelve (drenaje, cuencas, susc, clsH)."""
    H, W = z.shape
    land = ~sea
    cell_km2 = (celda_m / 1000) ** 2
    # Quemado de cauces: baja 3 m el DEM sobre las quebradas IGM 1:25 000 para que el flujo las siga
    rios = [shape(ft["geometry"]) for ft in json.loads((ROOT/"capas/igm/rio.geojson").read_text())["features"]
            if ft["properties"]["isla"] == isla]
    igm_rio = features.rasterize([(g, 1) for g in rios], out_shape=(H, W), transform=tr, all_touched=True).astype(bool) if rios else np.zeros((H, W), bool)
    zb = z.copy(); zb[igm_rio & land] -= 3.0
    f = TMP / f"{key}{sufijo}_dem.tif"
    fb = TMP / f"{key}{sufijo}_dem_quemado.tif"
    with rasterio.open(fb, "w", **prof) as d: d.write(zb, 1)
    grid = Grid.from_raster(str(fb)); dem = grid.read_raster(str(fb))
    pit = grid.fill_pits(dem); fl = grid.fill_depressions(pit); inf = grid.resolve_flats(fl)
    fdir = grid.flowdir(inf)
    acc = grid.accumulation(fdir)
    thr = UMBRAL_KM2 / cell_km2
    streams = Raster((np.asarray(acc) > thr) & land, viewfinder=fdir.viewfinder)
    order = grid.stream_order(fdir, streams)
    net = grid.extract_river_network(fdir, streams)
    A = np.asarray(acc); O = np.asarray(order)
    inv = ~tr
    dren = []
    origen = "Derivado de Copernicus GLO-30 (umbral 0,1 km²)" if fuente == FUENTE_COP else f"Derivado de {fuente} (umbral 0,1 km²)"
    for ft in net["features"]:
        coords = ft["geometry"]["coordinates"]
        if len(coords) < 2: continue
        idx = [tuple(int(v) for v in inv * (x, y)) for x, y in coords]
        aa = [A[min(r, H-1), min(c, W-1)] for c, r in idx]; oo = [O[min(r, H-1), min(c, W-1)] for c, r in idx]
        km2 = float(max(aa)) * cell_km2
        ls = LineString(coords).simplify(simp_dren)
        dren.append({"type": "Feature", "geometry": mapping(ls),
                     "properties": {"isla": isla, "area_drenada_km2": round(km2, 2), "orden": int(max(oo)), "fuente": origen}})

    # Cuencas: desembocaduras al mar de cauces con ≥ 1 km² drenados
    cu = []
    if cuencas:
        fd = np.asarray(fdir)
        dirmap = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
        outlets = []
        rr, cc = np.where((A * cell_km2 >= 1.0) & land)
        for r, c in zip(rr, cc):
            d = dirmap.get(int(fd[r, c]))
            if not d:      # celda terminal (borde con el mar)
                outlets.append((r, c, A[r, c] * cell_km2)); continue
            r2, c2 = r + d[0], c + d[1]
            if r2 < 0 or c2 < 0 or r2 >= H or c2 >= W or sea[r2, c2]:
                outlets.append((r, c, A[r, c] * cell_km2))
        meta = {}
        lab = np.zeros((H, W), np.int32)
        for i, (r, c, km2) in enumerate(sorted(outlets, key=lambda t: -t[2])[:60], 1):
            x, y = tr * (c + 0.5, r + 0.5)
            cat = np.asarray(grid.catchment(x=x, y=y, fdir=fdir, xytype="coordinate"))
            lab[(cat > 0) & (lab == 0)] = i
            meta[i] = {"x": x, "y": y, "km2": km2}
        bag = {}
        for geom, val in features.shapes(lab, mask=lab > 0, transform=tr): bag.setdefault(int(val), []).append(shape(geom))
        for val, gs in bag.items():
            m = meta[val]
            props = {"isla": isla, "cuenca_id": f"{key}-{val}", "area_km2": round(m["km2"], 2),
                     "desembocadura": [round(m["x"], 5), round(m["y"], 5)]}
            if fuente != FUENTE_COP: props["relieve"] = fuente
            cu.append({"type": "Feature", "geometry": mapping(unary_union(gs).simplify(0.0002, preserve_topology=True)),
                       "properties": props})

    # HAND: altura sobre el drenaje más cercano → susceptibilidad a inundación fluvial/de quebrada
    major = ((A > (0.5 / cell_km2)) | (igm_rio & (A > (0.05 / cell_km2)))) & land
    dem0 = grid.read_raster(str(f))      # HAND sobre el DEM sin quemar
    hand = np.asarray(grid.compute_hand(fdir, dem0, Raster(major, viewfinder=fdir.viewfinder), nodata_out=np.nan))
    clsH = np.zeros((H, W), np.uint8)
    clsH[(hand <= 5) & land] = 1; clsH[(hand <= 2.5) & land] = 2; clsH[(hand <= 1) & land] = 3
    # restringe a 300 m del cauce (evita mesetas planas lejanas)
    dist = distance_transform_edt(~major) * celda_m
    clsH[dist > 300] = 0
    clsH = median_filter(clsH, size=3)
    susc = []
    names = {1: "Baja (HAND 2,5–5 m)", 2: "Media (HAND 1–2,5 m)", 3: "Alta (HAND ≤ 1 m)"}
    polys = {1: [], 2: [], 3: []}
    for geom, val in features.shapes(clsH, mask=clsH > 0, transform=tr): polys[int(val)].append(shape(geom))
    for lv, lst in polys.items():
        u = unary_union(lst)
        for part in getattr(u, "geoms", [u]):
            if part.area * 1.19e10 < 2500: continue
            susc.append({"type": "Feature", "geometry": mapping(part.simplify(simp_hand, preserve_topology=True)),
                         "properties": {"isla": isla, "nivel": lv, "susceptibilidad": names[lv],
                                        "metodo": f"HAND sobre {fuente}; cauces IGM 1:25k + drenaje ≥ 0,5 km²; ≤ 300 m del cauce"}})
    return dren, cu, susc, clsH


def _mismo_tipo(r, g):
    """Deja solo las partes del mismo tipo que g (líneas o polígonos); None si no queda nada."""
    dim = 2 if g.geom_type.endswith("Polygon") else 1
    partes = [p for p in getattr(r, "geoms", [r]) if (p.area if dim == 2 else p.length) > 0]
    if not partes: return None
    return unary_union(partes) if len(partes) > 1 else partes[0]


def empalmar(gruesas, finas, nucleo):
    """Capas de 30 m fuera del núcleo + capas de 5 m dentro. Conserva las propiedades de cada entidad."""
    out = []
    for ft in gruesas:
        g = shape(ft["geometry"])
        if not g.intersects(nucleo): out.append(ft); continue
        r = _mismo_tipo(g.difference(nucleo), g)
        if r is not None: out.append({**ft, "geometry": mapping(r)})
    for ft in finas:
        g = shape(ft["geometry"])
        if not g.intersects(nucleo): continue
        r = g if nucleo.contains(g) else _mismo_tipo(g.intersection(nucleo), g)
        if r is not None: out.append({**ft, "geometry": mapping(r)})
    return out


def alta_resolucion(key, isla, z30, tr30):
    """HAND, drenaje, costa baja y curvas en ≈ 5 m sobre la cobertura del DTM SGIAR (más un margen con Copernicus)."""
    cub = relieve_sgiar.cobertura("EPSG:4326")
    w, s, e, n = cub.bounds
    w, s, e, n = w - ALTA_MARGEN_GRADOS, s - ALTA_MARGEN_GRADOS, e + ALTA_MARGEN_GRADOS, n + ALTA_MARGEN_GRADOS
    r = ALTA_RES_GRADOS
    W = int(math.ceil((e - w) / r)); H = int(math.ceil((n - s) / r))
    tr = from_origin(w, n, r, r)
    zc = np.full((H, W), np.nan, "float32")    # Copernicus (ya con el mar en −9999) remuestreado a 5 m
    reproject(z30, zc, src_transform=tr30, src_crs="EPSG:4326", dst_transform=tr, dst_crs="EPSG:4326",
              src_nodata=-9999, dst_nodata=np.nan, resampling=Resampling.bilinear)
    zc = np.where(np.isfinite(zc), zc, -9999).astype("float32")
    z, peso, _ = relieve_sgiar.fusionar(zc, tr, "EPSG:4326")
    sea = z <= 0.5
    z[sea] = -9999
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs="EPSG:4326", transform=tr,
                nodata=-9999, compress="deflate", predictor=3, tiled=True)
    with rasterio.open(TMP / f"{key}_dtm5_dem.tif", "w", **prof) as d: d.write(z, 1)
    print(f"   malla de 5 m: {W}×{H}")
    celda = r * 111320
    dren, _, susc, clsH = hidrologia(z, sea, tr, prof, isla, key, "_dtm5", celda, FUENTE_ALTA,
                                     simp_dren=0.00002, simp_hand=0.00002, cuencas=False)
    cb = costa_baja(z, sea, tr, isla, simp=0.00002, fuente=FUENTE_ALTA)
    cv = curvas(z, sea, tr, isla, simp=0.00002, fuente=FUENTE_ALTA)
    return {"drenaje": dren, "susc": susc, "costa": cb, "curvas": cv}


bounds_meta = {}
for key, (isla, (w, s, e, n)) in REGIONES.items():
    print("==", isla, key)
    srcs = [rasterio.open(f) for f in DEM]
    z, tr = merge(srcs, bounds=(w, s, e, n), nodata=-9999)
    z = z[0].astype("float32"); [x.close() for x in srcs]
    sea = z <= 0.5
    z[sea] = -9999
    fusion = key == "santa_cruz" and relieve_sgiar.disponible()
    fuente = FUENTE_COP
    if fusion:
        z_cop = z.copy()
        z, _, _ = relieve_sgiar.fusionar(z, tr, "EPSG:4326")
        sea = z <= 0.5
        z[sea] = -9999
        fuente = FUENTE_FUSION
        print("   relieve fusionado con el DTM SGIAR")
    prof = dict(driver="GTiff", height=z.shape[0], width=z.shape[1], count=1, dtype="float32",
                crs="EPSG:4326", transform=tr, nodata=-9999, compress="deflate")
    f = TMP / f"{key}_dem.tif"
    with rasterio.open(f, "w", **prof) as d: d.write(z, 1)
    H, W = z.shape
    dx = CELDA_M * math.cos(math.radians((s + n) / 2)); dy = CELDA_M
    bounds_meta[key] = {"isla": isla, "bounds": [[tr.f + tr.e * H, tr.c], [tr.f, tr.c + tr.a * W]]}

    # --- Relieve sombreado + tinte hipsométrico (PNG para el visor) ---
    zf = np.where(sea, 0, z)
    hs, slope = hillshade(zf, dx, dy)
    g = np.clip(hs, 0, 1)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., 0:3] = (g * 255).astype(np.uint8)[..., None]
    rgba[..., 3] = np.where(sea, 0, (np.clip(1 - g, 0, 1) * 200 + 25)).astype(np.uint8)
    png(rgba, f"{key}_relieve.png")
    norm = colors.Normalize(0, float(np.nanmax(zf)))
    tint = (matplotlib.colormaps["terrain"](norm(zf) * 0.75 + 0.22) * 255).astype(np.uint8)
    tint[..., 3] = np.where(sea, 0, 255)
    png(tint, f"{key}_elevacion.png")

    # --- Pendientes (posible inestabilidad de laderas) ---
    cls = np.zeros_like(z, np.uint8)
    cls[(slope >= 15) & ~sea] = 1; cls[(slope >= 25) & ~sea] = 2; cls[(slope >= 35) & ~sea] = 3
    pal = {1: (250, 204, 21, 110), 2: (249, 115, 22, 150), 3: (185, 28, 28, 180)}
    sp = np.zeros((H, W, 4), np.uint8)
    for k, c in pal.items(): sp[cls == k] = c
    png(sp, f"{key}_pendientes.png")

    # --- Curvas, costa baja, hidrología (30 m) ---
    extra = fuente if fusion else None
    cv = curvas(z, sea, tr, isla, fuente=extra)
    cb = costa_baja(z, sea, tr, isla, fuente=extra)
    dren, cu, susc, clsH = hidrologia(z, sea, tr, prof, isla, key, "", CELDA_M, fuente)

    hp = np.zeros((H, W, 4), np.uint8)
    for k_, c_ in {1: (147, 197, 253, 120), 2: (59, 130, 246, 165), 3: (30, 58, 138, 210)}.items(): hp[clsH == k_] = c_
    png(hp, f"{key}_susc_inundacion.png")

    # --- Alta resolución dentro de la cobertura del DTM SGIAR ---
    if fusion:
        alta = alta_resolucion(key, isla, z_cop, tr)
        nucleo = relieve_sgiar.cobertura("EPSG:4326", recorte_m=relieve_sgiar.TRANSICION_M)
        cv = empalmar(cv, alta["curvas"], nucleo)
        cb = empalmar(cb, alta["costa"], nucleo)
        dren = empalmar(dren, alta["drenaje"], nucleo)
        susc = empalmar(susc, alta["susc"], nucleo)
    save(f"{key}_curvas.geojson", cv)
    save(f"{key}_costa_baja.geojson", cb)
    save(f"{key}_drenaje_derivado.geojson", dren)
    save(f"{key}_cuencas.geojson", cu)
    save(f"{key}_susc_inundacion.geojson", susc)

(RAS / "limites.json").write_text(json.dumps(bounds_meta, ensure_ascii=False, indent=1))
print("ok")
