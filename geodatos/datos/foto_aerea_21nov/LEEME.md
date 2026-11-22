# Foto aérea del 21-nov-2026 en Puerto Ayora: foto rectificada, zona afectada y edificios

**Estimación propia de SOS Galápagos por visión artificial. No es un dato oficial ni un censo de daños.**

**Crédito de la foto: Tui De Roy.** La foto y todo lo que se deriva de su imagen (la foto rectificada y sus teselas) son de su autora: no quedan bajo la licencia CC BY 4.0 del repositorio (ver `LICENCIA-DATOS.md`). Cítela siempre así: «Foto: Tui De Roy».

## Qué hay

| Archivo | Qué es |
|---|---|
| `ortofoto_21nov.tif` | La foto aérea oblicua del 21-nov-2026, rectificada al mapa. GeoTIFF RGB con máscara, EPSG:32715, 0,5 m por píxel. Cubre desde el escarpe de La Cascada hasta el malecón (≈ 178 ha) |
| `zona_inundada_foto_21nov.geojson` | Zona afectada (≈ 28 ha), suavizada y partida en cuatro clases de **gravedad aparente** (campo `gravedad`, de 1 leve a 4 muy grave) |
| `edificios_afectados_foto_21nov.geojson` | Los 742 edificios del mapa dentro de la zona, con `gravedad`, `tamano`, `pisos_est`, `altura_m`, `viviendas_est` y `personas_est` |
| `resumen_estimacion.json` | Totales: edificios, pisos, familias y personas, por gravedad y por tamaño, y el contraste con el censo |
| `camara.json` | Posición y orientación de la cámara que se ajustó para proyectar la foto |
| `estimacion_21nov.geojson`, `estimacion_21nov.jpg` | **Fuente curada.** La estimación de familias afectadas (450 a 870) como un punto con hora (14:00), y la foto con la zona y los edificios marcados. Sale en la línea del tiempo de `/riesgos/informe/` |

## Cómo se hizo

1. **Cámara.** La foto se tomó a las 14:00 (hora de Galápagos) desde unos 520 m de altura, unos 500 m al norte del borde de La Cascada, mirando al sur-suroeste. Se ajustó un modelo de cámara con 20 puntos de control (estadio, reservorio, paneles solares, techos grandes) sobre el **DTM 1 m: SGIAR (Vricon/Maxar)**. El error mediano es de 6 píxeles, unos 3 a 6 m en el suelo cerca de La Cascada y más hacia el malecón.
2. **Foto rectificada.** Cada punto del suelo toma el color del píxel de la foto que lo mira. **No es una ortofoto verdadera:** sale de una sola foto oblicua de 1600 px, así que los edificios aparecen «acostados» hacia el sur y lo que tapan no se ve. Sirve para ubicar, no para medir fachadas.
3. **Agua.** Tres modelos sobre la foto (regla de color para el agua turbia, k-medias sin supervisión y bosque aleatorio con textura); se toma el consenso de dos de tres y se proyecta al mapa. A eso se suma una franja de 12 m alrededor del agua vista (los frentes de las calles con agua) y las áreas que el coordinador de SOS Galápagos marcó a mano sobre la foto.
4. **Zona suavizada.** La zona de agua se cierra sobre las manzanas rodeadas de agua (un edificio rodeado por calles inundadas cuenta como afectado) y se suaviza el borde.
5. **Gravedad aparente.** Para cada punto: la fracción del suelo sin edificar que se ve con agua a su alrededor (a 14 m y a 34 m; vale la mayor). Menos de 12 % es leve; de 12 a 32 %, moderada; de 32 a 55 %, grave; más de 55 %, muy grave. Si hay un reporte ciudadano a menos de 45 m, la clase sube hasta la gravedad de ese reporte. **No mide profundidad.**
6. **Edificios.** Huellas de OpenStreetMap y Google Open Buildings con el centro dentro de la zona: 742. Una muestra de 16 celdas de 60 m, inventariada edificio por edificio sobre la foto (139 edificios), da 1,045 edificios por cada huella: unos 775 edificios.
7. **Pisos, familias y personas.** No se miden edificio por edificio. En la muestra, los edificios pequeños tienen 1,1 pisos de media, los medianos 1,4 y los grandes 1,8 (3 m por piso). Las huellas del mapa se reparten en pequeñas, medianas y grandes en la misma proporción que la muestra, por orden de área. Viviendas por edificio = máx(1; pisos × huella × 0,80 ÷ 60 m²), con huella de 45, 75 o 120 m² y uso dudoso contado a la mitad; una familia por vivienda y 3,25 personas por hogar. Resultado: 1.308 familias (1.135 a 1.483) y 4.252 personas. El censo, repartido por manzana, da 691 viviendas y 2.957 personas. **Rango que se publica: entre 690 y 1.310 familias y entre 2.950 y 4.250 personas.**

En el mapa de `/riesgos/`, la capa de edificios lleva `extrusion` en `visor_mapas.json`: en la vista 3D se enciende sola y cada edificio se levanta hasta `altura_m` con el color de su gravedad.

## Límites

- La zona no dice profundidad: la foto no deja ver la orilla real del agua entre las casas. «Gravedad» es lo que aparenta la foto.
- Los pisos, familias y personas de cada edificio son promedios de su tamaño: sirven para sumar, no para un edificio concreto.
- Un edificio no es una vivienda: hay locales, galpones y casas con varios hogares.
- El trazo a mano es aproximado. Todo está **por validar** en campo.
- Sin nombres ni datos personales.

## Qué se versiona y qué no

Aquí están los resultados. La foto original y los scripts de detección (necesitan la foto, SAM y scikit-learn, que no están en `requirements.txt`) quedan en local, fuera del repositorio. Las teselas se generan con `scripts/est_21nov_foto_teselas.py` y no van a git.
