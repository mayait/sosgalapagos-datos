[[SALTO]]

# 4. Análisis topográfico e hidrológico

## 4.1 Métodos

**Modelo de elevación.** Se usó el modelo Copernicus GLO-30, reproyectado a UTM 15S en celdas de 30 m con interpolación bilineal. Es un modelo digital de **superficie** (DSM), así que incluye copas de árboles y techos.

**Cuenca.** La dirección de flujo se calculó con el método D8 (pysheds) sobre el DSM, con las quebradas IGM 1:25 000 «quemadas» y tras rellenar depresiones y resolver zonas planas. Cada celda se asignó a la entrada por la que su flujo alcanza primero el barrio. El barrio es la unión de los polígonos «La Cascada» de OSM y del CGREG.

**Depresión.** Se trabajó sobre el DSM sin quemar, con un llenado estático («bathtub»): para cada cota *h*, se toman las celdas con cota ≤ *h* conectadas al punto más bajo del barrio, dentro de un radio de 600 m. El llenado no tiene en cuenta el caudal, el tiempo ni las pérdidas.

**Salida y corredores.** La salida por rebose se buscó como el camino de mínimo umbral (*minimax*) hasta el mar. Los corredores de desvío se trazaron con una búsqueda de tipo Dijkstra que maximiza la cota de la rasante con cuatro condiciones:
- pendiente ≥ 0,5 %;
- corte ≤ 3 m (o 6 m);
- terraplén ≤ 1 m;
- sin pasar por zonas pobladas, manzanas ni barrios, con un margen de 30 m.

**Hidrología.**
- Lluvia efectiva: SCS-CN con Ia = 0,2 S.
- Transformación en caudal: hidrograma unitario adimensional SCS, con Tlag = 0,6 tc y Δt = 10 min.
- Cuenca agregada, sin flujo base.
- Escenarios de diseño: tormenta SCS tipo II de 24 h. Evento: hietograma horario de lluvia modelada por ECMWF (sección 3).

**Contraste vertical.** El DSM se comparó con 468 puntos acotados del IGM 1:25 000 situados a menos de 5 km del barrio.

Todo el cálculo se reproduce con `geodatos/scripts/12_cascada_analisis.py`, que reúne las cifras en `datos/resumen.json`.

## 4.2 Cuenca aportante

Tabla: Subcuencas que drenan a La Cascada.

| Subcuenca | Área (km²) | Cota máx. (m) | Pendiente media | Entrada al barrio |
|---|---|---|---|---|
| Rama 1 (norte) | 29,5 | 856 | 10,1 % | −90,31291; −0,73265 (14,7 m) |
| Rama 2 (noroeste) | 12,2 | 826 | 9,2 % | −90,31533; −0,73211 (15,0 m) |
| Escorrentía local | 0,6 | 65 | 5,9 % | — |
| **Total** | **42,3** | | 9,7 % (mediana 8,6 %) | |

El área aportante es prácticamente **toda la cuenca de Puerto Ayora** (47 km²). Incluye la zona agrícola alta y Bellavista. La conexión no es un efecto del relleno de depresiones: solo el 0,7 % del área depende de depresiones de más de 1 m. Se apoya en 33 km de quebradas del IGM, **cuya traza termina en el borde norte del barrio**. El cauce principal (rama 1) mide 13,0 km y baja de 773 a 14,7 m, con una pendiente media del 5,8 %.

![Cuenca que drena a La Cascada, con sus dos ramas, las quebradas cartografiadas, el límite del Parque Nacional y los trazados de desvío evaluados.](figuras/f_mapa_cuenca.png)

![Perfil longitudinal de los cauces principales (D8) y área drenada acumulada hasta la entrada al barrio.](figuras/f_perfil_cauce.png)

## 4.3 Tiempos de concentración y de viaje

Tabla: Tiempos de concentración y de viaje según distintos métodos.

| Tramo | L (km) | Kirpich | Manning (n = 0,045) | Témez | TR-55 | SCS lag (CN 80–60) |
|---|---|---|---|---|---|---|
| Cuenca completa (cabecera → barrio) | 13,0 | 1,4 h | 1,5 h | 3,6 h | 4,2 h | 3,4–5,9 h |
| Bellavista (cauce a 170 m, 8,1 km²) → barrio | 6,1 | 65 min | 53 min | 142 min | 152 min | — |
| Rama 1, cota 40 m → barrio | 0,49 | 7 min | 3 min | 18 min | 8 min | — |
| Rama 2, cota 40 m → barrio | 0,40 | 5 min | 2 min | 15 min | 5 min | — |

Kirpich se calibró en cuencas de menos de 0,5 km², y el SCS lag en cuencas de menos de unos 8 km²; ambos quedan fuera de rango para 42 km². Por eso se adopta **Témez (3,6 h) como valor central** y Kirpich (1,4 h) como cota superior del caudal pico. El intervalo defendible es de **1,4 a 6 h**.

En términos operativos:
- una crecida observada en Bellavista llega al barrio en **1 a 2,5 h**;
- desde el borde del escarpe (cota 40 m) llega en **2 a 18 min**.

Son tiempos de concentración, no tiempos de viaje medidos de una onda de crecida. Sirven solo como orden de magnitud para la alerta.

## 4.4 La Cascada es un vaso de acumulación al pie de escarpes

Las secciones transversales muestran un fondo cerrado por tres lados (figura siguiente):
- **al norte**, el terreno cae de unos 36 a 13 m en unos 240 m;
- **al este** hay un escalón de 29 a 12,5 m en unos 120 m;
- **al oeste** el terreno sube a 26–28 m.

La mediana de cota es de 13,1 m dentro del barrio y de 22,7 m en un anillo de 300 m alrededor.

**El vaso.** El punto más bajo está a 10,5 m (−90,31452; −0,73401). La cota de rebose es la mínima a la que el agua conectada con ese punto alcanza el mar. Se toma como referencia **12,95 m** (DSM, conectividad de 8 vecinos), con el punto de control unos 270 m al ESE (−90,31237; −0,73509). La sensibilidad es de **13,25 m** con conectividad de 4 vecinos y de **12,0 m** con el «proxy de suelo».

El umbral del proxy de suelo coincide con el punto Isla Santiago – Karl Angermeyer del diagnóstico urbano. Los dos puntos están sobre la misma ruta de salida: el segundo es un umbral aguas abajo, que solo controla si el primero está elevado por techos en el DSM. **La cota real del rebose está entre unos 12,0 y 13,25 m, y solo se puede fijar con GNSS.**

Hasta el rebose, el vaso almacena **42 000–62 000 m³ en 3,7–6,2 ha**, con una profundidad máxima de 2,4 m. El rango depende de si un paso diagonal a ≈12,85 m une una segunda poza.

**Conciliación con el criterio de gestión de riesgos.** El especialista en gestión de riesgos obtuvo 14 ha y 125 000 m³ con otro criterio: todas las depresiones de más de 0,2 m situadas a menos de 400 m. El cálculo se reproduce exactamente, pero ese conjunto agrupa 19 vasos independientes con cotas de rebose de 11,4 a 34,9 m. La diferencia viene del dominio y de la conectividad, no del umbral. Como almacenamiento físico del barrio se adopta el rango de 50 000–62 000 m³.

![Perfiles norte–sur y este–oeste de ±600 m por el barrio. La línea discontinua marca la cota de rebose del vaso (≈13,0 m).](figuras/f_secciones.png)

![Vista 3D del entorno de La Cascada (exageración vertical ≈12×): el barrio ocupa el fondo, al pie del escarpe norte. Morado: interceptor hipotético analizado en la sección 5.](figuras/f3d_barrio.png)

Tabla: Curva cota–volumen–exposición. Edificios de OSM y Open Buildings; población de las manzanas del INEC ponderada por área.

| Cota (m) | Área (ha) | Volumen (m³) | Edificios | Población estimada | ¿Sobre el rebose? |
|---|---|---|---|---|---|
| 12,0 | 1,7 | 11 700 | 66 | 283 | no |
| 12,5 | 2,3 | 21 700 | 86 | 400 | no |
| 13,0 | 13,2 | 138 800 | 406 | 1 458 | sí |
| 13,5 | 21,2 | 261 600 | 630 | 2 149 | sí |
| 14,0 | 25,7 | 379 900 | 782 | 2 759 | sí |
| 15,0 | 39,9 | 733 900 | 1 162 | 4 251 | sí |
| 16,0 | 46,4 | 1 168 000 | 1 317 | 4 965 | sí |

Por encima de 12,95 m la lámina ya no es un volumen almacenado: representa lo que quedaría bajo esa cota si la salida estuviera en remanso u obstruida. Además, el resultado depende del radio de la ventana.

**Referencia observada.** El único dato con fuente es el testimonio de agua «hasta dos metros» (sección 3.4), y no se sabe en qué punto del barrio se observó. Sobre un fondo de 10,5–11 m equivale a una cota de **≈12,5–13,0 m**, es decir, al vaso lleno hasta aproximadamente su rebose.

**Exposición dentro del vaso** (de 12,5 m al rebose): **68–204 edificios, unas 400–910 personas y 74–182 viviendas**. El mínimo corresponde a 12,5 m contando los edificios por su centroide; el máximo, a la cota justo bajo el rebose contando los edificios que tocan la mancha. **Las filas de 13 m o más de la tabla anterior no deben citarse como exposición**: describen el camino del desborde hasta el borde de la ventana de cálculo, no agua almacenada.

![Curva cota–volumen–exposición de la zona baja. La banda rosa marca el intervalo de la cota observada (≈12–13 m).](figuras/f_cota_volumen.png)

## 4.5 Salida natural por rebose

El camino de mínimo umbral cruza los 12,95 m y luego se divide en dos ramas:
- **sur**: 1,5 km hasta la bahía, con el 94 % del recorrido en zona poblada y 208 edificios a menos de 20 m;
- **este, por el fondo de la fosa tectónica (graben)**: 2,2 km hasta el mar, con el 76 % en zona poblada y 185 edificios.

**Hoy, la salida natural del vaso atraviesa la trama urbana con una pendiente de ~1 %**, sin cauce (sección 6).

Las cifras de esta sección (1,5 km y 208 edificios a menos de 20 m) corresponden a la ruta de mínimo umbral, con un margen de 20 m. Las de la sección 6 (1 194 m y 28 edificaciones atravesadas) corresponden a la línea de flujo D8 y cuentan solo los edificios que esa línea cruza. Son dos maneras de medir la misma salida.

## 4.6 Hidrogramas de diseño

**Rango de CN.** La cuenca se reparte en un 42 % de Parque (basalto fracturado con suelo somero), un 50 % de zona agrícola y un 8 % de zona poblada. Con CN de 55, 76 y 90 para esas clases, el CN compuesto es de **68 en condición normal**, 47 en condición seca y **83 en condición húmeda**.

Tabla: Escenarios de diseño (tormenta tipo II de 24 h; cuenca de 42,4 km², incluido el barrio). La última columna divide por el vaso máximo de 62 000 m³.

| Lluvia 24 h | CN | Escorrentía (mm) | Volumen (hm³) | Q pico, Témez (m³/s) | Q pico, Kirpich (m³/s) | Volumen / vaso |
|---|---|---|---|---|---|---|
| 50 mm | 60 / 70 / 80 | 1,4 / 5,8 / 13,8 | 0,06 / 0,25 / 0,59 | 1,5 / 10 / 30 | 1,7 / 17 / 58 | 1 / 4 / 9 |
| 100 mm | 60 / 70 / 80 | 18,6 / 32,7 / 50,5 | 0,79 / 1,39 / 2,14 | 36 / 74 / 123 | 67 / 143 / 239 | 13 / 22 / 35 |
| 150 mm | 60 / 70 / 80 | 47 / 69 / 94 | 2,0 / 2,9 / 4,0 | 106 / 167 / 232 | 205 / 324 / 448 | 32 / 47 / 64 |
| 200 mm | 60 / 70 / 80 | 82 / 111 / 140 | 3,5 / 4,7 / 5,9 | 195 / 272 / 347 | 378 / 526 / 664 | 56 / 76 / 96 |

> **Hallazgo central de la hidrología.** Según el método SCS-CN, y suponiendo que toda la escorrentía llega al barrio (sin pérdidas en cauces efímeros sobre basalto fracturado, grietas ni tubos de lava), **el vaso se llena con unos 25–50 mm de lluvia**. Con 100 mm, la escorrentía es de 13 a 50 veces su volumen. Lo que determina la altura del agua en el barrio es la **capacidad de salida**, no el almacenamiento.

## 4.7 El evento del 30–31 de octubre de 2026

**Lluvia de entrada.** Se ponderó la lluvia de ECMWF de 9 km sobre la cuenca asignando la serie de la parte alta a la fracción situada por encima de 200 m (55 %). El resultado es **110 mm en 24 h** (117 mm con polígonos de Thiessen).

**Condición de humedad previa.** El criterio del SCS usa la lluvia de los 5 días anteriores. Entre el 26 y el 30 de octubre, ECMWF de 9 km da 25,7 mm en la costa, 56,8 mm en la parte alta y 42,8 mm ponderados. Con los umbrales de la estación de crecimiento eso es **AMC II**, y con los de la estación latente, AMC III. Los demás modelos dan 2–18 mm, es decir, AMC I–II.

Se adopta **CN 76 como valor central** (intermedio entre AMC II y III), con 83 y 68 como sensibilidad. El CN 55 del Parque es un supuesto: TR-55, matorral desértico, grupo hidrológico A por la permeabilidad del basalto fracturado. Si se clasificara el suelo somero como grupo D, el CN sería mucho mayor.

Como contraste se calculó también el escenario de ECMWF de 0,25° (26 mm).

Tabla: Escenarios del evento (lluvia de modelo; hora de Galápagos, UTC−6).

| Escenario | Lluvia | CN | Volumen | Q pico (Témez – Kirpich) | Hora del pico | Vaso lleno a las |
|---|---|---|---|---|---|---|
| **ECMWF 9 km, central** | 110 mm | **76** | **2,13 hm³** (34–50× el vaso) | **119 – 186 m³/s** | 31-oct ≈07:30 | 05:10 |
| ECMWF 9 km, suelo húmedo | 110 mm | 83 | 2,80 hm³ | 154 – 230 m³/s | 06:30–07:30 | 04:20 |
| ECMWF 9 km, Thiessen | 117 mm | 83 | 3,04 hm³ | 166 – 245 m³/s | 06:30–07:30 | 04:10 |
| ECMWF 0,25° | 26 mm | 83 | 0,15 hm³ (2,4× el vaso) | ≈ 3 m³/s | 15:20–16:10 | 13:20 |

![Hidrogramas sintéticos: (a) escenarios de diseño; (b) evento del 30–31 de octubre con la lluvia de dos versiones del modelo ECMWF (CN 76 central; CN 83 como sensibilidad de suelo húmedo).](figuras/f_hidrogramas.png)

**Comparación con la lámina observada.** La salida sobre el umbral se modeló como un vertedero de cresta ancha (C = 1,7) con el caudal pico. Con los caudales del escenario de suelo húmedo (154–230 m³/s) y según la longitud efectiva del desborde (30, 100 o 300 m, desconocida), la cota del agua sería de **13,4 a 15,7 m**; con CN 76 sería algo menor. La observada es de ≈12,5–13,0 m. Por tanto, con ECMWF de 9 km el modelo **la sobrestima en unos 0,4–1,7 m si el frente de desborde mide 100–300 m, y en unos 2–3 m si mide 30 m**. Con ECMWF de 0,25° el agua queda en unos 13,0 m.

El vertedero libre es una simplificación: ignora el remanso aguas abajo, donde los primeros 400 m son casi planos y están edificados.

**El orden de magnitud cierra, pero la comparación no discrimina entre escenarios.** Hay tres razones:
1. el vaso se llena con cualquier lluvia de más de unos 25 mm en suelo húmedo;
2. la diferencia es del orden del error vertical del DSM;
3. no se conoce el punto exacto del testimonio.

La sobrestimación es compatible con cualquiera de estas explicaciones, sin que se pueda elegir entre ellas:
- que la lluvia real fuera menor que la de ECMWF de 9 km;
- que la cuenca infiltrara más de lo que supone el CN;
- que la salida tuviera más capacidad de la supuesta.

## 4.8 Incertidumbre

- **DSM frente a los puntos acotados del IGM.** La diferencia tiene una media de −2,1 m, una desviación típica de unos 2,0 m y un RMSE de 2,9 m; en zona poblada, −3,4 m. El sesgo negativo apunta a una diferencia de referencia vertical (EGM2008 frente al nivel medio del mar del IGM) que afecta menos a los desniveles locales que a las cotas absolutas. Sin embargo, la diferencia entre zona poblada (−3,4 m) y no poblada (≈−1,9 m) indica que **ninguna cota absoluta del DSM debe usarse como umbral normativo**.
- **Errores locales del DSM.** Sobrestima el terreno bajo copas y techos, lo que puede crear umbrales falsos de varios metros. También suaviza los cauces y las grietas de menos de 30 m.
- **Un error del orden de las magnitudes clave.** El error aleatorio de ±2 m es del mismo orden que la profundidad del vaso (2,4 m), que la diferencia entre lámina modelada y observada, y que el desnivel del interceptor en sus primeros 2,5 km.
- **Hidrología.** Para 100 mm, el caudal pico varía unas 7 veces (36–239 m³/s) según el CN y el tc. La lluvia del evento, de menos de 1 a ≈130 mm según el modelo, es la mayor fuente de incertidumbre, junto con la condición de humedad previa (CN 68–83).

Tabla: Nivel de confianza de cada conclusión.

| Conclusión | Confianza |
|---|---|
| Área de la cuenca (42,3 km²; idéntica con y sin quemar las quebradas) y sus dos ramas | Alta |
| Existencia del vaso y rebose a ≈12–13,25 m; salida sin cauce por la ciudad | Media-alta |
| Corredor de desvío al este | Media-baja |
| Caudales pico | Baja (solo orden de magnitud) |
| Lluvia del evento | Muy baja |
