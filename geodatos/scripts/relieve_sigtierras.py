# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""DEM de 10 m de SIGTIERRAS para toda Santa Cruz (entregado por el Instituto de Geografía de la USFQ).

Lo usa 03_dem.py. Lo deja listo 38_usfq_cuencas_sigtierras.py en descargas/usfq_geografia/ (UTM 15 S, sin dato = −9999).
Cubre el 97 % de la tierra de Santa Cruz. Frente a 7 859 puntos acotados del IGM 1:25 000 su error absoluto medio es
0,52 m (mediana −0,04 m); el Copernicus GLO-30 da 2,70 m (mediana −1,89 m). No trae techos ni copas: en Puerto Ayora
queda en mediana 1,1 m bajo el DTM de la SGIAR, donde un DSM quedaría por encima. Ojo: el acuerdo tan alto con el IGM
sugiere que el DEM se hizo en parte con esa cartografía, así que esos puntos no son un control independiente.

Orden de prioridad del relieve de Santa Cruz: DTM 1 m SGIAR > SIGTIERRAS 10 m > Copernicus GLO-30.
Aquí solo se cambia el Copernicus por SIGTIERRAS donde hay dato; la fusión con el DTM la hace relieve_sgiar.py después.

Funciones:
  disponible()
  fusionar(z, transform, crs, nodata)   relieve con SIGTIERRAS donde hay dato y z (Copernicus) fuera
  cobertura(crs, recorte_m)             rectángulo del DEM (recortado hacia dentro recorte_m metros)
"""
import pathlib

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform_geom
from shapely.geometry import box, shape

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEM = ROOT / "descargas/usfq_geografia/santa_cruz_sigtierras_10m.tif"
FUENTE = "DEM 10 m SIGTIERRAS (vía Instituto de Geografía USFQ)"


def disponible():
    return DEM.exists()


def exigir():
    if not DEM.exists():
        raise SystemExit(f"Falta {DEM.relative_to(ROOT)}. Corre antes: .venv/bin/python -I scripts/38_usfq_cuencas_sigtierras.py "
                         "(necesita descargas/usfq_geografia/GALAPAGOS-SCRUZ.zip)")


def fusionar(z, transform, crs, nodata=-9999):
    """Devuelve (z con SIGTIERRAS donde hay dato, máscara de celdas que vienen de SIGTIERRAS)."""
    H, W = z.shape
    zs = np.full((H, W), np.nan, "float32")
    with rasterio.open(DEM) as d:
        # Si la malla de destino es más gruesa que 10 m se promedia; si es más fina, se interpola
        fina = abs(transform.a) * (111320 if crs == "EPSG:4326" else 1) < 10
        reproject(rasterio.band(d, 1), zs, dst_transform=transform, dst_crs=crs, dst_nodata=np.nan,
                  resampling=Resampling.bilinear if fina else Resampling.average)
    ok = np.isfinite(zs)
    out = z.astype("float32").copy()
    out[ok] = zs[ok]
    out[ok & (zs <= 0.5)] = nodata          # mar y costa bajo 0,5 m, como en el Copernicus
    return out, ok


def cobertura(crs="EPSG:4326", recorte_m=0.0):
    with rasterio.open(DEM) as d:
        b = d.bounds
        src = d.crs
    g = box(b.left + recorte_m, b.bottom + recorte_m, b.right - recorte_m, b.top - recorte_m)
    return shape(transform_geom(src, crs, g.__geo_interface__))
