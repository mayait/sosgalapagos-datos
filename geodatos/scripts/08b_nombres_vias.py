"""Puntos de rótulo para los nombres de calles, a partir de vias.geojson ya exportado.

Une los tramos con el mismo nombre (por isla) y pone un rótulo en el medio de cada
calle, repetido cada ~400 m en las largas. El mapa los muestra solo de cerca
(zoom_min en capas.json), sin depender de mapas base con rótulos.

Uso: .venv/bin/python -I scripts/08b_nombres_vias.py [carpeta]   (por defecto export/galapagos)
"""
import json, pathlib, sys
from collections import defaultdict
from shapely.geometry import shape, mapping
from shapely.ops import linemerge, unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIR = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "export" / "galapagos"
M = 1 / 111320            # grados por metro en el ecuador
MIN_M, CADA_M = 60, 400   # largo mínimo para rotular y separación entre rótulos

feats = json.loads((DIR / "vias.geojson").read_text())["features"]
por_calle = defaultdict(list)
for f in feats:
    p = f["properties"]
    if p.get("nombre"):
        por_calle[(p.get("isla"), p["nombre"])].append(shape(f["geometry"]))

out = []
for (isla, nombre), geoms in sorted(por_calle.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
    u = unary_union(geoms)
    merged = linemerge(u) if u.geom_type == "MultiLineString" else u
    for line in getattr(merged, "geoms", [merged]):
        largo = line.length / M
        if largo < MIN_M:
            continue
        n = max(1, int(largo // CADA_M))
        for i in range(n):
            pt = line.interpolate((i + 0.5) / n, normalized=True)
            out.append({"type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [round(pt.x, 5), round(pt.y, 5)]},
                        "properties": {"nombre": nombre, "isla": isla}})

(DIR / "nombres_vias.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": out}, ensure_ascii=False, separators=(",", ":")))
print(f"nombres_vias.geojson: {len(out)} rótulos de {len(por_calle)} calles")
