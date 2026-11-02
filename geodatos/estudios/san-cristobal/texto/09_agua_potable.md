[[SALTO]]

# 9. Agua potable: tomas, conducciones y riesgos

> **PRELIMINAR.** Ninguna toma se ha visitado. Las ubicaciones se reconstruyeron cruzando la cartografía del IGM 1:25 000, la capa de captaciones de la FCD/CGREG, OSM, un registro de la SNGR y documentos técnicos. Cada punto lleva su fuente y una **confianza en la ubicación**. Las cotas proceden del DSM GLO-30 (±2–4 m; sesgo ≈ −2 m) y son solo descriptivas.

## 9.1 Ubicación de las tomas

**Qué se sabe del sistema.** El sistema municipal de Puerto Baquerizo Moreno y El Progreso se abastece de **manantiales y cañadas de la parte alta**, en la vertiente sur de barlovento. No usa la laguna El Junco, que según la USFQ no es una fuente de consumo humano.

Las fuentes coinciden en estas tomas:

- **Cerro Gato:** 27 l/s; alimenta la **planta Las Palmeras**.
- **Toma de Los Americanos:** 19 l/s.
- **La Toma:** alimenta la **planta El Progreso**.
- **El Chino:** 20 l/s.

Los caudales son del CGREG (2015) y la asignación de cada toma a su planta es de la USFQ. El CGREG cita además El Plátano (6 l/s), La Policía (6 l/s), La Honda (30 l/s) y Las Goteras, y cuenta unos 30 manantiales permanentes en la isla. Según el GAD, recogido por *Bitácora Ecuador* (2021), hay cuatro captaciones —Chuquimarca, Cerro Gato, Los Americanos y El Platanal— que suman unos 30 l/s; Chuquimarca aún no estaba operativa. Hay que confirmar con el GAD cuáles de todas están en servicio en 2026.

Tabla: Tomas y fuentes de agua localizadas (`datos/agua/tomas.geojson`, `fuentes_agua.csv`). Confianza: alta = el objeto está cartografiado y otra fuente lo confirma a ≤ 350 m; media = una sola fuente cartográfica o una coordenada administrativa; baja = solo toponimia.

| Id | Toma | Lon, lat | Cota* (m) | Tipo | Abastece | Caudal (l/s) | Confianza | Fuentes de la ubicación |
|---|---|---|---|---|---|---|---|---|
| AG-01 | **Cerro Gato** | −89,4787; −0,9200 | ≈267 | Manantial o cañada | Planta Las Palmeras → Puerto Baquerizo Moreno | 27 | **Media** (aproximada) | Inicio de la línea IGM «Proyecto de agua Cerro Gato» y tanque IGM en el mismo punto; topónimo IGM a 0,4–0,7 km |
| AG-02 | **Los Americanos** | −89,4873; −0,9134 | ≈407 | Represa pequeña sobre una cañada | Red de Puerto Baquerizo Moreno | 19 | **Media** (aproximada) | Coordenada del registro SNGR del aluvión de 2023 («El Junco – Finca Las Carmelitas») |
| AG-03 | **La Toma** | −89,5064; −0,9116 | ≈503 | Captación con reservorio | Planta El Progreso → El Progreso y el puerto | — | **Alta** | Captación FCD; reservorio IGM a 250 m; topónimo IGM «La Toma» a 330 m; fin de la línea IGM «Pampas Mías» a 150 m |
| AG-04 | El Chino (manantial) | −89,4571; −0,9019 | ≈296 | Manantial | Red rural; conducción IGM de 3,3 km | 20 | Media | Manantial IGM, origen de una línea enterrada; captación FCD a 275 m |
| AG-08 | Vertiente Las Goteras | −89,4771; −0,8842 | ≈581 | Manantial | No documentado | — | Alta (manantial) | Manantial IGM con nombre |
| AG-09 a 11 | 3 captaciones FCD sin nombre | Ver el CSV | 326–422 | Captación | No documentado | — | Media | Capa de captaciones FCD/CGREG |
| AG-05 a 07 | El Chino, J Chico, La Piscina | Ver el CSV | 393–561 | Pozas o reservorios | No documentado | — | Alta | FCD y reservorio IGM |

\* Cota del DSM.

**Instalaciones aguas abajo:**

- **Planta El Progreso** (AG-P1; ≈339 m*): IGM y OSM. Confianza alta.
- **Planta y tanques Las Palmeras** (AG-P2; ≈82 m*): 4 tanques del IGM y 4 de OSM. Confianza alta.
- **Tanque Cerro Patricia** (AG-T1; ≈56 m*): confianza media. De él sale la red hacia el puerto.
- **Tanques de Cerro Verde** (AG-T2).

**Advertencias:**

1. **Las cotas no coinciden.** La USFQ da 164 m para Cerro Gato y 150 m para La Toma. En los puntos de este inventario, el DSM da ≈267 m y ≈500 m. O los puntos de la USFQ son otros (por ejemplo, de muestreo), o lo son los de este inventario. Hay que resolverlo con GNSS.
2. **La ubicación de Los Americanos es frágil.** Viene de la coordenada de un registro de evento, a ≈170 m de la quebrada IGM más cercana, y el DSM no muestra un cauce en el punto. La represa puede estar a decenas o cientos de metros.
3. **AG-01 es el inicio de una línea**, no una captación etiquetada como tal.

## 9.2 Infraestructura

**Conducciones cartografiadas.** El IGM registra 10 líneas de acueducto en la isla (`datos/agua/conducciones.geojson`). OSM no tiene tuberías.

Tabla: Conducciones del IGM y sus cruces con cauces y vías (cruces con cauces D8 de ≥ 0,1 km² y quebradas IGM/OSM, deduplicados a 40 m).

| Conducción (IGM) | Estado (IGM) | Longitud | Desde → hasta | Cruces con cauces (≥ 0,5 km²) | Cauce mayor cruzado | Cruces con vías | En la franja CGREG de 20 m | En polígonos de riesgo del CGREG |
|---|---|---|---|---|---|---|---|---|
| «Proyecto de agua Cerro Gato» | En construcción, enterrada | 16,7 km | Cerro Gato (≈270 m) → Las Palmeras (≈83 m) | 42 (21) | 7,1 km² a ≈91 m* | 9 | 1,65 km | Ninguno |
| «Proyección Agua Potable Pampas Mías» | En construcción, enterrada | 6,0 km | La Toma (≈503 m) → planta El Progreso (≈333 m) | 13 (6) | 1,4 km² | 9 | 0,25 km | Ninguno |
| Sin nombre (El Chino) | Funcionando, enterrada | 3,3 km | Manantial El Chino (≈296 m) → sureste (≈110 m) | 4 (4) | 5,1 km² | 4 | 0,04 km | Ninguno |
| Sin nombre (Cerro Verde) | Funcionando, enterrada | 9,7 km | Origen sin identificar (≈223 m) → tanques de Cerro Verde | 15 (6) | 2,3 km² | 4 | 0,39 km | Ninguno |
| **Sin nombre (red al puerto)** | Funcionando, en superficie | 1,5 km | Cerca del tanque Cerro Patricia (≈53 m) → Malecón (≈4 m) | 8 (7) | **10,5 km² (Barrio Frío)** | 8 | 1,27 km | **Flujos de lodo por El Niño: 1,45 km** |
| Otras 5 líneas cortas (norte y este de la isla, desembocadura de Barrio Frío) | Funcionando | 0,1–1,5 km | Origen y destino no identificados | — | Hasta 17 km² | — | — | Desembocadura de Barrio Frío: 92 m en flujos de lodo |

**Lo que no está cartografiado y se deja como desconocido** (sin geometría en `conducciones.geojson`):
- la conducción desde Los Americanos;
- la conducción entre la planta El Progreso y Puerto Baquerizo Moreno;
- el estado actual de las dos líneas que el IGM da como «en construcción». No se sabe si hoy son las conducciones en servicio.

No se inventó ningún trazado.

**Accesos.** Distancia de cada toma a la vía OSM más cercana:

| Toma | Distancia | Tipo de vía |
|---|---|---|
| Cerro Gato | ≈470 m | Camino sin clasificar |
| Los Americanos | ≈150 m | Pista |
| La Toma | ≈120 m | Pista |
| El Chino | ≈15 m | Pista |

Todas están en laderas con pendientes medias del 12–31 % (DSM). En 2012, el colapso de una alcantarilla en la «vía principal del sector Cerro Gato» cortó el acceso (registro de la SNGR). El acceso a las tomas en temporada de lluvias es, por tanto, un punto débil propio del sistema.

## 9.3 Riesgos

**1. Aluvión en la toma.** **Ya ocurrió y dejó a la ciudad con agua racionada.**
- El 15-abr-2023, un aluvión **arrastró lodo y lechuguines** (jacinto de agua) y **obstruyó una válvula de la represa de Los Americanos**.
- El COE cantonal declaró **en emergencia el sistema de agua potable** del 17-abr al 8-may-2023, durante 21 días. La distribución se redujo por horas y hubo **112 familias (325 personas)** afectadas indirectamente (SNGR, SITREP 01 y 03).

Las tomas son represas pequeñas o captaciones de cañada en laderas empinadas. Ese es el modo de fallo más probable en un evento como el de octubre de 2026: **sedimento y vegetación que colmatan la toma o la válvula**, más que la rotura de la obra.

**2. Cruces de las conducciones con las cañadas.**
- La línea de Cerro Gato cruza **42 cauces**, 21 de ellos de 0,5 km² o más (hasta 7 km²), y discurre **1,65 km dentro de la franja de quebradas del CGREG**.
- Una tubería enterrada que cruza una cañada queda expuesta donde la crecida socava el lecho. No hay datos de profundidad ni de protección en esos cruces.
- **La red que baja al puerto discurre 1,45 km dentro del polígono de flujos de lodo del CGREG** y a lo largo de la encañada de Barrio Frío (10,5 km²). Es el tramo de mayor exposición a crecidas del sistema.

**3. Plantas y tanques.**
- **Las Palmeras** está a ≈150 m de un polígono de flujos de lodo y a ≈100 m de uno de contaminación de acuíferos, ambos del CGREG.
- **El tanque Cerro Patricia** queda dentro de un polígono de «explosión de combustible, derrames e incendios» del CGREG.
- La planta El Progreso no tiene polígonos de riesgo del CGREG a menos de 500 m.

**4. Calidad.**
- Hay coliformes fecales en las cañadas (USFQ) y, según un estudio de la USFQ de 2014 y reportes del PNG recogidos por la prensa, también a la salida de las plantas y en los hogares.
- En 2014, el GAD alertó de una presunta contaminación de la red de Puerto Baquerizo Moreno (SNGR).
- Tras una crecida, la turbidez y la carga orgánica suben: **las plantas de coagulación y filtración pueden tener que parar**, aunque la toma no sufra daños.

**5. Cuencas de captación.** Las tomas tienen cuencas pequeñas según el D8: 0,6 km² en Cerro Gato, 1,3 km² en La Toma y 4,9 km² en El Chino. En Los Americanos el D8 no muestra un cauce en el punto. Las cuencas están ocupadas en parte por fincas y pastos; Galápagos Conservancy financia la restauración de la cuenca de Cerro Gato con caña guadúa y *Miconia*. Su delimitación se trata en la subsección del hidrólogo.

**El evento de octubre de 2026.** No se encontró **ninguna información pública** sobre afectaciones al sistema de agua potable de San Cristóbal (búsqueda del 2-nov-2026). Lo que sí está documentado:
- hubo lluvia fuerte en la isla el 30 y el 31-oct (sección 3);
- el CGREG trabajó con maquinaria en varias encañadas (prensa del 1-nov);
- en Santa Cruz se suspendió el suministro de agua en Puerto Ayora.

**Que no haya noticias no quiere decir que no haya habido daños.** Con el precedente de 2023, conviene **preguntar al GAD por el estado de las tomas de Los Americanos y Cerro Gato, de sus válvulas y de la turbidez en las dos plantas**.

**Recomendaciones:**
1. **Inmediato:** inspeccionar las tomas, las válvulas y los cruces de la línea de Cerro Gato con cauces de más de 2 km². Medir la turbidez en las plantas.
2. **Semanas:** levantar con GNSS las tomas, la represa de Los Americanos y las conducciones reales para corregir este inventario.
3. **Meses:**
   - incorporar desarenadores y rejillas con limpieza programada;
   - instalar válvulas de purga accesibles;
   - proteger los cruces de tubería con cauces;
   - mantener los accesos a las tomas transitables en temporada de lluvias.
4. **Plan de contingencia:** reservas en tanques, distribución con tanqueros y comunicación de los horarios, a partir de lo aprendido en 2023.

<!-- Subsección «Cuencas de captación»: la añade el hidrólogo de San Cristóbal. -->

**Fuentes:**
- IGM 1:25 000, WFS de Galápagos: acueducto, manantial, tanque, estanque y toponimia.
- FCD/CGREG GeoNode: captaciones de agua.
- OSM: planta El Progreso (way 1548803171) y tanques de Las Palmeras.
- SNGR: registros de eventos 2010–2025; [SITREP 01 de 2023](https://www.gestionderiesgos.gob.ec/wp-content/uploads/2023/06/SITREP_Nr.-01_Epoca_Lluviosa_01012023_-Galapagos-.-..pdf) y [SITREP 03 de 2023](https://www.gestionderiesgos.gob.ec/wp-content/uploads/2023/09/SITREP_Nr.-03_Epoca_Lluviosa_01012023_a_31082023-1.pdf).
- CGREG (2015), [estudio de preinversión del recurso hídrico subterráneo](https://www.gobiernogalapagos.gob.ec/wp-content/uploads/downloads/2015/07/LINK-3.1Proyecto-H%C3%ADdrico-Planificaci%C3%B3n_-VS8.pdf).
- USFQ/GSC, [«Agua para Galápagos»](https://revistas.usfq.edu.ec/index.php/esferas/article/download/2026/2344?inline=1).
- [Galápagos Conservancy (2024), Cerro Gato](https://www.galapagos.org/newsroom/remarkable-benefits-of-reviving-a-critical-water-source/).
- [Bitácora Ecuador](https://www.bitacoraec.com/post/por-qu%C3%A9-en-gal%C3%A1pagos-se-bebe-agua-con-excrementos).
- [Vistazo, 1-nov-2026](https://www.vistazo.com/actualidad/2026-11-01-galapagos-amanece-lluvias-diferente-intensidad-ayuda-humanitaria-santa-cruz-electricidad-OD11300806).

**Archivos:** `datos/agua/tomas.geojson`, `conducciones.geojson`, `fuentes_agua.csv`, `cruces_conducciones.csv` y `diagnostico.json`. Se generan con `scripts/16c_agua_san_cristobal.py`.
