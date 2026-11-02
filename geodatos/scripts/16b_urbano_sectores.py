"""Diagnóstico urbano preliminar de dos ámbitos (complementa 16_cruces_quebradas_vias.py):

  A. Sector Tomás de Berlanga (Santa Cruz, −0,7109; −90,3198), parte alta de la cuenca de La Cascada.
  B. San Cristóbal: Puerto Baquerizo Moreno y El Progreso, con atención a la quebrada que llega al campus
     USFQ / Galapagos Science Center (−0,8955; −89,6089).

Método (mismo D8 y mismo cálculo de caudal que el script 16):
  - Cauces: D8 propio sobre el DSM GLO-30 con quebradas IGM quemadas; se usan los cauces con área drenada
    ≥ A_MIN_KM2. Los «sistemas» de cauce urbano se definen por la celda de salida: cada celda de cauce dentro del
    área urbana se asigna a la celda donde su trayectoria D8 sale del área urbana o llega al mar.
  - Ocupación del cauce: edificios (OSM + Open Buildings v3) cuyo polígono está a ≤ 15 m o ≤ 30 m de la línea
    de cauce; población INEC repartida por área de techo dentro de cada manzana.
  - Franja normativa: polígonos CGREG «encañadas» (buffer 20 m) y cobertura de la línea de cauce por la franja.
  - Cruces y estructuras: estudios/<isla>/datos/cruces.csv (script 16).
  - Cotas del DSM con error ±2–4 m (sesgo local frente al IGM: ≈ −2 m en Puerto Ayora, ≈ +1,5 m en Puerto Baquerizo
    Moreno, ≈ +1,9 m en El Progreso): solo descriptivas.

Salidas
  estudios/santa-cruz/datos/urbano/tomas_de_berlanga_{cauces,edificios}.geojson, tomas_de_berlanga.json
  estudios/san-cristobal/datos/urbano/{cauces_urbanos,edificios_expuestos,cuenca_gsc,cauce_gsc}.geojson,
  cifras.json

Uso:  .venv/bin/python -I scripts/16b_urbano_sectores.py   (después de 03, 06, 07 y 16)
"""
import csv, importlib.util, json, math, pathlib, collections
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape, mapping, Point, LineString, MultiLineString
from shapely.ops import unary_union, linemerge, transform as stransform
from shapely.strtree import STRtree
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("c16", ROOT / "scripts/16_cruces_quebradas_vias.py")
c16 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c16)
A_MIN_KM2 = 0.5

def cargar(rel, isla, cond=lambda p: True):
    return [(shape(f["geometry"]), f["properties"]) for f in json.loads((ROOT / rel).read_text())["features"]
            if f.get("geometry") and f["properties"].get("isla") == isla and cond(f["properties"])]

def fc(feats): return {"type": "FeatureCollection", "features": feats}
def guardar(path, feats):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fc(feats), ensure_ascii=False), encoding="utf-8")

class Isla:
    """Capas de una isla en UTM, D8 y utilidades de trazado."""
    def __init__(self, isla):
        cfg = c16.ISLAS[isla]; self.isla = isla; self.cfg = cfg
        self.T = Transformer.from_crs(4326, cfg["epsg"], always_xy=True).transform
        self.TI = Transformer.from_crs(cfg["epsg"], 4326, always_xy=True).transform
        self.hd = c16.hidro(cfg["key"])
        H, W = self.hd["A"].shape; self.H, self.W = H, W
        ed = cargar("capas/final/edificios_exposicion.geojson", isla)
        self.ed = [(stransform(self.T, g), p) for g, p in ed]
        self.edg = [g for g, p in self.ed]; self.ted = STRtree(self.edg)
        # población por edificio (INEC, reparto por área de techo)
        self.pob = np.zeros(len(self.edg))
        for g, p in cargar("capas/final/manzanas_inec.geojson", isla):
            if not p.get("pob_estimada"): continue
            g = stransform(self.T, g)
            ids = [i for i in self.ted.query(g) if g.contains(self.edg[i].centroid)]
            a = np.array([self.edg[i].area for i in ids])
            if len(ids) and a.sum() > 0: self.pob[ids] += p["pob_estimada"] * a / a.sum()
        self.franja = unary_union([stransform(self.T, g) for g, p in cargar("capas/final/quebradas_franja20m_cgreg.geojson", isla)])
        self.qnom = [(stransform(self.T, g), p["nombre"]) for g, p in cargar("capas/final/quebradas.geojson", isla, lambda p: p.get("nombre"))]
        self.cruces = [r for r in csv.DictReader(open(ROOT / f"estudios/{cfg['est']}/datos/cruces.csv", encoding="utf-8"))]
        for r in self.cruces: r["_xy"] = Point(self.T(float(r["lon"]), float(r["lat"])))
        self.tcr = STRtree([r["_xy"] for r in self.cruces])

    def rc(self, lon, lat):
        c, r = ~self.hd["tr"] * (lon, lat); return int(r), int(c)
    def xy(self, r, c):
        lon, lat = self.hd["tr"] * (c + .5, r + .5); return self.T(lon, lat)
    def km2(self, r, c): return float(self.hd["A"][r, c] * c16.CELL_KM2)

    def aguas_abajo(self, r, c, stop=None):
        path = [(r, c)]; i = r * self.W + c; dn = self.hd["down"]
        while dn[i] >= 0 and len(path) < 20000:
            i = int(dn[i]); rr, cc = divmod(i, self.W)
            if not self.hd["land"][rr, cc]: break
            path.append((rr, cc))
            if stop is not None and stop(rr, cc): break
        return path

    def cuenca(self, r, c):
        """Máscara de celdas que drenan a (r, c)."""
        dn = self.hd["down"]; tgt = r * self.W + c
        land = self.hd["land"].ravel()
        lab = np.zeros(self.H * self.W, bool); lab[tgt] = True
        order = np.argsort(-self.hd["A"].ravel())      # de aguas abajo a aguas arriba
        for i in order:
            if land[i] and not lab[i] and dn[i] >= 0 and lab[dn[i]]: lab[i] = True
        return lab.reshape(self.H, self.W)

    def cauce_principal_arriba(self, r, c):
        """Remonta siguiendo la celda vecina con mayor acumulación (cauce principal)."""
        path = [(r, c)]; dn = self.hd["down"]; A = self.hd["A"]
        while True:
            best = None
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = path[-1][0] + dr, path[-1][1] + dc
                    if (dr or dc) and 0 <= rr < self.H and 0 <= cc < self.W and dn[rr * self.W + cc] == path[-1][0] * self.W + path[-1][1]:
                        if best is None or A[rr, cc] > A[best]: best = (rr, cc)
            if best is None or A[best] * c16.CELL_KM2 < 0.02: break
            path.append(best)
        return path

    def linea(self, path): return LineString([self.xy(r, c) for r, c in path])

    def expo(self, zona):
        ids = [i for i in self.ted.query(zona, predicate="intersects")]
        return ids, int(round(self.pob[ids].sum()))

    def cruces_en(self, geom, d=25):
        return [self.cruces[k] for k in self.tcr.query(geom.buffer(d), predicate="intersects")]

def caudal(A, L, J, evento=False):
    return c16.caudales(A, L, J, evento)

# ================================================================ A. Tomás de Berlanga
def tomas_de_berlanga():
    I = Isla("Santa Cruz"); T = I.T
    p0 = Point(T(-90.3198, -0.7109))
    bar = unary_union([stransform(T, g) for g, p in cargar("capas/final/barrios.geojson", "Santa Cruz", lambda p: p.get("nombre") == "TOMAS DE BERLANGA")])
    zona = unary_union([bar, p0.buffer(500)])
    out = dict(punto=[-90.3198, -0.7109])
    out["barrio_cgreg_ha"] = round(bar.area / 1e4, 1)
    suelo = [p.get("suelo") for g, p in cargar("capas/final/suelo_urbano_rural_cgreg.geojson", "Santa Cruz") if stransform(T, g).contains(p0)]
    out["suelo_cgreg_en_el_punto"] = suelo
    for nm, z in [("barrio_cgreg", bar), ("radio_500m", p0.buffer(500)), ("radio_300m", p0.buffer(300))]:
        ids, pob = I.expo(z)
        vv = [p for g, p in cargar("capas/final/viviendas_sngr.geojson", "Santa Cruz") if z.contains(Point(T(*g.coords[0])))]
        out[nm] = dict(area_ha=round(z.area / 1e4, 1), edificios=len(ids), pob_inec=pob, viviendas_sngr=len(vv),
                       pob_sngr=int(round(sum(p["pob_x_casa"] for p in vv))))
    # cauces D8 ≥ A_MIN en la zona: celdas de cauce, agrupadas por la celda de salida de la zona
    msk = np.zeros((I.H, I.W), bool)
    rr, cc = np.where(I.hd["A"] * c16.CELL_KM2 >= A_MIN_KM2)
    for r, c in zip(rr, cc):
        if zona.contains(Point(I.xy(r, c))): msk[r, c] = True
    sal = {}
    for r, c in zip(*np.where(msk)):
        path = I.aguas_abajo(r, c, stop=lambda a, b: not msk[a, b])
        sal.setdefault(path[-1], []).append((r, c))
    cauces = []
    for (rs, cs), cells in sal.items():
        if len(cells) < 3: continue
        top = max(cells, key=lambda x: -I.hd["A"][x])   # celda de cauce más aguas arriba (menor A)
        path = I.aguas_abajo(*top, stop=lambda a, b: not msk[a, b])
        ln = I.linea(path)
        A = I.km2(*path[-1]); L = float(I.hd["L"][path[-1]]); zs = float(I.hd["Zs"][path[-1]]); z0 = float(I.hd["Z"][path[-1]])
        J = max((zs - z0) / L, 0.005)
        ids15, pob15 = I.expo(ln.buffer(15)); ids30, pob30 = I.expo(ln.buffer(30))
        sobre = [i for i in ids15 if I.edg[i].intersects(ln)]
        cr = I.cruces_en(ln)
        q = caudal(A, L, J, True)
        cauces.append(dict(geom=ln, area_km2=round(A, 2), largo_en_zona_m=round(ln.length), cota_ini=round(float(I.hd["Z"][path[0]]), 1),
                           cota_fin=round(z0, 1), edif_15m=len(ids15), edif_30m=len(ids30), pob_30m=pob30, edif_sobre_linea=len(sobre),
                           cruces=len(cr), cruces_ids=", ".join(r["id"] for r in cr), **q))
    cauces.sort(key=lambda d: -d["area_km2"])
    out["cauces"] = [{k: v for k, v in d.items() if k != "geom"} for d in cauces]
    # cauces mayores según drenaje_derivado (03_dem.py), recortados a la zona: más robusto que el trazado por sistemas
    dd = [(stransform(T, g), p["area_drenada_km2"]) for g, p in cargar("capas/final/drenaje_derivado.geojson", "Santa Cruz", lambda p: p["area_drenada_km2"] >= 5)]
    dd = [(g.intersection(zona), A) for g, A in dd if g.intersects(zona)]
    mayor = unary_union([g for g, A in dd])
    if not mayor.is_empty:
        i15, p15 = I.expo(mayor.buffer(15)); i30, p30 = I.expo(mayor.buffer(30))
        sobre = [i for i in i15 if I.edg[i].intersects(mayor)]
        out["cauces_mayores_5km2"] = dict(tramos=len(dd), areas_km2=sorted({A for g, A in dd}), largo_en_zona_m=round(mayor.length),
                                          edif_15m=len(i15), edif_30m=len(i30), pob_inec_30m=p30, edif_sobre_linea=len(sobre))
    # escuela
    esc = [(stransform(T, g), p) for g, p in cargar("capas/final/puntos_clave.geojson", "Santa Cruz", lambda p: "Berlanga" in (p.get("nombre") or "") or "BERLANGA" in (p.get("nombre") or ""))]
    out["escuela"] = [dict(nombre=p.get("nombre"), dist_cauce_mayor_m=round(g.distance(mayor)) if not mayor.is_empty else None,
                           cota_dsm_m=round(float(I.hd["Z"][I.rc(*I.TI(g.x, g.y))]), 1)) for g, p in esc]
    # vías y cruces de la zona
    vias = collections.Counter()
    for g, t in cargar("capas/osm/vias.geojson", "Santa Cruz"):
        g = stransform(T, g)
        if g.intersects(zona): vias[(t.get("name") or "(sin nombre)", t.get("highway"), t.get("surface") or "")] += round(g.intersection(zona).length)
    out["vias_m"] = [dict(nombre=k[0], highway=k[1], superficie=k[2], metros=v) for k, v in vias.most_common()]
    crz = I.cruces_en(zona, 0)
    out["cruces"] = [{k: r[k] for k in ("id", "via_nombre", "via_tipo", "area_km2", "q100", "q30oct", "estructura", "prioridad", "cota_dsm_m")} for r in sorted(crz, key=lambda r: -float(r["q30oct"] or 0))]
    out["franja_cgreg_dist_m"] = round(p0.distance(I.franja)) if not I.franja.is_empty else None
    cu = unary_union([stransform(T, g) for g, p in [(shape(f["geometry"]), f["properties"]) for f in json.loads((ROOT / "estudios/la-cascada/datos/cuenca_cascada.geojson").read_text())["features"]]])
    out["dentro_cuenca_la_cascada"] = bool(cu.contains(p0))
    o = ROOT / "estudios/santa-cruz/datos/urbano"
    guardar(o / "tomas_de_berlanga_cauces.geojson", [{"type": "Feature", "geometry": mapping(stransform(I.TI, g)),
             "properties": {"area_drenada_km2": A, "fuente": "D8 GLO-30 (03_dem.py), recortado al sector"}} for g, A in dd if not g.is_empty])
    ids, _ = I.expo(mayor.buffer(30)) if not mayor.is_empty else ([], 0)
    guardar(o / "tomas_de_berlanga_edificios.geojson", [{"type": "Feature", "geometry": mapping(stransform(I.TI, I.edg[i])),
             "properties": {"fuente": I.ed[i][1].get("fuente"), "dist_cauce_m": round(I.edg[i].distance(mayor), 1),
                            "sobre_linea": bool(I.edg[i].intersects(mayor)), "pob_inec": round(float(I.pob[i]), 1)}} for i in ids])
    (o / "tomas_de_berlanga.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    mapa(I, -90.3175, -0.7115, 750, cauces_d8(I, -90.3175, -0.7115, 750), ROOT / "estudios/santa-cruz/figuras/f_tomas_de_berlanga.png",
         "Sector Tomás de Berlanga (Santa Cruz): cauces, edificaciones y cruces con vías", [(-90.3198, -0.7109, "Escuela Tomás de Berlanga (OSM)")])
    print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])

# ================================================================ B. San Cristóbal
def san_cristobal():
    I = Isla("San Cristóbal"); T = I.T
    urb_igm = unary_union([stransform(T, g) for g, p in cargar("capas/final/zonas_pobladas.geojson", "San Cristóbal", lambda p: p.get("tipo") == "Límite urbano IGM")])
    huella = [(stransform(T, g), p) for g, p in cargar("capas/final/zonas_pobladas.geojson", "San Cristóbal", lambda p: p.get("tipo") == "Huella edificada")]
    prog = unary_union([stransform(T, g) for g, p in cargar("capas/final/suelo_urbano_rural_cgreg.geojson", "San Cristóbal", lambda p: p.get("suelo") == "Suelo urbano")])
    pbm_lon, pbm_lat = -89.6106, -0.9015
    pbm = unary_union([urb_igm] + [g for g, p in huella if g.distance(Point(T(pbm_lon, pbm_lat))) < 2500])
    elp = unary_union([prog] + [g for g, p in huella if g.distance(prog) < 300])
    cif = {}
    feats_c, feats_e = [], []
    for nombre, zona in [("Puerto Baquerizo Moreno", pbm), ("El Progreso", elp)]:
        ids, pob = I.expo(zona)
        fr = I.franja.intersection(zona)
        idsf, pobf = I.expo(fr) if not fr.is_empty else ([], 0)
        c = dict(area_ha=round(zona.area / 1e4, 1), edificios=len(ids), pob_inec=pob, franja_cgreg_ha=round(fr.area / 1e4, 2),
                 edificios_en_franja_cgreg=len(idsf), pob_en_franja=pobf)
        for i in idsf:
            feats_e.append({"type": "Feature", "geometry": mapping(stransform(I.TI, I.edg[i])), "properties": {"localidad": nombre, "motivo": "franja CGREG 20 m", "fuente": I.ed[i][1].get("fuente"), "pob_inec": round(float(I.pob[i]), 1)}})
        # sistemas de cauce: celdas de cauce ≥ A_MIN dentro de la zona, agrupadas por salida
        msk = np.zeros((I.H, I.W), bool)
        rr, cc = np.where(I.hd["A"] * c16.CELL_KM2 >= A_MIN_KM2)
        zb = zona.buffer(30)
        for r, cq in zip(rr, cc):
            if zb.contains(Point(I.xy(r, cq))): msk[r, cq] = True
        sal = {}
        for r, cq in zip(*np.where(msk)):
            path = I.aguas_abajo(r, cq, stop=lambda a, b: not msk[a, b])
            sal.setdefault(path[-1], []).append((r, cq))
        sist = []
        for (rs, cs), cells in sal.items():
            if len(cells) < 2: continue
            # entrada: la celda del sistema con mayor área entre las que reciben de fuera
            top = min(cells, key=lambda x: I.hd["A"][x])
            path = I.aguas_abajo(*top, stop=lambda a, b: not msk[a, b])
            ln = I.linea(path)
            A = I.km2(*path[-1]); L = float(I.hd["L"][path[-1]]); zs = float(I.hd["Zs"][path[-1]]); z0 = float(I.hd["Z"][path[-1]])
            J = max((zs - z0) / L, 0.005)
            # ¿la salida llega al mar?
            nxt = I.aguas_abajo(*path[-1])
            al_mar = len(nxt) <= 3
            ent = max([x for x in cells if not zona.contains(Point(I.xy(*x)))] or [path[0]], key=lambda x: I.hd["A"][x])
            ids15, pob15 = I.expo(ln.buffer(15)); ids30, pob30 = I.expo(ln.buffer(30))
            sobre = [i for i in ids15 if I.edg[i].intersects(ln)]
            cob = ln.intersection(I.franja.buffer(30)).length / ln.length if ln.length else 0   # franja a ≤ 30 m (el D8 se desplaza del cauce real)
            qn = min(I.qnom, key=lambda gn: gn[0].distance(ln)) if I.qnom else None
            nombre_q = qn[1] if qn and qn[0].distance(ln) < 150 else ""
            cr = I.cruces_en(ln)
            q = caudal(A, L, J, False)
            lon_s, lat_s = I.TI(*ln.coords[-1])
            d = dict(localidad=nombre, quebrada_igm_nombre=nombre_q, area_salida_km2=round(A, 2), area_entrada_km2=round(I.km2(*ent), 2), largo_m=round(ln.length),
                     cota_ini_m=round(float(I.hd["Z"][path[0]]), 1), cota_salida_m=round(z0, 1), salida=[round(lon_s, 5), round(lat_s, 5)],
                     salida_al_mar=al_mar, edif_15m=len(ids15), edif_30m=len(ids30), pob_30m=pob30, edif_sobre_linea=len(sobre),
                     cobertura_franja_cgreg_30m_pct=round(cob * 100), cruces=len(cr), cruces_con_estructura=sum(1 for r in cr if r["estructura"] != "ninguna cartografiada"),
                     cruces_ids=", ".join(r["id"] for r in cr), **q)
            sist.append((ln, d))
            for i in ids30:
                feats_e.append({"type": "Feature", "geometry": mapping(stransform(I.TI, I.edg[i])), "properties": {"localidad": nombre, "motivo": "≤ 30 m de cauce D8 (%.1f km²)" % A, "dist_m": round(I.edg[i].distance(ln), 1), "fuente": I.ed[i][1].get("fuente"), "pob_inec": round(float(I.pob[i]), 1)}})
        sist.sort(key=lambda s: -s[1]["area_salida_km2"])
        for k, (ln, d) in enumerate(sist, 1):
            d["id"] = ("PBM" if nombre.startswith("Puerto") else "ELP") + f"-{k:02d}"
            feats_c.append({"type": "Feature", "geometry": mapping(stransform(I.TI, ln)), "properties": d})
        c["sistemas_de_cauce"] = [d for ln, d in sist]
        ids30 = set()
        for ln, d in sist: ids30 |= set(I.expo(ln.buffer(30))[0])
        c["edificios_30m_algun_cauce"] = len(ids30); c["pob_30m_algun_cauce"] = int(round(I.pob[list(ids30)].sum())) if ids30 else 0
        # complemento: tramos de drenaje_derivado (03_dem.py) ≥ 0,3 km² que pasan a ≤ 50 m de la zona
        prox = []
        for g, p in cargar("capas/final/drenaje_derivado.geojson", I.isla, lambda p: p["area_drenada_km2"] >= 0.3):
            g = stransform(T, g)
            if g.distance(zona) <= 50:
                i15, _ = I.expo(g.buffer(15)); i30, p30 = I.expo(g.buffer(30))
                if len(i15):
                    lon_m, lat_m = I.TI(*g.interpolate(0.5, normalized=True).coords[0])
                    prox.append(dict(area_km2=p["area_drenada_km2"], largo_m=round(g.length), edif_15m=len(i15), edif_30m=len(i30), pob_30m=p30, punto_medio=[round(lon_m, 5), round(lat_m, 5)]))
        c["tramos_drenaje_derivado_0_3km2"] = sorted(prox, key=lambda d: -d["edif_15m"])
        # comparación con las cañadas oficiales de la hidrología (datos/cañadas_oficiales.geojson), recortadas a la zona
        fo = ROOT / "estudios/san-cristobal/datos/cañadas_oficiales.geojson"
        if fo.exists():
            comp = []
            ofi = json.loads(fo.read_text(encoding="utf-8"))["features"]
            gal = unary_union([stransform(T, shape(f["geometry"])) for f in ofi if f["properties"]["cañada_oficial"].startswith("Galápagos")])
            for f in ofi:
                g = stransform(T, shape(f["geometry"]))
                if not f["properties"]["cañada_oficial"].startswith("Galápagos"):
                    g = g.difference(gal.buffer(10))   # solo el tramo propio: sin el curso compartido de la Galápagos
                g = g.intersection(zona)
                if g.is_empty or g.length < 20: continue
                i15, _ = I.expo(g.buffer(15)); i30, p30 = I.expo(g.buffer(30))
                comp.append(dict(cañada_oficial=f["properties"]["cañada_oficial"], largo_en_zona_m=round(g.length), edif_15m=len(i15), edif_30m=len(i30), pob_30m=p30,
                                 sobre_linea=sum(1 for i in i15 if I.edg[i].intersects(g)), franja_directa_m=round(g.intersection(I.franja).length),
                                 franja_30m_m=round(g.intersection(I.franja.buffer(30)).length)))
            c["cañadas_oficiales_en_zona"] = comp
            print("   oficiales:", comp)
        c["definicion_zona"] = ("límite urbano IGM ∪ huella edificada a < 2,5 km del centro" if nombre.startswith("Puerto") else "suelo urbano CGREG ∪ huella edificada a < 300 m")
        cif[nombre] = c
        print("==", nombre, {k: v for k, v in c.items() if k != "sistemas_de_cauce"})
        for ln, d in sist:
            print("   ", d["id"], d["quebrada_igm_nombre"], "A", d["area_salida_km2"], "L", d["largo_m"], "mar" if d["salida_al_mar"] else "no-mar", d["salida"], "edif15/30", d["edif_15m"], d["edif_30m"], "sobre", d["edif_sobre_linea"], "franja%", d["cobertura_franja_cgreg_30m_pct"], "cruces", d["cruces"], d["cruces_con_estructura"], "Q100", d["q100"])
    # ---------------- campus USFQ / GSC
    g0 = Point(T(-89.6089, -0.8955))
    campus_nombres = ("USFQ", "Galapagos Science Center", "Laboratorio de Salud Animal", "Universidad San Francisco")
    osm_ed = [(stransform(T, shape(f["geometry"])), f["properties"]) for f in json.loads((ROOT / "capas/osm/edificios.geojson").read_text())["features"]
              if f["properties"].get("isla") == "San Cristóbal" and shape(f["geometry"]).distance(Point(-89.6089, -0.8955)) * 111000 < 300]
    campus = [(g, p) for g, p in osm_ed if any(n.lower() in (p.get("name") or "").lower() for n in campus_nombres)]
    campus_u = unary_union([g for g, p in campus]).buffer(60)
    # celda de cauce con mayor A a ≤ 90 m del campus
    best = None
    r0, c0 = I.rc(*I.TI(g0.x, g0.y))
    for dr in range(-5, 6):
        for dc in range(-5, 6):
            r, c = r0 + dr, c0 + dc
            if I.hd["land"][r, c] and Point(I.xy(r, c)).distance(unary_union([g for g, p in campus])) <= 90:
                if best is None or I.hd["A"][r, c] > I.hd["A"][best]: best = (r, c)
    A = I.km2(*best)
    arriba = I.cauce_principal_arriba(*best)
    abajo = I.aguas_abajo(*best)
    ln = I.linea(arriba[::-1] + abajo[1:])
    cu = I.cuenca(*best)
    poly = unary_union([shape(g) for g, v in shapes(cu.astype("uint8"), mask=cu, transform=I.hd["tr"])])
    poly_u = stransform(I.T, poly)
    L = float(I.hd["L"][best]); zs = float(I.hd["Zs"][best]); z0 = float(I.hd["Z"][best]); J = max((zs - z0) / L, 0.005)
    q = caudal(A, L, J, False)
    q_ev = c16.caudales(A, L, J, True)   # lluvia del 30-oct en Santa Cruz aplicada como escenario hipotético
    cr = I.cruces_en(ln)
    ed_campus = []
    for g, p in osm_ed:
        dd = g.distance(ln)
        if dd <= 60: ed_campus.append(dict(nombre=p.get("name") or p.get("amenity") or p.get("building"), niveles=p.get("building:levels"), dist_cauce_m=round(dd, 1), cota_dsm_m=round(float(I.hd["Z"][I.rc(*I.TI(g.centroid.x, g.centroid.y))]), 1)))
    ids15, pob15 = I.expo(ln.buffer(15)); ids30, pob30 = I.expo(ln.buffer(30))
    usos = collections.Counter()
    for g, p in cargar("capas/final/zonas_pobladas.geojson", "San Cristóbal"):
        g = stransform(T, g)
        if g.intersects(poly_u): usos[p.get("tipo")] += round(g.intersection(poly_u).area / 1e4, 1)
    parque = unary_union([stransform(T, g) for g, p in cargar("capas/final/parque_zonificacion.geojson", "San Cristóbal")]) if (ROOT / "capas/final/parque_zonificacion.geojson").exists() else None
    gsc = dict(celda_lonlat=[round(v, 5) for v in I.TI(*I.xy(*best))], area_km2=round(A, 3), L_km=round(L / 1000, 2), J_pct=round(J * 100, 1),
               cota_cabecera_m=round(zs), cota_campus_m=round(z0, 1), **q, q30oct_hipotetico=q_ev.get("q30oct"),
               franja_cgreg_cubre_cauce_pct=round(ln.intersection(I.franja.buffer(30)).length / ln.length * 100), franja_dist_campus_m=round(unary_union([g for g, p in campus]).distance(I.franja)),
               cruces=[{k: r[k] for k in ("id", "via_nombre", "via_tipo", "area_km2", "q100", "estructura", "cota_dsm_m")} for r in cr],
               edificios_campus_60m=ed_campus, edificios_15m=len(ids15), edificios_30m=len(ids30), pob_30m=pob30,
               cuenca_huella_edificada_ha=round(usos.get("Huella edificada", 0), 1), cuenca_ha=round(poly_u.area / 1e4, 1),
               cuenca_edificios=len([i for i in I.ted.query(poly_u, predicate="intersects")]))
    cif["campus_USFQ_GSC"] = gsc
    print("== GSC", json.dumps(gsc, ensure_ascii=False)[:3000])
    o = ROOT / "estudios/san-cristobal/datos/urbano"
    guardar(o / "cauces_urbanos.geojson", feats_c)
    guardar(o / "edificios_expuestos.geojson", feats_e)
    guardar(o / "cuenca_gsc.geojson", [{"type": "Feature", "geometry": mapping(poly), "properties": {"area_km2": round(A, 3)}}])
    guardar(o / "cauce_gsc.geojson", [{"type": "Feature", "geometry": mapping(stransform(I.TI, ln)), "properties": {k: v for k, v in gsc.items() if not isinstance(v, list)}}])
    (o / "cifras.json").write_text(json.dumps(cif, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    fo = ROOT / "estudios/san-cristobal/figuras"
    mapa(I, -89.6060, -0.9015, 1300, cauces_d8(I, -89.6060, -0.9015, 1300), fo / "f_urbano_pbm.png",
         "Puerto Baquerizo Moreno: cauces que entran en la ciudad, franja CGREG y cruces con vías", [(-89.6089, -0.8955, "USFQ / GSC")])
    mapa(I, -89.6060, -0.8965, 550, cauces_d8(I, -89.6060, -0.8965, 550, 0.1) + [(ln, 0.3)], fo / "f_campus_gsc.png",
         "Campus USFQ / Galapagos Science Center: cauce que llega al campus", [(-89.6089, -0.8955, "GSC")])


# ================================================================ figuras
def mapa(I, lon, lat, R, cauces, out, titulo, marcas=()):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, rasterio
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    c0 = Point(I.T(lon, lat)); win = c0.buffer(R * 1.5)
    fig, ax = plt.subplots(figsize=(9, 9))
    # relieve (DSM) remuestreado a UTM por puntos
    xs = np.linspace(c0.x - R, c0.x + R, 160); ys = np.linspace(c0.y + R, c0.y - R, 160)
    Z = np.full((160, 160), np.nan)
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            r, c = I.rc(*I.TI(x, y))
            if 0 <= r < I.H and 0 <= c < I.W and I.hd["land"][r, c]: Z[i, j] = I.hd["Z"][r, c]
    ax.imshow(Z, extent=(c0.x - R, c0.x + R, c0.y - R, c0.y + R), cmap="terrain", vmin=np.nanmin(Z) - 30, vmax=np.nanmax(Z) + 30, alpha=.45)
    cs = ax.contour(xs, ys, np.nan_to_num(Z, nan=-5), levels=np.arange(0, 1000, 10), colors="k", linewidths=.3, alpha=.6)
    ax.clabel(cs, fmt="%d m", fontsize=6)
    if not I.franja.is_empty:
        for gg in getattr(I.franja.intersection(win), "geoms", [I.franja.intersection(win)]):
            if gg.geom_type == "Polygon": ax.fill(*gg.exterior.xy, color="#2ab7ca", alpha=.45, lw=0)
    for g in I.edg:
        if g.intersects(win):
            for gg in getattr(g, "geoms", [g]): ax.fill(*gg.exterior.xy, color="0.3", lw=0)
    for g, t in cargar("capas/osm/vias.geojson", I.isla):
        g = stransform(I.T, g)
        if g.intersects(win):
            hw = t.get("highway"); ax.plot(*g.xy, color="#c0392b" if hw in ("primary", "secondary", "tertiary") else "white", lw=1.6 if hw in ("primary", "secondary", "tertiary") else .7, zorder=3)
    for ln, A in cauces:
        ax.plot(*ln.xy, color="#1f6fd1", lw=1 + 1.2 * min(A, 10) ** .5, zorder=4, solid_capstyle="round")
    col = {"alta": "#d62728", "media": "#ffbf00", "baja": "#bbbbbb"}
    for r in I.cruces:
        if r["_xy"].within(win):
            ax.plot(r["_xy"].x, r["_xy"].y, "o", color=col[r["prioridad"]], mec="k", mew=.5, ms=7 if r["prioridad"] == "alta" else 5, zorder=6)
    for mlon, mlat, txt in marcas:
        x, y = I.T(mlon, mlat); ax.plot(x, y, "*", color="k", ms=14, zorder=7); ax.annotate(txt, (x, y), xytext=(6, 6), textcoords="offset points", fontsize=8, zorder=7)
    ax.set_xlim(c0.x - R, c0.x + R); ax.set_ylim(c0.y - R, c0.y + R); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(titulo, fontsize=10)
    ax.plot([c0.x - R * .9, c0.x - R * .9 + 200], [c0.y - R * .92] * 2, "k-", lw=3); ax.text(c0.x - R * .9, c0.y - R * .88, "200 m", fontsize=8)
    ley = [Patch(color="0.3", label="Edificaciones (OSM + Open Buildings)"), Line2D([], [], color="#1f6fd1", lw=3, label="Cauce D8 ≥ 0,5 km² (grosor ∝ área)"),
           Patch(color="#2ab7ca", alpha=.45, label="Franja de quebrada CGREG (20 m)"), Line2D([], [], color="#c0392b", lw=2, label="Vía principal OSM"),
           Line2D([], [], marker="o", ls="", color="#d62728", mec="k", label="Cruce prioridad alta"), Line2D([], [], marker="o", ls="", color="#ffbf00", mec="k", label="Cruce prioridad media")]
    ax.legend(handles=ley, loc="lower right", fontsize=7, framealpha=.9)
    fig.text(.5, .02, "Relieve y curvas cada 10 m del DSM Copernicus GLO-30 (±2–4 m). Cauces D8 derivados del DSM: posición aproximada. PRELIMINAR.", ha="center", fontsize=7)
    out.parent.mkdir(parents=True, exist_ok=True); fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)

def cauces_d8(I, lon, lat, R, amin=A_MIN_KM2):
    """Líneas de cauce D8 (≥ amin) en un radio, para dibujar."""
    feats = [(stransform(I.T, g), p["area_drenada_km2"]) for g, p in cargar("capas/final/drenaje_derivado.geojson", I.isla, lambda p: p["area_drenada_km2"] >= amin)]
    c0 = Point(I.T(lon, lat))
    return [(g, A) for g, A in feats if g.distance(c0) < R * 1.5]

if __name__ == "__main__":
    tomas_de_berlanga()
    san_cristobal()
