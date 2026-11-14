# Nivel preliminar de inundación (v0.3, 14-nov-2026)

> La versión vigente es la **v0.3** (sección final). Lo que sigue se conserva como historia de la v0.1 y la v0.2.

Regla propuesta por la sesión de coordinación a partir del informe técnico de La Cascada (`geodatos/estudios/la-cascada`, secciones de hidrología y `resumen.json`) y del registro de IERSE de abril a noviembre de 2026. **Pendiente de revisión por quien hizo el informe.** El JSON que usa el recolector es `recolector/umbrales_inundacion.json` y el cálculo está en `recolector/inundacion.py`.

## Por qué la intensidad y no el total diario
- El informe usa SCS-CN: 68 en condición normal, 47 en seca y 83 en húmeda, con un valor central de 76. La cuenca mide 42,33 km² y el vaso 50 000–62 000 m³, es decir, solo 1,2–1,5 mm de escorrentía sobre la cuenca. Según eso, el vaso se llenaría con 25–50 mm de lluvia si no hubiera pérdidas en el cauce.
- El registro no lo confirma. El 3-oct, Los Guayabillos midió 68 mm en el día (máximo de 12,6 mm/h). El 23-oct, Santa Rosa midió 97 mm (máximo de 28 mm/h). No consta inundación ninguno de esos días; falta confirmarlo.
- El 30-oct, en cambio, hubo 61–66 mm/h, 117–131 mm en 3 h y 179–238 mm en el día. Eso apunta a pérdidas grandes en el basalto: lo que manda es la intensidad en 1–3 h.
- La marea no influye en La Cascada: el rebose está a unos 12–13 m de altura y a 0,9–1,3 km del mar. Solo importa para la costa baja de 0–3 m.

## Regla
- Lluvia de referencia por zona: `R_v = máx(peso × lluvia en la ventana v)` sobre las estaciones válidas, con v ∈ {1 h, 3 h, 24 h}.
  - La Cascada: Los Guayabillos ×1, Santa Rosa ×0,75 (cociente del 30-oct, 179/238) e INAMHI Puerto Ayora ×1.
- Exclusiones:
  - estaciones con cobertura menor del 80 %;
  - estaciones que marcan 0 mm en 3 h mientras otra válida marca 10 mm o más;
  - Cerro Crocker queda fuera de todas las zonas.
  - Si no queda ninguna estación válida, el nivel es «sin datos», nunca «bajo».
- Umbrales (basta superar uno):

| Nivel | 1 h | 3 h | 24 h | Probabilidad orientativa |
|---|---|---|---|---|
| Muy alto | 45 | 90 | 150 | más del 60 % |
| Alto | 30 | 60 | 100 | 25–60 % |
| Medio | 15 | 30 | 50 | 5–25 % |
| Bajo | — | — | — | menos del 5 % |

  - **Medio:** según el SCS, el vaso podría empezar a llenarse.
  - **Alto:** supera todo lo registrado sin inundación conocida.
  - **Muy alto:** se acerca al 30-oct (unos 2/3 de lo medido en 1 y 3 h).
- Humedad antecedente: P5d es la lluvia de los 5 días anteriores a las últimas 24 h. Con P5d < 36 mm, umbrales ×1,2; con P5d > 53 mm, ×0,8. Son los cortes del SCS.
- Persistencia: el nivel se mantiene 3 h, porque el pico llega 1,5–3,5 h después de la lluvia (tc de Kirpich–Témez).
- Otras zonas, todas «sin calibrar»:
  - Parte alta de Santa Cruz: estaciones locales sin el factor 0,75.
  - San Cristóbal: máximo de las estaciones del GSC y el INAMHI.
  - Isabela: «sin datos».
- La probabilidad es juicio experto basado en un solo evento calibrado; no es estadística. Se muestra como rango orientativo.

## Prueba retrospectiva (La Cascada)
- 30-oct 21:20, hora de Galápagos: **muy alto** (R1h 58, R3h 131, R24h 178).
- 3-oct: bajo.
- 23-oct: medio.

## Advertencia que se muestra
«Nivel preliminar y no oficial, calculado por SOS Galápagos con la lluvia medida y un estudio técnico preliminar que tiene un solo evento de referencia (30-oct-2026). No es una alerta oficial: siga siempre las indicaciones del COE, la SNGR y el ECU 911.»

## Para mejorarlo
- Confirmar si hubo inundación el 3-oct, el 23-oct y el 1/2-nov, y ajustar con eso el umbral de «alto».
- Usar marcas de agua.
- Construir curvas IDF con la serie diaria del GSC desde 2015 y la de la FCD desde 1965.
- Revisar el pluviómetro de Los Guayabillos: marca 0 desde el 31-oct.

## Cambios de la v0.2

Revisión del especialista en gestión de riesgos del comité de estudios. Simuló la regla con la serie de IERSE de abril a noviembre de 2026.

- **Silencio en alerta = alarma.** Si las estaciones de una zona dejan de transmitir y el nivel era «alto» o más en las últimas 8 h, el nivel pasa a «muy alto».
  - Solo se aplica si el recolector consultó la fuente con éxito, es decir, si fue la estación la que calló.
  - Si falla nuestra recolección, se muestra «sin datos» con el último nivel conocido.
- **Cobertura solo en las ventanas cortas.** El 80 % se exige en 1 h y 3 h. Así un corte no deja ciega la regla durante un día entero en la ventana de 24 h.
- **Persistencia de 8 h** en lugar de 3. El vaso se vació entre las 00:00 y las 08:00 del 31-oct.
- **Sin ajuste en seco.** El único evento calibrado ocurrió con el suelo seco: subir los umbrales retrasó la alerta de las 18:51 a las 19:05. Solo se mantiene la rebaja del 20 % con suelo húmedo.
- **Probabilidad cualitativa** (poco probable, posible, probable, muy probable), en lugar de porcentajes sin base estadística.

Simulación del 30-oct:
- medio a las 15:15 (por Santa Rosa);
- alto a las 19:05, con 2,6–3,8 h de margen hasta el pico modelado (21:40–22:50);
- muy alto a las 20:55.
El vaso se llenó entre las 16:50 y las 18:10, y solo lo precedió «medio».

«Alto» de la regla (30/60/100 mm) coincide con la «alerta» del estudio de Santa Cruz (sección 11): 30 mm en 1 h y 50 mm en 3 h.

**Pendientes:**
- Santa Rosa está a 6,6 km de la cuenca y Los Guayabillos, a 0,4 km fuera de ella. Hay que asignar estaciones por sector.
- Confirmar con el GAD o el COE si hubo anegamientos el 3-oct, el 23-oct y el 1–2-nov.

- 2-nov-2026: se añadió a La Cascada la estación particular WeatherLink de Erna en Puerto Ayora (Davis Vantage Vue), con peso 1, como segundo pluviómetro costero junto a INAMHI M0191.
  - Está en la costa, aguas abajo de la cuenca, y **no representa la lluvia de la cuenca alta**. Como R es un máximo, no puede bajar el nivel, pero un chubasco costero sí puede subirlo.
  - El pluviómetro es un balancín pequeño de 0,01" (0,254 mm) y subestima la lluvia intensa.
  - Se descartan los saltos de más de 100 mm/h.
  - Es la estación de Erna, en Puerto Ayora (−0,7534 / −90,3120); se publica con su nombre y su ubicación exacta (autorizado el 2-nov-2026).

## Referencias horarias del modelo 2D (ANUGA / LISFLOOD-ACC, 30-oct, hora de Galápagos)
- Primera llegada de agua (0,1 m) al punto bajo: 15:36. La regla daba «medio» a las 15:15.
- Agua en el centro del barrio: 20:37. «Alto» se activó a las 19:05, unas 1,5 h antes.
- Máximo: 22:08. «Muy alto» se activó a las 20:55.

## San Cristóbal: umbrales propios (12-nov-2026)

Hasta el 12-nov, San Cristóbal usaba los umbrales de La Cascada y estaba «sin calibrar». Ese día marcó «alto» a las 08:00 y «muy alto» a las 11:00, pero lo que pasó en la isla fue de nivel medio. Se calibró con los dos eventos que tienen impactos conocidos:

| Evento | Qué pasó | R1h | R3h | R24h | Datos |
|---|---|---|---|---|---|
| 31-oct-2026 | Desborde de las cañadas Barrio Frío y Divino Niño en la mañana (SNGR, ECU 911). El 1-nov, la SNGR no registró vías inundadas ni viviendas afectadas | 39,1 (El Junco, Cerro Alto) | 79,5 (Cerro Alto) | 204,2 (El Junco) | INAMHI horario de las estaciones USFQ (M5300–M5303); M0221 sin datos |
| 12-nov-2026 | Unos 15 cm de agua frente a la USFQ y agua en algunas casas cerca del malecón (reporte de la coordinación) | 44,0 (Puerto Baquerizo, M0221) | 68,7 (M0221) | 144,5 (El Junco) | GSC-USFQ e INAMHI M0221, cada 5 min |

| Nivel | 1 h | 3 h | 24 h |
|---|---|---|---|
| Muy alto | 80 | 140 | 330 |
| Alto | 55 | 95 | 230 |
| Medio | 20 | 35 | 80 |

- **Alto** queda por encima de los dos eventos, con márgenes del 25 % (1 h), 19 % (3 h) y 13 % (24 h).
- **Medio:** con estos umbrales, el 12-nov habría marcado «medio» desde las 03:00, unas 7 h antes del pico (10:00–11:00).
- **Muy alto** = 1,5 × «alto», la misma proporción que en La Cascada. No hay un evento grave de referencia en San Cristóbal.
- **Sin rebaja por suelo húmedo** (`ajuste_humedad: false`): los dos eventos ya ocurrieron con el suelo húmedo, así que rebajar otra vez los umbrales contaría ese efecto dos veces.
- Estaciones con peso 1: El Junco, Cerro Alto, El Mirador, Merceditas e INAMHI M0221. R sigue siendo el máximo entre ellas, así que El Junco (548 m) suele mandar en 24 h, aunque los impactos se vieron en la costa de Puerto Baquerizo.
- Los umbrales y los datos de cada evento están en `umbrales_inundacion.json` (zona `san-cristobal`, claves `umbrales` y `calibracion`).

**Pendiente:** con solo dos eventos de nivel medio, no se sabe dónde empieza el nivel alto. Conviene registrar cada lluvia fuerte con lo que pasó (calles, cañadas, viviendas, barrios) y reajustar. También falta asignar las estaciones por cuenca (la quebrada de Playa Mann y el campus USFQ, Barrio Frío, Divino Niño).

## Correcciones del 12-nov-2026 (revisión del sistema)

- **Persistencia cada 5 minutos.** Antes, el nivel solo se guardaba a la hora en punto: un «alto» que ocurría entre dos horas desaparecía en la siguiente corrida (15 min después) en vez de mantenerse 8 h, y el silencio en alerta podía no activarse. Ahora el nivel instantáneo se evalúa cada 5 min de las últimas 80 h; el historial de 72 h muestra el nivel más alto de cada hora.
- **Ventanas hasta el último dato de cada estación.** Antes, la cobertura del 80 % se contaba hasta la hora actual: una estación con 15 min o más de retraso (el INAMHI llega con 10–17 min) quedaba fuera aunque estuviera midiendo lluvia fuerte. Ahora las ventanas de 1, 3 y 24 h terminan en su último dato, y la estación se usa si ese dato tiene 30 min o menos (`frescura_max_min`).
- **Silencio solo si de verdad callan.** Antes, si todas las estaciones llegaban con retraso, la regla podía publicar «muy alto» por un silencio que era solo latencia. Ahora la zona solo está «callada» si ninguna estación mandó datos en los últimos 60 min (`silencio_min`).

## v0.3 (14-nov-2026): estaciones nuevas de Santa Cruz y dos crecidas sin inundación

**Por qué.** La regla seguía usando solo cuatro estaciones en La Cascada (Los Guayabillos, Santa Rosa, INAMHI M0191 y Erna). Con Los Guayabillos dañado y Santa Rosa con cortes, el 14-nov a las 13:35 el nivel dependía de una sola estación (Erna). Las estaciones que entraron al panel el 6 y el 12-nov (Miconia, Evolución, las dos de la ESPOL, Punta Estrada y Casa Marina) se mostraban, pero no entraban en el nivel.

Además hay dos eventos nuevos con resultado conocido (reporte de la coordinación): el **11-nov** y el **14-nov** la quebrada de La Cascada creció y **no hubo inundación**.

### Qué se midió (máximos del día; hora de Galápagos)

| Evento | Miconia (422 m) | Santa Rosa (416 m) | Puerto Ayora (INAMHI, Evolución) | Qué pasó |
|---|---|---|---|---|
| 30-oct | 82 mm/1 h · 172 mm/3 h · 336 mm/24 h | 73 · 139 · 240 | 36 · 54 · 118 (y otros 50 · 109 en 1 y 3 h a la 01:00 del 31) | inundación |
| 11-nov | 28 · 58 · 66 | 35 · 77 · 88 | 2 · 5 · 6 | creció, sin inundación |
| 14-nov (hasta las 13:35) | 52 · 100 · 221 | 27 · 54 · 128 | 19 · 42 · 92 | creció, sin inundación |

- El 14-nov llovió casi tanto en 24 h como el 30-oct a la hora de la inundación, y sobre suelo muy húmedo (Miconia: unos 200 mm en los 5 días previos). **Lo que separa al 30-oct es la intensidad:** las tres estaciones de la parte alta llegaron a 64–82 mm en 1 h y 138–172 mm en 3 h (máximos entre las 20:55 y las 21:35).
- El primer pulso del 30-oct (15:00–17:00: Santa Rosa 43 mm/1 h y 69 mm/3 h) se parece a las dos crecidas sin inundación. Con la lluvia sola no se puede distinguir una crecida de la primera fase de una inundación: por eso «alto» sigue saltando ahí.

### Cambios

1. **Estaciones de La Cascada:** se añaden Miconia ×0,55, Evolución ×1 y EPMAPASC–ESPOL ×1.
   - Miconia está a 3,4 km de la cuenca y llueve más que en ella: Los Guayabillos midió 0,53 de Miconia el 30-oct (179/336) y 0,50 en los 67 días comunes. Es el mismo criterio que el ×0,75 de Santa Rosa.
   - Evolución (centro de Puerto Ayora) registra cada 5 min sin cortes desde ago-2024.
   - EPMAPASC–ESPOL es la más cercana al barrio (0,8 km de la cuenca), pero se apaga unas 5 h cada noche y al volver entrega de golpe la lluvia acumulada (113 mm en un registro el 31-oct).
2. **Parte alta de Santa Cruz:** se añaden Miconia ×0,7 y El Manzanillo–ESPOL ×1. Miconia mide un 40 % más que Santa Rosa (cociente 0,71 en 70 días comunes); con ×1 la zona habría marcado «muy alto» el 14-nov a las 06:00; con ×0,7 marcó «alto», igual que la v0.2. La zona sigue **sin calibrar con impactos**.
3. **No entran en el nivel:**
   - **Punta Estrada (Tempest):** su sensor háptico midió 0,28–0,35 de lo que midieron Evolución y el INAMHI en los cuatro días de lluvia fuerte (35 frente a 110 mm el 30-oct; 23 frente a 82 mm el 14-nov). Como R es un máximo, no aporta; y si quedara como única estación válida, daría un «bajo» falso.
   - **Casa Marina (Weather Underground):** el acumulado que publica no se reinicia a medianoche; baja por tramos, como una ventana móvil. El recolector guardaba todo el acumulado como lluvia de 5 min en la primera lectura tras las 06:00 UTC (33,5 mm el 13-nov sin lluvia). Se corrigió la lectura (`fuente_wunderground`), pero la serie no sirve para fechar bien la lluvia.
   - **Cerro Crocker** sigue fuera: midió 5 mm el 30-oct y 4 mm el 14-nov.
4. **Umbral de 24 h:** «alto» pasa de 100 a 150 mm y «muy alto» de 150 a 225 mm (Santa Cruz; San Cristóbal conserva los suyos).
   - Con 100 mm, la regla marcó «alto» el 4-oct, el 1-nov y (con Miconia) el 14-nov, sin inundación conocida.
   - El 30-oct, «alto» saltó a las 15:40 por la lluvia de 1 h y «muy alto» a las 20:35 por la de 1–3 h. El umbral de 24 h no adelantó nada.
   - El estudio de tormentas sintéticas propone 190 mm; 150 queda por debajo.
5. **Sin rebaja por suelo húmedo en Santa Cruz** (`ajuste_humedad: false`, como en San Cristóbal). En el registro, la rebaja solo subió el nivel en días sin inundación conocida (23-oct, 2-nov, 14-nov). Con Miconia en la zona, el suelo estaría «húmedo» casi toda la temporada y los umbrales quedarían rebajados de forma permanente. La lluvia de los 5 días previos se sigue mostrando.
6. **Los umbrales de 1 h y 3 h no cambian** (15/30, 30/60 y 45/90 mm). Las dos crecidas sin inundación quedaron justo debajo de «alto» (26–28 mm en 1 h y 55–57 mm en 3 h).
7. **Cobertura parcial** (`cobertura_parcial`: 0,5). Una estación con entre el 50 y el 80 % de sus registros ya no se descarta: lo que midió es un mínimo y puede subir R. El 14-nov, el INAMHI perdió 3 de 12 registros en la hora y quedó fuera con 35 mm en 3 h. Si solo hay estaciones parciales y no marcan lluvia fuerte, el nivel sigue siendo «sin datos».
8. **Lluvia de un corte** (`hueco_max_min`: 15). En Ambient, WeatherLink y Weather Underground la lluvia sale por diferencia de un acumulado. El registro que sigue a un corte de más de 15 min cuenta para 24 h y para la humedad, pero no para 1 h ni 3 h. Si el corte pasa de 12 h, no cuenta.

### Prueba retrospectiva (23-ago a 14-nov-2026, nivel instantáneo cada 5 min)

| | v0.2 | v0.3 |
|---|---|---|
| 30-oct | medio 15:10 · alto 15:40 · muy alto 20:35 | igual |
| 30-oct con la red de hoy (sin Los Guayabillos) | igual | igual |
| 4-oct y 1-nov | alto (por las 24 h) | medio |
| 11-nov | medio | medio (R: 26 / 57 / 66 mm) |
| 14-nov | medio; a las 13:35 solo con Erna | medio (R: 28 / 55 / 121 mm), con Miconia, INAMHI y Erna |
| 14-nov si solo se hubieran añadido las estaciones | — | muy alto a las 12:55 (falsa alarma) |
| Tiempo «sin datos» | 1,1 % (3,2 % sin Los Guayabillos) | 0 % |
| Parte alta, 11 y 14-nov | alto | alto |

### Lo que sigue pendiente

- **Las dos crecidas quedaron a menos del 10 % de «alto».** El margen es mínimo: hace falta anotar de cada crecida la hora, hasta dónde llegó el agua y si el vaso rebosó.
- La parte alta sigue sin un solo impacto conocido para calibrar.
- Los Guayabillos, la mejor estación de la cuenca, sigue dañada. Casi todas las particulares de Puerto Ayora dependen de la luz y el internet del pueblo: el 14-nov a las 12:50 dejaron de llegar a la vez Evolución, EPMAPASC, Casa Marina, Punta Estrada y Santa Rosa. Miconia y el INAMHI siguieron.
- El pluviómetro en la cuenca media (issue #19) sigue siendo la mejora más útil.
