# Metodología

Cómo se construyó cada capa derivada, con qué supuestos y con qué límites. Los scripts están en `geodatos/scripts/` y se ejecutan en orden.

## 1. Datos de partida

| Dato | Detalle |
|---|---|
| Relieve | **Copernicus GLO-30**: modelo digital de **superficie**, 30 m (1 segundo de arco), de AWS Open Data. Incluye la altura de edificios y de árboles. |
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
- El DEM es de superficie: en zonas urbanas y bosque denso la altura está sesgada por edificios y árboles.
- La resolución de 30 m no capta cauces estrechos ni obras de drenaje (alcantarillas, canales).
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
