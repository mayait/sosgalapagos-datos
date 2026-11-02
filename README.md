# SOS Galápagos · Datos geográficos, meteorológicos y estudios de riesgo

Información geográfica, mediciones del clima, estudios técnicos y servidores que se usaron para coordinar la respuesta a las **inundaciones por El Niño de octubre y noviembre de 2026** en **Santa Cruz, San Cristóbal e Isabela** (Galápagos, Ecuador).

- Coordinación: **USFQ Galápagos**. Responsable del repositorio: **Julián Maya**. Equipos y colaboradores: ver [Créditos](#créditos).
- Se publica en: [sosgalapagos.org/mapas](https://sosgalapagos.org/mapas/) · [/estudios](https://sosgalapagos.org/estudios/) · [/clima](https://sosgalapagos.org/clima/).
- La plataforma de coordinación (ResponseGrid) vive en otro repositorio: [mayait/sosgalapagos](https://github.com/mayait/sosgalapagos).

> ⚠️ **Todo lo de aquí es preliminar.** No existe un mapa oficial de amenaza por inundación pluvial para Galápagos. Las capas marcadas como **modelo** (susceptibilidad HAND, cuencas, costa baja, lluvias de modelos) sirven para **priorizar**, no para delimitar ni para normar. Las capas **oficiales** citan su institución.

## ⬇️ Descargar los datos

| Qué | Enlace |
|---|---|
| **Todo el repositorio** (capas, clima, estudios y scripts) | [ZIP de `main`](https://github.com/mayait/sosgalapagos-datos/archive/refs/heads/main.zip) |
| **Capas de las islas completas en Shapefile** (WGS84, UTF-8, con LEEME) | [Versiones publicadas → `todo-completo-shp.zip`](https://github.com/mayait/sosgalapagos-datos/releases/latest) |
| **Capas de las islas completas en GeoJSON** | [Versiones publicadas → `todo-completo-geojson.zip`](https://github.com/mayait/sosgalapagos-datos/releases/latest) |
| **Datos del clima** (IERSE, INAMHI, FCD) | [Versiones publicadas → `clima-datos-*.zip`](https://github.com/mayait/sosgalapagos-datos/releases/latest) · carpeta [`clima/datos/`](clima/datos/) |
| Capas del mapa de la emergencia (zona poblada), una por una | [`mapas-galapagos/datos/`](mapas-galapagos/datos/) |
| Capas por fuente y depuradas (OSM, IGM, DEM, integradas) | [`geodatos/capas/`](geodatos/capas/) |
| Una capa a la vez, en Shapefile o GeoJSON, desde el visor | [sosgalapagos.org/mapas](https://sosgalapagos.org/mapas/) |
| Informe de La Cascada (PDF) | [`geodatos/estudios/la-cascada/`](geodatos/estudios/la-cascada/) |

Todas las capas están en **EPSG:4326**. Antes de usarlas, lee las advertencias de [§6](#6-cómo-se-usó-el-modelo-hand) y las licencias del final.

---

## El repositorio en una imagen

```
                 DATOS                                         SERVIDOR
  (se descargan, se procesan, se versionan)        (sirven lo generado / recogen datos)

  geodatos/                                         servidores/  ← índice y publicar.sh
  ├─ scripts/01–09  proceso de capas  ─────┐
  ├─ capas/         capas por fuente       │        sosgalapagos.org
  ├─ export/        paquete para el mapa ──┼──────▶ ├─ /mapas/     visor + descargas
  ├─ estudios/      informes técnicos ─────┼──────▶ ├─ /estudios/  informes web + comentarios
  └─ docs/          fuentes y guías        │        └─ /clima/     panel en vivo
                                           │                ▲
  clima/                                   │                │ cada 5 min
  ├─ datos/         mediciones (crudos) ◀──┼──── recolector (systemd) + puente IERSE (Mac)
  ├─ scripts/       consolidación          │
  └─ recolector/, web/, deploy/  ──────────┘ (código de servidor del clima)

  mapas-galapagos/  entregable cerrado: datos + visor + documentación
  docs/             explicaciones transversales (modelo HAND)
```

| Si buscas… | Ve a |
|---|---|
| Las capas listas para usar (GeoJSON, PNG y manifiesto) | [`mapas-galapagos/`](mapas-galapagos/00-LEEME.md) o [sosgalapagos.org/mapas](https://sosgalapagos.org/mapas/) (Shapefile y GeoJSON) |
| Cómo se hacen las capas | [`geodatos/LEEME.md`](geodatos/LEEME.md) |
| Las mediciones del clima | [`clima/LEEME.md`](clima/LEEME.md) |
| Los informes | [`geodatos/estudios/`](geodatos/estudios/) |
| Cómo funciona cada servidor y cómo publicar | [`servidores/README.md`](servidores/README.md) |
| Cómo trabajar en equipo, con ramas y agentes | [`CONTRIBUIR.md`](CONTRIBUIR.md) · [`AGENTS.md`](AGENTS.md) |
| Qué falta | [Issues del proyecto](https://github.com/mayait/sosgalapagos-datos/issues) |

---

## 1. Qué se hizo

| Fecha (2026) | Hito |
|---|---|
| 30–31 oct | Lluvias intensas e inundación en Puerto Ayora (barrio **La Cascada**) y otras zonas de Santa Cruz |
| 31 oct | Descarga del extracto de OpenStreetMap y del relieve Copernicus GLO-30; búsqueda de fuentes oficiales |
| 1 nov | Capas base de las tres islas: quebradas, cuencas, susceptibilidad HAND, zonas pobladas, vías, puntos clave y Parque Nacional. Visor local e integración en el mapa de ResponseGrid. Entregable `mapas-galapagos/` |
| 1 nov | Página pública [/mapas](https://sosgalapagos.org/mapas/) con descargas en Shapefile y GeoJSON; GeoServer de prueba |
| 2 nov | **Informe técnico preliminar de La Cascada** (PDF de 39 páginas): cuenca, vaso, desvío de quebradas, lluvias y propuestas |
| 2 nov | **Clima en vivo** ([/clima](https://sosgalapagos.org/clima/)): recolector cada 5 min de las estaciones IERSE (Santa Cruz) y USFQ GSC (San Cristóbal) |
| 2 nov | Estudios web de **Santa Cruz** y **San Cristóbal** ([/estudios](https://sosgalapagos.org/estudios/), en revisión) |
| 2 nov | Nivel **preliminar** de inundación por zona en /clima (regla v0.1 por lluvia de 1 h, 3 h y 24 h y humedad previa) |
| 2 nov | Modelos 2D del evento en Santa Cruz y San Cristóbal; tomas de agua del acueducto de San Cristóbal |
| 2 nov | Este repositorio: datos, estudios y servidores separados de la plataforma |

## 2. Qué datos hay

| Dominio | Qué contiene | Dónde | ¿En git? |
|---|---|---|---|
| **Geografía cruda** | Extracto OSM (Geofabrik, 31-oct), DEM Copernicus GLO-30, WFS IGM 1:25 000 (70 capas), capas SNGR, INEC, CGREG/FCD, MSP, MINEDUC e INOCAR, Google Open Buildings | `geodatos/descargas/` | **No.** Pesa ~400 MB, trae datos personales y se regenera con los scripts 01–07 |
| **Capas depuradas** | Por fuente (`osm/`, `igm/`, `dem/`), integradas (`final/`), rásteres PNG y capa operativa de áreas afectadas | `geodatos/capas/` | Sí |
| **Paquete del mapa** | 25 capas recortadas al área de interés + manifiesto `capas.json` + resumen de exposición | `geodatos/export/galapagos/` | Sí |
| **Entregable** | Datos, visor y documentación (catálogo, metodología, fuentes, especificación y cómo actualizar) | `mapas-galapagos/` | Sí |
| **Clima medido** | Estaciones IERSE (4, Santa Cruz, cada 5 min, desde abril de 2026); historial INAMHI (16-oct → 2-nov, la fuente solo guarda 90 días); series diarias de la FCD (Puerto Ayora desde 1965 y Bellavista); series consolidadas de 5 min, horarias y diarias. En el servidor se recogen además USFQ GSC, INAMHI en vivo, mareógrafos y METAR | `clima/datos/` ([LEEME](clima/datos/LEEME.md)) | Sí (los crudos nunca se modifican) |
| **Estudios** | Textos, datos, figuras y PDF de La Cascada, Santa Cruz y San Cristóbal (incluye modelos 2D del 30-oct y las tomas de agua de San Cristóbal); se siguen ampliando | `geodatos/estudios/` | Sí |

**Exposición estimada** (`geodatos/export/galapagos/resumen_exposicion.json`):

| | Santa Cruz | San Cristóbal | Isabela |
|---|---:|---:|---:|
| Edificios | 10 350 | 4 579 | 2 072 |
| Población estimada | 16 880 | 8 094 | 3 086 |
| … en susceptibilidad alta o media (HAND) | 3 965 | 657 | 928 |
| … en zona de tsunami | 917 | 207 | 1 064 |

## 3. Qué capas hay

Las del mapa de la emergencia (`geodatos/export/galapagos/capas.json`). Detalle de cada una, con sus campos, en [`mapas-galapagos/documentacion/01-catalogo-de-capas.md`](mapas-galapagos/documentacion/01-catalogo-de-capas.md).

| Grupo | Capa | Tipo | Fuente |
|---|---|---|---|
| Emergencia en curso | Áreas afectadas (inundación, servicios, deslave, riesgo) | operativa | COE, ECU 911, equipos en terreno |
| Parque y zona agrícola | Parque Nacional, límite del parque, zona agrícola | oficial | Zonificación PNG 2017 (CGREG/FCD) |
| Zonas inundables | **Susceptibilidad a inundación por quebradas** (alta, media, baja) | **modelo** | HAND sobre Copernicus GLO-30 + quebradas IGM ([explicación](docs/modelo-hand.md)) |
| | Zonas inundables y de riesgo oficiales (flujos de lodo por El Niño, riesgo de inundación en Puerto Ayora y Villamil, terreno inundable) | oficial | IGM 1:25 000, CGREG |
| | Costa baja (0–3, 3–5 y 5–10 m) | modelo | Copernicus GLO-30 |
| | Inundación por tsunami | oficial | SNGR / INOCAR |
| Quebradas y drenaje | Cuencas completas que drenan a cada poblado; subcuencas por punto de entrada | modelo | D8 sobre GLO-30 + quebradas IGM |
| | Quebradas y cauces mapeados | oficial | IGM 1:25 000 + OSM |
| | Cauces adicionales detectados en el relieve | modelo | GLO-30 |
| | Franja de protección de quebradas de 20 m | oficial | CGREG |
| Zonas pobladas | Límite urbano, barrios, población estimada por manzana | oficial + estimación | IGM, CGREG, INEC MGN 2026 + viviendas SNGR |
| Vías y evacuación | Vías, nombres de calles, rutas de evacuación por tsunami | abierta / oficial | OSM (31-oct), SNGR |
| Puntos clave | Salud, refugios, seguridad, servicios, logística | oficial + abierta | MSP, SNGR, MINEDUC, IGM, OSM |
| Relieve | Relieve sombreado, curvas cada 10 m, pendientes fuertes | modelo | Copernicus GLO-30 |

**Área cubierta:** zona agrícola y urbana completas, más las **cuencas completas** que drenan a cada poblado (aunque suban al Parque), 500 m alrededor de las zonas pobladas y 300 m alrededor de las vías. En [/mapas](https://sosgalapagos.org/mapas/) se publican las islas completas, sin recorte.

## 4. De dónde salieron los datos

| Fuente | Qué aporta | Acceso |
|---|---|---|
| **IGM** (Instituto Geográfico Militar) | Cartografía 1:25 000: quebradas, curvas, límite urbano, terreno inundable | WFS público. Devuelve cada elemento repetido tres veces y hay que quitar los duplicados |
| **Copernicus GLO-30** (ESA/Airbus) | Relieve de 30 m (DSM: incluye edificios y árboles) | AWS Open Data |
| **OpenStreetMap** (© colaboradores, ODbL) | Vías, edificios, servicios y uso del suelo | Extracto Geofabrik. Overpass falló (502/504) |
| **SNGR** | Tsunami, rutas y zonas seguras, refugios, viviendas con población, eventos históricos | ArcGIS público. Trae datos personales, que se depuran |
| **INEC** | Manzanas y sectores (MGN 2026) | IDGN |
| **CGREG / FCD** | Zonificación del Parque 2017, barrios, franja de quebradas, riesgos (flujos de lodo por El Niño) | GeoNode de la FCD. El SIIG pide usuario |
| **MSP, MINEDUC** | Salud y educación | Copias en la SNGR |
| **Google Open Buildings v3** | Huellas de edificios (no cubre San Cristóbal) | Abierta |
| **IERSE** (Universidad del Azuay), Proyecto DARWIN | 4 estaciones meteorológicas en Santa Cruz, cada 5 min | CC BY-NC-ND 4.0; cita obligatoria en [`clima/datos/LEEME.md`](clima/datos/LEEME.md#cómo-citar) |
| **FCD** (Fundación Charles Darwin) | Series climáticas diarias de Puerto Ayora (desde 1965) y Bellavista | CC BY-NC-SA |
| **USFQ GSC** (Galapagos Science Center) | 5 estaciones en San Cristóbal; lluvia diaria desde 2015 | Se cita como pide el GSC ([`clima/datos/LEEME.md`](clima/datos/LEEME.md#cómo-citar)) |
| **INAMHI** | Estaciones automáticas; historial de 90 días | Se cita la fuente, sin enlace |
| **ECMWF y otros modelos** (vía Open-Meteo) | Lluvia estimada del evento y climatología 1991–2020 | Abierta |

El catálogo completo de las fuentes geográficas, con los servicios probados, está en [`geodatos/docs/fuentes-oficiales.md`](geodatos/docs/fuentes-oficiales.md). Licencias y atribuciones: [`mapas-galapagos/documentacion/03-fuentes-y-licencias.md`](mapas-galapagos/documentacion/03-fuentes-y-licencias.md). Las fuentes meteorológicas se citan como piden sus autores; no se publican los servicios (endpoints) de los que se descargan.

## 5. Cómo se procesaron

### Capas (`geodatos/scripts/`)

```
01–02  OSM: extracto Geofabrik → vías, edificios, servicios, uso del suelo (pyosmium)
04–05  IGM: WFS 1:25 000 → quitar triplicados → filtrar las 3 islas
03     DEM: recorte por isla → relieve, curvas, costa baja, pendientes
            → quemado de quebradas IGM → D8 → drenaje, cuencas → HAND
06     Integración: zonas pobladas, quebradas, puntos clave (deduplicados a < 40 m)
07     Oficiales: SNGR/INEC/CGREG, depuración de datos personales, edificios
            (OSM + Open Buildings) y exposición por edificio y vivienda
07b    Cuencas completas que drenan a cada poblado (salto de punteros sobre D8)
08     Exportación: recorte al área de interés, simplificación y manifiesto capas.json
08b    Rótulos de nombres de calles
09     Entregable mapas-galapagos/ (y código para la app)
10–11  Publicación web (/mapas) y GeoServer local
```

Paso a paso y cómo regenerar: [`geodatos/LEEME.md`](geodatos/LEEME.md). Supuestos y límites de cada capa: [`mapas-galapagos/documentacion/02-metodologia.md`](mapas-galapagos/documentacion/02-metodologia.md).

### Clima (`clima/`)

Las estaciones se descargan **tal cual** a `clima/datos/<fuente>/crudos/`, con un archivo por día que nunca se corrige. Luego se consolidan en series de 5 min, horarias y diarias, con su porcentaje de cobertura: cuando una estación no transmite, esa lluvia **no se mide** y el total del día es un mínimo. En el servidor, el recolector guarda todo en SQLite con horas UTC y publica el panel. Ver [`clima/LEEME.md`](clima/LEEME.md).

### Estudios (`geodatos/estudios/`)

Cada estudio tiene sus textos (Markdown), sus datos y sus figuras, y los generan scripts propios (12–20 y `grd_*`). El de La Cascada lo preparó un comité de agentes (asesor hidrológico, meteorología, gestión de riesgos y urbanismo) con un revisor independiente. Conclusiones principales: al barrio drenan 42,3 km²; es un **vaso cerrado** sin cauce de salida; el desvío al este no es descartable, pero no está demostrado; **no hay lluvia medida** en Puerto Ayora durante el evento.

## 6. Cómo se usó el modelo HAND

**HAND** (*Height Above Nearest Drainage*) mide cuántos metros está cada punto del terreno **por encima de la quebrada a la que drena**. Si una casa está a 1 m sobre su quebrada, se moja con poco. Si está a 10 m, es muy improbable.

1. Se baja 3 m el relieve sobre las quebradas del IGM («quemado»), para que el agua siga los cauces reales.
2. Se calcula por dónde corre el agua (D8) y cuánta área drena cada celda.
3. Se toman como cauces de referencia los que drenan al menos 0,5 km², más las quebradas IGM.
4. Para cada celda se calcula su altura sobre ese cauce, en el relieve sin quemar.
5. Clases: **alta ≤ 1 m**, **media ≤ 2,5 m**, **baja ≤ 5 m**, solo hasta 300 m del cauce.
6. Se cruza con cada edificio y vivienda para estimar la **exposición**.

Coincide con el polígono oficial de riesgo de inundación de Puerto Ayora (CGREG). Sus límites: el relieve de 30 m incluye techos y árboles, no ve alcantarillas, exagera en terreno plano (Villamil) y **no tiene caudal ni período de retorno**. Explicación completa, parámetros y cómo mejorarlo: [`docs/modelo-hand.md`](docs/modelo-hand.md).

## 7. Servidores

Resumen: **/mapas** y **/estudios** son archivos estáticos que se generan aquí y se suben con `rsync`. **/clima** es un recolector en el servidor (systemd, cada 5 min) más un panel estático. Los comentarios de los estudios son un contenedor de la app. Todo pasa por Caddy en `152.44.45.89`.

```bash
servidores/publicar.sh mapas | estudios | clima     # solo desde main y con el árbol limpio
```

Mapa completo, rutas en el servidor, timers, respaldos y comprobaciones: [`servidores/README.md`](servidores/README.md).

## 8. Cómo trabajar aquí

- **Equipos y ramas:** [`CONTRIBUIR.md`](CONTRIBUIR.md) explica:
  - qué se edita a mano y qué se regenera;
  - quién es dueño de cada carpeta;
  - cómo se nombran las ramas;
  - cómo usar *worktrees*;
  - las recetas para añadir capas, fuentes y estudios.
- **Agentes de IA:** [`AGENTS.md`](AGENTS.md) recoge las reglas que no se pueden romper (privacidad, enlaces de clima, publicación).
- **Instalación:**
  ```bash
  git clone https://github.com/mayait/sosgalapagos-datos.git ~/dev/sosgalapagos-datos
  cd ~/dev/sosgalapagos-datos/geodatos && uv venv .venv --python 3.12 && uv pip install -p .venv -r requirements.txt
  cd ../clima && uv venv .venv --python 3.12 && uv pip install -p .venv -r requirements.txt
  cd ../geodatos && ./scripts/servir.sh     # visor local en http://127.0.0.1:8765/visor/
  ```
  `geodatos/descargas/` no está en git: se regenera con los scripts 01–07 (unos 15 min y ~400 MB). Los secretos de clima (`clima/privado/`) se piden a Julián.
- **Relación con la app:** `09_entregable.py` y `export/integracion/copiar-a-app.sh` copian a la app ResponseGrid. Usan `SOSGALAPAGOS_APP`, que por defecto apunta a `~/dev/RESPONSEGRID_GALAPAGOS/app`.
- **Dependencia interna:** algunos estudios leen `clima/datos/`. `geodatos/` y `clima/` deben estar uno junto al otro.

## 9. Qué falta

Todo lo pendiente está en los **[issues del proyecto](https://github.com/mayait/sosgalapagos-datos/issues)**, con prioridad (P1, P2, P3) y tipo (datos faltantes, más resolución, procesos, plataforma, gobernanza). [Ver solo los P1](https://github.com/mayait/sosgalapagos-datos/issues?q=is%3Aopen+label%3AP1). Lo más urgente:

1. **Delimitación oficial de lo inundado** el 30–31-oct y **marcas de agua** para validar el modelo.
2. **Lluvia medida en Puerto Ayora**: incorporar al estudio la estación INAMHI M0191, que sí registró el evento.
3. **Relieve de 1 m sin edificios** (dron o LiDAR) de los poblados, para rehacer HAND y modelar la inundación en 2D.
4. **Catastro y red de drenaje urbano** de los tres GAD.
5. **Curvas IDF y alerta temprana por lluvia** conectadas al recolector.

## Licencias, créditos y privacidad

- Licencia del código: **por definir** (ver los [issues de gobernanza](https://github.com/mayait/sosgalapagos-datos/issues?q=is%3Aopen+label%3Agobernanza)). Datos derivados: cada capa conserva la licencia de su fuente; ver `03-fuentes-y-licencias.md`. Las capas con OSM se publican bajo **ODbL**.
- **Datos personales:** se eliminaron los nombres y teléfonos de los responsables de refugios y de las fuentes de eventos de la SNGR. Nunca se publican nombres de personas afectadas.
- Atribución sugerida: «Datos: IGM, CGREG/FCD, SNGR, INEC, INOCAR, © colaboradores de OpenStreetMap (ODbL), Copernicus GLO-30, IERSE, USFQ GSC. Procesamiento: SOS Galápagos (USFQ Galápagos)».

## Créditos

- **Julián Maya**: responsable del repositorio.
- **USFQ Galápagos**: coordinación de la respuesta.
- *Equipos y colaboradores: por completar.*
