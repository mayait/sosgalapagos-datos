# Foto aérea del 21-nov-2026 en Puerto Ayora: foto rectificada, zona inundada y techos

**Estimación propia de SOS Galápagos por visión artificial. No es un dato oficial ni un censo de daños.**

**Crédito de la foto: Tui De Roy.** La foto y todo lo que se deriva de su imagen (la foto rectificada y sus teselas) son de su autora: no quedan bajo la licencia CC BY 4.0 del repositorio (ver `LICENCIA-DATOS.md`). Cítela siempre así: «Foto: Tui De Roy».

## Qué hay

| Archivo | Qué es |
|---|---|
| `ortofoto_21nov.tif` | La foto aérea oblicua del 21-nov-2026, rectificada al mapa. GeoTIFF RGB con máscara, EPSG:32715, 0,5 m por píxel. Cubre desde el escarpe de La Cascada hasta el malecón (≈ 178 ha) |
| `zona_inundada_foto_21nov.geojson` | Zona inundada estimada (≈ 21 ha). Campo `origen`: «Agua detectada en la foto» o «Marcado a mano por el coordinador» |
| `techos_foto_21nov.geojson` | 392 techos segmentados con SAM dentro de esa zona, uno por polígono |
| `camara.json` | Posición y orientación de la cámara que se ajustó para proyectar la foto |
| `estimacion_21nov.geojson`, `estimacion_21nov.jpg` | **Fuente curada.** La estimación de familias afectadas (450 a 870) como un punto con hora (14:00), y la foto con la zona y los edificios marcados. Sale en la línea del tiempo de `/riesgos/informe/` |

## Cómo se hizo

1. **Cámara.** La foto se tomó a las 14:00 (hora de Galápagos) desde unos 520 m de altura, unos 500 m al norte del borde de La Cascada, mirando al sur-suroeste. Se ajustó un modelo de cámara con 20 puntos de control (estadio, reservorio, paneles solares, techos grandes) sobre el **DTM 1 m: SGIAR (Vricon/Maxar)**. El error mediano es de 6 píxeles, unos 3 a 6 m en el suelo cerca de La Cascada y más hacia el malecón.
2. **Foto rectificada.** Cada punto del suelo toma el color del píxel de la foto que lo mira. **No es una ortofoto verdadera:** sale de una sola foto oblicua de 1600 px, así que los edificios aparecen «acostados» hacia el sur y lo que tapan no se ve. Sirve para ubicar, no para medir fachadas.
3. **Agua.** Tres modelos sobre la foto (regla de color para el agua turbia, k-medias sin supervisión y bosque aleatorio con textura); se toma el consenso de dos de tres y se proyecta al mapa. La zona suma una franja de 12 m alrededor del agua vista (los frentes de las calles con agua) y las áreas que el coordinador de SOS Galápagos marcó a mano sobre la foto.
4. **Techos.** Segmentación automática con SAM (Segment Anything) por mosaicos ampliados de la foto. Se quedan los techos claros y anaranjados dentro de la zona. **Cuenta de menos:** no separa las losas de hormigón gris ni las terrazas oscuras. En la misma zona el mapa tiene 493 huellas de edificios (OSM + Google Open Buildings) y una muestra de 16 celdas da unos 515 edificios (451 a 580).

## Límites

- La zona no dice profundidad: la foto no deja ver la orilla real del agua entre las casas.
- Un techo no es una vivienda: hay locales, galpones y casas con varios hogares.
- El trazo a mano es aproximado. Todo está **por validar** en campo.
- Sin nombres ni datos personales.

## Qué se versiona y qué no

Aquí están los resultados. La foto original y los scripts de detección (necesitan la foto, SAM y scikit-learn, que no están en `requirements.txt`) quedan en local, fuera del repositorio. Las teselas se generan con `scripts/est_21nov_foto_teselas.py` y no van a git.
