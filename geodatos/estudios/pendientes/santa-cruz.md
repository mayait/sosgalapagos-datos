Intro: Lo que todavía no se sabe sobre las inundaciones en Santa Cruz: datos que faltan, datos con poco detalle y análisis por hacer. Cada punto es un issue público en GitHub; si tienes información, compártela.

# Cómo aportar

Esta página reúne los pendientes abiertos del proyecto que tocan a Santa Cruz: **21 propios de la isla** y **27 comunes a las islas**. Se arma sola a partir de los [issues de GitHub](https://github.com/mayait/sosgalapagos-datos/issues) (última descarga: 2026-11-02) y se ordena por prioridad: la prioridad 1 cambia decisiones de esta emergencia; la 2 mejora mucho el análisis; la 3 es deseable.

Si tienes un dato que ayude (fotos o videos con fecha, hora y lugar, marcas de agua, lluvia medida, planos de obras, registros de daños), escríbelo en los comentarios de la sección que corresponda o en el issue de GitHub. Los comentarios son públicos: no pongas nombres, teléfonos ni datos de otras personas.

# Datos que faltan

Datos que no tenemos: hay que pedirlos a quien los tiene o levantarlos en campo.

## En Santa Cruz

- **[Marcas de agua del evento con GNSS (barrio La Cascada y su salida)](https://github.com/mayait/sosgalapagos-datos/issues/2)** (#2 · prioridad 1 · 2 comentarios)  
    **Quién lo tiene o puede levantarlo:** GAD Santa Cruz, academia, sociedad civil  
    **Para qué sirve:** Calibrar la lámina y el rebose del vaso de La Cascada (≈12–13 m)
- **[Lluvia medida en Puerto Ayora el 30–31-oct: incorporar INAMHI M0191 al estudio de La Cascada](https://github.com/mayait/sosgalapagos-datos/issues/3)** (#3 · prioridad 1 · 1 comentario)  
    **Novedad (2-nov):** la estación INAMHI M0191 (Puerto Ayora, 6 m, a 1,4 km de La Cascada) registró 93,6 mm el 30-oct y 135,4 mm el 31-oct (días en UTC−5), con un pico de ~37 mm/h. El recolector de clima ya la recoge.  
    **Dato:** **Lluvia medida el 30–31-oct** en Puerto Ayora (no hay estación allí)  
    **Quién lo tiene o puede levantarlo:** FCD, INAMHI, aeropuerto, pluviómetros privados  
    **Para qué sirve:** Decidir entre ECMWF 9 km (≈80–130 mm) y los otros modelos (0,2–26 mm)
- **[Catastro municipal (predios, edificios, usos) de los tres GAD](https://github.com/mayait/sosgalapagos-datos/issues/4)** (#4 · prioridad 1)  
    **Quién lo tiene o puede levantarlo:** GAD Santa Cruz, San Cristóbal, Isabela  
    **Para qué sirve:** Exposición real por edificio en lugar de OSM + Open Buildings
- **[Confirmar si hubo inundación en La Cascada el 3-oct, el 23-oct y el 1/2-nov de 2026](https://github.com/mayait/sosgalapagos-datos/issues/52)** (#52 · prioridad 1)  
    Ese día cayeron 68 mm (Los Guayabillos, 3-oct) y 97 mm con 28 mm/h (Santa Rosa, 23-oct), y no hay reportes de inundación. Hoy se usan como validación **condicional** del modelo 2D ([#26](https://github.com/mayait/sosgalapagos-datos/issues/26)) y de la regla de alerta ([#30](https://github.com/mayait/sosgalapagos-datos/issues/30)).  
    **Quién puede confirmarlo:** GAD Santa Cruz, COE, ECU 911, vecinos o la prensa local.
- **[Recuperar la lluvia de la red IERSE durante el corte del 30-oct (21:25) al 31-oct (18:45) y saber la causa](https://github.com/mayait/sosgalapagos-datos/issues/62)** (#62 · prioridad 1)  
    Las estaciones de Los Guayabillos y Santa Rosa dejaron de transmitir a la vez en el peor momento. Hay que saber si guardaron registros en memoria local y qué cortó la transmisión (energía, comunicaciones). También si tienen batería, panel solar o comunicaciones de respaldo. Complementa [#56](https://github.com/mayait/sosgalapagos-datos/issues/56).  
    **Isla:** Santa Cruz  
    **Sale de:** 02_lluvia.md (tabla de vacíos), 07_riesgos.md  
    https://sosgalapagos.org/estudios/santa-cruz/lluvia/  
    https://sosgalapagos.org/estudios/santa-cruz/riesgos/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Cota de rebose de La Cascada y naturaleza del umbral de la calle Isla Santiago – Karl Angermeyer](https://github.com/mayait/sosgalapagos-datos/issues/65)** (#65 · prioridad 1)  
    La cota real del rebose está entre 12,0 y 13,25 m en el DSM y solo se fija con GNSS. Hay que saber si el umbral es un lomo de lava o un relleno urbano, y si hay sótanos o muros que corten el flujo.  
    **Isla:** Santa Cruz  
    **Sale de:** 03_la_cascada.md, «Qué falta saber»  
    https://sosgalapagos.org/estudios/santa-cruz/la-cascada/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Tomás de Berlanga: trazado del cauce, cota de la escuela y ruta de evacuación](https://github.com/mayait/sosgalapagos-datos/issues/66)** (#66 · prioridad 1)  
    El cauce no se ha recorrido en campo desde la Av. Padre Julio Herrera. Faltan la cota de la escuela respecto al cauce y su ruta de evacuación (de eso depende si puede servir de refugio), y saber si existe aviso o cierre de la vía con lluvia intensa. Pasos CR-SCZ-0016 a 0020 y 0041: comentar en [#33](https://github.com/mayait/sosgalapagos-datos/issues/33).  
    **Isla:** Santa Cruz  
    **Sale de:** 05_parte_alta.md, «Qué falta saber»  
    https://sosgalapagos.org/estudios/santa-cruz/parte-alta/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Exposición real de los refugios de Bellavista y Puerto Ayora](https://github.com/mayait/sosgalapagos-datos/issues/67)** (#67 · prioridad 1)  
    El refugio oficial (estadio Gordon Wolf) está a 59 m de un cauce de ≈7,5 km². El Coliseo y la Casa de los Mormones están en cotas bajas según el DSM. Faltan la cota del piso, los muros y las alcantarillas, verificados en campo. Complementa [#6](https://github.com/mayait/sosgalapagos-datos/issues/6).  
    **Isla:** Santa Cruz  
    **Sale de:** 07_riesgos.md  
    https://sosgalapagos.org/estudios/santa-cruz/riesgos/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Lectura diaria de la estación Charles Darwin (FCD) del 15-oct al 2-nov](https://github.com/mayait/sosgalapagos-datos/issues/63)** (#63 · prioridad 2)  
    Es un dato de lluvia en Puerto Ayora, independiente de M0191 ([#3](https://github.com/mayait/sosgalapagos-datos/issues/3)). Dato en manos de la FCD (dataZone).  
    **Isla:** Santa Cruz  
    **Sale de:** 02_lluvia.md, tabla de vacíos  
    https://sosgalapagos.org/estudios/santa-cruz/lluvia/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Horas de los hechos del 30-oct en Santa Cruz](https://github.com/mayait/sosgalapagos-datos/issues/64)** (#64 · prioridad 2)  
    Hora del desborde de cada cañada; cuándo llegó el agua a La Cascada y hasta qué altura; avisos informales; sesión del COE cantonal y declaratoria; si siguió lloviendo después de las 21:25. Se puede reconstruir con entrevistas y registros. Sin nombres de personas afectadas.  
    **Isla:** Santa Cruz  
    **Sale de:** 01_que_paso.md, «Qué falta saber»  
    https://sosgalapagos.org/estudios/santa-cruz/que-paso/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[¿La cañada El Aguacatal drena hacia La Cascada?](https://github.com/mayait/sosgalapagos-datos/issues/68)** (#68 · prioridad 2)  
    Según las coordenadas del registro SNGR de 2024, sí; está por verificar en campo. Cambia el área y la lluvia que llegan al barrio.  
    **Isla:** Santa Cruz  
    **Sale de:** 01_que_paso.md, 07_riesgos.md  
    https://sosgalapagos.org/estudios/santa-cruz/que-paso/  
    https://sosgalapagos.org/estudios/santa-cruz/riesgos/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.
- **[Fotografías aéreas históricas del IGM e historial de OSM](https://github.com/mayait/sosgalapagos-datos/issues/11)** (#11 · prioridad 3)  
    **Quién lo tiene o puede levantarlo:** IGM  
    **Para qué sirve:** Drenajes históricos y fecha de urbanización del escarpe
- **[Nivel del mar / mareógrafo (Puerto Ayora, Baquerizo)](https://github.com/mayait/sosgalapagos-datos/issues/13)** (#13 · prioridad 3)  
    **Novedad (2-nov):** el recolector de clima ya recoge el mareógrafo IOC de Puerto Ayora. Falta Puerto Baquerizo Moreno y la serie histórica.  
    **Quién lo tiene o puede levantarlo:** INOCAR  
    **Para qué sirve:** Costa baja y marejadas combinadas con lluvia
- **[Serie original de lluvia de Bellavista (FCD) y episodio de marzo de 2008](https://github.com/mayait/sosgalapagos-datos/issues/73)** (#73 · prioridad 3)  
    La FCD advierte que los datos publicados se «ajustaron». Los 770 mm en 3 días de marzo de 2008 hay que verificarlos con la serie original.  
    **Isla:** Santa Cruz  
    **Sale de:** 02_lluvia.md  
    https://sosgalapagos.org/estudios/santa-cruz/lluvia/  
    Si tienes el dato, compártelo aquí o en los comentarios de la página del estudio. No incluyas datos personales de personas afectadas.

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

## En Santa Cruz

- **[DTM ≤ 1 m de los poblados: Puerto Ayora y escarpe (5–10 km²), Bellavista, Puerto Baquerizo Moreno, Puerto…](https://github.com/mayait/sosgalapagos-datos/issues/16)** (#16 · prioridad 1 · 1 comentario)  
    **Hoy:** **DSM Copernicus GLO-30** (30 m, incluye edificios y árboles)  
    **Lo que necesitamos:** **DTM ≤ 1 m** de los poblados: Puerto Ayora y escarpe (5–10 km²), Bellavista, Puerto Baquerizo Moreno, Puerto Villamil  
    **Cómo:** Dron con fotogrametría (OpenDroneMap) + GNSS RTK; o LiDAR
- **[Pluviómetros en cada poblado y en la parte alta de cada cuenca (hoy: Lluvia: 4 estaciones IERSE en Santa…](https://github.com/mayait/sosgalapagos-datos/issues/19)** (#19 · prioridad 1)  
    **Hoy:** Lluvia: 4 estaciones IERSE en Santa Cruz (ninguna en Puerto Ayora) + red GSC en San Cristóbal  
    **Lo que necesitamos:** Pluviómetros en cada poblado y en la parte alta de cada cuenca  
    **Cómo:** Instalar pluviómetros (USFQ, FCD, ciudadanos) y sumarlos a `clima/`
- **[Revisar en campo los pluviómetros de Cerro Crocker y Los Guayabillos (IERSE)](https://github.com/mayait/sosgalapagos-datos/issues/56)** (#56 · prioridad 1)  
    · **Cerro Crocker:** parece fallar desde agosto de 2026 (9 y 18 mm en septiembre y octubre frente a 140 y 340 mm en Los Guayabillos).  
    · **Los Guayabillos:** marca 0 mm desde el 31-oct con cobertura completa, mientras Santa Rosa mide lluvia. Probablemente está obstruido.  
    Afectan a la regla de alerta ([#30](https://github.com/mayait/sosgalapagos-datos/issues/30)) y a la lluvia areal de los estudios. Coordinar con el IERSE.

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

## En Santa Cruz

- **[Alerta temprana por lluvia conectada al recolector (regla provisional v0.1 de La Cascada)](https://github.com/mayait/sosgalapagos-datos/issues/30)** (#30 · prioridad 1 · en curso)  
    **Depende de:** Clima en vivo, IDF  
    **Notas:** Calibrar: confirmar si hubo inundación el 3-oct, el 23-oct y el 1/2-nov; revisar el pluviómetro de Los Guayabillos (marca 0 desde el 31-oct). Después, aviso al bot de WhatsApp y al COE
- **[Inventario en terreno de cruces quebrada–vía](https://github.com/mayait/sosgalapagos-datos/issues/33)** (#33 · prioridad 1 · en curso · 2 comentarios)  
    **Notas:** El estudio de Santa Cruz los lista; falta verificar
- **[Modelo hidráulico 2D (HEC-RAS 2D, ANUGA o SFINCS) del escarpe, La Cascada y la salida](https://github.com/mayait/sosgalapagos-datos/issues/26)** (#26 · prioridad 2 · en curso · 1 comentario)  
    **Depende de:** DTM, caudales  
    **Notas:** Mancha, calados y velocidades por período de retorno

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

## En Santa Cruz

- **[¿Existe un protocolo de evacuación por inundación para La Cascada, Bellavista y El Aguacatal?](https://github.com/mayait/sosgalapagos-datos/issues/71)** (#71 · prioridad 1)  
    No se encontró ninguno, aunque la alerta naranja por El Niño rige desde el 20-jul. Dato en manos del GAD, el COE y la SNGR.  
    **Isla:** Santa Cruz  
    **Sale de:** 01_que_paso.md, tabla «Qué señales había»  
    https://sosgalapagos.org/estudios/santa-cruz/que-paso/  
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
