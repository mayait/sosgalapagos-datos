Intro: Qué muestra un modelo 2D de inundación con la lluvia medida el 30 de octubre: cuándo llegó el agua a La Cascada, cuánta y por dónde salió. También qué juego de parámetros se toma como principal y por qué, cómo se contrastó y hasta dónde llega: el modelo explica el mecanismo, pero no sirve todavía para dimensionar obras.

# Lo que muestra el modelo

Es un modelo de inundación **bidimensional distribuido** («rain-on-grid»): la lluvia medida cae sobre cada celda, una parte se pierde por infiltración y el resto escurre por el terreno. No está calibrado con caudales ni con marcas de agua, y corre sobre un modelo de superficie de 30 m que incluye techos y vegetación. **Sirve para entender el mecanismo, el orden de magnitud y la secuencia del evento, no para delimitar zonas ni fijar cotas normativas.** El método está al final de esta página.

Se usan dos juegos de parámetros de pérdidas: **(a)**, SCS-CN distribuido, y **(b)**, pérdida inicial más pérdida constante. El (b) es el principal (ver «Qué juego se toma como principal»).

## Resultados del 30 de octubre

Tabla: Resultados del modelo 2D del 30-oct (lluvia central; hora UTC−6). Los calados son sobre el DSM.

| Magnitud | Juego (a) SCS-CN | Juego (b) pérdida constante |
|---|---|---|
| La Cascada, centro del barrio: calado máximo | **2,4 m** | **1,8 m** |
| La Cascada, celda más baja (≈10,5 m*): calado máximo | 4,6 m | 4,0 m |
| Nivel máximo del agua (DSM) | 15,3 m* | 14,8 m* |
| Llegada del agua al centro (≥ 0,1 m) | 20:40 | 20:53 |
| Hora del calado máximo en el barrio | 22:11 | 22:24 |
| Caudal de entrada a La Cascada: pico (hora) | 345 m³/s (22:01) | 147 m³/s (22:12) |
| Volumen que entra a La Cascada (hasta 08:00 del 31-oct) | 3,2 hm³ | 1,1 hm³ |
| Salida al mar: pico (hora) | 403 m³/s (22:27) | 155 m³/s (22:34) |
| Vaso de Matazarnos (SC-002) | 3,9 m | 3,3 m |
| Cruce de la Av. Charles Darwin (44 km²) | 2,0 m | 1,6 m |
| Tomás de Berlanga, cauce: calado (llegada) | 0,49 m (19:00) | 0,35 m (20:00) |
| Tomás de Berlanga, escuela | seca | seca |
| Bellavista, centro (llegada SC-003) | 0,71 m | 0,53 m |
| Superficie con más de 1 m de agua / entre 0,5 y 1 m | 143 ha / 141 ha | 89 ha / 95 ha |

\* Cota del DSM (±2–4 m), orientativa.

## Cómo se llenó La Cascada

1. La lluvia de la tarde (15:00–16:00) y la que cae sobre el propio barrio empiezan a llenar la parte más baja hacia las 15:30.
2. El pulso de 18:00–21:30 genera la crecida de las dos ramas.
3. El agua entra a La Cascada a partir de las 20:30–21:00.
4. El barrio se llena y desborda hacia Matazarnos y el frente urbano, que a su vez se llenan. El nivel máximo se alcanza **entre las 22:10 y las 22:25**.
5. Después, el agua baja lentamente. A las 08:00 del 31-oct quedan 2,6–3 m en la celda más baja, porque el vaso no tiene salida por gravedad, y 0,5–0,8 m en el centro.

En Tomás de Berlanga, el 2D confirma un flujo por el cauce no cartografiado de 0,3–0,5 m de calado y 1,5–1,9 m/s. La escuela no se inunda con esta resolución. Si allí entró agua, fue por las calles y por los pasos bajo la vía, que una malla de 30 m no representa (ver [Tomás de Berlanga, Bellavista y resto de la isla](../parte-alta/)).

![Calado máximo del 30 de octubre, juego (b), el principal.](figuras/m2d_calado_max_b_central.png)

![Hora de llegada del agua (calado ≥ 0,1 m), juego (b).](figuras/m2d_hora_llegada_b_central.png)

![Animación cada 10 minutos, juego (b), del 30-oct a las 12:00 al 31-oct a las 08:00.](figuras/anim_30oct.gif)

![Calado máximo con el juego (a), SCS-CN, como envolvente superior.](figuras/m2d_calado_max_central.png)

# Qué juego se toma como principal

**Se toma el juego (b) como principal** porque es el único que cumple a la vez dos condiciones: reproduce el 30-oct y deja sin inundación el 3–4 oct, días en que no consta inundación (por confirmar con el GAD/COE). El juego (a) queda como envolvente superior: sería el válido si llegara a confirmarse que esos días sí hubo inundación.

Los dos juegos coinciden en tres puntos:
- La Cascada se inunda cuando llueve con **intensidad alta y sostenida** sobre la parte media de la cuenca, del orden de **más de 20–25 mm/h durante más de una hora**.
- El agua llega al centro del barrio **unos 40–60 minutos después del máximo de lluvia** (20:00–21:00) y unas 2,5–3 horas después del inicio del pulso intenso (18:00).
- Una vez dentro, queda atrapada en el vaso durante horas.

Y discrepan en lo que importa para una obra: el caudal. Con la lluvia central, la crecida que entra al barrio va de 47 a 319 m³/s según la pérdida constante del juego (b), y es de 345 m³/s con el juego (a). **El diseño de obras no puede apoyarse en este modelo sin aforos.**

# Validación

## Contraste con lo observado

- **Calado frente al testimonio.** El testimonio habla de agua «hasta dos metros» (prensa, por validar). El modelo da 1,8 m (b) y 2,4 m (a) en el centro del barrio, y 4–4,6 m en la celda más baja del DSM. **Es compatible**, pero no discrimina: no se sabe el punto exacto del testimonio y el DSM tiene ±2 m de error.
- **Hora frente a la SNGR.** El agua llega al barrio a las 20:40–20:55 y alcanza el máximo a las 22:10–22:25 del 30-oct. Esto coincide con la «tarde y noche del 30» de la SNGR y con el corte de las estaciones a las 21:25.
- **Volumen frente al modelo agregado.** Con el juego (a), el volumen que entra al barrio (3,2 hm³) es el 69 % de la escorrentía agregada de su cuenca (4,6 hm³). El resto queda retenido en depresiones del DSM aguas arriba o sigue escurriendo a las 08:00. El caudal pico (345 m³/s a las 22:01) cae dentro del rango agregado (325–497 m³/s; ver [La Cascada: cuenca, vaso y crecida](../hidrologia/)). El juego (b) reduce el volumen a 1,1 hm³ y el pico a 147 m³/s.

## Validación condicional con días sin inundación reportada

La red IERSE midió estos días de lluvia sin que conste inundación en La Cascada, aunque está **por confirmar con el GAD/COE**:
- **3 de octubre:** 68,2 mm en Los Guayabillos, con 12,6 mm/h de máximo horario (cobertura del 100 %).
- **4 de octubre:** 43,8 mm más.
- **23 de octubre:** 97,2 mm en Santa Rosa, con 28,2 mm/h. Este día **se descarta para La Cascada**: Los Guayabillos midió 0 mm, así que la lluvia cayó al oeste, fuera de la cuenca. En el modelo, ninguno de los dos juegos lleva agua al barrio ese día.

Tabla: Validación condicional con el 3 y el 4 de octubre (sin inundación reportada, por confirmar).

| Juego | Centro del barrio | Celda más baja | Caudal de entrada | Volumen que entra | ¿Cumple? |
|---|---|---|---|---|---|
| (a) SCS-CN | 1,2 m | 3,3 m | 27 m³/s | 1,2 hm³ | **No**: inundaría el barrio |
| (b) pérdida constante de 25 mm/h | 0,0 m | 0,5 m (lluvia local) | 0 m³/s | 0 | **Sí** |

**Qué cambia entre los dos juegos.** El SCS-CN reparte las pérdidas según el **volumen** acumulado. Cualquier día de 60–70 mm sobre suelo húmedo produce escorrentía, y el vaso, que se llena con decenas de miles de metros cúbicos, se inunda. La pérdida constante, en cambio, depende de la **intensidad**: solo escurre la lluvia que supera la capacidad de infiltración del basalto. El 3-oct, con un máximo de 12,6 mm/h (26 mm/h en 10 min), casi nada supera esa capacidad. El 30-oct hubo unas 3 horas seguidas a 21–61 mm/h, y la mayor parte de esa lluvia escurre. Con el juego (b), la **intensidad**, y no el volumen diario, es lo que separa un día sin inundación de uno con inundación.

## Rango de parámetros compatible con ambas condiciones

Barrido de la pérdida constante en Parque y zona agrícola, con 20 mm de pérdida inicial:

Tabla: Barrido de la pérdida constante, juego (b).

| Pérdida constante | 3-oct: centro / caudal de entrada | 30-oct: centro / caudal de entrada |
|---|---|---|
| 10 mm/h | 0 m / 0,5 m³/s | 2,4 m / 319 m³/s |
| 15 mm/h | 0 m / 0,6 m³/s | 2,3 m / 268 m³/s |
| 20 mm/h | 0 m / 0 m³/s | 2,1 m / 211 m³/s |
| **25 mm/h** | **0 m / 0 m³/s** | **1,8 m / 147 m³/s** |
| 30 mm/h | 0 m / 0 m³/s | 1,6 m / 82 m³/s |
| 35 mm/h | 0 m / 0 m³/s | 1,3 m / 47 m³/s |

Cualquier pérdida constante de al menos 10–15 mm/h deja el barrio sin inundar el 3-oct. Con 15–25 mm/h se obtienen 1,8–2,3 m en el centro el 30-oct. El calado del 30-oct es poco sensible a este parámetro, pero **el caudal pico varía unas 7 veces** (47–319 m³/s). Por eso el diseño de obras no puede apoyarse en este modelo sin aforos.

![Series simuladas en La Cascada con los juegos (a) y (b): 30-oct y 3–4 oct, con la lluvia horaria de Los Guayabillos.](figuras/m2d_validacion.png)

# Sensibilidad y límites

## Sensibilidad

Tabla: Sensibilidad del modelo 2D (30-oct; calado en el centro de La Cascada y caudal de entrada).

| Variante | Juego (a): centro / caudal de entrada | Juego (b): centro / caudal de entrada |
|---|---|---|
| Central | 2,4 m / 345 m³/s | 1,8 m / 147 m³/s |
| Lluvia baja (× 0,85, 152 mm) | 2,2 m / 246 m³/s | 1,4 m / 58 m³/s |
| Lluvia alta (gradiente con la cota, ≈208 mm) | 2,7 m / 454 m³/s | 2,0 m / 204 m³/s |
| Manning × 0,6 | 2,2 m / 413 m³/s (pico 21:34) | 1,8 m / 216 m³/s (21:43) |
| Manning × 1,4 | 2,6 m / 290 m³/s (pico 22:27) | 1,8 m / 101 m³/s (22:50) |
| CN 68 en lugar de 76 | 2,2 m / 265 m³/s | — |

- El calado en el barrio varía poco: 1,4–2,7 m en todas las variantes. Lo controlan la cota del umbral de salida y el remanso en Matazarnos y el frente urbano, no el caudal.
- La rugosidad casi no cambia el calado, pero desplaza el pico unos ±30–40 minutos y cambia el caudal en un factor de 1,4–2.
- Lo que más pesa en los caudales y en la extensión inundada es el juego de pérdidas, (a) frente a (b).

**¿Es razonable el gradiente del escenario alto?**

- El escenario alto interpola la lluvia entre Los Guayabillos (178 m) y Santa Rosa (416 m) y la mantiene constante por encima.
- Dos fuentes independientes apoyan esa forma:
  - en el reanálisis GAR (TU Berlín, modelo de 2 km, 1980–2025), el máximo diario medio crece ≈1,5–1,8 veces de la costa a 300–400 m y se estabiliza por encima [E];
  - en la red DARWIN, las mayores intensidades de El Niño 2023–24 se midieron en la costa y a cotas medias, no en la cumbre (Tenelanda et al. 2025).
- **No hay base para extrapolar por encima de Santa Rosa.**
- Ambas fuentes indican también que la franja costera de la cuenca recibe **menos** que Los Guayabillos: en GAR, ≈0,55–0,65 veces. El escenario central (Los Guayabillos uniforme) sobrestima algo la lluvia sobre la parte baja; el escenario bajo (× 0,85) cubre parte de ese efecto.
- El 30-oct no fue así en la costa después de las 22:00: el M0191 de Puerto Ayora siguió midiendo lluvia fuerte cuando la red IERSE ya estaba cortada (ver «Límites»).

![Lluvia y cota en Santa Cruz y San Cristóbal según el reanálisis GAR (lluvia modelada, celdas de 2 km). Estrellas: lluvia medida el 30-oct (mínimos).](figuras/marburg_gar_gradiente.png)

## Límites

- **Terreno.** El DSM de 30 m incluye techos y vegetación (±2–4 m; sesgo de unos −2 m frente al IGM). No representa calles, muros, alcantarillas ni cauces estrechos. Los calados absolutos tienen una incertidumbre del orden de ±1–2 m.
- **Pérdidas.** Ningún juego está calibrado con caudales. El juego (b) se apoya en una validación condicional (sin inundación reportada, por confirmar), y su pérdida constante (10–35 mm/h) solo está acotada.
- **Lluvia.** Es puntual y mínima: hay dos estaciones útiles, ambas fuera de la cuenca, que dejaron de transmitir a las 21:25. **La lluvia de entrada se corta a esa hora.** El pluviómetro M0191 del INAMHI, en Puerto Ayora, midió **135 mm más entre las 22:00 y las 03:00** [M]. Si esa lluvia también cayó en la parte media de la cuenca, lo que no se sabe, el vaso de La Cascada siguió recibiendo agua después del máximo que da el modelo (ver [La lluvia](../lluvia/)).
- **Mar.** El modelo fija el mar en +0,75 m. El mareógrafo de Puerto Ayora (IOC, operado por el INOCAR) midió otra cosa [M]:
  - a la hora del pico (22:12–22:34) el mar estaba en **+0,13 a +0,05 m** y bajando, 1,5 h antes de la bajamar de medianoche (−0,11 m). Es decir, **0,6–0,7 m por debajo** del supuesto;
  - la pleamar había sido a las 17:50 (+1,21 m). Durante la simulación el mar varió entre −0,41 y +1,21 m;
  - la comparación supone que el cero del DSM coincide con el nivel medio del mar de 2017–2024 del mareógrafo, algo que no está comprobado. Vale para el sentido (el modelo puso más mar del que hubo), no para los centímetros.
- **Qué implica el mar.** Con +0,75 m quedan bajo el mar desde el inicio 7 celdas de tierra (≈0,6 ha) en la orilla de Pelican Bay y junto al muelle; con el nivel real de esa hora, ninguna. Para La Cascada, Matazarnos y el cruce de la Av. Charles Darwin, cambiar el mar entre −0,1 y +1,2 m no cambia el resultado: están a 10–15 m* y los controla su propio umbral. **El supuesto es conservador para la orilla y neutro para el barrio. La marea no agravó La Cascada el 30-oct.**
- **Mar alto por El Niño.** Desde septiembre el mar está **0,26–0,51 m por encima de su marea astronómica** en Puerto Ayora y Baltra; a finales de octubre, +0,43 a +0,51 m [M]. Las pleamares de esos días llegaron a 1,1–1,4 m. Si una tormenta así coincide con una pleamar de mareas vivas, como la del 27–28-oct (+1,36 m), el último tramo de la salida (1,3–5 m* de cota) tendría ≈1,3 m más de mar que el 30-oct a las 22:30, más el oleaje, que el mareógrafo no ve.
- **Contraste con ANUGA.** Se repitió el juego (b) con ANUGA: 20 400 triángulos de hasta 8 000 m² (2 000 m² en zona urbana), desde las 17:00 y partiendo de terreno seco. Los dos motores coinciden en lo esencial:
  - nivel máximo del agua en La Cascada: 14,5 m con ANUGA frente a 14,8 m con LISFLOOD-ACC;
  - hora del máximo: 22:17 frente a 22:24;
  - Matazarnos: 13,9 m frente a 14,0 m;
  - superficie con más de 1 m de agua: 89 ha en los dos.

  Los calados en puntos concretos difieren hasta ±0,8 m, porque cada malla promedia de forma distinta la cota del DSM en la celda o en el triángulo. El caudal de entrada también difiere (67 frente a 147 m³/s): ANUGA arranca seco a las 17:00 y la sección de control se calcula de otra manera. Las salidas están en `datos/modelo2d/b_central_desde17h_anuga/`.
- **Resolución.** Con 30 m no se resuelven los pasos bajo vías ni la red de calles. Una versión de 10–15 m solo tiene sentido con un modelo del terreno de dron o LiDAR.

\* Cota del DSM (±2–4 m), orientativa.

![Lluvia y marea en cada evento de Santa Cruz: nivel del mar observado en Puerto Ayora a la hora de cada pico de lluvia y de cada hito del modelo 2D (juego b).](figuras/mareas_tabla_eventos.png)

# Método

## Planteamiento

La lluvia medida cae sobre cada celda, una parte se pierde por infiltración y el resto escurre por el terreno siguiendo las ecuaciones de aguas someras.

- **Dominio.** Toda la cuenca que drena a Puerto Ayora (47 km², incluida la de La Cascada), con 150 m de margen y una franja de mar. Abarca Bellavista, Tomás de Berlanga, La Cascada y el frente urbano.
- **Terreno.** Es el DSM Copernicus GLO-30. En el mar se supone un fondo de −3 m.
- **Contornos.** El mar tiene un nivel fijo de **+0,75 m**. Es un supuesto: a la hora del pico el mar real estaba entre +0,05 y +0,13 m (ver «Límites»). El resto del contorno es una pared.
- **Rugosidad de Manning.** 0,08 en zona urbana (los edificios como rugosidad alta), 0,06 en zona agrícola, 0,08 en Parque (lava y matorral) y 0,03 en el mar.
- **Lluvia.** Medida por la red IERSE-WSN (Universidad del Azuay), en intervalos de 10 min. Cerro Crocker queda excluido.
  - Escenario **central**: Los Guayabillos repartido de forma uniforme (179 mm).
  - Escenario **bajo**: la misma serie × 0,85, como reducción areal (152 mm).
  - Escenario **alto**: gradiente con la cota entre Los Guayabillos y Santa Rosa (≈208 mm de media).
  - La simulación arranca a las 12:00 del 30-oct. La lluvia de la mañana se cuenta en las pérdidas iniciales.

## Comparación de motores

Tabla: Motores de cálculo usados para el 30-oct.

| Motor | Malla | Estado | Resultado |
|---|---|---|---|
| Esquema inercial local de Bates et al. (2010), el de LISFLOOD-FP, con la ponderación θ = 0,8 de de Almeida et al. (2012); programado en Python/numpy | Regular de 30 m: unas 58 000 celdas y 52 km². Paso de tiempo adaptativo (α = 0,7), unos 21 000 pasos por evento | Completo: juegos (a) y (b), tres escenarios de lluvia, sensibilidad y validación condicional | Todos los resultados de esta página. Cada evento de 20 h tarda alrededor de **1 minuto** en un ordenador portátil |
| ANUGA 4.1 (volúmenes finitos sobre malla triangular) | Triangular: 47 000 triángulos en la prueba de rendimiento; 20 400 en la corrida de contraste (juego (b), desde las 17:00, partiendo de terreno seco) | Terminado: la corrida de contraste tardó 2,4 h | Coincide en lo esencial con el esquema inercial (ver Límites). Con 47 000 triángulos necesita unos 13 minutos por hora simulada en plena crecida, así que se usa solo como contraste |

El esquema inercial usa la ponderación θ = 0,8 porque amortigua las oscilaciones en aguas profundas y planas.

## Los dos juegos de parámetros de pérdidas

- **Juego (a), SCS-CN distribuido.** CN de 55 en Parque, 76 en zona agrícola y 90 en zona urbana (AMC II), con un factor sobre S de 0,665. Ese factor se calibró para que la escorrentía total de la cuenca de La Cascada sea igual a la del modelo agregado con CN 76 (109 mm). Reproduce el 30-oct sin ninguna otra restricción.
- **Juego (b), pérdida inicial más pérdida constante.**
  - Pérdida inicial de 20 mm y pérdida constante de **25 mm/h** en Parque y zona agrícola.
  - En zona urbana, 5 mm y 5 mm/h: refleja techos que vierten a cisternas y sumideros que descargan a grietas.
  - La pérdida constante se aplica a la lluvia y también al agua que corre por la superficie, así que incluye las **pérdidas de transmisión** en los cauces sobre basalto fracturado.
  - Este juego reproduce el 30-oct y, además, deja sin inundación los días de lluvia de octubre sin inundación reportada (ver «Validación»).

## Archivos

El modelo está en `scripts/24_modelo2d_santa_cruz.py`. Las salidas de cada escenario están en `datos/modelo2d/<escenario>/`:
- calado y velocidad máximos, hora de llegada y hora del máximo, en GeoTIFF;
- `calado_max_clases.geojson`, con clases de 0,1–0,5, 0,5–1, 1–2 y más de 2 m;
- `series_puntos.csv`, con las series en los puntos de control (La Cascada, Tomás de Berlanga, Bellavista, Matazarnos, Pelican Bay y seis cruces de vía);
- `caudales_secciones.csv`, con el caudal de entrada a La Cascada y la salida al mar;
- `cuadros_10min.npz`, con los cuadros cada 10 minutos;
- `resumen_<escenario>.json`.

El nivel del mar observado y predicho está en `geodatos/datos/mareas/` del repositorio, y la lluvia y la marea de cada evento, en `datos/lluvia_mareas_eventos.csv` (`scripts/30_lluvia_mareas.py`).
