Intro: El detalle técnico detrás de la página de La Cascada: la cuenca que drena al barrio, los tiempos de llegada del agua, el vaso donde se acumula, la salida por rebose y los caudales del 30 de octubre calculados con la lluvia medida. Al final, la incertidumbre, la confianza de cada conclusión y los métodos.

# Lo que muestra este análisis

- **Casi toda la cuenca de Puerto Ayora drena a La Cascada**: 40,1 km² con dos ramas, desde la zona agrícola alta y Bellavista. Las quebradas cartografiadas terminan en el borde norte del barrio.
- **El barrio es un vaso cerrado por tres lados** al pie de escarpes. Hasta el rebose (entre unos 12,0 y 13,25 m) guarda **42 000–62 000 m³**. Dentro del vaso hay **68–204 edificios y unas 400–910 personas**.
- **La salida natural por rebose cruza la ciudad sin cauce**, con una pendiente de ~1 %.
- **El 30 de octubre el vaso se llenó horas antes del pico.** Con la lluvia medida (152–208 mm sobre la cuenca), el caudal pico calculado es de **215–549 m³/s**, solo como orden de magnitud. A partir de ahí, la altura del agua en el barrio la controla la capacidad de salida, no el almacenamiento.
- **La intensidad pesa más que el volumen.** El 3-oct cayeron 68,2 mm sin inundación reportada (por confirmar con el GAD/COE); el 30-oct hubo unas 3 horas seguidas a 21–61 mm/h. El umbral está del orden de 20–25 mm/h sostenidos durante más de una hora.
- **Las cotas vienen de un modelo de superficie de 30 m** con un error del mismo orden que la profundidad del vaso. La cota real del rebose solo se puede fijar con GNSS.

Para la lectura general, ver [La Cascada: por qué se inunda y qué está expuesto](../la-cascada/). Las opciones de obra están en [La Cascada: opciones que aparecen en el análisis](../la-cascada-opciones/).

# Cuenca y tiempos de llegada

## Cuenca aportante

Tabla: Subcuencas que drenan a La Cascada.

| Subcuenca | Área (km²) | Cota máx. (m) | Pendiente media | Entrada al barrio |
|---|---|---|---|---|
| Rama 1 (norte) | 29,5 | 856 | 10,1 % | −90,31291; −0,73265 (14,7 m) |
| Rama 2 (noroeste) | 12,2 | 826 | 9,2 % | −90,31533; −0,73211 (15,0 m) |
| Escorrentía local | 0,6 | 65 | 5,9 % | — |
| **Total** | **42,3** | | 9,7 % (mediana 8,6 %) | |

\* Cota del DSM (±2–4 m), orientativa.

El área aportante es prácticamente **toda la cuenca de Puerto Ayora** (47 km²). Incluye la zona agrícola alta y Bellavista. La conexión no es un efecto del relleno de depresiones: solo el 0,7 % del área depende de depresiones de más de 1 m. Se apoya en 33 km de quebradas del IGM, **cuya traza termina en el borde norte del barrio**. El cauce principal (rama 1) mide 13,0 km y baja de 773 a 14,7 m, con una pendiente media del 5,8 %.

![Cuenca que drena a La Cascada, con sus dos ramas, las quebradas cartografiadas, el límite del Parque Nacional y los trazados de desvío evaluados.](figuras/f_mapa_cuenca.png)

![Perfil longitudinal de los cauces principales (D8) y área drenada acumulada hasta la entrada al barrio.](figuras/f_perfil_cauce.png)

## Tiempos de concentración y de viaje

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

# El vaso de La Cascada y su salida

## Un vaso de acumulación al pie de escarpes

Las secciones transversales muestran un fondo cerrado por tres lados (figura siguiente):
- **al norte**, el terreno cae de unos 36 a 13 m en unos 240 m;
- **al este** hay un escalón de 29 a 12,5 m en unos 120 m;
- **al oeste** el terreno sube a 26–28 m.

La mediana de cota es de 13,1 m dentro del barrio y de 22,7 m en un anillo de 300 m alrededor.

**El vaso.** El punto más bajo está a 10,5 m (−90,31452; −0,73401). La cota de rebose es la mínima a la que el agua conectada con ese punto alcanza el mar. Se toma como referencia **12,95 m** (DSM, conectividad de 8 vecinos), con el punto de control unos 270 m al ESE (−90,31237; −0,73509). La sensibilidad es de **13,25 m** con conectividad de 4 vecinos y de **12,0 m** con el «proxy de suelo».

El umbral del proxy de suelo coincide con el punto Isla Santiago – Karl Angermeyer del diagnóstico urbano. Los dos puntos están sobre la misma ruta de salida: el segundo es un umbral aguas abajo, que solo controla si el primero está elevado por techos en el DSM. **La cota real del rebose está entre unos 12,0 y 13,25 m, y solo se puede fijar con GNSS.**

Hasta el rebose, el vaso almacena **42 000–62 000 m³ en 3,7–6,2 ha**, con una profundidad máxima de 2,4 m. El rango depende de si un paso diagonal a ≈12,85 m une una segunda poza.

**Conciliación con el criterio de gestión de riesgos.** El especialista en gestión de riesgos obtuvo 14 ha y 125 000 m³ con otro criterio: todas las depresiones de más de 0,2 m situadas a menos de 400 m. El cálculo se reproduce exactamente, pero ese conjunto agrupa 19 vasos independientes con cotas de rebose de 11,4 a 34,9 m. La diferencia viene del dominio y de la conectividad, no del umbral. Como almacenamiento físico del barrio se adopta el rango de 42 000–62 000 m³.

![Perfiles norte–sur y este–oeste de ±600 m por el barrio. La línea discontinua marca la cota de rebose del vaso (≈13,0 m).](figuras/f_secciones.png)

![Vista 3D del entorno de La Cascada (exageración vertical ≈12×): el barrio ocupa el fondo, al pie del escarpe norte. Morado: interceptor hipotético analizado en la página de opciones.](figuras/f3d_barrio.png)

## Curva cota–volumen y exposición

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

\* Cota del DSM (±2–4 m), orientativa.

Por encima de 12,95 m la lámina ya no es un volumen almacenado: representa lo que quedaría bajo esa cota si la salida estuviera en remanso u obstruida. Además, el resultado depende del radio de la ventana.

**Referencia observada.** El único dato con fuente es el testimonio de agua «hasta dos metros» (ver [Qué pasó el 30 de octubre](../que-paso/)), y no se sabe en qué punto del barrio se observó. Sobre un fondo de 10,5–11 m equivale a una cota de **≈12,5–13,0 m**, es decir, al vaso lleno hasta aproximadamente su rebose.

**Exposición dentro del vaso** (de 12,5 m al rebose): **68–204 edificios, unas 400–910 personas y 74–182 viviendas**. El mínimo corresponde a 12,5 m contando los edificios por su centroide; el máximo, a la cota justo bajo el rebose contando los edificios que tocan la mancha. **Las filas de 13 m o más de la tabla anterior no son cifras de exposición**: describen el camino del desborde hasta el borde de la ventana de cálculo, no agua almacenada.

![Curva cota–volumen–exposición de la zona baja. La banda rosa marca el intervalo de la cota observada (≈12–13 m).](figuras/f_cota_volumen.png)

## Salida natural por rebose

El camino de mínimo umbral cruza los 12,95 m y luego se divide en dos ramas:
- **sur**: 1,5 km hasta la bahía, con el 94 % del recorrido en zona poblada y 208 edificios a menos de 20 m;
- **este, por el fondo de la fosa tectónica (graben)**: 2,2 km hasta el mar, con el 76 % en zona poblada y 185 edificios.

**Hoy, la salida natural del vaso atraviesa la trama urbana con una pendiente de ~1 %**, sin cauce (ver [La Cascada](../la-cascada/)).

Las cifras de este apartado (1,5 km y 208 edificios a menos de 20 m) corresponden a la ruta de mínimo umbral, con un margen de 20 m. Las de la página [La Cascada](../la-cascada/) (1 194 m y 28 edificaciones atravesadas) corresponden a la línea de flujo D8 y cuentan solo los edificios que esa línea cruza. Son dos maneras de medir la misma salida.

# Crecida: escenarios de diseño y evento del 30 de octubre

## Escenarios de diseño

**Rango de CN.** La cuenca se reparte en un 42 % de Parque (basalto fracturado con suelo somero), un 50 % de zona agrícola y un 8 % de zona poblada. Con CN de 55, 76 y 90 para esas clases, el CN compuesto es de **68 en condición normal**, 47 en condición seca y **83 en condición húmeda**.

Tabla: Escenarios de diseño (tormenta tipo II de 24 h; cuenca de 42,4 km², incluido el barrio). La última columna divide por el vaso máximo de 62 000 m³.

| Lluvia 24 h | CN | Escorrentía (mm) | Volumen (hm³) | Q pico, Témez (m³/s) | Q pico, Kirpich (m³/s) | Volumen / vaso |
|---|---|---|---|---|---|---|
| 50 mm | 60 / 70 / 80 | 1,4 / 5,8 / 13,8 | 0,06 / 0,25 / 0,59 | 1,5 / 10 / 30 | 1,7 / 17 / 58 | 1 / 4 / 9 |
| 100 mm | 60 / 70 / 80 | 18,6 / 32,7 / 50,5 | 0,79 / 1,39 / 2,14 | 36 / 74 / 123 | 67 / 143 / 239 | 13 / 22 / 35 |
| 150 mm | 60 / 70 / 80 | 47 / 69 / 94 | 2,0 / 2,9 / 4,0 | 106 / 167 / 232 | 205 / 324 / 448 | 32 / 47 / 64 |
| 200 mm | 60 / 70 / 80 | 82 / 111 / 140 | 3,5 / 4,7 / 5,9 | 195 / 272 / 347 | 378 / 526 / 664 | 56 / 76 / 96 |

**Lo que dice el SCS-CN y lo que no respalda la evidencia.** Según el método SCS-CN agregado, y suponiendo que toda la escorrentía llega al barrio sin pérdidas en los cauces efímeros sobre basalto fracturado, el vaso se llenaría con unos 25–50 mm de lluvia. **La serie medida de octubre no respalda ese resultado.** El 3-oct cayeron 68,2 mm en Los Guayabillos, y 112 mm entre el 3 y el 4, sin inundación reportada en La Cascada (por confirmar con el GAD/COE). Con ese criterio, el modelo 2D con SCS-CN inunda el barrio, mientras que un modelo de pérdida inicial más pérdida constante no lo hace (ver [Modelo 2D](../modelo-2d/)).

**Umbral empírico.** La diferencia entre ese día y el 30-oct está en la **intensidad**, más que en el volumen:
- el 3-oct, el máximo horario fue de 12,6 mm/h;
- el 30-oct hubo unas 3 horas seguidas a 21–61 mm/h.

El umbral está entre ambos casos: del orden de **20–25 mm/h sostenidos durante más de una hora** sobre la parte media de la cuenca, tras unos 20 mm de pérdida inicial. Una vez superado, lo que determina la altura del agua en el barrio es la **capacidad de salida**, no el almacenamiento.

## Lluvia medida el 30 de octubre

La red IERSE-WSN (Universidad del Azuay) registró la tormenta cada ~5 minutos, en hora de Galápagos (UTC−6). Los totales son **mínimos**: Los Guayabillos y Santa Rosa dejaron de transmitir a las 21:22–21:25, cuando todavía llovía a unos 5 mm cada 5 minutos. En la costa, el pluviómetro M0191 del INAMHI, en Puerto Ayora, midió 135 mm más entre las 22:00 y las 03:00; el modelo agregado no incluye esa lluvia, porque no se sabe si cayó también sobre la cuenca. El análisis completo de la lluvia está en [La lluvia](../lluvia/).

Tabla: Lluvia medida el 30 de octubre de 2026 (red IERSE-WSN; hora UTC−6).

| Estación | Cota (DEM) | Total 30-oct | Máximo en 1 h | Pulsos principales | Último registro |
|---|---|---|---|---|---|
| Los Guayabillos (parte media, a 370 m de la cuenca) | ≈178 m | **178,8 mm** | **61,0 mm** (20:00–21:00) | 15:00–16:00: 7,8 mm; 18:00–21:30: 143 mm | 21:25 |
| Santa Rosa (oeste, fuera de la cuenca) | ≈416 m | **237,6 mm** | **66,4 mm** (20:00–21:00) | 15:00–16:00: 43 mm; 18:00–21:30: 140 mm | 21:22 |
| Cerro Crocker (cumbre, borde norte de la cuenca) | ≈861 m | 5,0 mm (no fiable) | 0,8 mm | ninguno | 23:57 |
| Militar (Baltra) | ≈14 m | 2,0 mm | 0,8 mm | ninguno | 23:57 |

**Calidad de los pluviómetros** (serie IERSE del 23-abr al 2-nov).
- *Cerro Crocker* casi seguro falla desde agosto. En junio midió 297 mm, pero en septiembre y octubre solo 9 y 18 mm, mientras Los Guayabillos medía 140 y 340 mm. Sus 5 mm del 30-oct no se usan.
- *Los Guayabillos* marca 0 mm del 31-oct al 2-nov con cobertura completa, mientras Santa Rosa mide 13–43 mm al día. Probablemente el pluviómetro se obstruyó o se dañó durante el evento. Su registro del 30-oct es coherente con el de Santa Rosa y se mantiene, como total mínimo.

**Lluvia areal sobre la cuenca (42,4 km²).** Se usaron tres métodos, todos con el hietograma de 10 min de las estaciones:

Tabla: Lluvia areal del 30-oct sobre la cuenca de La Cascada.

| Método | Supuesto | Lluvia areal |
|---|---|---|
| Los Guayabillos con reducción areal | Factor 0,85 para una tormenta convectiva de 1–3 h sobre ~40 km² (curvas TP-29: 0,85–0,90) | 152 mm (cota inferior) |
| **Los Guayabillos uniforme (central)** | La estación está a 178 m, cerca de la mediana de cota de la cuenca (225 m) | **179 mm** |
| Gradiente con la cota (Guayabillos–Santa Rosa) | Interpolación lineal entre 178 y 416 m; Crocker descartado | 208 mm (cota superior) |

Si la lluvia hubiera seguido 30 minutos más al ritmo de los últimos registros, el método central sumaría unos 26 mm (204 mm). Es solo una sensibilidad, no un dato. Si Crocker fuera correcto, un Thiessen con esa estación daría 127 mm; se conserva en `resumen.json` solo como referencia.

**Condición de humedad previa.**
- Los 5 días previos (25–29 de octubre) sumaron solo 12 mm en Los Guayabillos y 10 mm en Santa Rosa: AMC I–II según el criterio SCS.
- Sin embargo, octubre fue húmedo (340 mm en Los Guayabillos) y el 30-oct ya habían caído unos 25 mm antes del pulso principal. Esa lluvia la recoge el propio método SCS-CN en la abstracción inicial.
- Se mantiene **CN 76 como valor central**. CN 68 es igual de defendible, y CN 83 (AMC III) queda sin respaldo.
- El CN 55 del Parque sigue siendo un supuesto (TR-55, matorral desértico, grupo hidrológico A).

## Hidrogramas del evento

Tabla: Hidrogramas del evento medido en la entrada al barrio (CN 76; Témez – Kirpich; hora UTC−6).

| Lluvia areal | Escorrentía | Volumen | Q pico | Hora del pico | Q > 1 m³/s desde | Vaso lleno a las |
|---|---|---|---|---|---|---|
| Reducción areal, 152 mm | 85 mm (C = 0,56) | 3,59 hm³ | 260 – 401 m³/s | 21:40 – 22:50 | 15:50 – 16:20 | 17:45 – 19:10 |
| **Los Guayabillos, 179 mm** | **108 mm (C = 0,61)** | **4,59 hm³ (74× el vaso)** | **325 – 497 m³/s** | **21:40 – 22:50** | 14:20 – 15:50 | **16:50 – 18:10** |
| Gradiente con la cota, 208 mm | 134 mm (C = 0,65) | 5,69 hm³ | 362 – 549 m³/s | 21:30 – 22:40 | 10:30 – 14:50 | 15:40 – 16:30 |

Con CN 68, el pico del escenario central queda en 277–434 m³/s. El conjunto de los escenarios (152–208 mm, CN 68–76) da **215–549 m³/s**.

Son caudales específicos de 5–13 m³/s por km², propios de crecidas convectivas en cuencas pequeñas. Un modelo agregado, con lluvia uniforme y sin pérdidas en el cauce, puede sobrestimarlos; sin la estación de la cumbre no se sabe si la tormenta cubrió la parte alta. Los hidrogramas están en `datos/hidrogramas_evento_30oct.csv`.

![Hidrogramas sintéticos: (a) escenarios de diseño; (b) evento del 30 de octubre con la lluvia medida por la red IERSE-WSN (tres métodos de lluvia areal; CN 76), con la lluvia horaria de Los Guayabillos.](figuras/f_hidrogramas.png)

## Tránsito por el vaso y lámina de agua

El hidrograma se transitó por el vaso con:
- la curva cota-volumen (apartado «Curva cota–volumen y exposición»);
- una salida en vertedero de cresta ancha (C = 1,7) sobre el umbral de 12,95 m;
- tres longitudes efectivas del frente de desborde: 100, 300 y 1 000 m.

Tabla: Lámina máxima simulada sobre el punto más bajo del DSM (≈10,5 m), con lluvia areal de 152–208 mm, CN 68–76 y tc de Témez a Kirpich.

| Frente de desborde | Cota máxima del agua | Lámina sobre el fondo | Hora de la lámina máxima |
|---|---|---|---|
| 100 m | 14,1 – 15,1 m | 3,6 – 4,5 m | 21:50 – 23:10 |
| 300 m | 13,5 – 14,0 m | 3,0 – 3,5 m | 21:40 – 23:00 |
| 1 000 m | 13,2 – 13,4 m | 2,7 – 2,9 m | 21:40 – 22:55 |

\* Cota del DSM (±2–4 m), orientativa.

## Comparación con lo observado

- *Hora.* La lluvia medida, el inicio de la escorrentía (10:30–18:00), el llenado del vaso (15:40–20:00) y el pico (21:30–22:50) coinciden con la SNGR, que sitúa las lluvias fuertes y las inundaciones en la «tarde y noche del 30/10». ECMWF situaba el máximo unas 8–9 horas más tarde y con menos lluvia areal (110 mm): **queda descartado como representación del evento**.
- *Lámina.* El testimonio de agua «hasta dos metros» es compatible con el modelo si el frente de desborde fue de varios cientos de metros, es decir, si el agua se extendió sobre la zona baja urbana. También es compatible si el testigo estaba 0,5–1 m por encima del punto más bajo del DSM. Con un frente de 300–1 000 m, una vivienda situada 0,5–1 m sobre ese punto habría tenido entre 1,7 y 3,0 m de agua. La cifra de «unos 3 m», sin fuente, también cabe en el intervalo. La revisión de la fase anterior («ECMWF sobrestima la lámina») deja de ser aplicable.
- *Vaciado.* La lámina vuelve a la cota de rebose entre las 00:00 y las 08:00 del 31-oct. Por debajo de ese nivel quedan retenidos **42 000–62 000 m³** sin salida por gravedad, que solo se pierden por infiltración o bombeo. Esto concuerda con el anuncio de la SNGR de que «se drenará el sector La Cascada».

## Qué implica

- **CN e infiltración.** La lámina es casi insensible a la lluvia y al CN: todos los escenarios caen en 13,5–14,0 m con un frente de 300 m. La razón es que la controla la cota del umbral más una carga que crece con Q^(2/3). Por eso **el testimonio no sirve para calibrar el CN ni la infiltración**. Eso solo se resolvería con huellas de crecida en las quebradas (método de sección y pendiente) o con el volumen desbordado.
- **Capacidad de salida.** Es la variable que gobierna la lámina. El caudal pico del evento, unos 300–500 m³/s en el escenario central, supera:
  - unas 7–14 veces los 35–45 m³/s de la calle-canal que aparece entre las opciones (ver [La Cascada: opciones](../la-cascada-opciones/));
  - el caudal considerado para el interceptor en esa misma página (150–230 m³/s). Conducir 325–497 m³/s exigiría 35–54 m de base al 0,5 %.
- **Lo que no cambia.** El 30-oct, el vaso se llenó horas antes del pico. La lluvia medida refuerza la conclusión de que, superado el umbral de intensidad, el problema es de salida y de exposición, no de almacenamiento.

# Incertidumbre y confianza

- **DSM frente a los puntos acotados del IGM.** La diferencia tiene una media de −2,1 m, una desviación típica de unos 2,0 m y un RMSE de 2,9 m; en zona poblada, −3,4 m. El sesgo negativo apunta a una diferencia de referencia vertical (EGM2008 frente al nivel medio del mar del IGM) que afecta menos a los desniveles locales que a las cotas absolutas. Sin embargo, la diferencia entre zona poblada (−3,4 m) y no poblada (≈−1,9 m) indica que **ninguna cota absoluta del DSM sirve como umbral normativo**.
- **Errores locales del DSM.** Sobrestima el terreno bajo copas y techos, lo que puede crear umbrales falsos de varios metros. También suaviza los cauces y las grietas de menos de 30 m.
- **Un error del orden de las magnitudes clave.** El error aleatorio de ±2 m es del mismo orden que la profundidad del vaso (2,4 m), que la lámina simulada y que el desnivel del interceptor en sus primeros 2,5 km.
- **Lluvia del evento.** Está medida, pero solo en dos estaciones útiles, ambas fuera de la cuenca y con totales mínimos por el corte de transmisión. La estación de la cumbre falla desde agosto y la de Los Guayabillos dejó de medir después del evento. La lluvia areal va de 152 a 208 mm (reducción areal a gradiente con la cota). Los pluviómetros de balancín subestiman las intensidades de más de 50 mm/h.
- **Hidrología.** Para el evento medido, el caudal pico varía de 215 a 549 m³/s (factor ~2,5) según la lluvia areal, el CN (68–76) y el tc (Témez–Kirpich). El modelo es agregado, con lluvia uniforme, sin pérdidas en el cauce y sin calibrar con caudales.
- **Tránsito por el vaso.** El vertedero libre ignora el remanso aguas abajo, donde los primeros 400 m son casi planos y están edificados. La longitud efectiva del frente de desborde (100–1 000 m) es un supuesto. El [Modelo 2D](../modelo-2d/) sí representa ese remanso.
- **Pérdidas por intensidad.** El SCS-CN reparte las pérdidas según el volumen acumulado, no según la intensidad. Los días sin inundación reportada de octubre (3 y 4 de octubre: 68 y 44 mm con ≤ 13 mm/h; por confirmar) indican que sobre el basalto fracturado dominan las pérdidas por intensidad (infiltración y transmisión en los cauces). Por eso **el SCS-CN sobrestima la frecuencia de llenado del vaso**: el «25–50 mm» del apartado «Escenarios de diseño» no sirve como umbral de alerta.

Tabla: Nivel de confianza de cada conclusión.

| Conclusión | Confianza |
|---|---|
| Área de la cuenca (42,3 km²; idéntica con y sin quemar las quebradas) y sus dos ramas | Alta |
| Hora del evento (tarde y noche del 30-oct; pico entre las 21:30 y las 23:00) | Alta (lluvia medida y SNGR) |
| Existencia del vaso y rebose a ≈12–13,25 m; salida sin cauce por la ciudad | Media-alta |
| El vaso se llenó horas antes del pico; la lámina la controla la salida | Media-alta |
| Lluvia areal del evento (152–208 mm, totales mínimos) | Media-baja |
| Corredor de desvío al este | Media-baja |
| Caudales pico | Baja (solo orden de magnitud) |

# Métodos

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
- Escenarios de diseño: tormenta SCS tipo II de 24 h. Evento: hietograma horario de lluvia modelada por ECMWF (ver [La lluvia](../lluvia/)). La recalibración del apartado «Lluvia medida el 30 de octubre» usa el hietograma de 10 min de las estaciones IERSE-WSN.

**Contraste vertical.** El DSM se comparó con 468 puntos acotados del IGM 1:25 000 situados a menos de 5 km del barrio.

## Archivos

Todo el cálculo se reproduce con `geodatos/scripts/12_cascada_analisis.py`, que reúne las cifras en `datos/resumen.json`. Los hidrogramas del evento están en `datos/hidrogramas_evento_30oct.csv`. Más detalle en [Métodos, datos y descargas](../metodos/).
