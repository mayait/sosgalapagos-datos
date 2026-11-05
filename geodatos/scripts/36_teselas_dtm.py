#!/usr/bin/env python3
"""Teselas XYZ del DTM de 1 m de la SGIAR (Santa Cruz) para el visor de /mapas.

Dos juegos de teselas (EPSG:3857, 256 px, esquema XYZ de OpenStreetMap):
  relieve/{z}/{x}/{y}.webp   relieve sombreado multidireccional con tinte hipsométrico, zoom ZOOM_MIN–ZOOM_MAX.
                             El mar es transparente. Es una imagen: sirve para mirar, no para medir.
  cota/{z}/{x}/{y}.png       cota del terreno codificada en RGB (formato «Terrarium» de Mapzen:
                             cota = R·256 + G + B/256 − 32768, en m sobre EGM2008), solo en zoom ZOOM_COTA (≈2,4 m por píxel).
                             El visor la lee para mostrar la cota bajo el cursor. Alfa 0 = mar o sin dato.
y teselas.json con la cobertura, los zooms y la atribución.

Salida: teselas/dtm_sgiar/ (no va a git: se regenera; 10_publicar_web.py la copia a publicar/mapas/teselas/).
Uso, desde geodatos/:
  .venv/bin/python -I scripts/36_teselas_dtm.py [--procesos 8]
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
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
VRT = ROOT / "datos/dtm_sgiar/dtm_sgiar_1m.vrt"
MAR = ROOT / "descargas/dem_recortes/santa_cruz_dtm_mar_5m.tif"
OUT = ROOT / "teselas/dtm_sgiar"
ZOOM_MIN, ZOOM_MAX, ZOOM_COTA = 11, 17, 16
R_TIERRA = 6378137.0
MUNDO = 2 * math.pi * R_TIERRA
ATRIBUCION = "DTM 1 m: SGIAR (Vricon/Maxar)"
# exageración vertical del sombreado por zoom (en zoom bajo el relieve se aplana)
EXAG = {11: 4.0, 12: 3.5, 13: 3.0, 14: 2.5, 15: 2.0, 16: 1.6, 17: 1.3}
TINTE = LinearSegmentedColormap.from_list("tinte", [
    (0.00, "#e9f0d8"), (0.04, "#d7e5b4"), (0.12, "#b9d38f"), (0.25, "#8fbf6f"), (0.45, "#6f9f58"),
    (0.65, "#8f8a5a"), (0.82, "#a8876a"), (1.00, "#d9cfc4")])
Z_MAX = 870.0


def lonlat_a_tesela(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return int(x), int(y)


def tesela_transform(z, x, y, px=256, borde=1):
    tam = MUNDO / 2 ** z
    res = tam / px
    x0 = -MUNDO / 2 + x * tam
    y0 = MUNDO / 2 - y * tam
    return from_origin(x0 - borde * res, y0 + borde * res, res, res), res


def leer(z, x, y, borde):
    tr, res = tesela_transform(z, x, y, borde=borde)
    n = 256 + 2 * borde
    a = np.full((n, n), np.nan, "float32")
    with rasterio.open(VRT) as d:
        reproject(rasterio.band(d, 1), a, src_nodata=d.nodata, dst_nodata=np.nan, dst_transform=tr, dst_crs="EPSG:3857",
                  resampling=Resampling.average if res > 1.5 else Resampling.bilinear)
    a[_mar_en(tr, n)] = np.nan
    return a, res


_MAR = {}
def _mar_en(tr, n):
    """Máscara de mar (5 m, UTM) en los centros de los píxeles de la tesela (vecino más cercano)."""
    if not _MAR:
        with rasterio.open(MAR) as d:
            _MAR.update(m=d.read(1).astype(bool), inv=~d.transform, crs=d.crs)
        _MAR["T"] = Transformer.from_crs("EPSG:3857", _MAR["crs"], always_xy=True)
    xs = tr.c + tr.a * (np.arange(n) + 0.5); ys = tr.f + tr.e * (np.arange(n) + 0.5)
    X, Y = np.meshgrid(xs, ys)
    U, V = _MAR["T"].transform(X, Y)
    c, r = _MAR["inv"] * (U, V)
    c = np.floor(c).astype(int); r = np.floor(r).astype(int)
    m = _MAR["m"]
    dentro = (r >= 0) & (r < m.shape[0]) & (c >= 0) & (c < m.shape[1])
    out = np.zeros((n, n), bool)
    out[dentro] = m[r[dentro], c[dentro]]
    return out


def sombreado(z, res, exag):
    """Sombreado multidireccional (4 azimuts ponderados), 0–1."""
    zz = np.where(np.isfinite(z), z, np.nanmin(z) if np.isfinite(z).any() else 0)
    gy, gx = np.gradient(zz * exag, res)
    pend = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    alt = math.radians(45)
    hs = 0
    for az, w in ((225, 0.15), (270, 0.25), (315, 0.45), (360, 0.15)):
        b = math.radians(az)
        hs = hs + w * (math.sin(alt) * np.cos(pend) + math.cos(alt) * np.sin(pend) * np.cos(b - asp))
    return np.clip(hs, 0, 1)


def tesela_relieve(args):
    z, x, y = args
    a, res = leer(z, x, y, borde=1)
    dest = OUT / "relieve" / str(z) / str(x) / f"{y}.webp"
    dest.parent.mkdir(parents=True, exist_ok=True)
    ok = np.isfinite(a)
    if not ok.any():
        Image.new("RGBA", (256, 256), (0, 0, 0, 0)).save(dest, "WEBP", lossless=True)
        return 0
    hs = sombreado(a, res, EXAG[z])[1:-1, 1:-1]
    a = a[1:-1, 1:-1]; ok = ok[1:-1, 1:-1]
    t = TINTE(np.sqrt(np.clip(np.nan_to_num(a, nan=0) / Z_MAX, 0, 1)))[..., :3]
    # contraste respecto del terreno llano (sombreado = sen 45° ≈ 0,707): las laderas al sol aclaran y las opuestas oscurecen
    luz = np.clip(0.92 + 2.2 * (hs[..., None] - math.sin(math.radians(45))), 0.18, 1.25)
    rgb = np.clip(t * luz, 0, 1)
    img = np.zeros((256, 256, 4), "uint8")
    img[..., :3] = (rgb * 255).astype("uint8")
    img[..., 3] = np.where(ok, 255, 0)
    Image.fromarray(img, "RGBA").save(dest, "WEBP", quality=80, method=5)
    return 1


def tesela_cota(args):
    z, x, y = args
    a, _ = leer(z, x, y, borde=0)
    dest = OUT / "cota" / str(z) / str(x) / f"{y}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    ok = np.isfinite(a)
    v = np.where(ok, a, 0).astype("float64") + 32768
    img = np.zeros((256, 256, 4), "uint8")
    img[..., 0] = np.floor(v / 256)
    img[..., 1] = np.floor(v) % 256
    img[..., 2] = np.floor((v - np.floor(v)) * 256)
    img[..., 3] = np.where(ok, 255, 0)
    Image.fromarray(img, "RGBA").save(dest, "PNG", optimize=True)
    return int(ok.any())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--procesos", type=int, default=8)
    args = ap.parse_args()
    t0 = time.time()
    if not MAR.exists(): raise SystemExit(f"Falta {MAR.relative_to(ROOT)}: corre antes scripts/03_dem.py")
    with rasterio.open(VRT) as d:
        w, s, e, n = transform_bounds(d.crs, "EPSG:4326", *d.bounds)
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    trabajos = []
    for z in range(ZOOM_MIN, ZOOM_MAX + 1):
        x0, y0 = lonlat_a_tesela(w, n, z); x1, y1 = lonlat_a_tesela(e, s, z)
        trabajos += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    x0, y0 = lonlat_a_tesela(w, n, ZOOM_COTA); x1, y1 = lonlat_a_tesela(e, s, ZOOM_COTA)
    cotas = [(ZOOM_COTA, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    print(f"{len(trabajos)} teselas de relieve (zoom {ZOOM_MIN}–{ZOOM_MAX}) y {len(cotas)} de cota (zoom {ZOOM_COTA})")
    with ProcessPoolExecutor(args.procesos) as ex:
        nr = sum(ex.map(tesela_relieve, trabajos, chunksize=16))
        nc = sum(ex.map(tesela_cota, cotas, chunksize=16))
    meta = {"titulo": "Relieve del DTM de 1 m (SGIAR), Santa Cruz", "atribucion": ATRIBUCION,
            "fuente": "SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo. Producto Vricon DTM (Maxar), imágenes 2020–2024.",
            "limites": [[round(s, 6), round(w, 6)], [round(n, 6), round(e, 6)]],
            "relieve": {"url": "relieve/{z}/{x}/{y}.webp", "zoom_min": ZOOM_MIN, "zoom_max": ZOOM_MAX},
            "cota": {"url": "cota/{z}/{x}/{y}.png", "zoom": ZOOM_COTA, "codificacion": "terrarium",
                     "nota": "cota = R*256 + G + B/256 - 32768 (m, EGM2008); alfa 0 = mar o sin dato"},
            "script": "geodatos/scripts/36_teselas_dtm.py"}
    (OUT / "teselas.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    tam = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) / 1e6
    print(f"Listo: {nr} teselas de relieve con datos, {nc} de cota; {tam:.0f} MB en {OUT.relative_to(ROOT)} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
