[[SALTO]]

# 2. Qué pasó: cronología del evento y factores de alerta

En esta sección se reconstruye el evento del 30–31 de octubre de 2026 en Santa Cruz a partir de tres tipos de información que no deben mezclarse:
- **[M] medido**: los pluviómetros de la red IERSE-WSN;
- **[E] estimado**: los modelos meteorológicos e hidrológicos;
- **[R] reportado**: los informes oficiales y la prensa.

Todas las horas están en **hora de Galápagos (UTC−6)**. Muchas fuentes nacionales (SNGR, INAMHI y prensa continental) no indican el huso. En esos casos se asume la hora continental (UTC−5), se resta una hora y se marca la cifra como incierta. La cronología completa, con 69 entradas, sus fuentes y su nivel de confianza, está en `datos/linea_tiempo.csv`.

> **Advertencia.** La cronología es **preliminar**. No se encontraron las horas de varios hechos clave: el desbordamiento de cada cañada, el fallecimiento, las primeras evacuaciones ni la sesión del COE cantonal. Las horas de la lluvia sí están medidas, pero solo en dos estaciones y solo hasta las 21:25 del 30 de octubre.

## 2.1 Antes: un contexto de alerta prolongado y genérico

- **Alerta naranja desde el 20 de julio.** La Resolución SNGR-193-2026 elevó la alerta por El Niño a **naranja** en Puerto Ayora, Bellavista y Santa Rosa, entre otras parroquias del país. Su art. 5 ordena a los GAD preparar protocolos de evacuación preventiva en sectores expuestos a inundaciones [R].
- **El Niño declarado el 28 de agosto.** El Comité Nacional ERFEN declaró oficialmente el evento El Niño (informe 007-2026). Al día siguiente, la SNGR declaró la **alerta roja en todo el territorio nacional** (Resolución SNGR-238-2026) [R].
- **COE provincial activo desde el 24 de junio** (SitRep 67) [R].
- **Pronóstico de corto plazo.** La advertencia n.º 84 del INAMHI estaba vigente desde el mediodía del 29 de octubre hasta la noche del 1 de noviembre. Para la región insular preveía **«eventos leves en el archipiélago y de puntual alta intensidad en Isla Isabela»**. Santa Cruz no aparecía como zona de mayor intensidad [R].

Durante tres meses hubo, por tanto, una alerta oficial de nivel alto (naranja y luego roja). Pero esa alerta se refería a un fenómeno climático de escala nacional, no a una tormenta concreta. **El único pronóstico específico para esos días no anticipaba lluvia fuerte en Santa Cruz.**

## 2.2 Durante: la tarde y la noche del 30 de octubre

Tabla: Lluvia horaria medida [M] (mm; red IERSE-WSN). Las horas indican el inicio del intervalo. Los totales son mínimos: las estaciones dejaron de transmitir a las 21:22–21:25.

| Hora (UTC−6) | Los Guayabillos (≈178 m*) | Santa Rosa (≈416 m*) | Cerro Crocker (≈861 m*) | Militar, Baltra (≈14 m*) |
|---|---|---|---|---|
| 13–14 h | 1,8 | 2,2 | 0,2 | 0,0 |
| 14–15 h | 1,2 | 16,4 | 0,0 | 0,8 |
| **15–16 h** | 7,8 | **43,2** | 0,8 | 0,0 |
| 16–17 h | 5,2 | 8,8 | 0,4 | 0,0 |
| 17–18 h | 1,0 | 2,4 | 0,2 | 0,0 |
| **18–19 h** | **35,0** | 8,8 | 0,0 | 0,0 |
| 19–20 h | 21,2 | **43,0** | 0,6 | 0,4 |
| **20–21 h** | **61,0** | **66,4** | 0,2 | 0,2 |
| 21–21:25 h | 25,6 | 21,6 | 0,2 | 0,0 |
| **Total del 30-oct** | **≥ 178,8** | **≥ 237,6** | 5,0 | 2,0 |

\* Cotas del modelo de superficie Copernicus GLO-30 (±2–4 m; sesgo de unos −2 m frente al IGM).

**Primer pulso (14:00–16:30) [M].** Llovió con fuerza sobre todo en Santa Rosa, al oeste: 43 mm entre las 15 y las 16 h. En Los Guayabillos, en la parte media, la lluvia fue moderada (8 mm). No se encontraron reportes de afectación asociados a este pulso.

**Pausa (16:30–18:00) [M].** Entre los dos pulsos casi no llovió. Con 60 mm ya caídos en Santa Rosa, el suelo de la parte media-alta estaba húmedo antes del segundo pulso.

**Segundo pulso (18:00–21:25+) [M].**
- En Los Guayabillos llovieron 35 mm entre las 18 y las 19 h, y **61 mm entre las 20 y las 21 h**. El máximo en una hora móvil fue de **63,8 mm, en los 60 minutos hasta las 20:56**.
- En Santa Rosa, el máximo en una hora móvil fue de **73,0 mm, hasta las 21:12**.
- En la cumbre (Cerro Crocker) y en Baltra llovió menos de 1 mm por hora.

La tormenta fue **convectiva y se concentró en cotas medias (≈150–450 m)**. Es la franja de Bellavista, El Aguacatal, Los Guayabillos y Santa Rosa, que en la cuenca de La Cascada coincide con la parte media. Hay que verificar si la lectura casi nula de Cerro Crocker es real o un fallo del sensor.

**21:22–21:25: las dos estaciones que medían la tormenta dejan de transmitir a la vez [M].** Volvieron simultáneamente entre las 18:42 y las 18:45 del 31 de octubre, unas 21 horas después. Es compatible con un corte eléctrico o de comunicaciones común, pero no está verificado. ELECGALÁPAGOS informó del alimentador 203, que abastece la zona rural (Bellavista, Santa Rosa, Aguacatal), fuera de servicio, y de 3 689 usuarios afectados. No se conoce la hora del corte [R]. Por tanto, **no se midió nada de la lluvia posterior a las 21:25**: ni su final ni una posible continuación en la madrugada.

**Impactos reportados en la tarde y la noche del 30 [R]** (SitRep 01 y SitRep 67 de la SNGR; prensa):
- desbordamiento de las cañadas El Aguacatal, Guayabillos y El Occidente (Bellavista), y Parque Artesanal y El Bosque (Puerto Ayora);
- **una persona fallecida por el desbordamiento de la cañada El Aguacatal**, en Bellavista. La hora no consta. Según la ubicación de los registros SNGR de febrero de 2024, esa cañada pertenece a la cuenca que drena hacia La Cascada (por verificar);
- en Puerto Ayora, vías anegadas «por las precipitaciones registradas durante las últimas dos horas»;
- inundación en La Cascada, con daños en la UPC y en el edificio de la DINAF. Un testigo habló de agua «hasta dos metros». La Dirección del Parque Nacional usó tres botes zodiac en el barrio;
- el Centro de Salud Santa Cruz quedó «incomunicado e inaccesible» por la inundación de sus instalaciones y accesos;
- según la prensa, inundaciones también en Santa Rosa, Miramar (donde colapsó una vivienda), La Unión, Divino Niño y el sector Tomás de Berlanga, e interrupción de la vía entre el Parque Artesanal y Bellavista.

**Respuesta [R].**
- El COE cantonal declaró la emergencia el 30 de octubre, según el SitRep 67; algunos medios la sitúan el 31. No se encontró la hora.
- Las evacuaciones ocurrieron «durante la noche y madrugada», priorizando a los grupos vulnerables.
- Se habilitaron dos refugios: el Coliseo Cerrado de Deportes y la Casa de los Mormones.

**Hidrología de La Cascada [E].** Modelo agregado alimentado con la lluvia medida (estudio de La Cascada, sección 4.7):
- el caudal en la entrada del barrio supera 1 m³/s desde las **14:20–17:00**;
- **el vaso se llena hasta su rebose entre las 16:50 y las 18:10** en el escenario central (15:40–19:45 en todos). Para entonces, las viviendas más bajas ya tendrían agua;
- **el pico de la crecida llega entre las 21:40 y las 22:50**, con 155–600 m³/s. La lámina máxima se alcanza entre las 21:35 y las 23:10;
- el agua vuelve a la cota de rebose entre las 00:00 y las 08:00 del 31 de octubre.

Son estimaciones sin calibrar con caudales, pero su cronología coincide con la de la SNGR.

**Desfase de los modelos.** El modelo ECMWF de 9 km situaba el máximo a las 05–06 h del 31 de octubre, unas 9 h después de lo medido, y con menos lluvia en la parte media [E]. La prensa habló de lluvia «entre las 22:00 y las 06:00» sin indicar el huso [R]. **Lo medido coincide con la SNGR: «tarde y noche del 30».**

## 2.3 Después: 31 de octubre a 2 de noviembre

- **31-oct, mañana.** El aeropuerto de Baltra suspendió los vuelos comerciales unas cuatro horas (de 08:00 a 12:00 según la prensa; huso incierto). Se reanudaron hacia las 15:00. Se anunció un paso controlado por la vía a Itabaca desde las 15:00 [R].
- **31-oct, mañana, en San Cristóbal.** Se desbordaron las cañadas Barrio Frío y Divino Niño en Puerto Baquerizo Moreno (véase el estudio de San Cristóbal) [R].
- **31-oct, ≈14:00.** El INAMHI emitió la **alerta roja de corto plazo n.º 59**, unas 17 h después del máximo de lluvia medido [R].
- **31-oct, corte de las 15:30 del SitRep 01** (huso incierto). Recoge:
  - 1 fallecido;
  - 43 familias y 175 personas afectadas;
  - 165 personas en refugios;
  - **unas 700 personas con familias acogientes**.

  La prensa habló además de **dos personas desaparecidas en el sector Divino Niño** (balance preliminar del ECU 911 y el COE). No se encontró confirmación ni desmentido posterior [R].
- **1-nov, corte de las 15:00 del SitRep 67.** Da 3 120 personas y 780 familias afectadas en la provincia, pero el texto dice «60 familias»: es una incoherencia interna. El Centro de Salud seguía inoperativo y el refugio del Coliseo acogía a 76 personas. La advertencia n.º 85 del INAMHI, del 1 al 4 de noviembre, preveía eventos muy fuertes «de manera ocasional en las islas» [R].

## 2.4 Factores de alerta

Tabla: Señales de alerta disponibles, quién las tenía y qué margen daban.

| Señal | Disponible desde (UTC−6) | Quién la tenía | ¿Se tradujo en aviso o acción local? | Margen respecto al máximo de lluvia (30-oct, 20–21 h) |
|---|---|---|---|---|
| Alerta naranja por El Niño (SNGR-193-2026) | 20-jul | SNGR, GAD, COE; pública | Activación del COE provincial (desde el 24-jun). **No se encontró** un protocolo de evacuación específico para La Cascada, Bellavista o El Aguacatal (por verificar) | ≈3 meses; genérica, sin día ni hora |
| El Niño declarado (ERFEN) y alerta roja nacional (SNGR-238-2026) | 28–29-ago | CN-ERFEN, SNGR, GAD; pública | Igual que la anterior | ≈2 meses; genérica |
| Advertencia n.º 84 del INAMHI | ≈29-oct, 12:00 | INAMHI, SNGR, medios | Para Galápagos anunciaba «eventos leves»: **no era una señal de peligro para Santa Cruz** | ≈32 h, pero con un contenido que no anticipaba el evento |
| Lluvia medida en tiempo casi real (IERSE-WSN) | Continua; cada ≈5 min | Universidad del Azuay; visor público (socios: FCD, DPNG, MAG) | **No consta** que ninguna institución la vigilara ni que estuviera ligada a un protocolo | Véase la fila siguiente |
| ≥ 30 mm en 1 h, en Santa Rosa (primer pulso) | 15:17 | Visible en el visor; nadie la tenía asignada | No consta | ≈5 h; Santa Rosa no drena hacia La Cascada |
| ≥ 30 mm en 1 h, en Los Guayabillos | **18:51** | Ídem | No consta | **≈1–2 h** hasta el máximo de lluvia; para La Cascada, **≈2,8–4 h** hasta el pico modelado (21:40–22:50), pero **después** del llenado del vaso (16:50–18:10) [E] |
| ≥ 50 mm en 3 h, en Los Guayabillos | 19:36 | Ídem | No consta | ≈0,5–1,5 h; para La Cascada, ≈2–3 h hasta el pico modelado [E] |
| Silencio de las dos estaciones | 21:22–21:25 | Ídem | No consta | Después del máximo; habría sido una señal de agravamiento |
| Reportes ciudadanos y llamadas al ECU 911 | Desconocido | ECU 911, bomberos, COE | Sí (respuesta), pero sin horas publicadas | **Dato faltante** |
| Alerta roja de corto plazo n.º 59 del INAMHI | ≈31-oct, 14:00 | INAMHI, SNGR | Posterior al evento | Negativo (≈17 h después) |

Los umbrales de 30 mm/h y 50 mm/3 h son **ilustrativos**: en Galápagos no existen umbrales oficiales. Los márgenes para La Cascada se calculan respecto al hidrograma modelado con la lluvia medida, sin calibrar. El análisis de umbrales y la propuesta de protocolo están en la sección 7.3.

## 2.5 Lecciones (preliminares)

1. **La alerta existía, pero era genérica.** Durante tres meses estuvo vigente una alerta de nivel alto. No se encontró evidencia de que se tradujera en avisos por sector con criterios de activación medibles. Esto no implica que no hubiera planes: no se han podido consultar los registros del COE cantonal ni de la UGR municipal.
2. **El pronóstico no anticipó la tormenta.** El INAMHI preveía «eventos leves», y el modelo ECMWF desplazaba el máximo 9 h y subestimaba la lluvia de la parte media. **Con la información de pronóstico disponible, no había una señal clara de evento extremo en Santa Cruz.**
3. **La medición sí la anticipaba, con poco margen.** La red IERSE-WSN mostró en tiempo casi real que en la parte media se superaban intensidades de 30 mm/h **1–2 h antes del máximo de lluvia**. Ese margen es corto para la parte alta (El Aguacatal, Bellavista), cuyos cauces responden en minutos. Para La Cascada, el modelo indica ≈3–4 h hasta el pico, tiempo suficiente para evacuar ante la crecida mayor. Sin embargo, **el vaso ya se habría llenado antes de que se superara cualquier umbral**: las viviendas más bajas se inundan con lluvias moderadas, y para ellas un SAT no basta.
4. **El sistema de medición falló cuando más se necesitaba.** Las dos estaciones relevantes dejaron de transmitir en el momento más intenso y estuvieron unas 21 h sin datos. Es una lección de resiliencia: un sistema de alerta temprana (SAT) necesita energía de respaldo, comunicaciones redundantes y una regla para el silencio de las estaciones (sección 7.3).
5. **La evacuación fue sobre todo espontánea.** Unas 700 personas se fueron con familias acogientes, frente a 165 en refugios. Al menos uno de los refugios improvisados, el Coliseo, está en una zona baja según el DSM.
6. **Lo que no se sabe** y conviene reconstruir con entrevistas y registros:
   - la hora del desbordamiento de cada cañada y la del fallecimiento;
   - cuándo llegó el agua a La Cascada y hasta qué altura;
   - si hubo avisos informales (redes sociales, llamadas) y cuándo;
   - la hora de la sesión del COE cantonal y de la declaratoria;
   - si la lluvia continuó tras las 21:25;
   - la situación de las dos personas reportadas como desaparecidas.
