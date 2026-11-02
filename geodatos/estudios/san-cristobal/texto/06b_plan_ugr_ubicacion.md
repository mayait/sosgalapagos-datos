[[SALTO]]

## 1 Los lugares del Plan de Acción de la UGR en el mapa

> **PRELIMINAR.** Esta subsección ubica y contrasta, **desde lo urbano**, los lugares y medidas del *Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal*. Ni la asignación de las cañadas oficiales a los cauces ni la integración del plan en la gestión del riesgo se tratan aquí: corresponden a la sección 4.6 (hidrología) y a la sección 7 (riesgo). Los nombres de las encañadas siguen la correspondencia de la sección 4.6.

### Qué se ubicó y con qué fiabilidad

El plan nombra **47 lugares**, contando por separado cada sitio de Floreana. **Se ubicaron 31**, con las fuentes registradas en cada caso:
- 28 puntos;
- la Vía Perimetral Jaime Roldós, como línea;
- la zona urbana de El Progreso y el poblado de Puerto Velasco Ibarra, como polígonos.

Las fuentes son OSM, la toponimia y las capas del IGM 1:25 000, las localidades del INEC, el MSP, el MINEDUC y las coordenadas de registros de la SNGR. La confianza de la ubicación es **alta en 13 lugares, media en 12 y baja en 6**.

El Centro de Gestión de Residuos Sólidos (CGRS) baja a confianza media: OSM e IGM lo cartografían, pero el GAD no lo ha confirmado. Los Viveros del PNG y la Galapaguera de Cerro Colorado **están ubicados pero no se analizan**, porque quedan fuera de las zonas urbanas estudiadas.

**Hay 16 lugares que no figuran en ninguna fuente** y no se ubicaron (`datos/ugr/no_localizados.csv`):
- **9 en Puerto Baquerizo Moreno:** los talleres del CGREG, la Estación Terrena, el sector El Manantial, los barrios San Francisco y Fragata, Los Arrayanes, **La Picada**, el patio de contenedores y el Parque Artesanal;
- **7 en Floreana:** La Lobería, las cañadas La Hormiga y La Varonesa, la desalinizadora, la bodega parroquial, el ABG y las oficinas del PNG.

**Hay cuatro casos dudosos**:
- **Hospital Oskar Jandl.** OSM y el MSP lo sitúan a 1,3 km de distancia. Se usó el punto de OSM porque el plan sitúa el hospital en el barrio Divino Niño, junto al Colegio Ignacio Hernández, y eso coincide con OSM.
- **Playa y Poza de las Garzas.** No tiene topónimo. Se ubicó en la desembocadura de la Galápagos (Barrio Frío), porque el plan la describe como su «punto final».
- **«El puente» de Manzanillo.** Se supone que es el puente de OSM de la Vía Perimetral (cruce CR-SCR-0011). **Está sobre la Galápagos**, en el tramo medio de ≈9,4 km², y no sobre el ramal Manzanillo–El Manantial, que se une a la Galápagos unos 360 m aguas arriba.
- **Los Arroyos.** El poblado del IGM está 9 km al este y no encaja con el recorrido de la cañada Galápagos que describe el plan.

![Lugares y medidas del Plan de Acción SC-4-09-2026 ubicados en Puerto Baquerizo Moreno, sobre los cauces D8 y la franja del CGREG.](figuras/f_plan_ugr.png)

### Medidas del plan trazadas

Todas son **aproximaciones sobre cauces D8**. El plan no da trazados (`datos/ugr/medidas_plan.geojson`).

- **Zanja de 1 040 m en Manzanillo.** Hay dos hipótesis, porque no se sabe sobre qué cauce está:
  - **A (principal):** los últimos 1 040 m del ramal **Manzanillo–El Manantial** (≈1,8 km²) antes de unirse a la Galápagos. El caudal de diseño sería del orden de **6 m³/s** con 100 mm (3–19; sección 4.2).
  - **B (alternativa):** 1 040 m de la **Galápagos, tramo alto** (8–9 km²), aguas arriba del puente de la Vía Perimetral, pasando junto a la Ciudadela El Gran Maestro. El caudal de diseño sería de unos **24 m³/s** (14–38), **cuatro veces más**.

  Que el plan sitúe el desborde «a 100 m del puente» favorece la hipótesis B. Que diga «barrio Manzanillo, sector El Manantial» favorece la A. Elegir mal el cauce hace que la sección de la zanja quede cuatro veces corta o cuatro veces sobrada. Hay que confirmarlo con la UGR antes de dimensionar.
- **Limpieza en La Picada** (170 m en el PNG y 240 m urbanos). La cañada Palmeras–Arrayanes de la hidrología (PBM-L07) **no toca el PNG**, así que no admite «170 m en el PNG». El trazado se hizo sobre el único cauce que cruza el límite del PNG junto al barrio Palmeras, a 54 m del punto: la Galápagos, tramo alto. La incertidumbre es muy alta, porque La Picada no está localizada.
- **Desembocadura de Playa de Oro.** Es la salida al mar de Divino Niño, junto a la playa. La incertidumbre es de unos ±50 m.
- **Muro del hospital (240 m).** Se trazó como 240 m del cauce de Divino Niño centrados en el hospital de OSM. El hospital está a 15 m del cauce D8 de esta sección y a 35 m de la cañada oficial.
- **Conexión de las cañadas de Floreana (500 m).** No se pudo trazar porque las cañadas no están cartografiadas. Ver la sección 4c, exploratoria.

### Contraste con el diagnóstico urbano

Para cada lugar de prioridad máxima se contaron los edificios y la población del INEC, los cruces quebrada–vía de la sección 5 y la cobertura de la franja del CGREG, todo en un radio de 150 m. El radio sirve para comparar lugares entre sí; no delimita el barrio. En la última columna figura la cañada oficial más cercana y su distancia.

Tabla: Sectores de prioridad máxima del plan frente al diagnóstico urbano (radio de 150 m; población del INEC repartida por área de techo).

| Sector del plan | Confianza | Edificios / personas | Cruces (prioridad alta; con estructura) | Franja CGREG en el radio | Cañada oficial más cercana |
|---|---|---|---|---|---|
| Playa y Poza de las Garzas | Baja | 136 / ≈190 | 5 (1; 3 puentes) | 8 %; a 30 m | Galápagos (15 m) |
| Barrio Frío | Media | 108 / ≈170 | 4 (2; 3 puentes) | 5 %; a 120 m | Galápagos (90 m) |
| Playa de Oro | Alta | 112 / ≈230 | 5 (2; 0) | 0 %; a 200 m | Divino Niño (56 m) |
| Hospital Oskar Jandl | Media | 123 / ≈380 | 4 (3; 0) | 14 %; a 56 m | Divino Niño (35 m) |
| Colegio Ignacio Hernández | Alta | 61 / ≈230 | 1 (0; 0) | 0 %; a 300 m | Divino Niño (59 m) |
| Barrio Divino Niño | Media | 151 / ≈480 | 3 (2; 0) | 0 %; a 170 m | Divino Niño (41 m) |
| Barrio Playa Mann | Media | 73 / ≈40 | 1 (1; 0) | 0 %; a 270 m | Alvear y Playa Mann (147 m) |
| Barrio Manzanillo | Media | 58 / ≈130 | 3 (0; 0) | 0 %; a 330 m | Manzanillo–El Manantial (75 m); Galápagos (200 m) |
| Ciudadela El Gran Maestro | Baja | 96 / ≈240 | 3 (2; 0) | 9 %; a 110 m | Galápagos, tramo alto (16 m); Manzanillo–El Manantial (33 m) |
| Puente de Manzanillo | Baja | 57 / ≈190 | 2 (1; 2 puentes) | 17 %; sobre ella | Galápagos, tramo medio (5 m) |
| Barrio Palmeras | Media | 52 / ≈90 | 5 (0; 0) | 0 %; a 400 m | La Planada / Manzanillo–El Manantial (15 m) |
| Sector La Planada | Media | 69 / ≈150 | 5 (1; 0) | 0 %; a 400 m | La Planada / Manzanillo–El Manantial (32 m) |

**Lectura:**

1. **El plan y el diagnóstico de gabinete coinciden en los ejes.**
   - Los sectores de prioridad máxima se agrupan en torno a cuatro encañadas oficiales: la **Galápagos** (Barrio Frío, las Garzas, el puente y El Gran Maestro), **Divino Niño**, **La Planada → Manzanillo–El Manantial** y **Alvear–Playa Mann**.
   - Los sectores de mayor densidad, Divino Niño y el entorno del hospital, con unas 380–480 personas en 150 m, están sobre la cañada más ocupada en relación con su tamaño: Divino Niño (sección 6.2).
2. **La franja del CGREG casi no cubre los sectores prioritarios.**
   - Solo toca, en parte, cinco de los doce, todos sobre la Galápagos o junto al hospital.
   - **No cubre en absoluto** Playa de Oro, Divino Niño, Playa Mann, Manzanillo, Palmeras ni La Planada. Varios de ellos son los que el plan da como más afectados en 2025–2026.
3. **Los pasos de vía de los sectores altos no tienen estructura cartografiada.**
   - En La Planada, Palmeras, Manzanillo y Divino Niño ninguno de los cruces a menos de 150 m tiene puente ni alcantarilla cartografiados.
   - Las únicas estructuras están sobre la Galápagos, en Barrio Frío y en la Vía Perimetral.
4. **El Progreso.**
   - El plan cuenta **43 viviendas y 124 personas expuestas directamente**.
   - En el polígono urbano de la sección 6.1 hay 183 edificios y unas 250 personas, y un cauce de 0,74 km² pasa con **16 edificios a menos de 15 m**.
   - Las dos cifras son compatibles si la del plan se refiere a los sectores bajos y a la franja del cauce.
5. **Floreana.** No hay manzanas del INEC ni huellas de edificios en Puerto Velasco Ibarra en las capas del proyecto. Solo se ubicaron el poblado, Playa Negra, el dispensario y la central eléctrica.

**Para la UGR:**
- validar en campo los lugares de confianza baja o no localizados, empezando por La Picada, El Manantial, las Garzas y «el puente»;
- confirmar **sobre qué cauce va la zanja de 1 040 m**;
- entregar los trazados reales de la zanja, del muro de 240 m y de la conexión de 500 m en Floreana.

**Archivos:**
- `datos/ugr/lugares_plan.geojson`, `no_localizados.csv`, `medidas_plan.geojson` y `contraste_sectores.json`.
- Se generan con `scripts/16d_plan_ugr_sancristobal.py`.
