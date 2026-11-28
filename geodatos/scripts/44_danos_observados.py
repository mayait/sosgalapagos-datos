#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Inventario de daños observados en las ortofotos de dron del GAD de Santa Cruz (escombros, viviendas dañadas, lodo...).

A diferencia de las huellas de 42/43 (muestra al azar para validar), este es un recorrido COMPLETO y dirigido de la zona
poblada y de las orillas de las cañadas: sirve como capa de lo observado y para ver dónde cayó el daño respecto de los
modelos, pero no para calcular tasas de acierto (no es una muestra al azar).

Pasos:
  bloques  Hojas de bloques de 240 m (cuadrícula fija) donde hay foto y edificios del mapa, o una cañada del GAD o un
           flujo observado a 40 m o menos. Se anotan en danos_bloques.csv los bloques con daño visible.
  celdas   Hojas de detalle de los bloques anotados: cada bloque son 3 × 3 celdas de 80 m y cada celda tiene una rejilla
           de 3 × 3 subceldas (a…i). Los daños se anotan en danos_marcas.csv con celda + subcelda.
  capa     Convierte danos_marcas.csv en danos_observados.geojson (un punto por daño, en el centro de la subcelda,
           ± 15 m) y resume en qué clase HAND y a qué distancia de las cañadas cae.

Entradas: descargas/gad_santa_cruz/ortofotos/ (COG del GAD, fuera de git), capas/final/edificios_exposicion.geojson,
          datos/gad_santa_cruz/canadas_santa_cruz.geojson (si está), ../reportes/eventos/2026-11-21/flujo_observado.geojson,
          capas/dem/santa_cruz_susc_inundacion.geojson.
Salidas:  estudios/santa-cruz/figuras/danos/ (hojas, solo locales)
          estudios/santa-cruz/datos/danos/danos_observados.geojson y resumen.json

Uso, desde geodatos/:
  .venv/bin/python -I scripts/44_danos_observados.py bloques|celdas|capa
"""
import csv
import json
import pathlib
import sys
from collections import Counter

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import shapes
from rasterio.windows import from_bounds
from shapely import STRtree
from shapely.geometry import Point, box, shape
from shapely.ops import transform, unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORTOS = sorted((ROOT / "descargas/gad_santa_cruz/ortofotos").glob("orto_*_2026-11-*.tif"), key=lambda p: p.stem.rsplit("_", 1)[1])
DAT = ROOT / "estudios/santa-cruz/datos/danos"
FIG = ROOT / "estudios/santa-cruz/figuras/danos"
UTM = Transformer.from_crs(4326, 32715, always_xy=True).transform
GEO = Transformer.from_crs(32715, 4326, always_xy=True).transform
B, C = 240, 80              # bloque y celda (m); un bloque son 3 × 3 celdas
ORIGEN = (796000, 9917000)  # origen fijo de la cuadrícula (UTM 15S), para que los id no cambien
SUB = "abcdefghi"           # subceldas de una celda, de arriba a la izquierda a abajo a la derecha
TIPOS = {"escombros", "vivienda_destruida", "vivienda_danada", "lodo_sedimento", "erosion", "rocas_arrastradas",
         "vegetacion_tumbada", "via_danada", "muro_caido",
         # infraestructura: lo que sirve para avisar a la empresa de agua, a la eléctrica o a obras públicas
         "tuberia_rota", "tuberia_expuesta", "poste_caido", "cerca_caida", "estructura_arrastrada"}
INFRA = {"tuberia_rota", "tuberia_expuesta", "poste_caido", "via_danada", "muro_caido", "cerca_caida"}


def leer(p, cond=lambda q: True):
    p = pathlib.Path(p)
    if not p.exists():
        return []
    return [(transform(UTM, shape(f["geometry"])), f["properties"]) for f in json.loads(p.read_text())["features"]
            if f.get("geometry") and cond(f["properties"])]


def huellas():
    out = []
    for p in ORTOS:
        with rasterio.open(p, overview_level=4) as r:
            a = r.read(4) > 127
            out.append((p, unary_union([shape(g) for g, _ in shapes(a.astype("uint8"), mask=a, transform=r.transform)])))
    return out


def id_bloque(x, y):
    return f"B{int((x - ORIGEN[0]) // B):03d}-{int((y - ORIGEN[1]) // B):03d}"


def caja_bloque(bid):
    i, j = (int(v) for v in bid[1:].split("-"))
    return ORIGEN[0] + i * B, ORIGEN[1] + j * B, ORIGEN[0] + (i + 1) * B, ORIGEN[1] + (j + 1) * B


def recorte(hs, x0, y0, x1, y1, n):
    """Mosaico RGB del recorte, con el vuelo más reciente encima."""
    lienzo = np.full((3, n, n), 255, np.uint8)
    for p, h in hs:
        if not h.intersects(box(x0, y0, x1, y1)):
            continue
        with rasterio.open(p) as r:
            a = r.read([1, 2, 3, 4], window=from_bounds(x0, y0, x1, y1, r.transform), out_shape=(4, n, n),
                       resampling=Resampling.average, boundless=True, fill_value=0)
        m = a[3] > 127
        lienzo[:, m] = a[:3, m]
    return Image.fromarray(np.moveaxis(lienzo, 0, -1))


def hojas(items, nombre, n, cols=3, rejilla=None):
    FIG.mkdir(parents=True, exist_ok=True)
    for h in range(0, len(items), cols * cols):
        hoja = Image.new("RGB", (cols * n, cols * (n + 22)), "white")
        for k, (titulo, im) in enumerate(items[h:h + cols * cols]):
            if rejilla:
                d = ImageDraw.Draw(im)
                for t in range(1, rejilla):
                    d.line([(t * n / rejilla, 0), (t * n / rejilla, n)], fill=(255, 255, 0), width=1)
                    d.line([(0, t * n / rejilla), (n, t * n / rejilla)], fill=(255, 255, 0), width=1)
                for s in range(rejilla * rejilla):
                    d.text((s % rejilla * n / rejilla + 4, s // rejilla * n / rejilla + 3), SUB[s], fill=(255, 255, 0))
            cx, cy = (k % cols) * n, (k // cols) * (n + 22)
            hoja.paste(im, (cx, cy + 22))
            ImageDraw.Draw(hoja).text((cx + 5, cy + 5), titulo, fill="black")
        hoja.save(FIG / f"{nombre}_{h // (cols * cols) + 1:02d}.jpg", quality=85)
    return (len(items) + cols * cols - 1) // (cols * cols)


def bloques():
    hs = huellas()
    foto = unary_union([h for _, h in hs])
    ed = STRtree([g for g, _ in leer(ROOT / "capas/final/edificios_exposicion.geojson") if g.intersects(foto)])
    lineas = [g for g, _ in leer(ROOT / "datos/gad_santa_cruz/canadas_santa_cruz.geojson")] + \
             [g for g, _ in leer(ROOT.parent / "reportes/eventos/2026-11-21/flujo_observado.geojson")]
    tl = STRtree(lineas) if lineas else None
    x0, y0, x1, y1 = foto.bounds
    ids = []
    for x in np.arange(ORIGEN[0] + ((x0 - ORIGEN[0]) // B) * B, x1, B):
        for y in np.arange(ORIGEN[1] + ((y0 - ORIGEN[1]) // B) * B, y1, B):
            b = box(x, y, x + B, y + B)
            if foto.intersection(b).area < 0.2 * B * B:
                continue
            if len(ed.query(b, predicate="intersects")) or (tl is not None and len(tl.query(b.buffer(40), predicate="intersects"))):
                ids.append(id_bloque(x + 1, y + 1))
    ids.sort(key=lambda s: (-int(s.split("-")[1]), s))   # de norte a sur
    items = [(f"{bid} · 240 m", recorte(hs, *caja_bloque(bid), 480)) for bid in ids]
    n = hojas(items, "bloques", 480)
    DAT.mkdir(parents=True, exist_ok=True)
    (DAT / "bloques_recorridos.txt").write_text("\n".join(ids) + "\n")
    print(f"{len(ids)} bloques en {n} hojas → {FIG.relative_to(ROOT)}")


def celdas():
    """Una lámina por bloque con daño (720 px): rejilla gruesa de 3 × 3 celdas de 80 m (1-9) y fina de subceldas (a-i)."""
    marcados = [r["bloque"] for r in csv.DictReader(open(DAT / "danos_bloques.csv", encoding="utf-8")) if r["con_dano"] == "si"]
    hs = huellas()
    n = 720
    items = []
    for bid in marcados:
        im = recorte(hs, *caja_bloque(bid), n)
        d = ImageDraw.Draw(im)
        for t in range(1, 9):
            d.line([(t * n / 9, 0), (t * n / 9, n)], fill=(255, 255, 0), width=1)
            d.line([(0, t * n / 9), (n, t * n / 9)], fill=(255, 255, 0), width=1)
        for t in range(1, 3):
            d.line([(t * n / 3, 0), (t * n / 3, n)], fill=(255, 0, 0), width=3)
            d.line([(0, t * n / 3), (n, t * n / 3)], fill=(255, 0, 0), width=3)
        for k in range(9):
            cx, cy = (k % 3) * n / 3, (k // 3) * n / 3
            d.rectangle([cx + 2, cy + 2, cx + 16, cy + 16], fill=(255, 0, 0)); d.text((cx + 5, cy + 3), str(k + 1), fill="white")
            for s in range(9):
                if s == 0: continue
                d.text((cx + (s % 3) * n / 9 + 3, cy + (s // 3) * n / 9 + 2), SUB[s], fill=(255, 255, 0))
        items.append((f"{bid} · celdas 1-9 de 80 m, subceldas a-i de 27 m", im))
    k = hojas(items, "detalle", n, cols=2)
    print(f"{len(marcados)} bloques con daño en {k} hojas")


REGISTRO = ROOT / "datos/gad_santa_cruz/registro_ortofotos.json"


def corrector():
    """Corrección de posición de las ortofotos (registro contra el DSM de la SGIAR, 45_edificios_ortofotos.py).

    Las marcas se leyeron sobre las ortofotos tal como las entregó el GAD, que están corridas de 1,4 a 5 m. Cada punto se
    lleva a su posición real con la afín de la ortofoto que se veía encima (la más reciente que lo cubre). Sin registro,
    no corrige y lo dice."""
    if not REGISTRO.exists():
        print("  sin registro_ortofotos.json: las posiciones quedan sin corregir (corrimiento de 1,4 a 5 m)")
        return None
    reg = json.loads(REGISTRO.read_text())["ortofotos"]
    hs = [(p, h) for p, h in huellas()][::-1]           # más reciente primero
    def f(x, y):
        for p, h in hs:
            if h.contains(Point(x, y)) and "afin" in reg.get(p.name, {}):
                a, b, c, d, e, ff = reg[p.name]["afin"]
                return a * x + b * y + c, d * x + e * y + ff, p.name
        return x, y, None
    return f


def capa():
    filas = list(csv.DictReader(open(DAT / "danos_marcas.csv", encoding="utf-8")))
    corr = corrector()
    susc = leer(ROOT / "capas/dem/santa_cruz_susc_inundacion.geojson", lambda p: p.get("isla") == "Santa Cruz")
    ts = STRtree([g for g, _ in susc])
    can = unary_union([g for g, _ in leer(ROOT / "datos/gad_santa_cruz/canadas_santa_cruz.geojson")] +
                      [g for g, _ in leer(ROOT / "capas/dem/santa_cruz_drenaje_derivado.geojson")])
    nombres = {3: "alta", 2: "media", 1: "baja", 0: "fuera"}
    feats = []
    for r in filas:
        if r["tipo"] not in TIPOS:
            raise SystemExit(f"Tipo desconocido en {r}: usa uno de {sorted(TIPOS)}")
        if r.get("x_utm"):          # ubicado con zoom a resolución completa: ± 3 m
            x, y, prec = float(r["x_utm"]), float(r["y_utm"]), 3
        else:                       # por subcelda: ± 15 m
            x0, y0, _, _ = caja_bloque(r["bloque"])
            k = int(r["celda"]) - 1; s = SUB.index(r["subcelda"])
            x = x0 + (k % 3) * C + (s % 3 + 0.5) * C / 3
            y = y0 + (2 - k // 3) * C + (2 - s // 3 + 0.5) * C / 3
            prec = 15
        ortofoto = None
        if corr:
            x, y, ortofoto = corr(x, y)
        pt = Point(x, y)
        niv = max([susc[i][1]["nivel"] for i in ts.query(pt, predicate="intersects")], default=0)
        lon, lat = GEO(x, y)
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]},
                      "properties": {"isla": "Santa Cruz", "tipo": r["tipo"], "gravedad": r["gravedad"], "descripcion": r["descripcion"],
                                     "infraestructura": r["tipo"] in INFRA,
                                     "clase_hand": nombres[niv], "dist_cauce_m": round(can.distance(pt)),
                                     "precision_m": prec, "posicion_corregida": ortofoto is not None, "marcado_por": r["marcado_por"],
                                     "fuente": "Ortofotos de dron del GAD Municipal de Santa Cruz (3 al 22-nov-2026, CC BY 4.0); marcas de SOS Galápagos"}})
    DAT.mkdir(parents=True, exist_ok=True)
    (DAT / "danos_observados.geojson").write_text(json.dumps({"type": "FeatureCollection", "name": "danos_observados", "features": feats},
                                                             ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    d = np.array([f["properties"]["dist_cauce_m"] for f in feats]) if feats else np.array([0])
    res = {"danos": len(feats), "por_tipo": dict(Counter(f["properties"]["tipo"] for f in feats)),
           "por_gravedad": dict(Counter(f["properties"]["gravedad"] for f in feats)),
           "infraestructura": dict(Counter(f["properties"]["tipo"] for f in feats if f["properties"]["infraestructura"])),
           "por_clase_hand": dict(Counter(f["properties"]["clase_hand"] for f in feats)),
           "distancia_al_cauce_m": {"mediana": float(np.median(d)), "a_50m_o_menos": round(float((d <= 50).mean()), 2), "mas_de_150m": round(float((d > 150).mean()), 2)},
           "bloques_recorridos": len((DAT / "bloques_recorridos.txt").read_text().split()),
           "nota": "recorrido dirigido de la zona poblada y las orillas de las cañadas: no es una muestra al azar"}
    (DAT / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"bloques": bloques, "celdas": celdas, "capa": capa}[sys.argv[1]]()
