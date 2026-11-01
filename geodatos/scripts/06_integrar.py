"""Integra OSM + IGM + derivados del DEM en capas listas para el mapa de emergencia (capas/final/)."""
import json, pathlib
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
ROOT = pathlib.Path(__file__).resolve().parents[1]
C = ROOT / "capas"; OUT = C / "final"; OUT.mkdir(exist_ok=True)
def load(p): return json.loads((C / p).read_text())["features"]
def save(name, feats):
    (OUT / name).write_text(json.dumps({"type":"FeatureCollection","features":feats}, ensure_ascii=False, separators=(",",":")))
    print(f"{name:34s} {len(feats):6d}  {(OUT/name).stat().st_size/1e6:.1f} MB")
REG = {"Santa Cruz": "santa_cruz", "San Cristóbal": "san_cristobal", "Isabela": "isabela_sur"}
M = 1/111320  # grados por metro (ecuador)

# ---------- 1. Zonas pobladas ----------
urb = load("igm/zona_urbana.geojson"); osm_z = load("osm/zonas_pobladas.geojson")
bld_osm = load("osm/edificios.geojson"); bld_igm = load("igm/edificio_p.geojson") + load("igm/edificio_a.geojson")
zonas = []
for f in urb:
    p = f["properties"]
    zonas.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"nombre":p.get("nam"),
                  "tipo":"Límite urbano IGM","detalle":p.get("txt"),"fuente":"IGM 1:25 000"}})
for f in osm_z:
    p = f["properties"]
    if p.get("place") in ("island","islet","archipelago","ocean","sea"): continue
    t = p.get("landuse") or ("lugar: " + p["place"] if p.get("place") else "")
    zonas.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"nombre":p.get("name"),
                  "tipo":f"OSM {t}","fuente":"OpenStreetMap 31-oct-2026"}})
# huella edificada: buffer 35 m de cada edificio, unión, erosión 20 m, ≥ 1 ha
for isla in REG:
    gs = [shape(f["geometry"]).buffer(35*M, 4) for f in bld_osm + bld_igm if f["properties"]["isla"] == isla]
    u = unary_union(gs).buffer(-20*M, 4)
    for part in getattr(u, "geoms", [u]):
        if part.area / M**2 < 10000: continue
        n = sum(1 for g in gs if part.intersects(g.centroid))
        zonas.append({"type":"Feature","geometry":mapping(part.simplify(5*M)),"properties":{"isla":isla,
            "tipo":"Huella edificada","edificios":n,"area_ha":round(part.area/M**2/1e4,1),
            "fuente":"Derivada de edificios OSM + IGM (buffer 35 m)"}})
save("zonas_pobladas.geojson", zonas)

# ---------- 2. Susceptibilidad a inundación (vector solo cerca de zonas pobladas) ----------
pobl = unary_union([shape(z["geometry"]) for z in zonas if z["properties"]["tipo"] != "OSM farmyard"]).buffer(1000*M)
susc = []
for isla, k in REG.items():
    for f in load(f"dem/{k}_susc_inundacion.geojson"):
        g = shape(f["geometry"])
        if not g.intersects(pobl): continue
        g = g.intersection(pobl)
        if g.is_empty or g.area/M**2 < 1500: continue
        susc.append({"type":"Feature","geometry":mapping(g),"properties":f["properties"]})
save("susceptibilidad_inundacion_zonas_pobladas.geojson", susc)
costa = []
for isla, k in REG.items(): costa += load(f"dem/{k}_costa_baja.geojson")
save("costa_baja.geojson", costa)

# ---------- 3. Exposición de edificios ----------
s_geoms = [shape(f["geometry"]) for f in susc]; s_tree = STRtree(s_geoms)
c_geoms = [shape(f["geometry"]) for f in costa]; c_tree = STRtree(c_geoms)
expo, resumen = [], {}
for f in bld_osm:
    g = shape(f["geometry"]); pt = g.representative_point(); p = f["properties"]
    nv = max([susc[i]["properties"]["nivel"] for i in s_tree.query(g, predicate="intersects")], default=0)
    cb = min([costa[i]["properties"]["max_m"] for i in c_tree.query(pt, predicate="intersects")], default=None)
    q = {"isla": p["isla"], "tipo": p.get("building"), "nombre": p.get("name"), "osm_id": p["osm_id"],
         "susc_inundacion": nv, "cota_costera_m": cb}
    expo.append({"type":"Feature","geometry":mapping(g.simplify(1*M)),"properties":q})
    r = resumen.setdefault(p["isla"], {"edificios":0,"susc_alta":0,"susc_media":0,"susc_baja":0,"costa_0_3m":0,"costa_3_5m":0})
    r["edificios"] += 1
    if nv: r[{3:"susc_alta",2:"susc_media",1:"susc_baja"}[nv]] += 1
    if cb == 3: r["costa_0_3m"] += 1
    if cb == 5: r["costa_3_5m"] += 1
save("edificios_exposicion.geojson", expo)
(OUT/"resumen_exposicion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1)); print(resumen)

# ---------- 4. Puntos clave ----------
pts = []
for f in load("osm/servicios.geojson"):
    p = f["properties"]
    sub = p.get("amenity") or p.get("healthcare") or p.get("emergency") or p.get("shop") or p.get("tourism") or p.get("man_made") or p.get("power") or p.get("aeroway") or p.get("leisure") or p.get("office")
    pts.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"categoria":p["categoria"],"subtipo":sub,
                "nombre":p.get("name"),"fuente":"OSM","osm_id":p["osm_id"]}})
IGM_PTS = {"aeropuertos":("transporte","aeropuerto"),"pista_aterrizaje":("transporte","pista"),"muelle_a":("transporte","muelle"),
           "muelle_l":("transporte","muelle"),"faro":("transporte","faro"),"central_electrica":("energia","central eléctrica"),
           "tanque":("agua","tanque"),"torre_agua":("agua","torre de agua"),"pozo":("agua","pozo"),"manantial":("agua","manantial"),
           "acueducto":("agua","acueducto"),"estadio":("encuentro","estadio"),"cementerio":("otros","cementerio"),
           "torre_comunicacion":("telecom","torre de comunicación"),"antena_parabolica":("telecom","antena"),
           "procesamiento_residuos":("otros","procesamiento de residuos"),"vertedero_basurero":("otros","botadero"),
           "puente_l":("transporte","puente"),"puente_p":("transporte","puente")}
for capa, (cat, sub) in IGM_PTS.items():
    p_ = C / f"igm/{capa}.geojson"
    if not p_.exists(): continue
    for f in load(f"igm/{capa}.geojson"):
        g = shape(f["geometry"]); pt = g if g.geom_type == "Point" else g.representative_point()
        pts.append({"type":"Feature","geometry":mapping(pt),"properties":{"isla":f["properties"]["isla"],"categoria":cat,"subtipo":sub,
                    "nombre":f["properties"].get("nam") or f["properties"].get("txt"),"fuente":"IGM 1:25 000"}})
for f in load("igm/edificio_p.geojson"):
    p = f["properties"]
    if p.get("ebt_desc") not in (None,"NO APLICABLE","DESCONOCIDO"):
        pts.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"categoria":"educacion","subtipo":p["ebt_desc"].lower(),"nombre":p.get("nam"),"fuente":"IGM 1:25 000"}})
    elif p.get("hwt_desc") not in (None,"NO APLICABLE","DESCONOCIDO"):
        pts.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"categoria":"encuentro","subtipo":p["hwt_desc"].lower(),"nombre":p.get("nam"),"fuente":"IGM 1:25 000"}})
# marca si el punto cae en zona susceptible
for f in pts:
    g = shape(f["geometry"])
    f["properties"]["susc_inundacion"] = max([susc[i]["properties"]["nivel"] for i in s_tree.query(g, predicate="intersects")], default=0)
    f["properties"]["cota_costera_m"] = min([costa[i]["properties"]["max_m"] for i in c_tree.query(g, predicate="intersects")], default=None)
save("puntos_clave.geojson", pts)

# ---------- 5. Hidrografía y vías ----------
rios = []
for f in load("igm/rio.geojson"):
    p = f["properties"]; rios.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"nombre":p.get("nam"),
        "regimen":(p.get("hyc_desc") or "").replace("/ ","/"),"fuente":"IGM 1:25 000"}})
for f in load("osm/hidro_lineas.geojson"):
    p = f["properties"]; rios.append({"type":"Feature","geometry":f["geometry"],"properties":{"isla":p["isla"],"nombre":p.get("name"),
        "regimen":p.get("waterway"),"intermitente":p.get("intermittent"),"fuente":"OSM"}})
save("quebradas.geojson", rios)
dren = []
for isla, k in REG.items(): dren += load(f"dem/{k}_drenaje_derivado.geojson")
save("drenaje_derivado.geojson", [f for f in dren if f["properties"]["area_drenada_km2"] >= 0.2])
cu = []
for isla, k in REG.items(): cu += load(f"dem/{k}_cuencas.geojson")
save("cuencas.geojson", cu)
cv = []
for isla, k in REG.items(): cv += load(f"dem/{k}_curvas.geojson")
save("curvas_nivel.geojson", cv)
