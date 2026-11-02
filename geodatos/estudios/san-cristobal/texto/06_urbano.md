[[SALTO]]

# 6. Diagnóstico urbano: Puerto Baquerizo Moreno y El Progreso

> **TOTALMENTE PRELIMINAR.** Diagnóstico de gabinete con DSM de 30 m, OSM, Open Buildings e INEC. **No hay lluvia medida en San Cristóbal**: los caudales corresponden a un escenario de 100 mm (sección 5). Los nombres de las encañadas siguen la correspondencia de la sección 4.6, que es una hipótesis.

## 6.1 Ámbito y método

- **Ámbitos analizados.** Cada sección usa su propio polígono, así que el número de edificios varía:

| Localidad | Polígono que usa esta sección | Área | Edificios | Personas (INEC) |
|---|---|---|---|---|
| Puerto Baquerizo Moreno | Límite urbano del IGM ∪ huella edificada a < 2,5 km del centro | 145 ha | 2 703 | ≈6 900 |
| El Progreso | Suelo urbano del CGREG ∪ huella edificada a < 300 m | 23 ha | 183 | ≈250 |

  Las otras cifras del estudio (≈3 000 y 2 988 edificios en el puerto; 206 y ≈210 en El Progreso, con 35 ha) usan polígonos de zona poblada más amplios (secciones 4 y 7). Los edificios son los mismos: OSM + Open Buildings v3.
- **Suelo urbano del CGREG:** la capa solo tiene como suelo urbano a El Progreso. El polígono que contiene al puerto figura como «suelo rural». Hay que aclararlo con el GAD, porque condiciona qué norma se aplica.
- **Cauces:** D8 propio sobre el DSM con las quebradas IGM quemadas, con un área drenada de al menos 0,5 km². Cada «sistema» agrupa las celdas de cauce urbanas que salen de la ciudad por el mismo punto. Los nombres siguen la correspondencia de la **sección 4.6**, basada en el Plan de Acción de la UGR. Además, la exposición se calcula también sobre las **cañadas oficiales** de la hidrología (`datos/cañadas_oficiales.geojson`), para que las cifras sean comparables entre secciones.
- **Ocupación del cauce:** edificios cuyo polígono está a ≤ 15 m o a ≤ 30 m de la línea, dentro del polígono urbano.
- **Franja normativa:** la franja de 20 m del CGREG («encañadas»).

![Puerto Baquerizo Moreno: cauces D8 de ≥ 0,5 km², franja del CGREG, edificaciones y cruces priorizados.](figuras/f_urbano_pbm.png)

## 6.2 Quebradas que entran en la ciudad

Tabla: Sistemas de cauce de Puerto Baquerizo Moreno según el D8 de esta sección (Q100 central con CN 70 y rango CN 60–80; valores bajos, ver la sección 5.1).

| Sistema | Encañada oficial (sección 4.6) | Área (km²) | Recorrido urbano (m) | Salida | Edificios a ≤ 15 / ≤ 30 m | Sobre la línea | Población a ≤ 30 m | Franja CGREG a ≤ 30 m | Cruces (con estructura) | Q100 (m³/s) |
|---|---|---|---|---|---|---|---|---|---|---|
| PBM-02 | **Galápagos / Barrio Frío**, tramo bajo | 10,5–10,6 | 643 | Playa de Barrio Frío, en Bahía Naufragio (−0,9032; −89,6129) | 24 / 45 | 6 | ≈100 | 52 % | 5 (2) | 27 (16–42) |
| PBM-03 | **Galápagos**, tramo alto (sector El Manzanillo) | 8,7 | 304 | Sale del borde urbano a ≈60 m* y vuelve a entrar como tramo bajo | 16 / 33 | 6 | ≈90 | 7 % | 2 (0) | 24 (14–38) |
| PBM-07 | **Divino Niño** | 1,5–1,6 | 769 | **Playa de Oro** (UGR; boca D8 en −0,8990; −89,6096) | **60 / 88** | **16** | ≈240 | 41 % | 7 (0) | 5 (3–8) |
| PBM-08 | **Escuela Alejandro Alvear** | 0,7 | 391 | **Bahía Naufragio, junto a la pasarela del muelle de pescadores** (UGR; boca D8 en −0,8979; −89,6096) | 12 / 23 | 2 | ≈30 | 0 % | 2 (0) | 2 (1–4) |
| PBM-05 y 06 | **La Planada → Manzanillo–El Manantial** (ramales de ≈1,6–1,8 km²) | 1,6 | 340 | Salen de la zona a ≈83–87 m* | 18 / 37 | 7 | ≈100 | 0 % | 5 (0) | 5 |

\* Cota del DSM: ±2–4 m. Su sesgo local frente al IGM es de ≈ +1,5 m en Puerto Baquerizo Moreno y de ≈ +1,9 m en El Progreso (sección 4.5). El tramo final de Barrio Frío (PBM-01, 44 m, 11 km²) se suma a PBM-02.

Tabla: Exposición sobre las cañadas oficiales de la hidrología, recortadas al polígono urbano. Para cada cañada se cuenta solo su tramo propio, sin el curso compartido con la Galápagos. **Estas son las cifras que se recomiendan para comparar entre secciones.**

| Encañada oficial | Recorrido urbano (m) | Edificios a ≤ 15 / ≤ 30 m | Sobre la línea | Población a ≤ 30 m | Franja CGREG: solape directo / a ≤ 30 m |
|---|---|---|---|---|---|
| Galápagos / Barrio Frío | 1 187 | 78 / 150 | 19 | ≈440 | 403 m / 1 063 m (90 %) |
| Divino Niño | 795 | 64 / 108 | 14 | ≈370 | 76 m / 137 m (17 %) |
| Manzanillo–El Manantial | 288 | 30 / 52 | 10 | ≈120 | 0 / 0 |
| Playa Mann (quebrada del campus) | 335 | 19 / 32 | 6 | ≈50 | 0 / 0 |
| La Planada | 132 | 15 / 25 | 4 | ≈55 | 0 / 0 |
| Alejandro Alvear | 205 | 11 / 17 | 4 | ≈20 | 0 / 0 |
| Cerro Quemado / Don García | 277 | 9 / 16 | 3 | ≈45 | 0 / 34 m |

**Por qué las cifras cambian de una sección a otra.** Para Barrio Frío se citan 24, 78 y ≈108 edificios a ≤ 15 m; para Divino Niño, 60, 64 y 67; para Alvear, 12, 11 y 7. Hay tres causas:
- **la línea del cauce:** el D8 de esta sección, el de la hidrología y el de la sección 7 se separan entre sí 20–60 m en la ciudad;
- **el tramo:** los sistemas de la primera tabla empiezan donde el cauce alcanza 0,5 km² dentro de la ciudad, mientras que la cañada oficial cuenta todo su recorrido urbano;
- **el polígono urbano.**

La capa de edificios es la misma en todos los casos. Por la misma razón, el **solape directo con la franja** del CGREG es inestable: va de 0 a 403 m en la Galápagos y de 22–33 a 162 m en Divino Niño, según la línea. La medida «a ≤ 30 m» es más robusta.

En conjunto, **228 edificios y unas 550 personas** están a ≤ 30 m de algún sistema de cauce del D8 de esta sección.

**Hallazgos:**

1. **Divino Niño es el cauce más ocupado en relación con su tamaño.** Con 1–1,6 km² y un caudal del orden de 5 m³/s, tiene **14–16 edificaciones sobre la línea** y unos 60 a menos de 15 m. Ninguno de sus 7 cruces con calles tiene una estructura cartografiada. El agua que no cabe en el paso de cada calle corre por calzadas y lotes hasta Playa de Oro, cuya desembocadura, según la UGR, quedó tapada con lodo y piedras.
2. **La Galápagos es el sistema de mayor caudal**: ≈24 m³/s en el tramo alto (sector El Manzanillo) y 25–40 m³/s en el tramo bajo (Barrio Frío), con 100 mm. En su recorrido urbano están los únicos puentes cartografiados de la ciudad (5 del IGM y 2 de OSM) y una alcantarilla de OSM en la calle Azogues. Hay que verificar su sección y su gálibo frente a ese caudal y a las crecidas con troncos y sedimentos.
3. **Los ramales de Manzanillo–El Manantial son mucho menores** (≈1,8 km²; Q100 ≈ 6 m³/s, sección 4.2), pero tienen 30 edificios a ≤ 15 m en menos de 300 m y ninguna franja.
4. **La franja de 20 m del CGREG corre paralela a la Galápagos, pero no protege el resto.**
   - A ≤ 30 m cubre el 52–90 % de la Galápagos, según la línea; el 17–41 % de Divino Niño; y nada de Alvear, Playa Mann, Manzanillo–El Manantial ni La Planada.
   - La franja de Divino Niño **termina dentro de la ciudad**, a unos 200 m del mar. El tramo final, ya construido, no tiene protección normativa, igual que en La Cascada.
   - Dentro de la franja del CGREG hay **97 edificios y unas 270 personas**. Ya están construidos en suelo que debería estar libre.
5. **Salidas al mar** (según la UGR, contrastadas con el D8):
   - la Galápagos desemboca en la playa de Barrio Frío, en Bahía Naufragio, y pasa bajo la Av. Charles Darwin por puentes del IGM;
   - **Divino Niño desemboca en Playa de Oro**;
   - **Alvear desemboca en Bahía Naufragio, junto a la pasarela del muelle de pescadores**.
   
   Las bocas de Divino Niño y Alvear no tienen ninguna estructura cartografiada en su tramo final.

**El Progreso.** No le entra ningún sistema de cauce de 0,5 km² o más con más de dos edificios expuestos. Por su borde sur pasa un cauce de **0,74 km² con 16 edificios a ≤ 15 m** (25 a ≤ 30 m; unas 40 personas), cerca de la escuela Carlos Darwin (sección 7). El Progreso no tiene franja del CGREG. Los cruces de vía de su entorno tienen prioridad media (1–5 km²; 4–13 m³/s).

## 6.3 La quebrada que llega al campus de la USFQ / Galapagos Science Center

![Campus USFQ / GSC: cauce D8 que llega al campus (0,3 km²), cauces vecinos y cruces.](figuras/f_campus_gsc.png)

**De dónde viene.** El cauce que llega al campus (la «quebrada del campus», asignada a la encañada Playa Mann en la sección 4.6) nace en la ladera al este-noreste, a ≈75 m*. Recorre **1,6 km** con una pendiente media del 4,3 % y llega a la costa junto al campus (−0,8951; −89,6093).

- Su cuenca tiene **31 ha (0,31 km²)**, casi sin edificar: 9 edificios y ninguna huella urbana.
- Según la capa de zonificación del Parque del proyecto, el 34 % de la cuenca es zona de **Transición** y el 56 % de **Aprovechamiento sustentable**. Por eso cualquier obra aguas arriba requiere coordinarse con la DPNG.

**Qué cruza.**
- Un camino rural sin nombre a ≈19 m* (CR-SCR-0222).
- La **Vía Universidad**, a la entrada del campus, a ≈8 m* (CR-SCR-0218).

Ninguno de los dos cruces tiene una estructura cartografiada.

**Magnitud.**
- Escenario de 100 mm: **Q ≈ 1 m³/s** (0,6–1,7), con tc ≈ 47 min.
- Si cayera una lluvia como la del 30-oct en Santa Cruz: ≈3 m³/s.

Es un caudal pequeño, pero **llega en menos de una hora**. Basta para inundar un paso de vía sin alcantarilla y para arrastrar sedimento hacia los edificios bajos.

Tabla: Edificios del campus y de su entorno inmediato respecto al cauce (OSM; distancias horizontales a la línea D8, cuya posición tiene un error de decenas de metros).

| Edificio | Plantas (OSM) | Distancia al cauce (m) | Cota* (m) |
|---|---|---|---|
| Edificaciones sin nombre (3) | — | 14–26 | ≈20 |
| Laboratorio de Salud Animal | 1 | 21 | ≈11 |
| USFQ Extensión Galápagos | 2 | 34 | ≈13 |
| Galapagos Science Center | 3 | 40 | ≈13 |

\* DSM: ±2–4 m; sesgo local de ≈ +1,5 m frente al IGM (sección 4.5).

**Lo demás en torno al campus:**

- Hay un **segundo cauce pequeño** (0,3–0,4 km²) que llega a la costa entre 80 y 230 m al sur del campus.
- Alvear (0,7 km²) desemboca en Bahía Naufragio, junto a la pasarela del muelle de pescadores, y Divino Niño (1,6 km²) en Playa de Oro, unos 450–500 m al sur del campus (UGR).
- La franja del CGREG más cercana, la de Divino Niño, termina a **≈370–400 m** del campus. **El cauce del campus no tiene franja normativa.**
- En 2023 se registró una inundación en Playa Mann, a unos 300 m (sección 7).

**Lectura.** Con estos datos, el campus no está expuesto a una crecida de gran caudal, sino a **escorrentía concentrada de una cuenca pequeña y empinada** que cruza la Vía Universidad sin un paso conocido.

Lo que falta saber, y solo se puede saber en campo, es si el agua de Divino Niño o de Escuela Alvear **se desvía por las calles hacia el norte** cuando sus pasos se obstruyen. El D8 no lo ve, porque sigue el terreno y no las calzadas.

**Recomendaciones para el campus:**
- Inspeccionar el paso de la Vía Universidad y el cauce entre el camino rural y la costa.
- Mantener libre de construcciones y cerramientos una franja de 15 m a cada lado.
- Revisar los accesos y las plantas bajas del Laboratorio de Salud Animal y de las edificaciones a menos de 25 m.
- Instalar en el GSC un pluviómetro con transmisión (sección 7).

## 6.4 Normativa y competencias

- **La franja del CGREG existe en San Cristóbal**, a diferencia de Puerto Ayora. Pero está desplazada respecto a los cauces que modela el DSM, se corta en el borde urbano y ya tiene 97 edificios dentro. El **PUGS de San Cristóbal** debería redibujarla sobre un levantamiento de campo de los cauces reales, incluidos los tramos urbanos y los canalizados, y aplicarle un régimen de suelo de protección.
- Las obras en los cauces y en sus desembocaduras corresponden al GAD municipal. Las que estén en la Reserva Marina necesitan además la autorización de la DPNG, y el dominio hídrico público corresponde al MAATE.

## 6.5 Limitaciones

- El DSM no ve las canalizaciones ni los cauces entubados. Si Barrio Frío o Divino Niño están canalizados bajo las calles, la ocupación real puede ser menor y el riesgo de obstrucción, mayor.
- La población del INEC está repartida por área de techo dentro de cada manzana. Es una estimación de orden de magnitud.
- No hay inventario de alcantarillas ni de pasos bajo las vías.

**Archivos:**
- `datos/urbano/cauces_urbanos.geojson`
- `datos/urbano/edificios_expuestos.geojson`
- `datos/urbano/cuenca_gsc.geojson`
- `datos/urbano/cauce_gsc.geojson`
- `datos/urbano/cifras.json`

Se generan con `scripts/16b_urbano_sectores.py`.
