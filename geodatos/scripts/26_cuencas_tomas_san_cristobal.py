"""Cuencas de captación de las tomas de agua de San Cristóbal (preliminar).

Para cada punto con categoria = "toma" de estudios/san-cristobal/datos/agua/tomas.geojson (lo mantiene el especialista urbano):
  1. Ajuste («snap») al cauce D8 de mayor área dentro de SNAP_M (60 m), sobre el DSM GLO-30 con las quebradas IGM quemadas
     (UTM 16S, 30 m; mismo D8 que el script 17). Se documenta el desplazamiento y el área antes y después.
  2. Cuenca D8 aguas arriba: área, cotas, pendiente, cauce principal (L, S) y tc (Kirpich y Témez).
  3. Uso del suelo: Parque Nacional, zona agrícola, zona poblada (zonificación PNG 2017, zonas pobladas, manzanas INEC) y
     edificios (OSM + Open Buildings).
  4. Caudal de crecida (SCS-CN + hidrograma unitario SCS; CN por clase como en el script 17, AMC II y III) con
     (a) 100 mm en 24 h, tipo II, y (b) la tormenta medida en Los Guayabillos el 30-oct trasladada (mismo hietograma que el
     modelo 2D, script 25).
  5. Fuentes potenciales de contaminación y de sedimento aguas arriba: edificios, superficie agrícola y poblada, longitud
     de vías (OSM e IGM) y cruces vía–cauce (cauces D8 ≥ 0,05 km², cruces OSM/IGM agrupados a 40 m).
  6. Índice EXPLÍCITO de riesgo de turbidez / arrastre (ver INDICE_TURBIDEZ).
  7. Sensibilidad de la cota: la USFQ da 164 m (Cerro Gato) y 150 m (La Toma); el DSM da ≈267 y ≈500 m. Se busca dónde
     alcanza esa cota el flujo D8 aguas abajo del punto y qué cuenca tendría la toma allí.

Uso:  .venv/bin/python -I scripts/26_cuencas_tomas_san_cristobal.py     (desde geodatos/)
Salidas: estudios/san-cristobal/datos/agua/cuencas_tomas.geojson y cuencas_tomas.json
"""
import csv, json, math, pathlib, tempfile, datetime as dt_
import numpy as np, rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling, calculate_default_transform
from shapely.geometry import shape, mapping, Point, LineString, MultiPoint
from shapely.ops import unary_union, transform as stransform
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
AGUA = ROOT / "estudios/san-cristobal/datos/agua"
TOMAS = AGUA / "tomas.geojson"
DEM_CRUDO = ROOT / "descargas/dem_recortes/san_cristobal_dem.tif"
DEM_QUEMADO = ROOT / "descargas/dem_recortes/san_cristobal_dem_quemado.tif"
HIETO = ROOT / "estudios/santa-cruz/datos/lluvias/hietograma_5min.csv"
ISLA = "San Cristóbal"; EPSG = 32716; CELDA = 30.0
SNAP_M = 60
RADIO_CANADA_M = 300        # búsqueda de la cañada (cauce D8 ≥ A_CANADA_KM2) más cercana, como alternativa
A_CANADA_KM2 = 0.1
A_CAUCE_KM2 = 0.05
COTA_USFQ = {"AG-01": 164, "AG-03": 150}
CN_CLASE = {"parque": 60, "agricola": 76, "poblado": 90}
INDICE_TURBIDEZ = {
    "P_pendiente": "pendiente media de la cuenca: 0 (< 10 %), 1 (10–20 %), 2 (≥ 20 %)",
    "U_uso": "fracción agrícola + poblada: 0 (< 10 %), 1 (10–40 %), 2 (≥ 40 %)",
    "V_vias": "vías dentro de la cuenca: 0 (ninguna), 1 (< 1 km), 2 (≥ 1 km o algún cruce vía–cauce)",
    "Q_crecida": "caudal pico con 100 mm (CN AMC II, tc de Kirpich): 0 (< 1 m³/s), 1 (1–5), 2 (≥ 5)",
    "clase": "suma 0–8: baja (0–2), media (3–4), alta (≥ 5)",
}
T = Transformer.from_crs(4326, EPSG, always_xy=True).transform
TI = Transformer.from_crs(EPSG, 4326, always_xy=True).transform
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)


def feats(rel, cond=lambda p: True):
    out = []
    for f in json.loads((ROOT / rel).read_text())["features"]:
        if f.get("geometry") and f["properties"].get("isla", ISLA) == ISLA and cond(f["properties"]):
            g = shape(f["geometry"]); g = g.buffer(0) if g.geom_type.endswith("Polygon") else g
            out.append((stransform(T, g), f["properties"]))
    return out


def a_utm(p):
    src = rasterio.open(p)
    tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG}", src.width, src.height, *src.bounds, resolution=CELDA)
    arr = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), arr, src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs=f"EPSG:{EPSG}",
              resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    return arr, tr


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


# ---------------------------------------------------------------- hidrología (como en los scripts 12 y 17)
TII_H = [0, 2, 4, 6, 7, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 11.75, 12, 12.5, 13, 13.5, 14, 16, 20, 24]
TII_F = [0, .022, .048, .080, .098, .120, .133, .147, .163, .181, .204, .235, .283, .357, .663, .735, .772, .799, .820, .880, .952, 1.0]
UH_T = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5]
UH_Q = [0, .03, .1, .19, .31, .47, .66, .82, .93, .99, 1, .99, .93, .86, .78, .68, .56, .46, .39, .33, .28, .207, .147, .107, .077, .055, .04, .029, .021, .015, .011, .005, 0]


def guayabillos():
    filas = [r for r in csv.DictReader(open(HIETO, encoding="utf-8")) if r.get("estacion") == "Los Guayabillos" and r["fecha_hora_local"].startswith("2026-10-30")]
    t0 = dt_.datetime(2026, 10, 30)
    ts = np.array([0.0] + [(dt_.datetime.fromisoformat(r["fecha_hora_local"]) - t0).total_seconds() / 3600 for r in filas])
    pc = np.concatenate([[0.0], np.cumsum([float(r["lluvia_mm"] or 0) for r in filas])])
    return lambda t: np.interp(t, ts, pc)


FG = guayabillos() if HIETO.exists() else None


def hidrograma(area_km2, cn, tc_h, P=None, fun=None, dur_h=30):
    dt = min(1 / 6, max(tc_h / 6, 1 / 60))
    t = np.arange(0, dur_h + 1e-9, dt)
    Pc = P * np.interp(t, TII_H, TII_F) if fun is None else fun(t)
    S = 25400 / cn - 254; Ia = 0.2 * S
    Q = np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0)
    exc = np.diff(Q, prepend=0)
    tp = dt / 2 + 0.6 * tc_h
    tt = np.arange(0, 5 * tp + dt, dt)
    u = np.interp(tt / tp, UH_T, UH_Q); u = u / (u.sum() * dt * 3600) * area_km2 * 1e6 / 1000
    return float(np.convolve(exc, u)[: len(t)].max()), float(Q[-1])


# ---------------------------------------------------------------- D8
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
pend = np.hypot(*np.gradient(np.where(sea, np.nan, dem), CELDA)) * 100
rr, cc = np.indices((H, W))
nr, nc = rr.copy(), cc.copy()
for k, (a, b) in OFF.items():
    m = F == k; nr[m] += a; nc[m] += b
ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W) & np.isin(F, list(OFF)) & ~sea
NXT = (np.where(ok, nr, rr) * W + np.where(ok, nc, cc)).ravel()
NN = H * W


def aguas_arriba(r, c):
    mask = np.zeros(NN, bool); mask[r * W + c] = True
    tg = np.where(mask, np.arange(NN), -1); jj = NXT.copy()
    for _ in range(int(np.ceil(np.log2(NN))) + 1):
        un = tg == -1; tg[un] = tg[jj[un]]; jj = jj[jj]
    return (tg >= 0).reshape(H, W) & ~sea


def aguas_abajo(r, c):
    path = [(r, c)]; i = r * W + c
    while NXT[i] != i and len(path) < 20000:
        i = NXT[i]; path.append(divmod(i, W))
        if sea.ravel()[i]: break
    return path


def cauce(r, c):
    path = [(r, c)]
    while True:
        best, ba = None, -1
        for k, (a, b) in OFF.items():
            ur, uc = r - a, c - b
            if 0 <= ur < H and 0 <= uc < W and F[ur, uc] == k and not sea[ur, uc] and AKM[ur, uc] > ba:
                best, ba = (ur, uc), AKM[ur, uc]
        if best is None: break
        r, c = best; path.append(best)
    return path[::-1]


def longitud(path):
    return float(sum(CELDA * math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1)))


def poligono(m):
    return unary_union([shape(s) for s, _ in shapes(m.astype("uint8"), mask=m, transform=TR)])


# ---------------------------------------------------------------- capas
parque = rasterize([(g, 1) for g, _ in feats("export/galapagos/parque_nacional.geojson")], out_shape=(H, W), transform=TR).astype(bool)
agr = rasterize([(g, 1) for g, _ in feats("export/galapagos/zona_agricola.geojson")], out_shape=(H, W), transform=TR).astype(bool)
pob_g = [g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")] + [g for g, _ in feats("capas/final/manzanas_inec.geojson")]
pob = rasterize([(g, 1) for g in pob_g], out_shape=(H, W), transform=TR).astype(bool)
edif = feats("capas/final/edificios_exposicion.geojson")
vias_osm = feats("export/galapagos/vias.geojson")
vias_igm = feats("capas/igm/via.geojson")
queb_igm = feats("capas/final/quebradas.geojson")


def cauces_en(m):
    """Líneas de cauce D8 (≥ A_CAUCE_KM2) dentro de la cuenca m, como segmentos celda→celda."""
    segs = []
    rs, cs = np.where(m & (AKM >= A_CAUCE_KM2))
    for r, c in zip(rs, cs):
        j = NXT[r * W + c]
        if j == r * W + c: continue
        r2, c2 = divmod(j, W)
        segs.append(LineString([TR * (c + .5, r + .5), TR * (c2 + .5, r2 + .5)]))
    return unary_union(segs) if segs else None


def analizar(r, c, geom_pt):
    up = aguas_arriba(r, c)
    up[r, c] = True
    a = float(up.sum() * CELDA ** 2 / 1e6)
    pol = poligono(up)
    f_pob = float((up & pob).sum() / up.sum()); f_agr = float((up & agr & ~pob).sum() / up.sum())
    f_par = float((up & parque & ~agr & ~pob).sum() / up.sum()); f_otro = 1 - f_pob - f_agr - f_par
    cn = (f_par + f_otro) * CN_CLASE["parque"] + f_agr * CN_CLASE["agricola"] + f_pob * CN_CLASE["poblado"]
    cn3 = 23 * cn / (10 + 0.13 * cn)
    st = cauce(r, c); L = max(longitud(st), CELDA); Hh = float(dem[st[0]] - dem[r, c]); S = max(Hh / L, 1e-3)
    tk = 0.0195 * L ** 0.77 * S ** -0.385 / 60; tt = 0.3 * ((L / 1000) / S ** 0.25) ** 0.76
    q = {}
    for nm, kw in (("100mm_tipoII", dict(P=100.0)), ("guayabillos_30oct_trasladada", dict(fun=FG))):
        if kw.get("fun", 1) is None: continue
        for amc, cnx in (("AMC_II", cn), ("AMC_III", cn3)):
            q1, Qmm = hidrograma(a, cnx, max(tt, 1 / 60), **kw); q2, _ = hidrograma(a, cnx, max(tk, 1 / 60), **kw)
            q[f"{nm}_{amc}"] = {"CN": round(cnx, 1), "escorrentia_mm": round(Qmm, 1), "q_pico_m3s_temez": round(q1, 2), "q_pico_m3s_kirpich": round(q2, 2)}
    ne = sum(1 for gb, _ in edif if pol.contains(gb.centroid))
    lv_osm = sum(gv.intersection(pol).length for gv, _ in vias_osm if gv.intersects(pol)) / 1000
    lv_igm = sum(gv.intersection(pol).length for gv, _ in vias_igm if gv.intersects(pol)) / 1000
    red = cauces_en(up)
    cruces = []
    if red is not None:
        for gv, pv in vias_osm + vias_igm:
            if not gv.intersects(pol): continue
            x = gv.intersection(red)
            for pt in getattr(x, "geoms", [x]):
                if pt.is_empty: continue
                pt = pt if pt.geom_type == "Point" else pt.centroid
                if all(pt.distance(q_) > 40 for q_, _ in cruces):
                    cruces.append((pt, pv.get("nombre") or pv.get("tipo_osm") or pv.get("descripcio") or "vía"))
    l_queb_igm = sum(gq.intersection(pol).length for gq, pq in queb_igm if gq.intersects(pol) and str(pq.get("fuente", "")).startswith("IGM")) / 1000
    dens = (lv_osm + lv_igm) / a if a > 0 else 0
    q100a = q["100mm_tipoII_AMC_II"]["q_pico_m3s_kirpich"]; q100 = q100a / a if a > 0 else 0
    pm = float(np.nanmean(pend[up]))
    lv = lv_osm + lv_igm
    ind = {"P": 0 if pm < 10 else (1 if pm < 20 else 2), "U": 0 if f_agr + f_pob < 0.1 else (1 if f_agr + f_pob < 0.4 else 2),
           "V": 0 if lv == 0 and not cruces else (2 if lv >= 1 or cruces else 1), "Q": 0 if q100a < 1 else (1 if q100a < 5 else 2)}
    tot = sum(ind.values())
    return pol, {
        "area_km2": round(a, 3), "cota_max_m": round(float(dem[up].max()), 1), "cota_media_m": round(float(dem[up].mean()), 1),
        "cota_toma_dsm_m": round(float(dem[r, c]), 1), "pendiente_media_pct": round(pm, 1),
        "cauce_L_km": round(L / 1000, 2), "cauce_S_pct": round(S * 100, 1), "tc_kirpich_min": round(tk * 60), "tc_temez_min": round(tt * 60),
        "uso_parque_pct": round(100 * f_par, 1), "uso_agricola_pct": round(100 * f_agr, 1), "uso_poblado_pct": round(100 * f_pob, 1),
        "uso_otro_pct": round(100 * f_otro, 1), "cn_amc_ii": round(cn, 1), "edificios": ne,
        "vias_osm_km": round(lv_osm, 2), "vias_igm_km": round(lv_igm, 2), "densidad_vias_km_km2": round(dens, 2),
        "cruces_via_cauce": len(cruces), "cruces_lonlat": [[round(v, 5) for v in TI(*p_.coords[0])] + [n_] for p_, n_ in cruces],
        "quebradas_igm_km": round(l_queb_igm, 2), "caudales": q, "q_especifico_100mm_m3s_km2": round(q100, 2),
        "indice_turbidez": ind, "indice_turbidez_total": tot, "riesgo_turbidez": "baja" if tot <= 2 else ("media" if tot <= 4 else "alta")}, up


# ---------------------------------------------------------------- tomas
tomas = [(stransform(T, shape(f["geometry"])), f["properties"]) for f in json.loads(TOMAS.read_text())["features"] if f["properties"].get("categoria") == "toma"]
out_f, R = [], {"metodo": __doc__.split("Uso:")[0].strip(), "indice_turbidez": INDICE_TURBIDEZ, "tomas": {}}
rad = int(SNAP_M / CELDA)
for gp, pp in tomas:
    c0, r0 = ~TR * gp.coords[0]; r0, c0 = int(r0), int(c0)
    best = (AKM[r0, c0], r0, c0)
    for r in range(r0 - rad, r0 + rad + 1):
        for c in range(c0 - rad, c0 + rad + 1):
            if Point(TR * (c + .5, r + .5)).distance(gp) <= SNAP_M and AKM[r, c] > best[0]:
                best = (AKM[r, c], r, c)
    a_ini = float(AKM[r0, c0]); _, rs, cs = best
    pt_s = Point(TR * (cs + .5, rs + .5))
    pol, props, up = analizar(rs, cs, pt_s)
    props.update({"id": pp["id"], "nombre": pp["nombre"], "confianza_ubicacion": pp.get("confianza"), "caudal_captado_ls": pp.get("caudal_ls"),
                  "snap_desplazamiento_m": round(pt_s.distance(gp)), "area_en_punto_original_km2": round(a_ini, 3),
                  "punto_ajustado_lonlat": [round(v, 5) for v in TI(*pt_s.coords[0])],
                  "sin_cauce_definido": bool(AKM[rs, cs] < A_CAUCE_KM2)})
    # sensibilidad: cota de la USFQ
    if pp["id"] in COTA_USFQ:
        z_u = COTA_USFQ[pp["id"]]
        ab = aguas_abajo(rs, cs)
        k = next((i for i, q_ in enumerate(ab) if dem[q_] <= z_u), None)
        if k is not None:
            rk, ck = ab[k]
            dist = longitud(ab[:k + 1])
            _, alt, _ = analizar(rk, ck, Point(TR * (ck + .5, rk + .5)))
            props["sensibilidad_cota_usfq"] = {"cota_usfq_m": z_u, "punto_d8_a_esa_cota_lonlat": [round(v, 5) for v in TI(*(TR * (ck + .5, rk + .5)))],
                                              "distancia_aguas_abajo_km": round(dist / 1000, 2), "area_alli_km2": alt["area_km2"],
                                              "uso_agricola_pct": alt["uso_agricola_pct"], "uso_poblado_pct": alt["uso_poblado_pct"], "edificios": alt["edificios"],
                                              "q100_amc_ii_m3s": [alt["caudales"]["100mm_tipoII_AMC_II"]["q_pico_m3s_temez"], alt["caudales"]["100mm_tipoII_AMC_II"]["q_pico_m3s_kirpich"]]}
    # alternativa: cañada (cauce D8 ≥ A_CANADA_KM2) más cercana dentro de RADIO_CANADA_M
    radc = int(RADIO_CANADA_M / CELDA); cand = []
    for r in range(r0 - radc, r0 + radc + 1):
        for c in range(c0 - radc, c0 + radc + 1):
            if 0 <= r < H and 0 <= c < W and AKM[r, c] >= A_CANADA_KM2:
                d_ = Point(TR * (c + .5, r + .5)).distance(gp)
                if d_ <= RADIO_CANADA_M: cand.append((round(d_ / CELDA), -AKM[r, c], r, c, d_))
    if cand and props["area_km2"] < A_CANADA_KM2:
        _, _, rc_, cc_, d_ = min(cand)
        polc, alt, _ = analizar(rc_, cc_, None)
        props["canada_mas_cercana"] = {"distancia_m": round(d_), "lonlat": [round(v, 5) for v in TI(*(TR * (cc_ + .5, rc_ + .5)))],
                                       **{k_: alt[k_] for k_ in ("area_km2", "cota_toma_dsm_m", "cota_max_m", "pendiente_media_pct", "uso_parque_pct", "uso_agricola_pct",
                                                                 "uso_poblado_pct", "edificios", "vias_osm_km", "vias_igm_km", "cruces_via_cauce", "cruces_lonlat",
                                                                 "tc_kirpich_min", "tc_temez_min", "cauce_L_km", "cauce_S_pct", "riesgo_turbidez", "indice_turbidez")},
                                       "q100_amc_ii_m3s": [alt["caudales"]["100mm_tipoII_AMC_II"]["q_pico_m3s_temez"], alt["caudales"]["100mm_tipoII_AMC_II"]["q_pico_m3s_kirpich"]],
                                       "q100_amc_iii_m3s": [alt["caudales"]["100mm_tipoII_AMC_III"]["q_pico_m3s_temez"], alt["caudales"]["100mm_tipoII_AMC_III"]["q_pico_m3s_kirpich"]],
                                       "q_guayabillos_amc_ii_m3s": [alt["caudales"]["guayabillos_30oct_trasladada_AMC_II"]["q_pico_m3s_temez"], alt["caudales"]["guayabillos_30oct_trasladada_AMC_II"]["q_pico_m3s_kirpich"]]}
        out_f.append({"type": "Feature", "properties": {"id": pp["id"], "nombre": pp["nombre"], "elemento": f"cuenca de la cañada más cercana (alternativa, a {round(d_)} m)",
                                                        **{k_: v_ for k_, v_ in props["canada_mas_cercana"].items() if k_ not in ("cruces_lonlat", "indice_turbidez")}},
                      "geometry": r6(polc)})
    R["tomas"][pp["id"]] = props
    out_f.append({"type": "Feature", "properties": {**{k_: v_ for k_, v_ in props.items() if k_ not in ("caudales", "cruces_lonlat", "indice_turbidez", "sensibilidad_cota_usfq")},
                                                    "elemento": "cuenca de captación",
                                                    "q100_amc_ii_m3s": [props["caudales"]["100mm_tipoII_AMC_II"]["q_pico_m3s_temez"], props["caudales"]["100mm_tipoII_AMC_II"]["q_pico_m3s_kirpich"]],
                                                    "q_guayabillos_amc_ii_m3s": [props["caudales"]["guayabillos_30oct_trasladada_AMC_II"]["q_pico_m3s_temez"],
                                                                                 props["caudales"]["guayabillos_30oct_trasladada_AMC_II"]["q_pico_m3s_kirpich"]] if FG else None},
                  "geometry": r6(pol)})
    out_f.append({"type": "Feature", "properties": {"id": pp["id"], "nombre": pp["nombre"], "elemento": "toma ajustada al cauce D8",
                                                    "snap_desplazamiento_m": props["snap_desplazamiento_m"]}, "geometry": r6(pt_s)})
    for p_, n_ in [(Point(T(*x[:2])), x[2]) for x in props["cruces_lonlat"]]:
        out_f.append({"type": "Feature", "properties": {"id": pp["id"], "elemento": "cruce vía–cauce aguas arriba", "via": n_}, "geometry": r6(p_)})
    print(pp["id"], pp["nombre"], {k_: props[k_] for k_ in ("snap_desplazamiento_m", "area_en_punto_original_km2", "area_km2", "cota_toma_dsm_m", "cota_max_m", "pendiente_media_pct",
                                                            "uso_parque_pct", "uso_agricola_pct", "uso_poblado_pct", "edificios", "vias_osm_km", "vias_igm_km", "cruces_via_cauce",
                                                            "riesgo_turbidez", "indice_turbidez")},
          {k_: (v_["q_pico_m3s_temez"], v_["q_pico_m3s_kirpich"]) for k_, v_ in props["caudales"].items()}, props.get("sensibilidad_cota_usfq"),
          {k_: v_ for k_, v_ in props.get("canada_mas_cercana", {}).items() if k_ != "cruces_lonlat"})
# cuencas anidadas
ids = list(R["tomas"])
R["notas"] = {"anidadas": [], "cuencas_con_area_menor_a_0.1km2_tras_ajuste": [i for i in ids if R["tomas"][i]["area_km2"] < 0.1]}
(AGUA / "cuencas_tomas.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": out_f}, ensure_ascii=False))
(AGUA / "cuencas_tomas.json").write_text(json.dumps(R, ensure_ascii=False, indent=1))
print("Listo:", AGUA / "cuencas_tomas.geojson")
