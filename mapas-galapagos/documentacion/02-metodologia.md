# Metodología

Cómo se construyó cada capa derivada, con qué supuestos y con qué límites. Los scripts están en `geodatos/scripts/` y se ejecutan en orden.

## 1. Datos de partida

| Dato | Detalle |
|---|---|
| Relieve | **Copernicus GLO-30**: modelo digital de **superficie**, 30 m (1 segundo de arco), de AWS Open Data. Incluye la altura de edificios y de árboles. |
| Relieve de Santa Cruz | **DTM de 1 m de la SGIAR** (Subsecretaría de Gestión de la Información y Análisis de Riesgo; producto Vricon/Maxar, imágenes 2020–2024) en Puerto Ayora, el escarpe y Bellavista (183 km²). Es un modelo del **terreno**: sin edificios ni árboles. `03_dem.py` lo fusiona con el Copernicus (transición de 300 m; `relieve_sgiar.py`) y, dentro de su cobertura, calcula HAND, drenaje, costa baja y curvas en una malla de **5 m**. Ficha en `geodatos/datos/dtm_sgiar/LEEME.md`. |
| Hidrografía oficial | **IGM 1:25 000**, del WFS `geoportaligm.gob.ec/galapagos25`: 70 capas. El servicio devuelve cada elemento repetido tres veces por las hojas superpuestas, así que **se eliminan duplicados por geometría** (`05_igm_limpiar.py`). Quedan 909 quebradas en las tres islas. |
| OpenStreetMap | Extracto de Geofabrik para Ecuador, del 31-oct-2026, procesado con pyosmium: vías, edificios, servicios y uso del suelo. |
| Fuentes oficiales | SNGR, INEC, MSP, MINEDUC y CGREG (GeoNode de la FCD). Detalle en `03-fuentes-y-licencias.md`. |

## 2. Área de interés (`area_interes.geojson`)

Es la unión de:
- la **zona agrícola y la urbana** completas, según la zonificación del Parque Nacional de 2017 (zonas RURAL y URBANO) y el suelo urbano y rural del CGREG;
- las **cuencas completas** que drenan hacia cada poblado (ver §5);
- 500 m alrededor de las zonas pobladas (límite urbano del IGM, uso residencial de OSM, huella edificada y manzanas del INEC);
- 300 m alrededor de las vías transitables (OSM, incluidos los caminos de tierra; no se cuentan los senderos peatonales).

Todo se recorta a la línea de costa con 60 m de margen. Las capas de detalle se recortan a esta área. El resto del Parque Nacional se muestra rayado.

## 3. Parque Nacional y zona agrícola

Salen de la **zonificación del PNG de 2017** (CGREG/FCD):
- **Parque:** zonas Intangible, Conservación, Transición, Aprovechamiento sustentable y Área especial.
- **Zona colonizada:** zonas RURAL y URBANO.
- **Límite del parque:** el borde de la zona colonizada que toca el parque; se excluye la línea de costa.

## 4. Quebradas y cauces

- **Quebradas mapeadas:** IGM 1:25 000 (intermitentes y perennes) más los canales y drenajes de OSM.
- **Cauces adicionales:** red de drenaje D8 calculada sobre el DEM, con las quebradas del IGM **quemadas**. Esto significa que el DEM se baja 3 m a lo largo de esas quebradas, para que el flujo siga los cauces reales.
  - Se dibuja un cauce cuando drena al menos 0,2 km².
  - Solo se conservan los tramos que **no coinciden** (a 45 m) con una quebrada ya mapeada. Son candidatos a revisar en terreno.
- **Franja de 20 m:** la capa oficial del CGREG («encañadas» con buffer de 20 m).
- **Cañadas del GAD de Santa Cruz** (desde el 28-nov-2026): 25 cañadas trazadas por el GAD Municipal entre Bellavista y La Cascada. Van como capa propia y se suman al drenaje del Instituto de Geografía USFQ, sin reemplazarlo, porque solo cubren ese corredor. No se marcan en el relieve (ver §11).

## 5. Cuencas que drenan a los poblados

Script `07b_cuencas_aportantes.py`. Para cada celda del DEM se sigue la dirección de flujo D8 aguas abajo. Se usa **salto de punteros** (pointer jumping), que tiene coste O(N log N).

- **Cuenca completa de cada localidad:** todas las celdas cuyo flujo **termina pasando** por la localidad, aunque antes atraviese otro poblado. Por eso la de Puerto Ayora (44 km²) incluye la de Bellavista. La localidad se define como la unión de sus manzanas del INEC y su límite urbano del IGM.
- **Subcuencas por punto de entrada:** cada celda se asigna al primer punto donde su flujo entra en una zona poblada. Las que suman al menos 0,2 km² se dibujan como subcuenca, con el nombre de la quebrada si el IGM lo tiene. El resto se agrupa como «escorrentía local».

| Localidad | Área aguas arriba (km²) |
|---|---:|
| Puerto Ayora | 44,2 |
| Bellavista | 15,6 |
| Puerto Baquerizo Moreno | 11,5 |
| Tomás de Berlanga | 10,8 |
| Puerto Villamil | 1,4 |
| Santa Rosa | 0,3 |
| El Progreso | 0,1 |

Santa Rosa y El Progreso dan valores muy pequeños porque están sobre lomas. Conviene confirmarlo en terreno.

## 6. Susceptibilidad a inundación por quebradas (HAND)

Se usa el índice **HAND** (Height Above Nearest Drainage), que mide la altura de cada celda sobre el cauce más cercano en la dirección del flujo:

- **Cauces de referencia:** quebradas del IGM más el drenaje que acumula al menos 0,5 km².
- **Clases:**
  - **alta:** hasta 1 m sobre el cauce;
  - **media:** hasta 2,5 m;
  - **baja:** hasta 5 m.
- **Restricción:** solo a 300 m o menos del cauce.
- **Suavizado:** filtro de mediana de 3×3, más cierre y apertura morfológica de 12 m para redondear la escalera de píxeles. Las clases se publican **acumuladas**: el polígono de «baja» contiene al de «media» y este al de «alta».

**Límites:**
- Fuera de la cobertura del DTM de la SGIAR, el DEM es de superficie: en zonas urbanas y bosque denso la altura está sesgada por edificios y árboles.
- Con 30 m (y aun con los 5 m del DTM) no se captan obras de drenaje: alcantarillas, canales, sumideros. El DTM tampoco tiene muros ni edificios: el agua «pasa» bajo las casas.
- En terreno muy plano, como **Puerto Villamil**, HAND marca casi todo como susceptible.
- No modela el caudal ni el período de retorno. Es un índice de posición topográfica, no una simulación hidráulica.

**Contraste con datos oficiales:**
- La susceptibilidad alta coincide con el polígono de «Riesgo de inundación – Puerto Ayora» del CGREG.
- El polígono de «flujos de lodo por El Niño» del CGREG está sobre la quebrada encima de **La Cascada**, el barrio más afectado en el evento del 30–31 de octubre.

## 7. Costa baja

Celdas del DEM con cota de 0–3 m, de 3–5 m y de 5–10 m, suavizadas. Sirven para la inundación costera por oleaje o marea alta. Para tsunami se usa la capa oficial del INOCAR.

## 8. Población y exposición

- **Población estimada por manzana:** se suman las viviendas georreferenciadas de la SNGR (9 475, cada una con su población estimada) dentro de cada manzana del INEC MGN 2026. Los totales por isla coinciden en orden de magnitud con el censo de 2022.
- **Edificios:** OSM más Google Open Buildings v3 (confianza ≥ 0,70, sin solaparse con OSM). Open Buildings no cubre San Cristóbal.
- **Exposición:** cada edificio y cada vivienda se cruza con la susceptibilidad, la franja de quebrada, la zona de tsunami y la costa de 0–3 m. El resultado está en `resumen_exposicion.json`.
- **Puntos clave:** los de cada categoría se fusionan y se eliminan duplicados a menos de 40 m, dando prioridad a la fuente oficial. Cada punto lleva `en_susc_alta_media` y `en_zona_tsunami`.

## 9. Topografía

- **Curvas:** cada 10 m, con maestras cada 50 m, a partir del DEM suavizado (gaussiano σ = 1,2 celdas) y recortadas al área de interés.
- **Pendientes:** rangos de 15–25°, 25–35° y más de 35°.
- **Relieve sombreado:** azimut 315°, elevación 45°.

## 10. Zona afectada, gravedad y edificios a partir de la foto aérea del 21-nov-2026 (Puerto Ayora)

**Es una estimación propia por visión artificial, no un dato oficial ni un censo de daños.** Foto: Tui De Roy.

1. **Cámara.** Se ajustó un modelo de cámara a la foto con 20 puntos de control sobre el DTM 1 m: SGIAR (Vricon/Maxar). Error mediano: 6 píxeles (3 a 6 m en el suelo cerca de La Cascada).
2. **Foto rectificada.** Cada punto del suelo toma el color del píxel que lo mira. No es una ortofoto verdadera: los edificios se ven inclinados y lo que tapan no aparece.
3. **Agua.** Consenso de dos de tres modelos sobre la foto (regla de color, k-medias y bosque aleatorio). La zona suma una franja de 12 m alrededor del agua vista y las áreas que el coordinador marcó a mano. No dice profundidad.
4. **Gravedad aparente.** La zona se cierra sobre las manzanas rodeadas de agua y se parte en cuatro clases según la fracción de suelo con agua a la vista y la gravedad de los reportes ciudadanos cercanos.
5. **Edificios, familias y personas.** Huellas del mapa dentro de la zona, corregidas con una muestra inventariada sobre la foto. Pisos y viviendas salen del promedio por tamaño en esa muestra; 3,25 personas por hogar. Se publica el rango entre el censo y el cálculo sobre la foto.

Detalle, archivos y límites: `geodatos/datos/foto_aerea_21nov/LEEME.md`.

## 11. Cañadas del GAD, cruces con vías y calles con cañada (Santa Cruz, desde el 28-nov-2026)

**Cruces de cañadas con vías** (`16_cruces_quebradas_vias.py`):
- **Fuentes de cauce.** A las quebradas del IGM y OSM y al cauce D8 se suman las cañadas del GAD, con prioridad sobre las quebradas sin nombre y el D8 al agrupar cruces cercanos (40 m).
- **Una cañada que corre por la vía no la cruza.** Si en 150 m alrededor del punto hay más de 80 m de cañada a 10 m o menos de la vía, o el ángulo entre las dos es menor de 25°, no se cuenta como cruce. Así se descartan 45 intersecciones.
- **Resultado frente a la versión anterior:** 20 cruces nuevos (1 de prioridad alta, 11 media, 8 baja) y uno que sube de media a alta.
- **Los id ya no se renumeran.** Cada cruce hereda el id del cruce anterior más cercano a 60 m o menos (pareja uno a uno). Los nuevos toman números a partir del mayor anterior. El modelo 2D, las tormentas sintéticas y `estudios/pendientes.json` citan cruces por id.
- **Ojo con el área drenada.** Donde la cañada del GAD no coincide con el cauce del relieve, el área drenada del cruce sale casi nula y subestima el caudal.

**Calles por donde corre una cañada** (`40_gad_santa_cruz_canadas.py` → `vias_con_canada.geojson`):
- Son tramos de vía de OSM con más de 80 m de cañada del GAD a 10 m o menos. Hay 17 tramos y 4,9 km en total; el más largo, 1,7 km de la Av. Padre Julio Herrera.
- Con lluvia fuerte, el agua y el lodo bajan por la calzada.

**Por qué no se marcan en el relieve.** Revisamos sobre las ortofotos los tramos que se alejan más de 60 m de nuestro drenaje, y el trazado es desigual. Algunas cañadas siguen cicatrices de erosión con precisión; otras son tramos rectos sobre bosque, sin cauce visible ni en la foto ni en el DTM. Bajar 3 m el DTM de 5 m a lo largo de una línea corrida inventaría un cauce que no existe, y lo heredarían el HAND y el modelo 2D.

## 12. Ortofotos de dron del GAD (Santa Cruz)

- **Mosaico de los cinco vuelos posteriores al evento**, del 3 al 22-nov-2026. Donde dos se solapan queda encima el más reciente.
- **Teselas webp de 256 px** en EPSG:3857, de los zooms 14 a 19 (≈ 30 cm por píxel, 90 MB en git). Las hace `41_teselas_ortofotos_gad.py`, que lee de cada COG la vista reducida más cercana a la resolución de cada zoom.
- **Pueden estar corridas 2 a 4 m** respecto de otras capas. Los vuelos se hicieron sin puntos de control conocidos.
- **El detalle completo** (2 a 7,5 cm) está en los GeoTIFF originales, que van a Zenodo.

