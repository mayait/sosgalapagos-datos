"""Recorta todas las capas al área de interés (zonas pobladas, zona agrícola y vías; se excluye el parque),
suaviza los polígonos derivados de píxeles, quita duplicados y exporta un paquete listo para el proyecto
principal: export/galapagos/*.geojson + capas.json (manifiesto con grupos, estilos y leyendas).

Uso: .venv/bin/python -I scripts/08_exportar.py
"""
import json, pathlib, math
import numpy as np, rasterio
from rasterio import features
from scipy.ndimage import gaussian_filter
import contourpy
from PIL import Image
from shapely.geometry import shape, mapping, LineString, MultiLineString, Point, box
from shapely.ops import unary_union, linemerge
from shapely.strtree import STRtree
from shapely import set_precision

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = ROOT / "capas"; OUT = ROOT / "export" / "galapagos"; OUT.mkdir(parents=True, exist_ok=True)
(OUT / "raster").mkdir(exist_ok=True)
M = 1 / 111320                      # grados por metro en el ecuador
REG = {"Santa Cruz": "santa_cruz", "San Cristóbal": "san_cristobal", "Isabela": "isabela_sur"}
VIAS_OK = {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
           "residential", "service", "living_street", "track", "pedestrian", "trunk"}

def load(p): return json.loads((C / p).read_text())["features"]
def rnd(g, nd=5):
    return json.loads(json.dumps(mapping(g)), parse_float=lambda x: round(float(x), nd))
manifest_sizes = {}
def save(name, feats):
    fc = {"type": "FeatureCollection", "features": feats}
    (OUT / name).write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")))
    manifest_sizes[name] = len(feats)
    print(f"  {name:42s} {len(feats):6d}  {(OUT / name).stat().st_size / 1e6:5.2f} MB")
def F(g, **p): return {"type": "Feature", "geometry": rnd(g), "properties": {k: v for k, v in p.items() if v not in (None, "")}}
def suave(g, r=12):
    """Cierre + apertura morfológica: redondea la escalera de píxeles de 30 m sin cambiar la forma."""
    return g.buffer(r * M, 4).buffer(-2 * r * M, 4).buffer(r * M, 4).simplify(3 * M, preserve_topology=True)
def parts(g):
    return [x for x in getattr(g, "geoms", [g]) if not x.is_empty]

# ───────────────────────── 1. Área de interés ─────────────────────────
print("Área de interés")
tierra = {}
for f in load("igm/islas.geojson"):
    tierra.setdefault(f["properties"]["isla"], []).append(shape(f["geometry"]).buffer(0))
tierra = {k: unary_union(v).buffer(60 * M) for k, v in tierra.items()}
pobl = [shape(f["geometry"]) for f in load("final/zonas_pobladas.geojson") if f["properties"]["tipo"] != "OSM farmyard"]
pobl += [shape(f["geometry"]) for f in load("final/manzanas_inec.geojson")]
suelo = [shape(f["geometry"]).buffer(0) for f in load("final/suelo_urbano_rural_cgreg.geojson")]
# Zonificación del Parque Nacional Galápagos 2017 (CGREG/FCD): RURAL y URBANO = zona colonizada; el resto = parque
ZONAS_PARQUE = {"INTANGIBLE": "Intangible", "CONSERVACION": "Conservación", "TRANSICION": "Transición",
                "APROVECHAMIENTO SUSTENTABLE": "Aprovechamiento sustentable", "AREA ESPECIAL": "Área especial"}
zon = json.loads((ROOT / "descargas/oficiales/fcd_zonificacion_png_2017_terrestre.geojson").read_text())["features"]
parque_z, colon = [], []
for f in zon:
    g = shape(f["geometry"]).buffer(0); n = f["properties"].get("nombre")
    if n in ("RURAL", "URBANO"): colon.append((g, n))
    elif n in ZONAS_PARQUE: parque_z.append((g, ZONAS_PARQUE[n]))
suelo += [g for g, _ in colon]
vias_osm = [f for f in load("osm/vias.geojson") if f["properties"].get("highway") in VIAS_OK]
aoi = {}
def isla_de(g):
    p = g.representative_point()
    for k, (w, s, e, n) in {"Santa Cruz": (-90.56, -0.80, -90.15, -0.42), "San Cristóbal": (-89.66, -0.97, -89.22, -0.66),
                            "Isabela": (-91.67, -1.10, -90.76, 0.18)}.items():
        if w <= p.x <= e and s <= p.y <= n: return k
aoi_feats = []
for isla in REG:
    a = [g.buffer(500 * M, 8) for g in pobl if isla_de(g) == isla]
    a += [g for g in suelo if isla_de(g) == isla]          # toda la zona agrícola y urbana
    a += [shape(f["geometry"]).buffer(0) for f in load("dem/cuencas_localidad.geojson") + load("dem/cuencas_aportantes.geojson")
          if f["properties"]["isla"] == isla]                 # cuencas que drenan a poblados, completas
    a += [shape(f["geometry"]).buffer(300 * M, 4) for f in vias_osm if f["properties"]["isla"] == isla]
    u = unary_union(a).buffer(100 * M, 4).buffer(-100 * M, 4)          # cierra huecos pequeños
    u = u.intersection(tierra[isla]).simplify(15 * M, preserve_topology=True)
    u = unary_union([p for p in parts(u) if p.area / M**2 > 50_000])
    aoi[isla] = u
    aoi_feats.append(F(u, isla=isla, area_km2=round(u.area / M**2 / 1e6, 1),
                       criterio="Zona agrícola y urbana completas (zonificación PNG 2017 y CGREG) + cuencas completas que drenan a poblados + 500 m de zonas pobladas + 300 m de vías"))
    print(f"  {isla}: {u.area / M**2 / 1e6:.1f} km²")
AOI = unary_union(list(aoi.values()))
def clip(g):
    """Recorta una geometría al área de interés; devuelve (geom, isla) o (None, None)."""
    for isla, a in aoi.items():
        if g.intersects(a):
            c = g.intersection(a) if not a.contains(g) else g
            if not c.is_empty: return c, isla
    return None, None

print("Exportando capas")
save("area_interes.geojson", aoi_feats)

# ───────────────────────── 1b. Parque Nacional y zona agrícola ─────────────────────────
BBX = {"Santa Cruz": box(-90.56, -0.80, -90.15, -0.42), "San Cristóbal": box(-89.66, -0.97, -89.22, -0.66), "Isabela": box(-91.67, -1.10, -90.76, 0.18)}
pq, zp, lp, ag = [], [], [], []
for isla, bx in BBX.items():
    col = unary_union([g for g, _ in colon if g.intersects(bx)]).intersection(bx)
    park = unary_union([g for g, _ in parque_z if g.intersects(bx)]).intersection(bx).difference(col.buffer(5 * M))
    for z in ZONAS_PARQUE.values():
        u = unary_union([g for g, n in parque_z if n == z and g.intersects(bx)])
        if u.is_empty: continue
        u = u.intersection(bx).difference(col.buffer(5 * M)).simplify(20 * M, preserve_topology=True)
        for x in parts(u):
            if x.area / M**2 > 20_000: zp.append(F(x, isla=isla, zona=z, fuente="Zonificación PNG 2017 (CGREG/FCD)"))
    for x in parts(park.simplify(20 * M, preserve_topology=True)):
        if x.area / M**2 > 20_000:
            pq.append(F(x, isla=isla, nombre="Parque Nacional Galápagos", area_km2=round(x.area / M**2 / 1e6, 1),
                        nota="Área protegida. Fuera de la zona colonizada (rural y urbana).", fuente="Zonificación PNG 2017 (CGREG/FCD)"))
    # límite parque ↔ zona colonizada (sin la línea de costa)
    lim = col.boundary.intersection(park.buffer(40 * M))
    lim = linemerge([x for x in parts(lim) if x.geom_type.endswith("LineString")]) if not lim.is_empty else lim
    for x in parts(lim):
        if x.geom_type.endswith("LineString") and x.length / M > 150:
            lp.append(F(x.simplify(8 * M), isla=isla, nombre="Límite del Parque Nacional Galápagos", fuente="Zonificación PNG 2017 (CGREG/FCD)"))
    for g, n in colon:
        if g.intersects(bx) and n == "RURAL":
            ag.append(F(g.simplify(8 * M, preserve_topology=True), isla=isla, nombre="Zona agrícola (suelo rural)",
                        area_km2=round(g.area / M**2 / 1e6, 1), fuente="Zonificación PNG 2017 (CGREG/FCD)"))
save("parque_nacional.geojson", pq)
save("parque_zonificacion.geojson", zp)
save("limite_parque.geojson", lp)
save("zona_agricola.geojson", ag)

# ───────────────────────── 2. Zonas inundables ─────────────────────────
NIV = {1: "Baja", 2: "Media", 3: "Alta"}
susc = []
for isla, k in REG.items():
    raw = {1: [], 2: [], 3: []}
    for f in load(f"dem/{k}_susc_inundacion.geojson"): raw[f["properties"]["nivel"]].append(shape(f["geometry"]))
    for lv in (1, 2, 3):                                  # polígonos acumulados: nivel ≥ lv
        u = unary_union(sum((raw[x] for x in (1, 2, 3) if x >= lv), [])).intersection(aoi[isla])
        u = suave(u)
        for p in parts(u):
            if p.area / M**2 < 1500: continue
            susc.append(F(p, isla=isla, nivel=lv, susceptibilidad=NIV[lv],
                          descripcion={3: "Hasta 1 m sobre el cauce", 2: "Hasta 2,5 m sobre el cauce", 1: "Hasta 5 m sobre el cauce"}[lv],
                          fuente="Modelo HAND (Copernicus GLO-30 + quebradas IGM)"))
save("susceptibilidad_inundacion.geojson", sorted(susc, key=lambda f: f["properties"]["nivel"]))

zi = []
for f in load("igm/terreno_inundable.geojson") + load("igm/lago_laguna.geojson"):
    g, isla = clip(shape(f["geometry"]))
    if g is None: continue
    t = "Terreno inundable" if f["properties"]["capa_igm"] == "terreno_inundable" else "Laguna o poza"
    zi.append(F(g, isla=isla, tipo=t, nombre=f["properties"].get("nam"), fuente="IGM 1:25 000"))
for f in load("final/riesgos_cgreg.geojson"):
    g, isla = clip(shape(f["geometry"]))
    if g is None: continue
    p = f["properties"]
    zi.append(F(g, isla=isla, tipo=p["tipo"].replace(" en el fenómeno del Niño", " (El Niño)"), localidad=p.get("localidad"), fuente="CGREG"))
save("zonas_inundables_oficiales.geojson", zi)

cb = []
for f in load("final/costa_baja.geojson"):
    g, isla = clip(shape(f["geometry"]))
    if g is None: continue
    for p in parts(suave(g, 10)):
        if p.area / M**2 >= 1500:
            cb.append(F(p, isla=isla, cota_max_m=f["properties"]["max_m"], clase=f["properties"]["clase"], fuente="Modelo (Copernicus GLO-30)"))
save("costa_baja.geojson", sorted(cb, key=lambda f: -f["properties"]["cota_max_m"]))
save("tsunami_inundacion.geojson", [F(shape(f["geometry"]).simplify(2 * M), isla=f["properties"]["isla"], localidad=f["properties"]["localidad"],
                                      clase=f["properties"]["clase"], fuente="SNGR / INOCAR") for f in load("final/tsunami_inundacion_inocar.geojson")])

# ───────────────────────── 3. Hidrografía ─────────────────────────
q_out, q_geoms = [], []
for f in load("final/quebradas.geojson"):
    g, isla = clip(shape(f["geometry"]))
    if g is None or g.length / M < 30: continue
    p = f["properties"]
    q_geoms.append(g)
    q_out.append(F(g, isla=isla, nombre=p.get("nombre"), regimen=(p.get("regimen") or "").title().replace("/", " / ") or None,
                   perenne=(p.get("regimen") or "").upper().endswith("PERENNE") and "NO PERENNE" not in (p.get("regimen") or "").upper()
                   and "INTERMITENTE" not in (p.get("regimen") or "").upper(), fuente=p["fuente"]))
save("quebradas.geojson", q_out)
qb = unary_union([g.buffer(45 * M, 2) for g in q_geoms])
dd = []
for f in load("final/drenaje_derivado.geojson"):
    g, isla = clip(shape(f["geometry"]))
    if g is None: continue
    rest = g.difference(qb)                               # solo lo que NO coincide con una quebrada mapeada
    for p in parts(rest):
        if p.geom_type.endswith("LineString") and p.length / M >= 80:
            dd.append(F(p.simplify(4 * M), isla=isla, orden=f["properties"]["orden"], area_drenada_km2=f["properties"]["area_drenada_km2"],
                        fuente="Modelo (Copernicus GLO-30), cauce no mapeado por el IGM"))
save("drenaje_adicional.geojson", dd)
fr = []
for f in load("final/quebradas_franja20m_cgreg.geojson"):
    g, isla = clip(shape(f["geometry"]))
    if g is not None: fr.append(F(g, isla=isla, tipo=f["properties"].get("tipo"), fuente="CGREG"))
save("franja_quebradas_20m.geojson", fr)
save("cuencas_localidad.geojson", [F(shape(f["geometry"]), **f["properties"]) for f in load("dem/cuencas_localidad.geojson")])
save("cuencas_aportantes.geojson", [F(shape(f["geometry"]), **{k: v for k, v in f["properties"].items() if k != "punto_entrada"})
                                    for f in load("dem/cuencas_aportantes.geojson")])

# ───────────────────────── 4. Población ─────────────────────────
save("limite_urbano.geojson", [F(shape(f["geometry"]), isla=f["properties"]["isla"], nombre=f["properties"].get("nam"),
                                 categoria=f["properties"].get("txt"), fuente="IGM 1:25 000") for f in load("igm/zona_urbana.geojson")])
save("barrios.geojson", [F(shape(f["geometry"]).simplify(2 * M), isla=f["properties"]["isla"], nombre=(f["properties"].get("nombre") or "").title(),
                           area_ha=f["properties"].get("area_ha"), fuente="CGREG") for f in load("final/barrios.geojson")])
save("manzanas_poblacion.geojson", [F(shape(f["geometry"]), isla=f["properties"]["isla"], codigo=f["properties"]["codigo"],
                                      viviendas=f["properties"].get("viviendas", 0), poblacion_estimada=f["properties"].get("pob_estimada", 0),
                                      fuente="INEC MGN 2026 + viviendas SNGR") for f in load("final/manzanas_inec.geojson")])
ex = []
for f in load("final/edificios_exposicion.geojson"):
    p = f["properties"]
    if not (p["susc_inundacion"] or p["zona_tsunami"] or p["franja_quebrada"] or p.get("cota_costera_m") == 3): continue
    ex.append(F(shape(f["geometry"]), isla=p["isla"], nombre=p.get("nombre"), susc_inundacion=p["susc_inundacion"],
                zona_tsunami=p["zona_tsunami"], franja_quebrada=p["franja_quebrada"], costa_0_3m=p.get("cota_costera_m") == 3, fuente=p["fuente"]))
save("edificios_expuestos.geojson", ex)

# ───────────────────────── 5. Vías ─────────────────────────
JER = {"primary": "Principal", "primary_link": "Principal", "trunk": "Principal", "secondary": "Secundaria", "secondary_link": "Secundaria",
       "tertiary": "Secundaria", "tertiary_link": "Secundaria", "track": "Camino de tierra"}
vv = []
for f in vias_osm:
    g, isla = clip(shape(f["geometry"]))
    if g is None: continue
    p = f["properties"]
    vv.append(F(g, isla=isla, nombre=p.get("name"), jerarquia=JER.get(p["highway"], "Local"), tipo_osm=p["highway"], superficie=p.get("surface"),
                puente=p.get("bridge") == "yes" or None, fuente="OSM 31-oct-2026"))
save("vias.geojson", vv)
save("rutas_evacuacion_tsunami.geojson", [F(shape(f["geometry"]), isla=f["properties"]["isla"], tipo=(f["properties"].get("tipo") or "").title(),
                                          via=f["properties"].get("via"), fuente="SNGR") for f in load("final/tsunami_rutas_evacuacion.geojson")])

# ───────────────────────── 6. Puntos clave (unificados y sin duplicados) ─────────────────────────
susc_hi = unary_union([shape(f["geometry"]) for f in susc if f["properties"]["nivel"] >= 2])
tsu = unary_union([shape(f["geometry"]) for f in load("final/tsunami_inundacion_inocar.geojson")]).buffer(0)
pts = []
def add_pt(g, cat, nombre, subtipo, fuente, **extra):
    if g.geom_type != "Point": g = g.representative_point()
    if not AOI.contains(g): return
    pts.append((g, dict(categoria=cat, nombre=(nombre or None), subtipo=subtipo, fuente=fuente, **extra)))
for f in load("final/salud_msp.geojson"):
    p = f["properties"]
    publico = p.get("institucion") not in ("PRIVADO", "OTROS ESTABLECIMIENTOS")
    mayor = any(t in (p.get("tipologia") or "") for t in ("HOSPITAL", "CENTRO DE SALUD", "CENTRO DE ESPECIALIDADES"))
    add_pt(shape(f["geometry"]), "salud" if publico or mayor else "salud_privada", (p.get("nombre") or "").title(), (p.get("tipologia") or "").capitalize(), "MSP 2023",
                                institucion=p.get("institucion"), nivel=p.get("nivel"))
for f in load("final/albergues_sngr.geojson"):
    p = f["properties"]; add_pt(shape(f["geometry"]), "albergue", p.get("nombre"), p.get("tipo"), "SNGR 2025",
                                capacidad_personas=p.get("capacidad_personas"), capacidad_familias=p.get("capacidad_familias"))
for f in load("final/tsunami_zonas_seguras.geojson"):
    p = f["properties"]; add_pt(shape(f["geometry"]), "zona_segura", (p.get("nombre") or "").title(), (p.get("tipo") or "").capitalize(), "SNGR",
                                capacidad=p.get("capacidad"))
for f in load("final/tsunami_sirenas.geojson"):
    p = f["properties"]; add_pt(shape(f["geometry"]), "sirena", p.get("codigo"), p.get("referencia"), "SNGR SAT")
for f in load("final/educacion_mineduc.geojson"):
    p = f["properties"]; add_pt(shape(f["geometry"]), "educacion", (p.get("nom_instit") or p.get("nombre") or "").title(), (p.get("nom_sosten") or "").capitalize(), "MINEDUC 2021")
MAP = {"salud": "salud", "emergencia": "emergencia", "refugio": "albergue", "educacion": "educacion", "gobierno": "gobierno", "agua": "agua",
       "energia": "energia", "transporte": "transporte", "telecom": "telecom", "abastecimiento": "abastecimiento", "alojamiento": "alojamiento",
       "encuentro": "encuentro", "otros": "otros"}
for f in load("final/puntos_clave.geojson"):
    p = f["properties"]
    if p["categoria"] == "refugio" and p.get("subtipo") in ("shelter",): continue   # paradas/techos en OSM, no albergues
    cat = MAP[p["categoria"]]
    if cat == "salud" and p.get("subtipo") not in ("hospital", "clinic"): cat = "salud_privada"
    add_pt(shape(f["geometry"]), cat, p.get("nombre"), p.get("subtipo"), p["fuente"])
# deduplicar: misma categoría a < 40 m → conserva la fuente oficial (orden de llegada)
keep = []
for g, p in pts:
    if any(q["categoria"] == p["categoria"] and g.distance(h) < 40 * M for h, q in keep): continue
    keep.append((g, p))
out = []
for g, p in keep:
    p["isla"] = isla_de(g)
    p["en_susc_alta_media"] = bool(susc_hi.contains(g)) or None
    p["en_zona_tsunami"] = bool(tsu.contains(g)) or None
    out.append(F(g, **p))
save("puntos_clave.geojson", out)

# ───────────────────────── 7. Topografía ─────────────────────────
cv = []
for isla, k in REG.items():
    with rasterio.open(ROOT / f"descargas/dem_recortes/{k}_dem.tif") as d:
        z = d.read(1).astype("float64"); tr = d.transform
    sea = z <= 0
    zs = gaussian_filter(np.where(sea, 0, z), 1.2)
    H, W = z.shape
    xs = tr.c + tr.a * (np.arange(W) + .5); ys = tr.f + tr.e * (np.arange(H) + .5)
    cg = contourpy.contour_generator(xs, ys, zs, line_type="Separate")
    for lv in range(10, int(zs.max()) + 1, 10):
        for seg in cg.lines(lv):
            if len(seg) < 5: continue
            g = LineString(seg).simplify(6 * M)
            g = g.intersection(aoi[isla])
            for p in parts(g):
                if p.length / M >= 60:
                    cv.append(F(p, isla=isla, elevacion_m=lv, maestra=lv % 50 == 0))
    # relieve sombreado completo (contexto) + máscara del área de interés
    lim = json.loads((C / "raster/limites.json").read_text())[k]["bounds"]
    Image.open(C / f"raster/{k}_relieve.png").save(OUT / f"raster/{k}_relieve.png", optimize=True)
    mask = features.rasterize([(aoi[isla], 1)], out_shape=(H, W), transform=tr).astype(bool)
    im = np.array(Image.open(C / f"raster/{k}_pendientes.png")); im[~mask] = 0
    Image.fromarray(im, "RGBA").save(OUT / f"raster/{k}_pendientes.png", optimize=True)
save("curvas_nivel.geojson", cv)
lim = json.loads((C / "raster/limites.json").read_text())
(OUT / "raster/limites.json").write_text(json.dumps(lim, ensure_ascii=False, indent=1))

# resumen de exposición (se copia tal cual)
(OUT / "resumen_exposicion.json").write_text((C / "final/resumen_exposicion.json").read_text())
(OUT / "_conteos.json").write_text(json.dumps(manifest_sizes, indent=1))
tot = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
print(f"Total paquete: {tot / 1e6:.1f} MB")

# capa operativa (la mantiene el COE / coordinación; se copia tal cual)
(OUT / "areas_afectadas.geojson").write_text((C / "operativas/areas_afectadas.geojson").read_text())
manifest_sizes["areas_afectadas.geojson"] = len(json.loads((C / "operativas/areas_afectadas.geojson").read_text())["features"])

# ───────────────────────── 8. Manifiesto ─────────────────────────
man = json.loads((ROOT / "scripts/capas.json").read_text())
man["generado"] = __import__("datetime").date.today().isoformat()
for g in man["grupos"]:
    for c in g["capas"]:
        if c.get("archivo"):
            assert (OUT / c["archivo"]).exists(), f"falta {c['archivo']}"
            c["elementos"] = manifest_sizes.get(c["archivo"])
(OUT / "capas.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
print("  capas.json OK")
