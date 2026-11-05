# DTM de 1 m de Santa Cruz (SGIAR)

Modelo digital del **terreno** (suelo desnudo, sin edificios ni vegetación) de 1 m de Puerto Ayora, el escarpe y Bellavista. Es un **dato institucional de la SGIAR**, no un modelo propio de SOS Galápagos.

> **Fuente:** SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo.
> Cite a la SGIAR cada vez que use, muestre o derive algo de este DTM.

## Cómo citarlo

> SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo (2026). *Modelo digital del terreno (DTM) de 1 m de Santa Cruz, Galápagos: Puerto Ayora y Bellavista* [conjunto de datos]. Producto Vricon DTM (Maxar), imágenes de 2020 a 2024, pedido 7032308101286995205. Recomprimido por SOS Galápagos (USFQ): https://github.com/mayait/sosgalapagos-datos/tree/main/geodatos/datos/dtm_sgiar

```bibtex
@misc{sgiar2026dtm,
  author       = {{SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo}},
  title        = {Modelo digital del terreno ({DTM}) de 1 m de Santa Cruz, Galápagos: Puerto Ayora y Bellavista},
  year         = {2026},
  howpublished = {Producto Vricon DTM (Maxar), imágenes de 2020 a 2024, pedido 7032308101286995205},
  note         = {Recomprimido por SOS Galápagos (USFQ), geodatos/datos/dtm\_sgiar}
}
```

En mapas y figuras basta con: **«DTM 1 m: SGIAR (Vricon/Maxar)»**.

## Ficha

| | |
|---|---|
| Producto | Vricon DTM (Maxar), estéreo satelital; software Vricon E v25.02.28 |
| Entrega | SGIAR, pedido 7032308101286995205 del 25-jul-2026 |
| Imágenes | 2-feb-2020 a 3-mar-2024. **No muestra cambios posteriores**, como los de las inundaciones de 2026 |
| Cobertura | 12,3 × 15,0 km (183 km²): lon −90,3916 a −90,2814, lat −0,7729 a −0,6378. Huella en `cobertura.geojson` |
| Resolución | 1 m, 4 teselas de hasta 8192 × 8192 celdas (se solapan 1 celda) |
| Proyección | EPSG:32715 (WGS84 G1674 / UTM 15 S). **No se reproyecta a EPSG:4326** para no remuestrear la malla de 1 m |
| Cotas | m sobre el geoide **EGM2008** (como el Copernicus GLO-30), en `float32`; sin datos = −32767 |
| Mar | Aparece como una superficie plana de unos 0,75 m (9 % del área). **No es batimetría** |
| Licencia | EULA de Vricon/Maxar, entregado por la SGIAR, que **autorizó su publicación en este repositorio**. La CC BY 4.0 del repositorio **no** se aplica (ver [`LICENCIA-DATOS.md`](../../../LICENCIA-DATOS.md)) |

## Archivos

| Archivo | Qué es |
|---|---|
| `dtm_sgiar_1m_<tesela>.tif` (4) | Teselas de 1 m, COG con compresión LERC_DEFLATE. Error máximo de la compresión: **1 cm** |
| `dtm_sgiar_1m.vrt` | Mosaico virtual de las 4 teselas. Ábralo en QGIS o GDAL como si fuera un solo raster |
| `dtm_sgiar_5m.tif` | Mosaico remuestreado a 5 m (promedio de 5 × 5 celdas), con vistas reducidas. Para mirar rápido o para modelos que no necesitan 1 m |
| `cobertura.geojson` | Huella en EPSG:4326 |
| `resumen.json` | Metadatos, tamaños, SHA-256 de los originales y control de calidad |
| `SHA256SUMS` | Sumas de verificación de los archivos de esta carpeta |

Los originales pesaban 422 MB (deflate sin pérdida). La recompresión los deja en 91 MB, y el archivo más grande pesa 35 MB, por debajo del límite de 100 MB de GitHub. La malla, la proyección y las cotas son las del original, con un error menor o igual a 1 cm, muy inferior a la exactitud del producto.

**Lo que no se sube:** el DSM, la `filling_mask` (vale 1 en todas las celdas) y el `request.json` del pedido (trae el correo de la cuenta y el bucket de entrega). El zip original queda en `geodatos/descargas/sgiar/`, que no va a git.

## Firma y verificación

Cada GeoTIFF lleva en sus metadatos:
- la fuente, en `TIFFTAG_ARTIST` y `FUENTE`;
- la cita, en `CITA`;
- la licencia, en `LICENCIA` y `TIFFTAG_COPYRIGHT`;
- el proceso, en `PROCESO`;
- el SHA-256 de la tesela original del proveedor, en `ORIGEN_SHA256`;
- las etiquetas `R3DM_*` de Vricon.

Para verlos: `gdalinfo dtm_sgiar_1m.vrt` o `gdalinfo <tesela>.tif`.

```bash
cd geodatos/datos/dtm_sgiar && shasum -a 256 -c SHA256SUMS
```

## Control de calidad

Los valores vienen de `resumen.json`, donde se recalculan cada vez que corre el script. Las diferencias están en metros.

| Comparación | n | Mediana | Desv. est. | p05 a p95 |
|---|---|---|---|---|
| DTM − puntos acotados IGM 1:25 000 | 1 264 | −1,0 | 3,5 | −6,4 a 3,6 |
| Copernicus GLO-30 − puntos IGM | 1 264 | −1,8 | 3,0 | −7,0 a 1,9 |
| DTM − Copernicus (malla de 100 m en tierra) | 16 704 | +1,2 | 2,8 | −3,0 a 4,6 |

- Las cotas del IGM son enteras y están referidas a su propio nivel medio del mar. Una diferencia de 1 m entre el DTM y el IGM no es, por sí sola, un error del DTM. Antes de usar cotas absolutas como umbrales, contrástelas con puntos GNSS ([#2](https://github.com/mayait/sosgalapagos-datos/issues/2), [#65](https://github.com/mayait/sosgalapagos-datos/issues/65)).
- El DTM queda en promedio 1 m **por encima** del Copernicus, aunque el Copernicus es un DSM (incluye techos y copas). Esto concuerda con el sesgo de −2 a −3 m del Copernicus frente al IGM que se describe en [`docs/modelo-hand.md`](../../../docs/modelo-hand.md).

## Uso en el proyecto

Es el DTM de 1 m que pedía el issue [#16](https://github.com/mayait/sosgalapagos-datos/issues/16) para Puerto Ayora, el escarpe y Bellavista. Todavía no alimenta ningún modelo. Rehacer HAND y el modelo 2D con él es el issue [#23](https://github.com/mayait/sosgalapagos-datos/issues/23). Cuando un script lo use, declárelo como entrada en `geodatos/flujo.toml`.

Lo que se calcule con este DTM (HAND, cuencas, modelo 2D) sigue siendo un **modelo propio**: hay que decirlo en mapas y textos, y citar a la SGIAR como fuente del relieve.

## Cómo se rehace

```bash
cd geodatos
.venv/bin/python -I scripts/35_dtm_sgiar.py            # lee descargas/sgiar/7032308101286995205.zip
```

El script comprueba el SHA-256 de cada tesela contra el `files.sha256` del proveedor y se detiene si alguna no coincide.
