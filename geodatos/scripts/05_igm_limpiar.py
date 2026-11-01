"""Depura las capas IGM 1:25 000: quita duplicados (hojas superpuestas), deja solo Santa Cruz (+Baltra),
San Cristóbal e Isabela, normaliza el nombre de la isla y guarda en capas/igm/."""
import json, pathlib, hashlib
from shapely.geometry import shape
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "descargas/igm/wfs"; OUT = ROOT / "capas/igm"; OUT.mkdir(parents=True, exist_ok=True)
def isla(v):
    v = (v or "").upper()
    if "SANTA CRUZ" in v or "BALTRA" in v: return "Santa Cruz"
    if "CRIST" in v: return "San Cristóbal"
    if "ISABELA" in v: return "Isabela"
    return None
BBOX = {"Santa Cruz": (-90.56,-0.80,-90.15,-0.42), "San Cristóbal": (-89.66,-0.97,-89.22,-0.66), "Isabela": (-91.67,-1.10,-90.76,0.18)}
def isla_geo(g):
    p = g.representative_point()
    for k,(w,s,e,n) in BBOX.items():
        if w<=p.x<=e and s<=p.y<=n: return k
DROP = {"gid","igds_color","igds_graph","igds_style","igds_weigh","Shape_Leng","Shape_Area","OBJECTID"}
resumen = {}
for f in sorted(SRC.glob("*.geojson")):
    d = json.loads(f.read_text()); seen = set(); out = []
    for ft in d["features"]:
        if not ft.get("geometry"): continue
        g = shape(ft["geometry"])
        i = isla(ft["properties"].get("isla")) or (isla_geo(g) if not ft["properties"].get("isla") else None)
        if not i: continue
        h = hashlib.md5(g.wkb).hexdigest()
        if h in seen: continue
        seen.add(h)
        p = {k: v for k, v in ft["properties"].items() if k not in DROP and v not in (None, "", 999)}
        p["isla"] = i; p["capa_igm"] = f.stem
        geo = ft["geometry"]
        if f.stem == "punto_acotado_p": geo = {"type":"Point","coordinates":[round(c,6) for c in ft["geometry"]["coordinates"][:2]]}; p = {"isla": i, "z": ft["properties"].get("zv2")}
        out.append({"type":"Feature","geometry":geo,"properties":p})
    if out:
        (OUT / f.name).write_text(json.dumps({"type":"FeatureCollection","features":out}, ensure_ascii=False, separators=(",",":")))
    by = {}
    for o in out: by[o["properties"]["isla"]] = by.get(o["properties"]["isla"],0)+1
    resumen[f.stem] = {"original": len(d["features"]), "depurado": len(out), "por_isla": by}
    print(f"{f.stem:30s} {len(d['features']):6d} → {len(out):6d} {by}")
(ROOT/"capas/igm/_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
