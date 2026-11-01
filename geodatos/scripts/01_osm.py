"""Descarga capas OSM (Overpass) para Santa Cruz, San Cristóbal e Isabela."""
import json, sys, time, pathlib, requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "descargas" / "osm"
OUT.mkdir(parents=True, exist_ok=True)

# bbox: sur, oeste, norte, este
ISLAS = {
    "santa_cruz":    (-0.80, -90.56, -0.42, -90.15),   # incluye Baltra
    "san_cristobal": (-0.97, -89.66, -0.66, -89.22),
    "isabela":       (-1.10, -91.67,  0.18, -90.76),
}

GRUPOS = {
 "vias": 'way["highway"]',
 "hidro": ['way["waterway"]', 'nwr["natural"~"water|spring|wetland|bay"]', 'nwr["water"]', 'nwr["landuse"="reservoir"]',
           'nwr["man_made"~"water_tower|water_works|wastewater_plant|reservoir_covered|storage_tank|water_well|pumping_station"]'],
 "poblado": ['nwr["landuse"~"residential|commercial|retail|industrial|farmyard|construction"]', 'nwr["place"]',
             'rel["boundary"="administrative"]', 'nwr["boundary"="protected_area"]', 'rel["boundary"="national_park"]'],
 "edificios": 'nwr["building"]',
 "servicios": ['nwr["amenity"]', 'nwr["healthcare"]', 'nwr["emergency"]', 'nwr["aeroway"~"aerodrome|helipad|terminal"]',
               'nwr["power"~"plant|substation|generator"]', 'nwr["man_made"~"pier|breakwater|antenna|mast|communications_tower"]',
               'nwr["office"="government"]', 'nwr["leisure"~"stadium|sports_centre|pitch"]', 'nwr["tourism"~"hotel|hostel|guest_house"]',
               'nwr["shop"~"supermarket|hardware|convenience"]', 'nwr["harbour"]', 'nwr["seamark:type"~"harbour"]'],
 "islas": ['nwr["place"~"island|islet"]'],
}

URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]

def run(q):
    for attempt in range(4):
        url = URLS[attempt % len(URLS)]
        try:
            r = requests.post(url, data={"data": q}, timeout=300, headers={"User-Agent": "ResponseGrid-Galapagos/1.0 (emergencia)"})
            if r.status_code == 200:
                return r.json()
            print("  HTTP", r.status_code, url, file=sys.stderr)
        except Exception as e:
            print("  err", e, file=sys.stderr)
        time.sleep(10)
    raise RuntimeError("Overpass falló")

for isla, (s, w, n, e) in ISLAS.items():
    for g, sel in GRUPOS.items():
        sel = sel if isinstance(sel, list) else [sel]
        f = OUT / f"{isla}_{g}.osm.json"
        if f.exists(): continue
        body = "".join(f"{x}({s},{w},{n},{e});" for x in sel)
        q = f"[out:json][timeout:240];({body});out body geom;"
        d = run(q)
        f.write_text(json.dumps(d))
        print(isla, g, len(d.get("elements", [])))
        time.sleep(2)
