[[SALTO]]

# 7. Gestión del riesgo de desastres

Esta sección cubre el cantón San Cristóbal: Puerto Baquerizo Moreno, El Progreso y, en lo que toca a la gestión, Floreana. Combina tres tipos de información:
- **[R] reportado**: registro de eventos y SitReps de la SNGR, y el **Plan de Acción SC-4-09-2026 «Fenómeno El Niño – San Cristóbal» de la Unidad de Gestión de Riesgos (UGR) del GAD municipal**, en adelante «el plan de la UGR». Es un documento interno, facilitado por la coordinación de USFQ Galápagos el 2 de noviembre de 2026; aquí se cita, no se reproduce;
- **[E] estimado**: los análisis del estudio. Hidrología en la sección 4, modelo 2D en la 4b, Floreana en la 4c, cruces en la 5, diagnóstico urbano en la 6 y la ubicación de los lugares del plan en la 6b;
- **[M] medido**: no hay lluvia medida del evento en San Cristóbal.

Los datos propios de esta sección están en `datos/riesgo/` y se regeneran con `scripts/grd_riesgo_islas.py`:
- `instalaciones_criticas.csv`;
- `recurrencia_sngr.csv`;
- `capas_cgreg_resumen.csv`.

Las cotas marcadas con * proceden del DSM Copernicus GLO-30. Tienen un error de ±2–4 m y, en Puerto Baquerizo Moreno, un **sesgo local de unos +1,5 m** frente al IGM (sección 4.5). **No deben usarse como umbrales normativos.** La correspondencia entre cauces y encañadas y la validación topográfica son de la sección 4.6. Las cifras de exposición a lo largo de los cauces son las del diagnóstico urbano (sección 6.2).

## 7.1 Caracterización del riesgo

**Amenaza.** La amenaza es la crecida súbita de las **encañadas que bajan del cerro hacia la bahía**, con arrastre de lodo y piedras.
- **Inventario de la UGR:** 15 encañadas principales. Diez están en Puerto Baquerizo Moreno: Galápagos o Barrio Frío, Cerro Quemado o Don García, Divino Niño, Escuela Alejandro Alvear, Playa Mann, Manzanillo–El Manantial, Palmeras–Arrayanes, La Planada, Centro de Gestión de Residuos Sólidos y Parque Artesanal. Las demás están en los recintos de El Progreso, en los viveros del PNG y la Galapaguera, y en Floreana (La Hormiga y La Varonesa–Lobería).
- **Estudio previo de la USFQ:** destaca tres (Barrio Frío, Divino Niño y Escuela Alvear) y sitúa sus inundaciones en la época de lluvias, de enero a junio.

Tabla: Encañadas urbanas: correspondencia con los cauces del estudio (sección 4.6) y exposición (sección 6.2).

| Encañada (UGR) | Cauce del estudio | Área | Edificios a ≤ 15 / ≤ 30 m del eje | Franja del CGREG a ≤ 30 m |
|---|---|---|---|---|
| **Galápagos / Barrio Frío**, tramo urbano hasta el Malecón | PBM-02 (+ PBM-01) | ≈10,5–11 km² | 24 / 45 | 52 % |
| **Galápagos, tramo alto** (sureste; puente de El Manzanillo) | PBM-03 | ≈8,7 km² | 16 / 33 | 7 % |
| **Manzanillo–El Manantial** | Ramales PBM-L02 (tramo bajo), L08 y L09 | ≈1,8 km² | Incluidos en los afluentes del sureste (6.2) | — |
| **La Planada** | PBM-L02 (tramo alto) | — | Ídem | — |
| **Divino Niño**, que desemboca en **Playa de Oro** | PBM-07 | ≈1,5–1,6 km² | **60 / 88** (16 sobre la línea) | 41 % |
| **Escuela Alvear** | PBM-08 | ≈0,7 km² | 12 / 23 | 0 % |
| **Playa Mann**: la quebrada del campus USFQ / GSC | PBM-L05 | ≈0,31 km² | Véase la sección 4.4 | — |

La UGR describe además **bifurcaciones**: Divino Niño «se separa de la Galápagos» y la Alvear «recoge aguas de Divino Niño». Ni el modelo de flujo ni el 2D las reproducen. Sin embargo, la sección 4.6 identifica un collado con solo 1,2 m de resalte (dentro del error del DSM) por el que la Galápagos podría verter hacia Divino Niño, junto al hospital. **Es una hipótesis de consecuencia alta**: hay que verificarla en campo y no rellenar ese tramo.

**Capas del CGREG.**
- **Flujos de lodo y escombros por El Niño**: 2 polígonos (47,3 ha):
  - uno de 10,2 ha en el entorno de Divino Niño, con 77 edificios, que queda **a 29 m del hospital**;
  - otro de 37,1 ha en el sector sureste (tramo alto de la Galápagos, El Manzanillo y La Planada), con 158 edificios.
- **Franja de protección de 20 m de quebradas**:
  - **no sigue los cauces del DSM**: solo coincide directamente con el eje en 162 m de Divino Niño;
  - en un radio de 30 m cubre el 52 % de Barrio Frío y el 41 % de Divino Niño;
  - Alvear no tiene franja, y la de Divino Niño termina unos 200 m antes del mar;
  - dentro de la franja hay 97 edificios urbanos (sección 6.2).- **Otras capas**: derrumbes (2 polígonos; 13,3 ha), contaminación de acuíferos (3; 64,7 ha) y explosión o derrame de combustible (5; 10 ha).

**Recurrencia.** El registro de la SNGR (2010–2025) contiene **16 inundaciones con fecha** en San Cristóbal, más que en Santa Cruz (12). A ellas se suman 3 deslizamientos, 1 aluvión (El Junco, 2023) y 1 socavamiento (vía a Cerro Gato, 2012). El plan de la UGR añade eventos recientes que no están en esa capa.

Tabla: Inundaciones por sector (registro de la SNGR 2010–2025 y plan de la UGR).

| Sector | Registro de la SNGR | Plan de la UGR |
|---|---|---|
| Divino Niño | 2010 (daño en calles), 2011, 2012 (dos) | Muro del hospital fracturado; desembocadura de Playa de Oro tapada |
| Barrio Frío y Malecón | 2012 (8 familias), 2024 y 2025 | Rompimiento de la playa; riesgo para embarcaciones |
| El Manzanillo | 2011, 2019 (12 viviendas) y 2023 | **Abril de 2026**: desborde a 100 m del puente, que está sobre la Galápagos (tramo alto); destrucción de viviendas, calles, agua potable, alcantarillado y postes |
| **La Planada** | Abril de 2025 (2 viviendas afectadas) | «El sector más afectado en 2025–2026». **Abril de 2025: 5 familias evacuadas. Abril de 2026: nuevo desborde** |
| La Picada (Palmeras–Arrayanes) | — | Daños en calles y viviendas; **7 meses sin servicios básicos** (fecha no indicada) |
| Playa Mann | 2023 (cancha de la U. E. Alejandro Alvear) | Rejillas y alcantarillado taponados; vía adoquinada dañada |
| El Progreso | 2016 (vía a Cerro Verde), 2021 (dispensario del IESS), 2024 (Escuela Carlos Darwin) | 43 viviendas y 124 personas expuestas en la zona urbana |

El sector sureste (La Planada, El Manzanillo y El Manantial) se inundó en **tres de los últimos cuatro años (2023, 2025 y 2026), siempre en abril**. En la SNGR y en la UGR, las cifras de un mismo evento usan unidades distintas: en abril de 2025, 2 viviendas afectadas frente a 5 familias evacuadas.

Otros datos del registro:
- La mayor afectación registrada por la SNGR es de 12 viviendas (El Manzanillo, 2019). No hay víctimas registradas.
- En febrero de 2010 se anotó en Divino Niño una lluvia de «100,1 mm» en una hora y media (dato de radiosonda).
- Los registros de 2010–2012 tienen todos la misma coordenada genérica. El de marzo de 2024 (Av. Antonio Gil) está asignado por error a Puerto Villamil.

**Instalaciones críticas.**

Tabla: Instalaciones críticas del cantón (DSM; modelo 2D con la tormenta trasladada, sección 4b; plan de la UGR).

| Instalación | Cota* | Relación con los cauces | Otras capas | Situación según la UGR u otras fuentes |
|---|---|---|---|---|
| **Hospital Oskar Jandl** | ≈27 m (ubicación OSM) | A **2–15 m** del cauce de Divino Niño, según la malla | A 29 m del polígono de flujos de lodo; HAND media | **UGR:** muro de contención **fracturado en 240 m** y **calle de emergencia obstruida**; el agua de la vía Jaime Roldós, junto al Colegio Ignacio Hernández, **impide el acceso**. El plan lo sitúa en Divino Niño, lo que confirma la ubicación de OSM. La del registro MSP–SNGR, 1,3 km al suroeste, parece errónea |
| Colegio Ignacio Hernández (también zona segura de tsunami) | ≈41–43 m | 193–220 m | — | El agua que corre por la vía Jaime Roldós baja de la ladera del ramal sur de Divino Niño (sección 4.6). Es escorrentía por la calzada, que un DSM de 30 m no capta |
| **USFQ / Galapagos Science Center** | ≈9–12 m | Quebrada de Playa Mann (0,31 km²); en el 2D, 2–5 cm en el campus (secciones 4.4 y 4b) | Flujos de lodo a 357 m; franja a 405 m; una parte en la zona de tsunami del INOCAR | Inundación de 2023 en Playa Mann, a 309 m |
| Alcaldía de San Cristóbal | ≈6 m | 12 m (Galápagos) | — | Sede del COE cantonal (por verificar) |
| Capitanía de Puerto | ≈4 m | 28 m (Galápagos) | **Dentro** del polígono de flujos de lodo | — |
| Escuela Alejandro Alvear | ≈15–16 m | 40–49 m (Alvear) | Zona de tsunami | Cancha inundada en 2023 (SNGR) |
| Escuela Carlos Darwin, El Progreso | ≈316 m | 37–47 m (0,7 km²) | Depresión del DSM de 0,4–1,4 m | Inundada en 2024 (SNGR) |
| **Floreana**: dispensario médico, **desalinizadora**, empresa eléctrica, bodega parroquial, ABG y oficinas del PNG | — | Las instalaciones no se evaluaron una a una. Los cauces del poblado se analizan de forma exploratoria en la sección 4c | — | UGR: «todo el poblado» en riesgo por las cañadas La Hormiga y La Varonesa |

En Floreana, el dispensario, la desalinizadora y la central eléctrica son servicios **sin respaldo en la isla**. Si fallan, el poblado depende de apoyo por mar.

**Refugios.** El registro de la SNGR de 2025 contiene **4 refugios activos en San Cristóbal, con capacidad para 358 personas en total**:
- **Estadio Olímpico Luis Cruz Sayo**, en el barrio San Francisco (147 personas; ≈18,5 m*).
  - Es el único refugio oficial de la ciudad, y está en un barrio que la UGR considera de máxima prioridad.
  - Según el DSM, está a 66 m de un afluente de ≈1,6 km² y a menos de 150 m de la Galápagos.
  - El modelo 2D da calados de **≤ 0,04 m en el estadio y su entorno inmediato** (malla de 15 m) y de hasta 0,3 m a unos 60 m (malla de 30 m). En cambio, los barrios del entorno (San Francisco, Fragata y Estación Terrena) alcanzan 1,25 m, con 54 edificios afectados. **El riesgo del refugio está en el acceso, más que en el recinto.**
- **Estadio Juan Olaya Mora**, en El Progreso (89 personas; ≈317 m*). Está a 79 m de un cauce de 0,7 km², y el 2D da **0,2–0,4 m en el propio recinto y hasta 0,75–1,0 m a su alrededor**: es encharcamiento, el mecanismo que la UGR describe en El Progreso. **Debe verificarse antes de usarlo en un evento de lluvia.**
- Finca Santa Mónica, administrada por la Armada (90 personas; ≈401 m*).
- Escuela Alejandro Humboldt, en La Soledad (32 personas; ≈376 m*).

Floreana no tiene refugio oficial en el registro.

Dos zonas seguras de **tsunami** no sirven para crecidas:
- el Liceo Naval (≈12 m*), dentro del polígono de flujos de lodo;
- el Parque Martha Bucaram de Roldós (≈15 m*), dentro del polígono de flujos de lodo y de la franja de 20 m.

Además, el acceso al Colegio Ignacio Hernández, otra zona segura de tsunami, se inunda por la vía Jaime Roldós.

## 7.2 Sectores prioritarios: plan de la UGR frente al estudio

Tabla: Sectores de máxima prioridad según la UGR y evidencia del estudio (secciones 4.6, 4b y 6b; aquí, la lectura de gestión).

| Sector (UGR) | Evidencia del estudio | Valoración |
|---|---|---|
| Barrio Frío: playa y Poza de las Garzas | Galápagos, tramo urbano; en el ranking de puntos (S01, V22); 2D: 1,4 m | **Coincide** |
| El Manzanillo, El Manantial y Cdla. El Gran Maestro | El desborde de 2026 junto al puente está sobre la Galápagos (tramo alto); 2D: 0,86 m y 10 edificios; no aparece en el ranking de puntos | **Coincide** en el 2D |
| La Planada | En el ranking (V15, L02); 2D: 0,94 m y 15 edificios | **Coincide** |
| Divino Niño (Playa de Oro, hospital, Colegio Ignacio Hernández) | Boca de Playa de Oro en el ranking (S02); cauce con 60 edificios a ≤ 15 m; hospital a 2–15 m. El muro, la boca tapada y el agua por la calzada no son visibles en el DSM | **Coincide** en el cauce y el hospital; **no evaluable** el muro ni la calzada |
| Playa Mann | Quebrada del campus (0,31 km²); 2D: ≈0,5 m en el tramo bajo; rejillas no cartografiadas | **Coincide en parte** |
| San Francisco, Fragata y Estación Terrena | 2D: 1,25 m y 54 edificios; no aparece en el ranking; el refugio oficial de la ciudad está en ese sector; la cañada Cerro Quemado no está resuelta | **Coincide** en el 2D |
| Palmeras–Los Arrayanes y La Picada | Ubicación supuesta (sección 6b); el 2D da 1,0 m, pero ninguno de 23 edificios afectado | **No evaluado con fiabilidad** |
| El Progreso (zona urbana; Cerro Verde, El Chino, Las Goteras) | 20–51 edificios en vasos; 28–35 con ≥ 0,1 m en el 2D, frente a las 43 viviendas del plan; refugio Juan Olaya Mora con encharcamiento | **Coincide** (mismo mecanismo y mismo orden de magnitud) |
| Floreana | Análisis exploratorio (sección 4c) | **Evaluado solo de forma exploratoria** |

**Lectura para la gestión.**
- Las dos fuentes **coinciden en los grandes sistemas**: Galápagos con su tramo alto, La Planada, Divino Niño y El Progreso.
- La UGR aporta lo que un DSM de 30 m no ve:
  - muros, rejillas y bocas taponadas;
  - agua que corre por las calzadas;
  - daños a redes;
  - bifurcaciones.
- El estudio aporta la ubicación de las instalaciones críticas respecto de los cauces, la hipótesis del collado Galápagos–Divino Niño y la exposición de los dos refugios oficiales urbanos y periurbanos.

## 7.3 El evento de 2026 en San Cristóbal

- **Abril de 2026 (UGR) [R].** Desbordes en El Manzanillo, a 100 m del puente, con destrucción de viviendas, calles y redes, y en La Planada.
- **16 de octubre de 2026 (SitRep 67) [R].** Se habilitó un refugio temporal en el barrio Estación Terrena, **antes del evento**, y estaba cerrado al 1 de noviembre (sección 3.5). Las fuentes no indican el motivo. Por sí solo no identifica una zona afectada.
- **31 de octubre, por la mañana (SitRep 01) [R]:**
  - desbordamiento de las cañadas **Barrio Frío y Divino Niño**, con calles anegadas en el casco urbano y afectación a varias familias;
  - la desembocadura afectó la playa «Los Marinos», con riesgo de arrastrar embarcaciones.
- **1 de noviembre (SitRep 67) [R].** «Tras el cese de las precipitaciones, no se registran vías inundadas ni reportes de viviendas afectadas». El evento figura como finalizado.

Sin embargo, el plan de la UGR documenta **daños acumulados** que siguen sin reparar: el muro del hospital, la calle de emergencia, la desembocadura de Playa de Oro taponada y las redes de El Manzanillo. **Un sistema dañado es más vulnerable a la siguiente lluvia**, y en los Niños fuertes la temporada se extendió de noviembre a junio.

**No hay lluvia medida del evento en San Cristóbal [M].** No se sabe qué intensidad desbordó las cañadas (sección 3).

## 7.4 Medidas

### Medidas propuestas por el plan de la UGR y sus riesgos

El plan propone **tres medidas explícitas**. Se valoran aquí con la misma lógica aplicada al desvío de La Cascada: qué resuelven, dónde trasladan el riesgo, qué mantenimiento exigen y qué permisos necesitan. Sus trazados aproximados están en la sección 6b.

Tabla: Medidas propuestas por el plan de la UGR y riesgos asociados.

| Medida (UGR) | Qué resuelve | Riesgos estructurales o ambientales | Condiciones mínimas |
|---|---|---|---|
| **Zanja de 1 040 m en El Manzanillo** | Da salida al desborde junto al puente | **Traslado del riesgo** aguas abajo: según el D8, el sistema desemboca por Barrio Frío, que ya es prioritario. Sin curvas IDF ni lluvia medida, la capacidad es incierta. El sector está en el polígono de flujos de lodo, así que la zanja **se colmatará**. Una zanja abierta en zona urbana supone riesgo de caídas y ahogamiento y, si retiene agua, criadero de mosquitos. **Efecto dique**: puede inducir a construir junto a ella. Si su trazado entra en el PNG, necesita autorización de la DPNG | Perfil topográfico de detalle (dron o GNSS); inicio, fin y descarga definidos (el plan no los da); pendiente continua sin encharcamiento; responsable y presupuesto de limpieza; prohibir construir en su franja |
| **Limpieza de 240 m urbanos y 170 m dentro del PNG**, La Picada | Recupera la capacidad del cauce, que según el D8 es la parte alta del sistema de El Manzanillo | Bajo riesgo estructural. En el PNG: retirada de vegetación nativa, disposición del material retirado, que no debe ir a la bahía, y posible dispersión de especies invasoras | Autorización y acompañamiento de la DPNG; protocolo de bioseguridad (ABG); hacerlo antes de cada temporada, como **mantenimiento recurrente** y no como obra única |
| **Floreana: conectar las cañadas con 500 m de excavación** para proteger Playa Negra | Desvía hacia otra salida parte del agua que llega a Playa Negra | Es un **desvío entre cuencas**, análogo al interceptor de La Cascada. La sección 4c lo considera **topográficamente plausible hacia el norte**: un canal de 250–300 m desviaría el 57 % de la cuenca de Playa Negra. **Hacia el sur no lo es.** Hacia el norte, el agua desviada llega a la costa 690 m al norte, adonde se **trasladan el riesgo y los sedimentos**. El 40–45 % inferior de la cuenca seguiría llegando a Playa Negra. Probablemente cruza suelo del PNG en una isla con un programa activo de restauración ecológica. Está cerca de servicios críticos sin respaldo | Identificar qué cauce es cada cañada; levantamiento GNSS; conocer el destino aguas abajo del agua desviada; evaluación de impacto ambiental con la DPNG y el MAATE; comparar con alternativas que no desvíen (proteger instalaciones, despejar cauces) |

### Medidas que se deducen del plan

El plan describe estas situaciones como **afectaciones**, no como medidas. Se incluyen porque se deducen directamente de ellas.

Tabla: Medidas que se deducen de las afectaciones descritas en el plan.

| Medida | Qué resuelve | Riesgos | Condiciones mínimas |
|---|---|---|---|
| **Despejar la desembocadura de Playa de Oro** (lodo y piedras) | Es la más urgente: una salida taponada eleva el nivel en todo Divino Niño, incluido el entorno del hospital | Los sedimentos van a la playa y a la **Reserva Marina**. Una boca rígida podría trasladar la erosión a las playas vecinas | Coordinación con la DPNG (Reserva Marina) y la Capitanía; repetirla tras cada evento; no endurecer la salida sin estudiar la dinámica costera |
| **Reparar el muro del hospital (240 m)** y despejar la calle de emergencia | Recupera el acceso y la protección del único hospital de la isla | Un muro reparado puede dar **falsa seguridad** y, si colapsa en una crecida, aporta escombros al cauce. Si se confirma el collado de la sección 4.6, el caudal de diseño junto al hospital sería mucho mayor que el de Divino Niño | Prioridad inmediata; diseñar el muro con el escenario de bifurcación; **ruta alternativa de acceso** que no dependa de la vía Jaime Roldós |

### Medidas no estructurales del estudio

**Inmediatas (días)**
- **Hospital**:
  - garantizar una ruta de acceso alternativa y señalizarla;
  - verificar la estabilidad del muro;
  - definir un plan de continuidad del servicio si el acceso se corta, como le ocurrió al Centro de Salud de Puerto Ayora el 30 de octubre.
- **Collado Galápagos–Divino Niño**: verificarlo con GNSS y prohibir rellenos en ese tramo (sección 4.6).
- **Marcas de agua y daños** en El Manzanillo, La Planada, Barrio Frío y Divino Niño, con GNSS y fotografías, junto con entrevistas sobre las horas.
- **Revisar los refugios**:
  - el acceso al Estadio Luis Cruz Sayo;
  - el encharcamiento del Estadio Juan Olaya Mora;
  - sitios alternativos fuera de cauces y de vasos;
  - un refugio para Floreana.

**3 meses**
- **SAT por lluvia.** Pluviómetros telemétricos en El Progreso (≈300 m*), en la parte alta hacia El Junco y en la ciudad, con umbrales y un protocolo análogos a los de Santa Cruz (véase el estudio de Santa Cruz, sección 11.3).
  - Las cuencas urbanas son pequeñas (0,3–11 km²) y responden en minutos. El aviso debe basarse en la lluvia medida en la parte alta y en el INAMHI.
  - La USFQ / Galapagos Science Center puede alojar una estación y apoyar la vigilancia.
- **Simulacros** en El Manzanillo, La Planada, Barrio Frío y Divino Niño, que acumulan registros en 2023–2026.

**1 año**
- **Mapa oficial de amenaza** de las 15 encañadas, con LiDAR o dron y modelación 2D que represente bifurcaciones, muros y pasos bajo las vías, y conciliación con la franja del CGREG.
- **Normas de uso del suelo** en las franjas de cauce (LOOTUGS art. 108, núm. 7). Prioridades: el tramo final de Divino Niño sin franja y el sector sureste.
- **Plan de mantenimiento** anual de cauces, rejillas y desembocaduras, con presupuesto propio.

### Riesgo sanitario: dengue por agua estancada

El plan de la UGR ya identifica la **epidemia de dengue por acumulación de agua** entre las afectaciones comunes a todos los barrios.
- **Antecedentes:**
  - *Aedes aegypti* está establecido en Puerto Baquerizo Moreno y en Puerto Ayora;
  - en 2010, Puerto Baquerizo Moreno tuvo un brote con una incidencia de unos 1 410 casos por 10 000 habitantes;
  - en una encuesta de 2014, el almacenamiento de agua en el hogar fue el principal factor asociado al vector (Ryan et al., 2019).
- **Lo que añade el estudio** es un criterio operativo: **ninguna zanja, cuneta, desembocadura ni depósito debe retener agua más de 7 días**, que es aproximadamente el ciclo del mosquito. Esto condiciona el diseño de la zanja de El Manzanillo y de cualquier canal nuevo.
- **Otras medidas:**
  - tapar los depósitos domésticos, que aumentan donde falla la red, como en La Picada y El Manzanillo;
  - vigilancia entomológica con trampas (la USFQ probó trampas Gravid-Aedes en ambas islas);
  - vigilancia de casos febriles coordinada entre el MSP, la ABG y el GAD;
  - restituir primero el agua potable y el alcantarillado, porque el agua estancada mezclada con aguas servidas expone también a enfermedades de origen hídrico (sección 8).

## 7.5 Gobernanza

Puerto Baquerizo Moreno es la **capital provincial**. Allí tiene su sede el **CGREG**, cuyo presidente preside el comité provincial de gestión del riesgo y el COE provincial (LOGIRD, disposición general octava). El CGREG también coordina la gestión de riesgos y las obras en cuencas (LOREG arts. 5 y 23).

El plan de la UGR muestra que **el GAD dispone de un diagnóstico propio y de un plan de acción por sectores**. Es el instrumento natural sobre el que articular las medidas de este estudio.

Tabla: Actores y competencias en el cantón San Cristóbal.

| Actor | Rol | Base legal |
|---|---|---|
| GAD municipal de San Cristóbal (UGR) | Competencia directa: plan de acción, mapas, monitoreo, ordenamiento del suelo, alcantarillado pluvial y comités comunitarios | COOTAD arts. 55 y 140; LOGIRD arts. 9, 20, 21 y 39 |
| COE cantonal | Coordina la respuesta y dispone las evacuaciones | LOGIRD arts. 28–29 |
| GAD parroquiales de El Progreso y Floreana | Análisis de riesgos y capacitación comunitaria | LOGIRD art. 9 |
| CGREG y COE provincial | Coordinación provincial; su presidente preside el COE de Galápagos | LOREG arts. 5 y 23; LOGIRD, disposición general octava |
| SNGR (UMEVA Galápagos) | Monitoreo, SitReps, lineamientos del SAT y estándares de mapas | LOGIRD arts. 23, 56 y 62 |
| INAMHI | Advertencias y red hidrometeorológica | LOGIRD art. 34 |
| DPNG y MAATE | Cabeceras de las encañadas en el PNG; desembocaduras en la Reserva Marina; autorización de obras y limpiezas | LOREG art. 23 |
| MSP y ABG | Continuidad del hospital; vigilancia del dengue y del vector | — |
| ELECGALÁPAGOS y empresa de agua | Redes dañadas (postes, tuberías); desalinizadora de Floreana | — |
| Armada (Capitanía, II Zona Naval) | Respuesta; refugio Finca Santa Mónica; embarcaciones y desembocaduras | — |
| USFQ / GSC | Organismo técnico-científico (previo registro): datos, monitoreo y apoyo al SAT | LOGIRD art. 34 |

## 7.6 Riesgos de las soluciones estructurales

Además de lo señalado para cada medida (sección 7.4), valen las advertencias generales del estudio:
- **efecto dique**: reducir los eventos frecuentes tiende a aumentar la exposición y a debilitar la preparación;
- **dimensionamiento** sin curvas IDF ni lluvia medida en la isla;
- **mantenimiento**, que necesita un responsable y presupuesto;
- **sedimentos** que colmatan zanjas y desembocaduras;
- **traslado del riesgo** hacia otros barrios, otras cuencas o la bahía.

Las recomendaciones integradas están en la sección 9. El estudio previo de la USFQ compara alternativas de obra para las encañadas: embalses, desvío y micro-embalses. Conviene contrastar sus supuestos con los eventos de 2023–2026.

## Fuentes de esta sección

- UGR del GAD municipal de San Cristóbal, *Plan de Acción SC-4-09-2026 – Fenómeno El Niño – San Cristóbal*. Documento interno facilitado por la coordinación de USFQ Galápagos el 2-nov-2026; citado, no reproducido.
- SNGR, SitRep n.º 01 de Galápagos (31-oct-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SITREP-Nro.-01-Lluvias_Galapagos_29.08.2026-31.10.2026.pdf
- SNGR, SitRep 67 nacional (1-nov-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SitRep-No-67-Lluvias-29082026-al-01112026-15h00f21.pdf
- USFQ, estudio de las encañadas de Puerto Baquerizo Moreno: https://repositorio.usfq.edu.ec/bitstream/23000/10220/1/138016.pdf
- Ryan, S. J. et al. (2019). Socio-ecological factors associated with dengue risk and *Aedes aegypti* presence in the Galápagos Islands, Ecuador. *Int. J. Environ. Res. Public Health*: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6427784/
- Universidad de Florida, resumen del estudio (incidencia de 2010 en Puerto Baquerizo Moreno): https://epi.ufl.edu/2019/03/13/new-study-explores-galapagos-islands-dengue-risks
- USFQ, *Esferas*: vigilancia de *Aedes aegypti* con trampas Gravid-Aedes en Galápagos: https://revistas.usfq.edu.ec/index.php/esferas/article/download/1988/2312
- LOGIRD: https://procuraduria.utpl.edu.ec/NormativaExterna/LEY%20ORG%C3%81NICA%20PARA%20LA%20GESTI%C3%93N%20INTEGRAL%20DEL%20RIESGO%20DE%20DESASTRES.pdf
- LOREG: https://faolex.fao.org/docs/pdf/ecu166165.pdf
- Datos: `capas/final/` (eventos SNGR, refugios SNGR 2025, MSP, MINEDUC, OSM, CGREG, INOCAR), DSM Copernicus GLO-30 y resultados del modelo 2D (`datos/modelo2d/`).
