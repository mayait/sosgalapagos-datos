"""Descarga todas las capas del WFS IGM Galápagos 1:25 000 a GeoJSON (EPSG:4326)."""
import re, json, sys, pathlib, requests, time
from concurrent.futures import ThreadPoolExecutor
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "descargas" / "igm"; OUT = RAW / "wfs"; OUT.mkdir(parents=True, exist_ok=True)
URL = "https://www.geoportaligm.gob.ec/galapagos25/ows"
caps = (RAW / "wfs_caps.xml").read_text(encoding="utf-8", errors="replace")
names = re.findall(r"<(?:wfs:)?Name>(igm:[^<]+)</", caps)
def get(n):
    f = OUT / (n.split(":")[1] + ".geojson")
    if f.exists() and f.stat().st_size > 100: return n, "cache", json.loads(f.read_text()).get("features", []).__len__()
    for i in range(3):
        try:
            r = requests.get(URL, params={"service":"WFS","version":"2.0.0","request":"GetFeature","typeNames":n,
                                          "outputFormat":"application/json","srsName":"EPSG:4326"}, timeout=600)
            if r.ok and r.text.lstrip().startswith("{"):
                f.write_bytes(r.content); return n, "ok", len(r.json().get("features", []))
            err = r.text[:200]
        except Exception as e: err = str(e)
        time.sleep(5)
    return n, "ERROR " + err, 0
with ThreadPoolExecutor(4) as ex:
    for n, st, c in ex.map(get, names): print(f"{n:38s} {st:6s} {c}", flush=True)
