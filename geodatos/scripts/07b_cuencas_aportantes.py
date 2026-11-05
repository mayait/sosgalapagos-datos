"""Cuencas completas que drenan hacia zonas pobladas.

Para cada celda del DEM se sigue la dirección de flujo (D8, DEM con quebradas IGM quemadas) hasta la primera
celda poblada que encuentra (salto de punteros, O(N log N)). Las celdas se agrupan por el punto de entrada
a la zona poblada: cada grupo es una subcuenca aportante, completa aguas arriba aunque entre al Parque Nacional.

Uso: .venv/bin/python -I scripts/07b_cuencas_aportantes.py   (después de 03, 06 y 07; antes de 08)
"""
import json, pathlib
import numpy as np, rasterio
from rasterio import features
from scipy.ndimage import median_filter
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Relieve de cada isla: Santa Cruz usa el DTM 1 m de la SGIAR donde hay cobertura (03_dem.py, relieve_sgiar.py)
_DTM = (ROOT / "datos/dtm_sgiar/dtm_sgiar_1m.vrt").exists()
def relieve(isla):
    return "DTM 1 m SGIAR + Copernicus GLO-30" if _DTM and isla == "Santa Cruz" else "Copernicus GLO-30"
C = ROOT / "capas"; TMP = ROOT / "descargas/dem_recortes"
M = 1 / 111320; CELL_KM2 = (30.87e-3) ** 2
REG = {"Santa Cruz": "santa_cruz", "San Cristóbal": "san_cristobal", "Isabela": "isabela_sur"}
MIN_SUB_KM2 = 0.2          # subcuencas menores se agrupan como «escorrentía local»
def load(p): return json.loads((C / p).read_text())["features"]

# zonas pobladas: límite urbano IGM, uso residencial OSM, huella edificada, manzanas INEC
pobl = [(shape(f["geometry"]).buffer(0), f["properties"]) for f in load("final/zonas_pobladas.geojson") if f["properties"]["tipo"] != "OSM farmyard"]
pobl += [(shape(f["geometry"]).buffer(0), f["properties"]) for f in load("final/manzanas_inec.geojson")]
# nombres de localidades (límite urbano y poblados IGM)
loc = [(shape(f["geometry"]), f["properties"].get("nam")) for f in load("igm/zona_urbana.geojson") + load("igm/poblado.geojson") if f["properties"].get("nam")]
loc_tree = STRtree([g for g, _ in loc])
def nombre_loc(g):
    i = loc_tree.nearest(g); d = loc[i][0].distance(g) / M
    return loc[i][1] if d < 1500 else "Zona poblada rural"
quebr = [(shape(f["geometry"]), f["properties"].get("nombre")) for f in load("final/quebradas.geojson") if f["properties"].get("nombre")]
q_tree = STRtree([g for g, _ in quebr]) if quebr else None

PARR = {"200150": "Puerto Baquerizo Moreno", "200151": "El Progreso", "200250": "Puerto Villamil", "200251": "Tomás de Berlanga",
        "200350": "Puerto Ayora", "200351": "Bellavista", "200352": "Santa Rosa"}
manz_parr = {}
for f in load("final/manzanas_inec.geojson"):
    n = PARR.get(str(f["properties"].get("codigo", ""))[:6])
    if n: manz_parr.setdefault(n, []).append(shape(f["geometry"]).buffer(0))
for g, nm in [(shape(f["geometry"]), f["properties"].get("nam")) for f in load("igm/zona_urbana.geojson")]:
    if nm in manz_parr: manz_parr[nm].append(g)
LOCALIDAD = {n: unary_union(gs) for n, gs in manz_parr.items()}
completas = []
DIRS = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
out = []
for isla, key in REG.items():
    f = TMP / f"{key}_dem_quemado.tif"
    grid = Grid.from_raster(str(f)); dem = grid.read_raster(str(f))
    fdir = grid.flowdir(grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem))))
    acc = np.asarray(grid.accumulation(fdir))
    fd = np.asarray(fdir); H, W = fd.shape; N = H * W
    with rasterio.open(f) as d: tr = d.transform; z = d.read(1)
    land = z > -9000
    # siguiente celda aguas abajo (terminal → sí misma)
    rr, cc = np.indices((H, W))
    nr, nc = rr.copy(), cc.copy()
    for code, (dr, dc) in DIRS.items():
        m = fd == code; nr[m] += dr; nc[m] += dc
    ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W)
    nr = np.where(ok, nr, rr); nc = np.where(ok, nc, cc)
    nxt = (nr * W + nc).ravel()
    nxt[~land.ravel()] = np.flatnonzero(~land.ravel())               # el mar es terminal
    # celdas pobladas con identificador de polígono
    from shapely.geometry import box
    bx = box(tr.c, tr.f + tr.e * H, tr.c + tr.a * W, tr.f)
    shapes_i = [(g, i + 1) for i, (g, _) in enumerate(pobl) if g.intersects(bx)]
    P_id = features.rasterize(shapes_i, out_shape=(H, W), transform=tr, all_touched=True, dtype="int32").ravel()
    P = (P_id > 0) & land.ravel()
    # salto de punteros: primera celda poblada aguas abajo
    target = np.where(P, np.arange(N), -1)
    j = nxt.copy()
    for _ in range(int(np.ceil(np.log2(N))) + 1):
        un = target == -1
        target[un] = target[j[un]]
        j = j[j]
    up = (target >= 0) & ~P & land.ravel()
    for nm, gT in LOCALIDAD.items():
        if not gT.intersects(bx): continue
        PT = features.rasterize([(gT, 1)], out_shape=(H, W), transform=tr, all_touched=True).ravel().astype(bool) & land.ravel()
        hit = PT.copy(); j2 = nxt.copy()
        for _ in range(int(np.ceil(np.log2(N))) + 1):
            hit |= hit[j2]; j2 = j2[j2]
        m2 = median_filter(hit.reshape(H, W).astype(np.uint8), 3)
        g = unary_union([shape(x) for x, _ in features.shapes(m2, mask=m2 > 0, transform=tr)])
        g = g.buffer(15 * M, 4).buffer(-15 * M, 4).simplify(12 * M, preserve_topology=True)
        a_up = (hit & ~PT).sum() * CELL_KM2
        completas.append({"type": "Feature", "geometry": mapping(g), "properties": {"isla": isla, "tipo": "Cuenca completa de la localidad",
            "destino": nm, "area_km2": round(g.area / M**2 / 1e6, 2), "area_aguas_arriba_km2": round(a_up, 2),
            "descripcion": f"Todo el terreno cuya agua termina pasando por {nm}, incluida la parte alta y lo que atraviesa otros poblados",
            "fuente": f"Modelo D8 sobre {relieve(isla)} con quebradas IGM quemadas; localidad = manzanas INEC + límite urbano IGM"}})
        print(f"   cuenca completa {nm}: {a_up:.1f} km² aguas arriba")                           # celdas aguas arriba que drenan a un poblado
    print(f"{isla}: {up.sum() * CELL_KM2:.1f} km² drenan hacia zonas pobladas")
    # agrupar por punto de entrada; las subcuencas pequeñas se agrupan por localidad
    ent, cnt = np.unique(target[up], return_counts=True)
    area = dict(zip(ent.tolist(), (cnt * CELL_KM2).tolist()))
    meta = {}
    nid = 0
    big = [e for e in ent.tolist() if area[e] >= MIN_SUB_KM2]
    for e in big:
        nid += 1; meta[nid] = ("subcuenca", e)
    ent_to_id = {e: i for i, (t, e) in meta.items()}
    lab_up = np.zeros(N, np.int32)
    tid = np.zeros(N, np.int64); tid[up] = target[up]
    # vectorizado: mapa entrada → id
    keys = np.array(list(ent_to_id.keys()), dtype=np.int64); vals = np.array(list(ent_to_id.values()), dtype=np.int32)
    order = np.argsort(keys); keys, vals = keys[order], vals[order]
    pos = np.searchsorted(keys, tid[up]); pos = np.clip(pos, 0, len(keys) - 1)
    hit = keys[pos] == tid[up]
    lab_up[np.flatnonzero(up)[hit]] = vals[pos[hit]]
    # escorrentía local: el resto, agrupado por localidad de destino
    resto = up & (lab_up == 0)
    loc_ids = {}
    for t in np.unique(target[resto]).tolist():
        r, c = divmod(t, W); x, y = tr * (c + .5, r + .5)
        nm = nombre_loc(Point(x, y))
        if nm not in loc_ids:
            nid += 1; loc_ids[nm] = nid; meta[nid] = ("local", nm)
    tr_loc = {t: loc_ids[nombre_loc(Point(*(tr * (divmod(t, W)[1] + .5, divmod(t, W)[0] + .5))))] for t in np.unique(target[resto]).tolist()}
    idx = np.flatnonzero(resto)
    lab_up[idx] = [tr_loc[t] for t in target[resto].tolist()]
    L2 = median_filter(lab_up.reshape(H, W), size=3)
    L2[~up.reshape(H, W) & (L2 > 0) & ~(median_filter(up.reshape(H, W).astype(np.uint8), 3) > 0)] = 0
    polys = {}
    for geom, v in features.shapes(L2.astype(np.int32), mask=L2 > 0, transform=tr):
        polys.setdefault(int(v), []).append(shape(geom))
    for v, gs in polys.items():
        g = unary_union(gs).buffer(15 * M, 4).buffer(-15 * M, 4).simplify(12 * M, preserve_topology=True)
        tipo, e = meta[v]
        a = g.area / M**2 / 1e6
        if tipo == "subcuenca":
            r, c = divmod(e, W); x, y = tr * (c + .5, r + .5); pe = Point(x, y)
            destino = nombre_loc(pe)
            q = None
            if q_tree is not None:
                k = q_tree.nearest(pe)
                if quebr[k][0].distance(pe) / M < 150: q = quebr[k][1]
            props = {"isla": isla, "tipo": "Subcuenca aportante", "destino": destino, "quebrada": q, "area_km2": round(a, 2),
                     "area_drenada_entrada_km2": round(float(acc.ravel()[e]) * CELL_KM2, 2),
                     "punto_entrada": [round(x, 5), round(y, 5)],
                     "descripcion": f"Toda el área cuya agua llega a {destino}" + (f" por la {q}" if q else ""),
                     "fuente": f"Modelo D8 sobre {relieve(isla)} con quebradas IGM quemadas"}
        else:
            props = {"isla": isla, "tipo": "Escorrentía local", "destino": e, "area_km2": round(a, 2),
                     "descripcion": f"Laderas pequeñas que escurren directamente hacia {e}",
                     "fuente": f"Modelo D8 sobre {relieve(isla)}"}
        if a < 0.02: continue
        out.append({"type": "Feature", "geometry": mapping(g), "properties": {k: v for k, v in props.items() if v is not None}})
out.sort(key=lambda f: (f["properties"]["tipo"] != "Escorrentía local", -f["properties"]["area_km2"]))
completas.sort(key=lambda f: -f["properties"]["area_km2"])
(C / "dem/cuencas_localidad.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": completas}, ensure_ascii=False, separators=(",", ":")))
(C / "dem/cuencas_aportantes.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": out}, ensure_ascii=False, separators=(",", ":")))
for isla in REG:
    sub = [f for f in out if f["properties"]["isla"] == isla and f["properties"]["tipo"] == "Subcuenca aportante"]
    print(f"  {isla}: {len(sub)} subcuencas; mayores: " + ", ".join(f"{f['properties']['destino']} {f['properties']['area_km2']} km²" for f in sorted(sub, key=lambda f: -f['properties']['area_km2'])[:5]))
