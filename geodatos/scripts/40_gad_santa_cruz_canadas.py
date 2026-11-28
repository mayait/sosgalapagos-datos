#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Cañadas de Santa Cruz trazadas por el GAD Municipal de Santa Cruz (entrega de nov-2026, CC BY 4.0).

Entrada: descargas/gad_santa_cruz/canadas_gad_2026-11.gpx. Es el GPX original del GAD (fuera de git). Tiene 26 rutas,
         una de ellas vacía.
Salida:  datos/gad_santa_cruz/canadas_santa_cruz.geojson, con 25 líneas en EPSG:4326 y los campos id, isla,
         longitud_m (medida en UTM 15S) y fuente.
         datos/gad_santa_cruz/resumen.json, con la huella SHA-256 del GPX, el recuento y la comparación con el drenaje
         derivado del relieve.
         datos/gad_santa_cruz/vias_con_canada.geojson, con los tramos de vía (OSM) por donde corre una cañada del GAD:
         más de 80 m seguidos de cañada a 10 m o menos de la vía. Son calles que funcionaron como cauce.

Uso, desde geodatos/:
  .venv/bin/python -I scripts/40_gad_santa_cruz_canadas.py
"""
import hashlib
import json
import pathlib
import re

import numpy as np
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import LineString, mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
GPX = ROOT / "descargas" / "gad_santa_cruz" / "canadas_gad_2026-11.gpx"
OUT = ROOT / "datos" / "gad_santa_cruz"
FUENTE = "GAD Municipal de Santa Cruz (nov-2026), CC BY 4.0"
UTM = Transformer.from_crs(4326, 32715, always_xy=True)
GEO = Transformer.from_crs(32715, 4326, always_xy=True)
FRANJA_M, LARGO_MIN_M = 10, 80
# Contra qué drenaje se compara: el de la USFQ (DEM de 10 m) y el derivado por SOS (DTM de la SGIAR, 5 m, y GLO-30).
COMPARAR = {"drenaje_usfq_10m": "datos/usfq_geografia/drenaje_santa_cruz.geojson",
            "drenaje_sos": "capas/dem/santa_cruz_drenaje_derivado.geojson"}


def utm(coords):
    x, y = UTM.transform(*zip(*coords))
    return LineString(zip(x, y))


def main():
    txt = GPX.read_text(encoding="utf-8")
    rutas = re.findall(r"<rte>(.*?)</rte>", txt, re.S)
    feats, lineas = [], []
    for i, blk in enumerate(rutas, 1):
        pts = [(round(float(lo), 7), round(float(la), 7)) for la, lo in re.findall(r'lat="([-\d.]+)" lon="([-\d.]+)"', blk)]
        if len(pts) < 2:
            continue
        lu = utm(pts)
        lineas.append(lu)
        feats.append({"type": "Feature", "properties": {"id": i, "isla": "Santa Cruz", "longitud_m": round(lu.length, 1), "fuente": FUENTE},
                      "geometry": {"type": "LineString", "coordinates": pts}})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "canadas_santa_cruz.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "name": "canadas_gad_santa_cruz", "features": feats}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # Distancia de cada punto de las cañadas (cada 20 m) al cauce más cercano de cada drenaje.
    comparacion = {}
    for clave, ruta in COMPARAR.items():
        p = ROOT / ruta
        if not p.exists():
            continue
        geoms = []
        for f in json.loads(p.read_text())["features"]:
            if not f["geometry"]:
                continue
            g = shape(f["geometry"])
            partes = getattr(g, "geoms", [g])
            geoms += [utm(list(q.coords)) for q in partes if not q.is_empty and len(q.coords) > 1]
        arbol = STRtree(geoms)
        d = []
        for lu in lineas:
            for s in np.arange(0, lu.length, 20):
                q = lu.interpolate(s)
                d.append(geoms[arbol.nearest(q)].distance(q))
        d = np.array(d)
        comparacion[clave] = {"archivo": ruta, "mediana_m": round(float(np.median(d)), 1),
                              "a_30m_o_menos": round(float((d <= 30).mean()), 3), "a_60m_o_menos": round(float((d <= 60).mean()), 3)}

    # Vías por donde corre una cañada: tramo de cañada dentro de la franja de cada vía, si suma más de LARGO_MIN_M.
    vias_cauce = []
    vias = []
    for f in json.loads((ROOT / "capas/osm/vias.geojson").read_text())["features"]:
        if not f["geometry"] or f["properties"].get("isla") != "Santa Cruz":
            continue
        g = shape(f["geometry"])
        for q in getattr(g, "geoms", [g]):
            if len(q.coords) > 1:
                vias.append((utm(list(q.coords)), f["properties"]))
    arbol_v = STRtree([v for v, _ in vias])
    canadas = unary_union(lineas)
    por_via = {}
    for k in arbol_v.query(canadas.buffer(FRANJA_M), predicate="intersects"):
        v, p = vias[k]
        tramo = canadas.intersection(v.buffer(FRANJA_M))
        if tramo.length > 0:
            clave = p.get("name") or p.get("osm_id") or k
            prev = por_via.get(clave)
            por_via[clave] = (unary_union([prev[0], tramo]) if prev else tramo, p)
    for clave, (tramo, p) in por_via.items():
        partes = [q for q in getattr(tramo, "geoms", [tramo]) if q.geom_type == "LineString" and q.length > 0]
        largo = sum(q.length for q in partes)
        if largo <= LARGO_MIN_M:
            continue
        geo = [[[round(c, 7) for c in GEO.transform(x, y)] for x, y in q.coords] for q in partes]
        vias_cauce.append({"type": "Feature", "properties": {"isla": "Santa Cruz", "via": p.get("name") or "(sin nombre)",
                           "tipo_via": p.get("highway") or "", "largo_m": round(largo), "fuente": FUENTE + "; vías de OpenStreetMap"},
                           "geometry": {"type": "MultiLineString", "coordinates": geo}})
    vias_cauce.sort(key=lambda f: -f["properties"]["largo_m"])
    (OUT / "vias_con_canada.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "name": "vias_con_canada_gad", "features": vias_cauce}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    resumen = {"fuente": FUENTE, "gpx": GPX.name, "gpx_sha256": hashlib.sha256(GPX.read_bytes()).hexdigest(),
               "rutas_en_gpx": len(rutas), "canadas": len(feats), "longitud_km": round(sum(l.length for l in lineas) / 1000, 2),
               "comparacion_con_drenaje": comparacion,
               "vias_con_canada": {"tramos": len(vias_cauce), "largo_km": round(sum(f["properties"]["largo_m"] for f in vias_cauce) / 1000, 2),
                                   "criterio": f"más de {LARGO_MIN_M} m de cañada a {FRANJA_M} m o menos de la vía"}}
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
