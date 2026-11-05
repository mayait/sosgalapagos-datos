# Catálogo de fuentes oficiales y autorizadas: Galápagos (Santa Cruz, San Cristóbal, Isabela)

Paquete de datos para la gestión de emergencias por las inundaciones de El Niño de octubre de 2026.
Revisión hecha el **2026-11-01**. Todos los endpoints marcados con ✅ se probaron con `curl` en esa fecha.
No incluye OpenStreetMap ni Copernicus GLO-30, que se obtienen por separado.

**Recorte espacial usado en todas las descargas:** lon −91.3 a −89.2, lat −1.1 a −0.4 (EPSG:4326).
**Carpeta de descargas:** `geodatos/descargas/oficiales/` (72 GeoJSON, unos 126 MB en total, todos en EPSG:4326).

Leyenda: ✅ responde y descarga sin login · 🔒 requiere token o registro · ❌ no responde · ⚠️ responde, pero no cubre Galápagos

---

## 0. Resumen ejecutivo

| Necesidad | Mejor fuente que funciona | ¿Cubre Galápagos? |
|---|---|---|
| Amenaza o susceptibilidad a **inundación pluvial o fluvial** | **No existe una capa nacional oficial para Galápagos.** Las capas SNGR e INEC de inundación y movimientos en masa excluyen la provincia (0 entidades en el recorte). Lo más cercano: IGM 1:50k `area_inundacion_a` (zonas periódicamente inundables), CGREG «Encañadas» (quebradas con buffer de 20 m), CGREG «Riesgos antrópicos» (incluye flujos de lodo por El Niño) y el registro SNGR de eventos de inundación. | Parcial |
| Amenaza por **tsunami**, rutas de evacuación y zonas seguras | Servidor ArcGIS de la SNGR (`sgrportal.gestionderiesgos.gob.ec`) | ✅ Sí, para Puerto Ayora, Puerto Baquerizo Moreno y Puerto Villamil |
| Hidrografía (ríos, quebradas, cañadas) | IGM WFS `galapagos50k:rio_l` y CGREG «Encañadas» (GeoNode de la FCD) | ✅ |
| Topografía y cartografía base | IGM WFS `galapagos50k:*` (curvas, cotas, vías, edificios) | ✅ |
| Cartografía censal (manzanas, sectores, edificios) | INEC Marco Geoestadístico 2026 (`idgn.ecuadorencifras.gob.ec`) | ✅ |
| Población | SNGR e INEC (población por sector y por vivienda), WorldPop R2025A, GHSL | ✅ |
| Huellas de edificios | Google Open Buildings v3 ✅; Microsoft Global Buildings ❌ no cubre Galápagos | Google sí, Microsoft no |
| Salud, educación, refugios, puntos de encuentro | SNGR (copias de MSP 2023, MINEDUC 2021, refugios 2025, zonas seguras) | ✅ |
| Activaciones satelitales | No hay activaciones de Copernicus EMS ni del Charter para Galápagos (ni en 2026 ni en 2023) | ❌ |

---

## 1. Amenazas: inundación, movimientos en masa, tsunami

### 1.1 SNGR: servidor ArcGIS Enterprise (fuente principal) ✅

- **Editor:** Secretaría Nacional de Gestión de Riesgos (SNGR)
- **Raíz REST:** `https://sgrportal.gestionderiesgos.gob.ec/server/rest/services?f=json` (ArcGIS 11.3). Responde.
- **Portal:** `https://sgrportal.gestionderiesgos.gob.ec/portal/` (tableros públicos ENOS: `.../portal/apps/dashboards/1ec9311119484344b58ecc53d6f3a41f` para inundaciones y `.../74b925b1cfe049eea959943adf224744` para movimientos en masa, enlazados desde `https://alertasecuador.gob.ec/el_nino/zonas-expuestas/`)
- **Licencia:** no declarada. Son servicios públicos de una entidad estatal. Conviene citar a la SNGR.
- **Consulta tipo (GeoJSON):**
  `…/<servicio>/<capa>/query?where=1%3D1&geometry=-91.3,-1.1,-89.2,-0.4&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson`
- Las carpetas `INEC/*`, `0_GDB_MIN_PUB/institucion_educativa`, `0_GDB_MIN_PUB/parroquias_urbanas_CNEL` y `test` requieren **token** 🔒.

**Capas probadas que SÍ cubren Galápagos (descargadas):**

| Servicio/capa | Contenido | Entidades en el recorte | Archivo |
|---|---|---|---|
| `area_de_inundacion_por_tsunamis/MapServer/0` | Polígonos de inundación por tsunami de Puerto Ayora, Puerto Baquerizo y Puerto Villamil, con campo `ari` (clases 1 a 8). Probablemente derivados de las cartas INOCAR/JICA. | 449 | `sngr_tsunami_area_inundacion_inocar.geojson` |
| `Hosted/ZONA_INUNDACION_TSUNAMI/FeatureServer/0` | Zona de inundación por tsunami por parroquia, `clase_amen` | 11 | `sngr_tsunami_zona_inundacion_parroquia.geojson` |
| `Hosted/SUSCEPT_INUNDACION_TSUNAMI/FeatureServer/0` (también `SUSCEPT_INUNDACION_TSUNAMI/MapServer/0`) | Susceptibilidad a inundación por tsunami | 13 | `sngr_tsunami_susceptibilidad.geojson` |
| `Hosted/area_inundacion_x_tsunami_v/FeatureServer/0` | Área de inundación por tsunami por parroquia (CONALI) | 6 | `sngr_tsunami_area_x_parroquia.geojson` |
| `0_GDB_MIN_PUB/pd_tsunami/FeatureServer/0` | Sectores censales en zona de tsunami, con población (total, hombres, mujeres, pobreza) y personas con discapacidad por tipo | 25 | `sngr_tsunami_poblacion_discapacidad_sectores.geojson` |
| `0_GDB_MIN_PUB/pd_sirena_tsunami/FeatureServer/0` | Sectores dentro del radio de las sirenas de tsunami, con población y discapacidad | 50 | `sngr_sirena_tsunami_poblacion_sectores.geojson` |
| `Monitoreo/sirenas/FeatureServer/0` | Sirenas del Sistema de Alerta Temprana (SAT) de tsunami | 4 | `sngr_sirenas_sat.geojson` |
| `Hosted/Rutas_Evacuacion/FeatureServer/0` | Rutas de evacuación (Puerto Ayora 63, Puerto Baquerizo Moreno 21, Puerto Villamil 18, El Progreso 2) | 104 | `sngr_rutas_evacuacion.geojson` |
| `SAT/MapServer/1` | Rutas de evacuación de 2016, versión anterior (no admite paginación) | 96 | `sngr_sat_rutas_evacuacion_2016.geojson` |
| `Hosted/Zonas_Seguras/FeatureServer/0` | **Zonas de seguridad y puntos de encuentro** (`tipo_seña`, `capacidad`, `nombre_ref`): Puerto Baquerizo Moreno 8, El Progreso 1, Puerto Ayora 2 (Estadio Pampas Coloradas, Coliseo), Puerto Villamil 1 (San Vicente) | 12 | `sngr_zonas_seguras_puntos_encuentro.geojson` |
| `Hosted/POBLACION_A_EVACUAR/FeatureServer/0` | Puntos de vivienda con población dentro de las parroquias con tsunami (`pob_x_casa`, `amenazas_exp`) | 1 075 | `sngr_poblacion_a_evacuar_tsunami.geojson` |
| `VIVIENDAS/MapServer/0` (POB_VIV_INU_MM) | Puntos de vivienda con población estimada por casa (`pob_x_casa`). Los campos de susceptibilidad están **vacíos** en Galápagos. | 9 475 | `sngr_viviendas_pob_susceptibilidad.geojson` |
| `Hosted/POB_VIV_MM_INU_PARR_STATIS/FeatureServer/0` | Población y viviendas expuestas a inundación y movimientos en masa por parroquia | 8 | `sngr_pob_viv_expuesta_parroquia.geojson` |
| `Hosted/eventos_historicos/FeatureServer/0` | Eventos peligrosos históricos registrados por la SNGR: 28 inundaciones, 3 deslizamientos, 1 aluvión, 2 oleajes, 2 tsunamis, entre otros | 126 | `sngr_eventos_historicos.geojson` |
| `Hosted/EVENTOS_X_LLUVIAS/FeatureServer/0` | Eventos por lluvias (época lluviosa) | 7 | `sngr_eventos_lluvias.geojson` |
| `Hosted/EVENT_ADV_HOST/FeatureServer/0` | Eventos adversos de la Red de Monitoreo (inundación en Puerto Ayora, deslizamiento en Las Tijeretas, entre otros) | 8 | `sngr_eventos_adversos_redm.geojson` |
| `Hosted/Parroquia_ENOS_ACT/FeatureServer/0` | Estado del Plan de Acción ENOS 2026 por parroquia | 8 | `sngr_plan_accion_enos_parroquias.geojson` |
| `Hosted/INFORM_CANT_09032026/FeatureServer/0` | Índice de riesgo INFORM cantonal (marzo de 2026) | 3 | `sngr_inform_riesgo_cantonal_2026.geojson` |

**Capas probadas que NO cubren Galápagos** ⚠️ (0 entidades en el recorte, aunque el servicio responde):
`Susceptibilidad_de_Inundaciones/MapServer/0` (43 058 entidades a nivel nacional), `SUSCEPT_INUNDACIONES_Z`, `Zonas_Susept_Inundaciones`, `ZONAS_SUSCEPTIBLES_INUNDACIONES`, `Hosted/ZONAS_SUSCEPTIBLES_INUNDACIONES_CT1500`, `SUSCEP_MOVIMIENTO_MASA`, `SUSCEPTIBILIDAD_MOV_MASAS`, `Movimientos_Masa` (raster), `0_GDB_MIN_PUB/pd_inundaciones`, `0_GDB_MIN_PUB/pd_mov_masa`, `Hosted/MULTIAMENAZAS_EC`, `Hosted/MULTIAMENAZAS_SGR`, `Hosted/Polígono_de_afectación_ENOS`, `Hosted/Area_afectación_ENOS_C1500`, `Hosted/Z_Seguras_Rutas_2026` y `Hosted/Zonas_Seguras_Tsunami_Z4` (estas dos solo cubren el continente), `Hosted/CURVAS_NIVEL`, `Hosted/RIO_L`. **Conclusión:** el mapa nacional de susceptibilidad a inundaciones y movimientos en masa de la SNGR no incluye la región insular.

### 1.2 INEC: capas de amenaza en el servidor IDGN ✅ / ⚠️

- `https://idgn.ecuadorencifras.gob.ec/server/rest/services/Hosted/TSUNAMI_inec/FeatureServer/0`: celdas con viviendas y población (`viv_sum`, `pob_sum`) por categoría de amenaza de tsunami. Tiene **55** entidades en el recorte. Archivo: `inec_tsunami_pob_viv_celdas.geojson`.
- `Hosted/INUNDACIONES` y `Hosted/MOVMASA` responden, pero tienen **0** entidades en Galápagos ⚠️.

### 1.3 CGREG, publicado en el GeoNode de la Fundación Charles Darwin ✅

- **URL:** `https://geodata.fcdarwin.org.ec/` · WFS `https://geodata.fcdarwin.org.ec/geoserver/ows?service=WFS&request=GetCapabilities` (71 capas) · WMS en la misma ruta con `service=WMS` · API `https://geodata.fcdarwin.org.ec/api/v2/datasets`
- **Autoría:** Consejo de Gobierno del Régimen Especial de Galápagos (CGREG), según el campo de atribución de cada capa. Licencia «not_specified».
- **Descarga tipo:** `…/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&outputFormat=application/json&srsName=EPSG:4326&typeName=geonode:<capa>`

| Capa (`geonode:`) | Contenido | Entidades | Archivo |
|---|---|---|---|
| `riesgo_inundacion_santa_cruz_4385cf…` | Riesgo de inundación **por tsunami** en la bahía Academy (Puerto Ayora), dato de 2020 | 2 | `fcd_riesgo_inundacion_santa_cruz.geojson` |
| `riesgo_inundacion_isabela_1d417e…` | Lo mismo para Puerto Villamil | 1 | `fcd_riesgo_inundacion_isabela.geojson` |
| `riesgos_antropicos_e96933…` | Riesgos antrópicos, entre ellos **«Flujos de lodo y escombros en el fenómeno de El Niño»** (3) y «Derrumbes» (4) | 31 | `fcd_riesgos_antropicos.geojson` |
| `encanadas_buffer_20m_61b526…` | **Encañadas**: quebradas de escurrimiento intermitente con buffer de 20 m, en todo el archipiélago | 539 | `fcd_encanadas_buffer_20m.geojson` |

No hay capa de riesgo de inundación para San Cristóbal (solo para Floreana, Isabela y Santa Cruz).

### 1.4 INOCAR (tsunami) 🔒 / sin servicio

- `https://www.inocar.mil.ec/web/index.php/tsunamis` y `https://www.inocar.mil.ec/tsunamis/eventos.php` responden, pero **no publican descargas GIS ni WMS**. `https://coos.inocar.mil.ec/geoserver/` devuelve 404.
- Las cartas de inundación por tsunami de Galápagos (INOCAR con JICA) se pueden usar a través de la capa SNGR `area_de_inundacion_por_tsunamis` (ver 1.1). Para obtener los PDF o shapefiles originales hay que pedirlos a INOCAR (Dirección de Oceanografía).

### 1.5 Otras

- **Alístate Ecuador / Atlas Nacional de Riesgos (SNGR):** visores web. Los datos están detrás de los servicios de 1.1.
- **Google Drive SNGR «Zonas expuestas El Niño 2026»:** `https://drive.google.com/drive/folders/1PefrWAvVKXnUnz9Z5NvMEp9wNMzqOd_z` (enlazado desde alertasecuador.gob.ec). Contiene mapas en PDF o imagen. No se descargó.
- **GAD municipales (Santa Cruz, San Cristóbal, Isabela):** no encontré mapas de amenaza ni catastro descargables. Ver 3.3.

---

## 2. Hidrografía

| Fuente | Endpoint | Estado | Contenido y cobertura |
|---|---|---|---|
| **IGM 1:50 000 Galápagos** | WFS `http://www.geoportaligm.gob.ec/50k/wfs?service=WFS&request=GetCapabilities` · capas `galapagos50k:rio_l`, `lago_laguna_a`, `area_inundacion_a`, `cienaga_a`, `zanja_l`, `estanque_a`, `zona_manglar_a`, `acueducto_canal_l` | ✅ | Ríos y quebradas (casi todos intermitentes), lagunas y zonas periódicamente inundables. **Archivos:** `igm50k_gal_rio_l` (548), `igm50k_gal_area_inundacion_a` (14), `igm50k_gal_lago_laguna_a` (42), `igm50k_gal_cienaga_a` (1), `igm50k_gal_zanja_l` (8), `igm50k_gal_estanque_a` (1), `igm50k_gal_zona_manglar_a` (54) |
| **CGREG Encañadas** | GeoNode de la FCD (ver 1.3) | ✅ | Quebradas con buffer de 20 m (539 entidades) |
| **CGREG Recarga hídrica** | `geonode:scr_recarga_hidrica_…`, `stx_recarga_hidrica_…`, `isa_recarga_hidrica_…` | ✅ | Zonas de interés hidrogeológico. Archivos `fcd_recarga_hidrica_*` (3, 2 y 3 entidades). También `fcd_captacion_agua` (44). |
| **MAATE IDE (antes SENAGUA)** | WMS/WFS `http://ide.ambiente.gob.ec:8080/geoserver/ows?service=WMS&request=GetCapabilities` (`mae_ide:*`) | ✅ / ⚠️ | Unidades hidrográficas Pfafstetter N1 a N6, `unidad_hidrica_N7_50K_2017`, demarcaciones. **No hay unidades Pfafstetter propias de Galápagos.** La N7 1:50k da 0 entidades. `v_hb004_unidad_planificacion_hidrografica_local_a` tiene un solo polígono «GALÁPAGOS» (Demarcación Manabí). **No hay microcuencas oficiales para las islas.** |

Para microcuencas y cauces de detalle conviene derivarlos del DEM GLO-30 y validarlos con `igm50k_gal_rio_l` y `fcd_encanadas_buffer_20m`.

---

## 3. Topografía, cartografía base y catastro

### 3.1 IGM: Instituto Geográfico Militar ✅

- **WMS 1:50k:** `http://www.geoportaligm.gob.ec/50k/wms?service=WMS&request=GetCapabilities` (1 323 nombres de capa; el espacio de trabajo `galapagos50k` tiene 67 capas)
- **WFS 1:50k:** `http://www.geoportaligm.gob.ec/50k/wfs` (WFS 2.0.0, admite `outputFormat=application/json`). Sistema nativo **EPSG:32715** (UTM 15S). Para filtrar por bbox en grados hay que añadir el CRS: `&bbox=-91.3,-1.1,-89.2,-0.4,EPSG:4326`. Sin él, el bbox se interpreta en UTM y la respuesta llega vacía.
- **WMS de mapa base:** `https://www.geoportaligm.gob.ec/geoserver/ows?service=WMS&request=GetCapabilities`. Capa `mapabase:50k_galapagos` (Galápagos 1:50 000). `mapabase:actual_5k`, `25k` y `50k_actualizada` **no cubren Galápagos** (su extensión empieza en −81°). También hay `mapabase:igmdtm`, un DTM que sí llega a −92°.
- **Descarga de shapefiles:** `https://www.geoportaligm.gob.ec/downloads/public/` 🔒 (requiere registro gratuito)
- **Licencia:** uso libre con cita al IGM. La cartografía «reservada» (`igm_reservada:*`) no es pública.
- **No existe cartografía IGM 1:5 000 de Galápagos** en los servicios públicos.

Capas `galapagos50k:*` descargadas (con el bbox de las tres islas):

| Capa | Entidades | Archivo |
|---|---|---|
| `curva_nivel_l` (curvas de nivel). La capa completa pesa unos 60 MB, así que solo se descargaron recortes alrededor de los pueblos. | 115 (Santa Cruz sur, bbox −90.45,−0.78,−90.25,−0.6) · 57 (San Cristóbal oeste, −89.65,−0.96,−89.4,−0.84) | `igm50k_gal_curva_nivel_l_scz_sur`, `igm50k_gal_curva_nivel_l_sc_oeste` |
| Isabela sur (−91.15,−0.98,−90.9,−0.8): **no se guardó**, porque pesaba 21,8 MB y tenía solo 64 líneas | — | (se baja con la misma consulta) |
| `punto_acotado_cota_p` (cotas) | 15 378 | `igm50k_gal_punto_acotado_cota_p` |
| `via_ruta_l` (vías) | 1 458 | `igm50k_gal_via_ruta_l` |
| `edificio_p` / `edificio_a` | 1 146 / 8 | `igm50k_gal_edificio_p`, `igm50k_gal_edificio_a` |
| `zona_edificada_a` (manchas urbanas) | 5 | `igm50k_gal_zona_edificada_a` |
| `poblado_p` / `nombre_sitio_p` (toponimia) | 11 / 237 | `igm50k_gal_poblado_p`, `igm50k_gal_nombre_sitio_p` |
| `isla_a` (línea de costa) | 38 | `igm50k_gal_isla_a` |
| `grieta_l` | 82 | `igm50k_gal_grieta_l` |
| `aeropuerto_a`, `pista_aterrizaje_a`, `muelle_a`, `central_electrica_p`, `tanque_almacenamiento_p`, `torre_agua_p` | 2, 1, 1, 1, 28, 1 | `igm50k_gal_*` |

### 3.1b SGIAR: DTM de 1 m de Santa Cruz ✅ (entregado, sin servicio en línea)

- **Fuente:** SGIAR, Subsecretaría de Gestión de la Información y Análisis de Riesgo. Producto Vricon DTM (Maxar), estéreo satelital con imágenes de 2020 a 2024. Pedido 7032308101286995205 del 25-jul-2026.
- **Cobertura:** Puerto Ayora, el escarpe y Bellavista, 183 km² (lon −90,392 a −90,281, lat −0,773 a −0,638). Resolución de 1 m, EPSG:32715, cotas sobre EGM2008.
- **En el repositorio:** `geodatos/datos/dtm_sgiar/`, generado por `35_dtm_sgiar.py` a partir del zip en `descargas/sgiar/`. Ficha, cita y control de calidad en su `LEEME.md`.
- **Licencia:** EULA de Vricon/Maxar. La SGIAR autorizó publicarlo en este repositorio. Cita obligatoria a la SGIAR.

### 3.2 Límites administrativos y suelo urbano

| Fuente | Endpoint | Entidades | Archivo |
|---|---|---|---|
| CONALI 2026, parroquias (en el servidor SNGR) | `https://sgrportal.gestionderiesgos.gob.ec/server/rest/services/Hosted/LIM_PARR_2026/FeatureServer/1` | 8 | `sngr_conali_parroquias_2026.geojson` |
| CONALI 2026, cantones | `…/Hosted/LIM_CANT_2026/FeatureServer/1` | 3 | `sngr_conali_cantones_2026.geojson` |
| **CGREG límite urbano y rural** | `geonode:urbano_rural` (FCD GeoNode). Polígonos de suelo urbano de Puerto Ayora, Bellavista, Santa Rosa, Puerto Villamil, El Progreso y otros, con población de 2015. | 27 | `fcd_urbano_rural.geojson` |
| CGREG estructura del suelo urbano y rural (2021) | `geonode:estructura_suelo_urbano_rural_21_12_21` | 66 | `fcd_estructura_suelo_urbano_rural.geojson` |
| CGREG barrios | `geonode:barrios`, `geonode:barrios_de_puerto_ayora` | 31 / 18 | `fcd_barrios.geojson`, `fcd_barrios_puerto_ayora.geojson` |
| CGREG asentamientos humanos | `geonode:asentamientos_humanos_…` | 44 | `fcd_asentamientos_humanos.geojson` |
| MAATE SNAP: Parque Nacional y Reserva Marina de Galápagos. El suelo fuera del parque es la zona urbana y agrícola. | WFS `http://ide.ambiente.gob.ec:8080/geoserver/wfs` · `mae_ide:fa210_snap_galapagos_a` | 2 | `maate_snap_pn_reserva_marina_galapagos.geojson` |
| PNG zonificación 2017 (terrestre) | `geonode:zonificacion_2017_terrestre` | 117 | `fcd_zonificacion_png_2017_terrestre.geojson` |
| HDX COD-AB Ecuador (OCHA) | `https://data.humdata.org/dataset/cod-ab-ecu` → `ecu_adm_2024.zip` (CC BY-IGO) | — | no descargado (se puede usar como alternativa) |

### 3.3 Catastro urbano municipal 🔒 / ❌

- **GAD Santa Cruz:** `https://www.gadsantacruz.gob.ec/` responde, pero no ofrece geoportal ni catastro descargable.
- **GAD San Cristóbal e Isabela:** los dominios probados (`municipiosancristobal.gob.ec`, `isabela.gob.ec`, `gadmisabela.gob.ec`) **no responden**.
- **CGREG SIIG:** `https://siig.gobiernogalapagos.gob.ec/` no responde. La versión interna (`siig-intra.gobiernogalapagos.gob.ec`) exige **login Keycloak** 🔒.
- **Recomendación:** pedir el catastro (predios y construcciones) directamente a las Direcciones de Avalúos y Catastros de cada GAD o al CGREG. Mientras tanto, se pueden usar como sustitutos las manzanas y edificios censales de INEC (sección 4), los edificios de Google Open Buildings y los edificios IGM.

---

## 4. Áreas pobladas y población

### 4.1 INEC: Marco Geoestadístico Nacional (cartografía censal 2022, actualizada en 2026) ✅

- **REST:** `https://idgn.ecuadorencifras.gob.ec/server/rest/services/PortalMGN/MGNWMS2026/MapServer` (ArcGIS 10.71, `Query` habilitado, maxRecordCount 2000)
- **WMS oficial:** `https://idgn.ecuadorencifras.gob.ec/server/services/PortalMGN/MGNWMS2026/MapServer/WMSServer?service=WMS&request=GetCapabilities` ✅. Fuente: `https://www.ecuadorencifras.gob.ec/documentos/web-inec/Geografia_Estadistica/wmsSW.txt`
- **Alternativas:** `…/Cartografia_Censal_WMS_2022/MapServer` y `…/Hosted/Marco_Geoestadistico_2022/FeatureServer`, con las mismas capas en la versión 2022.
- **Capas:** 0 `ejes_l`, 1 `ca04_l`, 2 `edif_p`, 3 `loc_p`, 4 `ingresos_l`, 5 `sector_disperso`, 6 `sector_amanzanado`, 7 a 9 límites, 10 `zon`, 11 `sec`, 12 `man`
- **Licencia:** datos públicos del INEC, con cita obligatoria. Las geometrías de `man`, `sec` y `zon` están **simplificadas** (`*_simp`).
- **Nota:** la API de Python `urllib` recibió HTTP 400 en algunas consultas. Con `curl` y un User-Agent de navegador funciona.

| Capa | Entidades | Archivo |
|---|---|---|
| `man` manzanas censales (`man` = código de 15 dígitos) | 820 | `inec_mgn2026_manzanas.geojson` |
| `sec` sectores censales (`sec` = código de 12 dígitos) | 113 | `inec_mgn2026_sectores.geojson` |
| `zon` zonas censales | 13 | `inec_mgn2026_zonas.geojson` |
| `loc_p` localidades | 69 | `inec_mgn2026_localidades.geojson` |
| `edif_p` edificios censales (multipunto, con código `edif_cod`) | 10 982 | `inec_mgn2026_edificios_censales.geojson` |
| `ejes_l` ejes viales con nombre de calle | 2 019 | `inec_mgn2026_ejes_viales.geojson` |
| `Hosted/parroquias_pob` población parroquial (por ejemplo, Puerto Baquerizo Moreno 7 290 y El Progreso 865) | 7 | `inec_parroquias_poblacion2022.geojson` |
| `Hosted/DEGURBA_DATOS_2022_Dissolve` celdas de grado de urbanización con suma de población, viviendas, salud y educación (zona «INSULAR») | 15 | `inec_degurba2022_celdas.geojson` |

**Tabulados del Censo 2022 para unir por código** (no descargados por su tamaño):
- Sector: `https://www.ecuadorencifras.gob.ec/documentos/web-inec/bd-censo/sector/BDD_CPV2022_SECT_CSV.zip` (595 MB)
- Manzana y localidad: `https://www.ecuadorencifras.gob.ec/documentos/web-inec/bd-censo/manzana/BDD_CPV2022_MANLOC_CSV.zip` (597 MB)
- Capa nacional de sectores: `https://www.ecuadorencifras.gob.ec/documentos/web-inec/capa/CapaSectores.zip` (423 MB)
- Geodatabase nacional 2021: `…/Geografia_Estadistica/Documentos/GEODATABASE_NACIONAL_2021.zip` (2,9 GB)
- Clasificador geográfico 2026: `…/Cartografia/Clasificador_Geografico/CLASIFICADOR_GEOGRAFICO_2026.zip` (0,9 MB)
- Para tener la población por sector sin bajar estos archivos, se pueden usar las capas SNGR `pd_tsunami` y `pd_sirena_tsunami` (sección 1.1), que ya traen población por sector, aunque solo para los sectores expuestos.

### 4.2 Productos globales de población

| Fuente | URL | Formato y licencia | ¿Cubre Galápagos? (verificado) |
|---|---|---|---|
| **WorldPop R2025A, 100 m, constrained, 2026** | `https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2026/ECU/v1/100m/constrained/ecu_pop_2026_CN_100m_R2025A_v1.tif` (25 MB). Listado en `https://hub.worldpop.org/rest/data/pop/G2_CN_POP_R25A_100m?iso3=ECU`. | GeoTIFF, CC BY 4.0 | ✅ Sí. La extensión del archivo empieza en −92.01. Sumas de prueba: Santa Cruz unas 18 500 personas, San Cristóbal unas 8 850, Isabela sur unas 3 200. |
| **GHSL GHS-POP R2023A, época 2025, 3″** | `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_4326_3ss/V1-0/tiles/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0_R{9,10}_C{9,10}.zip` (de 1,6 a 5,4 MB por tesela) | GeoTIFF, CC BY 4.0 | ✅ Sí. Las islas caen en 4 teselas: R9 y R10, C9 y C10. En R10_C10 San Cristóbal suma unas 9 900 personas. Se aplica igual a GHS-BUILT-S y GHS-SMOD. |
| **Google Open Buildings v3** | `https://storage.googleapis.com/open-buildings-data/v3/polygons_s2_level_4_gzip/9ab_buildings.csv.gz` (Santa Cruz e Isabela, 1,6 MB, 16 122 edificios) y `…/901_buildings.csv.gz` (San Cristóbal, 0,5 MB, 5 585 edificios). Índice: `…/v3/score_thresholds_s2_level_4.csv`. | CSV con WKT, CC BY 4.0 / ODbL | ✅ Sí. **Descargado y recortado:** `google_open_buildings_v3_galapagos.geojson` (**21 157** polígonos, con campos `confidence`, `area_m2` y `plus_code`). Conviene filtrar por `confidence ≥ 0.7`. |
| **Microsoft Global ML Building Footprints** | `https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv` | GeoJSONL, ODbL | ❌ **No.** Ecuador tiene 62 quadkeys, todos continentales. No hay ningún quadkey de Galápagos (por ejemplo, 201111113 para Puerto Ayora o 210000002 para Puerto Baquerizo). |
| **Overture Maps, tema buildings** | `s3://overturemaps-us-west-2/release/<versión>/theme=buildings/type=building/` (GeoParquet) | ODbL / CDLA | No se probó con consulta, porque no hay DuckDB ni GDAL disponibles. Overture combina OSM, Google y Microsoft, así que en Galápagos debería traer OSM más Google. |
| **VIDA Google+Microsoft por país** | `https://data.source.coop/vida/google-microsoft-open-buildings/geoparquet/by_country/country_iso=ECU/ECU.parquet` | GeoParquet, 1,2 GB | ✅ responde (HTTP 200), pero no se descargó por su tamaño |

---

## 5. Activaciones satelitales y delineación de inundaciones

| Mecanismo | Resultado (API o listados consultados el 2026-11-01) |
|---|---|
| **Copernicus EMS Rapid Mapping** (API `https://mapping.emergency.copernicus.eu/activations/api/activations/`) | Hay 5 activaciones en Ecuador: **EMSR870** (inundación, 2026-03-11, 13 AOI continentales: Alluriquín, Quinindé, Manta, Machala, Esmeraldas, Babahoyo y otras), EMSR813 (2025-07), EMSR796 (2025-03), EMSR789 (2025-02) y EMSR159 (sismo de 2016). **Ninguna cubre Galápagos.** Detalle de AOI: `https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?code=EMSR870` |
| **International Charter Space & Major Disasters** | Activaciones en Ecuador: 862 (febrero de 2024, El Niño costa), 822 (junio de 2023, Esmeraldas), 810 (marzo de 2023, ciclón Yaku) y 749 (2022). **Ninguna para Galápagos ni para octubre de 2026.** `https://disasterscharter.org/activations/flood-in-ecuador-activation-862-` |
| **UNOSAT** | No encontré productos para Galápagos. |
| **Eventos de 2023 en Galápagos (referencia)** | SITREP SNGR «Época lluviosa 2023, Galápagos»: `https://www.gestionderiesgos.gob.ec/wp-content/uploads/2023/06/SITREP_Nr.-01_Epoca_Lluviosa_01012023_-Galapagos-.-..pdf` (inundaciones en Puerto Ayora el 15 de abril de 2023 y en San Cristóbal). Los puntos están en `sngr_eventos_historicos.geojson`. |
| **SitReps de lluvias 2026 (SNGR)** | Por ejemplo: `https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/06/SitRep-No-116-Lluvias-01012026-al-09062026-14h00.pdf`. Galápagos registra muy pocos eventos. |

**Recomendación:** si se necesita delinear la inundación de octubre de 2026, la vía es que la SNGR solicite la activación de CEMS o del Charter. Otra opción es una delineación propia con Sentinel-1 (Copernicus Browser o GEE) y PlanetScope, porque no existe un producto oficial.

---

## 6. Infraestructura crítica

| Capa | Fuente y endpoint | Entidades | Archivo | Notas |
|---|---|---|---|---|
| **Establecimientos de salud 2023 (MSP, vía SNGR)** | `https://sgrportal.gestionderiesgos.gob.ec/server/rest/services/Hosted/Establecimientos_de_Salud/FeatureServer/0` | 94 | `sngr_msp_establecimientos_salud_2023.geojson` | Incluye el Hospital General de San Cristóbal, centros de salud tipo A del MSP y del IESS, puestos de salud y muchos consultorios privados (campo `estado`: ACTIVADO o EN REVISION). Hay que filtrar por `institución` y `tipología`. |
| Instituciones educativas 2021 (MINEDUC, vía SNGR) | `…/Hosted/Instituciones_Educativas/FeatureServer/0` (también `institucion_educativa_enterprise/MapServer/0`) | 21 | `sngr_mineduc_instituciones_educativas_2021.geojson` | Parece incompleta. Conviene contrastarla con el AMIE del MINEDUC. |
| **Albergues y alojamientos temporales activos 2025** | `…/Hosted/ALOJAMIENTOS_TEMPORALES_ACTIVOS/FeatureServer/0` | 6 | `sngr_albergues_activos_2025.geojson` | ⚠️ Incluye **nombres y teléfonos** de responsables. Es dato personal: no se debe redistribuir públicamente. |
| **Zonas seguras y puntos de encuentro** | `…/Hosted/Zonas_Seguras/FeatureServer/0` | 12 | `sngr_zonas_seguras_puntos_encuentro.geojson` | Pensados para tsunami. Tienen capacidad y señalética. |
| Rutas de evacuación | ver 1.1 | 104 | `sngr_rutas_evacuacion.geojson` | |
| Sirenas SAT | ver 1.1 | 4 | `sngr_sirenas_sat.geojson` | |
| Infraestructura CGREG (agua, energía, residuos) | GeoNode FCD: `captacion_agua`, `tratamiento_agua_potable`, `tuberia_agua`, `central_electrica`, `sub_estaciones`, `linea_transporte_electrico`, `gasolinera`, `relleno_sanitario`, `helipuerto`, `muelle`, `aeropuerto` | — | solo se descargó `fcd_captacion_agua` (44) | El resto se baja con la misma consulta WFS. |
| ECU 911, centrales eléctricas, subestaciones (SNGR) | `Hosted/ECU911`, `Hosted/CENTRALES_DE_GENERACIÓN_ELECTRICA`, `Hosted/SUBESTACION_ELECTRICA` | 0 | — | ⚠️ No cubren Galápagos. |
| MSP / MINEDUC directos | geoportales propios | — | — | No se probaron. La SNGR republica sus datos. |

---

## 7. Observaciones y advertencias

1. **Hueco crítico:** no existe un mapa oficial de amenaza o susceptibilidad a inundación pluvial para las islas, ni de la SNGR, ni del INEC, ni del MAATE. Para el evento de 2026 habrá que combinar el DEM GLO-30, las encañadas del CGREG, `rio_l` y `area_inundacion_a` del IGM y los eventos históricos de la SNGR.
2. **Los datos de tsunami son abundantes y están actualizados.** Ojo: las zonas seguras y rutas de tsunami no son necesariamente adecuadas para inundación pluvial, porque los puntos altos de evacuación por tsunami pueden estar en cauces de quebradas.
3. **Seguridad:** al revisar las fuentes se encontró un problema de configuración en algunos servicios públicos del INEC y de la SNGR. Se reporta a las instituciones por un canal privado. Aquí solo se hicieron **lecturas**; usa siempre los **MapServer** en modo de solo lectura.
4. El servidor SNGR expone servicios **Survey123** con registros de asistencia humanitaria y formularios. **No se consultaron**, porque pueden contener datos personales.
5. Las fechas de los datos varían: CONALI 2026, MGN 2021 a 2026, MSP 2023, MINEDUC 2021, refugios 2025, IGM 1:50k Galápagos de fecha no declarada y CGREG de 2020 a 2024.
6. Todo el contenido descargado se trató como dato no confiable. No se ejecutó nada de lo descargado.

## 8. Endpoints que no respondieron (2026-11-01)

`geoportal.gestionderiesgos.gob.ec`, `servicios.gestionderiesgos.gob.ec`, `geoportal.igm.gob.ec`, `geoportal.inec.gob.ec`, `siig.gobiernogalapagos.gob.ec`, `geoportal.galapagos.gob.ec`, `geonode.darwinfoundation.org`, `www.geoportal.inocar.mil.ec`, `ide.ambiente.gob.ec` por HTTPS (solo funciona `http://…:8080`), `geoportal.agricultura.gob.ec/geoserver` (404), y los dominios de los GAD de San Cristóbal e Isabela.
