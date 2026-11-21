#!/usr/bin/env python3
"""Teselas de cota de todo el archipiélago para la vista 3D del mapa de reportes.

Una pirámide XYZ (EPSG:3857, 256 px) con la cota del terreno codificada en RGB (formato «Terrarium» de Mapzen:
cota = R·256 + G + B/256 − 32768, en m sobre EGM2008), del zoom ZOOM_MIN al ZOOM_MAX:
  cota/{z}/{x}/{y}.png
y teselas.json con la cobertura, los zooms y la atribución.

Relieve: el mismo relieve fusionado de 03_dem.py (relieve_sgiar.py). En Santa Cruz manda el DTM de 1 m de la SGIAR
(Puerto Ayora, el escarpe y Bellavista), con una transición de 300 m hacia el Copernicus GLO-30, que cubre el resto
de las islas. El mar vale 0 m.

Por qué existe: MapLibre necesita la cota en varios niveles de zoom para levantar el terreno. Las teselas de cota de
36_teselas_dtm.py solo existen en el zoom 16 y solo en Santa Cruz (sirven para leer la cota bajo el cursor).

Detalles:
  - Las teselas que son solo mar no se escriben: el visor las toma como cota 0.
  - La cota se redondea a 0,1 m donde hay DTM y a 0,5 m donde solo hay Copernicus (su error es de metros).
    Así las imágenes pesan mucho menos y no se pierde nada que el dato tenga.
  - Es para MIRAR el relieve, no para medir: el modelo es de superficie fuera de la cobertura del DTM.

Salida: teselas/relieve3d/ (no va a git: se regenera; 10_publicar_web.py la copia a publicar/mapas/teselas/).
Uso, desde geodatos/:
  .venv/bin/python -I scripts/37_teselas_relieve3d.py [--procesos 8] [--zoom-max 14]
"""
import argparse
import glob
import importlib.util
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
from rasterio.warp import reproject, transform_bounds

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("relieve_sgiar", ROOT / "scripts/relieve_sgiar.py")
relieve_sgiar = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(relieve_sgiar)

COPERNICUS = sorted(glob.glob(str(ROOT / "descargas/dem/Copernicus_DSM_COG_10_*_DEM.tif")))
OUT = ROOT / "teselas/relieve3d"
ARCHIPIELAGO = (-92.1, -1.6, -89.1, 0.8)   # oeste, sur, este, norte (sin Darwin ni Wolf)
ZOOM_MIN, ZOOM_MAX = 8, 14                 # zoom 14 ≈ 9,5 m por píxel en el ecuador
R_TIERRA = 6378137.0
MUNDO = 2 * math.pi * R_TIERRA
MAR = -9999.0
PASO_DTM_M, PASO_COPERNICUS_M = 0.1, 0.5
ATRIBUCION = "Relieve: DTM 1 m SGIAR (Vricon/Maxar) en Santa Cruz; Copernicus GLO-30 (ESA) en el resto"


def lonlat_a_tesela(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return int(x), int(y)


def tesela_transform(z, x, y, px=256):
    tam = MUNDO / 2 ** z
    return from_origin(-MUNDO / 2 + x * tam, MUNDO / 2 - y * tam, tam / px, tam / px)


def limites_3857(z, x, y):
    tam = MUNDO / 2 ** z
    return -MUNDO / 2 + x * tam, MUNDO / 2 - (y + 1) * tam, -MUNDO / 2 + (x + 1) * tam, MUNDO / 2 - y * tam


_FUENTES = []
def _fuentes():
    """Límites en EPSG:3857 de cada tesela del Copernicus, para abrir solo las que tocan."""
    if not _FUENTES:
        for ruta in COPERNICUS:
            with rasterio.open(ruta) as d:
                _FUENTES.append((ruta, transform_bounds(d.crs, "EPSG:3857", *d.bounds)))
    return _FUENTES


_COBERTURA = []
def _cobertura_dtm():
    if not _COBERTURA:
        _COBERTURA.append(relieve_sgiar.cobertura("EPSG:3857").bounds if relieve_sgiar.disponible() else None)
    return _COBERTURA[0]


def _se_tocan(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def cota_de(z, x, y):
    """Cota (m) de la tesela, con el mar en MAR, y el peso del DTM (0 = solo Copernicus)."""
    tr = tesela_transform(z, x, y)
    caja = limites_3857(z, x, y)
    cop = np.full((256, 256), MAR, "float32")
    for ruta, lim in _fuentes():
        if not _se_tocan(caja, lim):
            continue
        with rasterio.open(ruta) as d:
            parte = np.full((256, 256), np.nan, "float32")
            # al alejar se promedia (cada píxel cubre muchas celdas); al acercar se interpola
            modo = Resampling.average if z < 12 else Resampling.bilinear
            reproject(rasterio.band(d, 1), parte, dst_nodata=np.nan, dst_transform=tr, dst_crs="EPSG:3857", resampling=modo)
        ok = np.isfinite(parte)
        cop[ok] = parte[ok]
    cop[cop <= 0] = MAR                      # en el Copernicus el mar vale 0
    peso = np.zeros((256, 256), "float32")
    cob = _cobertura_dtm()
    if cob and z >= 10 and _se_tocan(caja, cob):
        cop, peso, _ = relieve_sgiar.fusionar(cop, tr, "EPSG:3857", nodata=MAR)
    return cop, peso


def tesela(args):
    """Escribe la tesela si tiene tierra. Devuelve (z, x, y, bytes) o None si es solo mar."""
    z, x, y = args
    cota, peso = cota_de(z, x, y)
    tierra = cota != MAR
    if not tierra.any():
        return None
    cota = np.where(tierra, cota, 0).astype("float64")
    paso = np.where(peso > 0, PASO_DTM_M, PASO_COPERNICUS_M)
    v = np.round(cota / paso) * paso + 32768
    img = np.zeros((256, 256, 3), "uint8")
    img[..., 0] = np.floor(v / 256)
    img[..., 1] = np.floor(v) % 256
    img[..., 2] = np.round((v - np.floor(v)) * 256).clip(0, 255)
    dest = OUT / "cota" / str(z) / str(x) / f"{y}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGB").save(dest, "PNG", optimize=True)
    return z, x, y, dest.stat().st_size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--procesos", type=int, default=8)
    ap.add_argument("--zoom-max", type=int, default=ZOOM_MAX)
    args = ap.parse_args()
    t0 = time.time()
    if not COPERNICUS:
        raise SystemExit("Faltan las teselas del Copernicus en descargas/dem/ (ver geodatos/LEEME.md)")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    w, s, e, n = ARCHIPIELAGO
    x0, y0 = lonlat_a_tesela(w, n, ZOOM_MIN); x1, y1 = lonlat_a_tesela(e, s, ZOOM_MIN)
    trabajos = [(ZOOM_MIN, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    resumen = {}
    with ProcessPoolExecutor(args.procesos) as ex:
        for z in range(ZOOM_MIN, args.zoom_max + 1):
            hechas = [r for r in ex.map(tesela, trabajos, chunksize=8) if r]
            resumen[z] = (len(hechas), sum(r[3] for r in hechas))
            print(f"zoom {z}: {len(hechas)} teselas con tierra de {len(trabajos)} ({resumen[z][1] / 1e6:.1f} MB)", flush=True)
            # solo se baja al siguiente zoom dentro de las teselas que tienen tierra
            trabajos = [(z + 1, 2 * x + i, 2 * y + j) for _, x, y, _ in hechas for i in (0, 1) for j in (0, 1)]

    meta = {"titulo": "Cota del terreno para la vista 3D (archipiélago)", "atribucion": ATRIBUCION,
            "fuente": relieve_sgiar.FUENTE if relieve_sgiar.disponible() else "Copernicus GLO-30",
            "limites": [[s, w], [n, e]],
            "cota": {"url": "cota/{z}/{x}/{y}.png", "zoom_min": ZOOM_MIN, "zoom_max": args.zoom_max, "codificacion": "terrarium",
                     "nota": "cota = R*256 + G + B/256 - 32768 (m, EGM2008); el mar vale 0 y las teselas de solo mar no existen"},
            "advertencia": "Para mirar el relieve, no para medir. Fuera del DTM de la SGIAR es un modelo de superficie de 30 m.",
            "script": "geodatos/scripts/37_teselas_relieve3d.py"}
    (OUT / "teselas.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    total = sum(n for n, _ in resumen.values()); tam = sum(b for _, b in resumen.values()) / 1e6
    print(f"Listo: {total} teselas, {tam:.0f} MB en {OUT.relative_to(ROOT)} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
