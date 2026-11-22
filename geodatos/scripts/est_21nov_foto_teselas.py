#!/usr/bin/env python3
"""Teselas XYZ de la foto aérea rectificada del 21-nov-2026 (Puerto Ayora) para el mapa de /riesgos/.

Entrada: datos/foto_aerea_21nov/ortofoto_21nov.tif (foto oblicua rectificada sobre el DTM de la SGIAR; ver su LEEME.md).
Salida:  teselas/ortofoto_21nov/relieve/{z}/{x}/{y}.webp (EPSG:3857, 256 px, esquema XYZ; transparente fuera de la foto)
         y teselas.json con la cobertura, los zooms y la atribución (Foto: Tui De Roy).
La carpeta de salida no va a git: se regenera; 10_publicar_web.py la copia a publicar/mapas/teselas/.
La clave «relieve» de teselas.json es la que lee el mapa para cualquier capa de tipo «teselas».

Uso, desde geodatos/:
  .venv/bin/python -I scripts/est_21nov_foto_teselas.py
"""
import json
import math
import pathlib
import shutil

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIF = ROOT / "datos" / "foto_aerea_21nov" / "ortofoto_21nov.tif"
OUT = ROOT / "teselas" / "ortofoto_21nov"
ZOOM_MIN, ZOOM_MAX = 13, 18          # la foto da ≈ 0,5 m por píxel cerca de La Cascada (zoom 18) y 3 m hacia el malecón
MUNDO = 2 * math.pi * 6378137.0
CREDITO = "Foto: Tui De Roy"


def tesela_de(x, y, z):
    """Límites en EPSG:3857 de la tesela XYZ."""
    lado = MUNDO / 2 ** z
    return -MUNDO / 2 + x * lado, MUNDO / 2 - (y + 1) * lado, -MUNDO / 2 + (x + 1) * lado, MUNDO / 2 - y * lado


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    n = 0
    with rasterio.open(TIF) as src:
        rgb = src.read(); mascara = src.dataset_mask()
        o, s, e, nn = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
        w3, s3, e3, n3 = transform_bounds(src.crs, "EPSG:3857", *src.bounds)
        for z in range(ZOOM_MIN, ZOOM_MAX + 1):
            lado = MUNDO / 2 ** z
            x0, x1 = int((w3 + MUNDO / 2) // lado), int((e3 + MUNDO / 2) // lado)
            y0, y1 = int((MUNDO / 2 - n3) // lado), int((MUNDO / 2 - s3) // lado)
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    a, b, c, d = tesela_de(x, y, z)
                    tr = from_origin(a, d, lado / 256, lado / 256)
                    sal = np.zeros((4, 256, 256), np.uint8)
                    for i in range(3):
                        reproject(rgb[i], sal[i], src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs="EPSG:3857",
                                  resampling=Resampling.average if z < 18 else Resampling.bilinear)
                    reproject(mascara, sal[3], src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs="EPSG:3857", resampling=Resampling.nearest)
                    if not sal[3].any(): continue
                    p = OUT / "relieve" / str(z) / str(x) / f"{y}.webp"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(np.moveaxis(sal, 0, 2), "RGBA").save(p, "WEBP", quality=82, method=6)
                    n += 1
    (OUT / "teselas.json").write_text(json.dumps({
        "titulo": "Foto aérea rectificada del 21-nov-2026, Puerto Ayora",
        "atribucion": CREDITO,
        "fuente": "Foto aérea oblicua del 21-nov-2026. Crédito: Tui De Roy. Rectificada por SOS Galápagos sobre el DTM 1 m: SGIAR (Vricon/Maxar). No es una ortofoto oficial.",
        "limites": [[round(s, 6), round(o, 6)], [round(nn, 6), round(e, 6)]],
        "relieve": {"url": "relieve/{z}/{x}/{y}.webp", "zoom_min": ZOOM_MIN, "zoom_max": ZOOM_MAX},
        "script": "geodatos/scripts/est_21nov_foto_teselas.py"}, ensure_ascii=False, indent=1))
    mb = sum(f.stat().st_size for f in OUT.rglob("*.webp")) / 1e6
    print(f"{n} teselas, {mb:.1f} MB → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
