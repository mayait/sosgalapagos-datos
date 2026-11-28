# Cañadas de Santa Cruz (GAD Municipal de Santa Cruz)

Las entregó el **GAD Municipal de Santa Cruz** a SOS Galápagos el 28-nov-2026, junto con ortofotos de dron de la misma zona. Las publicamos con su permiso y bajo **CC BY 4.0**.

> **Crédito:** «Cañadas: GAD Municipal de Santa Cruz (CC BY 4.0)».

## Archivos

| Archivo | Qué es |
|---|---|
| `canadas_santa_cruz.geojson` | 25 cañadas trazadas entre Bellavista y La Cascada, ≈ 49 km en total. Están en EPSG:4326 y tienen los campos `id`, `isla`, `longitud_m` (medida en UTM 15S) y `fuente` |
| `resumen.json` | Recuento, huella SHA-256 del GPX original y comparación con el drenaje derivado del relieve |

Los genera `geodatos/scripts/40_gad_santa_cruz_canadas.py` a partir de `descargas/gad_santa_cruz/canadas_gad_2026-11.gpx`, que queda fuera de git. **No se editan a mano.** El GPX tiene 26 rutas; una está vacía y se omite.

## Qué son y qué no

- Son **trazado del GAD**, no un cálculo de SOS. No sabemos todavía si se trazaron en campo, sobre las ortofotos o sobre un relieve; queda por confirmar con el GAD.
- Solo cubren el corredor de Bellavista a La Cascada. En el resto de la isla el drenaje que se ve es el del Instituto de Geografía USFQ.
- Contra el drenaje de la USFQ (DEM de 10 m), el 46 % del recorrido de las cañadas cae a 30 m o menos de algún cauce. Contra el drenaje de SOS sobre el DTM de la SGIAR, el 62 % cae a 30 m o menos. Las cifras exactas están en `resumen.json`.

## Dónde se usan

- En el mapa de `/riesgos/` como capa propia, «Cañadas trazadas por el GAD de Santa Cruz», dentro del grupo «Quebradas y drenaje».
- Las ortofotos y el GPX original están en el registro de Zenodo del GAD, pendiente de publicar.
