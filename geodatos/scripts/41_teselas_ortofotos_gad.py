#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Teselas XYZ de las ortofotos de dron del GAD Municipal de Santa Cruz (nov-2026, CC BY 4.0) para el mapa de /riesgos/.

Entrada: descargas/gad_santa_cruz/ortofotos/orto_*_2026-11-*.tif. Son las cinco ortofotos de después del evento, en COG
         sin pérdida (EPSG:32715, RGBA, de 2 a 7,5 cm). Quedan fuera de git; los originales completos van a Zenodo.
Salida:  teselas/ortofotos_gad/relieve/{z}/{x}/{y}.webp (EPSG:3857, 256 px, esquema XYZ, transparente fuera del vuelo)
         y teselas.json con la cobertura, los zooms y la atribución.

Mosaico: donde dos vuelos se solapan queda encima el más reciente. Cada zoom lee la vista reducida (overview) del COG
más cercana a su resolución, así que el zoom 14 no lee los 25 GB.

Uso, desde geodatos/:
  .venv/bin/python -I scripts/41_teselas_ortofotos_gad.py [--zoom-max 20] [--procesos 8]
"""
import argparse
import json
import math
import pathlib
import shutil
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "descargas" / "gad_santa_cruz" / "ortofotos"
OUT = ROOT / "teselas" / "ortofotos_gad"
ZOOM_MIN = 14
MUNDO = 2 * math.pi * 6378137.0
META = 8                    # metatesela de 8 × 8 teselas (2048 px)
CREDITO = "Ortofotos: GAD Municipal de Santa Cruz (CC BY 4.0)"


def fuentes():
    """Ortofotos de después del evento, de la más antigua a la más reciente (la última queda encima)."""
    tifs = sorted(ENTRADA.glob("orto_*_2026-11-*.tif"), key=lambda p: p.stem.rsplit("_", 1)[1])
    if not tifs:
        raise SystemExit(f"Faltan las ortofotos en {ENTRADA}. Ver datos/gad_santa_cruz/LEEME.md")
    return tifs


def abrir(p, res_m):
    """Abre la vista reducida del COG cuya resolución es la más gruesa que no pasa de res_m."""
    with rasterio.open(p) as r:
        r0 = r.res[0]; facs = r.overviews(1)
    nivel = None
    for k, f in enumerate(facs):
        if r0 * f <= res_m:
            nivel = k
    return rasterio.open(p, overview_level=nivel) if nivel is not None else rasterio.open(p)


def metatesela(args):
    z, mx, my, tifs, cajas = args
    lado = MUNDO / 2 ** z
    x0m, y0m = -MUNDO / 2 + mx * META * lado, MUNDO / 2 - my * META * lado
    caja = (x0m, y0m - META * lado, x0m + META * lado, y0m)
    n = META * 256
    tr = from_origin(x0m, y0m, lado / 256, lado / 256)
    res_m = lado / 256 * math.cos(math.radians(0.72))
    lienzo = np.zeros((4, n, n), np.uint8)
    for p, cj in zip(tifs, cajas):
        if cj[0] > caja[2] or cj[2] < caja[0] or cj[1] > caja[3] or cj[3] < caja[1]:
            continue
        with abrir(p, res_m) as src, WarpedVRT(src, crs="EPSG:3857", transform=tr, width=n, height=n,
                                                resampling=Resampling.bilinear, src_nodata=None, add_alpha=False) as v:
            a = v.read([1, 2, 3, 4])
        m = a[3] > 127
        lienzo[:, m] = a[:, m]
    escritas = 0
    for i in range(META):
        for j in range(META):
            t = lienzo[:, j * 256:(j + 1) * 256, i * 256:(i + 1) * 256]
            if not (t[3] > 0).any():
                continue
            ruta = OUT / "relieve" / str(z) / str(mx * META + i) / f"{my * META + j}.webp"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.moveaxis(t, 0, 2), "RGBA").save(ruta, "WEBP", quality=80, method=4)
            escritas += 1
    return escritas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zoom-max", type=int, default=20)
    ap.add_argument("--procesos", type=int, default=8)
    a = ap.parse_args()
    tifs = fuentes()
    cajas = []
    for p in tifs:
        with rasterio.open(p) as r:
            cajas.append(transform_bounds(r.crs, "EPSG:3857", *r.bounds))
    w3, s3 = min(c[0] for c in cajas), min(c[1] for c in cajas)
    e3, n3 = max(c[2] for c in cajas), max(c[3] for c in cajas)
    if OUT.exists():
        shutil.rmtree(OUT)
    resumen = {}
    with ProcessPoolExecutor(a.procesos) as ex:
        for z in range(ZOOM_MIN, a.zoom_max + 1):
            t0 = time.time()
            lado = MUNDO / 2 ** z * META
            mx0, mx1 = int((w3 + MUNDO / 2) // lado), int((e3 + MUNDO / 2) // lado)
            my0, my1 = int((MUNDO / 2 - n3) // lado), int((MUNDO / 2 - s3) // lado)
            trabajos = [(z, mx, my, tifs, cajas) for mx in range(mx0, mx1 + 1) for my in range(my0, my1 + 1)]
            n = sum(ex.map(metatesela, trabajos, chunksize=1))
            mb = sum(f.stat().st_size for f in (OUT / "relieve" / str(z)).rglob("*.webp")) / 1e6 if n else 0
            resumen[z] = {"teselas": n, "mb": round(mb, 1)}
            print(f"zoom {z}: {n} teselas, {mb:.1f} MB, {time.time() - t0:.0f} s", flush=True)
    o, s, e, nn = transform_bounds("EPSG:3857", "EPSG:4326", w3, s3, e3, n3)
    (OUT / "teselas.json").write_text(json.dumps({
        "titulo": "Ortofotos de dron del GAD Municipal de Santa Cruz, 3 al 22-nov-2026",
        "atribucion": CREDITO,
        "fuente": "Ortomosaicos de dron del GAD Municipal de Santa Cruz (PIX4Dmatic), de 2 a 7,5 cm por píxel, del 3 al 22 de noviembre de 2026. "
                  "Licencia CC BY 4.0. Teselas de SOS Galápagos; donde dos vuelos se solapan queda el más reciente.",
        "vuelos": [p.stem for p in tifs],
        "limites": [[round(s, 6), round(o, 6)], [round(nn, 6), round(e, 6)]],
        "relieve": {"url": "relieve/{z}/{x}/{y}.webp", "zoom_min": ZOOM_MIN, "zoom_max": a.zoom_max},
        "por_zoom": resumen,
        "script": "geodatos/scripts/41_teselas_ortofotos_gad.py"}, ensure_ascii=False, indent=1))
    print(f"total: {sum(v['teselas'] for v in resumen.values())} teselas, {sum(v['mb'] for v in resumen.values()):.0f} MB → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
