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

**El Progreso.** Tiene 35 ha, ≈210 edificios y ≈280 personas, y recibe 1,1 km². Su llegada principal (PRO-L01) es la quebrada del IGM que baja de la parte alta, **cuyo trazado termina en el borde noreste del poblado**. Según el D8, el agua sale de El Progreso hacia el oeste y entra en la cuenca de El Manzanillo–Barrio Frío. **El Progreso está, por tanto, aguas arriba de Puerto Baquerizo Moreno.**

Tabla: Llegadas principales a las zonas pobladas (D8). Q100: tormenta tipo II de 100 mm; valor central con CN 70 y tc de Témez; entre paréntesis, de CN 60 con Témez a CN 80 con Kirpich. Los nombres locales son la hipótesis de la sección 7.

| Id | Nombre local probable | Área (km²) | Cota máx.* (m) | Pendiente media | Cauce: L (km) / pendiente | tc (h) | Q100 (m³/s) |
|---|---|---|---|---|---|---|---|
| PBM-L01 | El Manzanillo → Barrio Frío | 5,4 | 526 | 10,4 % | 8,9 / 4,8 % | 1,0–4,2 | 11 (5–35) |
| PBM-L02 | Afluente sureste (La Planada) | 1,8 | 294 | 8,9 % | 3,7 / 5,3 % | 0,4–2,3 | 6 (3–19) |
| PBM-L03 | Divino Niño | 1,0 | 139 | 6,4 % | 2,2 / 4,6 % | 0,2–1,7 | 4 (2–13) |
| PBM-L04 | Escuela Alvear | 0,45 | 122 | 8,6 % | 1,7 / 5,6 % | 0,1–1,2 | 2 (1–7) |
| PBM-L05 | Quebrada del campus (§ 4.4) | 0,31 | 78 | 8,1 % | 1,3 / 4,6 % | 0,1–1,0 | 2 (1–5) |
| PRO-L01 | Quebrada IGM de El Progreso | 1,0 | 526 | 14,0 % | 3,2 / 6,1 % | 0,3–1,6 | 4 (2–12) |

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
| PBM-S01 | Barrio Frío | Malecón (−0,9026; −89,6132) | 10,6 | Sí (IGM; puentes) | 25 | 19 (9–58) |
| PBM-S02 | Divino Niño | Sur de Playa Mann (−0,8994; −89,6097) | 1,5 | No | 32 | 6 (3–18) |
| PBM-S03 | Escuela Alvear | Playa Mann (−0,8980; −89,6097) | 1,0 | No | 8 | 4 (2–14) |
| PBM-S04 | Cauce pequeño | Norte del campus (−0,8945; −89,6102) | 0,1 | No | 6 | 0,9 (0,4–2) |

**Ranking.** Cada punto suma de 0 a 9 puntos (`datos/puntos_inundacion.geojson`):
- **A. Área aportante:** 0 (< 0,1 km²), 1 (0,1–0,5), 2 (0,5–2) o 3 (≥ 2).
- **E. Edificios:** 0 (< 5), 1 (5–24), 2 (25–99) o 3 (≥ 100). Se cuentan en la franja de 20 m del tramo propio de cada llegada (hasta que se une a una mayor), a ≤ 45 m del tramo final de cada salida o dentro del vaso.
- **C. Confinamiento:** 1 si no hay cauce cartografiado o si el vaso es robusto.
- **H. Antecedente [R]:** 1 si hay un registro de la SNGR a ≤ 250 m. Se excluyen 6 registros con coordenadas genéricas.
- **L. CGREG:** 1 si toca la capa de flujos de lodo por El Niño o la franja de quebradas.

Tabla: Los diez primeros puntos del ranking.

| # | Id | Tipo | Lugar | Área (km²) | Edificios | Puntos (A-E-C-H-L) |
|---|---|---|---|---|---|---|
| 1 | PBM-L01 | Llegada | El Manzanillo, entrada este (−0,9062; −89,5938) | 5,4 | 110 | 8 (3-3-0-1-1) |
| 2 | PBM-S01 | Salida con cauce | Barrio Frío, Malecón | 10,6 | 25 | 7 (3-2-0-1-1) |
| 3 | PBM-S02 | Salida sin cauce | Divino Niño | 1,5 | 32 | 7 (2-2-1-1-1) |
| 4 | PBM-L02 | Llegada | La Planada (−0,9116; −89,5919) | 1,8 | 45 | 6 (2-2-1-1-0) |
| 5 | PBM-L03 | Llegada | Divino Niño (−0,8996; −89,6035) | 1,0 | 66 | 6 (2-2-1-1-0) |
| 6 | V22 | Vaso no robusto | Desembocadura de Barrio Frío | 10,6 | 2 | 5 (3-0-0-1-1) |
| 7 | PBM-S03 | Salida sin cauce | Escuela Alvear, Playa Mann | 1,0 | 8 | 5 (2-1-1-1-0) |
| 8 | V15 | Vaso no robusto | La Planada | 2,0 | 8 | 4 (2-1-0-1-0) |
| 9 | PBM-L04 | Llegada | Escuela Alvear (−0,8975; −89,6048) | 0,45 | 13 | 4 (1-1-1-1-0) |
| 10 | PBM-L05 | Llegada | Quebrada del campus (−0,8961; −89,6070) | 0,31 | 12 | 4 (1-1-1-1-0) |

El primer punto de El Progreso es el vaso V03 (puesto 13). El ranking sirve para **ordenar las visitas de campo**; no mide el riesgo, porque los pesos son convencionales. V22 es, en la práctica, la boca de Barrio Frío (S01).

## 4.4 La quebrada del campus USFQ / Galapagos Science Center

**De dónde viene.** Nace en la ladera al este-noreste del campus, a ≈78 m*, en terreno casi sin edificar. Al llegar a un **rellano a ≈20 m***, entre 160 y 200 m al este del campus, su trazado se vuelve ambiguo:
- **En la rejilla UTM** (este análisis), gira al sur, se une a la encañada de la Escuela Alvear y llega al mar en Playa Mann (−0,8980; −89,6097). Pasa a **157 m** del campus en su punto más cercano.
- **En la rejilla geográfica original** (la de la sección 6), sigue al oeste, **atraviesa el campus** y llega a la costa junto a él (−0,8951; −89,6093).
- **Con 1–3 m de ruido en el DSM**, entre el **12 y el 23 %** de las realizaciones cruzan el campus. En su mayoría entran por la esquina noreste, junto a la Vía Universidad (−0,8950; −89,6083).

El transecto recto del rellano al GSC baja de 19,8 a ≈16 m*, con un resalte de solo 1,6 m, menor que el error del DSM. **Los edificios del campus están 8–13 m* más bajos que el rellano**: nada en el DSM impide que el agua que se salga del cauce ahí (por una obstrucción o siguiendo la calle) baje hacia el campus.

> **Conclusión.** Que la quebrada llegue al campus es **plausible, pero el DSM de 30 m no permite confirmarlo ni descartarlo.** Hay que verificarlo en campo.

Tabla: Cuenca de la quebrada del campus en sus dos puntos de control.

| | Rellano frente al campus | Desembocadura en Playa Mann (con Escuela Alvear) |
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

## 4.6 Incertidumbre

- **DSM:** ±3 m en torno a la ciudad y ±5 m en El Progreso. En tramos con un 1–3 % de pendiente eso equivale al desnivel de 100 m de recorrido, así que las rutas del rellano del campus y de las salidas a Playa Mann son inciertas en decenas a cientos de metros.
- **El DSM no ve** alcantarillas, cauces entubados ni bordillos; en la ciudad el agua sigue las calles.
- **Lluvia:** no hay ninguna medida. Con 100 mm, el caudal pico de la quebrada del campus varía unas 7 veces (2,0–13,7 m³/s) según el CN (60–80) y el método de tc.
- **Campus:** no está cartografiado como polígono. Se aproximó con los edificios universitarios de OSM (0,8 ha).

Tabla: Nivel de confianza de cada conclusión.

| Conclusión | Confianza |
|---|---|
| Área que drena a Puerto Baquerizo (≈11 km²) y peso de El Manzanillo–Barrio Frío | Alta |
| El Progreso está en la cuenca alta de Barrio Frío | Media-alta |
| En Puerto Baquerizo no hay vasos de almacenamiento relevantes: el problema es el paso del agua | Media |
| Encharcamiento por depresiones en El Progreso | Media-baja |
| Ranking de puntos | Media-baja (pesos convencionales) |
| La quebrada del campus puede entrar en él por la Vía Universidad | Baja-media: plausible, no demostrada |
| Sesgo del DSM de +1,5 m en Puerto Baquerizo | Media |
| Caudales pico | Baja (solo orden de magnitud) |
