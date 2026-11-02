[[SALTO]]

## 6.6 Los lugares del Plan de Acción de la UGR en el mapa

> **PRELIMINAR.** Esta subsección ubica y contrasta, **desde lo urbano**, los lugares y medidas del *Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal*. Ni la asignación de las cañadas oficiales a los cauces ni la integración del plan en la gestión del riesgo se tratan aquí: corresponden a la sección 4 (hidrología) y a la sección 7 (riesgo).

### Qué se ubicó y con qué fiabilidad

El plan nombra unos 45 lugares. **Se ubicaron 31**, con las fuentes registradas en cada caso:
- 28 puntos;
- la Vía Perimetral Jaime Roldós, como línea;
- la zona urbana de El Progreso y el poblado de Puerto Velasco Ibarra, como polígonos.

Las fuentes son OSM, la toponimia y las capas del IGM 1:25 000, las localidades del INEC, el MSP, el MINEDUC y las coordenadas de registros de la SNGR. La confianza de la ubicación es alta en 14 lugares, media en 11 y baja en 6.

**Hay 14 lugares que no figuran en ninguna fuente** y no se ubicaron (`datos/ugr/no_localizados.csv`):
- en Puerto Baquerizo Moreno: los talleres del CGREG, la Estación Terrena, el sector El Manantial, los barrios San Francisco y Fragata, Los Arrayanes, **La Picada**, el patio de contenedores y el Parque Artesanal;
- en Floreana: La Lobería, las cañadas La Hormiga y La Varonesa, la desalinizadora, la bodega parroquial, el ABG y las oficinas del PNG.

**Hay cuatro casos dudosos**:
- **Hospital Oskar Jandl.** OSM y el MSP lo sitúan a 1,3 km de distancia. Se usó el punto de OSM porque el plan sitúa el hospital en el barrio Divino Niño, junto al Colegio Ignacio Hernández, y eso coincide con OSM.
- **Playa y Poza de las Garzas.** No tiene topónimo. Se ubicó en la desembocadura del cauce de Barrio Frío porque el plan la describe como «punto final de la cañada Galápagos».
- **«El puente» de Manzanillo.** Se supone que es el puente de OSM de la Vía Perimetral sobre el cauce de El Manzanillo (cruce CR-SCR-0011).
- **Los Arroyos.** El poblado del IGM está 9 km al este y no encaja con el recorrido de la cañada Galápagos que describe el plan.

![Lugares y medidas del Plan de Acción SC-4-09-2026 ubicados en Puerto Baquerizo Moreno, sobre los cauces D8 y la franja del CGREG.](figuras/f_plan_ugr.png)

### Medidas del plan trazadas

Todas son **aproximaciones sobre el cauce D8**. El plan no da trazados (`datos/ugr/medidas_plan.geojson`).

- **Zanja de 1 040 m en Manzanillo.** Se trazó a lo largo del cauce de El Manzanillo (8–9 km²), aguas arriba del puente de la Vía Perimetral. Pasa junto a la Ciudadela El Gran Maestro. La incertidumbre es alta: no se sabe dónde empieza ni dónde acaba.
- **Limpieza en La Picada** (170 m en el PNG y 240 m urbanos). Se trazó sobre el cauce que cruza el límite del PNG a unos 50 m del barrio Palmeras. La incertidumbre es muy alta, porque La Picada no está localizada. Según el D8, ese cauce es la parte alta del mismo sistema de El Manzanillo.
- **Desembocadura de Playa de Oro.** Es la salida al mar del cauce de Divino Niño (1,5 km²), junto a la playa. La incertidumbre es de unos ±50 m.
- **Muro del hospital (240 m).** Se trazó como 240 m del cauce de Divino Niño centrados en el hospital de OSM, que está a **15 m** del cauce del DSM.
- **Conexión de las cañadas de Floreana (500 m).** No se pudo trazar: las cañadas no están cartografiadas y en este proyecto no hay DEM procesado de Floreana.

### Contraste con el diagnóstico urbano

Para cada lugar de prioridad máxima se contaron los edificios y la población del INEC, los cruces quebrada–vía de la sección 5 y la cobertura de la franja del CGREG, todo en un radio de 150 m. El radio sirve para comparar lugares entre sí; no delimita el barrio.

Tabla: Sectores de prioridad máxima del plan frente al diagnóstico urbano (radio de 150 m; población del INEC repartida por área de techo).

| Sector del plan | Confianza | Edificios / personas | Cruces (prioridad alta; con estructura) | Franja CGREG en el radio | Cauce de la sección 6.2 (distancia) |
|---|---|---|---|---|---|
| Playa y Poza de las Garzas | Baja | 136 / ≈190 | 5 (1; 3 puentes) | 8 %; a 30 m | Barrio Frío, 10,6 km² (sobre él) |
| Barrio Frío | Media | 108 / ≈170 | 4 (2; 3 puentes) | 5 %; a 120 m | Barrio Frío (90 m) |
| Playa de Oro | Alta | 112 / ≈230 | 5 (2; 0) | 0 %; a 200 m | Divino Niño, 1,5 km² (80 m) |
| Hospital Oskar Jandl | Media | 123 / ≈380 | 4 (3; 0) | 14 %; a 56 m | Divino Niño (15 m) |
| Colegio Ignacio Hernández | Alta | 61 / ≈230 | 1 (0; 0) | 0 %; a 300 m | Divino Niño (200 m) |
| Barrio Divino Niño | Media | 151 / ≈480 | 3 (2; 0) | 0 %; a 170 m | Divino Niño (100 m) |
| Barrio Playa Mann | Media | 73 / ≈40 | 1 (1; 0) | 0 %; a 270 m | Escuela Alvear, 0,7 km² (140 m) |
| Barrio Manzanillo | Media | 58 / ≈130 | 3 (0; 0) | 0 %; a 330 m | El Manzanillo, 8,7 km² (210 m) |
| Ciudadela El Gran Maestro | Baja | 96 / ≈240 | 3 (2; 0) | 9 %; a 110 m | El Manzanillo (30 m) |
| Puente de Manzanillo | Baja | 57 / ≈190 | 2 (1; 2 puentes) | 17 %; sobre ella | Sistema Barrio Frío–Manzanillo |
| Barrio Palmeras | Media | 52 / ≈90 | 5 (0; 0) | 0 %; a 400 m | Afluente alto, 1,6 km² (50 m) |
| Sector La Planada | Media | 69 / ≈150 | 5 (1; 0) | 0 %; a 400 m | Afluente alto, 1,6 km² (90 m) |

**Lectura:**

1. **El plan y el diagnóstico de gabinete coinciden en los ejes.**
   - Los sectores de prioridad máxima se agrupan en torno a tres sistemas de cauce de la sección 6.2: **Barrio Frío y El Manzanillo**, **Divino Niño** y **los afluentes altos** de Palmeras y La Planada.
   - Los dos sectores de mayor densidad, Divino Niño y el entorno del hospital, con unas 380–480 personas en 150 m, están sobre el cauce más ocupado del diagnóstico: Divino Niño, con 16 edificaciones sobre la línea.
2. **La franja del CGREG casi no cubre los sectores prioritarios.**
   - Solo toca, en parte, cinco de los doce: Garzas, Barrio Frío, el hospital, El Gran Maestro y el puente.
   - **No cubre en absoluto** Playa de Oro, Divino Niño, Playa Mann, Manzanillo, Palmeras ni La Planada. Varios de ellos son los que el plan da como más afectados en 2025–2026.
   - Esto confirma lo dicho en la sección 6.2: la franja vigente no protege los tramos urbanos que más se inundan.
3. **Los pasos de vía de los sectores altos no tienen estructura cartografiada.**
   - En La Planada, Palmeras, Manzanillo y Divino Niño ninguno de los cruces a menos de 150 m tiene puente ni alcantarilla cartografiados.
   - Las únicas estructuras están en el tramo bajo de Barrio Frío y en la Vía Perimetral.
   - El plan describe desbordes «a 100 m del puente» y desembocaduras tapadas: son puntos donde la sección hidráulica disponible es la que manda.
4. **El Progreso.**
   - El plan cuenta **43 viviendas y 124 personas expuestas directamente**.
   - En la zona urbana hay 183 edificios y unas 250 personas (INEC), y un cauce de 0,74 km² pasa con **16 edificios a menos de 15 m** (sección 6.2).
   - Las dos cifras son compatibles si la del plan se refiere a los sectores bajos y a la franja del cauce.
5. **Floreana.** No hay manzanas del INEC ni huellas de edificios en Puerto Velasco Ibarra en las capas del proyecto, y las cañadas no están cartografiadas. Solo se pudo ubicar el poblado, Playa Negra, el dispensario y la central eléctrica.

**Para la UGR:**
- validar en campo los lugares de confianza baja o no localizados, empezando por La Picada, El Manantial, las Garzas y «el puente»;
- entregar los trazados reales de la zanja de 1 040 m, del muro de 240 m y de la conexión de 500 m en Floreana, para sustituir las aproximaciones.

**Archivos:**
- `datos/ugr/lugares_plan.geojson`, `no_localizados.csv`, `medidas_plan.geojson` y `contraste_sectores.json`.
- Se generan con `scripts/16d_plan_ugr_sancristobal.py`.
