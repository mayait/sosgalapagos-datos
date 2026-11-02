[[SALTO]]

# 4. Hidrología: Puerto Baquerizo Moreno, El Progreso y el campus USFQ / GSC

> **TOTALMENTE PRELIMINAR.** Análisis de gabinete sobre un modelo de superficie (DSM) de 30 m. **No hay lluvia medida en San Cristóbal** (sección 3): los caudales son escenarios de orden de magnitud. Las cotas marcadas con * proceden del DSM (±2–4 m; en Puerto Baquerizo, sesgo local de unos +1,5 m frente al IGM, sección 4.5) y no deben usarse como umbrales.

## 4.1 Métodos

Se aplicaron los métodos ya revisados en La Cascada (Santa Cruz):
- **Flujo:** D8 (pysheds) sobre el DSM Copernicus GLO-30 reproyectado a UTM 16S (30 m), con las quebradas del IGM quemadas (−3 m). Como sensibilidad se repitió sin quemarlas.
- **Vasos:** relleno global desde el mar («priority-flood», equivalente al camino de mínimo umbral), sin ventanas de cálculo y, por tanto, sin bordes artificiales. Un vaso es **robusto** si tiene ≥ 1 m de profundidad y persiste (≥ 0,3 m) con el «proxy de suelo» (mínimo 3×3 del DSM). La exposición se cuenta solo por debajo de la cota de rebose.
- **Hidrología:** SCS-CN (Ia = 0,2 S) e hidrograma unitario SCS; tormenta tipo II de 24 h con 50, 100 y 150 mm y CN de 60, 70 y 80; tc por Kirpich, Témez, SCS lag, TR-55 y Manning, del que se da el rango.
- **Trazado junto al campus:** 400 realizaciones con 1–3 m de ruido añadido al DSM (Monte Carlo) y una repetición en la rejilla geográfica original.

El cálculo se reproduce con `scripts/17_san_cristobal_inundacion.py`; las cifras están en `datos/resumen.json`.

## 4.2 Cuencas que drenan a las zonas pobladas

**Puerto Baquerizo Moreno.** La zona analizada (271 ha, con la huella edificada y las manzanas del INEC) tiene ≈3 000 edificios y ≈7 300 personas.
- Recibe el agua de **11,1 km²** (11,5 km² sin quemar las quebradas).
- Solo el 0,6 % depende del relleno de depresiones de más de 1 m: la conexión no es un artefacto.
- Llegan 14 quebradas de ≥ 0,05 km². Las cinco mayores suman el 81 % del área.

**El Progreso.** Tiene 35 ha, ≈210 edificios y ≈280 personas, y recibe 1,1 km². Su llegada principal (PRO-L01) es la quebrada del IGM que baja de la parte alta, **cuyo trazado termina en el borde noreste del poblado**. Según el D8, el agua sale de El Progreso hacia el oeste y entra en la cuenca de la Galápagos (Barrio Frío). **El Progreso está, por tanto, aguas arriba de Puerto Baquerizo Moreno.**

Tabla: Llegadas principales a las zonas pobladas (D8). Q100: tormenta tipo II de 100 mm; valor central con CN 70 y tc de Témez; entre paréntesis, de CN 60 con Témez a CN 80 con Kirpich. Los nombres siguen la correspondencia con el Plan de Acción SC-4-09-2026 de la UGR del GAD San Cristóbal (sección 4.6).

| Id | Encañada oficial | Área (km²) | Cota máx.* (m) | Pendiente media | Cauce: L (km) / pendiente | tc (h) | Q100 (m³/s) |
|---|---|---|---|---|---|---|---|
| PBM-L01 | Galápagos / Barrio Frío | 5,4 | 526 | 10,4 % | 8,9 / 4,8 % | 1,0–4,2 | 11 (5–35) |
| PBM-L02 | La Planada → Manzanillo–El Manantial | 1,8 | 294 | 8,9 % | 3,7 / 5,3 % | 0,4–2,3 | 6 (3–19) |
| PBM-L03 | Divino Niño | 1,0 | 139 | 6,4 % | 2,2 / 4,6 % | 0,2–1,7 | 4 (2–13) |
| PBM-L04 | Alejandro Alvear | 0,45 | 122 | 8,6 % | 1,7 / 5,6 % | 0,1–1,2 | 2 (1–7) |
| PBM-L05 | Playa Mann (quebrada del campus, § 4.4) | 0,31 | 78 | 8,1 % | 1,3 / 4,6 % | 0,1–1,0 | 2 (1–5) |
| PRO-L01 | Cabecera rural de la Galápagos (quebrada IGM de El Progreso) | 1,0 | 526 | 14,0 % | 3,2 / 6,1 % | 0,3–1,6 | 4 (2–12) |

## 4.3 Puntos potenciales de inundación

**Vasos.** Hay 24 depresiones cerradas de más de 300 m³ dentro de las zonas pobladas o a menos de 100 m (`datos/vasos.geojson`).
- **En Puerto Baquerizo Moreno no hay ningún vaso robusto.** Todos tienen entre 0,3 y 0,85 m de profundidad y desaparecen con el proxy de suelo. A diferencia de La Cascada, el problema de la ciudad no es el almacenamiento, sino **el paso del agua** por las encañadas y por sus salidas al mar.
- **El Progreso tiene 5 vasos robustos**, en una meseta a ≈300–320 m*.
  - El mayor, V01 (−0,9037; −89,5577), está al noroeste del poblado, sobre el cauce que sale hacia Puerto Baquerizo. Ocupa 3,6 ha y ≈61 000 m³, con 4,6 m de profundidad en el DSM pero solo ≈1 m con el proxy de suelo. Tiene 2 edificios.
  - Al sur del centro hay un grupo de vasos pequeños (V03, V06, V08 y V11), de 0,9 a 2,2 m y de 1 700 a 7 100 m³ cada uno, con hasta 15 edificios. Están **a menos de 250 m de dos registros de la SNGR**: el del dispensario del IESS (2021) y el de la Escuela Carlos Darwin (2024) [R]. El vaso de la escuela (V08, 0,9 m) no persiste con el proxy de suelo y queda dentro del ruido.
  - La coincidencia con dos registros independientes sugiere, sin probarlo, que en El Progreso el mecanismo es el **encharcamiento por falta de drenaje** («mala canalización de aguas lluvias», según la SNGR), no una crecida.

**Salidas al mar.** Las llegadas de Puerto Baquerizo desembocan por cuatro puntos. Solo la de Barrio Frío tiene cauce cartografiado.

Tabla: Salidas al mar de Puerto Baquerizo Moreno (D8). Edificios a ≤ 45 m del último tramo, de ≈150 m. Q100 como en la tabla anterior.

| Id | Encañada | Lugar | Área (km²) | Cauce cartografiado al final | Edificios | Q100 (m³/s) |
|---|---|---|---|---|---|---|
| PBM-S01 | Galápagos / Barrio Frío | Playa de Barrio Frío, Poza de las Garzas (−0,9026; −89,6132) | 10,6 | Sí (IGM; puentes) | 25 | 19 (9–58) |
| PBM-S02 | Divino Niño | Playa de Oro (−0,8994; −89,6097) | 1,5 | No | 32 | 6 (3–18) |
| PBM-S03 | Alejandro Alvear | Bahía Naufragio, junto a una pasarela de muelle al sur de Playa Mann (−0,8980; −89,6097) | 1,0 | No | 8 | 4 (2–14) |
| PBM-S04 | Playa Mann (ramal norte) | Norte del campus (−0,8945; −89,6102) | 0,1 | No | 6 | 0,9 (0,4–2) |

**Ranking.** Cada punto suma de 0 a 9 puntos (`datos/puntos_inundacion.geojson`):
- **A. Área aportante:** 0 (< 0,1 km²), 1 (0,1–0,5), 2 (0,5–2) o 3 (≥ 2).
- **E. Edificios:** 0 (< 5), 1 (5–24), 2 (25–99) o 3 (≥ 100). Se cuentan en la franja de 20 m del tramo propio de cada llegada (hasta que se une a una mayor), a ≤ 45 m del tramo final de cada salida o dentro del vaso.
- **C. Confinamiento:** 1 si no hay cauce cartografiado o si el vaso es robusto.
- **H. Antecedente [R]:** 1 si hay un registro de la SNGR a ≤ 250 m. Se excluyen 6 registros con coordenadas genéricas.
- **L. CGREG:** 1 si toca la capa de flujos de lodo por El Niño o la franja de quebradas.

Tabla: Los diez primeros puntos del ranking.

| # | Id | Tipo | Lugar | Área (km²) | Edificios | Puntos (A-E-C-H-L) |
|---|---|---|---|---|---|---|
| 1 | PBM-L01 | Llegada | Galápagos, entrada este (−0,9062; −89,5938) | 5,4 | 110 | 8 (3-3-0-1-1) |
| 2 | PBM-S01 | Salida con cauce | Galápagos, playa de Barrio Frío | 10,6 | 25 | 7 (3-2-0-1-1) |
| 3 | PBM-S02 | Salida sin cauce | Divino Niño, Playa de Oro | 1,5 | 32 | 7 (2-2-1-1-1) |
| 4 | PBM-L02 | Llegada | La Planada (−0,9116; −89,5919) | 1,8 | 45 | 6 (2-2-1-1-0) |
| 5 | PBM-L03 | Llegada | Divino Niño (−0,8996; −89,6035) | 1,0 | 66 | 6 (2-2-1-1-0) |
| 6 | V22 | Vaso no robusto | Desembocadura de Barrio Frío | 10,6 | 2 | 5 (3-0-0-1-1) |
| 7 | PBM-S03 | Salida sin cauce | Alvear, Bahía Naufragio (sur de Playa Mann) | 1,0 | 8 | 5 (2-1-1-1-0) |
| 8 | V15 | Vaso no robusto | La Planada | 2,0 | 8 | 4 (2-1-0-1-0) |
| 9 | PBM-L04 | Llegada | Alvear (−0,8975; −89,6048) | 0,45 | 13 | 4 (1-1-1-1-0) |
| 10 | PBM-L05 | Llegada | Playa Mann, quebrada del campus (−0,8961; −89,6070) | 0,31 | 12 | 4 (1-1-1-1-0) |

El primer punto de El Progreso es el vaso V03 (puesto 13). El ranking sirve para **ordenar las visitas de campo**; no mide el riesgo, porque los pesos son convencionales. V22 es, en la práctica, la boca de Barrio Frío (S01).

## 4.4 La quebrada del campus USFQ / Galapagos Science Center

**Nombre oficial: cañada de Playa Mann** (Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal; sección 4.6). **De dónde viene.** Nace en la ladera al este-noreste del campus, a ≈78 m*, en terreno casi sin edificar. Al llegar a un **rellano a ≈20 m***, entre 160 y 200 m al este del campus, su trazado se vuelve ambiguo:
- **En la rejilla UTM** (este análisis), gira al sur, se une a la encañada de Alvear y llega al mar por la boca D8 de esta, al sur de Playa Mann (−0,8980; −89,6097). Pasa a **157 m** del campus en su punto más cercano.
- **En la rejilla geográfica original** (la de la sección 6), sigue al oeste, **atraviesa el campus** y llega a la costa junto a él (−0,8951; −89,6093).
- **Con 1–3 m de ruido en el DSM**, entre el **12 y el 23 %** de las realizaciones cruzan el campus. En su mayoría entran por la esquina noreste, junto a la Vía Universidad (−0,8950; −89,6083).

El transecto recto del rellano al GSC baja de 19,8 a ≈16 m*, con un resalte de solo 1,6 m, menor que el error del DSM. **Los edificios del campus están 8–13 m* más bajos que el rellano**: nada en el DSM impide que el agua que se salga del cauce ahí (por una obstrucción o siguiendo la calle) baje hacia el campus.

> **Conclusión.** Que la quebrada llegue al campus es **plausible, pero el DSM de 30 m no permite confirmarlo ni descartarlo.** Hay que verificarlo en campo.

Tabla: Cuenca de la quebrada del campus en sus dos puntos de control.

| | Rellano frente al campus | Boca D8 de Alvear, al sur de Playa Mann |
|---|---|---|
| Área | 0,28 km² | 0,98 km² |
| Cota máx.* | 78 m | 122 m |
| Pendiente media de la cuenca | 8,3 % | 7,8 % |
| Cauce principal | 1,23 km; 4,7 % | 2,25 km; 5,2 % |
| tc de Kirpich / Témez | 15 / 38 min | 23 / 58 min |
| tc, rango de los métodos | 7–58 min | 12–98 min |
| Área que depende del relleno de depresiones | 0 % | 0 % |

**Edificios expuestos y acumulación.**
- Con el trazado UTM, ningún edificio del campus queda a ≤ 20 m ni a ≤ 45 m del cauce.
- Con el de la rejilla original, la sección 6 sitúa el Laboratorio de Salud Animal a 21 m, el edificio de la USFQ a 34 m y el GSC a 40 m de la línea.
- **No hay vasos a menos de 150 m: el campus no es una zona de acumulación.** Está en ladera, a ≈90 m del mar, y el agua que le llegue lo cruzaría hacia la costa.
- Aguas abajo, por la ruta de la Escuela Alvear, hay 29 edificios a ≤ 20 m del trazado en 607 m, entre ellos la escuela (inundada en abril de 2023 según la SNGR [R]).
- Las capas CGREG más cercanas (flujos de lodo y franja de Divino Niño) están a 300–350 m. **La quebrada del campus no tiene franja normativa.**

**Salida al mar.** Las dos rutas llegan al mar en menos de 650 m, con un 2–3 % de pendiente y sin vasos intermedios, pero **ninguna tiene cauce cartografiado** en su tramo final. La ruta UTM cruza las avenidas Alsacio Northia y Jaime Roldós; la otra, la Vía Universidad. En ambos casos el agua correría por calzadas y lotes.

Tabla: Caudal pico de la quebrada del campus (m³/s), con tormenta tipo II de 24 h. Cada intervalo va del tc de Témez al de Kirpich.

| Lluvia | CN | Rellano (0,28 km²) | Desembocadura (0,98 km²) |
|---|---|---|---|
| 50 mm | 60 / 70 / 80 | ≈0 / 0,2–0,3 / 0,7–1,2 | ≈0 / 0,5–0,9 / 1,7–3,4 |
| 100 mm | 60 / 70 / 80 | 0,8–1,5 / 1,7–3,0 / 2,8–4,9 | 2,0–3,8 / 4,2–8,3 / 7,1–13,7 |
| 150 mm | 60 / 70 / 80 | 2,5–4,3 / 3,8–6,7 / 5,2–9,0 | 6,0–11,9 / 9,6–18,6 / 13,4–25,4 |

**Cómo leer estos caudales**
- Con 150 mm, la tormenta tipo II concentra ≈68 mm en su hora más intensa. Es del orden de lo medido en Santa Cruz el 30-oct (61–66 mm/h).
- Para dar escala: 4 m³/s por una calle de 8 m con un 2,8 % de pendiente circularían con ≈0,2 m de calado y ≈2,6 m/s; 14 m³/s, con ≈0,4 m y ≈4 m/s. A esas velocidades el agua arrastra sedimento y objetos aunque el calado sea pequeño.
- La sección 6 estima ≈1 m³/s (0,6–1,7) para 100 mm con el método racional; la tormenta tipo II da picos mayores porque concentra la lluvia en pocos minutos.
- Con la lluvia de los modelos (sección 3; 13–59 mm en las 24 h más lluviosas), el caudal en la desembocadura no pasa de ≈2,3 m³/s ni con CN 80. Como esos modelos subestimaron mucho la lluvia de Santa Cruz, es solo un mínimo.

**Qué verificar en campo**
- Si hay paso o alcantarilla en la Vía Universidad y en el rellano.
- Por dónde corrió el agua el 30 y el 31 de octubre: marcas y sedimento.
- La cota real del rellano frente al campus, con GNSS.

## 4.5 Contraste del DSM con los puntos acotados del IGM

Tabla: DSM menos punto acotado del IGM 1:25 000 (m).

| Ámbito | n | Media | Mediana | Desv. típica | RMSE | P5 a P95 |
|---|---|---|---|---|---|---|
| Isla completa | 2 087 | −2,9 | −2,1 | 6,3 | 6,9 | −11,9 a 3,9 |
| ≤ 5 km de Puerto Baquerizo | 96 | +1,5 | +1,8 | 2,6 | 3,0 | −3,2 a 5,4 |
| Dentro de la zona urbana | 21 | +1,0 | +1,1 | 2,8 | 3,0 | −2,3 a 4,8 |
| ≤ 2 km de El Progreso | 25 | +1,9 | +1,5 | 4,7 | 5,1 | −5,5 a 9,3 |

- En el entorno de Puerto Baquerizo el error es de ≈3 m (RMSE), como en Santa Cruz, pero **el sesgo cambia de signo**: +1,5 m, frente a −2,1 m en Puerto Ayora. **El sesgo de «unos −2 m» que usa el estudio no vale aquí**: es local.
- En El Progreso el RMSE sube a 5 m, del orden de la profundidad de sus vasos. En la isla completa hay colas largas (P5 = −12 m) por el relieve y la vegetación de la parte alta.

## 4.6 Contraste con el Plan de Acción de la UGR

La Unidad de Gestión de Riesgos del GAD de San Cristóbal identifica en su plan 15 encañadas oficiales y los sectores afectados en abril de 2025 y abril de 2026 [R] (Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal; documento interno). Los cálculos se reproducen con `scripts/27_canadas_oficiales_san_cristobal.py` y están en `datos/contraste_plan_ugr.json`.

### Correspondencia de nombres

Las capas `cuencas.geojson` y `puntos_inundacion.geojson` llevan ahora la propiedad `cañada_oficial`, y `datos/cañadas_oficiales.geojson` contiene el cauce D8 de cada encañada.

Tabla: Correspondencia entre los cauces D8 y las encañadas oficiales. La confianza es la de la correspondencia, no la del cauce.

| Encañada oficial | Cauces y puntos D8 | Anclaje | Confianza |
|---|---|---|---|
| Galápagos / Barrio Frío | PBM-L01, S01, V22 y PRO-L01 (cabecera rural) | Cuenca principal (10,6 km²) que llega a la playa de Barrio Frío | Alta |
| Divino Niño | PBM-L03, L11, S02 | Desemboca en Playa de Oro (OSM), a 60 m | Alta en la salida; media en el trazado |
| Alejandro Alvear | PBM-L04, L13, S03 | Pasa junto a la E. E. B. Alejandro Alvear. El plan la hace desembocar en Bahía Naufragio junto al muelle de pescadores; la boca D8 (S03) está a 115 m de una pasarela de muelle (OSM), que no se ha podido confirmar como la de pescadores | Media |
| Playa Mann | PBM-L05 (quebrada del campus), L12, S04 | Pasa junto a las oficinas del PNG y llega a Playa Mann (rejilla original y 2D) | Media |
| La Planada | PBM-L02 (tramo alto), L14, V15 | Registro de la SNGR de 2025 a 210 m | Media |
| Manzanillo–El Manantial | PBM-L02 (tramo bajo), L08, L09 | Ramales de ≈1,8 km² que bajan desde La Planada, como dice el plan. El tronco de 8–9 km² que pasa por El Manzanillo es la **Galápagos (tramo alto)**, no esta encañada | Media-baja |
| Palmeras–Arrayanes | PBM-L07 | Entre Las Palmeras (IGM) y la Galápagos; no hay topónimo «Arrayanes» | Baja |
| Cerro Quemado / Don García | PBM-L06, L10 | Laderas de Estación Terrena | Baja |
| CGRS | Recorrido desde el antiguo vertedero del IGM | Ubicación del CGRS sin confirmar | Baja |
| Parque Artesanal | — | No localizado | — |

**Lo que no cuadra:**
- **Cerro Quemado.** El D8 no lleva ninguna ladera a la mina de Cerro Quemado (OSM): Estación Terrena drena a Barrio Frío y la mina vierte hacia el sur. O el cauce está canalizado, o la mina tiene un fondo cerrado que el DSM no resuelve.
- **Playa Mann y Alvear.** En el D8 en UTM la quebrada de Playa Mann es un afluente de Alvear. En la rejilla original y en el 2D se reparte entre ambas (sección 4.4).

### Bifurcaciones: Divino Niño «se separa de la Galápagos» y Alvear «recoge aguas de Divino Niño»

**Lo que puede hacer cada modelo**
- **El D8 no puede bifurcar.** Le da a Divino Niño una cuenca propia de ≈1 km², sin conexión con la Galápagos.
- **El 2D, con trazadores (sección 4b), tampoco reproduce el reparto.** Con la tormenta trasladada:
  - de la lluvia neta marcada en la Galápagos, el 67 % sale por la playa de Barrio Frío y solo el 0,03 % por Playa de Oro; el resto queda almacenado;
  - del agua de Divino Niño, el 75 % sale por Playa de Oro, el 1,7 % por Barrio Frío y el 0,9 % por la boca de Alvear.

**Lo que muestra el terreno: un paso posible, no demostrado.** Fuera de la franja costera, el cauce de la Galápagos (−0,9083; −89,5997; 62 m*) pasa a **466 m** del ramal sur de Divino Niño (−0,9042; −89,6008; 60 m*).
- En la recta entre ambos puntos, el DSM sube **1,2 m** sobre el lecho de la Galápagos.
  - Es una recta de 466 m, no un collado trazado: puede haber pasos más altos o más bajos fuera de ella.
  - El DSM sin quemar suaviza los cauces y eleva su lecho, así que el resalte real probablemente es **mayor**.
- El 2D da allí 0,65 m de calado con la tormenta trasladada y 0,28 m con 100 mm. Para pasar por esa recta harían falta **≈0,55 m más de calado** sobre el escenario trasladado, o una obstrucción, o un relleno que eleve el lecho.
- La SNGR registró en 2010 que «la encañada que atraviesa […] ha sido obstaculizada por relleno» en El Manzanillo [R]. Pero ese registro tiene la coordenada genérica de la SNGR, así que **no se puede situar en este punto**.
- **Hipótesis de confianza media-baja y consecuencia alta:** la separación que describe el plan («a la altura de los talleres del Consejo de Gobierno», que no están localizados) podría estar en este tramo, al noreste de Estación Terrena. Hay que comprobarlo en campo.

**La vía Jaime Roldós no lleva el agua de la Galápagos hacia el hospital.** Desde el puente de la perimetral (45 m*), la vía sube hasta 56 m* en Cerro Patricia y luego baja de 50 a 24 m* hasta el hospital. El agua que, según el plan, «drena por la vía perimetral» e impide el acceso al hospital es, según el DSM, la de la ladera del ramal sur de Divino Niño, no la de la Galápagos.

**Divino Niño y Alvear** pasan a 120 m entre sí cerca de la costa, con un resalte de 2,5 m*, probablemente edificios. Que Alvear recoja agua de Divino Niño es topográficamente posible, pero el 2D lo cuantifica en ≈1 %.

> **Por qué importa.** El plan describe que Divino Niño se separa de la Galápagos y que Alvear recoge aguas de Divino Niño. Si esas conexiones existen, la zona inundable de Divino Niño y Alvear no se limita a su cuenca D8: recibirían parte de la crecida de la Galápagos, en una proporción que este estudio no puede estimar. Ninguno de los dos modelos las representa con un DSM de 30 m sin rellenos ni obras. **Hay que levantar en campo la sección del cauce en ese tramo y los pasos bajo las vías.**

### Validación con los sectores de máxima prioridad del plan

Tabla: Sectores de máxima prioridad del plan frente al ranking (sección 4.3) y el modelo 2D (sección 4b). Calado máximo y número de edificios con ≥ 0,3 m en el radio de cada sector. Las columnas usan mallas distintas: la tormenta trasladada, 15 m; los 100 mm, 30 m.

| Sector del plan [R] | Ranking (puntos cercanos) | 2D, tormenta trasladada (malla de 15 m) | 2D, 100 mm (malla de 30 m) | ¿Lo identifica? |
|---|---|---|---|---|
| Barrio Frío: playa y Poza de las Garzas | S01 (n.º 2), V22 (n.º 6) | 1,4 m; 7 edificios | 0,8 m | **Sí** |
| Manzanillo: desborde a 100 m del puente (abr-2026), sobre la Galápagos (tramo alto) | Ninguno a ≤ 150 m | 0,86 m; 10 edificios | 0,24 m | **Sí en el 2D**; no en el ranking |
| La Planada | V15 (n.º 8); L02 (n.º 4) a 210 m | 0,94 m; 15 edificios | 0,54 m; 6 | **Sí** |
| Divino Niño: Playa de Oro (boca tapada) | S02 (n.º 3) | 0,68 m; 1 edificio | 0,15 m | Sí (la boca); **no** el taponamiento |
| Divino Niño: muro del hospital | Ninguno | 0,34 m | 0,07 m | **No** |
| Divino Niño: vía Jaime Roldós / Colegio I. Hernández | Ninguno | 0,19 m | 0,11 m | **No** |
| Playa Mann | S03 (n.º 7), L05 (n.º 10) | 0,53 m; 1 edificio | 0,12 m | Parcialmente |
| Los Arrayanes / La Picada (ubicación supuesta) | L07 (n.º 31) | 1,0 m; 0 de 23 edificios | 0,53 m | Solo el 2D, y con ubicación dudosa |
| San Francisco, Fragata y Estación Terrena | — | Sin ubicación fiable: no evaluado | — | — |

**Qué se le escapa al análisis y por qué**
1. **Los tramos intermedios de la Galápagos**, como el del puente de la perimetral.
   - El ranking solo puntúa entradas, salidas y vasos; no puntúa los tramos urbanos entre la entrada y la boca.
   - El 2D sí lo marca: 0,86 m y 10 edificios con ≥ 0,3 m.
   - Habría que añadir al ranking los tramos urbanos de cauce.
2. **Los procesos de obra e infraestructura:**
   - la boca de Playa de Oro tapada con lodo y piedras;
   - el muro del hospital;
   - las rejillas y el alcantarillado taponados de Playa Mann;
   - el agua que corre por la vía Jaime Roldós.
   
   El DSM de 30 m no ve calles, muros ni sumideros, y el modelo no transporta sedimento.
3. **Los Arrayanes / La Picada.** No hay topónimo cartografiado y la urbanización queda en el borde del polígono urbano usado, así que su exposición se cuenta casi a cero.
4. **El orden de magnitud de la lluvia.** Con 100 mm, el 2D apenas da 0,24 m junto al puente de la perimetral (Galápagos, tramo alto). El desborde de abril de 2026 sugiere una lluvia mayor u obstrucciones.

### El Progreso: 43 viviendas y 124 personas según el plan

El plan da **43 viviendas y 124 personas** expuestas directamente y atribuye la inundación de los sectores bajos a «cunetas y bordillos» [R]. Nuestros resultados son del mismo orden:

Tabla: Exposición en El Progreso según cada fuente.

| Fuente | Edificios / viviendas | Personas |
|---|---|---|
| Plan de Acción [R] | 43 viviendas | 124 |
| Vasos robustos (V01, V03, V06, V11) | 20 edificios | ≈10 |
| Todos los vasos del poblado (13) | 51 edificios | ≈27 |
| 2D, calado ≥ 0,1 m (100 mm con malla de 30 m / trasladada con malla de 15 m) | 28 / 35 edificios | — |
| 2D, calado ≥ 0,3 m (ídem; trasladada con 30 y 15 m) | 17 / 25–29 edificios | — |
| Total de la zona (INEC) | 206 edificios; 120 viviendas | 276 |

- **El mecanismo coincide:** encharcamiento en depresiones sin salida, no una crecida.
- **La magnitud** (≈30–50 edificios afectados) es compatible con las 43 viviendas del plan.
- **La población** asignada por manzana del INEC (≈10–30 personas) es mucho menor que la del plan. Las manzanas censales no coinciden con los vasos, y un edificio no es una vivienda.
- El plan cifra el 36 % de las viviendas y el 45 % de la población de El Progreso; el 2D, el 14–17 % de los edificios con ≥ 0,1 m.

## 4.7 Incertidumbre

- **DSM:** ±3 m en torno a la ciudad y ±5 m en El Progreso. En tramos con un 1–3 % de pendiente eso equivale al desnivel de 100 m de recorrido, así que las rutas del rellano del campus y de las salidas a Playa Mann son inciertas en decenas a cientos de metros.
- **El DSM no ve** alcantarillas, cauces entubados ni bordillos; en la ciudad el agua sigue las calles.
- **Lluvia:** no hay ninguna medida. Con 100 mm, el caudal pico de la quebrada del campus varía unas 7 veces (2,0–13,7 m³/s) según el CN (60–80) y el método de tc.
- **Campus:** no está cartografiado como polígono. Se aproximó con los edificios universitarios de OSM (0,8 ha).

Tabla: Nivel de confianza de cada conclusión.

| Conclusión | Confianza |
|---|---|
| Área que drena a Puerto Baquerizo (≈11 km²) y peso de la Galápagos (Barrio Frío) | Alta |
| Correspondencia con las encañadas oficiales (Galápagos, Divino Niño) | Alta; Alvear, Playa Mann y La Planada: media; resto: baja |
| Hipótesis: la Galápagos puede desbordar hacia Divino Niño por un tramo con ≈1,2 m* de resalte en una recta de 466 m | Media-baja (consecuencia alta) |
| El Progreso está en la cuenca alta de Barrio Frío | Media-alta |
| En Puerto Baquerizo no hay vasos de almacenamiento relevantes: el problema es el paso del agua | Media |
| Encharcamiento por depresiones en El Progreso | Media-baja |
| Ranking de puntos | Media-baja (pesos convencionales) |
| La quebrada del campus puede entrar en él por la Vía Universidad | Baja-media: plausible, no demostrada |
| Sesgo del DSM de +1,5 m en Puerto Baquerizo | Media |
| Caudales pico | Baja (solo orden de magnitud) |
