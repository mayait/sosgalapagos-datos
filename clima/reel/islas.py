#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Genera islas.js: el contorno de las islas, simplificado, para el mapa del reel del clima.

Sale de la capa del IGM (geodatos/capas/igm/islas.geojson). Solo hay que correrlo si esa capa cambia:

    geodatos/.venv/bin/python -I clima/reel/islas.py

Necesita shapely (está en geodatos/requirements.txt). El reel en sí no lo necesita: usa islas.js ya generado.
"""
import json
from pathlib import Path

from shapely.geometry import mapping, shape

AQUI = Path(__file__).resolve().parent
ORIGEN = AQUI.parents[1] / "geodatos" / "capas" / "igm" / "islas.geojson"
TOLERANCIA = 0.0006   # grados (≈ 65 m): de sobra para un mapa de todo el archipiélago
AREA_MINIMA = 3e-6    # grados²: se quitan los islotes que no se verían


def redondear(coords):
    if coords and isinstance(coords[0], (list, tuple)):
        return [redondear(c) for c in coords]
    return [round(coords[0], 5), round(coords[1], 5)]


def main():
    capa = json.loads(ORIGEN.read_text(encoding="utf-8"))
    islas = []
    for f in capa["features"]:
        geom = shape(f["geometry"]).simplify(TOLERANCIA)
        if geom.area > AREA_MINIMA:
            g = json.loads(json.dumps(mapping(geom)))
            g["coordinates"] = redondear(g["coordinates"])
            islas.append({"type": "Feature", "properties": {}, "geometry": g})
    salida = AQUI / "islas.js"
    salida.write_text(
        "// Generado por clima/reel/islas.py desde geodatos/capas/igm/islas.geojson (fuente: IGM). No editar a mano.\n"
        "window.ISLAS=" + json.dumps({"type": "FeatureCollection", "features": islas}, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    print(f"{salida}: {len(islas)} islas, {salida.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
