[[SALTO]]

# 7. Gestión del riesgo de desastres

Esta sección amplía a toda la isla el análisis de La Cascada: la parte alta (Bellavista, El Aguacatal, el sector Tomás de Berlanga y Santa Rosa) y la parte baja (Puerto Ayora). La cronología del evento y la tabla de factores de alerta están en la sección 2; aquí no se repiten.

Los datos auxiliares están en `datos/riesgo/` y se regeneran con `scripts/grd_riesgo_islas.py`. Las cotas marcadas con * proceden del DSM Copernicus GLO-30, con un error de ±2–4 m y un sesgo de unos −2 m frente al IGM. **No deben usarse como umbrales normativos.**

## 7.1 Caracterización del riesgo

**Amenaza.** En Santa Cruz la amenaza dominante es la **crecida súbita de cañadas con flujos de lodo y escombros**. Se presenta de dos formas:
- **En la parte media-alta (≈100–450 m*)**, las cañadas desbordan en minutos sobre viviendas, vías y vados. Así ocurrió el 30 de octubre en El Aguacatal, Guayabillos, El Occidente y el sector Tomás de Berlanga. El evento fue mortal: una persona falleció en la cañada El Aguacatal.
- **En la parte baja**, el agua de una cuenca de 42 km² se acumula en una zona cerrada al pie de un escarpe: el vaso de La Cascada, sin cauce hasta el mar.

Las capas oficiales cubren mal esta amenaza:
- el polígono del CGREG de «flujos de lodo por El Niño» cubre el 38 % de La Cascada (2,3 ha), pero **no cubre ningún punto crítico de la parte alta**;
- los polígonos de «riesgo de inundación» del CGREG para Puerto Ayora son costeros;
- la red de quebradas del IGM es muy escasa en la parte alta. Las instalaciones de Bellavista quedan a 300–1 900 m de la quebrada IGM más cercana, pero a **10–150 m de cauces derivados del DSM que drenan 7–10 km²**.

**La cartografía oficial no representa la amenaza de crecida súbita en la parte alta ni en el vaso de La Cascada.**

**Recurrencia.** El registro de la SNGR para Santa Cruz (2010–2025) contiene 12 inundaciones con fecha.

Tabla: Inundaciones del registro de la SNGR por parroquia (2010–2025).

| Parroquia | N.º | Años y sectores | Afectación máxima registrada |
|---|---|---|---|
| Bellavista | 6 | 2016 (Ciudadela Garden; vía a Baltra), 2023 (Barrio Central), **2024 (El Aguacatal, dos registros)**, 2025 (Miconia) | 8 viviendas (2016) |
| Puerto Ayora | 4 | 2015, 2021 (Alborada), **2023 (La Cascada, Unión, Matazarnos, Acacias, Central)**, 2025 | 3 viviendas |
| Santa Rosa | 2 | 2016 (control del PNG; Cerro Vicuña) | 3 viviendas |

Hubo inundaciones en 6 de los 16 años del registro, siempre entre enero y abril. Ninguna había causado víctimas hasta 2026.

- **La cañada El Aguacatal ya figuraba en el registro**: en febrero de 2024, una crecida afectó una vivienda y la vía de tercer orden. Según las coordenadas de ese registro, la cañada drena hacia la cuenca de La Cascada (por verificar en campo).
- En 2010, la SNGR registró el desborde de cuatro encañadas en Santa Rosa.

El registro tiene dos límites:
- sus coordenadas son a menudo genéricas: el punto de 2023 cae a 900 m de La Cascada;
- **no incluye los Niños de 1982–83 ni de 1997–98**, así que no permite estimar periodos de retorno de los eventos extremos.

**Instalaciones críticas en Puerto Ayora (La Cascada)** (distancia al barrio; profundidad de la depresión en el DSM):
- UPC La Cascada (8 m; 1,8 m), dañada según la SNGR;
- Iglesia Sagrada Familia (dentro; 1,9 m);
- Escuela Oswaldo Guayasamín (23–68 m; 0,9 m);
- tres servicios de salud a 0–94 m del barrio;
- Centro Médico Matazarnos (205 m);
- **Centro de Salud Santa Cruz del MSP** (278 m; cota ≈16,3 m*). Quedó «incomunicado e inaccesible debido a la inundación de sus instalaciones y vías de acceso» (SitRep 01) e «inoperativo» (SitRep 67). Su cota es mayor que la del rebose del vaso, así que el agua le llegó por las calles o por un cauce urbano que hay que identificar.

**Instalaciones críticas en la parte alta.**

Tabla: Instalaciones de la parte alta junto a cauces (DSM; distancias horizontales).

| Instalación | Cota* | Distancia al cauce derivado del DSM | Área drenada por el cauce | Otras capas |
|---|---|---|---|---|
| **Estadio Gordon Wolf**, Bellavista: **único refugio oficial de la isla** (250 personas) | ≈176 m | **59 m** | ≈7,3–7,7 km² | Dentro de la cuenca de La Cascada |
| Centro de Salud tipo A Bellavista (MSP) | ≈178 m | **11 m** | ≈7,3 km² | HAND media |
| Escuela Caupolicán Marín | ≈183 m | 40–57 m | ≈7,2–7,7 km² | HAND media; anegada en 2023 por colapso de canalones |
| Policía Comunitaria de Bellavista | ≈171 m | 100 m | ≈7,7 km² | HAND media |
| Gobierno Parroquial de Bellavista | ≈182 m | 151 m | ≈7,3 km² | — |
| U. E. Tomás de Berlanga, vía Puerto Ayora–Bellavista | ≈119–128 m | 37–142 m | ≈9,7 km² | Dentro de la cuenca de La Cascada |
| Escuela Julio Puebla | ≈272 m | 15–26 m | ≈1,1 km² | HAND alta |
| Puesto de salud El Cascajo | ≈194 m | 101 m | ≈5,5 km² | — |
| Subcentro de salud y escuela Delia Ibarra, Santa Rosa | ≈412–416 m | > 370 m | < 1 km² | Menor exposición según el DSM |

En Bellavista, **el refugio oficial, el centro de salud, la escuela principal y la policía están a lo largo del mismo cauce de unos 7–8 km²**. Ese cauce es el principal que baja de Bellavista hacia La Cascada. En un evento como el del 30 de octubre, los servicios de respuesta de la parroquia pueden quedar aislados o afectados al mismo tiempo. La exposición real (cota del piso, muros, alcantarillas) debe verificarse en campo: con un error vertical de ±2–4 m, el DSM no permite saber si estos edificios se inundan.

**Refugios.** El registro de la SNGR de 2025 contiene **un único refugio activo en Santa Cruz**: el Estadio Gordon Wolf, en Bellavista, con capacidad para 250 personas. Está en la parte alta y junto a un cauce. Durante el evento se habilitaron de forma improvisada:
- el Coliseo Cerrado de Deportes (100–110 personas, luego 76);
- la Casa de los Mormones (65 personas);
- la Unidad Educativa Nacional Galápagos.

**Al menos dos de esos sitios están en cotas bajas según el DSM** (por verificar en campo):
- el Coliseo de Puerto Ayora, que además es la zona segura de **tsunami**, está en una depresión topográfica;
- la Casa de los Mormones está a ≈11,8 m*, por debajo del rebose del vaso.

Unas 700 personas se fueron con familias acogientes. **Cada amenaza necesita sus propios refugios**, y la red de familias acogientes debe formar parte de la planificación.

## 7.2 Lecciones del evento

La cronología y los factores de alerta están en la sección 2. Aquí se resumen los hechos que sostienen las medidas.

**Hechos confirmados**
- La alerta por El Niño estaba vigente: **naranja** para Puerto Ayora, Bellavista y Santa Rosa desde el 20 de julio (SNGR-193-2026; su art. 5 ordena preparar protocolos de evacuación preventiva) y **roja nacional** desde el 29 de agosto (SNGR-238-2026).
- La advertencia vigente del INAMHI (n.º 84) preveía «eventos leves» en el archipiélago.
- **Lo medido [M]:** entre las 18 y las 21:25 del 30 de octubre cayeron ≥ 143 mm en Los Guayabillos y ≥ 140 mm en Santa Rosa, con máximos de 61–66 mm en una hora de reloj. Las estaciones dejaron de transmitir a las 21:22–21:25.
- Hubo 1 fallecido en la cañada El Aguacatal (Bellavista) y 165 personas en refugios. **Unas 700 personas salieron por sus propios medios** a casas de familias acogientes.
- La alerta roja de corto plazo del INAMHI (n.º 59) se emitió después del evento.

**Hechos por verificar**
- la lámina real de agua en La Cascada (un testigo habló de «hasta dos metros»);
- la hora del desbordamiento de cada cañada y la del fallecimiento;
- si existían planes de evacuación por sector;
- el estado de las alcantarillas, los sumideros y los vados antes del evento;
- la situación de las dos personas reportadas como desaparecidas en el sector Divino Niño.

> **Lección central.** La alerta nacional era genérica y el pronóstico no anticipó la tormenta. Una red de pluviómetros que transmitía en tiempo casi real **sí mostró, 1–2 h antes del máximo**, intensidades propias de un evento extremo. No había umbrales, nadie la vigilaba y no estaba conectada a un protocolo. Además, se apagó en el peor momento.

## 7.3 Medidas no estructurales

**Inmediatas (días)**
- **Marcas de agua y daños** en La Cascada, El Aguacatal, Tomás de Berlanga y Bellavista. Levantarlas con GNSS y fotografía georreferenciada, junto con una encuesta de daños por vivienda y entrevistas sobre las horas de llegada del agua. Es el único dato que permite calibrar los modelos y los umbrales, y se pierde con la limpieza.
- **Rutas de evacuación provisionales**, laterales y sin cruzar cauces ni vados. Se trazan en campo con la comunidad.
- **Refugios.** Revisar la exposición del Estadio Gordon Wolf frente a crecidas y designar edificios sólidos con plantas altas fuera de los cauces y de las depresiones. Descartar el Coliseo para esta amenaza y registrar a las familias acogientes.

**A 3 meses: SAT por lluvia con la red existente**

**¿Habría permitido avisar la red IERSE-WSN el 30 de octubre?** Para la parte baja, **probablemente sí**; para la parte alta, con muy poco margen. Las horas de superación de umbrales ilustrativos se calcularon con datos cada 5 min (`datos/riesgo/umbrales_sat_30oct.csv`).

Tabla: Primera superación de umbrales de lluvia el 30 de octubre (UTC−6) [M]. Umbrales ilustrativos, no oficiales.

| Umbral | Los Guayabillos (parte media, a 0,4 km de la cuenca de La Cascada) | Santa Rosa (oeste) |
|---|---|---|
| ≥ 20 mm en 1 h | 18:41 | 15:07 (primer pulso); 19:17 (segundo) |
| ≥ 30 mm en 1 h | **18:51** | 15:17; 19:32 |
| ≥ 50 mm en 3 h | 19:36 | 15:42 |
| ≥ 50 mm en 1 h | 20:31 | 20:17 |
| ≥ 100 mm en el día | 20:06 | 18:47 |
| Máximo en 1 h móvil | 63,8 mm (hasta las 20:56) | 73,0 mm (hasta las 21:12) |
| Último dato | 21:25 | 21:22 |

Margen que habrían dado estos umbrales:
- **Parte alta** (El Aguacatal, Bellavista, Tomás de Berlanga). Desde el umbral de 30 mm/h en Los Guayabillos (18:51) hasta el máximo de lluvia (20–21 h) pasaron **1–2 h**. Los cauces locales, de 1–10 km², responden en minutos o decenas de minutos. Ese margen solo sirve si el aviso es inmediato y la evacuación es corta y está ensayada.
- **La Cascada.** Según el hidrograma modelado con la lluvia medida [E], el pico llegó entre las 21:40 y las 22:50. El umbral de 30 mm/h habría dado **≈2,8–4 h de margen** hasta el pico, suficiente para evacuar ante la crecida mayor **si alguien vigila la red de noche**. Pero **el vaso se llenó entre las 16:50 y las 18:10**, antes de cualquier umbral: retener 42 000–62 000 m³ equivale a unos 1,5 mm de escorrentía de la cuenca. **Las viviendas del fondo del vaso se inundan con lluvias moderadas.** Para ellas, el SAT no sustituye las medidas permanentes (sin dormitorios en planta baja y reubicación voluntaria; véase la sección de alternativas).
- **El primer pulso de Santa Rosa** (15:17) habría activado una alerta en Santa Rosa, cuyo sector también reportó inundaciones, pero no en La Cascada, porque Santa Rosa no drena hacia ella. **Los umbrales deben asignarse por sector y por estación.**

Tabla: Propuesta de umbrales provisionales y protocolo. Debe validarse con el INAMHI y la SNGR y recalibrarse tras cada temporada.

| Nivel | Criterio, en cualquier estación de cota media del sector | Acción |
|---|---|---|
| **Aviso** | ≥ 20 mm en 1 h, o ≥ 40 mm en 3 h | La UGR municipal y el COE pasan a vigilancia; aviso a los comités barriales; los refugios se preparan |
| **Alerta** | ≥ 30 mm en 1 h, o ≥ 50 mm en 3 h | Evacuación preventiva de las franjas de cauce de la parte alta y de la zona baja de La Cascada; cierre preventivo de los vados y del tramo Parque Artesanal–Bellavista |
| **Alarma** | ≥ 50 mm en 1 h, ≥ 80 mm en 3 h o ≥ 100 mm en el día; **o pérdida de transmisión estando en alerta** | Evacuación general de las zonas expuestas; prohibición de cruzar cauces |

El 30 de octubre, con estos criterios, Los Guayabillos habría pasado a aviso a las 18:41, a alerta a las 18:51 y a alarma a las 20:06.

No se puede estimar la tasa de falsas alarmas. La red tiene datos solo desde abril de 2026, y el día más lluvioso de octubre o noviembre registrado en Bellavista por la FCD fue de 59,5 mm (1997). Los umbrales deben revisarse con la serie que se acumule y con el registro de daños.

**Componentes mínimos del SAT**
1. **Estaciones.** Mantener Los Guayabillos y Santa Rosa y añadir dos pluviómetros telemétricos:
   - uno en Bellavista, dentro de la cuenca de La Cascada;
   - uno en Puerto Ayora.

   Los Guayabillos está fuera de la cuenca (a 0,4 km) y Cerro Crocker apenas registró la tormenta.
2. **Vigilancia 24/7** con responsable asignado, a cargo de la UGR municipal o del ECU 911. Requiere un acuerdo de datos con la Universidad del Azuay (IERSE), con la FCD y con el INAMHI.
3. **Cadena de aviso** del umbral a la acción: alertas automáticas por SMS o mensajería, sirenas o altavoces en La Cascada y Bellavista, comités barriales y COE.
4. **Resiliencia**, la lección del 30 de octubre:
   - energía de respaldo (batería y panel solar) en cada estación;
   - comunicaciones redundantes (celular y radio o satélite);
   - almacenamiento local de los datos;
   - la regla «silencio en alerta = alarma».
5. **Simulacros** con el barrio y la parte alta antes de que avance la temporada. En los Niños fuertes, la lluvia extrema duró de noviembre a junio.

**A 1 año**
- **Mapa oficial de amenaza** por crecida súbita y flujos de lodo en toda la isla (cañadas de la parte alta, cruces con vías y vaso de La Cascada), con LiDAR o dron, curvas IDF y modelación 2D.
- **Normas de uso del suelo** en las franjas de cauce de la parte alta y en el vaso. La LOOTUGS (art. 108, núm. 7, reformado por la LOGIRD) sanciona aumentar el aprovechamiento del suelo en zonas de riesgo no mitigable, lo que exige una declaratoria técnica de ese riesgo.
- **Seguros** (LOGIRD art. 54).
- **Simulacros anuales** antes de la temporada de lluvias.

## 7.4 Gobernanza

Tabla: Actores y competencias en gestión del riesgo.

| Actor | Rol en este caso | Base legal |
|---|---|---|
| SNGR | Ente rector: alertas, estándares de mapas de amenaza y lineamientos del SAT | LOGIRD arts. 23, 56 y 62–64 |
| INAMHI | Red hidrometeorológica y advertencias; organismo técnico-científico del sistema | LOGIRD art. 34 |
| Comité cantonal para la gestión del riesgo | Instancia de prevención y reducción del riesgo, distinta del COE | LOGIRD art. 22 |
| GAD municipal de Santa Cruz | Competencia directa: mapas, monitoreo, ordenamiento del suelo, comités comunitarios de riesgo y alcantarillado pluvial | COOTAD arts. 55 y 140; LOGIRD arts. 9, 21 y 39 |
| GAD parroquial de Bellavista y de Santa Rosa | Análisis de riesgos en su territorio y capacitación comunitaria | LOGIRD art. 9 |
| COE cantonal | Coordina la respuesta y dispone las evacuaciones | LOGIRD arts. 28–29 |
| CGREG | Coordina la gestión de riesgos y las obras en cuencas. Su presidente preside el COE de Galápagos | LOREG arts. 5 y 23; LOGIRD, disposición general octava |
| DPNG y MAATE | Gestión del riesgo en las áreas protegidas; autorización de obras en el Parque | LOREG art. 23 |
| Universidades (Universidad del Azuay–IERSE, USFQ) y FCD | Operación de la red IERSE-WSN, datos y monitoreo; organismos técnico-científicos del sistema, previo registro | LOGIRD art. 34 |

La LOGIRD (R.O. 488, 30-I-2024) se declara alineada con el **Marco de Sendai 2015–2030**. Las cuatro prioridades de Sendai y su meta G (alerta temprana) sirven de estructura para el plan de acción. Para que la red IERSE-WSN funcione como SAT hacen falta tres cosas: un convenio entre el GAD, la SNGR, el INAMHI y la Universidad del Azuay; que su protocolo se ajuste a los lineamientos de la SNGR (LOGIRD art. 62); y que sus datos sean interoperables (art. 56).

## 7.5 Riesgos de las soluciones estructurales

- **Efecto dique («levee effect»).** Reducir las inundaciones frecuentes tiende a aumentar la exposición y a debilitar la preparación, y cuando la obra se supera el daño es mayor (Di Baldassarre et al., 2015). La obra **no sustituye** al SAT ni a la regulación del suelo.
- **Dimensionamiento.** El caudal de diseño es incierto (sección 4). La lluvia medida el 30 de octubre (≥ 179–238 mm en un día, 61–73 mm en una hora) supera con creces los máximos diarios de octubre y noviembre de la serie de la FCD (104,3 mm en Puerto Ayora y 59,5 mm en Bellavista). Sin curvas IDF, una obra puede quedar subdimensionada.
- **Mantenimiento.** Toda obra necesita un responsable y un presupuesto de mantenimiento, que hoy no existen.
- **Sedimentos.** Los flujos de lodo obstruyen alcantarillas, rejillas y vados. En la parte alta esto puede desviar el agua hacia viviendas y vías.
- **Traslado del riesgo.** Un interceptor que descargue al este traslada el caudal y los sedimentos a la zona de la Estación Charles Darwin y la DPNG.
