"""Extrae capas temáticas de OSM (Geofabrik Ecuador) para Santa Cruz, San Cristóbal e Isabela.
Uso: .venv/bin/python -I scripts/02_osm_extraer.py descargas/osm/ecuador-latest.osm.pbf
"""
import json, sys, pathlib
import osmium
from shapely.geometry import shape, mapping, box

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "capas" / "osm"; OUT.mkdir(parents=True, exist_ok=True)
PBF = sys.argv[1]

# oeste, sur, este, norte
ISLAS = {
    "Santa Cruz":    (-90.56, -0.80, -90.15, -0.42),   # incluye Baltra
    "San Cristóbal": (-89.66, -0.97, -89.22, -0.66),
    "Isabela":       (-91.67, -1.10, -90.76,  0.18),
}
BOXES = {k: box(*v) for k, v in ISLAS.items()}

def isla_de(lon, lat):
    for k, (w, s, e, n) in ISLAS.items():
        if w <= lon <= e and s <= lat <= n:
            return k
    return None

SERV = [  # (categoría, función de prueba)
 ("salud",       lambda t: t.get("amenity") in ("hospital","clinic","doctors","pharmacy","dentist") or "healthcare" in t),
 ("emergencia",  lambda t: t.get("amenity") in ("police","fire_station","ranger_station") or "emergency" in t and t.get("emergency") not in ("no","yes")),
 ("refugio",     lambda t: t.get("amenity") in ("shelter","community_centre","social_facility") or t.get("emergency")=="assembly_point"),
 ("educacion",   lambda t: t.get("amenity") in ("school","college","university","kindergarten")),
 ("gobierno",    lambda t: t.get("amenity") in ("townhall","courthouse") or t.get("office")=="government"),
 ("agua",        lambda t: t.get("amenity") in ("drinking_water","water_point") or t.get("man_made") in ("water_tower","water_works","wastewater_plant","reservoir_covered","storage_tank","water_well","pumping_station") or t.get("natural")=="spring"),
 ("energia",     lambda t: t.get("power") in ("plant","substation","generator") or t.get("amenity")=="fuel"),
 ("transporte",  lambda t: t.get("aeroway") in ("aerodrome","helipad","terminal") or t.get("amenity") in ("ferry_terminal","bus_station") or t.get("man_made") in ("pier",) or "harbour" in t),
 ("telecom",     lambda t: t.get("man_made") in ("mast","antenna","communications_tower")),
 ("abastecimiento", lambda t: t.get("shop") in ("supermarket","hardware","convenience") or t.get("amenity") in ("marketplace","bank","atm")),
 ("alojamiento", lambda t: t.get("tourism") in ("hotel","hostel","guest_house")),
 ("encuentro",   lambda t: t.get("leisure") in ("stadium","sports_centre") or t.get("amenity")=="place_of_worship"),
]
def cat_servicio(t):
    for c, f in SERV:
        try:
            if f(t): return c
        except Exception: pass
    return None

KEEP = ("name","highway","surface","waterway","intermittent","natural","water","landuse","place","building",
        "amenity","healthcare","emergency","shop","tourism","office","man_made","power","aeroway","leisure",
        "operator","addr:street","levels","building:levels","boundary","protect_class","admin_level","population","tunnel","bridge","layer")
def props(t, **extra):
    p = {k: t[k] for k in KEEP if k in t}
    p.update(extra); return p

F = osmium.geom.GeoJSONFactory()
layers = {k: [] for k in ["vias","hidro_lineas","hidro_areas","costa","zonas_pobladas","lugares","edificios","servicios","limites","islas"]}

def add(layer, gjson, t, isla, osmid, **extra):
    layers[layer].append({"type":"Feature","geometry":json.loads(gjson) if isinstance(gjson,str) else gjson,
                          "properties": props(t, isla=isla, osm_id=osmid, **extra)})

def way_isla(w):
    for n in w.nodes:
        if n.location.valid():
            i = isla_de(n.location.lon, n.location.lat)
            if i: return i
    return None

class H(osmium.SimpleHandler):
    def node(self, n):
        t = dict(n.tags)
        if not t: return
        i = isla_de(n.location.lon, n.location.lat)
        if not i: return
        g = F.create_point(n)
        if "place" in t: add("lugares", g, t, i, f"n{n.id}")
        c = cat_servicio(t)
        if c: add("servicios", g, t, i, f"n{n.id}", categoria=c)
    def way(self, w):
        t = dict(w.tags)
        if not t or not ("highway" in t or "waterway" in t or t.get("natural")=="coastline"): return
        i = way_isla(w)
        if not i: return
        try: g = F.create_linestring(w)
        except Exception: return
        if "highway" in t: add("vias", g, t, i, f"w{w.id}")
        elif "waterway" in t and t["waterway"] not in ("riverbank",): add("hidro_lineas", g, t, i, f"w{w.id}")
        elif t.get("natural")=="coastline": add("costa", g, t, i, f"w{w.id}")
    def area(self, a):
        t = dict(a.tags)
        if not t: return
        want = ("building" in t or t.get("landuse") in ("residential","commercial","retail","industrial","farmyard","construction","reservoir","basin")
                or t.get("natural") in ("water","wetland") or "water" in t or "place" in t or t.get("boundary") in ("administrative","protected_area","national_park")
                or cat_servicio(t))
        if not want: return
        i = None
        for ring in a.outer_rings():
            for n in ring:
                if n.location.valid():
                    i = isla_de(n.location.lon, n.location.lat)
                    if i: break
            if i: break
        big = t.get("boundary") in ("administrative","protected_area","national_park")
        if not i and not big: return
        try: g = json.loads(F.create_multipolygon(a))
        except Exception: return
        oid = ("w" if a.from_way() else "r") + str(a.orig_id())
        if big:
            if t.get("boundary")=="administrative" and t.get("admin_level") not in ("4","6","8"): return
            s = shape(g)
            for isl, b in BOXES.items():
                if s.intersects(b):
                    c = s.intersection(b).simplify(0.0003)
                    if not c.is_empty: add("limites", mapping(c), t, isl, oid)
            return
        if "building" in t:
            add("edificios", g, t, i, oid)
        elif t.get("place") in ("island","islet"):
            add("islas", g, t, i, oid)
        elif t.get("landuse") in ("residential","commercial","retail","industrial","farmyard","construction") or "place" in t:
            add("zonas_pobladas", g, t, i, oid)
        elif t.get("natural") in ("water","wetland") or "water" in t or t.get("landuse") in ("reservoir","basin"):
            add("hidro_areas", g, t, i, oid)
        c = cat_servicio(t)
        if c and "building" not in t or (c and "building" in t):
            if c:
                cen = shape(g).representative_point()
                add("servicios", mapping(cen), t, i, oid, categoria=c)

H().apply_file(PBF, locations=True, idx="flex_mem")
for k, feats in layers.items():
    (OUT / f"{k}.geojson").write_text(json.dumps({"type":"FeatureCollection","features":feats}, ensure_ascii=False))
    by = {}
    for f in feats: by[f["properties"]["isla"]] = by.get(f["properties"]["isla"],0)+1
    print(f"{k:16s} {len(feats):6d}  {by}")
