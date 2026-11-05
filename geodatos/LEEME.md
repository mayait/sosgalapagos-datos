# Geodatos Galápagos: capas para el mapa de la emergencia

> **El entregable final está en `../mapas-galapagos/`** (datos listos, visor, documentación y paquete para ResponseGrid). Esta carpeta es el taller: descargas, scripts y capas intermedias.

Mini proyecto para reunir, depurar y revisar la información geográfica de Santa Cruz, San Cristóbal e Isabela antes de integrarla en el mapa de ResponseGrid (`../app`).

## Ver el visor

```bash
./scripts/servir.sh          # luego abrir http://127.0.0.1:8765/visor/
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `descargas/` | Datos crudos: extracto OSM de Geofabrik (31-oct-2026), DEM Copernicus GLO-30, WFS IGM 1:25 000 (70 capas) y capas oficiales (SNGR, INEC, CGREG/FCD, Open Buildings). **No se sube al repositorio** (está en `.gitignore`: pesa 430 MB y contiene datos personales); se regenera con los scripts `01`–`07`. |
| `capas/osm/`, `capas/igm/`, `capas/dem/` | Capas depuradas por fuente. |
| `capas/final/` | Capas integradas de las islas completas. |
| `export/` | **Paquete para ResponseGrid**: capas recortadas al área de interés, manifiesto `capas.json`, motor TypeScript y guía de integración. |
| `datos/dtm_sgiar/` | **DTM de 1 m de Santa Cruz** (Puerto Ayora, escarpe y Bellavista), dato de la **SGIAR** (Subsecretaría de Gestión de la Información y Análisis de Riesgo) sobre un producto Vricon/Maxar. Lo prepara `35_dtm_sgiar.py`; ficha y cita en su `LEEME.md`. |
| `capas/raster/` | PNG para superponer: relieve, elevación, pendientes y susceptibilidad HAND; los límites están en `limites.json`. |
| `scripts/` | Proceso reproducible (`01`–`07`); ver abajo. |
| `docs/fuentes-oficiales.md` | Catálogo de fuentes y servicios probados. |

## Proceso

```bash
.venv/bin/python -I scripts/02_osm_extraer.py descargas/osm/ecuador-latest.osm.pbf  # unos 10 min
.venv/bin/python -I scripts/04_igm_wfs.py      # descarga el WFS IGM Galápagos 1:25 000
.venv/bin/python -I scripts/05_igm_limpiar.py  # quita duplicados de hojas superpuestas y filtra las 3 islas
.venv/bin/python -I scripts/03_dem.py          # relieve, curvas, drenaje, cuencas, HAND y costa baja (necesita 05)
.venv/bin/python -I scripts/06_integrar.py     # zonas pobladas, puntos clave, quebradas
.venv/bin/python -I scripts/07_oficiales.py    # SNGR/INEC/CGREG, edificios combinados y exposición
.venv/bin/python -I scripts/07b_cuencas_aportantes.py  # cuencas completas que drenan a cada poblado
.venv/bin/python -I scripts/08_exportar.py     # recorta al área de interés y genera export/galapagos + capas.json
.venv/bin/python -I scripts/08b_nombres_vias.py # rótulos de nombres de calles (nombres_vias.geojson)
.venv/bin/python -I scripts/09_entregable.py   # actualiza ../mapas-galapagos/ (entregable final)
```

El visor lee `export/galapagos/capas.json`, que es el mismo paquete que pasa al proyecto principal (ver `export/INTEGRACION.md`). Los estilos se editan en `scripts/capas.json`.

## Capas finales (`capas/final/`)

- **Hidrografía:**
  - `quebradas` (IGM 1:25 000 + OSM, 975)
  - `quebradas_franja20m_cgreg`
  - `drenaje_derivado` (DEM, orden de Strahler)
  - `cuencas`
- **Riesgos:**
  - `susceptibilidad_inundacion_zonas_pobladas` (HAND)
  - `costa_baja` (0–3, 3–5 y 5–10 m)
  - `tsunami_inundacion_inocar`
  - `riesgos_cgreg` (flujos de lodo por El Niño, derrumbes, riesgo de inundación en Puerto Ayora y Puerto Villamil, entre otros)
  - `eventos_historicos` (SNGR)
- **Población:**
  - `zonas_pobladas` (límite urbano IGM, uso residencial OSM y huella edificada)
  - `barrios`
  - `manzanas_inec` (con población estimada)
  - `sectores_inec`
  - `suelo_urbano_rural_cgreg`
  - `parroquias`
  - `viviendas_sngr`
  - `edificios_exposicion` (OSM + Google Open Buildings, con susceptibilidad, tsunami y franja de quebrada)
- **Puntos clave:**
  - `salud_msp`
  - `albergues_sngr`
  - `tsunami_zonas_seguras`
  - `tsunami_sirenas`
  - `tsunami_rutas_evacuacion`
  - `educacion_mineduc`
  - `puntos_clave` (OSM + IGM: agua, energía, transporte, etc.)
- **Topografía:** `curvas_nivel` (cada 20 m) y los PNG de relieve.
- `resumen_exposicion.json`: edificios y población por isla en cada zona de exposición.

## Límites y advertencias

- **No existe un mapa oficial de amenaza por inundación pluvial para Galápagos.** Las capas SNGR e INEC nacionales devuelven 0 entidades en las islas. La susceptibilidad HAND es un modelo propio sobre un DSM de 30 m que incluye edificios y vegetación, así que **sirve para priorizar, no para delimitar**. En terreno muy plano, como Puerto Villamil, sobrestima la susceptibilidad.
- La población es una estimación de la SNGR por vivienda; no proviene del censo publicado por manzana.
- La capa de rutas de evacuación es para **tsunami**, no para inundación por lluvia.
- Privacidad: se eliminaron los nombres y teléfonos de los responsables de refugios y de las fuentes de los eventos de la SNGR. No subas `descargas/oficiales/` sin depurar.
- El CGREG (SIIG) y el catastro de los tres GAD municipales no se pueden descargar: hay que pedirlos.
