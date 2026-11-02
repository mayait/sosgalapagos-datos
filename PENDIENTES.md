# Pendientes: datos, resolución, procesos y gestión del riesgo

Lista viva de lo que falta. Cada equipo marca lo que toma con su nombre y rama (`[ ]` → `[~] rama-x (equipo)` → `[x]`). Si algo nuevo aparece, se añade aquí en el mismo PR que lo descubre.

Prioridad: **P1** = cambia decisiones de esta emergencia · **P2** = mejora mucho el análisis · **P3** = deseable.

---

## 1. Datos que no tenemos (hay que pedirlos o levantarlos)

| | Dato | Prioridad | Quién lo tiene o puede levantarlo | Para qué sirve |
|---|---|---|---|---|
| [ ] | **Delimitación oficial de las áreas inundadas del 30–31-oct-2026** | P1 | COE cantonal, SNGR, vuelo de dron | Validar el modelo HAND y la capa `areas_afectadas` (hoy por validar) |
| [ ] | **Marcas de agua del evento** con GNSS (barrio La Cascada y su salida) | P1 | GAD Santa Cruz, academia, sociedad civil | Calibrar la lámina y el rebose del vaso de La Cascada (≈12–13 m) |
| [ ] | **Lluvia medida el 30–31-oct** en Puerto Ayora (no hay estación allí) | P1 | FCD, INAMHI, aeropuerto, pluviómetros privados | Decidir entre ECMWF 9 km (≈80–130 mm) y los otros modelos (0,2–26 mm) |
| [ ] | **Catastro municipal** (predios, edificios, usos) de los tres GAD | P1 | GAD Santa Cruz, San Cristóbal, Isabela | Exposición real por edificio en lugar de OSM + Open Buildings |
| [ ] | **Red de drenaje urbano**: sumideros, colectores, alcantarillas y pasos bajo vías con cotas de fondo | P1 | GAD (obras públicas), CGREG | Capacidad real de la salida urbana; cruces quebrada–vía |
| [ ] | **Refugios y puntos de encuentro para inundación** (distintos de los de tsunami) | P1 | COE, SNGR | Capa de puntos clave para esta amenaza |
| [ ] | **SIIG del CGREG** (requiere usuario) | P2 | CGREG | Capas oficiales de planificación y riesgos actualizadas |
| [ ] | **Censo 2022 por manzana** publicado | P2 | INEC | Población real; hoy es una estimación SNGR por vivienda |
| [ ] | **Aforos o huellas de crecida** en quebradas | P2 | Academia, DPNG | Calibrar CN y tiempo de concentración |
| [ ] | **Ensayos de infiltración y geología** (grietas, tubos de lava) | P2 | Academia, FCD | Pérdidas reales en el lecho de lava; alternativa de infiltración |
| [ ] | **Fotografías aéreas históricas del IGM** e historial de OSM | P3 | IGM | Drenajes históricos y fecha de urbanización del escarpe |
| [ ] | **Datum vertical**: IGM frente a EGM2008 en cada isla | P2 | IGM, INOCAR | Explicar el sesgo de −2 a −3 m del DSM y fijar cotas respecto del mar |
| [ ] | **Nivel del mar / mareógrafo** (Puerto Ayora, Baquerizo) | P3 | INOCAR | Costa baja y marejadas combinadas con lluvia |
| [ ] | **Registro histórico de eventos** completo (fechas, lugares, daños) | P2 | SNGR, GAD, prensa local | Frecuencia y validación de zonas susceptibles |
| [ ] | Floreana y resto de Isabela (hoy solo Isabela sur) | P3 | — | Cobertura completa de zonas pobladas |

## 2. Datos que tenemos pero con poca resolución

| | Hoy | Lo que necesitamos | Prioridad | Cómo |
|---|---|---|---|---|
| [ ] | **DSM Copernicus GLO-30** (30 m, incluye edificios y árboles) | **DTM ≤ 1 m** de los poblados: Puerto Ayora y escarpe (5–10 km²), Bellavista, Puerto Baquerizo Moreno, Puerto Villamil | P1 | Dron con fotogrametría (OpenDroneMap) + GNSS RTK; o LiDAR |
| [ ] | Curvas IGM 1:25 000 | Topografía urbana 1:1 000–1:5 000 si existe | P2 | Pedir a GAD / IGM |
| [ ] | Huellas de edificios: OSM + Google Open Buildings (no cubre San Cristóbal) | Huellas completas y con altura | P2 | Catastro, digitalización sobre ortofoto de dron |
| [ ] | Lluvia: 4 estaciones IERSE en Santa Cruz (ninguna en Puerto Ayora) + red GSC en San Cristóbal | Pluviómetros en cada poblado y en la parte alta de cada cuenca | P1 | Instalar pluviómetros (USFQ, FCD, ciudadanos) y sumarlos a `clima/` |
| [ ] | Lluvia de modelos (Open-Meteo, ECMWF 9 km) | Lluvia satelital GPM IMERG (30 min, 10 km) del evento y la serie | P2 | Cuenta NASA Earthdata |
| [ ] | Imágenes satelitales | Imagen de alta resolución posterior al evento | P2 | Maxar Open Data, Planet, Sentinel-1/2 |
| [ ] | Población estimada por vivienda (SNGR) | Población por manzana del censo | P2 | INEC |

## 3. Procesos que queremos hacer

| | Proceso | Prioridad | Depende de | Notas |
|---|---|---|---|---|
| [ ] | **Recalcular HAND con el DTM de dron** y validarlo con las marcas de agua | P1 | §2 DTM, §1 marcas | Ver [docs/modelo-hand.md](docs/modelo-hand.md) |
| [ ] | **Curvas IDF** (intensidad–duración–frecuencia) | P1 | Serie diaria GSC desde 2015, IERSE, FCD | Base de cualquier diseño de obra |
| [ ] | **Modelo lluvia–caudal (HEC-HMS)** por subcuenca, calibrado con el evento | P2 | IDF, aforos, infiltración | |
| [ ] | **Modelo hidráulico 2D** (HEC-RAS 2D, ANUGA o SFINCS) del escarpe, La Cascada y la salida | P2 | DTM, caudales | Mancha, calados y velocidades por período de retorno |
| [ ] | **Drenaje urbano 1D/2D** (SWMM) | P3 | Red de sumideros | |
| [ ] | **Mapa de amenaza por inundación** candidato a oficial (hoy no existe ninguno para Galápagos) | P1 | Los anteriores | Propuesta para SNGR, CGREG y GAD |
| [ ] | **Riesgo = amenaza × exposición × vulnerabilidad** por manzana | P2 | Catastro, censo | Hoy solo tenemos exposición |
| [~] | **Alerta temprana por lluvia**: umbrales por estación conectados al recolector. Hay una regla preliminar 0.1 para La Cascada (1 h / 3 h / 24 h + humedad antecedente; `clima/docs/umbrales-la-cascada.md`) | P1 | Clima en vivo, IDF | Calibrar: confirmar si hubo inundación el 3-oct, el 23-oct y el 1/2-nov; revisar el pluviómetro de Los Guayabillos (marca 0 desde el 31-oct). Después, aviso al bot de WhatsApp y al COE |
| [ ] | **Pronóstico 72 h** (ECMWF/GFS) en el panel de clima | P2 | — | |
| [ ] | **Susceptibilidad a movimientos en masa** (pendiente + lluvia + geología) | P2 | Geología | |
| [ ] | **Inventario en terreno de cruces quebrada–vía** | P1 | — | El estudio de Santa Cruz los lista; falta verificar |
| [ ] | Seguimiento de **El Niño** (ONI, temperatura del mar) | P3 | — | Contexto para alertas estacionales |

## 4. Plataforma y servidores

| | Tarea | Prioridad |
|---|---|---|
| [ ] | Decidir qué componente de mapa queda en la app (hay dos motores de capas en paralelo) | P1 |
| [ ] | Publicación automática desde `main` (CI que regenere y suba `/mapas` y `/estudios`) | P2 |
| [ ] | Validación automática en cada PR: GeoJSON válido, EPSG:4326, sin datos personales, catálogo completo | P2 |
| [ ] | Respaldo fuera del servidor de `clima.db` (hoy solo copias locales de 14 días) | P1 |
| [ ] | Monitoreo y aviso si el recolector de clima deja de correr | P1 |
| [ ] | WMS/WFS en producción (GeoServer) para que instituciones consuman las capas desde QGIS/ArcGIS | P3 |
| [ ] | Dividir el manifiesto `geodatos/scripts/capas.json` en un archivo por capa (`capas.d/<capa>.json`) y generar el agregado, para reducir conflictos entre ramas | P2 |
| [ ] | Generar el catálogo de capas (fuente, fecha, licencia, resolución, responsable) desde el manifiesto, en lugar de mantenerlo a mano | P2 |
| [ ] | Controlar el tamaño del repositorio: los GeoJSON regenerados pesan 8–15 MB por versión (evaluar Git LFS o publicar los generados como *release*) | P3 |
| [ ] | Renombrar capas y campos heredados que dicen «albergue» (p. ej. `albergues_sngr`) a «refugio» | P3 |

## 5. Gestión del riesgo y gobernanza de datos

| | Tarea | Prioridad |
|---|---|---|
| [ ] | Acuerdos de intercambio de datos con GAD, CGREG, DPNG, FCD, INAMHI, SNGR e INOCAR | P1 |
| [ ] | **Licencia IERSE CC BY-NC-ND 4.0 (sin derivadas):** decidir si las tablas consolidadas y los recortes de eventos derivados de IERSE se quedan en el repositorio público o pedir permiso al IERSE. Pedir también la licencia de los datos del GSC | P1 |
| [ ] | Metadatos por capa (fuente, fecha, licencia, resolución, responsable) en `catalogo/` para todas las capas | P2 |
| [ ] | Protocolo de datos personales (LOPDP): qué se depura, quién revisa, nunca subir crudos oficiales | P1 |
| [ ] | Distinguir siempre **dato oficial** de **modelo propio** en mapas y textos | P1 |
| [ ] | Definir la **licencia** del código (p. ej. MIT) y de los datos derivados (respetando ODbL de OSM y las de cada fuente) | P2 |
| [ ] | Formar un equipo local (USFQ, GAD, CGREG) que mantenga los datos después de la emergencia | P2 |
