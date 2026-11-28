# Cañadas de Santa Cruz (GAD Municipal de Santa Cruz)

Las entregó el **GAD Municipal de Santa Cruz** a SOS Galápagos el 28-nov-2026, junto con ortofotos de dron de la misma zona. Las publicamos con su permiso y bajo **CC BY 4.0**.

> **Crédito:** «Cañadas: GAD Municipal de Santa Cruz (CC BY 4.0)».

## Archivos

| Archivo | Qué es |
|---|---|
| `canadas_santa_cruz.geojson` | 25 cañadas trazadas entre Bellavista y La Cascada, ≈ 49 km en total. Están en EPSG:4326 y tienen los campos `id`, `isla`, `longitud_m` (medida en UTM 15S) y `fuente` |
| `vias_con_canada.geojson` | 17 tramos de vía de OpenStreetMap (4,9 km) por donde corre una cañada del GAD: más de 80 m seguidos con la cañada a 10 m o menos de la calle. Son calles que funcionaron como cauce |
| `resumen.json` | Recuento, huella SHA-256 del GPX original y comparación con el drenaje derivado del relieve |

Los genera `geodatos/scripts/40_gad_santa_cruz_canadas.py` a partir de `descargas/gad_santa_cruz/canadas_gad_2026-11.gpx`, que queda fuera de git. **No se editan a mano.** El GPX tiene 26 rutas; una está vacía y se omite.

## Qué son y qué no

- Son **trazado del GAD**, no un cálculo de SOS. No sabemos todavía si se trazaron en campo, sobre las ortofotos o sobre un relieve; queda por confirmar con el GAD.
- Solo cubren el corredor de Bellavista a La Cascada. En el resto de la isla el drenaje que se ve es el del Instituto de Geografía USFQ.
- Contra el drenaje de la USFQ (DEM de 10 m), el 46 % del recorrido de las cañadas cae a 30 m o menos de algún cauce. Contra el drenaje de SOS sobre el DTM de la SGIAR, el 62 % cae a 30 m o menos. Las cifras exactas están en `resumen.json`.

## Calidad del trazado

Revisamos sobre las ortofotos los tramos que se alejan de nuestro drenaje. El trazado es desigual:
- Algunas cañadas siguen con precisión cicatrices de erosión que se ven en las fotos.
- Otras corren por la calzada, por donde bajó el agua; de ahí salen las «calles con cañada».
- Otras son tramos rectos sobre bosque cerrado, sin cauce visible ni en la foto ni en el DTM de la SGIAR, y parecen esquemáticas.

Por eso **no se marcan en el relieve** que usan la HAND y el modelo 2D: una línea corrida inventaría un cauce que no existe en el DTM de 5 m.

## Dónde se usan

- En el mapa de `/riesgos/` como capa propia, «Cañadas trazadas por el GAD de Santa Cruz», dentro del grupo «Quebradas y drenaje», y en la capa «Calles por donde corre una cañada».
- Como cauce en los cruces con vías (`16_cruces_quebradas_vias.py`). Donde la cañada corre por la vía no se cuenta como cruce.
- Las ortofotos se ven en el mapa como teselas (`41_teselas_ortofotos_gad.py`, salen de `descargas/gad_santa_cruz/ortofotos/`).
- Las ortofotos y el GPX original están en el registro de Zenodo del GAD, pendiente de publicar.
