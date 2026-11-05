# SOS Galápagos · Datos y modelos de las inundaciones de 2026

Datos geográficos, mediciones del clima y modelos que se usaron para responder a las **inundaciones de octubre y noviembre de 2026** en **Santa Cruz, San Cristóbal e Isabela** (Galápagos, Ecuador).

- **Responsable:** Julián Maya, Universidad San Francisco de Quito (USFQ) · jamaya@usfq.edu.ec. Coordinación: USFQ Galápagos.
- **En línea:**
  - [sosgalapagos.org/mapas](https://sosgalapagos.org/mapas/)(https://sosgalapagos.org/mapas/) — visor y descargas de capas;
  - [/clima](https://sosgalapagos.org/clima/) — lluvia en vivo, nivel preliminar de inundación, pronóstico y satélite.
- **Plataforma de coordinación** (ResponseGrid): vive en otro repositorio, [mayait/sosgalapagos](https://github.com/mayait/sosgalapagos).

> ⚠️ **Todo es preliminar. Modelo propio ≠ dato oficial.** No existe un mapa oficial de amenaza por inundación pluvial para Galápagos. Lo marcado como **modelo** (HAND, cuencas, modelo 2D, tormentas sintéticas, curvas IDF, alerta, pronóstico) sirve para **priorizar y discutir**. No sirve para delimitar zonas, normar ni diseñar obras. Las capas **oficiales** citan su institución.

---

## 🆘 Qué nos falta

Sin estos datos, los modelos se quedan en estimaciones sin validar. Cada fila enlaza a su issue; la lista completa está en los [issues del proyecto](https://github.com/mayait/sosgalapagos-datos/issues), con los urgentes en [P1](https://github.com/mayait/sosgalapagos-datos/issues?q=is%3Aopen+label%3AP1). **Si tienes alguno de estos datos, abre un issue o escribe a jamaya@usfq.edu.ec.**

### 1. Lo que más necesitamos: cuándo y dónde se inundó de verdad

Es lo único que permite **validar** los modelos y la alerta. Hoy ninguna cifra de frecuencia ni de umbral está contrastada con un evento real fechado.

| Qué | Quién puede tenerlo | Issue |
|---|---|---|
| **Inundaciones históricas con fecha, hora, lugar y profundidad** (fotos con una puerta, un muro o un auto como referencia) | Vecinos, bomberos, ECU 911, GAD, medios | [#80](https://github.com/mayait/sosgalapagos-datos/issues/80), [#14](https://github.com/mayait/sosgalapagos-datos/issues/14) |
| ¿Hubo agua en La Cascada el 3-oct, el 23-oct y el 1–2-nov? Horas de los hechos del 30-oct | Vecinos, COE cantonal | [#52](https://github.com/mayait/sosgalapagos-datos/issues/52), [#64](https://github.com/mayait/sosgalapagos-datos/issues/64) |
| Delimitación oficial de lo inundado el 30–31-oct | COE cantonal, SNGR | [#1](https://github.com/mayait/sosgalapagos-datos/issues/1) |
| Marcas de agua medidas con GNSS en La Cascada y su salida | Equipo en terreno | [#2](https://github.com/mayait/sosgalapagos-datos/issues/2) |

### 2. Datos que tienen las instituciones

| Qué | Quién lo tiene | Para qué | Issue |
|---|---|---|---|
| Estudio de intensidades máximas (2015), series diarias de San Cristóbal y lluvia de la estación M0191 de Puerto Ayora durante el evento | **INAMHI** | Curvas IDF oficiales y lluvia del evento en Puerto Ayora | [#77](https://github.com/mayait/sosgalapagos-datos/issues/77), [#78](https://github.com/mayait/sosgalapagos-datos/issues/78), [#3](https://github.com/mayait/sosgalapagos-datos/issues/3) |
| Lluvia del corte del 30-oct (de las 21:25 al 31-oct a las 18:45) y **permiso escrito para obras derivadas** (modelo 2D, curvas IDF) | **IERSE** (Universidad del Azuay) | Completar el evento; su licencia es CC BY-NC-ND | [#62](https://github.com/mayait/sosgalapagos-datos/issues/62) |
| Lluvia a 5–10 min del 30–31-oct en San Cristóbal y licencia de sus datos | **USFQ GSC** | Modelo 2D de San Cristóbal con su propia lluvia | [#61](https://github.com/mayait/sosgalapagos-datos/issues/61), [#46](https://github.com/mayait/sosgalapagos-datos/issues/46), [#74](https://github.com/mayait/sosgalapagos-datos/issues/74) |
| Series del proyecto DARWIN (15-oct a 2-nov) y permiso para publicar derivados | U. de Marburgo | Lluvia en la parte alta de Santa Cruz | [#76](https://github.com/mayait/sosgalapagos-datos/issues/76) |
| Tesis sobre las encañadas de Puerto Baquerizo Moreno | USFQ | Curvas IDF y caudales de San Cristóbal | [#79](https://github.com/mayait/sosgalapagos-datos/issues/79) |
| **Catastro y red de drenaje urbano** (sumideros, colectores, alcantarillas, cotas) | GAD de Santa Cruz, San Cristóbal e Isabela | Modelar calles y alcantarillas; hoy el modelo no las ve | [#4](https://github.com/mayait/sosgalapagos-datos/issues/4), [#5](https://github.com/mayait/sosgalapagos-datos/issues/5) |
| Trazados de las obras del Plan de Acción de la UGR (zanja, muro, conexión de Floreana) | GAD y UGR de San Cristóbal | Evaluar las obras con el modelo | [#70](https://github.com/mayait/sosgalapagos-datos/issues/70), [#53](https://github.com/mayait/sosgalapagos-datos/issues/53) |
| Refugios y puntos de encuentro **para inundación** y protocolo de evacuación | SNGR, GAD | Rutas y refugios fuera de las zonas que se inundan | [#6](https://github.com/mayait/sosgalapagos-datos/issues/6), [#71](https://github.com/mayait/sosgalapagos-datos/issues/71), [#67](https://github.com/mayait/sosgalapagos-datos/issues/67) |
| Acceso al SIIG y censo 2022 por manzana | CGREG, INEC | Capas oficiales y población real | [#7](https://github.com/mayait/sosgalapagos-datos/issues/7), [#8](https://github.com/mayait/sosgalapagos-datos/issues/8) |

### 3. Mediciones en campo e instrumentos

| Qué | Para qué | Issue |
|---|---|---|
| **Relieve de 1 m sin edificios** (dron o LiDAR) de los poblados. Santa Cruz ya tiene el DTM de 1 m de la SGIAR (Puerto Ayora, el escarpe y Bellavista, en [`geodatos/datos/dtm_sgiar/`](geodatos/datos/dtm_sgiar/LEEME.md)); faltan San Cristóbal e Isabela | Rehacer HAND y el modelo 2D sin el error de ±2–4 m del DSM | [#16](https://github.com/mayait/sosgalapagos-datos/issues/16), [#23](https://github.com/mayait/sosgalapagos-datos/issues/23) |
| **Pluviómetros** en cada poblado y en la parte alta; el mejor sitio nuevo está en la cuenca media de La Cascada | Alerta con más anticipación | [#19](https://github.com/mayait/sosgalapagos-datos/issues/19) |
| Sensor de nivel en El Progreso | Ahí la lluvia no anticipa la inundación | [#81](https://github.com/mayait/sosgalapagos-datos/issues/81) |
| Revisión de los pluviómetros de Cerro Crocker y Los Guayabillos | Datos dudosos desde el 30-oct | [#56](https://github.com/mayait/sosgalapagos-datos/issues/56) |
| Cotas clave: rebose de La Cascada, cauce de Tomás de Berlanga, Vía Universidad frente al campus, zanja de Manzanillo | Confirmar umbrales que hoy salen del DSM | [#65](https://github.com/mayait/sosgalapagos-datos/issues/65), [#66](https://github.com/mayait/sosgalapagos-datos/issues/66), [#58](https://github.com/mayait/sosgalapagos-datos/issues/58), [#55](https://github.com/mayait/sosgalapagos-datos/issues/55) |
| Inventario en terreno de cruces quebrada–vía, aforos e infiltración | Calibrar caudales y pérdidas del suelo | [#33](https://github.com/mayait/sosgalapagos-datos/issues/33), [#9](https://github.com/mayait/sosgalapagos-datos/issues/9), [#10](https://github.com/mayait/sosgalapagos-datos/issues/10) |

### 4. Acuerdos y operación

- **Acuerdos de intercambio de datos** con GAD, CGREG, DPNG, FCD, INAMHI, SNGR e INOCAR ([#45](https://github.com/mayait/sosgalapagos-datos/issues/45)).
- **Equipo local** que mantenga los datos después de la emergencia ([#51](https://github.com/mayait/sosgalapagos-datos/issues/51)) y protocolo de datos personales ([#48](https://github.com/mayait/sosgalapagos-datos/issues/48)).
- **Titularidad:** la USFQ debe confirmar que el repositorio es suyo (ver [Licencias](#licencias-y-cómo-citar)).
- **Operación del servidor de clima:**
  - respaldo de `clima.db` fuera del servidor ([#38](https://github.com/mayait/sosgalapagos-datos/issues/38));
  - aviso si el recolector se detiene ([#39](https://github.com/mayait/sosgalapagos-datos/issues/39)).
- **Publicación automática** desde `main` ([#36](https://github.com/mayait/sosgalapagos-datos/issues/36)).

---

## Qué se hizo

| Fecha (2026) | Hito |
|---|---|
| 30–31 oct | Lluvias intensas e inundación en Puerto Ayora (barrio **La Cascada**) y otras zonas de Santa Cruz y San Cristóbal |
| 1 nov | Capas base de las tres islas: quebradas, cuencas, susceptibilidad HAND, zonas pobladas, vías y puntos clave. Visor [/mapas](https://sosgalapagos.org/mapas/) con descargas |
| 2 nov | Estudio de **La Cascada**. **Clima en vivo** ([/clima](https://sosgalapagos.org/clima/)) con las estaciones IERSE, USFQ GSC e INAMHI. Primera regla de alerta por lluvia |
| 2–3 nov | Modelos **2D** del evento en Santa Cruz y San Cristóbal. Reconocimiento hidrológico. Pronóstico experimental de lluvia fuerte |
| 3–4 nov | **500 tormentas sintéticas** por isla, **curvas IDF provisionales**, vigilancia satelital **GOES-19** |
| 4 nov | Licencia © USFQ (Apache 2.0 + CC BY 4.0) |
| 5 nov | **DTM de 1 m de la SGIAR** en Santa Cruz: HAND, La Cascada, modelo 2D y tormentas rehechos; relieve del DTM en [/mapas](https://sosgalapagos.org/mapas/) |

## Descargar los datos

| Qué | Enlace |
|---|---|
| **Todo el repositorio** (capas, clima y scripts) | [ZIP de `main`](https://github.com/mayait/sosgalapagos-datos/archive/refs/heads/main.zip) |
| **Capas de las islas completas** en Shapefile o GeoJSON (WGS84, UTF-8, con LEEME) | [Versiones publicadas](https://github.com/mayait/sosgalapagos-datos/releases/latest) → `todo-completo-shp.zip` · `todo-completo-geojson.zip` |
| **Datos del clima** (IERSE, INAMHI, FCD) | [Versiones publicadas](https://github.com/mayait/sosgalapagos-datos/releases/latest) → `clima-datos-*.zip` · carpeta [`clima/datos/`](clima/datos/) |
| Capas del mapa de la emergencia, una por una | [`mapas-galapagos/datos/`](mapas-galapagos/datos/) o el visor [/mapas](https://sosgalapagos.org/mapas/) |
| Datos de cada estudio (los que alimentan las capas de los modelos) | [`geodatos/estudios/`](geodatos/estudios/) |

Todas las capas están en **EPSG:4326**. Las horas se guardan en UTC; Galápagos está en UTC−6.

## Qué hay en el repositorio

```
geodatos/          capas: scripts/ (01–34), capas/, export/, estudios/ (datos de los modelos), docs/
clima/             estaciones: datos/ (crudos que nunca se modifican), recolector/, pronostico/, satelite/, web/
mapas-galapagos/   entregable cerrado del mapa: datos, visor y documentación (catálogo, metodología, fuentes)
servidores/        cómo se publica cada servicio en sosgalapagos.org (publicar.sh)
docs/              explicaciones transversales (modelo HAND)
```

| Si buscas… | Ve a |
|---|---|
| Qué método se usó y con qué datos | [`mapas-galapagos/documentacion/02-metodologia.md`](mapas-galapagos/documentacion/02-metodologia.md) y [`docs/modelo-hand.md`](docs/modelo-hand.md) |
| Las capas listas para usar | [`mapas-galapagos/`](mapas-galapagos/00-LEEME.md) o [/mapas](https://sosgalapagos.org/mapas/) |
| Cómo se hacen las capas | [`geodatos/LEEME.md`](geodatos/LEEME.md) |
| Las mediciones del clima, el pronóstico y el satélite | [`clima/LEEME.md`](clima/LEEME.md) |
| De dónde sale cada dato | [`geodatos/docs/fuentes-oficiales.md`](geodatos/docs/fuentes-oficiales.md) y [`03-fuentes-y-licencias.md`](mapas-galapagos/documentacion/03-fuentes-y-licencias.md) |
| Rehacer los estudios tras un dato nuevo | [`geodatos/flujo.toml`](geodatos/flujo.toml) + `geodatos/scripts/flujo.py --seco` |
| Publicar o tocar un servidor | [`servidores/README.md`](servidores/README.md) |
| Cómo trabajar en equipo, con ramas y agentes | [`CONTRIBUIR.md`](CONTRIBUIR.md) · [`AGENTS.md`](AGENTS.md) |

## Fuentes principales

IGM (1:25 000), CGREG/FCD, SNGR/INOCAR, INEC, MSP, MINEDUC, OpenStreetMap (ODbL), Google Open Buildings, Copernicus GLO-30, **SGIAR** (DTM de 1 m de Santa Cruz), **IERSE** (Universidad del Azuay; 4 estaciones en Santa Cruz cada 5 min), **USFQ GSC** (San Cristóbal), **INAMHI**, **FCD** (lluvia diaria desde 1965), reanálisis GAR (TU Berlín), modelos de pronóstico vía Open-Meteo y NOAA GOES-19.

Las fuentes meteorológicas se citan como piden sus autores. Los servicios (endpoints) de los que se descargan no se publican. Detalle y licencias de cada fuente: [`LICENCIA-DATOS.md`](LICENCIA-DATOS.md).

## Servidores

`/mapas` son archivos estáticos que se generan aquí. `/clima` es un recolector en el servidor (systemd, cada 5 min) con un panel estático.

```bash
servidores/publicar.sh mapas | clima     # solo desde main y con el árbol limpio
```

Detalle: [`servidores/README.md`](servidores/README.md).

## Cómo trabajar aquí

- **Equipos, ramas y agentes:** [`CONTRIBUIR.md`](CONTRIBUIR.md) y [`AGENTS.md`](AGENTS.md). Ahí están las reglas que no se pueden romper: privacidad, sin endpoints de clima, publicar solo desde `main`.
- **Instalación:**
  ```bash
  git clone https://github.com/mayait/sosgalapagos-datos.git ~/dev/sosgalapagos-datos
  cd ~/dev/sosgalapagos-datos/geodatos && uv venv .venv --python 3.12 && uv pip install -p .venv -r requirements.txt
  cd ../clima && uv venv .venv --python 3.12 && uv pip install -p .venv -r requirements.txt
  ```
- **Lo que no está en git:**
  - `geodatos/descargas/` se regenera con los scripts 01–07 (unos 15 min y ~400 MB).
  - Los secretos de clima (`clima/privado/`) se piden al responsable.

## Licencias y cómo citar

**© 2026 Universidad San Francisco de Quito (USFQ).**

| Qué | Licencia |
|---|---|
| Código | [Apache 2.0](LICENSE), con el aviso de atribución [`NOTICE`](NOTICE), que hay que conservar |
| Textos, figuras, mapas y salidas de los modelos propios | [CC BY 4.0](LICENCIA-CC-BY-4.0.txt): toda reutilización o publicación debe atribuirlos a la USFQ |
| Datos de terceros y lo que se deriva de ellos | Conservan su licencia, que prevalece si es más restrictiva (IERSE CC BY-NC-ND, FCD CC BY-NC-SA, OSM ODbL…); ver [`LICENCIA-DATOS.md`](LICENCIA-DATOS.md) |

**Cómo citar:**
- **El repositorio:** «Maya, J. (2026). *SOS Galápagos: datos, modelos y herramientas para las inundaciones de 2026 en Santa Cruz y San Cristóbal (Galápagos)*. Universidad San Francisco de Quito (USFQ). Licencia CC BY 4.0». También en [`CITATION.cff`](CITATION.cff) y en «Cite this repository».

**Datos personales:** se eliminan los nombres y teléfonos que traen las capas oficiales. Nunca se publican nombres de personas afectadas.

## Créditos

- **Julián Maya** (Universidad San Francisco de Quito, USFQ · jamaya@usfq.edu.ec): responsable del repositorio.
- **USFQ Galápagos:** coordinación de la respuesta.
- **Fuentes de datos:** IERSE (Universidad del Azuay), USFQ GSC, INAMHI, Fundación Charles Darwin, IGM, CGREG, SNGR, INOCAR, INEC y colaboradores de OpenStreetMap.
- El análisis se preparó con asistencia de agentes de inteligencia artificial, sin visitas de campo ni revisión profesional externa.
- *Equipos y colaboradores: por completar.*
