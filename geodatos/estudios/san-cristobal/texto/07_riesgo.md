[[SALTO]]

# 7. Gestión del riesgo de desastres

Esta sección cubre el cantón San Cristóbal: Puerto Baquerizo Moreno, El Progreso y, solo en lo que toca a la gestión, Floreana. Combina tres tipos de información:
- **[R] reportado**: registro de eventos y SitReps de la SNGR, y el **Plan de Acción SC-4-09-2026 «Fenómeno El Niño – San Cristóbal» de la Unidad de Gestión de Riesgos (UGR) del GAD municipal**, en adelante «el plan de la UGR». Es un documento interno, facilitado por la coordinación de USFQ Galápagos el 2 de noviembre de 2026; aquí se cita, no se reproduce;
- **[E] estimado**: el análisis del estudio sobre el DSM y las capas oficiales;
- **[M] medido**: no hay lluvia medida del evento en San Cristóbal.

Los datos auxiliares están en `datos/riesgo/` y se regeneran con `scripts/grd_riesgo_islas.py`:
- `instalaciones_criticas.csv`;
- `recurrencia_sngr.csv`;
- `capas_cgreg_resumen.csv`.

Las cotas marcadas con * proceden del DSM Copernicus GLO-30, con un error de ±2–4 m y un sesgo de unos −2 m frente al IGM. **No deben usarse como umbrales normativos.** Los cauces «del DSM» se derivaron con un umbral de 0,5 km² de área drenada. Su trazado en la ciudad, con edificios y calles, es aproximado. La validación topográfica de los cauces corresponde a la sección de hidrología.

## 7.1 Caracterización del riesgo

**Amenaza.** La amenaza es la crecida súbita de las **encañadas que bajan del cerro hacia la bahía**, con arrastre de lodo y piedras.
- **Inventario de la UGR:** 15 encañadas principales. Diez están en Puerto Baquerizo Moreno: Galápagos o Barrio Frío, Cerro Quemado o Don García, Divino Niño, Escuela Alejandro Alvear, Playa Mann, Manzanillo–El Manantial, Palmeras–Arrayanes, La Planada, Centro de Gestión de Residuos Sólidos y Parque Artesanal. Las demás están en los recintos de El Progreso, en los viveros del PNG y la Galapaguera, y en Floreana (La Hormiga y La Varonesa–Lobería).
- **Estudio previo de la USFQ:** destaca tres de ellas (Barrio Frío, Divino Niño y Escuela Alvear) y sitúa sus inundaciones en la época de lluvias, de enero a junio.

Tabla: Cauces urbanos principales según el DSM y nombre según la UGR (correspondencia por validar en la sección de hidrología).

| Cauce del DSM (área drenada) | Nombre según la UGR | Descripción de la UGR | Edificios a ≤ 15 m del eje (DSM) |
|---|---|---|---|
| ≈10,5–11 km²; desemboca hacia el Malecón | **Cañada Galápagos o Barrio Frío** | La principal. Nace en la zona rural, pasa por Cerro Mundo (PNG), La Planada y Los Arroyos, y desemboca en Bahía Naufragio, donde rompe la playa | ≈108 |
| ≈8–9,4 km²; sector sureste | **Manzanillo–El Manantial** | Varias ramificaciones que bajan de La Planada | ≈45 |
| ≈1,0–1,6 km²; pasa junto a la Iglesia Divino Niño | **Divino Niño** | Se separa de la Galápagos a la altura de los talleres del CGREG y desemboca en **Playa de Oro** | ≈67 |
| ≈0,7 km²; junto a la Escuela Alejandro Alvear | **Escuela Alvear** o **Playa Mann** (la UGR las distingue) | La Alvear recoge agua de Divino Niño y desemboca por el muelle de pescadores; la de Playa Mann nace junto al patio de contenedores | ≈7 |

En la versión anterior de esta sección se atribuía la desembocadura de Divino Niño a Playa Mann. **La UGR la sitúa en Playa de Oro, y se adopta su versión.** La UGR también describe una **bifurcación** (Divino Niño se separa de la Galápagos y la Alvear recoge agua de Divino Niño). Un modelo de flujo D8 no puede representarla, porque asigna a cada celda una sola salida.

**Capas del CGREG.**
- **Flujos de lodo y escombros por El Niño**: 2 polígonos (47,3 ha):
  - uno de 10,2 ha en el entorno de Divino Niño, con 77 edificios, que queda **a 29 m del hospital**;
  - otro de 37,1 ha en el sector de El Manzanillo, con 158 edificios.
- **Franja de protección de 20 m de quebradas**: incluye 172 edificios de la isla. **Apenas coincide con los cauces urbanos del DSM**: cubre 22 de los ≈1 000 m del cauce de Barrio Frío en la ciudad y 33 de los ≈700 m del de Divino Niño. Hay que aclarar con el CGREG sobre qué red de quebradas se trazó.
- **Otras capas**: derrumbes (2 polígonos; 13,3 ha), contaminación de acuíferos (3; 64,7 ha) y explosión o derrame de combustible (5; 10 ha).

**Recurrencia.** El registro de la SNGR (2010–2025) contiene **16 inundaciones con fecha** en San Cristóbal, más que en Santa Cruz (12). A ellas se suman 3 deslizamientos, 1 aluvión (El Junco, 2023) y 1 socavamiento (vía a Cerro Gato, 2012). El plan de la UGR añade eventos recientes que no están en esa capa.

Tabla: Inundaciones por sector (registro de la SNGR 2010–2025 y plan de la UGR).

| Sector | Registro de la SNGR | Plan de la UGR |
|---|---|---|
| Divino Niño | 2010 (daño en calles), 2011, 2012 (dos) | Muro del hospital fracturado; desembocadura de Playa de Oro tapada |
| Barrio Frío y Malecón | 2012 (8 familias), 2024 y 2025 | Rompimiento de la playa; riesgo para embarcaciones |
| El Manzanillo | 2011, 2019 (12 viviendas) y 2023 | **Abril de 2026**: desborde a 100 m del puente; destrucción de viviendas, calles, agua potable, alcantarillado y postes |
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

Tabla: Instalaciones críticas del cantón (DSM; distancias horizontales; plan de la UGR).

| Instalación | Cota* | Cauce del DSM más cercano | Otras capas | Situación según la UGR u otras fuentes |
|---|---|---|---|---|
| **Hospital Oskar Jandl** | ≈27 m (ubicación OSM) | **2–7 m** (1,0–1,6 km², Divino Niño) | A 29 m del polígono de flujos de lodo; HAND media | **UGR:** muro de contención **fracturado en 240 m** y **calle de emergencia obstruida**; el agua que corre por la vía Jaime Roldós, junto al Colegio Ignacio Hernández, **impide el acceso**. El plan lo sitúa en el barrio Divino Niño, lo que confirma la ubicación de OSM. La del registro MSP–SNGR, 1,3 km al suroeste, parece errónea; conviene corregirla |
| Colegio Ignacio Hernández (también zona segura de tsunami) | ≈41–43 m | 193–220 m | — | UGR: el agua drena por la vía Jaime Roldós. Es **escorrentía por la calzada**, que el análisis de cauces no capta |
| **USFQ / Galapagos Science Center** | ≈9–12 m | 82 m (0,3 km²); 252 m (0,7 km²); 380 m (1,6 km²) | Flujos de lodo a 357 m; franja a 405 m; una parte en la zona de tsunami del INOCAR | Inundación de 2023 en Playa Mann, a 309 m. No está en una depresión del DSM |
| Alcaldía de San Cristóbal | ≈6 m | 12 m (≈11 km², Galápagos) | — | Sede del COE cantonal (por verificar) |
| Capitanía de Puerto | ≈4 m | 28 m (≈11 km²) | **Dentro** del polígono de flujos de lodo | — |
| Escuela Alejandro Alvear | ≈15–16 m | 40–49 m (0,7 km²) | Zona de tsunami | Cancha inundada en 2023 (SNGR) |
| Escuela Carlos Darwin, El Progreso | ≈316 m | 37–47 m (0,7 km²) | Depresión del DSM de 0,4–1,4 m | Inundada en 2024 (SNGR) |
| **Floreana**: dispensario médico, **desalinizadora**, empresa eléctrica, bodega parroquial, ABG y oficinas del PNG | — | No evaluado: Floreana queda fuera del DSM procesado | — | UGR: «todo el poblado» en riesgo por las cañadas La Hormiga y La Varonesa |

En Floreana, el dispensario, la desalinizadora y la central eléctrica son servicios **sin respaldo en la isla**. Si fallan, el poblado depende de apoyo por mar.

**Refugios.** El registro de la SNGR de 2025 contiene **4 refugios activos en San Cristóbal, con capacidad para 358 personas en total**:
- **Estadio Olímpico Luis Cruz Sayo**, en el barrio San Francisco (147 personas; ≈18,5 m*). Está a **66 m de un cauce de 1,6 km²** y a menos de 150 m del de Barrio Frío, en un barrio que la UGR considera prioritario. Es el único refugio oficial de la ciudad y su exposición debe verificarse;
- Estadio Juan Olaya Mora, en El Progreso (89 personas; ≈317 m*; a 79 m de un cauce de 0,7 km²);
- Finca Santa Mónica, administrada por la Armada (90 personas; ≈401 m*);
- Escuela Alejandro Humboldt, en La Soledad (32 personas; ≈376 m*).

Floreana no tiene refugio oficial en el registro.

Dos zonas seguras de **tsunami** no sirven para crecidas:
- el Liceo Naval (≈12 m*), dentro del polígono de flujos de lodo;
- el Parque Martha Bucaram de Roldós (≈15 m*), dentro del polígono de flujos de lodo y de la franja de 20 m.

Además, el acceso al Colegio Ignacio Hernández, otra zona segura de tsunami, se inunda por la vía Jaime Roldós.

## 7.2 Sectores prioritarios: plan de la UGR frente al estudio

Tabla: Sectores de máxima prioridad según la UGR y evidencia del estudio (gestión; la validación topográfica está en la sección de hidrología).

| Sector (UGR) | Evidencia del estudio | Valoración |
|---|---|---|
| Barrio Frío: playa y Poza de las Garzas | Cauce principal (≈11 km²), ≈108 edificios a ≤ 15 m; SNGR 2012, 2024 y 2025 | **Coincide** |
| El Manzanillo, El Manantial y Cdla. El Gran Maestro | Cauce de ≈8–9 km²; polígono de lodo de 37 ha (158 edificios); SNGR 2011, 2019 y 2023 a 18–49 m del cauce | **Coincide** |
| La Planada | Registro SNGR de 2025 a 91 m del cauce de Manzanillo; a 359 m del polígono de lodo | **Coincide** (cabecera del sistema Manzanillo) |
| Divino Niño (Playa de Oro, hospital, Colegio Ignacio Hernández) | Cauce de 1,0–1,6 km² (≈67 edificios); polígono de lodo de 10 ha; hospital a 2–7 m | **Coincide** en el cauce y el hospital. **No coincide** en el Colegio, cuyo problema es la escorrentía por la vía |
| Playa Mann | Cauce de ≈0,7 km²; SNGR 2023 | **Coincide** |
| San Francisco, Fragata y Estación Terrena (cañadas Galápagos y Cerro Quemado) | Refugio oficial a 66 m de un cauce; refugio temporal en Estación Terrena (16-oct-2026, SitRep 67); cañada Cerro Quemado sin analizar | **Coincide en parte** / no evaluado |
| Palmeras–Los Arrayanes y La Picada | No se identificó en los datos | **No evaluado** |
| El Progreso (zona urbana; Cerro Verde, El Chino, Las Goteras) | SNGR 2016, 2021 y 2024; Escuela Carlos Darwin en depresión del DSM. La UGR describe anegamiento por cunetas y bordillos | **Coincide** (mecanismo de drenaje vial, no de cauce) |
| Floreana | Fuera del DSM procesado | **No evaluado** |

**Lectura de la tabla.**
- Las dos fuentes **coinciden en los cuatro grandes sistemas**: Galápagos, Manzanillo–La Planada, Divino Niño y Playa Mann.
- La UGR aporta lo que un DSM de 30 m no ve:
  - escorrentía por calzadas (Jaime Roldós, El Progreso);
  - rejillas y desembocaduras taponadas;
  - daños a redes;
  - bifurcaciones de cauces.
- El estudio aporta la ubicación de las instalaciones críticas respecto de los cauces y señala que el único refugio oficial de la ciudad está en una zona de prioridad.

## 7.3 El evento de 2026 en San Cristóbal

- **Abril de 2026 (UGR) [R].** Desbordes en El Manzanillo, a 100 m del puente, con destrucción de viviendas, calles y redes, y en La Planada.
- **16 de octubre de 2026 (SitRep 67) [R].** Refugio temporal en el barrio Estación Terrena, ya cerrado al 1 de noviembre. Indica un evento previo, en un sector que la UGR asocia a las cañadas Galápagos y Cerro Quemado (detalles por verificar).
- **31 de octubre, por la mañana (SitRep 01) [R]:**
  - desbordamiento de las cañadas **Barrio Frío y Divino Niño**, con calles anegadas en el casco urbano y afectación a varias familias;
  - la desembocadura afectó la playa «Los Marinos», con riesgo de arrastrar embarcaciones.
- **1 de noviembre (SitRep 67) [R].** «Tras el cese de las precipitaciones, no se registran vías inundadas ni reportes de viviendas afectadas». El evento figura como finalizado.

Sin embargo, el plan de la UGR documenta **daños acumulados** que siguen sin reparar: el muro del hospital, la calle de emergencia, la desembocadura de Playa de Oro taponada y las redes de El Manzanillo. **Un sistema dañado es más vulnerable a la siguiente lluvia**, y en los Niños fuertes la temporada se extendió de noviembre a junio.

**No hay lluvia medida del evento en San Cristóbal [M].** Ni la red IERSE-WSN ni el INAMHI ofrecen datos públicos. No se puede saber qué intensidad desbordó las cañadas.

## 7.4 Medidas

### Medidas del plan de la UGR y sus riesgos

Las medidas que propone el plan de la UGR se valoran aquí con la misma lógica aplicada al desvío de La Cascada: qué resuelven, dónde trasladan el riesgo, qué exige su mantenimiento y qué permisos necesitan.

Tabla: Medidas del plan de la UGR y riesgos asociados.

| Medida (UGR) | Qué resuelve | Riesgos estructurales o ambientales | Condiciones mínimas |
|---|---|---|---|
| **Zanja de 1 040 m en El Manzanillo** | Da salida al desborde junto al puente | **Traslado del riesgo** a su desembocadura y a los barrios aguas abajo. Sin curvas IDF ni lluvia medida, la capacidad es incierta. El sector está dentro del polígono de flujos de lodo, así que la zanja se **colmatará** con sedimentos. Una zanja abierta en zona urbana supone riesgo de caídas y ahogamiento y, si retiene agua, criadero de mosquitos. **Efecto dique**: puede inducir a construir junto a ella. Si su trazado entra en el PNG, necesita autorización de la DPNG | Perfil topográfico de detalle (dron o GNSS); punto de descarga definido y verificado; pendiente continua sin encharcamiento; responsable y presupuesto de limpieza; prohibir construir en su franja |
| **Limpieza de 240 m urbanos y 170 m dentro del PNG**, La Picada | Recupera la capacidad del cauce existente | Bajo riesgo estructural. En el PNG: retirada de vegetación nativa, disposición del material retirado, que no debe ir a la bahía, y posible dispersión de especies invasoras | Autorización y acompañamiento de la DPNG; protocolo de bioseguridad (ABG); hacerlo antes de cada temporada, como **mantenimiento recurrente** y no como obra única |
| **Desembocadura de Playa de Oro**: retirar lodo y piedras | Es la medida más urgente: una salida taponada eleva el nivel en todo Divino Niño, incluido el entorno del hospital | Los sedimentos van a la playa y a la **Reserva Marina**. Una desembocadura rígida podría trasladar la erosión a las playas vecinas | Coordinación con la DPNG (Reserva Marina) y la Capitanía; repetirla tras cada evento; no endurecer la salida sin un estudio de dinámica costera |
| **Floreana: conectar las cañadas La Hormiga y La Varonesa con 500 m de excavación** para proteger Playa Negra | Evita que el agua llegue a Playa Negra y al poblado | Es un **desvío entre cuencas**, análogo al interceptor de La Cascada. Suma dos caudales en un solo cauce: **aumenta el pico aguas abajo** y traslada el riesgo y los sedimentos a la otra desembocadura. Probablemente cruza suelo del PNG en una isla con un programa activo de restauración ecológica. Pasa cerca de servicios críticos sin respaldo (desalinizadora, dispensario, central eléctrica). Su viabilidad topográfica no está demostrada | Topografía de detalle y estudio hidrológico de ambas cuencas; evaluación de impacto ambiental con la DPNG y el MAATE; comparación con alternativas que no desvíen (proteger instalaciones, despejar cauces) |
| **Reparar el muro del hospital (240 m)** y despejar la calle de emergencia | Recupera el acceso y la protección del único hospital de la isla | Un muro reparado puede dar **falsa seguridad** y, si colapsa en una crecida, aporta escombros al cauce | Prioridad inmediata; diseño del muro con el caudal de Divino Niño; **ruta alternativa de acceso** al hospital que no dependa de la vía Jaime Roldós |

### Medidas no estructurales

**Inmediatas (días)**
- **Hospital**:
  - garantizar una ruta de acceso alternativa y señalizarla;
  - verificar la estabilidad del muro;
  - definir un plan de continuidad del servicio si el acceso se corta, como le ocurrió al Centro de Salud de Puerto Ayora el 30 de octubre.
- **Marcas de agua y daños** en El Manzanillo, La Planada, Barrio Frío y Divino Niño, con GNSS y fotografías, junto con entrevistas sobre las horas.
- **Despejar** la desembocadura de Playa de Oro, las rejillas de Playa Mann y los cauces de La Picada antes de nuevas lluvias.
- **Revisar los refugios**: exposición del Estadio Luis Cruz Sayo; sitios alternativos fuera de cauces y de las zonas prioritarias; un refugio para Floreana.
- **Dengue**: véase el apartado siguiente.

**3 meses**
- **SAT por lluvia.** Pluviómetros telemétricos en El Progreso (≈300 m*), en la parte alta hacia El Junco y en la ciudad, con umbrales y un protocolo análogos a los de Santa Cruz (véase el estudio de Santa Cruz, sección 7.3).
  - Las cuencas urbanas son pequeñas (0,7–11 km²) y responden en minutos. El aviso debe basarse en la lluvia medida en la parte alta y en el INAMHI.
  - La USFQ / Galapagos Science Center puede alojar una estación y apoyar la vigilancia.
- **Simulacros** en El Manzanillo, La Planada, Barrio Frío y Divino Niño, que acumulan registros en 2023–2026.

**1 año**
- **Mapa oficial de amenaza** de las 15 encañadas, con LiDAR o dron y modelación 2D que represente las bifurcaciones, y conciliación con la franja del CGREG.
- **Normas de uso del suelo** en las franjas de cauce (LOOTUGS art. 108, núm. 7) y en el sector sureste.
- **Plan de mantenimiento** anual de cauces, rejillas y desembocaduras, con presupuesto propio.

### Riesgo sanitario: dengue por agua estancada

El plan de la UGR advierte del riesgo de **epidemia de dengue por acumulación de agua**.
- **Antecedentes:**
  - *Aedes aegypti* está establecido en Puerto Baquerizo Moreno y en Puerto Ayora;
  - en 2010, Puerto Baquerizo Moreno tuvo un brote con una incidencia de unos 1 410 casos por 10 000 habitantes;
  - una encuesta de 2014 encontró más viviendas con el vector en San Cristóbal que en Santa Cruz, y el almacenamiento de agua en el hogar fue el principal factor asociado (Ryan et al., 2019).
- **Por qué importa ahora:** tras una inundación se suman tres factores:
  - agua estancada en zanjas, cunetas, desembocaduras taponadas y escombros;
  - más almacenamiento doméstico de agua si falla la red, como en La Picada y El Manzanillo;
  - temperaturas altas por El Niño.
- **Medidas:**
  - eliminar el agua estancada en menos de una semana, que es aproximadamente el ciclo del mosquito;
  - que las zanjas y canales nuevos **no retengan agua**;
  - tapar los depósitos domésticos;
  - vigilancia entomológica con trampas (la USFQ probó trampas Gravid-Aedes en ambas islas);
  - vigilancia de casos febriles coordinada entre el MSP, la ABG y el GAD.

  El agua estancada mezclada con aguas servidas también expone a otras enfermedades de origen hídrico. Por eso deben restituirse primero el agua potable y el alcantarillado de El Manzanillo.

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

Además de lo señalado para cada medida de la UGR (sección 7.4), valen las advertencias generales del estudio:
- **efecto dique**: reducir los eventos frecuentes tiende a aumentar la exposición y a debilitar la preparación;
- **dimensionamiento** sin curvas IDF ni lluvia medida en la isla;
- **mantenimiento**, que necesita un responsable y presupuesto;
- **sedimentos** que colmatan zanjas y desembocaduras;
- **traslado del riesgo** hacia otros barrios, otras cuencas o la bahía.

El estudio previo de la USFQ compara alternativas de obra para las encañadas: embalses, desvío y micro-embalses. Conviene contrastar sus supuestos con los eventos de 2023–2026.

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
- Datos: `capas/final/` (eventos SNGR, refugios SNGR 2025, MSP, MINEDUC, OSM, CGREG, INOCAR) y DSM Copernicus GLO-30.
