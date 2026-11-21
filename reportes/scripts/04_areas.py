#!/usr/bin/env python3
"""Paso 4 · Generar la capa de áreas afectadas del evento.

Lee `eventos/<evento>/areas.json` (redactado a mano: qué zonas, con qué geometría base y por qué),
los reportes curados (`reportes.json`), los barrios del CGREG y las vías de OSM, y escribe
`geodatos/capas/operativas/areas_afectadas.geojson` (EPSG:4326, 6 decimales, salida estable).

Geometría de cada zona (se pueden anidar):
    {"barrio": "LA CASCADA"}                       polígono del barrio (nombre de barrios.geojson)
    {"via": "Seymour", "buffer_m": 12}             franja alrededor de las vías de OSM con ese nombre (Santa Cruz)
    {"reporte": "r10", "buffer_m": 60}             círculo alrededor de un reporte con coordenadas
    {"punto": [lat, lon], "buffer_m": 60}          círculo alrededor de un punto
    {"cruce": ["Seymour", "Petrel"], "buffer_m": 50}
    {"al_norte_de": -0.7426} / {"al_sur_de": …}    semiplano, para recortar
    {"union": [...]} · {"interseccion": [...]} · {"menos": [a, b]}
Cualquier nodo admite además "buffer_m" (se aplica al resultado).

Antes de escribir valida tipos, reportes citados, geometrías y que ningún texto traiga teléfonos
ni nombres de quienes escriben en los grupos (misma comprobación que 03_publicar.py).

    geodatos/.venv/bin/python -I reportes/scripts/04_areas.py [--evento 2026-11-21]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402

_spec = importlib.util.spec_from_file_location("publicar", Path(__file__).resolve().parent / "03_publicar.py")
publicar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publicar)

GEO = comun.REPO / "geodatos" / "capas"
BARRIOS = GEO / "final" / "barrios.geojson"
VIAS = GEO / "osm" / "vias.geojson"
SALIDA = GEO / "operativas" / "areas_afectadas.geojson"
TIPOS = {"inundacion", "servicio", "deslave", "riesgo", "evacuacion"}
ISLA_VIAS = "Santa Cruz"
# UTM 15 S: metros para los buffers en Santa Cruz
A_M = Transformer.from_crs("EPSG:4326", "EPSG:32715", always_xy=True)
A_GRADOS = Transformer.from_crs("EPSG:32715", "EPSG:4326", always_xy=True)
LEJOS = 1e6   # para los semiplanos (m)


def transform(t: Transformer, g):
    return shapely.transform(g, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))


class Fuentes:
    def __init__(self, reportes: dict):
        self.barrios = {f["properties"]["nombre"]: transform(A_M, shape(f["geometry"]))
                        for f in json.loads(BARRIOS.read_text())["features"]}
        self.vias: dict[str, list] = {}
        for f in json.loads(VIAS.read_text())["features"]:
            p = f["properties"]
            if p.get("isla") == ISLA_VIAS and p.get("name"):
                self.vias.setdefault(p["name"], []).append(transform(A_M, shape(f["geometry"])))
        self.reportes = reportes

    def via(self, nombre: str):
        if nombre not in self.vias:
            raise SystemExit(f"areas.json: la vía «{nombre}» no está en {VIAS.name} ({ISLA_VIAS})")
        return unary_union(self.vias[nombre])

    def punto(self, lat: float, lon: float):
        return transform(A_M, shapely.Point(lon, lat))

    def geom(self, n: dict, usados: set[str]):
        if "barrio" in n:
            if n["barrio"] not in self.barrios:
                raise SystemExit(f"areas.json: el barrio «{n['barrio']}» no está en {BARRIOS.name}")
            g = self.barrios[n["barrio"]]
        elif "via" in n:
            g = self.via(n["via"])
        elif "reporte" in n:
            r = self.reportes.get(n["reporte"])
            if r is None or r.get("lat") is None:
                raise SystemExit(f"areas.json: el reporte {n['reporte']} no existe o no tiene coordenadas")
            usados.add(n["reporte"])
            g = self.punto(r["lat"], r["lon"])
        elif "punto" in n:
            g = self.punto(*n["punto"])
        elif "cruce" in n:
            a, b = (self.via(v) for v in n["cruce"])
            g = a.intersection(b)
            if g.is_empty:
                raise SystemExit(f"areas.json: {n['cruce'][0]} y {n['cruce'][1]} no se cruzan en OSM")
        elif "al_norte_de" in n or "al_sur_de" in n:
            lat = n.get("al_norte_de", n.get("al_sur_de"))
            y = self.punto(lat, -90.3).y
            g = box(-LEJOS, y, LEJOS, 1e8) if "al_norte_de" in n else box(-LEJOS, 0, LEJOS, y)
        elif "union" in n:
            g = unary_union([self.geom(h, usados) for h in n["union"]])
        elif "interseccion" in n:
            hijos = [self.geom(h, usados) for h in n["interseccion"]]
            g = hijos[0]
            for h in hijos[1:]:
                g = g.intersection(h)
        elif "menos" in n:
            a, b = (self.geom(h, usados) for h in n["menos"])
            g = a.difference(b)
        else:
            raise SystemExit(f"areas.json: nodo de geometría desconocido {sorted(n)}")
        if n.get("buffer_m"):
            g = g.buffer(n["buffer_m"], quad_segs=6)
        return g


def a_grados(g):
    g = transform(A_GRADOS, g)
    g = shapely.set_precision(shapely.make_valid(g), 1e-6)
    polys = [p for p in getattr(g, "geoms", [g]) if p.geom_type in ("Polygon", "MultiPolygon")]
    return unary_union(polys)


def redondear(obj):
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, (list, tuple)):
        return [redondear(x) for x in obj]
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--evento", default=comun.EVENTO_POR_DEFECTO)
    ev = ap.parse_args().evento
    carpeta = comun.carpeta_evento(ev)
    fuente = carpeta / "areas.json"
    if not fuente.exists():
        print(f"No existe {fuente}", file=sys.stderr)
        return 1
    cfg = json.loads(fuente.read_text(encoding="utf-8"))
    reportes = {r["id"]: r for r in json.loads((carpeta / "reportes.json").read_text(encoding="utf-8"))["reportes"]}
    autores = publicar.nombres_autores(comun.leer_mensajes(ev))
    fu = Fuentes(reportes)

    err: list[str] = []
    for k, t in cfg.get("fuentes", {}).items():
        publicar._revisar_texto(f"fuentes.{k}", t, autores, err)
    feats, filas, ids = [], [], set()
    for z in cfg["zonas"]:
        zid = z.get("id")
        if zid in ids:
            err.append(f"{zid}: id repetido")
        ids.add(zid)
        if z.get("tipo") not in TIPOS:
            err.append(f"{zid}: tipo desconocido {z.get('tipo')!r}")
        if z.get("fuente") not in cfg.get("fuentes", {}):
            err.append(f"{zid}: fuente desconocida {z.get('fuente')!r}")
        for r in z.get("reportes", []):
            if r not in reportes:
                err.append(f"{zid}: cita el reporte {r}, que no existe")
        for campo in ("nombre", "detalle"):
            if not z.get(campo):
                err.append(f"{zid}: falta {campo}")
            publicar._revisar_texto(f"{zid}.{campo}", z.get(campo) or "", autores, err)
        usados: set[str] = set()
        g_m = fu.geom(z["geometria"], usados)
        g = a_grados(g_m)
        if g.is_empty or not g.is_valid:
            err.append(f"{zid}: geometría vacía o no válida")
            continue
        minx, miny, maxx, maxy = g.bounds
        if not (publicar.LON[0] <= minx and maxx <= publicar.LON[1] and publicar.LAT[0] <= miny and maxy <= publicar.LAT[1]):
            err.append(f"{zid}: geometría fuera de Galápagos")
        area_ha = round(transform(A_M, g).area / 1e4, 2)
        props = {
            "id": zid,
            "nombre": z["nombre"],
            "tipo": z["tipo"],
            "estado": z.get("estado", "por_validar"),
            "isla": cfg["isla"],
            "fecha": z.get("fecha", cfg["fecha"]),
            "detalle": z["detalle"],
            "fuente": cfg["fuentes"][z["fuente"]],
            "reportes": ", ".join(z.get("reportes", [])),
            "area_ha": area_ha,
        }
        geom = mapping(g)
        geom = {"type": geom["type"], "coordinates": redondear(geom["coordinates"])}
        feats.append({"type": "Feature", "properties": props, "geometry": geom})
        filas.append((zid, z["tipo"], area_ha, z["nombre"]))
    if err:
        print(f"{len(err)} error(es) de validación:", file=sys.stderr)
        for e in err:
            print(f"  - {e}", file=sys.stderr)
        return 1

    fc = {"type": "FeatureCollection", "name": "areas-afectadas",
          "nota": f"Generado por reportes/scripts/04_areas.py desde reportes/eventos/{ev}/areas.json. No se edita a mano. "
                  "Delimitaciones aproximadas de SOS Galápagos a partir de reportes ciudadanos y avisos reenviados; no son datos oficiales.",
          "features": feats}
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(fc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Evento {ev}: {len(feats)} zonas → {SALIDA.relative_to(comun.REPO)}")
    for zid, tipo, ha, nombre in filas:
        print(f"  {zid}  {tipo:<11} {ha:>7.2f} ha  {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
