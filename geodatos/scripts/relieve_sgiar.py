"""Relieve fusionado de Santa Cruz: DTM de 1 m de la SGIAR donde hay cobertura y Copernicus GLO-30 fuera de ella.

Lo usa 03_dem.py. El DTM (datos/dtm_sgiar/, 35_dtm_sgiar.py) es de TERRENO (sin techos ni copas) y cubre Puerto Ayora,
el escarpe y Bellavista (183 km²). El Copernicus es de SUPERFICIE (DSM, 30 m). Para que no quede un escalón en el borde,
en una franja de TRANSICION_M metros hacia dentro de la cobertura se pasa linealmente de un relieve al otro.

Mar: en el DTM el mar es una superficie plana de ≈ 0,75 m. Se marca como mar lo que está por debajo de MAR_DTM_M y
conecta con el borde de la cobertura (en la malla de 5 m), y ahí se deja sin dato, como el mar del Copernicus.

Funciones:
  fusionar(z, transform, crs)   relieve fusionado sobre la malla que se le da (z = Copernicus en esa malla, −9999 = mar)
  cobertura(crs, recorte_m)     polígono de la cobertura del DTM (recortado hacia dentro recorte_m metros)
"""
import pathlib
from functools import lru_cache

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform_geom
from scipy import ndimage
from shapely.geometry import box, shape

ROOT = pathlib.Path(__file__).resolve().parents[1]
VRT = ROOT / "datos/dtm_sgiar/dtm_sgiar_1m.vrt"
TRANSICION_M = 300        # franja de paso Copernicus → DTM, hacia dentro de la cobertura
MAR_DTM_M = 0.76          # el mar del DTM es plano a 0,737–0,751 m
CELDA_5M = 5.0
FUENTE = "DTM 1 m SGIAR (Vricon/Maxar) en Puerto Ayora, el escarpe y Bellavista; Copernicus GLO-30 fuera"


def disponible():
    return VRT.exists()


@lru_cache(maxsize=1)
def _dtm_5m():
    """DTM promediado a 5 m (UTM 15 S), con el mar en NaN y la distancia al borde de la cobertura (m)."""
    with rasterio.open(VRT) as d:
        h, w = int(d.height // CELDA_5M), int(d.width // CELDA_5M)
        z = d.read(1, out_shape=(h, w), resampling=Resampling.average).astype("float32")
        tr = d.transform * d.transform.scale(d.width / w, d.height / h)
        crs = d.crs
        nodata = d.nodata
    z[z == nodata] = np.nan
    bajo = z < MAR_DTM_M
    lab, n = ndimage.label(bajo)
    borde = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    mar = np.isin(lab, borde[borde > 0])
    mar = ndimage.binary_opening(mar, iterations=1) | (mar & ndimage.binary_erosion(mar, iterations=2))
    z[mar] = np.nan
    # distancia (m) al borde de la cobertura, para la transición
    dentro = np.ones_like(bajo)
    dentro[0, :] = dentro[-1, :] = dentro[:, 0] = dentro[:, -1] = False
    dist = ndimage.distance_transform_edt(dentro) * CELDA_5M
    return z, tr, crs, mar, dist


def fusionar(z, transform, crs, nodata=-9999):
    """Devuelve (z_fusionado, peso_dtm, mar_dtm) en la malla de z. z es el Copernicus en esa malla (nodata = mar)."""
    z5, tr5, crs5, mar5, dist5 = _dtm_5m()
    H, W = z.shape
    kw = dict(src_transform=tr5, src_crs=crs5, dst_transform=transform, dst_crs=crs)
    zd = np.full((H, W), np.nan, "float32")
    reproject(np.nan_to_num(z5, nan=-32767).astype("float32"), zd, src_nodata=-32767, dst_nodata=np.nan,
              resampling=Resampling.average, **kw)
    marf = np.zeros((H, W), "float32")
    reproject(mar5.astype("float32"), marf, src_nodata=None, dst_nodata=0, resampling=Resampling.average, **kw)
    cub = np.zeros((H, W), "float32")
    reproject(np.ones_like(mar5, "float32"), cub, src_nodata=None, dst_nodata=0, resampling=Resampling.average, **kw)
    dist = np.zeros((H, W), "float32")
    reproject(dist5.astype("float32"), dist, src_nodata=None, dst_nodata=0, resampling=Resampling.bilinear, **kw)
    peso = np.where(cub > 0.999, np.clip(dist / TRANSICION_M, 0, 1), 0).astype("float32")
    mar = (cub > 0.999) & (marf >= 0.5)
    out = z.astype("float32").copy()
    tierra_cop = out != nodata
    ok = (peso > 0) & np.isfinite(zd)
    base = np.where(tierra_cop, out, zd)            # donde el Copernicus no tiene tierra y el DTM sí, manda el DTM
    out[ok] = (peso[ok] * zd[ok] + (1 - peso[ok]) * base[ok]).astype("float32")
    out[mar & (peso >= 1)] = nodata
    return out, peso, mar


def cobertura(crs="EPSG:4326", recorte_m=0.0):
    with rasterio.open(VRT) as d:
        b = d.bounds
        src = d.crs
    g = box(b.left + recorte_m, b.bottom + recorte_m, b.right - recorte_m, b.top - recorte_m)
    return shape(transform_geom(src, crs, g.__geo_interface__))
