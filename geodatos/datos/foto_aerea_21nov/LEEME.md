# Foto aérea del 21-nov-2026 en Puerto Ayora: foto rectificada, zona afectada y edificios

**Estimación propia de SOS Galápagos por visión artificial. No es un dato oficial ni un censo de daños.**

**Crédito de la foto: Tui De Roy.** La foto y todo lo que se deriva de su imagen (la foto rectificada y sus teselas) son de su autora: no quedan bajo la licencia CC BY 4.0 del repositorio (ver `LICENCIA-DATOS.md`). Cítela siempre así: «Foto: Tui De Roy».

## Qué hay

| Archivo | Qué es |
|---|---|
| `ortofoto_21nov.tif` | La foto aérea oblicua del 21-nov-2026, rectificada al mapa. GeoTIFF RGB con máscara, EPSG:32715, 0,5 m por píxel. Cubre desde el escarpe de La Cascada hasta el malecón (≈ 178 ha) |
| `zona_inundada_foto_21nov.geojson` | Zona afectada (≈ 28 ha), suavizada y partida en cuatro clases de **gravedad aparente** (campo `gravedad`, de 1 leve a 4 muy grave) |
| `edificios_afectados_foto_21nov.geojson` | Los 1.009 edificios dentro de la zona, redibujados sobre las ortofotos de dron del GAD de Santa Cruz (desde el 28-nov-2026; ver «Edificios sobre las ortofotos del GAD»), con `gravedad`, `tamano`, `area_m2`, `huella`, `altura_m`, `altura_medida`, `pisos_est`, `viviendas_est` y `personas_est` |
| `resumen_edificios_ortofotos.json` | Recuento de los edificios redibujados: cuántos salen de la ortofoto, cuántos conservan la huella vieja y por qué, por gravedad |
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

Los pasos 6 y 7 son los de la estimación publicada (22-nov). Los edificios de la capa se redibujaron después; ver la sección siguiente.

## Edificios sobre las ortofotos del GAD (28-nov-2026)

Las huellas de OpenStreetMap y Google eran cajas aproximadas, con errores locales de 1 a 4 m; faltaban edificios y sobraban otros. `scripts/45_edificios_ortofotos.py` las rehace sobre las ortofotos de dron del GAD Municipal de Santa Cruz (CC BY 4.0) del 3 y el 5-nov-2026, que cubren 24 de las 28 ha:

1. **Posición.** Las ortofotos estaban corridas de 2 a 3,5 m. Se calzan con el DSM de 1 m de la SGIAR (ver `datos/gad_santa_cruz/LEEME.md`); el residuo queda en 0,2 a 0,3 m.
2. **Techos.** SAM 2.1 (segmentación automática y puntos semilla en las huellas viejas y en los bultos del DSM), en mosaicos de 80 m a 10 cm por píxel. Un recorte es techo si es compacto (área/rectángulo ≥ 0,65), no es vegetación y está a 2 m o más sobre el terreno, o, si el DSM no lo ve alto, cae sobre una huella del mapa o es un techo claro de zinc o fibrocemento bien formado.
3. **Edificios.** Se juntan los anexos de menos de 20 m² pegados a otro techo y las dos aguas de un mismo tejado.
4. **Huellas viejas.** Donde no hay ortofoto (el sur de la zona, hacia el malecón) se conservan: 97. Donde la foto muestra algo alto que SAM no recortó, se conserva la parte que no cubre un techo nuevo: 72. Las que caen sobre suelo, patio o vegetación se quitan: 51 (quedan, para revisión, en `descargas/gad_santa_cruz/derivados/`, fuera de git).
5. **Altura.** Percentil 75 del DSM − DTM de la SGIAR dentro del techo (`altura_medida = true`, 899 edificios). El relieve viene de imágenes de 2020 a 2024: no ve lo construido después y suaviza las casas pequeñas de un piso. Donde no hay medida, `altura_m` es la del promedio de su tamaño.
6. **Familias y personas.** El total publicado (1.308 familias y 4.252 personas, valor central) **no cambia**: se reparte entre los 1.009 edificios según el promedio de su tamaño en la muestra, escalado (× 0,768) porque la ortofoto separa casas y anexos que el mapa juntaba. Los tamaños se reparten por rango de área en la proporción de la muestra (pequeño < 30 m², grande ≥ 98 m²).

En una revisión de 48 edificios al azar sobre la foto, unos 45 eran edificios reales y bien ubicados. Los errores: una huella vieja sobre un patio, un tanque redondo y techos grandes dibujados solo en parte. **Por validar en campo.**

En el mapa de `/riesgos/`, la capa de edificios lleva `extrusion` en `visor_mapas.json`: en la vista 3D se enciende sola y cada edificio se levanta hasta `altura_m` con el color de su gravedad.

## Límites

- La zona no dice profundidad: la foto no deja ver la orilla real del agua entre las casas. «Gravedad» es lo que aparenta la foto.
- Los pisos, familias y personas de cada edificio son promedios de su tamaño: sirven para sumar, no para un edificio concreto.
- Un edificio no es una vivienda: hay locales, galpones y casas con varios hogares.
- El trazo a mano es aproximado. Todo está **por validar** en campo.
- Sin nombres ni datos personales.

## Qué se versiona y qué no

Aquí están los resultados. Los edificios los rehace `scripts/45_edificios_ortofotos.py` (versionado; SAM necesita torch y ultralytics, ver el script). La foto original y los scripts de detección del agua (necesitan la foto, SAM y scikit-learn, que no están en `requirements.txt`) quedan en local, fuera del repositorio. Las teselas se generan con `scripts/est_21nov_foto_teselas.py` y no van a git.
