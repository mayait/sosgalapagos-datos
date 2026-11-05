#!/usr/bin/env python3
"""DTM de 1 m de Santa Cruz (Puerto Ayora–Bellavista) entregado por la SGIAR: lo prepara para el repositorio.

Fuente
  SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo. Producto «Vricon DTM» (Maxar),
  1 m, EPSG:32715 (UTM 15 S, WGS84 G1674), cotas sobre el geoide EGM2008, imágenes de 2020-02 a 2024-03.
  Pedido 7032308101286995205 (25-jul-2026). Es un DATO de la institución, no un modelo propio.

Qué hace
  1. Comprueba la integridad del zip original: el SHA-256 de cada tesela DTM contra el files.sha256 del proveedor.
  2. Recomprime las 4 teselas a COG con LERC_DEFLATE y error máximo de 1 cm (148 MB → 28 MB la mayor), para que
     cada archivo quede muy por debajo del límite de 100 MB de GitHub. No reproyecta ni remuestrea: la malla,
     la proyección y las cotas son las del original (± 1 cm).
  3. «Firma» cada GeoTIFF: escribe en sus metadatos la fuente (SGIAR), la cita, la licencia, el proceso y el
     SHA-256 de la tesela original. Conserva las etiquetas R3DM_* del proveedor.
  4. Arma el mosaico virtual (dtm_sgiar_1m.vrt), un mosaico remuestreado a 5 m (promedio) y la huella en EPSG:4326.
  5. Control de calidad: compara las cotas con los puntos acotados del IGM 1:25 000 y con el Copernicus GLO-30.
  6. Escribe resumen.json y SHA256SUMS (se verifica con «shasum -a 256 -c SHA256SUMS» dentro de la carpeta).

No se copian al repositorio: el request.json (trae el correo de la cuenta y el bucket de entrega), el DSM ni la
filling_mask (vale 1 en todas las celdas, no aporta información).

Uso, desde geodatos/:
  .venv/bin/python -I scripts/35_dtm_sgiar.py                       # lee descargas/sgiar/7032308101286995205.zip
  .venv/bin/python -I scripts/35_dtm_sgiar.py --zip RUTA/AL/ZIP
Salidas: datos/dtm_sgiar/
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.shutil import copy as rio_copy
from rasterio.warp import transform, transform_geom

ROOT = Path(__file__).resolve().parent.parent
ZIP_POR_OMISION = ROOT / "descargas/sgiar/7032308101286995205.zip"
OUT = ROOT / "datos/dtm_sgiar"
IGM_PUNTOS = ROOT / "capas/igm/punto_acotado_p.geojson"
COPERNICUS = ROOT / "descargas/dem/Copernicus_DSM_COG_10_S01_00_W091_00_DEM.tif"

ERROR_MAX = 0.01  # m, error máximo de la compresión LERC
FUENTE = "SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo"
TITULO = "Modelo digital del terreno (DTM) de 1 m de Santa Cruz, Galápagos: Puerto Ayora y Bellavista"
CITA = (f"{FUENTE} (2026). {TITULO} [conjunto de datos]. Producto Vricon DTM (Maxar), imágenes de 2020 a 2024, "
        "pedido 7032308101286995205. Recomprimido por SOS Galápagos (USFQ): "
        "https://github.com/mayait/sosgalapagos-datos/tree/main/geodatos/datos/dtm_sgiar")
LICENCIA = ("Dato de la SGIAR sobre un producto de Vricon/Maxar, sujeto al EULA de Vricon. La SGIAR autorizó su "
            "publicación en este repositorio. Cite a la SGIAR en todo uso. La licencia CC BY 4.0 del repositorio no se aplica a este dato (ver LICENCIA-DATOS.md).")
COPYRIGHT = "Vricon DTM, Copyright 2026 Vricon Inc. (Maxar); uso limitado por el EULA de Vricon. Provisto por la SGIAR."


def sha256(fh, bloque=1 << 22):
    h = hashlib.sha256()
    for trozo in iter(lambda: fh.read(bloque), b""):
        h.update(trozo)
    return h.hexdigest()


def sha256_archivo(ruta):
    with open(ruta, "rb") as fh:
        return sha256(fh)


def stats(d):
    d = np.asarray(d, float)
    if not len(d):
        return {"n": 0}
    return {"n": int(len(d)), "media": round(float(d.mean()), 2), "mediana": round(float(np.median(d)), 2),
            "desv_est": round(float(d.std()), 2), "p05": round(float(np.percentile(d, 5)), 2),
            "p95": round(float(np.percentile(d, 95)), 2),
            "emc": round(float(np.sqrt((d ** 2).mean())), 2)}


def escribir_cog(datos, perfil, destino, overviews, **etiquetas):
    """GeoTIFF en memoria con metadatos («firma») → COG LERC; así las etiquetas quedan dentro del COG."""
    perfil = {k: perfil[k] for k in ("crs", "transform", "nodata")} | {
        "driver": "GTiff", "dtype": "float32", "count": 1, "height": datos.shape[0], "width": datos.shape[1]}
    with MemoryFile() as mem:
        with mem.open(**perfil) as d:
            d.write(datos, 1)
            d.update_tags(**etiquetas)
            d.set_band_description(1, "elevacion_m_egm2008")
        with mem.open() as d:
            rio_copy(d, destino, driver="COG", compress="LERC_DEFLATE", max_z_error=ERROR_MAX, blocksize=512,
                     overviews=overviews, overview_resampling="average", bigtiff="NO")


def escribir_vrt(teselas, ruta):
    """Mosaico virtual con rutas relativas (sin gdalbuildvrt)."""
    ds = [rasterio.open(t) for t in teselas]
    try:
        izq = min(d.bounds.left for d in ds); der = max(d.bounds.right for d in ds)
        aba = min(d.bounds.bottom for d in ds); arr = max(d.bounds.top for d in ds)
        res = ds[0].res[0]
        ancho, alto = round((der - izq) / res), round((arr - aba) / res)
        fuentes = []
        for t, d in zip(teselas, ds):
            x0, y0 = round((d.bounds.left - izq) / res), round((arr - d.bounds.top) / res)
            fuentes.append(f"""    <ComplexSource>
      <SourceFilename relativeToVRT="1">{Path(t).name}</SourceFilename>
      <SourceBand>1</SourceBand>
      <SourceProperties RasterXSize="{d.width}" RasterYSize="{d.height}" DataType="Float32" BlockXSize="512" BlockYSize="512" />
      <SrcRect xOff="0" yOff="0" xSize="{d.width}" ySize="{d.height}" />
      <DstRect xOff="{x0}" yOff="{y0}" xSize="{d.width}" ySize="{d.height}" />
      <NODATA>{d.nodata}</NODATA>
    </ComplexSource>""")
        wkt = ds[0].crs.to_wkt()
        nodata = ds[0].nodata
    finally:
        for d in ds:
            d.close()
    xml = f"""<VRTDataset rasterXSize="{ancho}" rasterYSize="{alto}">
  <SRS dataAxisToSRSAxisMapping="1,2">{wkt.replace('"', '&quot;')}</SRS>
  <GeoTransform>{izq:.1f}, {res:.1f}, 0.0, {arr:.1f}, 0.0, {-res:.1f}</GeoTransform>
  <Metadata>
    <MDI key="FUENTE">{FUENTE}</MDI>
    <MDI key="CITA">{CITA}</MDI>
  </Metadata>
  <VRTRasterBand dataType="Float32" band="1">
    <Description>elevacion_m_egm2008</Description>
    <NoDataValue>{nodata}</NoDataValue>
{chr(10).join(fuentes)}
  </VRTRasterBand>
</VRTDataset>
"""
    ruta.write_text(xml)
    return (izq, aba, der, arr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--zip", type=Path, default=ZIP_POR_OMISION)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Integridad del original y metadatos del proveedor
    with zipfile.ZipFile(args.zip) as z:
        nombres = z.namelist()
        base = next(n for n in nombres if n.endswith("/vricon_raster_1m/dtm/files.sha256")).rsplit("/", 1)[0]
        esperado = {}
        for linea in z.read(f"{base}/files.sha256").decode().splitlines():
            h, nombre = linea.split(maxsplit=1)
            esperado[nombre.lstrip("*").removeprefix("./")] = h
        meta = json.loads(z.read(f"{base}/metadata.json"))
        pedido = json.loads(z.read(next(n for n in nombres if n.endswith("-request.json"))))
        teselas_zip = sorted(n for n in nombres if n.startswith(f"{base}/data/") and n.endswith("_dtm.tif"))
        sha_origen = {}
        tam_origen = {n: z.getinfo(n).file_size for n in teselas_zip}
        for n in teselas_zip:
            rel = n.removeprefix(f"{base}/")
            with z.open(n) as fh:
                h = sha256(fh)
            if h != esperado.get(rel):
                raise SystemExit(f"SHA-256 no coincide en {rel}: {h} ≠ {esperado.get(rel)}")
            sha_origen[rel] = h
    print(f"Integridad del original: {len(teselas_zip)} teselas DTM coinciden con files.sha256")

    # 2–3. Recompresión y firma
    comunes = dict(TIFFTAG_ARTIST=FUENTE, TIFFTAG_COPYRIGHT=COPYRIGHT,
                   TIFFTAG_SOFTWARE="SOS Galápagos, geodatos/scripts/35_dtm_sgiar.py (rasterio/GDAL)",
                   FUENTE=FUENTE, CITA=CITA, LICENCIA=LICENCIA,
                   DATO="Dato institucional (SGIAR), no es un modelo propio de SOS Galápagos",
                   DATUM_VERTICAL="EGM2008", DATUM_HORIZONTAL="WGS84 G1674 (EPSG:32715, UTM 15 S)",
                   ORIGEN_PEDIDO=pedido["id"], ORIGEN_UUID=meta["uuid"])
    salidas = []
    for n in teselas_zip:
        rel = n.removeprefix(f"{base}/")
        tesela = re.match(r".*/(\d{7}w_\d{6}s)_", n).group(1)
        destino = OUT / f"dtm_sgiar_1m_{tesela}.tif"
        with rasterio.open(f"/vsizip/{args.zip}/{n}") as s:
            a = s.read(1)
            nodata = s.nodata
            perfil = s.profile
            proveedor = {k: v for k, v in s.tags().items() if k.startswith("R3DM_")}
        escribir_cog(a, perfil, destino, overviews="NONE", **proveedor, **comunes,
                     TIFFTAG_IMAGEDESCRIPTION=f"{TITULO}. Tesela {tesela}. Cota en m sobre EGM2008.",
                     PROCESO=f"Recompresión LERC_DEFLATE, error máximo {ERROR_MAX * 100:.0f} cm; "
                             "sin reproyectar ni remuestrear",
                     ORIGEN_ARCHIVO=Path(rel).name, ORIGEN_SHA256=sha_origen[rel])
        with rasterio.open(destino) as d:
            b = d.read(1)
        err = float(np.abs(b.astype(float) - a.astype(float))[a != nodata].max())
        if err > ERROR_MAX * 1.001:
            raise SystemExit(f"{destino.name}: error de compresión {err:.4f} m > {ERROR_MAX} m")
        salidas.append({"archivo": destino.name, "origen": Path(rel).name, "sha256_origen": sha_origen[rel],
                        "mb_origen": round(tam_origen[n] / 1e6, 1),
                        "mb": round(destino.stat().st_size / 1e6, 1), "error_max_m": round(err, 4)})
        print(f"  {destino.name}: {salidas[-1]['mb_origen']} → {salidas[-1]['mb']} MB, error máx. {err * 100:.2f} cm")
        del a, b
    teselas = [OUT / s["archivo"] for s in salidas]

    # 4. Mosaico virtual, mosaico a 5 m y huella
    vrt = OUT / "dtm_sgiar_1m.vrt"
    izq, aba, der, arr = escribir_vrt(teselas, vrt)
    ds = [rasterio.open(t) for t in teselas]
    mosaico, tr = merge(ds, res=5, resampling=Resampling.average, nodata=ds[0].nodata)
    perfil = ds[0].profile | {"height": mosaico.shape[1], "width": mosaico.shape[2], "transform": tr}
    for d in ds:
        d.close()
    escribir_cog(mosaico[0], perfil, OUT / "dtm_sgiar_5m.tif", overviews="AUTO", **comunes,
                 TIFFTAG_IMAGEDESCRIPTION=f"{TITULO}. Mosaico remuestreado a 5 m (promedio de 5×5 celdas).",
                 PROCESO="Mosaico de las 4 teselas de 1 m, promedio a 5 m, LERC_DEFLATE error máx. 1 cm")

    caja = {"type": "Polygon", "coordinates": [[[izq, aba], [der, aba], [der, arr], [izq, arr], [izq, aba]]]}
    caja4326 = transform_geom("EPSG:32715", "EPSG:4326", caja, precision=6)
    huella = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": caja4326, "properties": {
        "nombre": "DTM 1 m SGIAR, Santa Cruz", "fuente": FUENTE, "resolucion_m": 1.0,
        "adquisicion": "2020-02 a 2024-03", "datum_vertical": "EGM2008"}}]}
    (OUT / "cobertura.geojson").write_text(json.dumps(huella, ensure_ascii=False))

    # 5. Control de calidad frente al IGM y al Copernicus GLO-30
    puntos = json.loads(IGM_PUNTOS.read_text())["features"]
    lon = np.array([p["geometry"]["coordinates"][0] for p in puntos])
    lat = np.array([p["geometry"]["coordinates"][1] for p in puntos])
    z_igm = np.array([float(p["properties"]["z"]) for p in puntos])
    xs, ys = transform("EPSG:4326", "EPSG:32715", lon, lat)
    xs, ys = np.array(xs), np.array(ys)
    dentro = (xs > izq + 5) & (xs < der - 5) & (ys > aba + 5) & (ys < arr - 5)
    with rasterio.open(vrt) as d:
        z_dtm = np.array([v[0] for v in d.sample(zip(xs[dentro], ys[dentro]))], float)
        nd = d.nodata
    z_i = z_igm[dentro]
    ok = (z_dtm != nd) & (z_i > 0)
    control = {"puntos_igm_en_cobertura": int(dentro.sum()),
               "dtm_menos_igm_m": stats(z_dtm[ok] - z_i[ok])}
    if COPERNICUS.exists():
        with rasterio.open(COPERNICUS) as c:
            z_cop = np.array([v[0] for v in c.sample(zip(lon[dentro], lat[dentro]))], float)
        control["copernicus_menos_igm_m"] = stats(z_cop[ok] - z_i[ok])
        # Diferencia de superficie: DTM (suelo) − Copernicus (DSM, incluye techos y copas), en una malla de 100 m
        gx, gy = np.meshgrid(np.arange(izq + 50, der, 100), np.arange(aba + 50, arr, 100))
        glon, glat = transform("EPSG:32715", "EPSG:4326", gx.ravel(), gy.ravel())
        with rasterio.open(vrt) as d:
            gd = np.array([v[0] for v in d.sample(zip(gx.ravel(), gy.ravel()))], float)
        with rasterio.open(COPERNICUS) as c:
            gc = np.array([v[0] for v in c.sample(zip(glon, glat))], float)
        tierra = (gd != nd) & (gc > 1)
        control["dtm_menos_copernicus_malla_100m_m"] = stats(gd[tierra] - gc[tierra])
    control["nota"] = ("IGM: puntos acotados 1:25 000 (cota entera). Copernicus GLO-30 es un DSM (techos y copas). "
                       "Diferencias en m; emc = error medio cuadrático.")
    print("Control:", json.dumps(control, ensure_ascii=False))

    # 6. Resumen y sumas de verificación
    resumen = {
        "titulo": TITULO, "fuente": FUENTE, "cita": CITA, "licencia": LICENCIA, "copyright_proveedor": COPYRIGHT,
        "tipo": "dato institucional (no es modelo propio)",
        "producto": meta["product"], "software_proveedor": meta["software"],
        "pedido": pedido["id"], "fecha_pedido": pedido["date_created"], "uuid": meta["uuid"],
        "adquisicion": {"primera": meta["acquisition"]["first-date"], "ultima": meta["acquisition"]["last-date"]},
        "crs": "EPSG:32715 (WGS84 G1674 / UTM 15 S)", "datum_vertical": meta["srs"]["vertical-datum"],
        "resolucion_m": meta["post-spacing"], "unidad": "m",
        "extension_utm": [round(izq, 1), round(aba, 1), round(der, 1), round(arr, 1)],
        "extension_4326": caja4326["coordinates"][0],
        "area_km2": round((der - izq) * (arr - aba) / 1e6, 1),
        "compresion": f"COG LERC_DEFLATE, error máximo {ERROR_MAX * 100:.0f} cm",
        "teselas": salidas, "control_calidad": control,
        "no_incluido": ["DSM (no se pidió)", "filling_mask (vale 1 en todas las celdas)",
                        "request.json (correo de la cuenta y bucket de entrega)"],
        "script": "geodatos/scripts/35_dtm_sgiar.py",
    }
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    lineas = [f"{sha256_archivo(p)}  {p.name}" for p in sorted(OUT.iterdir())
              if p.is_file() and p.name not in ("SHA256SUMS", "LEEME.md")]
    (OUT / "SHA256SUMS").write_text("\n".join(lineas) + "\n")
    total = sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()) / 1e6
    print(f"Listo: {OUT.relative_to(ROOT)} ({total:.0f} MB, el mayor {max(s['mb'] for s in salidas)} MB)")


if __name__ == "__main__":
    main()
