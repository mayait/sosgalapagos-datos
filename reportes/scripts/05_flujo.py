#!/usr/bin/env python3
"""Paso 5 · Capa «Por dónde bajó el agua» (flujo observado) de un evento.

Lee `eventos/<evento>/flujo_observado.json` (fuente editable: tramos sobre calles de OSM o vértices libres) y
`geodatos/capas/osm/vias.geojson`, y escribe `eventos/<evento>/flujo_observado.geojson` (EPSG:4326, 6 decimales):
  - una línea por elemento de tipo «flujo» o «salida», en el sentido del agua;
  - un polígono por elemento de tipo «remolino» (agua arremolinada o empozada);
  - puntas de flecha (tipo «flecha», en V) cada ~45 m y al final de cada línea, para que el sentido se vea en el mapa.

Es un trazo observado a partir de reportes y videos, sin levantamiento en campo: no es un dato oficial.
Valida que ningún texto traiga teléfonos (misma expresión que 03_publicar.py).

    geodatos/.venv/bin/python -I reportes/scripts/05_flujo.py [--evento 2026-11-21]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, mapping, shape
from shapely.ops import linemerge, substring, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import RAIZ, REPO, RE_TELEFONO, EVENTO_POR_DEFECTO  # noqa: E402

VIAS = REPO / "geodatos" / "capas" / "osm" / "vias.geojson"
M_LAT = 110_574.0                       # m por grado de latitud
M_LON = 111_320.0 * math.cos(math.radians(0.74))
CADA_M, BRAZO_M, ANGULO = 45.0, 7.0, 28.0


def r6(g):
    return json.loads(json.dumps(mapping(g)), parse_float=lambda s: round(float(s), 6))


def a_m(g):      # grados → metros locales (para medir y cortar)
    from shapely.affinity import scale
    return scale(g, M_LON, M_LAT, origin=(0, 0))


def a_grados(g):
    from shapely.affinity import scale
    return scale(g, 1 / M_LON, 1 / M_LAT, origin=(0, 0))


def tramo_via(vias, t):
    lineas = [g for n, g in vias if n == t["via"]]
    if not lineas: raise SystemExit(f"No hay ninguna vía «{t['via']}» en {VIAS}")
    a, b = Point(t["desde_lonlat"]), Point(t["hasta_lonlat"])
    m = linemerge(unary_union(lineas))
    partes = list(getattr(m, "geoms", [m]))
    linea = min(partes, key=lambda l: l.distance(a) + l.distance(b))
    for p in (a, b):
        if a_m(linea).distance(a_m(p)) > 30: raise SystemExit(f"{t['via']}: el punto {list(p.coords)[0]} queda a más de 30 m de la calle")
    lm = a_m(linea)
    da, db = lm.project(a_m(a)), lm.project(a_m(b))
    seg = substring(lm, da, db) if da < db else substring(lm, db, da).reverse()
    return list(a_grados(seg).coords)


def flechas(linea_g):
    """Puntas de flecha en V a lo largo de la línea (en grados), cada CADA_M y en el extremo final."""
    lm = a_m(linea_g); L = lm.length; out = []
    pos = [d for d in [CADA_M * k for k in range(1, int(L // CADA_M) + 1)] if d < L - 15] + [L]
    for d in pos:
        p, q = lm.interpolate(max(d - 3, 0)), lm.interpolate(d)
        ang = math.atan2(q.y - p.y, q.x - p.x)
        brazos = [(q.x - BRAZO_M * math.cos(ang + s * math.radians(ANGULO)), q.y - BRAZO_M * math.sin(ang + s * math.radians(ANGULO))) for s in (1, -1)]
        out.append(a_grados(LineString([brazos[0], (q.x, q.y), brazos[1]])))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--evento", default=EVENTO_POR_DEFECTO); arg = ap.parse_args()
    d = RAIZ / "eventos" / arg.evento
    src = json.loads((d / "flujo_observado.json").read_text())
    vias = [(f["properties"].get("name"), shape(f["geometry"])) for f in json.loads(VIAS.read_text())["features"]
            if f["properties"].get("isla") in (None, "Santa Cruz")]
    feats = []
    for e in src["elementos"]:
        for k in ("nombre", "detalle"):
            if RE_TELEFONO.search(e.get(k, "")): raise SystemExit(f"{e['id']}: «{k}» trae un número de teléfono")
        coords = []
        for t in e["tramos"]:
            c = tramo_via(vias, t) if "via" in t else [tuple(p) for p in t["puntos_lonlat"]]
            coords += c if not coords or coords[-1] != c[0] else c[1:]
        props = {"id": e["id"], "nombre": e["nombre"], "tipo": e["tipo"], "detalle": e["detalle"],
                 "reportes": ", ".join(e.get("reportes", [])), "fuente": src["fuente"]}
        if e["tipo"] == "remolino":
            g = Polygon(coords).buffer(0)
            props["area_m2"] = round(a_m(g).area)
            feats.append({"type": "Feature", "geometry": r6(g), "properties": props})
            continue
        g = LineString(coords)
        props["largo_m"] = round(a_m(g).length)
        feats.append({"type": "Feature", "geometry": r6(g), "properties": props})
        for v in flechas(g):
            feats.append({"type": "Feature", "geometry": r6(v), "properties": {**props, "tipo": "flecha", "largo_m": None}})
    out = d / "flujo_observado.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "name": "flujo_observado", "features": feats}, ensure_ascii=False, indent=0) + "\n")
    n = {t: sum(f["properties"]["tipo"] == t for f in feats) for t in ("flujo", "salida", "remolino", "flecha")}
    print(f"{out.relative_to(REPO)}: {n}")


if __name__ == "__main__":
    main()
