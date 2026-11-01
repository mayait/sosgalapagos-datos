"""Procesa el DEM Copernicus GLO-30 (DSM, 30 m): recorte por isla, relieve sombreado, curvas de nivel,
red de drenaje derivada (quebradas), cuencas, HAND (susceptibilidad a inundación), zonas costeras bajas y pendientes.
Uso: .venv/bin/python -I scripts/03_dem.py
"""
import json, glob, pathlib, math
import numpy as np, rasterio
from scipy.ndimage import median_filter
from rasterio.merge import merge
from rasterio import features
from shapely.geometry import shape, mapping, LineString
from shapely.ops import unary_union
import contourpy
import matplotlib
from matplotlib import colors
from PIL import Image
from pysheds.grid import Grid
from pysheds.sview import Raster

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEM = sorted(glob.glob(str(ROOT / "descargas/dem/*.tif")))
OUT = ROOT / "capas" / "dem"; OUT.mkdir(parents=True, exist_ok=True)
RAS = ROOT / "capas" / "raster"; RAS.mkdir(parents=True, exist_ok=True)
TMP = ROOT / "descargas" / "dem_recortes"; TMP.mkdir(parents=True, exist_ok=True)

REGIONES = {  # oeste, sur, este, norte
    "santa_cruz":    ("Santa Cruz",    (-90.56, -0.80, -90.15, -0.42)),
    "san_cristobal": ("San Cristóbal", (-89.66, -0.97, -89.22, -0.66)),
    "isabela_sur":   ("Isabela",       (-91.25, -1.08, -90.85, -0.70)),
}
CELL_KM2 = (30.87e-3) ** 2   # celda de 1 arcosegundo en el ecuador ≈ 30.9 m
UMBRAL_KM2 = 0.10            # área drenada mínima para dibujar un cauce

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

def polygonize(mask, transform, props_fn, simplify=0.00012, min_area=0):
    out = []
    for geom, val in features.shapes(mask.astype(np.uint8), mask=mask > 0, transform=transform):
        s = shape(geom).simplify(simplify, preserve_topology=True)
        if s.area * 1.19e10 < min_area: continue    # m² aprox. en el ecuador
        out.append((s, int(val)))
    return out

bounds_meta = {}
for key, (isla, (w, s, e, n)) in REGIONES.items():
    print("==", isla, key)
    srcs = [rasterio.open(f) for f in DEM]
    z, tr = merge(srcs, bounds=(w, s, e, n), nodata=-9999)
    z = z[0].astype("float32"); [x.close() for x in srcs]
    sea = z <= 0.5
    z[sea] = -9999
    prof = dict(driver="GTiff", height=z.shape[0], width=z.shape[1], count=1, dtype="float32",
                crs="EPSG:4326", transform=tr, nodata=-9999, compress="deflate")
    f = TMP / f"{key}_dem.tif"
    with rasterio.open(f, "w", **prof) as d: d.write(z, 1)
    H, W = z.shape
    dx = 30.87 * math.cos(math.radians((s + n) / 2)); dy = 30.87
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

    # --- Curvas de nivel ---
    xs = tr.c + tr.a * (np.arange(W) + 0.5); ys = tr.f + tr.e * (np.arange(H) + 0.5)
    cg = contourpy.contour_generator(xs, ys, np.where(sea, -1, z).astype("float64"), line_type="Separate")
    feats = []
    zmax = float(z[~sea].max())
    for lv in range(20, int(zmax) + 1, 20):
        for seg in cg.lines(lv):
            if len(seg) < 4: continue
            ls = LineString(seg).simplify(0.00008)
            feats.append({"type": "Feature", "geometry": mapping(ls),
                          "properties": {"isla": isla, "elev_m": lv, "maestra": lv % 100 == 0}})
    for seg in cg.lines(1.0):   # línea de costa aproximada del DEM
        if len(seg) >= 4:
            feats.append({"type": "Feature", "geometry": mapping(LineString(seg).simplify(0.00008)),
                          "properties": {"isla": isla, "elev_m": 0, "maestra": True}})
    save(f"{key}_curvas.geojson", feats)

    # --- Zonas costeras bajas (inundación costera / oleaje / tsunami) ---
    land = ~sea
    feats = []
    for lim, lab in [(3, "0–3 m"), (5, "3–5 m"), (10, "5–10 m")]:
        lo = {3: 0, 5: 3, 10: 5}[lim]
        m = median_filter((land & (z > lo) & (z <= lim)).astype(np.uint8), size=3).astype(bool)
        u = unary_union([shape(g_) for g_, _ in features.shapes(m.astype(np.uint8), mask=m, transform=tr)])
        for geom in [p_.simplify(0.00008, preserve_topology=True) for p_ in getattr(u, "geoms", [u]) if p_.area * 1.19e10 >= 3000]:
            feats.append({"type": "Feature", "geometry": mapping(geom),
                          "properties": {"isla": isla, "clase": lab, "max_m": lim}})
    save(f"{key}_costa_baja.geojson", feats)

    # --- Hidrología derivada ---
    # Quemado de cauces: baja 3 m el DEM sobre las quebradas IGM 1:25 000 para que el flujo las siga
    rios = [shape(ft["geometry"]) for ft in json.loads((ROOT/"capas/igm/rio.geojson").read_text())["features"]
            if ft["properties"]["isla"] == isla]
    igm_rio = features.rasterize([(g, 1) for g in rios], out_shape=(H, W), transform=tr, all_touched=True).astype(bool) if rios else np.zeros((H, W), bool)
    zb = z.copy(); zb[igm_rio & land] -= 3.0
    fb = TMP / f"{key}_dem_quemado.tif"
    with rasterio.open(fb, "w", **prof) as d: d.write(zb, 1)
    grid = Grid.from_raster(str(fb)); dem = grid.read_raster(str(fb))
    pit = grid.fill_pits(dem); fl = grid.fill_depressions(pit); inf = grid.resolve_flats(fl)
    fdir = grid.flowdir(inf)
    acc = grid.accumulation(fdir)
    thr = UMBRAL_KM2 / CELL_KM2
    streams = Raster((np.asarray(acc) > thr) & land, viewfinder=fdir.viewfinder)
    order = grid.stream_order(fdir, streams)
    net = grid.extract_river_network(fdir, streams)
    A = np.asarray(acc); O = np.asarray(order)
    inv = ~tr
    feats = []
    for ft in net["features"]:
        coords = ft["geometry"]["coordinates"]
        if len(coords) < 2: continue
        idx = [tuple(int(v) for v in inv * (x, y)) for x, y in coords]
        aa = [A[min(r, H-1), min(c, W-1)] for c, r in idx]; oo = [O[min(r, H-1), min(c, W-1)] for c, r in idx]
        km2 = float(max(aa)) * CELL_KM2
        ls = LineString(coords).simplify(0.00005)
        feats.append({"type": "Feature", "geometry": mapping(ls),
                      "properties": {"isla": isla, "area_drenada_km2": round(km2, 2), "orden": int(max(oo)),
                                     "fuente": "Derivado de Copernicus GLO-30 (umbral 0,1 km²)"}})
    save(f"{key}_drenaje_derivado.geojson", feats)

    # Cuencas: desembocaduras al mar de cauces con ≥ 1 km² drenados
    fd = np.asarray(fdir); dem_a = np.asarray(dem)
    # celdas de cauce cuyo vecino aguas abajo es mar/nodata
    dirmap = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
    outlets = []
    rr, cc = np.where((A * CELL_KM2 >= 1.0) & land)
    for r, c in zip(rr, cc):
        d = dirmap.get(int(fd[r, c]))
        if not d:      # celda terminal (borde con el mar)
            outlets.append((r, c, A[r, c] * CELL_KM2)); continue
        r2, c2 = r + d[0], c + d[1]
        if r2 < 0 or c2 < 0 or r2 >= H or c2 >= W or sea[r2, c2]:
            outlets.append((r, c, A[r, c] * CELL_KM2))
    feats = []
    lab = np.zeros((H, W), np.int32)
    for i, (r, c, km2) in enumerate(sorted(outlets, key=lambda t: -t[2])[:60], 1):
        x, y = tr * (c + 0.5, r + 0.5)
        cat = np.asarray(grid.catchment(x=x, y=y, fdir=fdir, xytype="coordinate"))
        lab[(cat > 0) & (lab == 0)] = i
        feats.append({"x": x, "y": y, "km2": km2, "id": i})
    cuencas = []
    meta = {f_["id"]: f_ for f_ in feats}
    bag = {}
    for geom, val in features.shapes(lab, mask=lab > 0, transform=tr): bag.setdefault(int(val), []).append(shape(geom))
    for val, gs in bag.items():
        m = meta[val]
        cuencas.append({"type": "Feature", "geometry": mapping(unary_union(gs).simplify(0.0002, preserve_topology=True)),
                        "properties": {"isla": isla, "cuenca_id": f"{key}-{val}", "area_km2": round(m["km2"], 2),
                                       "desembocadura": [round(m["x"], 5), round(m["y"], 5)]}})
    save(f"{key}_cuencas.geojson", cuencas)

    # HAND: altura sobre el drenaje más cercano → susceptibilidad a inundación fluvial/de quebrada
    major = ((np.asarray(acc) > (0.5 / CELL_KM2)) | (igm_rio & (np.asarray(acc) > (0.05 / CELL_KM2)))) & land
    dem0 = grid.read_raster(str(f))      # HAND sobre el DEM sin quemar
    hand = np.asarray(grid.compute_hand(fdir, dem0, Raster(major, viewfinder=fdir.viewfinder), nodata_out=np.nan))
    clsH = np.zeros((H, W), np.uint8)
    clsH[(hand <= 5) & land] = 1; clsH[(hand <= 2.5) & land] = 2; clsH[(hand <= 1) & land] = 3
    # restringe a 400 m del cauce (evita mesetas planas lejanas)
    from scipy.ndimage import distance_transform_edt, median_filter
    dist = distance_transform_edt(~np.asarray(major)) * 30.87
    clsH[dist > 300] = 0
    clsH = median_filter(clsH, size=3)
    feats = []
    names = {1: "Baja (HAND 2,5–5 m)", 2: "Media (HAND 1–2,5 m)", 3: "Alta (HAND ≤ 1 m)"}
    hp = np.zeros((H, W, 4), np.uint8)
    for k_, c_ in {1: (147, 197, 253, 120), 2: (59, 130, 246, 165), 3: (30, 58, 138, 210)}.items(): hp[clsH == k_] = c_
    png(hp, f"{key}_susc_inundacion.png")
    polys = {1: [], 2: [], 3: []}
    for geom, val in features.shapes(clsH, mask=clsH > 0, transform=tr): polys[int(val)].append(shape(geom))
    for lv, lst in polys.items():
        u = unary_union(lst)
        for part in getattr(u, "geoms", [u]):
            if part.area * 1.19e10 < 2500: continue
            feats.append({"type": "Feature", "geometry": mapping(part.simplify(0.00007, preserve_topology=True)),
                          "properties": {"isla": isla, "nivel": lv, "susceptibilidad": names[lv],
                                         "metodo": "HAND sobre Copernicus GLO-30; cauces IGM 1:25k + drenaje ≥ 0,5 km²; ≤ 300 m del cauce"}})
    save(f"{key}_susc_inundacion.geojson", feats)

(RAS / "limites.json").write_text(json.dumps(bounds_meta, ensure_ascii=False, indent=1))
print("ok")
