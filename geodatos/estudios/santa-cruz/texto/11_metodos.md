Intro: Quién hizo este estudio de Santa Cruz y con qué datos, qué límites tiene, qué datos faltan y qué resolvería cada uno, con qué herramientas se trabajó, cómo se reproduce, las descargas y todas las fuentes y referencias.

# Quién lo hizo y para qué sirve

Es un reconocimiento de gabinete. **No es un diseño de ingeniería, ni un mapa oficial de amenaza, ni un dictamen profesional.** Ninguna cifra sustituye a un levantamiento topográfico, a la calibración con mediciones de campo ni a un modelo hidráulico bidimensional. **Ningún punto se ha visitado.** No sirve para decidir obras, permisos ni reasentamientos, y las cifras cambiarán cuando lleguen datos de campo.

**Quién lo hizo.** Lo elaboró un sistema de inteligencia artificial (Claude, de Anthropic) organizado como **comité de agentes especializados**, a pedido de la coordinación de respuesta de USFQ Galápagos:
- un asesor en hidrología e hidráulica;
- un especialista en meteorología;
- un especialista en gestión del riesgo de desastres;
- un especialista en planificación urbana y drenaje;
- un hidrólogo dedicado a San Cristóbal, que trabajó en un estudio aparte (ver [San Cristóbal: métodos](../../san-cristobal/metodos/)).

Cada especialista trabajó con los mismos datos. Sus discrepancias se resolvieron de forma explícita y un revisor científico independiente revisó la versión de La Cascada. **No lo han revisado profesionales habilitados**, y esa revisión es imprescindible antes de usar estas conclusiones para cualquier decisión.

# Datos y convenciones

## Con qué datos

- **Elevación:** modelo de superficie Copernicus GLO-30 (30 m). Incluye techos y vegetación, tiene un error vertical de ±2–4 m y un sesgo de unos −2 m respecto del IGM.
- **Cartografía:** IGM 1:25 000 y OpenStreetMap (31-oct-2026).
- **Edificios:** OSM y Google Open Buildings.
- **Población:** INEC.
- **Registros y capas de riesgo:** SNGR y CGREG.
- **Lluvia medida:** red IERSE-WSN de la Universidad del Azuay, con cuatro estaciones en Santa Cruz, una medición cada 5 minutos y datos desde abril de 2026.
- **Climatología:** Fundación Charles Darwin, 1965–2026.
- **Lluvia estimada por modelos:** Open-Meteo (ECMWF y otros).

## Convenciones

- Las horas son de Galápagos (UTC−6).
- Las cotas son del DSM. Bajo las tablas con cotas se repite la nota «Cota del DSM (±2–4 m), orientativa».
- Se distingue lo **medido [M]**, lo **estimado [E]** y lo **reportado [R]**. En las páginas se marca donde el tipo de dato cambia la lectura, sobre todo en la cronología y la lluvia.
- Se usa el término «refugio» para los lugares de acogida temporal.

# Vacíos de información y herramientas

## Qué resolvería cada dato

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

Las alternativas C, D y G y el criterio C4 se describen en [La Cascada: opciones que aparecen en el análisis](../la-cascada-opciones/).

## Herramientas

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

## Secuencia técnica habitual

Un estudio técnico de este tipo suele avanzar por fases. Los plazos son los habituales para cada producto.

Tabla: Fases del estudio técnico.

| Fase | Plazo | Productos |
|---|---|---|
| 0. Evidencias del evento | Días | Marcas de agua (GNSS), encuesta de daños, fotografías georreferenciadas, lluvia medida |
| 1. Datos base | 2–6 semanas | Dron o LiDAR de 5–10 km²; catastro de sumideros y pasos bajo vías; ensayos de infiltración; IMERG; primeras curvas IDF con la serie de la FCD |
| 2. Modelación | 1–3 meses | HEC-HMS calibrado con el evento; modelo 2D (HEC-RAS o ANUGA) del escarpe, el barrio y la salida; mapa de amenaza |
| 3. Alternativas | 3–6 meses | Comparación de las alternativas C a H y sus combinaciones (costo, beneficio, impacto, gobernanza) |
| 4. Prefactibilidad y permisos | 6–18 meses | Diseño a nivel de prefactibilidad de la alternativa que se elija; estudio de impacto ambiental si hay obra en el Parque; financiación |

# Reproducibilidad y descargas

## Reproducibilidad

Todo se regenera con los scripts `12` a `20` de `geodatos/scripts/` del repositorio público (https://github.com/mayait/sosgalapagos-datos), a partir de los datos de `geodatos/estudios/`. El contenido numérico y gráfico del análisis de La Cascada se regenera desde la carpeta `geodatos/` con:

- `.venv/bin/python -I scripts/12_cascada_analisis.py` (≈20 s): cuenca, vaso, curva cota-volumen, corredores, hidrogramas y `resumen.json`.
- `.venv/bin/python -I scripts/13_cascada_figuras.py`: las 12 figuras, en `estudios/la-cascada/figuras/`.
- `.venv/bin/python -I scripts/14_cascada_informe.py`: el informe en PDF de La Cascada, a partir de los textos de `estudios/la-cascada/texto/`.

Tabla: Archivos de datos del análisis de La Cascada (`estudios/la-cascada/datos/`).

| Archivo | Contenido |
|---|---|
| `cuenca_cascada.geojson`, `cauce_principal.geojson` | Subcuencas (ramas 1 y 2, local) y cauces D8 |
| `perfil_cauce.csv`, `secciones_barrio.csv` | Perfil longitudinal y secciones de ±600 m |
| `curva_cota_volumen.csv`, `mancha_13m…16m.geojson` | Vaso: área, volumen y exposición por cota; manchas de llenado |
| `salidas_rebose.geojson` | Caminos de rebose hacia el sur y el este |
| `rutas_desvio.geojson`, `perfil_interceptor_este.csv` | 34 trazados evaluados y perfil del interceptor este |
| `perfil_cauce_este.csv` | Verificación del cauce de OSM hacia el este |
| `hidrogramas.csv`, `lluvia_evento_ecmwf_horaria.csv` | 12 escenarios de diseño y 6 del evento |
| `lluvias/` | Lluvia diaria y horaria por modelo, climatología de la FCD, celdas de los modelos |
| `urbano/` | Salida urbana, obstáculos, zona baja, franja del cauce, cifras de exposición |
| `resumen.json` | Todas las cifras clave |

Los datos crudos (`descargas/`) no se publican porque pesan unos 430 MB y algunas capas oficiales contienen datos personales. Se regeneran con los scripts `01`–`07` del proyecto `geodatos`.

## Descargas

Todas las capas y tablas del estudio, en GeoJSON (WGS84) y CSV (UTF-8). Incluyen cotas del DSM de 30 m (±2–4 m) y lluvia con cortes de transmisión. Las fuentes y licencias están más abajo, en «Fuentes y referencias». Las capas que derivan de OpenStreetMap se distribuyen con licencia ODbL.

[[DESCARGAS]]

# Fuentes y referencias

Todas las fuentes en línea se consultaron el 2 de noviembre de 2026.

## Datos

- Copernicus DEM GLO-30 (ESA/Airbus): https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- IGM Ecuador, cartografía base 1:25 000 de Galápagos (servicio WFS `galapagos25`): https://www.geoportaligm.gob.ec/
- OpenStreetMap, extracto de Geofabrik del 31-oct-2026: https://download.geofabrik.de/south-america/ecuador.html
- Google Open Buildings v3: https://sites.research.google/open-buildings/
- Red IERSE-WSN, Universidad del Azuay: pluviómetros de Santa Cruz.
- Fundación Charles Darwin, Galapagos Climatology Database (CC BY-NC-SA 4.0): https://datazone.darwinfoundation.org/en/climate/puerto-ayora
- Open-Meteo, Forecast y Historical API: https://open-meteo.com/
- NOAA OISST v2.1 (ERDDAP CoastWatch): https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21NrtAgg.html
- NOAA CPC, índices semanales Niño y discusión diagnóstica ENSO (8-oct-2026): https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml
- NASA GES DISC, GPM IMERG Early V07: https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDE.07/

## Informes oficiales

- SNGR, SitRep n.º 01 «Lluvias con incidencia El Niño – Galápagos» (corte: 31-oct-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SITREP-Nro.-01-Lluvias_Galapagos_29.08.2026-31.10.2026.pdf
- SNGR, SitRep 67 nacional (corte: 1-nov-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SitRep-No-67-Lluvias-29082026-al-01112026-15h00f21.pdf
- SNGR, Resolución SNGR-193-2026 (alerta naranja): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/07/RESOLUCION-Nro-193_Cambio-alerta-naranja-El-Nino-f-signed-signed-signed-signed.pdf
- SNGR, SitRep n.º 01 de la época lluviosa 2023, Galápagos: https://www.gestionderiesgos.gob.ec/wp-content/uploads/2023/06/SITREP_Nr.-01_Epoca_Lluviosa_01012023_-Galapagos-.-..pdf
- CN-ERFEN, Informe Técnico Ejecutivo 010-2026: https://www.teleamazonas.com/uploads/files/2026/10/07/erfen_20261001.pdf

## Normativa

- Ley Orgánica para la Gestión Integral del Riesgo de Desastres (LOGIRD), R.O. 3.er Supl. 488, 30-I-2024: https://procuraduria.utpl.edu.ec/NormativaExterna/LEY%20ORG%C3%81NICA%20PARA%20LA%20GESTI%C3%93N%20INTEGRAL%20DEL%20RIESGO%20DE%20DESASTRES.pdf
- Ley Orgánica de Régimen Especial de Galápagos (LOREG), R.O. 2.º Supl. 520, 11-VI-2015: https://faolex.fao.org/docs/pdf/ecu166165.pdf
- Ley Orgánica de Ordenamiento Territorial, Uso y Gestión del Suelo (LOOTUGS), R.O. 790, 2016: https://www.asambleanacional.gob.ec/sites/default/files/private/asambleanacional/filesasambleanacionalnameuid-29/Leyes%202013-2017/110-territorial/RO-ley-ord-territ-ro-790-sup-05-07-2016.pdf
- Ordenanza del Plan Galápagos 2030: https://www.gobiernogalapagos.gob.ec/wp-content/uploads/downloads/2021/02/ordenanza_plan_galapagos_2030.pdf
- Marco de Sendai para la Reducción del Riesgo de Desastres 2015–2030: https://www.undrr.org/publication/sendai-framework-disaster-risk-reduction-2015-2030

## Literatura y casos comparables

- Di Baldassarre, G. et al. (2015). Debates—Perspectives on socio-hydrology: Capturing feedbacks between physical and social processes. *Water Resources Research*, 51, 4770–4781. https://doi.org/10.1002/2014WR016416
- Fragoso, M. et al. (2012). Crecidas súbitas de Madeira del 20-feb-2010. *Natural Hazards and Earth System Sciences*, 12, 715–730. https://nhess.copernicus.org/articles/12/715/2012/
- Lira, C. et al. (2013). Madeira, 20-feb-2010: inventario de deslizamientos y balance de sedimentos. *Natural Hazards and Earth System Sciences*, 13, 709–719. https://nhess.copernicus.org/articles/13/709/2013/
- Marzol, M. V. (2002). Análisis del aguacero del 31-mar-2002 en Santa Cruz de Tenerife. Asociación Española de Climatología: https://aeclim.org/wp-content/uploads/2016/02/0047_PU-SA-III-2002-MV_MARZOL.pdf
- Plan de Aguaceros de Copenhague (Climate-ADAPT): https://climate-adapt.eea.europa.eu/en/metadata/case-studies/the-economics-of-managing-heavy-rains-and-stormwater-in-copenhagen-2013-the-cloudburst-management-plan/
- Calidad del agua y acuífero de Puerto Ayora: MDPI *Water* 11(5):937, https://www.mdpi.com/2073-4441/11/5/937; MDPI *Sustainability* 12:8851, https://mdpi.com/2071-1050/12/21/8851
- USDA-NRCS (1986). *Urban Hydrology for Small Watersheds* (TR-55). Método SCS-CN e hidrograma unitario.
- Témez, J. R. (1978). *Cálculo hidrometeorológico de caudales máximos en pequeñas cuencas naturales*. MOPU, Madrid.

## Prensa (cifras de afectación y testimonios)

- Primicias, 31-oct-2026: https://www.primicias.ec/sociedad/fenomeno-elnino-ultimas-noticias-ecuador-emergencia-santa-cruz-lluvias-136171/
- El Comercio, 1-nov-2026: https://www.elcomercio.com/actualidad/galapagos-enfrenta-emergencia-humanitaria-recibe-ayuda-inundaciones/
- El Universo, 31-oct-2026: https://www.eluniverso.com/comunidad/ecuador/santa-cruz-en-emergencia-intensa-lluvia-inunda-barrios-y-obliga-a-evacuar-viviendas-de-isla-mas-poblada-de-galapagos-nota/
- Vistazo, 31-oct-2026: https://www.vistazo.com/amp/actualidad/2026-10-31-galapagos-mantiene-emergencia-inundaciones-ocasionadas-intensas-lluvias-CD11300417
- El Universo, 22-abr-2023 (falta de alcantarillado pluvial): https://www.eluniverso.com/noticias/ecuador/planes-de-contingencia-en-galapagos-por-las-lluvias-nota/
