"""Puntos potenciales de inundación en las zonas pobladas de Santa Cruz (fuera de La Cascada).

Tres tipos de punto, todos sobre Copernicus GLO-30 (DSM, 30 m) reproyectado a UTM 15S:
  VASO     depresión cerrada del DSM crudo (relleno de depresiones) que toca zona poblada; cota de rebose = nivel de relleno.
  LLEGADA  celda donde un flujo D8 (DSM con quebradas IGM quemadas) con área aportante >= A_LLEGADA_MIN_KM2 entra en zona poblada.
  PIE      zona poblada casi plana (< PIE_PEND_MAX) al pie de una ladera (pendiente >= PIE_PEND_LADERA en 150 m) que recibe flujo.

Para cada punto: área aportante, volumen del vaso, edificios y población expuestos, y caudal pico (SCS-CN + HU SCS) con
la lluvia MEDIDA del 30-oct-2026 (red IERSE-WSN) y con una tormenta tipo II de 100 mm. Ranking de prioridad con criterios
explícitos. Análisis específico del sector Tomás de Berlanga (vía Puerto Ayora–Bellavista).

Uso:  .venv/bin/python -I scripts/15_santa_cruz_inundacion.py     (después de 12_cascada_analisis.py, que copia la lluvia IERSE)
Salidas: estudios/santa-cruz/datos/ (puntos_inundacion.geojson, vasos.geojson, cuencas_puntos.geojson, acumulacion_d8.tif,
         direcciones_d8.tif, resumen.json, hidrogramas_puntos_30oct.csv; añade los hitos de Tomás de Berlanga a hitos_hidrologicos.csv)
Limitación: el DSM incluye techos y vegetación (±2–4 m; sesgo ≈ −2 m frente al IGM). Las depresiones de < 2 m entre edificios
pueden ser artefactos. Sirve para priorizar inspecciones, no para delimitar.
"""
import csv, json, math, pathlib, tempfile, datetime as dt
import numpy as np, rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy import ndimage
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, transform as stransform
from shapely.strtree import STRtree
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "estudios/santa-cruz/datos"
LC = ROOT / "estudios/la-cascada/datos"
EPSG = 32715; CELDA = 30.0
A_LLEGADA_MIN_KM2 = 0.25
VASO_PROF_MIN_M = 1.0; VASO_AREA_MIN_HA = 0.18; VASO_VOL_MIN_M3 = 1000
PIE_PEND_MAX = 2.0; PIE_PEND_LADERA = 10.0; PIE_A_MIN_KM2 = 0.05; PIE_AREA_MIN_HA = 0.27
FRANJA_LLEGADA_M = 300; FRANJA_BUFFER_M = 30
CN = 76                                   # central, como en La Cascada (intermedio AMC II–III)
DT_H = 1 / 6; SIM_H = 48
COTA_G, COTA_SR = 178.0, 416.0
PUNTO_TDB = (-90.3198, -0.7109)          # sector Tomás de Berlanga (contexto del coordinador)
HITOS_CSV = OUT / "hitos_hidrologicos.csv"
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)
T = Transformer.from_crs(4326, EPSG, always_xy=True).transform
TI = Transformer.from_crs(EPSG, 4326, always_xy=True).transform
OUT.mkdir(parents=True, exist_ok=True)


def a_utm(p):
    src = rasterio.open(p)
    tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG}", src.width, src.height, *src.bounds, resolution=CELDA)
    arr = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), arr, src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs=f"EPSG:{EPSG}",
              resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    return arr, tr


def feats(rel, cond=lambda p: True):
    out = []
    for f in json.loads((ROOT / rel).read_text())["features"]:
        if f["properties"].get("isla", "Santa Cruz") != "Santa Cruz" or not cond(f["properties"]): continue
        g = shape(f["geometry"]); g = g.buffer(0) if g.geom_type.endswith("Polygon") else g
        out.append((stransform(T, g), f["properties"]))
    return out


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


# ---------------------------------------------------------------- DEM, D8, relleno
dem, TR = a_utm(ROOT / "descargas/dem_recortes/santa_cruz_dem.tif")
demq, _ = a_utm(ROOT / "descargas/dem_recortes/santa_cruz_dem_quemado.tif")
H, W = dem.shape; N = H * W
nod = dem == -9999; sea = nod | (dem <= 0.5)
with tempfile.TemporaryDirectory() as td:
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=f"EPSG:{EPSG}", transform=TR, nodata=-9999)
    for n_, a_ in (("q.tif", demq), ("c.tif", dem)):
        with rasterio.open(f"{td}/{n_}", "w", **prof) as d: d.write(a_, 1)
    g = Grid.from_raster(f"{td}/q.tif"); dq = g.read_raster(f"{td}/q.tif")
    fd = g.flowdir(g.resolve_flats(g.fill_depressions(g.fill_pits(dq))), dirmap=DIRMAP)
    F = np.asarray(fd).astype(np.int32); A = np.asarray(g.accumulation(fd, dirmap=DIRMAP)) * CELDA ** 2 / 1e6   # km²
    g2 = Grid.from_raster(f"{td}/c.tif"); dc = g2.read_raster(f"{td}/c.tif")
    lleno = np.asarray(g2.fill_depressions(g2.fill_pits(dc)))
A = np.where(nod, 0, A).astype("float32")
with rasterio.open(OUT / "acumulacion_d8.tif", "w", **{**prof, "nodata": -1}) as d:
    d.write(np.where(nod, -1, A).astype("float32"), 1)
    d.update_tags(unidades="km2 de área aportante", metodo="D8 pysheds sobre GLO-30 con quebradas IGM quemadas (3 m), depresiones rellenadas", crs="EPSG:32715")
with rasterio.open(OUT / "direcciones_d8.tif", "w", **{**prof, "dtype": "uint8", "nodata": 0}) as d:
    d.write(np.where(nod | ~np.isin(F, list(OFF)), 0, F).astype("uint8"), 1)
    d.update_tags(dirmap="N=64 NE=128 E=1 SE=2 S=4 SO=8 O=16 NO=32 (convención ESRI)", crs="EPSG:32715")
rr, cc = np.indices((H, W))
nr, nc = rr.copy(), cc.copy()
for k, (a, b) in OFF.items():
    m = F == k; nr[m] += a; nc[m] += b
ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W) & np.isin(F, list(OFF)) & ~nod
nr = np.where(ok, nr, rr); nc = np.where(ok, nc, cc)
nxt = (nr * W + nc).ravel()
paso = np.where((nr != rr) & (nc != cc), CELDA * math.sqrt(2), CELDA).ravel()
zf = dem.ravel()
# longitud del recorrido más largo aguas arriba y cota de su origen (orden topológico = acumulación creciente)
Lup = np.zeros(N, "float64"); zsrc = zf.astype("float64").copy()
orden = np.argsort(A.ravel(), kind="stable")
orden = orden[~nod.ravel()[orden]]
Lup_l = Lup.tolist(); zs_l = zsrc.tolist(); nx_l = nxt.tolist(); ps_l = paso.tolist()
for i in orden.tolist():
    j = nx_l[i]
    if j != i:
        c_ = Lup_l[i] + ps_l[i]
        if c_ > Lup_l[j]: Lup_l[j] = c_; zs_l[j] = zs_l[i]
Lup = np.array(Lup_l); zsrc = np.array(zs_l)
# lista de celdas aguas arriba (CSR) para delimitar cuencas
o_up = np.argsort(nxt, kind="stable"); cnt = np.bincount(nxt, minlength=N); ini = np.concatenate([[0], np.cumsum(cnt)])


def cuenca_mask(seed_idx):
    vis = [seed_idx]; out = {seed_idx}; k_ = 0
    while k_ < len(vis):
        j = vis[k_]; k_ += 1
        for u in o_up[ini[j]:ini[j + 1]].tolist():
            if u != j and u not in out: out.add(u); vis.append(u)
    return np.fromiter(out, dtype=np.int64)


pend = np.hypot(*np.gradient(np.where(nod, np.nan, dem), CELDA)) * 100

# ---------------------------------------------------------------- capas de exposición y contexto
casc = unary_union([g_ for g_, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("nombre") == "La Cascada")] +
                   [g_ for g_, p in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") == "LA CASCADA")])
pobl = [(g_, p) for g_, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")]
barrios = feats("capas/final/barrios.geojson")
P_geo = unary_union([g_ for g_, _ in pobl] + [g_ for g_, _ in barrios])
P = rasterize([(P_geo, 1)], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool) & ~nod
CASC = rasterize([(casc.buffer(60), 1)], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool)
edif = feats("capas/final/edificios_exposicion.geojson"); t_ed = STRtree([g_ for g_, _ in edif])
manz = feats("capas/final/manzanas_inec.geojson"); t_mz = STRtree([g_ for g_, _ in manz])
loc_igm = [(g_, p.get("nam")) for g_, p in feats("capas/igm/zona_urbana.geojson") + feats("capas/igm/poblado.geojson") if p.get("nam")]
urb = {p.get("nam"): g_ for g_, p in feats("capas/igm/zona_urbana.geojson") if p.get("nam")}
eventos = [(g_, p) for g_, p in feats("capas/final/eventos_historicos.geojson", lambda p: p.get("evento") == "Inundación")]
riesgo = [g_ for g_, p in feats("capas/final/riesgos_cgreg.geojson", lambda p: "inundaci" in (p.get("tipo") or "").lower())]
vias = feats("export/galapagos/vias.geojson"); t_via = STRtree([g_ for g_, _ in vias])
agua = [g_ for g_, p in feats("capas/osm/hidro_areas.geojson") if p.get("natural") in ("water", "wetland")]; t_agua = STRtree(agua)
queb = [g_ for g_, _ in feats("capas/final/quebradas.geojson")]; t_q = STRtree(queb)


def exposicion(geom):
    ids = t_ed.query(geom, predicate="intersects")
    pob = viv = 0.0
    for i in t_mz.query(geom, predicate="intersects"):
        gm, pm = manz[i]
        if gm.area: fr = gm.intersection(geom).area / gm.area; pob += fr * (pm.get("pob_estimada") or 0); viv += fr * (pm.get("viviendas") or 0)
    return len(ids), round(pob), round(viv)


def localidad(pt):
    for nm_, g_ in urb.items():
        if g_.distance(pt) < 300: return nm_
    return "rural"


def sector(pt):
    for g_, p in barrios:
        if g_.contains(pt): return p.get("nombre")
    best = min(loc_igm, key=lambda x: x[0].distance(pt))
    return best[1] if best[0].distance(pt) < 800 else None


def evidencia(pt):
    ev = [f"SNGR {p.get('año')}-{p.get('mes')} {str(p.get('sector') or '').strip()}" for g_, p in eventos if g_.distance(pt) < 300]
    if any(g_.contains(pt) for g_ in riesgo): ev.append("CGREG: riesgo de inundación")
    return sorted(set(ev))


def lonlat(i):
    r_, c_ = divmod(int(i), W); return [round(v, 6) for v in TI(*(TR * (c_ + .5, r_ + .5)))]


# ---------------------------------------------------------------- lluvia: medida 30-oct (IERSE) y tipo II 100 mm
t0 = dt.datetime(2026, 10, 30, 0, 0)
tm = np.arange(0, SIM_H + 1e-9, DT_H); nb = len(tm)
serie = {}
for f in csv.DictReader(open(LC / "lluvia_ierse_30oct_5min.csv")):
    k = int((dt.datetime.fromisoformat(f["fecha_hora_local"]) - t0).total_seconds() // (DT_H * 3600))
    if 0 <= k < nb: serie.setdefault(f["estacion"], np.zeros(nb))[k] += float(f["lluvia_mm"] or 0)
G_, SR_ = serie["Los Guayabillos"], serie["Santa Rosa"]
TII_H = [0, 2, 4, 6, 7, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 11.75, 12, 12.5, 13, 13.5, 14, 16, 20, 24]
TII_F = [0, .022, .048, .080, .098, .120, .133, .147, .163, .181, .204, .235, .283, .357, .663, .735, .772, .799, .820, .880, .952, 1.0]
Pc_100 = 100 * np.interp(tm, TII_H, TII_F)
UH_T = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5]
UH_Q = [0, .03, .1, .19, .31, .47, .66, .82, .93, .99, 1, .99, .93, .86, .78, .68, .56, .46, .39, .33, .28, .207, .147, .107, .077, .055, .04, .029, .021, .015, .011, .005, 0]


def hidrograma(Pc, area_km2, tc_h, cn=CN):
    S = 25400 / cn - 254; Ia = 0.2 * S
    Q = np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0); exc = np.diff(Q, prepend=0)
    tp = DT_H / 2 + 0.6 * tc_h; tt = np.arange(0, 5 * tp + DT_H, DT_H); u = np.interp(tt / tp, UH_T, UH_Q)
    u = u / (u.sum() * DT_H * 3600) * area_km2 * 1e6 / 1000
    return np.convolve(exc, u)[:nb], float(Q[-1])


def tcs(L, Hh):
    S = max(Hh / max(L, CELDA), 0.005)
    return max(0.0195 * max(L, CELDA) ** 0.77 * S ** -0.385 / 60, 1 / 6), max(0.3 * ((max(L, CELDA) / 1000) / S ** 0.25) ** 0.76, 1 / 6)


def hora(x):
    return (t0 + dt.timedelta(hours=float(x))).strftime("%d-%b %H:%M")


def hidro_punto(i, cmask):
    """Caudales del punto (celda i) con su cuenca cmask (índices)."""
    area = float(A.ravel()[i]); L = float(Lup[i]); Hh = float(zsrc[i] - zf[i])
    tk, tt_ = tcs(L, Hh)
    zm = float(np.mean(zf[cmask])); alfa = float(np.clip((zf[cmask] - COTA_G) / (COTA_SR - COTA_G), 0, 1).mean())
    Pc = np.cumsum((1 - alfa) * G_ + alfa * SR_)
    qt, Qmm = hidrograma(Pc, area, tt_); qk, _ = hidrograma(Pc, area, tk); q100, Q100 = hidrograma(Pc_100, area, tt_)
    q100k, _ = hidrograma(Pc_100, area, tk)
    return {"area_km2": round(area, 3), "L_km": round(L / 1000, 2), "cota_media_cuenca_m": round(zm), "lluvia_30oct_mm": round(float(Pc[-1]), 1),
            "tc_kirpich_h": round(tk, 2), "tc_temez_h": round(tt_, 2), "escorrentia_30oct_mm": round(Qmm, 1),
            "vol_escorrentia_30oct_m3": int(Qmm / 1000 * area * 1e6),
            "q30_temez_m3s": round(float(qt.max()), 2), "q30_kirpich_m3s": round(float(qk.max()), 2),
            "hora_pico_30oct": f"{hora(tm[qk.argmax()])} – {hora(tm[qt.argmax()])}",
            "q100_temez_m3s": round(float(q100.max()), 2), "q100_kirpich_m3s": round(float(q100k.max()), 2)}, (qt, qk)


# ---------------------------------------------------------------- candidatos
puntos, vasos_f, cuencas_f, hidros = [], [], [], {}
# (a) vasos
prof_dep = np.where(nod, 0, lleno - dem)
lab, nlab = ndimage.label(prof_dep > 0.001, structure=np.ones((3, 3)))
idx = np.arange(1, nlab + 1)
pmax = ndimage.maximum(prof_dep, lab, idx); ncel = ndimage.sum(np.ones_like(prof_dep), lab, idx); vol = ndimage.sum(prof_dep, lab, idx) * CELDA ** 2
reb = ndimage.maximum(lleno, lab, idx)
toca_P = ndimage.maximum(ndimage.binary_dilation(P), lab, idx) > 0; toca_C = ndimage.maximum(CASC, lab, idx) > 0
sel = idx[(pmax >= VASO_PROF_MIN_M) & (ncel * 900 / 1e4 >= VASO_AREA_MIN_HA) & (vol >= VASO_VOL_MIN_M3) & toca_P & ~toca_C]
# área aportante a cada vaso: celdas cuyo flujo D8 pasa por el vaso
labf = lab.ravel(); tgt = np.where(np.isin(labf, sel), labf, 0); j = nxt.copy()
for _ in range(int(np.ceil(np.log2(N))) + 1):
    un = tgt == 0; tgt[un] = tgt[j[un]]; j = j[j]
for v in sel.tolist():
    m = lab == v
    geom = unary_union([shape(s_) for s_, _ in shapes(m.astype("uint8"), mask=m, transform=TR)])
    ideep = int(np.flatnonzero(m.ravel())[np.argmax(prof_dep.ravel()[m.ravel()])])
    cdir = np.flatnonzero(tgt == v)                                                # celdas que llegan primero a este vaso
    cin = np.flatnonzero(m.ravel())
    ihid = int(cin[np.argmax(A.ravel()[cin])])                                     # celda de mayor acumulación dentro del vaso
    cm = cuenca_mask(ihid)                                                         # cuenca total (incluye lo que atraviesa otros vasos)
    hp, qs = hidro_punto(ihid, cm); hp["area_directa_km2"] = round(cdir.size * 900 / 1e6, 3)
    ne, pob, viv = exposicion(geom)
    pt = Point(TR * ((ideep % W) + .5, (ideep // W) + .5))
    puntos.append({"tipo": "VASO", "i": ideep, "geom_expo": geom, "cmask": cm, "q": qs,
                   "props": {"cota_fondo_m": round(float(zf[ideep]), 1), "cota_rebose_m": round(float(reb[v - 1]), 2),
                             "prof_max_m": round(float(pmax[v - 1]), 2), "area_vaso_ha": round(float(ncel[v - 1]) * 900 / 1e4, 2),
                             "vol_vaso_m3": int(vol[v - 1]), **hp, "se_llena_30oct": hp["vol_escorrentia_30oct_m3"] >= vol[v - 1],
                             "edificios": ne, "poblacion": pob, "viviendas": viv}})
    vasos_f.append((geom, v))
# (b) llegadas de flujo a zona poblada
Pf = P.ravel()
tgtP = np.where(Pf, np.arange(N), -1); j = nxt.copy()
for _ in range(int(np.ceil(np.log2(N))) + 1):
    un = tgtP == -1; tgtP[un] = tgtP[j[un]]; j = j[j]
ent = np.unique(tgtP[(~Pf) & (tgtP >= 0) & Pf[nxt] & (np.arange(N) != nxt)])        # celdas pobladas que reciben flujo de fuera
ent = [int(e) for e in ent if A.ravel()[e] >= A_LLEGADA_MIN_KM2 and not CASC.ravel()[e]]
ent.sort(key=lambda e: -A.ravel()[e])
usados = []
for e in ent:
    pe = np.array(TR * ((e % W) + .5, (e // W) + .5))
    if any(np.hypot(*(pe - u)) < 90 for u in usados): continue
    usados.append(pe)
    path = [e]; Lp = 0.0
    while Lp < FRANJA_LLEGADA_M and nxt[path[-1]] != path[-1]:
        Lp += paso[path[-1]]; path.append(int(nxt[path[-1]]))
    ln = LineString([TR * ((p_ % W) + .5, (p_ // W) + .5) for p_ in path]) if len(path) > 1 else Point(pe).buffer(1)
    franja = ln.buffer(FRANJA_BUFFER_M)
    cm = cuenca_mask(e)
    hp, qs = hidro_punto(e, cm)
    ne, pob, viv = exposicion(franja)
    pt = Point(pe)
    near_q = t_q.query(pt.buffer(60), predicate="intersects"); near_v = [vias[i][1] for i in t_via.query(franja, predicate="intersects")]
    puntos.append({"tipo": "LLEGADA", "i": e, "geom_expo": franja, "cmask": cm, "q": qs,
                   "props": {"cota_m": round(float(zf[e]), 1), **hp, "edificios": ne, "poblacion": pob, "viviendas": viv,
                             "quebrada_cartografiada_a_60m": bool(len(near_q)),
                             "vias_en_franja": sorted({str(p.get("nombre") or p.get("tipo_osm") or "s/n") for p in near_v})[:6]}})
# (c) pie de ladera
ladera = ndimage.maximum_filter(np.nan_to_num(pend), size=11) >= PIE_PEND_LADERA
pie = P & ~CASC & (ndimage.uniform_filter(np.nan_to_num(pend), 3) < PIE_PEND_MAX) & ladera & (A >= PIE_A_MIN_KM2)
labp, npie = ndimage.label(ndimage.binary_dilation(pie), structure=np.ones((3, 3)))
for v in range(1, npie + 1):
    m = (labp == v) & pie
    if m.sum() * 900 / 1e4 < PIE_AREA_MIN_HA: continue
    cells = np.flatnonzero(m.ravel()); i = int(cells[np.argmax(A.ravel()[cells])])
    geom = unary_union([shape(s_) for s_, _ in shapes((labp == v).astype("uint8"), mask=labp == v, transform=TR)]).buffer(FRANJA_BUFFER_M)
    cm = cuenca_mask(i)
    hp, qs = hidro_punto(i, cm)
    ne, pob, viv = exposicion(geom)
    puntos.append({"tipo": "PIE", "i": i, "geom_expo": geom, "cmask": cm, "q": qs,
                   "props": {"cota_m": round(float(zf[i]), 1), "area_zona_ha": round(m.sum() * 900 / 1e4, 2), **hp, "edificios": ne, "poblacion": pob, "viviendas": viv}})

# ---------------------------------------------------------------- ranking
CASC0 = rasterize([(casc, 1)], out_shape=dem.shape, transform=TR, all_touched=True).astype(bool).ravel()
for p_ in puntos:
    p_["props"]["recibe_desborde_la_cascada"] = bool(CASC0[p_["cmask"]].any())
vas_geo = [(p_["geom_expo"], p_) for p_ in puntos if p_["tipo"] == "VASO"]
for p_ in puntos:
    pt = Point(TR * ((p_["i"] % W) + .5, (p_["i"] // W) + .5))
    pr = p_["props"]; ev = evidencia(pt)
    E = pr["edificios"]; Q = pr["q30_temez_m3s"]
    llena = 1 if p_["tipo"] == "VASO" and pr["se_llena_30oct"] else 0
    pr["evidencia"] = ev
    pr["cuerpo_de_agua_osm"] = bool(len(t_agua.query(p_["geom_expo"] if p_["tipo"] == "VASO" else pt, predicate="intersects")))
    pr["puntaje"] = round(math.log10(1 + E) + math.log10(1 + Q) + 0.5 * bool(ev) + 0.5 * llena, 2)
    pr["prioridad"] = "Alta" if pr["puntaje"] >= 3.0 else ("Media" if pr["puntaje"] >= 2.0 else "Baja")
    pr.update({"tipo": p_["tipo"], "lon": lonlat(p_["i"])[0], "lat": lonlat(p_["i"])[1], "localidad": localidad(pt), "sector": sector(pt)})
puntos.sort(key=lambda p_: -p_["props"]["puntaje"])
for k_, p_ in enumerate(puntos, 1):
    p_["props"]["id"] = f"SC-{k_:03d}"; p_["props"]["rango"] = k_
for p_ in puntos:
    if p_["tipo"] != "VASO":
        pt = Point(TR * ((p_["i"] % W) + .5, (p_["i"] // W) + .5))
        p_["props"]["dentro_de_vaso"] = [q_["props"]["id"] for g_, q_ in vas_geo if g_.buffer(30).contains(pt)]
CRIT = ("puntaje = log10(1 + edificios expuestos) + log10(1 + Q pico 30-oct, Témez, m³/s) + 0,5 si hay evidencia histórica "
        "(SNGR inundación a < 300 m o zona de riesgo de inundación del CGREG) + 0,5 si es un vaso que el evento llenó. "
        "Alta >= 3,0; Media 2,0–3,0; Baja < 2,0. Edificios: dentro del vaso; franja de 300 m × 60 m aguas abajo de la llegada; zona de pie + 30 m.")

# ---------------------------------------------------------------- Tomás de Berlanga
ptb = Point(T(*PUNTO_TDB)); ctb, rtb = ~TR * ptb.coords[0]; itb = int(rtb) * W + int(ctb)
win = np.zeros((H, W), bool); win[int(rtb) - 10:int(rtb) + 11, int(ctb) - 10:int(ctb) + 11] = True
cand = np.flatnonzero((win & (A >= 1.0)).ravel())
ich = int(cand[np.argmin([np.hypot(*(np.array(TR * ((c_ % W) + .5, (c_ // W) + .5)) - np.array(ptb.coords[0]))) for c_ in cand])]) if cand.size else None
tdb = {"punto": PUNTO_TDB, "cota_dsm_m": round(float(zf[itb]), 1), "prof_depresion_max_200m_m": round(float(prof_dep[int(rtb) - 7:int(rtb) + 8, int(ctb) - 7:int(ctb) + 8].max()), 2),
       "pendiente_local_pct": round(float(ndimage.uniform_filter(np.nan_to_num(pend), 3)[int(rtb), int(ctb)]), 1),
       "area_aportante_punto_km2": round(float(A.ravel()[itb]), 3)}
if ich is not None:
    cm = cuenca_mask(ich)
    hp, (qt, qk) = hidro_punto(ich, cm)
    pc_ = Point(TR * ((ich % W) + .5, (ich // W) + .5))
    # trazado del cauce D8 600 m aguas arriba y abajo
    path_dn = [ich]
    for _ in range(20): path_dn.append(int(nxt[path_dn[-1]]))
    path_up = [ich]
    for _ in range(20):
        ups = o_up[ini[path_up[-1]]:ini[path_up[-1] + 1]]
        ups = ups[ups != path_up[-1]]
        if not ups.size: break
        path_up.append(int(ups[np.argmax(A.ravel()[ups])]))
    traza = path_up[::-1][:-1] + path_dn
    ln = LineString([TR * ((c_ % W) + .5, (c_ // W) + .5) for c_ in traza])
    cruces = []
    for i_v in t_via.query(ln, predicate="intersects"):
        x_ = vias[i_v][0].intersection(ln)
        for gx in getattr(x_, "geoms", [x_]):
            if gx.geom_type == "Point": cruces.append({"via": vias[i_v][1].get("nombre") or vias[i_v][1].get("tipo_osm"), "jerarquia": vias[i_v][1].get("jerarquia"),
                                                       "lonlat": [round(v, 5) for v in TI(*gx.coords[0])], "dist_al_punto_m": round(gx.distance(ptb))})
    perfil = [{"dist_m": round(k * CELDA), "cota_m": round(float(zf[c_]), 1), "area_km2": round(float(A.ravel()[c_]), 2), "en_zona_poblada": bool(Pf[c_])}
              for k, c_ in enumerate(traza)]
    ne, pob, viv = exposicion(ln.buffer(FRANJA_BUFFER_M))
    tdb.update({"cauce_d8_cercano_lonlat": [round(v, 5) for v in TI(*pc_.coords[0])], "dist_cauce_m": round(pc_.distance(ptb)), **hp,
                "quebrada_cartografiada_a_100m": bool(len(t_q.query(ln.buffer(100), predicate="intersects"))),
                "quebradas_cartografiadas_en_traza_m": round(sum(queb[i_].intersection(ln.buffer(60)).length for i_ in t_q.query(ln.buffer(60)))),
                "tramos_traza_con_quebrada": [k * 30 for k, c_ in enumerate(traza) if len(t_q.query(Point(TR * ((c_ % W) + .5, (c_ // W) + .5)).buffer(60), predicate="intersects"))],
                "cruces_con_vias": cruces,
                "edificios_franja_60m_1200m": ne, "poblacion_franja": pob, "perfil_cauce": perfil,
                "cuenca_drena_a_la_cascada": "ver estudios/la-cascada (rama 2)"})
    sig = np.argmax(qt > 1) if (qt > 1).any() else None
    hit = [[hora(tm[np.argmax(qk > 1)]) if (qk > 1).any() else "", "Tomás de Berlanga: inicio de escorrentía significativa en el cauce (Q > 1 m³/s)", "",
            f"{hora(tm[np.argmax(qk > 1)])} (Kirpich) a {hora(tm[sig]) if sig is not None else '—'} (Témez)"],
           [hora(tm[qk.argmax()]), "Tomás de Berlanga: caudal pico en el cauce junto al sector (tc Kirpich)", f"{qk.max():.0f} m³/s", f"Témez: {qt.max():.0f} m³/s a las {hora(tm[qt.argmax()])}; CN 76; lluvia {hp['lluvia_30oct_mm']} mm"]]
    rows = list(csv.reader(open(HITOS_CSV))) if HITOS_CSV.exists() else [["fecha_hora_utc6", "hito", "valor", "incertidumbre"]]
    rows = [r_ for r_ in rows if not (len(r_) > 1 and r_[1].startswith("Tomás de Berlanga:"))]
    for h_ in hit: rows.append(["2026-" + dt.datetime.strptime(h_[0], "%d-%b %H:%M").strftime("%m-%dT%H:%M") if h_[0] else "", h_[1], h_[2], h_[3]])
    with open(HITOS_CSV, "w", newline="") as fh: csv.writer(fh).writerows(rows)
    hidros["Tomas_de_Berlanga_cauce_temez"] = qt; hidros["Tomas_de_Berlanga_cauce_kirpich"] = qk
    # ¿a dónde va el cauce? (aguas abajo hasta el barrio La Cascada o el mar)
    k_ = ich; Ld = 0.0
    while not CASC0[k_] and not sea.ravel()[k_] and nxt[k_] != k_ and Ld < 30000: Ld += paso[k_]; k_ = int(nxt[k_])
    tdb["aguas_abajo"] = {"llega_a_la_cascada": bool(CASC0[k_]), "distancia_km": round(Ld / 1000, 2), "punto_final_lonlat": lonlat(k_)}
    # se añade como punto propio (cauce que atraviesa la zona poblada; no es una «llegada» porque la zona poblada es continua aguas arriba)
    ne2, pob2, viv2 = exposicion(ln.buffer(FRANJA_BUFFER_M))
    sc = round(math.log10(1 + ne2) + math.log10(1 + hp["q30_temez_m3s"]), 2)
    fp_tdb = {"type": "Feature", "geometry": r6(pc_), "properties": {
        "id": "SC-TdB", "tipo": "CAUCE_EN_ZONA_POBLADA", "localidad": "rural", "sector": "TOMAS DE BERLANGA", **hp,
        "edificios": ne2, "poblacion": pob2, "viviendas": viv2, "evidencia": ["Reporte del coordinador (fase 2): el sector se inunda"],
        "puntaje": round(sc + 0.5, 2), "prioridad": "Alta" if sc + 0.5 >= 3 else ("Media" if sc + 0.5 >= 2 else "Baja"),
        "nota": "Cauce D8 de 9,4 km² sin quebrada cartografiada (IGM/OSM) que cruza la vía secundaria y la trama de calles del sector; sin depresión en el DSM."}}
# punto TdB en la lista de candidatos más cercano
tdb["candidatos_a_500m"] = [p_["props"]["id"] + " " + p_["tipo"] for p_ in puntos if Point(TR * ((p_["i"] % W) + .5, (p_["i"] // W) + .5)).distance(ptb) < 500]

# ---------------------------------------------------------------- salidas
fp, fc_, fv = [], [], []
for p_ in puntos:
    pr = p_["props"]
    fp.append({"type": "Feature", "properties": {k_: v for k_, v in pr.items()}, "geometry": r6(Point(TR * ((p_["i"] % W) + .5, (p_["i"] // W) + .5)))})
    if pr["prioridad"] != "Baja" or p_["tipo"] == "VASO":
        m = np.zeros(N, bool); m[p_["cmask"]] = True; m = m.reshape(H, W)
        rs, cs_ = np.where(m); sl = (slice(rs.min(), rs.max() + 1), slice(cs_.min(), cs_.max() + 1))
        trs = TR * rasterio.Affine.translation(cs_.min(), rs.min())
        gq = unary_union([shape(s_) for s_, _ in shapes(m[sl].astype("uint8"), mask=m[sl], transform=trs)]).simplify(10)
        fc_.append({"type": "Feature", "properties": {"id": pr["id"], "tipo": p_["tipo"], "area_km2": pr["area_km2"], "prioridad": pr["prioridad"]}, "geometry": r6(gq)})
    hidros[pr["id"] + "_temez"] = p_["q"][0]
for p_ in puntos:
    if p_["tipo"] == "VASO":
        pr = p_["props"]
        fv.append({"type": "Feature", "properties": {k_: pr[k_] for k_ in ("id", "cota_fondo_m", "cota_rebose_m", "prof_max_m", "area_vaso_ha", "vol_vaso_m3",
                                                                           "edificios", "poblacion", "se_llena_30oct", "prioridad", "localidad", "sector")},
                   "geometry": r6(p_["geom_expo"])})
if ich is not None: fp.append(fp_tdb)
fcol = lambda fs: {"type": "FeatureCollection", "features": fs}
(OUT / "puntos_inundacion.geojson").write_text(json.dumps(fcol(fp), ensure_ascii=False, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)))
(OUT / "vasos.geojson").write_text(json.dumps(fcol(fv), ensure_ascii=False, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)))
(OUT / "cuencas_puntos.geojson").write_text(json.dumps(fcol(fc_), ensure_ascii=False))
with open(OUT / "hidrogramas_puntos_30oct.csv", "w", newline="") as fh:
    w_ = csv.writer(fh); keys = [k_ for k_ in hidros if k_.startswith("Tomas") or int(k_[3:6]) <= 30]
    w_.writerow(["fecha_hora_utc6"] + keys)
    for i_, x_ in enumerate(tm): w_.writerow([hora(x_)] + [round(float(hidros[k_][i_]), 2) for k_ in keys])
res = {"metodo": __doc__.split("\n\n")[1], "criterios_prioridad": CRIT,
       "parametros": {"A_llegada_min_km2": A_LLEGADA_MIN_KM2, "vaso_prof_min_m": VASO_PROF_MIN_M, "vaso_area_min_ha": VASO_AREA_MIN_HA,
                      "pie": [PIE_PEND_MAX, PIE_PEND_LADERA, PIE_A_MIN_KM2], "CN": CN,
                      "lluvia_30oct": "IERSE-WSN; mezcla Los Guayabillos–Santa Rosa según la cota media de cada cuenca (178–416 m); totales mínimos"},
       "conteos": {t_: {pr_: sum(1 for p_ in puntos if p_["tipo"] == t_ and p_["props"]["prioridad"] == pr_) for pr_ in ("Alta", "Media", "Baja")} for t_ in ("VASO", "LLEGADA", "PIE")},
       "top": [{k_: p_["props"][k_] for k_ in ("id", "tipo", "localidad", "sector", "lon", "lat", "area_km2", "edificios", "poblacion", "q30_temez_m3s",
                                               "q30_kirpich_m3s", "q100_temez_m3s", "puntaje", "prioridad", "evidencia")} for p_ in puntos[:30]],
       "tomas_de_berlanga": tdb,
       "salidas_d8": {"acumulacion": str((OUT / "acumulacion_d8.tif").relative_to(ROOT)), "direcciones": str((OUT / "direcciones_d8.tif").relative_to(ROOT))}}
(OUT / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)))
print("puntos:", len(puntos), res["conteos"])
for p_ in puntos[:25]:
    pr = p_["props"]; print(pr["id"], pr["tipo"], pr["localidad"], pr["sector"], pr["lon"], pr["lat"], pr["area_km2"], pr["edificios"], pr["poblacion"], pr["q30_temez_m3s"], pr["q30_kirpich_m3s"], pr["q100_temez_m3s"], pr["puntaje"], pr["prioridad"], pr["evidencia"], pr.get("vol_vaso_m3"), pr.get("prof_max_m"), pr.get("cota_rebose_m"), pr.get("se_llena_30oct"), pr["recibe_desborde_la_cascada"], pr.get("dentro_de_vaso"), pr.get("area_directa_km2"))
print("TdB:", json.dumps({k_: v for k_, v in tdb.items() if k_ != "perfil_cauce"}, ensure_ascii=False, default=float))
print("perfil TdB:", [(x["dist_m"], x["cota_m"], x["area_km2"], x["en_zona_poblada"]) for x in tdb.get("perfil_cauce", [])])
