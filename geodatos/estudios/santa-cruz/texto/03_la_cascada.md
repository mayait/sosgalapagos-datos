Intro: Por qué se inunda el barrio La Cascada, en Puerto Ayora: la cuenca que le llega, el vaso cerrado donde se acumula el agua y la salida al mar, que no tiene cauce. Incluye cuántos edificios y personas están expuestos y lo que todavía no se puede saber con los datos disponibles. El detalle de cálculo está en [La Cascada: cuenca, vaso y crecida](../hidrologia/).

# Lo que muestran los datos

La Cascada se inunda por la suma de tres hechos. Ninguno basta por sí solo.

1. **Recibe el agua de 42 km².** Al barrio drena prácticamente toda la cuenca de Puerto Ayora (47 km²), incluidas la zona agrícola alta y Bellavista. Son dos ramas de quebradas (29,5 y 12,2 km²) más 0,6 km² de escorrentía local. Las quebradas del IGM **terminan en el borde norte del barrio**.
2. **Ocupa un vaso cerrado al pie de un escarpe.** El fondo está cerrado al norte, al este y al oeste. Hasta el punto de rebose, el vaso almacena solo **42 000–62 000 m³ en 3,7–6,2 ha**, con una profundidad máxima de 2,4 m. El rebose está en **≈12–13,25 m** de cota; la cifra exacta solo se puede fijar con GNSS. Una lluvia de 100 mm en 24 h genera entre 13 y 35 veces el volumen del vaso.
3. **El agua no tiene por dónde salir.** Entre el barrio y el mar no hay ningún cauce cartografiado. La salida natural recorre 1,2 km de calles casi planas, pasa sobre edificaciones y cruza 16 veces las vías.

**Lo que manda es la intensidad de la lluvia, no el volumen.** El 3 de octubre cayeron 68,2 mm en Los Guayabillos (112 mm entre el 3 y el 4), con un máximo de 12,6 mm/h, y no hay inundación reportada en La Cascada (por confirmar con el GAD/COE). El 30 de octubre hubo unas 3 horas seguidas a 21–61 mm/h. El umbral está entre ambos casos: del orden de **20–25 mm/h sostenidos durante más de una hora** sobre la parte media de la cuenca, tras unos 20 mm de pérdida inicial.

Una vez superado ese umbral, el vaso se llena en pocas horas y lo que fija la altura del agua es la **capacidad de salida**, no el almacenamiento. El 30 de octubre el vaso se llenó horas antes del pico de la crecida.

## Lo que reproduce el modelo 2D

El [modelo hidrodinámico 2D](../modelo-2d/) con la lluvia medida reproduce el evento:
- el agua empieza a acumularse en el punto más bajo a media tarde;
- alcanza su máximo hacia las **22:00–22:30**, con **≈1,8 m en el centro del barrio** (1,4–2,7 m según los parámetros);
- la crecida que entra al barrio va de ≈47 a ≈319 m³/s según los parámetros (central, ≈147 m³/s).

Ese rango es tan amplio que el modelo **no sirve todavía para dimensionar obras**. La lámina modelada es compatible con el único testimonio con fuente (agua «hasta dos metros»), pero no lo valida: no se sabe en qué punto del barrio se observó.

## Las cotas de esta página

Las cotas salen del modelo de superficie Copernicus GLO-30 (DSM), que incluye techos y copas de árboles. Frente a los puntos acotados del IGM se desvía ±2–4 m (en zona poblada, de media −3,4 m), así que son orientativas: ninguna cota absoluta del DSM sirve como umbral normativo. Los desniveles locales son más fiables que las cotas absolutas.

# La salida natural del agua no tiene cauce

La quebrada cartografiada pasa a 28 m del borde norte del barrio. Desde allí, OSM la dibuja hacia el este por el pie del escarpe, pero sin llegar al mar (ver [opciones](../la-cascada-opciones/), apartado «¿Existe ya un cauce hacia el este?»). **Entre el barrio y el mar no hay ningún cauce cartografiado.**

La línea de flujo recorre **1 194 m hacia el SSE**, de la cota 12,0 m a la 1,3 m (pendiente media 0,9 %), hasta la ensenada al oeste del muelle de la DPNG. Por el camino **pasa sobre 28 edificaciones**, que ocupan el 24 % de su longitud, y tiene 16 cruces de vías: 11 calles y la Av. Charles Darwin, que cruza tres veces. Los primeros 400 m son prácticamente planos (0,25 % y luego −0,13 %).

Tabla: Perfil del cauce natural urbano por tramos (DSM).

| Tramo (m) | Cota (m) | Pendiente | Lectura |
|---|---|---|---|
| 0–400 | 12,0 → 11,8 | 0,25 % / −0,13 % | Fondo de la depresión, sin pendiente útil |
| 400–600 | 11,5 → 9,6 | 1,0 % | Umbral y comienzo del descenso |
| 600–800 | 9,2 → 5,8 | 1,8 % | El tramo más inclinado |
| 800–1 194 | 5,7 → 1,3 | 1,0–1,2 % | Frente costero y Av. Charles Darwin, bajo la influencia de la marea |

* Cota del DSM (±2–4 m), orientativa.

La calle **Marchena**, de 1 040 m, es la única vía continua alineada con este eje y la candidata natural a funcionar como calle-canal. Hoy no puede hacerlo: al salir del barrio sube unos 3 m (una parte puede ser efecto de los techos en el DSM). Además cruza unas 20 calles transversales y su pendiente media es de solo 0,64 %, con tramos en contrapendiente.

**Sobre la línea de flujo hay un umbral** de unos +1,4 m en Isla Santiago – Karl Angermeyer (−90,3121; −0,7372). Retiene el agua que ya desbordó del vaso del barrio. Con 30 m de resolución no se puede distinguir si es un lomo de lava o un relleno urbano.

Según la prensa (2023, sin fuente oficial), **Santa Cruz no tiene alcantarillado pluvial**, y el drenaje depende de sumideros que infiltran hacia las grietas del basalto. Está por verificar con el GAD.

Tabla: Obstáculos identificados sobre la salida natural.

| Tipo | n | Observación |
|---|---|---|
| Umbral sobre la línea de flujo (Isla Santiago – Karl Angermeyer) | 1 | +1,3–1,4 m sobre el fondo local; retiene el agua desbordada |
| Umbral en la cabecera de Marchena | 1 | +3 m; una parte puede ser efecto de los techos en el DSM |
| Cruces de vías | 16 | 11 calles y la Av. Charles Darwin (3 cruces). Se desconocen las rasantes, los bordillos y los pasos bajo la vía |
| Edificaciones sobre la línea de flujo | 28 | Hay muros y cerramientos sin cartografiar |
| Desembocadura | 1 | Tramo plano a 3–4 m de cota, edificado y con influencia de la marea. Con El Niño, el mar está ≈0,4–0,5 m sobre su marea y las pleamares llegan a 1,1–1,4 m (mareógrafo de Puerto Ayora, oct-2026). El 30-oct el pico llegó con el mar bajando (ver [Modelo 2D](../modelo-2d/)) |

* Cota del DSM (±2–4 m), orientativa.

![La Cascada: relieve, edificaciones, llenado estático de la depresión a las cotas 13–16 m, salida natural del agua hacia el mar y obstáculos sobre ella. En morado, el interceptor hipotético que se describe en la página de opciones.](figuras/f_mapa_barrio.png)

## Por dónde sale el agua cuando el vaso rebosa

Medida como ruta de mínimo umbral (con un margen de 20 m a cada lado), la salida cruza el rebose y se divide en dos ramas:
- **sur**: 1,5 km hasta la bahía, con el 94 % del recorrido en zona poblada y 208 edificios a menos de 20 m;
- **este, por el fondo de la fosa tectónica (graben)**: 2,2 km hasta el mar, con el 76 % en zona poblada y 185 edificios.

La línea de flujo de arriba (1 194 m y 28 edificaciones atravesadas) cuenta solo los edificios que esa línea cruza. Son dos maneras de medir la misma salida.

# Quién y qué está expuesto

Tabla: Edificaciones y población expuestas. La población del INEC se reparte por área de techo (en la página técnica de la cuenca se reparte por área de la manzana, lo que explica pequeñas diferencias). Entre paréntesis, la estimación de la SNGR.

| Zona | Área (ha) | Edificios | Población |
|---|---|---|---|
| Polígono del barrio (unión de OSM y CGREG) | 6,1 | 260 | 1 310 (1 309) |
| Área afectada aproximada, radio de 350 m (por validar) | 38,2 | 772 | 3 641 (3 602) |
| **Vaso cerrado, de 12,5 m al rebose (cifra de referencia)** | 3,7–6,2 | **68–204** | **≈ 400–910** |
| Sensibilidad: zona baja cerrada, DSM ≤ 13,25 m (4 vecinos) | 5,3 | 140 | ≈ 710 |
| Sensibilidad: zona baja cerrada, proxy de suelo ≤ 12,0 m | 15,0 | 374 | ≈ 1 680 |
| Franja de 15 m del cauce natural urbano | 3,6 | 57 | ≈ 150 |
| Franja de 30 m del cauce natural urbano | 7,4 | 130 | ≈ 300 |

* Cota del DSM (±2–4 m), orientativa.

- **Dentro del vaso** (de 12,5 m al rebose) hay **68–204 edificios, unas 400–910 personas y 74–182 viviendas**. El mínimo cuenta los edificios por su centroide a 12,5 m; el máximo, los que tocan la mancha justo bajo el rebose. Las cifras para cotas por encima del rebose describen el camino del desborde, no agua almacenada, y no miden exposición.
- **Aguas abajo**, a lo largo de la salida natural, hay 57 edificios en la franja de 15 m y 130 en la de 30 m. Cualquier mejora de la salida lleva más agua hacia ellos.
- **El cauce urbano no tiene protección normativa.** La franja de protección de quebradas del CGREG («encañadas», 20 m) **no tiene ningún polígono en Puerto Ayora**; el más cercano está a unos 4,7 km.
- **Indicios de crecimiento hacia el escarpe, sin fecha.** Hay 1 201 de 4 854 edificios del suelo urbano de Puerto Ayora (25 %) fuera de la antigua zona urbana del IGM. En el entorno de 500 m de La Cascada son pocos, 43 de 1 524, pero 36 de ellos están **al norte, hacia el pie del escarpe**, por donde entra el agua. Para confirmar si el crecimiento fue hacia allí hacen falta imágenes históricas o el catastro con las fechas de los permisos.

Los servicios críticos de la zona baja, los refugios y el resto de riesgos de la isla están en [Riesgos y observaciones](../riesgos/).

# Qué falta saber

Con estos datos no se puede saber:
- la **cota real del rebose** (entre unos 12,0 y 13,25 m en el DSM), que solo se fija con GNSS;
- las cotas reales de calles, bordillos y plantas bajas;
- si existen sumideros y pasos bajo las vías, y qué capacidad tienen; si hay alcantarillado pluvial (por verificar con el GAD);
- los sótanos y los muros que cortan el flujo;
- si el umbral de Isla Santiago – Karl Angermeyer es un lomo de lava o un relleno urbano;
- la fecha de la expansión urbana;
- la lámina real del evento y en qué punto se observó el agua «hasta dos metros».

Con un catastro, la red pluvial levantada y topografía de 0,5 m, las cifras de esta página podrían cambiar sustancialmente. Ningún punto se ha visitado en campo.

# Datos y método

El diagnóstico urbano parte del DSM GLO-30 y de un **«proxy de suelo»** construido a partir de él: el mínimo del DSM en una ventana de 3 × 3 celdas (90 m), que reduce el sesgo que introducen los techos. Sobre esa base se usaron:
- las vías de OSM con nombres (31-oct-2026);
- los edificios de OSM y Google Open Buildings v3;
- las manzanas del INEC con su población estimada y las viviendas de la SNGR;
- el suelo urbano del CGREG;
- las quebradas del IGM y de OSM, y la franja de 20 m del CGREG.

Con estas capas se trazaron tres elementos:
- la **línea de flujo D8** del barrio al mar;
- la **ruta de menor coste por la red de calles**, que penaliza cada metro de subida;
- un **llenado tipo «bañera»** conectado al fondo del barrio.

La cuenca, el vaso, los tiempos de concentración, los hidrogramas y la incertidumbre se explican en [La Cascada: cuenca, vaso y crecida](../hidrologia/). Las fuentes están en [Métodos, datos y descargas](../metodos/).

## Archivos

- Obstáculos sobre la salida natural: `datos/urbano/tapones.geojson`.
