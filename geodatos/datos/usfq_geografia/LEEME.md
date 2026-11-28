# Cuencas, subcuencas y drenaje de Santa Cruz (Instituto de Geografía USFQ, DEM de 10 m de SIGTIERRAS)

Entrega del **Instituto de Geografía de la USFQ** (María Belén Zapata) a SOS Galápagos, el 24-nov-2026. Se procesó en **SAGA GIS** sobre el **DEM de 10 m de SIGTIERRAS** y se exportó desde ArcGIS Pro.

> **Crédito:** «Cuencas y drenaje: Instituto de Geografía USFQ (María Belén Zapata), sobre el DEM 10 m de SIGTIERRAS».

## Archivos

| Archivo | Qué es |
|---|---|
| `cuencas_santa_cruz.geojson` | 186 cuencas que desembocan al mar (911,8 km² en total; la mayor, 54,4 km²) |
| `subcuencas_santa_cruz.geojson` | 1 186 subcuencas (mediana 0,63 km²); `cuenca_principal` dice a qué cuenca pertenecen |
| `drenaje_santa_cruz.geojson` | 1 222 tramos de cauce (1 550 km) con orden de Strahler y magnitud de Shreve |
| `resumen.json` | Recuento, huella del zip (SHA-256) y datos del DEM |

Todo en EPSG:4326. Lo genera `geodatos/scripts/38_usfq_cuencas_sigtierras.py` a partir de `descargas/usfq_geografia/GALAPAGOS-SCRUZ.zip` (fuera de git). **No se edita a mano.**

## Proyección de origen

WGS 84 / UTM zona 15 S (EPSG:32715). Lo indicó la autora y lo confirman los `.prj`.

## Campos

Los nombres vienen de SAGA, truncados a 10 caracteres por el formato shapefile. El significado de algunos se dedujo de los valores; **por confirmar con el Instituto** los marcados con «?».

| Campo aquí | Campo SAGA | Qué es |
|---|---|---|
| `id`, `cuenca_principal` | `ID`, `Main Basin` | Número de la (sub)cuenca y de su cuenca |
| `area_km2`, `perimetro_km` | `Area`, `Perimeter` | En m² y m en el origen |
| `cota_media_m` | `Mean Elevation` | Cota media de la cuenca (m) |
| `desnivel_m` | `Elevation` | Desnivel de la cuenca (m) ? |
| `longitud_flujo_max_km`, `longitud_flujo_media_km` | `Maximum Flow`, `Mean Flow` | Recorrido del agua hasta la salida (m en el origen) ? |
| `tiempo_concentracion_h` | `Concentration` | Tiempo de concentración (h) ? |
| `forma` | `Basin Type` | Forma de la cuenca (rectangular, oval-oblonga…) |
| `coef_orografico`, `coef_masividad` | `Orographic`, `Massivity` | Coeficientes de relieve de SAGA |
| `desembocadura` | `Outlet X/Y` | Salida de la cuenca, en lon/lat |
| `magnitud_shreve` | `Order` | Número de cabeceras aguas arriba. En el zip se llama «Order», pero en cada confluencia el valor de abajo es la **suma** de los de arriba (Shreve), no el orden de Strahler. En 6 confluencias no suma exacto |
| `orden_strahler`, `jerarquia` | — | Calculado en `38_…py` con la topología de los tramos: 687 de orden 1, 350 de 2, 166 de 3 y 19 de 4 |
| `longitud_m` | — | Longitud del tramo, calculada de la geometría (el campo `Length` del zip solo mide el último paso de 10–14 m) |

Simplificación: 8 m en los polígonos (vienen en escalera de 10 m) y 3 m en las líneas.

## El DEM de 10 m

`santa_cruz.tif`: 4 250 × 3 242 celdas de 10 m, 981 km² con dato, cotas de −7,3 a 868,9 m. **No va a git** hasta confirmar si se puede redistribuir; queda en `descargas/usfq_geografia/santa_cruz_sigtierras_10m.tif`.

Control (28-nov-2026):

| Comparación | Mediana | Error absoluto medio |
|---|---|---|
| Frente a 7 859 puntos acotados IGM 1:25 000 | −0,04 m | 0,52 m |
| Copernicus GLO-30 frente a los mismos puntos | −1,89 m | 2,70 m |
| DTM SGIAR (1 m) frente a 1 263 de esos puntos | −1,07 m | 2,52 m |
| SIGTIERRAS − DTM SGIAR, cotas de 2 a 30 m (Puerto Ayora) | −1,10 m | — |
| SIGTIERRAS − DTM SGIAR, cotas de 30 a 900 m | +1,6 a +2,9 m | — |

- Es de **terreno**: en la ciudad queda bajo el DTM de la SGIAR, no por encima como un DSM con techos.
- Coincide tanto con el IGM que es probable que se haya hecho en parte con esa cartografía. Por eso esos puntos **no son un control independiente**.
- **Nunca mezcles umbrales** de un relieve con los de otro: SIGTIERRAS, el DTM de la SGIAR y el Copernicus tienen cotas distintas (ver tabla).

Desde el 28-nov-2026 es el relieve de Santa Cruz fuera del DTM de la SGIAR (`relieve_sigtierras.py`, `03_dem.py`): HAND, cauces, costa baja y curvas se calculan ahí en una malla de 10 m.
