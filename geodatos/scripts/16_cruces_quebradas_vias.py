"""Cruces de quebradas con vías en Santa Cruz y San Cristóbal (inventario preliminar priorizado).

Qué hace
  1. Vías: TODAS las de OSM (capas/osm/vias.geojson, extracto Geofabrik 31-oct-2026, con name, bridge, tunnel,
     layer, surface) más la red vial IGM 1:25 000 (capas/igm/via.geojson). Estructuras: puentes OSM
     (bridge=*), alcantarillas OSM en la vía (tunnel=culvert) o en el cauce (capas/osm/hidro_lineas.geojson con
     tunnel=culvert) y puentes IGM (capas/igm/puente_p, puente_l). Los nodos sueltos man_made=culvert o ford no
     están en el extracto y no se consideran.
  2. Cauces: quebradas IGM 1:25 000 + OSM (capas/final/quebradas.geojson) y cauces D8 derivados del DSM con
     área drenada ≥ 0,1 km² (capas/final/drenaje_derivado.geojson, generados por 03_dem.py).
  3. Calcula todas las intersecciones vía × cauce y las deduplica: los cruces a menos de DEDUP_M metros se
     agrupan en uno solo (unión-búsqueda). Del grupo se conserva la vía OSM (tiene etiquetas) antes que la IGM y
     la quebrada con nombre / IGM / OSM antes que el cauce D8; se guardan todas las fuentes.
  4. Hidrología de orden de magnitud en cada cruce, con D8 propio (pysheds) sobre el DSM con quebradas IGM
     quemadas (descargas/dem_recortes/<isla>_dem_quemado.tif):
       - área drenada A: máximo de la acumulación en la ventana 3×3 alrededor del cruce;
       - longitud del cauce más largo aguas arriba L y cota de su cabecera → pendiente media J;
       - tiempo de concentración de Témez: tc[h] = 0,3·(L[km] / J^0,25)^0,76 (mínimo 10 min);
       - método racional modificado (Témez): Q = C·I(tc)·A·K / 3,6, con K = 1 + tc^1,25 / (tc^1,25 + 14);
       - I(tc): intensidad máxima de duración tc observada el 30-oct-2026 en Los Guayabillos (IERSE-WSN, 5 min,
         178,8 mm; ../clima/datos/ierse-wsn/serie_5min.csv.gz). Escenario de 100 mm: la misma curva escalada
         por 100/178,8 (se supone la misma estructura temporal). Escenario del 30-oct (≈180 mm): la curva sin
         escalar; solo se aplica a Santa Cruz (no hay lluvia medida en San Cristóbal);
       - C: coeficiente de escorrentía volumétrico SCS para la lámina total con CN 60 / 70 / 80
         (mínimo / central / máximo). Con 100 mm: 0,19 / 0,33 / 0,51; con 178,8 mm: 0,38 / 0,52 / 0,67.
     El método racional no es válido en rigor por encima de unos 10–25 km²: allí la cifra es solo una escala.
  5. Atributos de contexto: estructura (puente / alcantarilla / vado OSM o IGM a ≤ ESTR_M m), zona poblada
     (capas/final/zonas_pobladas.geojson, sin «farmyard»), edificios a ≤ 50 m (capas/final/edificios_exposicion),
     cota del DSM crudo (±2–4 m; sesgo ≈ −2 m frente a los puntos acotados IGM).
  6. Prioridad con criterios explícitos (ver PUNTOS más abajo) y salidas:
       estudios/santa-cruz/datos/cruces.geojson y .csv
       estudios/san-cristobal/datos/cruces.geojson y .csv

Si existe estudios/santa-cruz/datos/acumulacion_d8.tif (acumulación del asesor hidrológico), se muestrea
también y se guarda como area_km2_asesor para comparar; el cálculo usa siempre el D8 propio.

Uso:  .venv/bin/python -I scripts/16_cruces_quebradas_vias.py
"""
import csv, gzip, json, math, pathlib, datetime as dt
import numpy as np, rasterio
from shapely.geometry import shape, mapping, Point, LineString, MultiLineString
from shapely.ops import transform as stransform, unary_union
from shapely.strtree import STRtree
from pyproj import Transformer
from pysheds.grid import Grid

ROOT = pathlib.Path(__file__).resolve().parents[1]
LLUVIA = ROOT.parent / "clima/datos/ierse-wsn/serie_5min.csv.gz"
ESTACION = "n_glps05"           # Los Guayabillos
ISLAS = {
    "Santa Cruz":    dict(key="santa_cruz", est="santa-cruz", pref="SCZ", epsg=32715, bbox=(-90.56, -0.80, -90.15, -0.42)),
    "San Cristóbal": dict(key="san_cristobal", est="san-cristobal", pref="SCR", epsg=32716, bbox=(-89.66, -0.97, -89.22, -0.66)),
}
DEDUP_M = 40          # cruces a menos de esta distancia se fusionan
ESTR_M = 25           # radio de búsqueda de estructuras (puente, alcantarilla, vado)
CELL_M = 30.87        # celda de 1" en el ecuador
CELL_KM2 = (CELL_M / 1000) ** 2
CN_C = {  # coeficiente volumétrico SCS (P−Ia)²/(P−Ia+S)/P, Ia = 0,2 S, S = 25400/CN − 254
    "100": {cn: None for cn in (60, 70, 80)}, "evento": {cn: None for cn in (60, 70, 80)}}
P_EVENTO = 178.8      # mm, Los Guayabillos 30-oct-2026 (mínimo: la estación dejó de transmitir ≈21:30)

def c_scs(P, cn):
    S = 25400 / cn - 254; Ia = 0.2 * S
    return 0.0 if P <= Ia else (P - Ia) ** 2 / (P - Ia + S) / P
for cn in (60, 70, 80):
    CN_C["100"][cn] = c_scs(100, cn); CN_C["evento"][cn] = c_scs(P_EVENTO, cn)

# ---------------------------------------------------------------- lluvia: curva intensidad–duración observada
def curva_id():
    t0 = dt.datetime(2026, 10, 30, 0, 0); n = 2 * 288
    v = np.zeros(n)
    with gzip.open(LLUVIA, "rt") as f:
        for r in csv.DictReader(f):
            if r["estacion_id"] != ESTACION or not r["lluvia_mm"]: continue
            t = dt.datetime.fromisoformat(r["fecha_hora_local"])
            k = int((t - t0).total_seconds() // 300)
            if 0 <= k < n: v[k] += float(r["lluvia_mm"])
    tot = v[:288].sum()
    cs = np.concatenate([[0], np.cumsum(v)])
    P = {d: float(max(cs[d:] - cs[:-d])) for d in range(1, n)}   # d en pasos de 5 min
    return P, tot

P_D, TOT30 = curva_id()

def intensidad(tc_h, escala):
    d = tc_h * 12.0
    d0 = max(1, int(math.floor(d))); d1 = d0 + 1
    p = P_D[d0] + (P_D[min(d1, len(P_D))] - P_D[d0]) * (d - d0) if d > 1 else P_D[1] * d
    return escala * p / tc_h

# ---------------------------------------------------------------- D8 propio + longitud de flujo
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
def hidro(key):
    fq = ROOT / f"descargas/dem_recortes/{key}_dem_quemado.tif"
    grid = Grid.from_raster(str(fq)); d = grid.read_raster(str(fq))
    fl = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(d)))
    fdir = grid.flowdir(fl); acc = grid.accumulation(fdir)
    F = np.asarray(fdir); A = np.asarray(acc).astype(float)
    with rasterio.open(ROOT / f"descargas/dem_recortes/{key}_dem.tif") as src:
        Z = src.read(1).astype(float); tr = src.transform
    H_, W_ = Z.shape
    land = Z > -9000
    down = -np.ones(H_ * W_, dtype=np.int64); step = np.zeros(H_ * W_)
    rr, cc = np.indices((H_, W_))
    for k, (a, b) in OFF.items():
        m = (F == k) & land
        r2, c2 = rr[m] + a, cc[m] + b
        ok = (r2 >= 0) & (r2 < H_) & (c2 >= 0) & (c2 < W_)
        idx = (rr[m] * W_ + cc[m])[ok]
        down[idx] = (r2 * W_ + c2)[ok]
        step[idx] = CELL_M * (math.sqrt(2) if a and b else 1)
    Af = A.ravel(); Zf = np.where(land, Z, np.nan).ravel()
    order = np.argsort(Af, kind="stable")
    order = order[land.ravel()[order]]
    L = [0.0] * (H_ * W_); Zs = Zf.tolist(); dn = down.tolist(); st = step.tolist()
    for i in order.tolist():
        j = dn[i]
        if j < 0: continue
        c = L[i] + st[i]
        if c > L[j]: L[j] = c; Zs[j] = Zs[i]
    return dict(A=A, Z=Z, L=np.array(L).reshape(H_, W_), Zs=np.array(Zs).reshape(H_, W_), tr=tr, land=land, down=down)

def muestra(hd, lon, lat):
    c, r = ~hd["tr"] * (lon, lat); r, c = int(r), int(c)
    H_, W_ = hd["A"].shape
    best = None
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < H_ and 0 <= c2 < W_ and hd["land"][r2, c2]:
                if best is None or hd["A"][r2, c2] > hd["A"][best]: best = (r2, c2)
    if best is None: return None
    A = hd["A"][best] * CELL_KM2; L = hd["L"][best]; zs = hd["Zs"][best]; z0 = hd["Z"][best]
    zc = float(hd["Z"][r, c]) if hd["land"][r, c] else float(z0)
    J = max((zs - z0) / L, 0.005) if L > 0 else 0.05
    return dict(A=A, L=L, J=J, zc=zc)

def caudales(A, L, J, con_evento):
    tc = max(0.3 * ((L / 1000) / J ** 0.25) ** 0.76, 10 / 60)
    K = 1 + tc ** 1.25 / (tc ** 1.25 + 14)
    out = dict(tc_min=round(tc * 60))
    for esc, nom, P in [("100", "q100", 100.0)] + ([("evento", "q30oct", P_EVENTO)] if con_evento else []):
        I = intensidad(tc, P / TOT30)
        for cn, suf in ((60, "_min"), (70, ""), (80, "_max")):
            out[nom + suf] = round(CN_C[esc][cn] * I * A * K / 3.6, 1)
        out["i_" + nom + "_mmh"] = round(I, 1)
    return out

# ---------------------------------------------------------------- clasificación y prioridad
def tipo_via(hw, nombre, isla, poblada, fuente, desc=None):
    if fuente == "IGM":
        if desc and "PAVIMENTADA" in desc: hw = "tertiary"
        elif desc == "CALLE": hw = "residential"
        elif desc and "PEATONAL" in desc.upper(): hw = "footway"
        else: hw = "track"
    if hw in ("footway", "path", "steps", "cycleway", "bridleway", "pedestrian", "corridor"): return "peatonal", hw
    if hw in ("motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"):
        if isla == "Santa Cruz": return "carretera Puerto Ayora–Baltra" + (" (tramo urbano)" if poblada else ""), hw
        return "principal " + ("urbana" if poblada else "rural"), hw
    if hw in ("secondary", "secondary_link", "tertiary", "tertiary_link"):
        return ("principal urbana" if poblada else "principal rural"), hw
    if poblada: return "urbana", hw
    return "rural", hw

PUNTOS = """Puntaje (0–11):
  área drenada   ≥ 5 km² → 2 · 0,5–5 km² → 1 · < 0,5 km² → 0
  caudal Q100 central (CN 70)  ≥ 50 m³/s → 3 · 10–50 → 2 · 2–10 → 1 · < 2 → 0
  tipo de vía    carretera Puerto Ayora–Baltra → 3 · principal (secondary/tertiary; IGM pavimentada) → 2 ·
                 urbana → 2 · rural → 1 · peatonal → 0
  estructura     ninguna cartografiada → 1 · puente, alcantarilla o vado → 0
  zona poblada   dentro → 2 · fuera → 0
  Prioridad: alta ≥ 7 · media 4–6 · baja ≤ 3"""
def puntaje(r):
    p = (2 if r["area_km2"] >= 5 else 1 if r["area_km2"] >= 0.5 else 0)
    q = r["q100"]; p += 3 if q >= 50 else 2 if q >= 10 else 1 if q >= 2 else 0
    t = r["via_tipo"]; p += 3 if "carretera" in t else 2 if (t == "urbana" or t.startswith("principal")) else 1 if t == "rural" else 0
    p += 1 if r["estructura"] == "ninguna cartografiada" else 0
    p += 2 if r["zona_poblada"] else 0
    return p, ("alta" if p >= 7 else "media" if p >= 4 else "baja")

# ---------------------------------------------------------------- principal
def cargar(rel, isla, cond=lambda p: True):
    return [(shape(f["geometry"]), f["properties"]) for f in json.loads((ROOT / rel).read_text())["features"]
            if f.get("geometry") and f["properties"].get("isla") == isla and cond(f["properties"])]

def main():
    print("curva I-D Los Guayabillos: total 30-oct %.1f mm; P(1 h) %.1f; P(3 h) %.1f" % (TOT30, P_D[12], P_D[36]))
    for isla, cfg in ISLAS.items():
        T = Transformer.from_crs(4326, cfg["epsg"], always_xy=True).transform
        TI = Transformer.from_crs(cfg["epsg"], 4326, always_xy=True).transform
        print("==", isla); hd = hidro(cfg["key"])
        ases = None
        fa = ROOT / f"estudios/{cfg['est']}/datos/acumulacion_d8.tif"
        if fa.exists():
            ases = rasterio.open(fa); print("  acumulación del asesor encontrada:", fa)
        # cauces
        cauces = []
        for g, p in cargar("capas/final/quebradas.geojson", isla):
            cauces.append((g, dict(nombre=p.get("nombre"), fuente=p.get("fuente"), rank=0 if p.get("nombre") else 1 if "IGM" in p.get("fuente", "") else 2)))
        for g, p in cargar("capas/final/drenaje_derivado.geojson", isla):
            cauces.append((g, dict(nombre=None, fuente="D8 GLO-30 (≥0,1 km²)", rank=3)))
        tq = STRtree([g for g, _ in cauces])
        # vías
        vias = []
        for g, t in cargar("capas/osm/vias.geojson", isla):
            for gg in getattr(g, "geoms", [g]): vias.append((gg, t, "OSM", t.get("osm_id")))
        for g, p in cargar("capas/igm/via.geojson", isla):
            for gg in getattr(g, "geoms", [g]):
                vias.append((gg, {"highway": None, "_desc": p.get("descripcio")}, "IGM", None))
        pob = unary_union([g for g, p in cargar("capas/final/zonas_pobladas.geojson", isla, lambda p: p.get("tipo") != "OSM farmyard")])
        # nombre del lugar: barrio CGREG (solo Santa Cruz) > zona poblada con nombre > localidad OSM más cercana (≤ 3 km)
        barrios = [(g, p.get("nombre")) for g, p in cargar("capas/final/barrios.geojson", isla)]
        pobs = [(g, p.get("nombre")) for g, p in cargar("capas/final/zonas_pobladas.geojson", isla, lambda p: p.get("tipo") != "OSM farmyard") if p.get("nombre")]
        lugares = [(g, p.get("name")) for g, p in cargar("capas/osm/lugares.geojson", isla, lambda p: p.get("place") in ("town", "village", "hamlet", "neighbourhood"))]
        def lugar(pt):
            b = next((n for g, n in barrios if g.contains(pt)), None)
            z = next((n for g, n in pobs if g.contains(pt)), None)
            near = min(lugares, key=lambda gn: gn[0].distance(pt)) if lugares else None
            ln = near[1] if near and near[0].distance(pt) * 111000 <= 3000 else None
            partes = [x for x in (z or ln, ("barrio " + b.title()) if b else None) if x]
            return " · ".join(partes)
        edif = [stransform(T, g.centroid) for g, p in cargar("capas/final/edificios_exposicion.geojson", isla)]
        te = STRtree(edif)
        # estructuras
        estr = []
        for g, t in cargar("capas/osm/hidro_lineas.geojson", isla, lambda p: p.get("tunnel") == "culvert"):
            estr.append((stransform(T, g), "alcantarilla (OSM, cauce %s)" % t.get("osm_id")))
        for n in ("puente_p", "puente_l"):
            for g, p in cargar(f"capas/igm/{n}.geojson", isla):
                estr.append((stransform(T, g), "puente IGM (%s)" % (p.get("tuc_desc") or "").lower()))
        ts = STRtree([g for g, _ in estr]) if estr else None
        # intersecciones
        cand = []
        for gv, t, fv, oid in vias:
            for k in tq.query(gv, predicate="intersects"):
                gq, pq = cauces[k]
                x = gv.intersection(gq)
                pts = [x] if x.geom_type == "Point" else [p for p in getattr(x, "geoms", []) if p.geom_type == "Point"]
                for pt in pts:
                    cand.append(dict(pt=pt, xy=stransform(T, pt), via=t, fv=fv, oid=oid, q=pq))
        print("  intersecciones brutas", len(cand))
        # deduplicación por unión-búsqueda
        tc_ = STRtree([c["xy"] for c in cand]); par = list(range(len(cand)))
        def f_(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        for i, c in enumerate(cand):
            for j in tc_.query(c["xy"].buffer(DEDUP_M)):
                if j != i: par[f_(i)] = f_(j)
        grupos = {}
        for i in range(len(cand)): grupos.setdefault(f_(i), []).append(cand[i])
        print("  cruces tras deduplicar", len(grupos))
        filas = []
        for gid, gs in grupos.items():
            # representante
            RANGO = {"motorway": 0, "trunk": 0, "primary": 0, "secondary": 1, "tertiary": 1, "unclassified": 2, "residential": 2,
                     "living_street": 2, "service": 3, "track": 4, "pedestrian": 5, "footway": 5, "path": 5, "steps": 5, "cycleway": 5}
            gs_v = sorted(gs, key=lambda c: (c["fv"] != "OSM", RANGO.get(c["via"].get("highway"), 4), c["q"]["rank"]))
            rv = gs_v[0]
            rq = min(gs, key=lambda c: c["q"]["rank"])
            # punto representativo: el del cauce prioritario sobre la vía prioritaria si existe
            rep = next((c for c in gs if c["fv"] == rv["fv"] and c["q"]["rank"] == rq["q"]["rank"]), rv)
            lon, lat = rep["pt"].x, rep["pt"].y
            hm = max((muestra(hd, c["pt"].x, c["pt"].y) for c in gs), key=lambda m: m["A"] if m else -1)
            if hm is None: continue
            poblada = pob.contains(rep["pt"]) if not pob.is_empty else False
            zp = lugar(rep["pt"])
            t = rv["via"]
            nombre = t.get("name") or t.get("ref") or ("(sin nombre)" if rv["fv"] == "OSM" else "(vía IGM)")
            # todas las vías del grupo
            nombres = sorted({(c["via"].get("name") or "") for c in gs if c["fv"] == "OSM"} - {""})
            vt, hw = tipo_via(t.get("highway"), nombre, isla, poblada, rv["fv"], t.get("_desc"))
            # estructura
            est = "ninguna cartografiada"
            brid = [c for c in gs if c["fv"] == "OSM" and (c["via"].get("bridge") not in (None, "no") or c["via"].get("tunnel") == "culvert" or c["via"].get("culvert") == "yes")]
            if brid:
                b = brid[0]["via"]
                est = "puente (OSM bridge=%s)" % b.get("bridge") if b.get("bridge") not in (None, "no") else "alcantarilla (OSM, en la vía)"
            elif ts is not None:
                near = [estr[k][1] for k in ts.query(rep["xy"].buffer(ESTR_M), predicate="intersects")]
                if near: est = near[0]
            fuentes_q = sorted({c["q"]["fuente"] for c in gs})
            fila = dict(isla=isla, lon=round(lon, 6), lat=round(lat, 6),
                        via_nombre=nombre, via_otras="; ".join(n for n in nombres if n != nombre), via_tipo=vt,
                        via_highway=hw or "", via_fuente=rv["fv"], via_osm_id=rv["oid"] or "",
                        quebrada_nombre=rq["q"]["nombre"] or "", quebrada_fuente="; ".join(fuentes_q),
                        area_km2=round(hm["A"], 2), L_km=round(hm["L"] / 1000, 2), J_pct=round(hm["J"] * 100, 1),
                        estructura=est, zona_poblada=bool(poblada), lugar=zp or "",
                        edificios_50m=len(te.query(rep["xy"].buffer(50), predicate="intersects")),
                        cota_dsm_m=round(hm["zc"], 1))
            fila.update(caudales(hm["A"], hm["L"], hm["J"], isla == "Santa Cruz"))
            if ases is not None:
                try:   # máximo en 3×3 celdas; el raster del asesor está en km² (etiqueta «unidades»)
                    x, y = Transformer.from_crs(4326, ases.crs, always_xy=True).transform(lon, lat)
                    r0, c0 = ases.index(x, y)
                    v = ases.read(1, window=rasterio.windows.Window(c0 - 1, r0 - 1, 3, 3))
                    fila["area_km2_asesor"] = round(float(np.nanmax(v)), 2)
                except Exception: pass
            fila["puntaje"], fila["prioridad"] = puntaje(fila)
            filas.append(fila)
        filas.sort(key=lambda r: (-r["puntaje"], -r["q100"], -r["area_km2"]))
        for i, r in enumerate(filas, 1): r["id"] = f"CR-{cfg['pref']}-{i:04d}"
        out = ROOT / f"estudios/{cfg['est']}/datos"; out.mkdir(parents=True, exist_ok=True)
        cols = ["id"] + [k for k in filas[0] if k != "id"]
        with open(out / "cruces.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); [w.writerow(r) for r in filas]
        (out / "cruces.geojson").write_text(json.dumps({"type": "FeatureCollection", "metadata": {
            "titulo": f"Cruces de quebradas con vías — {isla} (PRELIMINAR)", "metodo": __doc__.split("Uso:")[0].strip(),
            "criterios_prioridad": PUNTOS, "C_scs": {k: {str(cn): round(v, 2) for cn, v in d.items()} for k, d in CN_C.items()},
            "lluvia": f"Curva intensidad–duración observada en Los Guayabillos el 30-oct-2026 ({TOT30:.1f} mm)"},
            "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                          "properties": {k: r[k] for k in cols if k not in ("lon", "lat")}} for r in filas]}, ensure_ascii=False), encoding="utf-8")
        import collections
        print("  prioridad:", collections.Counter(r["prioridad"] for r in filas), "| estructura:", collections.Counter(r["estructura"].split(" (")[0] for r in filas))
        for r in filas[:25]:
            print("   ", r["id"], r["puntaje"], r["via_nombre"], "|", r["via_tipo"], "|", r["quebrada_nombre"] or r["quebrada_fuente"], "| A", r["area_km2"], "| Q100", r["q100"], r.get("q30oct", ""), "|", r["estructura"], "|", r["lugar"], "| z", r["cota_dsm_m"])

if __name__ == "__main__":
    main()
