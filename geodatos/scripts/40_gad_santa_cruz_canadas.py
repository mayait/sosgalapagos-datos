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
from shapely.geometry import LineString, shape

ROOT = pathlib.Path(__file__).resolve().parents[1]
GPX = ROOT / "descargas" / "gad_santa_cruz" / "canadas_gad_2026-11.gpx"
OUT = ROOT / "datos" / "gad_santa_cruz"
FUENTE = "GAD Municipal de Santa Cruz (nov-2026), CC BY 4.0"
UTM = Transformer.from_crs(4326, 32715, always_xy=True)
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

    resumen = {"fuente": FUENTE, "gpx": GPX.name, "gpx_sha256": hashlib.sha256(GPX.read_bytes()).hexdigest(),
               "rutas_en_gpx": len(rutas), "canadas": len(feats), "longitud_km": round(sum(l.length for l in lineas) / 1000, 2),
               "comparacion_con_drenaje": comparacion}
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
