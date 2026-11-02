[[SALTO]]

# 9. Datos faltantes, herramientas y hoja de ruta técnica

## 9.1 Qué resolvería cada dato

Tabla: Datos faltantes y la pregunta que resuelve cada uno.

| Dato | Pregunta que resuelve |
|---|---|
| **Marcas de agua del evento** (GNSS), en el barrio y en la salida | Calibra la lámina y el frente de desborde. Si el agua llegó a ≈13 m, se confirma el vaso lleno hasta el umbral; una cota mucho mayor indicaría obstrucción o un caudal muy superior |
| **Pluviómetros del 30–31 de octubre** (FCD, INAMHI, privados) y GPM IMERG | Decide entre ECMWF de 9 km (≈110 mm) y los demás modelos (6–27 mm), fija la hora real y es la base de las curvas IDF |
| **Modelo del terreno de dron o LiDAR** (≤ 1 m, 5–10 km²) | Confirma o descarta el rebose a 12,95 m, los umbrales del cauce de OSM y la pendiente del interceptor en sus primeros 2,5 km (criterio C4) |
| **Huellas de crecida o aforos** en las quebradas | Calibran el CN y el tc. Si el caudal real es mucho menor que el calculado, domina la infiltración en el lecho de lava |
| **Ensayos de infiltración y geología** (grietas, tubos de lava) | Valida o descarta la alternativa G y el CN del Parque |
| **Catastro y red de sumideros** con cotas de fondo | Cuantifica la capacidad real de la salida urbana (alternativas C y D) |
| **Historial de OSM y fotografías aéreas históricas** del IGM | Confirma o refuta un drenaje histórico hacia el este y fecha la urbanización del borde del escarpe |
| **Datum vertical** del IGM frente a EGM2008 en la isla | Explica el sesgo de −2 m y fija las cotas absolutas respecto del mar |

## 9.2 Software y herramientas necesarias

Tabla: Herramientas por fase. Indica si funcionan de forma nativa en un Mac con Apple Silicon.

| Fase | Herramienta | Para qué | ¿Mac nativo? |
|---|---|---|---|
| Reconocimiento (hecho) | Python: rasterio, pysheds, shapely, scipy, matplotlib | Cuenca, vaso, perfiles, corredores, 3D | Sí |
| SIG de escritorio | **QGIS** con los complementos GRASS, SAGA y **WhiteboxTools** | Revisión visual, edición, análisis hidrológico alternativo y cartografía final | Sí |
| Topografía | Fotogrametría de dron: **OpenDroneMap** (libre) o Agisoft Metashape / Pix4D; GNSS RTK | Modelo del terreno de ≤ 1 m y marcas de agua | ODM con contenedor; Metashape sí |
| Hidrología | **HEC-HMS** (USACE, libre) | Lluvia-caudal calibrado por subcuencas, con pérdidas e infiltración | Sí (versión macOS) |
| Hidráulica 2D | **HEC-RAS 2D** (USACE) o **Iber** | Mancha, calados, velocidades, comparación de alternativas | No (Windows): máquina virtual (Parallels/UTM con Windows 11 ARM) o PC con Windows |
| Hidráulica 2D (alternativas) | **ANUGA** (Python), **LISFLOOD-FP**, **SFINCS** | Igual que la fila anterior, con código abierto | Sí o con `container` |
| Drenaje urbano | **EPA SWMM** o PCSWMM | Red de sumideros, colector y calle-canal (modelo 1D/2D dual) | Motor SWMM sí; interfaz de EPA solo en Windows |
| Lluvia | Cuenta gratuita de NASA Earthdata (GPM IMERG); Open-Meteo | Lluvia satelital y de modelos | Sí |

## 9.3 Hoja de ruta técnica

Tabla: Fases del estudio técnico.

| Fase | Plazo | Productos | Responsables sugeridos |
|---|---|---|---|
| 0. Evidencias del evento | Días | Marcas de agua (GNSS), encuesta de daños, fotografías georreferenciadas, lluvia medida | GAD, academia, sociedad civil |
| 1. Datos base | 2–6 semanas | Dron o LiDAR de 5–10 km²; catastro de sumideros y pasos bajo vías; ensayos de infiltración; IMERG; curvas IDF preliminares con la serie de la FCD | GAD, CGREG, FCD, academia |
| 2. Modelación | 1–3 meses | HEC-HMS calibrado con el evento; modelo 2D (HEC-RAS o ANUGA) del escarpe, el barrio y la salida; mapa de amenaza | GAD, CGREG, academia |
| 3. Alternativas | 3–6 meses | Comparación de las alternativas C a H y sus combinaciones (costo, beneficio, impacto, gobernanza) | GAD, CGREG, DPNG, MAATE |
| 4. Prefactibilidad y permisos | 6–18 meses | Diseño preliminar de la alternativa elegida; estudio de impacto ambiental si hay obra en el Parque; financiación | GAD, CGREG, DPNG, MAATE |
