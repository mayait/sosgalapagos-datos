Intro: Lo que todavía no se sabe sobre las inundaciones en San Cristóbal: datos que faltan, datos con poco detalle y análisis por hacer. Cada punto es un issue público en GitHub; si tienes información, compártela.

# Cómo aportar

Esta página reúne los pendientes abiertos del proyecto que tocan a San Cristóbal: **20 propios de la isla** y **27 comunes a las islas**. Se arma sola a partir de los [issues de GitHub](https://github.com/mayait/sosgalapagos-datos/issues) (última descarga: 2026-11-02) y se ordena por prioridad: la prioridad 1 cambia decisiones de esta emergencia; la 2 mejora mucho el análisis; la 3 es deseable.

Si tienes un dato que ayude (fotos o videos con fecha, hora y lugar, marcas de agua, lluvia medida, planos de obras, registros de daños), escríbelo en los comentarios de la sección que corresponda o en el issue de GitHub. Los comentarios son públicos: no pongas nombres, teléfonos ni datos de otras personas.

# Datos que faltan

Datos que no tenemos: hay que pedirlos a quien los tiene o levantarlos en campo.

## En San Cristóbal

- **[Catastro municipal (predios, edificios, usos) de los tres GAD](https://github.com/mayait/sosgalapagos-datos/issues/4)** (#4 · prioridad 1)  
    **Quién lo tiene o puede levantarlo:** GAD Santa Cruz, San Cristóbal, Isabela  
    **Para qué sirve:** Exposición real por edificio en lugar de OSM + Open Buildings
- **[Confirmar sobre qué cauce va la zanja de Manzanillo (alternativa A ≈6 m³/s o B ≈24 m³/s)](https://github.com/mayait/sosgalapagos-datos/issues/55)** (#55 · prioridad 1)  
    El caudal de diseño cambia unas cuatro veces según el cauce: ≈6 m³/s si es el A y ≈24 m³/s si es el B. Ver el estudio de San Cristóbal.
- **[Cota del rellano y de la Vía Universidad frente al campus USFQ / GSC, y paso de la quebrada bajo la vía](https://github.com/mayait/sosgalapagos-datos/issues/58)** (#58 · prioridad 1)  
    El resultado del campus es no concluyente: el resalte hacia el GSC (1,6 m) es menor que el error del DSM. Hace falta GNSS del rellano y de la vía, y saber si hay paso o alcantarilla en CR-SCR-0218 y qué capacidad tiene. También la cota de los accesos y de las plantas bajas de los edificios a menos de 25 m del cauce.  
    **Isla:** San Cristóbal  
    **Sale de:** san-cristobal/texto/04_campus.md, «Qué falta saber»  
    https://sosgalapagos.org/estudios/san-cristobal/campus/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Estado del agua potable de San Cristóbal tras el 30–31-oct](https://github.com/mayait/sosgalapagos-datos/issues/59)** (#59 · prioridad 1)  
    No hay información pública sobre las tomas de Los Americanos y Cerro Gato ni sobre sus válvulas, ni datos de turbidez de las plantas El Progreso y Las Palmeras, ni del estado de los cruces de la línea de Cerro Gato con cauces de más de 2 km². Dato en manos del GAD.  
    **Isla:** San Cristóbal  
    **Sale de:** 06_agua.md, «Vacíos de información»  
    https://sosgalapagos.org/estudios/san-cristobal/agua/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Lluvia medida en la ciudad y a 5–10 min del 30–31-oct en San Cristóbal (GSC, DARWIN, INAMHI)](https://github.com/mayait/sosgalapagos-datos/issues/61)** (#61 · prioridad 1 · 1 comentario)  
    Ya hay lluvia medida del evento en la parte alta de San Cristóbal (estaciones USFQ-GSC vía el historial del INAMHI; ver el comentario del 2-nov). Falta la lluvia **en la ciudad** (ninguna estación dentro de las cuencas urbanas; M0221 solo desde el 2-nov), las intensidades de 5–10 min del GSC, su serie histórica y las estaciones DARWIN.  
    **Isla:** San Cristóbal  
    https://sosgalapagos.org/estudios/san-cristobal/lluvia/
- **[Trazados de las obras del Plan de Acción de la UGR (zanja de 1 040 m, muro de 240 m, conexión de Floreana)](https://github.com/mayait/sosgalapagos-datos/issues/70)** (#70 · prioridad 1)  
    Los trazados reales están en manos de la UGR. Sin ellos, el análisis supone ubicaciones. Complementa [#55](https://github.com/mayait/sosgalapagos-datos/issues/55).  
    **Isla:** San Cristóbal  
    **Sale de:** 03_plan_ugr.md, «Qué falta saber»  
    https://sosgalapagos.org/estudios/san-cristobal/plan-ugr/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Series del proyecto DARWIN (U. de Marburgo) del 15-oct al 2-nov y permiso para publicar derivados](https://github.com/mayait/sosgalapagos-datos/issues/76)** (#76 · prioridad 1)  
    Tres estaciones de DARWIN parecen compartir sitio con estaciones IERSE-WSN de Santa Cruz (Santa Rosa, Cerro Crocker, Militar) y podrían tener la lluvia que IERSE perdió entre las 21:25 del 30-oct y las 18:45 del 31-oct; también hay estaciones en San Cristóbal (Puerto Baquerizo Moreno, La Galapaguera, El Junco). Lo publicado llega a 2025–may-2026 y el acuerdo de uso prohíbe redistribuir: hay que pedir las series del evento y permiso para publicar derivados (con coautoría si lo piden). Lo pide el responsable del proyecto. Relacionado con [#61](https://github.com/mayait/sosgalapagos-datos/issues/61) y [#62](https://github.com/mayait/sosgalapagos-datos/issues/62).
- **[Ubicar los 16 lugares no localizados del Plan de Acción de la UGR de San Cristóbal](https://github.com/mayait/sosgalapagos-datos/issues/53)** (#53 · prioridad 2)  
    El estudio de San Cristóbal integra el Plan de Acción de la UGR, pero 16 lugares no se pudieron georreferenciar (`geodatos/estudios/san-cristobal/datos/ugr/no_localizados.csv`). Hay que confirmarlos con la UGR o en terreno.
- **[Verificar en campo el collado Galápagos–Divino Niño (San Cristóbal)](https://github.com/mayait/sosgalapagos-datos/issues/54)** (#54 · prioridad 2)  
    El estudio lo plantea como **hipótesis** a partir del DEM de 30 m. Hay que verificar en terreno, o con GNSS o dron, si el agua puede pasar por ese collado.
- **[Ubicación y trazado verificados de las tomas y conducciones del acueducto de San Cristóbal](https://github.com/mayait/sosgalapagos-datos/issues/60)** (#60 · prioridad 2)  
    Qué tomas están en servicio en 2026; si las dos líneas «en construcción» del IGM son las actuales; trazado de las conducciones desde Los Americanos y entre la planta El Progreso y Puerto Baquerizo Moreno; profundidad y protección de las tuberías en los cruces; GNSS de tomas y represa.  
    **Isla:** San Cristóbal  
    **Sale de:** 06_agua.md  
    https://sosgalapagos.org/estudios/san-cristobal/agua/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Floreana: qué cauce es cada cañada del Plan de Acción y trazado de la conexión de ≈500 m](https://github.com/mayait/sosgalapagos-datos/issues/69)** (#69 · prioridad 2)  
    No se sabe cuál de los tres cauces es La Hormiga, La Varonesa o La Lobería, ni si La Hormiga es una obra (cuneta perimetral). Hace falta la topografía GNSS del trazado y saber adónde va el agua desviada.  
    **Isla:** San Cristóbal (Floreana)  
    **Sale de:** 07_floreana.md  
    https://sosgalapagos.org/estudios/san-cristobal/floreana/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Nivel del mar / mareógrafo (Puerto Ayora, Baquerizo)](https://github.com/mayait/sosgalapagos-datos/issues/13)** (#13 · prioridad 3)  
    **Novedad (2-nov):** el recolector de clima ya recoge el mareógrafo IOC de Puerto Ayora. Falta Puerto Baquerizo Moreno y la serie histórica.  
    **Quién lo tiene o puede levantarlo:** INOCAR  
    **Para qué sirve:** Costa baja y marejadas combinadas con lluvia
- **[Floreana y resto de Isabela (hoy solo Isabela sur)](https://github.com/mayait/sosgalapagos-datos/issues/15)** (#15 · prioridad 3)  
    **Para qué sirve:** Cobertura completa de zonas pobladas

## Comunes a las islas

- **[Delimitación oficial de las áreas inundadas del 30–31-oct-2026](https://github.com/mayait/sosgalapagos-datos/issues/1)** (#1 · prioridad 1)  
    **Quién lo tiene o puede levantarlo:** COE cantonal, SNGR, vuelo de dron  
    **Para qué sirve:** Validar el modelo HAND y la capa `areas_afectadas` (hoy por validar)
- **[Red de drenaje urbano: sumideros, colectores, alcantarillas y pasos bajo vías con cotas de fondo](https://github.com/mayait/sosgalapagos-datos/issues/5)** (#5 · prioridad 1 · 1 comentario)  
    **Quién lo tiene o puede levantarlo:** GAD (obras públicas), CGREG  
    **Para qué sirve:** Capacidad real de la salida urbana; cruces quebrada–vía
- **[Refugios y puntos de encuentro para inundación (distintos de los de tsunami)](https://github.com/mayait/sosgalapagos-datos/issues/6)** (#6 · prioridad 1)  
    **Quién lo tiene o puede levantarlo:** COE, SNGR  
    **Para qué sirve:** Capa de puntos clave para esta amenaza
- **[SIIG del CGREG (requiere usuario)](https://github.com/mayait/sosgalapagos-datos/issues/7)** (#7 · prioridad 2)  
    **Quién lo tiene o puede levantarlo:** CGREG  
    **Para qué sirve:** Capas oficiales de planificación y riesgos actualizadas
- **[Censo 2022 por manzana publicado](https://github.com/mayait/sosgalapagos-datos/issues/8)** (#8 · prioridad 2)  
    **Quién lo tiene o puede levantarlo:** INEC  
    **Para qué sirve:** Población real; hoy es una estimación SNGR por vivienda
- **[Aforos o huellas de crecida en quebradas](https://github.com/mayait/sosgalapagos-datos/issues/9)** (#9 · prioridad 2)  
    **Quién lo tiene o puede levantarlo:** Academia, DPNG  
    **Para qué sirve:** Calibrar CN y tiempo de concentración
- **[Ensayos de infiltración y geología (grietas, tubos de lava)](https://github.com/mayait/sosgalapagos-datos/issues/10)** (#10 · prioridad 2)  
    **Quién lo tiene o puede levantarlo:** Academia, FCD  
    **Para qué sirve:** Pérdidas reales en el lecho de lava; alternativa de infiltración
- **[Datum vertical: IGM frente a EGM2008 en cada isla](https://github.com/mayait/sosgalapagos-datos/issues/12)** (#12 · prioridad 2)  
    **Quién lo tiene o puede levantarlo:** IGM, INOCAR  
    **Para qué sirve:** Explicar el sesgo de −2 a −3 m del DSM y fijar cotas respecto del mar
- **[Registro histórico de eventos completo (fechas, lugares, daños)](https://github.com/mayait/sosgalapagos-datos/issues/14)** (#14 · prioridad 2)  
    **Quién lo tiene o puede levantarlo:** SNGR, GAD, prensa local  
    **Para qué sirve:** Frecuencia y validación de zonas susceptibles

# Datos con poco detalle

Datos que existen, pero con un detalle que no alcanza para responder bien.

## En San Cristóbal

- **[DTM ≤ 1 m de los poblados: Puerto Ayora y escarpe (5–10 km²), Bellavista, Puerto Baquerizo Moreno, Puerto…](https://github.com/mayait/sosgalapagos-datos/issues/16)** (#16 · prioridad 1 · 1 comentario)  
    **Hoy:** **DSM Copernicus GLO-30** (30 m, incluye edificios y árboles)  
    **Lo que necesitamos:** **DTM ≤ 1 m** de los poblados: Puerto Ayora y escarpe (5–10 km²), Bellavista, Puerto Baquerizo Moreno, Puerto Villamil  
    **Cómo:** Dron con fotogrametría (OpenDroneMap) + GNSS RTK; o LiDAR
- **[Pluviómetros en cada poblado y en la parte alta de cada cuenca (hoy: Lluvia: 4 estaciones IERSE en Santa…](https://github.com/mayait/sosgalapagos-datos/issues/19)** (#19 · prioridad 1)  
    **Hoy:** Lluvia: 4 estaciones IERSE en Santa Cruz (ninguna en Puerto Ayora) + red GSC en San Cristóbal  
    **Lo que necesitamos:** Pluviómetros en cada poblado y en la parte alta de cada cuenca  
    **Cómo:** Instalar pluviómetros (USFQ, FCD, ciudadanos) y sumarlos a `clima/`
- **[Huellas completas y con altura (hoy: Huellas de edificios: OSM + Google Open Buildings (no cubre San…](https://github.com/mayait/sosgalapagos-datos/issues/18)** (#18 · prioridad 2)  
    **Hoy:** Huellas de edificios: OSM + Google Open Buildings (no cubre San Cristóbal)  
    **Lo que necesitamos:** Huellas completas y con altura  
    **Cómo:** Catastro, digitalización sobre ortofoto de dron
- **[Modelo 2D de San Cristóbal con la lluvia USFQ-GSC del 30–31-oct](https://github.com/mayait/sosgalapagos-datos/issues/74)** (#74 · prioridad 2)  
    Correr el modelo 2D de Puerto Baquerizo Moreno con el hietograma medido (El Mirador o Cerro Alto; suelo húmedo, AMC III) y compararlo con los escenarios de 50/100/150 mm y con la tormenta de Santa Cruz trasladada. Una comparación gruesa sugiere que lo medido se parece más al escenario de 100 mm. Datos: geodatos/estudios/san-cristobal/datos/lluvia_mareas_horaria.csv. Avanza [#26](https://github.com/mayait/sosgalapagos-datos/issues/26).  
    https://sosgalapagos.org/estudios/san-cristobal/modelo-2d/

## Comunes a las islas

- **[Topografía urbana 1:1 000–1:5 000 si existe (hoy: Curvas IGM 1:25 000)](https://github.com/mayait/sosgalapagos-datos/issues/17)** (#17 · prioridad 2)  
    **Hoy:** Curvas IGM 1:25 000  
    **Lo que necesitamos:** Topografía urbana 1:1 000–1:5 000 si existe  
    **Cómo:** Pedir a GAD / IGM
- **[Lluvia satelital GPM IMERG (30 min, 10 km) del evento y la serie (hoy: Lluvia de modelos (Open-Meteo,…](https://github.com/mayait/sosgalapagos-datos/issues/20)** (#20 · prioridad 2)  
    **Hoy:** Lluvia de modelos (Open-Meteo, ECMWF 9 km)  
    **Lo que necesitamos:** Lluvia satelital GPM IMERG (30 min, 10 km) del evento y la serie  
    **Cómo:** Cuenta NASA Earthdata
- **[Imagen de alta resolución posterior al evento (hoy: Imágenes satelitales)](https://github.com/mayait/sosgalapagos-datos/issues/21)** (#21 · prioridad 2)  
    **Hoy:** Imágenes satelitales  
    **Lo que necesitamos:** Imagen de alta resolución posterior al evento  
    **Cómo:** Maxar Open Data, Planet, Sentinel-1/2
- **[Población por manzana del censo (hoy: Población estimada por vivienda (SNGR))](https://github.com/mayait/sosgalapagos-datos/issues/22)** (#22 · prioridad 2)  
    **Hoy:** Población estimada por vivienda (SNGR)  
    **Lo que necesitamos:** Población por manzana del censo  
    **Cómo:** INEC

# Análisis y modelos por hacer

Análisis que darán respuestas más firmes cuando lleguen los datos.

## En San Cristóbal

- **[Curvas IDF (intensidad–duración–frecuencia)](https://github.com/mayait/sosgalapagos-datos/issues/24)** (#24 · prioridad 1)  
    **Depende de:** Serie diaria GSC desde 2015, IERSE, FCD  
    **Notas:** Base de cualquier diseño de obra

## Comunes a las islas

- **[Recalcular HAND con el DTM de dron y validarlo con las marcas de agua](https://github.com/mayait/sosgalapagos-datos/issues/23)** (#23 · prioridad 1)  
    **Depende de:** §2 DTM, §1 marcas  
    **Notas:** Ver [docs/modelo-hand.md](https://github.com/mayait/sosgalapagos-datos/blob/main/docs/modelo-hand.md)
- **[Mapa de amenaza por inundación candidato a oficial (hoy no existe ninguno para Galápagos)](https://github.com/mayait/sosgalapagos-datos/issues/28)** (#28 · prioridad 1)  
    **Depende de:** Los anteriores  
    **Notas:** Propuesta para SNGR, CGREG y GAD
- **[Modelo lluvia–caudal (HEC-HMS) por subcuenca, calibrado con el evento](https://github.com/mayait/sosgalapagos-datos/issues/25)** (#25 · prioridad 2)  
    **Depende de:** IDF, aforos, infiltración
- **[Riesgo = amenaza × exposición × vulnerabilidad por manzana](https://github.com/mayait/sosgalapagos-datos/issues/29)** (#29 · prioridad 2)  
    **Depende de:** Catastro, censo  
    **Notas:** Hoy solo tenemos exposición
- **[Pronóstico 72 h (ECMWF/GFS) en el panel de clima](https://github.com/mayait/sosgalapagos-datos/issues/31)** (#31 · prioridad 2)
- **[Susceptibilidad a movimientos en masa (pendiente + lluvia + geología)](https://github.com/mayait/sosgalapagos-datos/issues/32)** (#32 · prioridad 2)  
    **Depende de:** Geología
- **[Drenaje urbano 1D/2D (SWMM)](https://github.com/mayait/sosgalapagos-datos/issues/27)** (#27 · prioridad 3)  
    **Depende de:** Red de sumideros
- **[Seguimiento de El Niño (ONI, temperatura del mar)](https://github.com/mayait/sosgalapagos-datos/issues/34)** (#34 · prioridad 3)  
    **Notas:** Contexto para alertas estacionales

# Acuerdos y gestión de los datos

Acuerdos, permisos y reglas para que los datos lleguen, se compartan y se mantengan.

## En San Cristóbal

- **[Series del proyecto DARWIN (U. de Marburgo) del 15-oct al 2-nov y permiso para publicar derivados](https://github.com/mayait/sosgalapagos-datos/issues/76)** (#76 · prioridad 1)  
    Tres estaciones de DARWIN parecen compartir sitio con estaciones IERSE-WSN de Santa Cruz (Santa Rosa, Cerro Crocker, Militar) y podrían tener la lluvia que IERSE perdió entre las 21:25 del 30-oct y las 18:45 del 31-oct; también hay estaciones en San Cristóbal (Puerto Baquerizo Moreno, La Galapaguera, El Junco). Lo publicado llega a 2025–may-2026 y el acuerdo de uso prohíbe redistribuir: hay que pedir las series del evento y permiso para publicar derivados (con coautoría si lo piden). Lo pide el responsable del proyecto. Relacionado con [#61](https://github.com/mayait/sosgalapagos-datos/issues/61) y [#62](https://github.com/mayait/sosgalapagos-datos/issues/62).
- **[Pedir al GSC la licencia de sus datos meteorológicos](https://github.com/mayait/sosgalapagos-datos/issues/46)** (#46 · prioridad 2)
- **[Clasificación del suelo del puerto de San Cristóbal (urbano o rural) en la capa del CGREG](https://github.com/mayait/sosgalapagos-datos/issues/72)** (#72 · prioridad 2)  
    En la capa del CGREG solo El Progreso figura como suelo urbano, y el polígono del puerto aparece como «rural». Hay que confirmarlo con el GAD, porque condiciona qué norma se aplica.  
    **Isla:** San Cristóbal  
    **Sale de:** 02_encanadas.md  
    https://sosgalapagos.org/estudios/san-cristobal/encanadas/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.

## Comunes a las islas

- **[Acuerdos de intercambio de datos con GAD, CGREG, DPNG, FCD, INAMHI, SNGR e INOCAR](https://github.com/mayait/sosgalapagos-datos/issues/45)** (#45 · prioridad 1)
- **[Protocolo de datos personales (LOPDP): qué se depura, quién revisa, nunca subir crudos oficiales](https://github.com/mayait/sosgalapagos-datos/issues/48)** (#48 · prioridad 1)
- **[Distinguir siempre dato oficial de modelo propio en mapas y textos](https://github.com/mayait/sosgalapagos-datos/issues/49)** (#49 · prioridad 1)
- **[Metadatos por capa (fuente, fecha, licencia, resolución, responsable) en catalogo/ para todas las capas](https://github.com/mayait/sosgalapagos-datos/issues/47)** (#47 · prioridad 2)
- **[Definir la licencia del código (p. ej. MIT) y de los datos derivados (respetando ODbL de OSM y las de cada…](https://github.com/mayait/sosgalapagos-datos/issues/50)** (#50 · prioridad 2)
- **[Formar un equipo local (USFQ, GAD, CGREG) que mantenga los datos después de la emergencia](https://github.com/mayait/sosgalapagos-datos/issues/51)** (#51 · prioridad 2)

# Tareas de la plataforma

Hay además 11 tareas abiertas sobre los servidores, los mapas y los scripts. No son vacíos de información, así que no se listan aquí: están en GitHub con la etiqueta [plataforma](https://github.com/mayait/sosgalapagos-datos/issues?q=is%3Aopen+label%3Aplataforma).

<!-- Generado por scripts/22_pendientes.py a partir de estudios/pendientes.json. No editar a mano. -->
