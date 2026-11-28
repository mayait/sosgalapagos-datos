#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Muestra de puntos para marcar huellas del agua (mojado / seco) sobre las ortofotos del GAD de Santa Cruz.

Para qué: validar la susceptibilidad HAND y el modelo 2D del 30-oct con lo que dejó el agua (sedimento, lodo, erosión,
marcas en muros), incluidos los lugares SECOS, que son los que permiten contar falsas alarmas.

Diseño, fijado antes de mirar el modelo:
  - Ortofotos de los vuelos del 3 y el 5-nov-2026: Tomas de Berlanga y Mira Mar, barrio La Cascada y Curva Brava. Muestran
    las huellas de las lluvias del 30-oct y el 2-nov; no se puede separar un evento del otro.
  - Solo suelo que se puede ver: a 40 m o menos de una vía o de un edificio del mapa. Bajo el bosque no se ve el suelo.
    Esto sesga la muestra hacia lo poblado, que es lo que importa para la exposición; queda anotado en la salida.
  - Estratos por clase HAND (alta, media, baja, fuera), N_ESTRATO puntos cada uno, al menos SEP_M metros entre puntos.
  - Partición fija con semilla: la mitad de cada estrato es «calibracion» y la otra mitad «validacion». Además, un 20 % al
    azar lleva revisar_humano = true: esos los confirma en campo o sobre la foto alguien que conozca la zona.
  - Las hojas para marcar NO muestran la clase HAND ni el modelo: se marca a ciegas.

Entradas: descargas/gad_santa_cruz/ortofotos/orto_*_2026-11-0[35].tif (COG del GAD, fuera de git),
          capas/dem/santa_cruz_susc_inundacion.geojson, capas/osm/vias.geojson, capas/final/edificios_exposicion.geojson.
Salidas:  estudios/santa-cruz/datos/validacion/huellas_muestra.geojson (versionado)
          estudios/santa-cruz/figuras/validacion/hoja_NN.jpg (hojas para marcar; solo locales, como todas las figuras)

Las marcas se escriben en estudios/santa-cruz/datos/validacion/huellas_marcas.csv (dato de observación, a mano) y las
cuenta 43_validacion_contraste.py.

Uso, desde geodatos/:
  .venv/bin/python -I scripts/42_validacion_muestra.py
"""
import json
import pathlib

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes
from rasterio.windows import from_bounds
from shapely import STRtree
from shapely.geometry import Point, box, shape
from shapely.ops import transform, unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORTOS = sorted((ROOT / "descargas/gad_santa_cruz/ortofotos").glob("orto_*_2026-11-0[35].tif"))
OUT = ROOT / "estudios/santa-cruz/datos/validacion"
FIG = ROOT / "estudios/santa-cruz/figuras/validacion"
SEMILLA = 20261128
N_ESTRATO = 30
SEP_M = 40
VISIBLE_M = 40
LADO_M = 50            # lado del recorte de cada punto en las hojas
CLASES = {3: "alta", 2: "media", 1: "baja", 0: "fuera"}
UTM = Transformer.from_crs(4326, 32715, always_xy=True).transform
GEO = Transformer.from_crs(32715, 4326, always_xy=True).transform


def leer(rel, cond=lambda p: True):
    return [(transform(UTM, shape(f["geometry"])), f["properties"]) for f in json.loads((ROOT / rel).read_text())["features"]
            if f.get("geometry") and f["properties"].get("isla", "Santa Cruz") == "Santa Cruz" and cond(f["properties"])]


def huella(p):
    """Polígono (UTM) de la parte con datos de la ortofoto, leída de una vista reducida."""
    with rasterio.open(p, overview_level=4) as r:
        a = r.read(4) > 127
        return unary_union([shape(g) for g, _ in shapes(a.astype("uint8"), mask=a, transform=r.transform)]).buffer(-5)


def main():
    if not ORTOS:
        raise SystemExit("Faltan las ortofotos del GAD en descargas/gad_santa_cruz/ortofotos/")
    vuelos = [(p, p.stem.rsplit("_", 1)[1], huella(p)) for p in ORTOS]
    dominio = unary_union([h for _, _, h in vuelos])
    visible = unary_union([g.buffer(VISIBLE_M) for g, _ in leer("capas/osm/vias.geojson") if g.intersects(dominio)] +
                          [g.buffer(VISIBLE_M) for g, _ in leer("capas/final/edificios_exposicion.geojson") if g.intersects(dominio)])
    zona = dominio.intersection(visible)
    susc = leer("capas/dem/santa_cruz_susc_inundacion.geojson")
    arbol = STRtree([g for g, _ in susc])

    def clase(pt):
        return max([susc[k][1]["nivel"] for k in arbol.query(pt, predicate="intersects")], default=0)

    rng = np.random.default_rng(SEMILLA)
    x0, y0, x1, y1 = zona.bounds
    elegidos = {c: [] for c in CLASES}
    todos = []
    intentos = 0
    while any(len(v) < N_ESTRATO for v in elegidos.values()) and intentos < 400000:
        intentos += 1
        pt = Point(rng.uniform(x0, x1), rng.uniform(y0, y1))
        if not zona.contains(pt):
            continue
        c = clase(pt)
        if len(elegidos[c]) >= N_ESTRATO or any(pt.distance(q) < SEP_M for q in todos):
            continue
        elegidos[c].append(pt); todos.append(pt)
    feats = []
    n = 0
    for c, pts in elegidos.items():
        uso = rng.permutation(["calibracion"] * (len(pts) // 2) + ["validacion"] * (len(pts) - len(pts) // 2))
        for pt, u in zip(pts, uso):
            n += 1
            # el vuelo más reciente que cubre el punto (es el que se ve en la hoja)
            vuelo = max([(f, p) for p, f, h in vuelos if h.contains(pt)], key=lambda t: t[0])
            lon, lat = GEO(pt.x, pt.y)
            feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]},
                          "properties": {"id": f"HU-{n:03d}", "isla": "Santa Cruz", "estrato_hand": CLASES[c], "uso": str(u),
                                         "revisar_humano": False, "fecha_vuelo": vuelo[0], "ortofoto": vuelo[1].name,
                                         "fecha_evento": "30-oct o 2-nov-2026", "precision_m": 3}})
    for k in rng.choice(len(feats), size=round(0.2 * len(feats)), replace=False):
        feats[k]["properties"]["revisar_humano"] = True
    # orden aleatorio de los id en las hojas, para que el estrato no se adivine por el número
    orden = rng.permutation(len(feats))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "huellas_muestra.geojson").write_text(json.dumps({
        "type": "FeatureCollection", "name": "huellas_muestra",
        "metadata": {"semilla": SEMILLA, "n_por_estrato": N_ESTRATO, "separacion_m": SEP_M,
                     "dominio": "ortofotos del GAD del 3 y el 5-nov-2026, suelo a 40 m o menos de una vía o un edificio del mapa",
                     "sesgo": "solo zonas pobladas o con vías: bajo el bosque no se ve el suelo",
                     "clases_hand": "capas/dem/santa_cruz_susc_inundacion.geojson (sin el ajuste del 21-nov)",
                     "script": "geodatos/scripts/42_validacion_muestra.py"},
        "features": feats}, ensure_ascii=False, indent=0), encoding="utf-8")

    # hojas para marcar: 3 × 3 recortes de LADO_M m, con un círculo de 10 m en el punto, sin clase ni modelo
    FIG.mkdir(parents=True, exist_ok=True)
    N = 420
    lista = [feats[i] for i in orden]
    for h in range(0, len(lista), 9):
        hoja = Image.new("RGB", (3 * N, 3 * (N + 24)), "white")
        for j, f in enumerate(lista[h:h + 9]):
            x, y = UTM(*f["geometry"]["coordinates"])
            with rasterio.open(ORTOS[[p.name for p in ORTOS].index(f["properties"]["ortofoto"])]) as r:
                a = r.read([1, 2, 3], window=from_bounds(x - LADO_M / 2, y - LADO_M / 2, x + LADO_M / 2, y + LADO_M / 2, r.transform),
                           out_shape=(3, N, N), resampling=Resampling.average, boundless=True, fill_value=255)
            im = Image.fromarray(np.moveaxis(a, 0, -1)); d = ImageDraw.Draw(im)
            rad = 10 / LADO_M * N
            d.ellipse([N / 2 - rad, N / 2 - rad, N / 2 + rad, N / 2 + rad], outline=(255, 0, 0), width=2)
            d.line([(10, N - 12), (10 + N * 10 / LADO_M, N - 12)], fill="white", width=3)
            cx, cy = (j % 3) * N, (j // 3) * (N + 24)
            hoja.paste(im, (cx, cy + 24))
            ImageDraw.Draw(hoja).text((cx + 6, cy + 6), f'{f["properties"]["id"]} · vuelo {f["properties"]["fecha_vuelo"]} · círculo 10 m', fill="black")
        hoja.save(FIG / f"hoja_{h // 9 + 1:02d}.jpg", quality=85)
    print(f"{len(feats)} puntos ({', '.join(f'{CLASES[c]} {len(v)}' for c, v in elegidos.items())}); "
          f"{sum(f['properties']['revisar_humano'] for f in feats)} para revisión humana; {(len(lista) + 8) // 9} hojas en {FIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
