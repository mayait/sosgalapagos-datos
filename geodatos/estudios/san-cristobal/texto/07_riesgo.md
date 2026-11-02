[[SALTO]]

# 7. Gestión del riesgo de desastres

Esta sección cubre Puerto Baquerizo Moreno y El Progreso. Los datos auxiliares están en `datos/riesgo/` y se regeneran con `scripts/grd_riesgo_islas.py`:
- `instalaciones_criticas.csv`;
- `recurrencia_sngr.csv`;
- `capas_cgreg_resumen.csv`.

Las cotas marcadas con * proceden del DSM Copernicus GLO-30, con un error de ±2–4 m y un sesgo de unos −2 m frente al IGM. **No deben usarse como umbrales normativos.** Los cauces «del DSM» se derivaron con un umbral de 0,5 km² de área drenada. Su trazado en la ciudad, con edificios y calles, es aproximado.

## 7.1 Caracterización del riesgo

**Amenaza.** Puerto Baquerizo Moreno está atravesado por **encañadas que bajan del cerro hacia la bahía**. Un estudio de la USFQ identifica tres principales: **Barrio Frío, Divino Niño y Escuela Alvear**. Se inundan en la época de lluvias (enero a junio). La correspondencia con los cauces derivados del DSM se propone como hipótesis por verificar en campo:

Tabla: Cauces urbanos principales según el DSM (hipótesis de correspondencia con los nombres locales).

| Cauce del DSM (área drenada) | Probable nombre local | Recorrido urbano | Edificios a ≤ 15 m del eje | Registros SNGR cercanos |
|---|---|---|---|---|
| ≈10,5–11 km²; desemboca hacia el Malecón | **Barrio Frío** | ≈1,0 km | ≈108 | Barrio Frío 2012, 2024 (a 52 m) y 2025 (Malecón) |
| ≈8–9,4 km²; sector sureste | Encañada de El Manzanillo | ≈0,55 km | ≈45 | Manzanillo 2011, 2019 y 2023 (a 18–49 m); La Planada 2025 |
| ≈1,0–1,6 km²; pasa junto a la Iglesia Divino Niño hacia Playa Mann | **Divino Niño** | ≈0,7 km | ≈67 | Divino Niño 2010, 2011 y 2012 (coordenadas genéricas) |
| ≈0,7 km²; pasa junto a la Escuela Alejandro Alvear hacia Playa Mann | **Escuela Alvear** | ≈0,3 km | ≈7 | Playa Mann y U. E. Alejandro Alvear, 2023 (a 10 m) |

**Capas del CGREG.**
- **Flujos de lodo y escombros por El Niño**: 2 polígonos (47,3 ha):
  - uno de 10,2 ha al noreste del centro, en el entorno de Divino Niño, con 77 edificios;
  - otro de 37,1 ha en el sector de El Manzanillo, con 158 edificios.
- **Franja de protección de 20 m de quebradas**: incluye 172 edificios de la isla. **Apenas coincide con los cauces urbanos del DSM**: cubre 22 de los ≈1 000 m del cauce de Barrio Frío en la ciudad y 33 de los ≈700 m del de Divino Niño. O la franja se trazó sobre otra red de quebradas, o los cauces urbanos están canalizados o desviados. Hay que aclararlo.
- **Otras capas**: derrumbes (2 polígonos; 13,3 ha), contaminación de acuíferos (3; 64,7 ha) y explosión o derrame de combustible (5; 10 ha).

**Recurrencia.** El registro de la SNGR (2010–2025) contiene **16 inundaciones con fecha** en San Cristóbal, más que en Santa Cruz (12). A ellas se suman 3 deslizamientos, 1 aluvión (El Junco, 2023) y 1 socavamiento (vía a Cerro Gato, 2012).
- **Puerto Baquerizo Moreno** concentra la mayoría:
  - Divino Niño: 3 registros (2011–2012);
  - Barrio Frío y Malecón: 3 (2012, 2024 y 2025);
  - El Manzanillo: 3 (2011, 2019 y 2023);
  - Playa Mann, La Planada y Puerto Chino.
- **El Progreso** tiene 3:
  - la vía a Cerro Verde, en 2016;
  - el dispensario del IESS, en 2021;
  - la Escuela Carlos Darwin, con dos aulas inundadas, en 2024.
- La mayor afectación registrada es de **12 viviendas** (El Manzanillo, 2019) y de **8 familias** (Barrio Frío, 2012). No hay víctimas registradas.
- En febrero de 2010, la SNGR anotó en Divino Niño una lluvia de «100,1 mm» en una hora y media (dato de radiosonda).

Los registros de 2010–2012 tienen todos la misma coordenada genérica. El de marzo de 2024 (Av. Antonio Gil) está asignado por error a Puerto Villamil.

**Instalaciones críticas.**

Tabla: Instalaciones críticas de Puerto Baquerizo Moreno y El Progreso (DSM; distancias horizontales).

| Instalación | Cota* | Cauce del DSM más cercano | Otras capas | Observación |
|---|---|---|---|---|
| **USFQ / Galapagos Science Center** | ≈9–12 m | 82 m (0,3 km²); 252 m (0,7 km², Escuela Alvear); 380 m (1,6 km², Divino Niño) | Flujos de lodo del CGREG a 357 m; franja a 405 m; una parte en la zona de tsunami del INOCAR | Inundación de 2023 en Playa Mann, a 309 m. No está en una depresión del DSM |
| **Hospital Oskar Jandl**, ubicación según OSM | ≈27 m | **2–7 m** (1,0–1,6 km², Divino Niño) | HAND media | **Las dos fuentes no coinciden**: la ubicación del MSP está 1,3 km al suroeste (≈13 m*; a 233 m del cauce de Barrio Frío). Hay que verificarla |
| Alcaldía de San Cristóbal | ≈6 m | 12 m (≈11 km², Barrio Frío) | — | Sede del COE cantonal (por verificar) |
| Capitanía de Puerto | ≈4 m | 28 m (≈11 km²) | **Dentro** del polígono de flujos de lodo | — |
| Escuela Alejandro Alvear | ≈15–16 m | 40–49 m (0,7 km²) | Zona de tsunami | Cancha inundada en 2023 (SNGR) |
| U. E. Fiscomisional San Cristóbal | ≈23 m | 56 m (≈11 km²) | — | — |
| Comando de Policía Galápagos n.º 20 | ≈6 m | 195 m | Zona de tsunami | — |
| Escuela Carlos Darwin, El Progreso | ≈316 m | 37–47 m (0,7 km²) | Depresión del DSM de 0,4–1,4 m | Inundada en 2024 (SNGR) |
| Centro de salud El Progreso | ≈315 m | 175–200 m | — | El dispensario del IESS se inundó en 2021 |

**Refugios.** El registro de la SNGR de 2025 contiene **4 refugios activos en San Cristóbal, con capacidad para 358 personas en total**:
- **Estadio Olímpico Luis Cruz Sayo**, en Puerto Baquerizo Moreno (147 personas; ≈18,5 m*). Está a **66 m de un cauce de 1,6 km²** y a menos de 150 m del de Barrio Frío. Es el único refugio oficial de la ciudad y su exposición a crecidas debe verificarse;
- Estadio Juan Olaya Mora, en El Progreso (89 personas; ≈317 m*; a 79 m de un cauce de 0,7 km²);
- Finca Santa Mónica, administrada por la Armada (90 personas; ≈401 m*);
- Escuela Alejandro Humboldt, en La Soledad (32 personas; ≈376 m*).

Dos zonas seguras de **tsunami** no sirven para crecidas:
- el Liceo Naval (≈12 m*), a 7 m de un cauce de ≈10,5 km² y dentro del polígono de flujos de lodo;
- el Parque Martha Bucaram de Roldós (≈15 m*), dentro del polígono de flujos de lodo y de la franja de 20 m.

Como en Santa Cruz, **cada amenaza necesita sus propios refugios**.

## 7.2 El evento de 2026 en San Cristóbal

Lo reportado por la SNGR [R]:
- **16 de octubre de 2026.** Se activó un refugio temporal en el «Barrio Estación Terrena», ya cerrado al 1 de noviembre (SitRep 67). Esto indica un evento previo en la isla, cuyos detalles no se encontraron (por verificar).
- **31 de octubre, por la mañana**, la mañana siguiente al máximo medido en Santa Cruz:
  - desbordamiento de las cañadas **Barrio Frío y Divino Niño**, con calles anegadas en el casco urbano y afectación a varias familias;
  - la desembocadura afectó la playa «Los Marinos», con riesgo de arrastrar embarcaciones;
  - la SNGR registró el nivel del cuerpo hídrico de Barrio Frío como «con tendencia a subir» (SitRep 01).
- **1 de noviembre (SitRep 67).** «Tras el cese de las precipitaciones, no se registran vías inundadas ni reportes de viviendas afectadas». El evento figura como **finalizado**.

**No hay lluvia medida en San Cristóbal.** La red IERSE-WSN solo tiene estaciones en Santa Cruz, y no se encontraron datos públicos del INAMHI ni de otras redes para el evento. Por tanto, no se puede decir qué intensidad desbordó las cañadas ni si hubo margen para avisar.

## 7.3 Medidas no estructurales

**Inmediatas (días)**
- **Marcas de agua y daños** de Barrio Frío, Divino Niño y la desembocadura, con GNSS y fotografías, junto con entrevistas sobre las horas.
- **Verificar la ubicación del Hospital Oskar Jandl** y su exposición al cauce de Divino Niño. Revisar sus accesos, porque en Santa Cruz el centro de salud principal quedó inaccesible.
- **Revisar los refugios**: la exposición del Estadio Luis Cruz Sayo y los sitios alternativos fuera de cauces.
- **Limpiar** las desembocaduras, rejillas y alcantarillas de las tres encañadas antes de nuevas lluvias.

**3 meses**
- **SAT por lluvia.** Instalar al menos dos pluviómetros telemétricos (El Progreso, a ≈300 m, y la parte alta hacia El Junco), más uno en la ciudad. Pueden integrarse en la red IERSE-WSN, con umbrales y un protocolo análogos a los de Santa Cruz (véase el estudio de Santa Cruz, sección 7.3).
  - Las cuencas urbanas son pequeñas (0,7–11 km²) y responden en minutos. El aviso debe basarse en la lluvia medida en la parte alta y en las alertas del INAMHI, no en el nivel del agua.
  - La USFQ / Galapagos Science Center puede alojar una estación y aportar personal de vigilancia (por verificar si ya dispone de una).
- **Simulacro** en Barrio Frío, Divino Niño y El Manzanillo.

**1 año**
- **Mapa oficial de amenaza** de las encañadas urbanas, con LiDAR o dron y modelación 2D, para conciliar la franja del CGREG con los cauces reales.
- **Normas de uso del suelo** en las franjas de cauce (LOOTUGS art. 108, núm. 7).
- **Plan de mantenimiento** de las encañadas canalizadas y de sus desembocaduras.

## 7.4 Gobernanza

Puerto Baquerizo Moreno es la **capital provincial**. Allí tiene su sede el **Consejo de Gobierno del Régimen Especial (CGREG)**, cuyo presidente preside el comité provincial de gestión del riesgo y el COE provincial (LOGIRD, disposición general octava). El CGREG también coordina la gestión de riesgos y las obras en cuencas (LOREG arts. 5 y 23).

Tabla: Actores y competencias en San Cristóbal.

| Actor | Rol | Base legal |
|---|---|---|
| GAD municipal de San Cristóbal (UGR) | Competencia directa: mapas, monitoreo, ordenamiento del suelo, alcantarillado pluvial y comités comunitarios | COOTAD arts. 55 y 140; LOGIRD arts. 9, 21 y 39 |
| COE cantonal | Coordina la respuesta y dispone las evacuaciones | LOGIRD arts. 28–29 |
| GAD parroquial de El Progreso | Análisis de riesgos y capacitación comunitaria en la zona rural | LOGIRD art. 9 |
| CGREG y COE provincial | Coordinación provincial; su presidente preside el COE de Galápagos | LOREG arts. 5 y 23; LOGIRD, disposición general octava |
| SNGR (UMEVA Galápagos) | Monitoreo, informes de situación, lineamientos del SAT y estándares de mapas | LOGIRD arts. 23, 56 y 62 |
| INAMHI | Advertencias y red hidrometeorológica | LOGIRD art. 34 |
| DPNG y MAATE | Las cabeceras de las encañadas están en el Parque Nacional; autorización de obras | LOREG art. 23 |
| Armada (Capitanía, II Zona Naval) | Respuesta; administra el refugio Finca Santa Mónica; desembocaduras y embarcaciones | Ley de Seguridad Pública y del Estado |
| USFQ / GSC | Organismo técnico-científico (previo registro): datos, monitoreo y apoyo al SAT | LOGIRD art. 34 |

## 7.5 Riesgos de las soluciones estructurales

El estudio de la USFQ citado compara alternativas de obra para las encañadas: embalses, desvío y micro-embalses. Valen las mismas advertencias que en Santa Cruz:
- **efecto dique**: la obra reduce los eventos frecuentes y aumenta la exposición;
- **dimensionamiento** sin curvas IDF ni lluvia medida;
- **mantenimiento**, que necesita un responsable y presupuesto;
- **sedimentos** que obstruyen las desembocaduras canalizadas;
- **traslado del riesgo** hacia la bahía: playa y embarcaciones.

## Fuentes de esta sección

- SNGR, SitRep n.º 01 de Galápagos (31-oct-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SITREP-Nro.-01-Lluvias_Galapagos_29.08.2026-31.10.2026.pdf
- SNGR, SitRep 67 nacional (1-nov-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SitRep-No-67-Lluvias-29082026-al-01112026-15h00f21.pdf
- USFQ, estudio de las encañadas de Puerto Baquerizo Moreno (Barrio Frío, Divino Niño y Escuela Alvear): https://repositorio.usfq.edu.ec/bitstream/23000/10220/1/138016.pdf
- LOGIRD: https://procuraduria.utpl.edu.ec/NormativaExterna/LEY%20ORG%C3%81NICA%20PARA%20LA%20GESTI%C3%93N%20INTEGRAL%20DEL%20RIESGO%20DE%20DESASTRES.pdf
- LOREG: https://faolex.fao.org/docs/pdf/ecu166165.pdf
- Datos: `capas/final/` (eventos SNGR, refugios SNGR 2025, MSP, MINEDUC, OSM, CGREG, INOCAR) y DSM Copernicus GLO-30.
