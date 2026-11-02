# Catálogo de capas

_Generado automáticamente el 2026-11-01 a partir de `datos/capas.json` (script `geodatos/scripts/09_entregable.py`). No editar a mano._

Las capas están en `datos/`. Todas usan GeoJSON EPSG:4326 con coordenadas a 5 decimales (≈ 1 m). Las que dicen «modelo» son cálculos propios sobre el DEM Copernicus GLO-30. Las demás vienen de fuentes oficiales o de OpenStreetMap. Ver `02-metodologia.md` y `03-fuentes-y-licencias.md`.

| Grupo | Capa | Archivo | Tipo | Elementos | Tamaño | Visible al abrir |
|---|---|---|---|---:|---:|:---:|
| Emergencia en curso | Áreas afectadas (COE) | `areas_afectadas.geojson` | poligono | 2 | 6 kB |  |
| Parque Nacional y zona agrícola | Parque Nacional Galápagos | `parque_nacional.geojson` | poligono | 32 | 0.31 MB | sí |
| Parque Nacional y zona agrícola | Límite del Parque Nacional | `limite_parque.geojson` | linea | 10 | 18 kB | sí |
| Parque Nacional y zona agrícola | Zona agrícola (suelo rural) | `zona_agricola.geojson` | poligono | 3 | 13 kB | sí |
| Zonas inundables | Susceptibilidad a inundación por quebradas | `susceptibilidad_inundacion.geojson` | poligono | 2558 | 2.30 MB | sí |
| Zonas inundables | Zonas inundables y de riesgo oficiales | `zonas_inundables_oficiales.geojson` | poligono | 54 | 69 kB | sí |
| Zonas inundables | Zonas costeras bajas (oleaje y marea) | `costa_baja.geojson` | poligono | 184 | 0.21 MB |  |
| Zonas inundables | Inundación por tsunami (INOCAR) | `tsunami_inundacion.geojson` | poligono | 449 | 0.40 MB |  |
| Quebradas y drenaje | Cuencas completas que drenan a cada poblado | `cuencas_localidad.geojson` | poligono | 7 | 51 kB | sí |
| Quebradas y drenaje | Quebradas y cauces mapeados | `quebradas.geojson` | linea | 286 | 0.40 MB | sí |
| Quebradas y drenaje | Cauces adicionales detectados en el relieve | `drenaje_adicional.geojson` | linea | 1324 | 0.53 MB | sí |
| Quebradas y drenaje | Franja de protección de quebradas, 20 m | `franja_quebradas_20m.geojson` | poligono | 151 | 0.17 MB |  |
| Quebradas y drenaje | Subcuencas por punto de entrada al poblado | `cuencas_aportantes.geojson` | poligono | 82 | 0.24 MB |  |
| Zonas pobladas | Límite urbano | `limite_urbano.geojson` | poligono | 5 | 8 kB | sí |
| Zonas pobladas | Barrios (Santa Cruz) | `barrios.geojson` | poligono | 31 | 15 kB | sí |
| Zonas pobladas | Población estimada por manzana | `manzanas_poblacion.geojson` | poligono | 820 | 0.28 MB |  |
| Vías y evacuación | Vías | `vias.geojson` | linea | 1713 | 0.64 MB | sí |
| Vías y evacuación | Rutas de evacuación por tsunami | `rutas_evacuacion_tsunami.geojson` | linea | 104 | 34 kB |  |
| Puntos clave | Salud, refugios y seguridad | `puntos_clave.geojson` | punto | 125 | 0.16 MB |  |
| Puntos clave | Servicios: salud privada, agua, energía, transporte | `puntos_clave.geojson` | punto | 247 | 0.16 MB |  |
| Puntos clave | Alojamiento, comercio y espacios de reunión | `puntos_clave.geojson` | punto | 307 | 0.16 MB |  |
| Relieve | Relieve sombreado | `raster/*_relieve.png` | raster | — | — | sí |
| Relieve | Curvas de nivel cada 10 m | `curvas_nivel.geojson` | linea | 967 | 0.95 MB |  |
| Relieve | Pendientes fuertes (laderas) | `raster/*_pendientes.png` | raster | — | — |  |

**Total del paquete:** 13.2 MB (GeoJSON 7.1 MB; resto: raster y JSON).

## Detalle por capa

### Áreas afectadas (COE)

- **Grupo:** Emergencia en curso · **id:** `areas_afectadas` · **tipo:** poligono
- **Fuente:** COE, ECU 911 y equipos en terreno
- **Qué es:** Capa operativa: se actualiza reemplazando areas_afectadas.geojson. Línea discontinua = por validar.
- **Clasificación por `tipo`:** Área inundada; Corte de servicios; Deslave; Riesgo inminente
- **Campos:** `nombre` (ej.: Barrio La Cascada — zona más afectada), `tipo` (ej.: inundacion), `estado` (ej.: por_validar), `isla` (ej.: Santa Cruz), `detalle` (ej.: Reportes de prensa: agua de hasta ~3 m; ), `fuente` (ej.: Prensa nacional 31-oct/1-nov 2026; COE c), `fecha` (ej.: 2026-10-31)

### Parque Nacional Galápagos

- **Grupo:** Parque Nacional y zona agrícola · **id:** `parque` · **tipo:** poligono
- **Fuente:** Zonificación PNG 2017 (CGREG/FCD)
- **Qué es:** Área protegida. Todo lo rayado en verde está fuera de la zona colonizada.
- **Campos:** `isla` (ej.: Santa Cruz), `nombre` (ej.: Parque Nacional Galápagos), `area_km2` (ej.: 872.7), `nota` (ej.: Área protegida. Fuera de la zona coloniz), `fuente` (ej.: Zonificación PNG 2017 (CGREG/FCD))

### Límite del Parque Nacional

- **Grupo:** Parque Nacional y zona agrícola · **id:** `limite_parque` · **tipo:** linea
- **Fuente:** Zonificación PNG 2017 (CGREG/FCD)
- **Campos:** `isla` (ej.: Santa Cruz), `nombre` (ej.: Límite del Parque Nacional Galápagos), `fuente` (ej.: Zonificación PNG 2017 (CGREG/FCD))

### Zona agrícola (suelo rural)

- **Grupo:** Parque Nacional y zona agrícola · **id:** `zona_agricola` · **tipo:** poligono
- **Fuente:** Zonificación PNG 2017 (CGREG/FCD)
- **Campos:** `isla` (ej.: Santa Cruz), `nombre` (ej.: Zona agrícola (suelo rural)), `area_km2` (ej.: 113.9), `fuente` (ej.: Zonificación PNG 2017 (CGREG/FCD))

### Susceptibilidad a inundación por quebradas

- **Grupo:** Zonas inundables · **id:** `susceptibilidad` · **tipo:** poligono
- **Fuente:** Modelo HAND sobre Copernicus GLO-30 y quebradas IGM
- **Qué es:** Altura del terreno sobre la quebrada más cercana. Sirve para priorizar; no es una delimitación oficial. En terreno muy plano (Puerto Villamil) sobrestima.
- **Clasificación por `nivel`:** Baja (≤ 5 m sobre el cauce); Media (≤ 2,5 m); Alta (≤ 1 m)
- **Campos:** `isla` (ej.: Santa Cruz), `nivel` (ej.: 1), `susceptibilidad` (ej.: Baja), `descripcion` (ej.: Hasta 5 m sobre el cauce), `fuente` (ej.: Modelo HAND (Copernicus GLO-30 + quebrad)

### Zonas inundables y de riesgo oficiales

- **Grupo:** Zonas inundables · **id:** `oficiales` · **tipo:** poligono
- **Fuente:** IGM 1:25 000 y CGREG
- **Clasificación por `tipo`:** Riesgo de inundación (CGREG); Terreno inundable (IGM); Laguna o poza (IGM); Flujos de lodo por El Niño (CGREG); Derrumbes (CGREG); Otros riesgos antrópicos (CGREG)
- **Campos:** `isla` (ej.: San Cristóbal), `tipo` (ej.: Terreno inundable), `fuente` (ej.: IGM 1:25 000), `nombre` (ej.: Poza de Zinc Chico), `localidad` (ej.: Puerto Ayora)

### Zonas costeras bajas (oleaje y marea)

- **Grupo:** Zonas inundables · **id:** `costa_baja` · **tipo:** poligono
- **Fuente:** Modelo sobre Copernicus GLO-30
- **Clasificación por `cota_max_m`:** 5–10 m; 3–5 m; 0–3 m
- **Campos:** `isla` (ej.: Santa Cruz), `cota_max_m` (ej.: 10), `clase` (ej.: 5–10 m), `fuente` (ej.: Modelo (Copernicus GLO-30))

### Inundación por tsunami (INOCAR)

- **Grupo:** Zonas inundables · **id:** `tsunami` · **tipo:** poligono
- **Fuente:** SNGR / INOCAR
- **Campos:** `isla` (ej.: Isabela), `localidad` (ej.: Puerto Villamil), `clase` (ej.: 2), `fuente` (ej.: SNGR / INOCAR)

### Cuencas completas que drenan a cada poblado

- **Grupo:** Quebradas y drenaje · **id:** `cuencas_localidad` · **tipo:** poligono
- **Fuente:** Modelo D8 (Copernicus GLO-30 + quebradas IGM)
- **Qué es:** Todo el terreno cuya agua termina pasando por el poblado, desde la parte alta (aunque esté en el parque).
- **Campos:** `isla` (ej.: Santa Cruz), `tipo` (ej.: Cuenca completa de la localidad), `destino` (ej.: Puerto Ayora), `area_km2` (ej.: 47.17), `area_aguas_arriba_km2` (ej.: 44.21), `descripcion` (ej.: Todo el terreno cuya agua termina pasand), `fuente` (ej.: Modelo D8 sobre Copernicus GLO-30 con qu)

### Quebradas y cauces mapeados

- **Grupo:** Quebradas y drenaje · **id:** `quebradas` · **tipo:** linea
- **Fuente:** IGM 1:25 000 y OSM
- **Clasificación por `fuente`:** Quebrada (IGM); Canal o drenaje (OSM)
- **Campos:** `isla` (ej.: Santa Cruz), `regimen` (ej.: Intermitente / No Perenne), `perenne` (ej.: False), `fuente` (ej.: IGM 1:25 000), `nombre` (ej.: Encañada Seca)

### Cauces adicionales detectados en el relieve

- **Grupo:** Quebradas y drenaje · **id:** `drenaje` · **tipo:** linea
- **Fuente:** Modelo sobre Copernicus GLO-30
- **Qué es:** Cauces que el IGM no tiene mapeados. Revisar en terreno.
- **Campos:** `isla` (ej.: Santa Cruz), `orden` (ej.: 1), `area_drenada_km2` (ej.: 0.28), `fuente` (ej.: Modelo (Copernicus GLO-30), cauce no map)

### Franja de protección de quebradas, 20 m

- **Grupo:** Quebradas y drenaje · **id:** `franja` · **tipo:** poligono
- **Fuente:** CGREG
- **Campos:** `isla` (ej.: San Cristóbal), `tipo` (ej.: Quebrada con escurrimiento intermitente), `fuente` (ej.: CGREG)

### Subcuencas por punto de entrada al poblado

- **Grupo:** Quebradas y drenaje · **id:** `subcuencas` · **tipo:** poligono
- **Fuente:** Modelo D8 (Copernicus GLO-30 + quebradas IGM)
- **Qué es:** Cada subcuenca es el área que entra a un poblado por un mismo cauce.
- **Clasificación por `tipo`:** Subcuenca (entra por una quebrada); Escorrentía local de laderas
- **Campos:** `isla` (ej.: Santa Cruz), `tipo` (ej.: Escorrentía local), `destino` (ej.: Zona poblada rural), `area_km2` (ej.: 0.96), `descripcion` (ej.: Laderas pequeñas que escurren directamen), `fuente` (ej.: Modelo D8 sobre Copernicus GLO-30), `area_drenada_entrada_km2` (ej.: 42.56)

### Límite urbano

- **Grupo:** Zonas pobladas · **id:** `limite_urbano` · **tipo:** poligono
- **Fuente:** IGM 1:25 000
- **Campos:** `isla` (ej.: San Cristóbal), `nombre` (ej.: Puerto Baquerizo Moreno), `categoria` (ej.: Cabecera Cantonal y Capital Provincial), `fuente` (ej.: IGM 1:25 000)

### Barrios (Santa Cruz)

- **Grupo:** Zonas pobladas · **id:** `barrios` · **tipo:** poligono
- **Fuente:** CGREG
- **Campos:** `isla` (ej.: Santa Cruz), `nombre` (ej.: Punta Estrada), `area_ha` (ej.: 14.27), `fuente` (ej.: CGREG)

### Población estimada por manzana

- **Grupo:** Zonas pobladas · **id:** `manzanas` · **tipo:** poligono
- **Fuente:** INEC MGN 2026 y viviendas SNGR
- **Clasificación por `poblacion_estimada`:** Sin dato; 1–10 hab.; 10–20; 20–40; Más de 40
- **Campos:** `isla` (ej.: San Cristóbal), `codigo` (ej.: 200151001001001), `viviendas` (ej.: 2), `poblacion_estimada` (ej.: 4.6), `fuente` (ej.: INEC MGN 2026 + viviendas SNGR)

### Vías

- **Grupo:** Vías y evacuación · **id:** `vias` · **tipo:** linea
- **Fuente:** OpenStreetMap, 31-oct-2026
- **Clasificación por `jerarquia`:** Principal; Secundaria; Local; Camino de tierra
- **Campos:** `isla` (ej.: Santa Cruz), `jerarquia` (ej.: Secundaria), `tipo_osm` (ej.: tertiary), `fuente` (ej.: OSM 31-oct-2026), `nombre` (ej.: Avenida Baltra), `superficie` (ej.: sett), `puente` (ej.: True)

### Rutas de evacuación por tsunami

- **Grupo:** Vías y evacuación · **id:** `rutas` · **tipo:** linea
- **Fuente:** SNGR
- **Clasificación por `tipo`:** Principal; Secundaria
- **Campos:** `isla` (ej.: Santa Cruz), `tipo` (ej.: Principal), `via` (ej.: JUAN MONTALVO), `fuente` (ej.: SNGR)

### Salud, refugios y seguridad

- **Grupo:** Puntos clave · **id:** `puntos_criticos` · **tipo:** punto
- **Fuente:** MSP, SNGR, MINEDUC, IGM y OSM
- **Filtro:** `categoria` ∈ salud, refugio, zona_segura, sirena, educacion, emergencia
- **Clasificación por `categoria`:** Salud pública, hospital o centro de salud; Refugio; Zona segura o punto de encuentro; Sirena de alerta; Centro educativo; Policía y bomberos
- **Campos:** `categoria` (ej.: salud), `nombre` (ej.: Hospital General Oskar Jandal), `subtipo` (ej.: Hospital general), `fuente` (ej.: MSP 2023), `institucion` (ej.: MSP), `nivel` (ej.: NIVEL 2), `isla` (ej.: San Cristóbal), `en_zona_tsunami` (ej.: True), `en_susc_alta_media` (ej.: True), `capacidad_personas` (ej.: 89), `capacidad_familias` (ej.: 22), `capacidad` (ej.: 0)

### Servicios: salud privada, agua, energía, transporte

- **Grupo:** Puntos clave · **id:** `puntos_servicios` · **tipo:** punto
- **Fuente:** IGM y OSM
- **Filtro:** `categoria` ∈ salud_privada, agua, energia, transporte, telecom, gobierno
- **Clasificación por `categoria`:** Consultorio, laboratorio o farmacia; Agua (tanques, captaciones); Energía y combustible; Muelles, aeropuertos y puentes; Telecomunicaciones; Gobierno
- **Campos:** `categoria` (ej.: salud_privada), `nombre` (ej.: Saltos Yepez Dolores Isabel), `subtipo` (ej.: Consultorio general), `fuente` (ej.: MSP 2023), `institucion` (ej.: PRIVADO), `nivel` (ej.: NIVEL 1), `isla` (ej.: Santa Cruz), `en_zona_tsunami` (ej.: True), `en_susc_alta_media` (ej.: True)

### Alojamiento, comercio y espacios de reunión

- **Grupo:** Puntos clave · **id:** `puntos_logistica` · **tipo:** punto · **zoom mínimo:** 14
- **Fuente:** IGM y OSM
- **Filtro:** `categoria` ∈ alojamiento, abastecimiento, encuentro
- **Clasificación por `categoria`:** Alojamiento; Supermercado, ferretería o banco; Estadio, coliseo o iglesia
- **Campos:** `categoria` (ej.: alojamiento), `nombre` (ej.: Albemarle Hotel), `subtipo` (ej.: hotel), `fuente` (ej.: OSM), `isla` (ej.: Isabela), `en_zona_tsunami` (ej.: True), `en_susc_alta_media` (ej.: True)

### Relieve sombreado

- **Grupo:** Relieve · **id:** `sombreado` · **tipo:** raster
- **Fuente:** Copernicus GLO-30

### Curvas de nivel cada 10 m

- **Grupo:** Relieve · **id:** `curvas` · **tipo:** linea · **zoom mínimo:** 14
- **Fuente:** Derivadas de Copernicus GLO-30
- **Clasificación por `maestra`:** Maestra (cada 50 m); Intermedia (10 m)
- **Campos:** `isla` (ej.: Santa Cruz), `elevacion_m` (ej.: 10), `maestra` (ej.: False)

### Pendientes fuertes (laderas)

- **Grupo:** Relieve · **id:** `pendientes` · **tipo:** raster
- **Fuente:** Copernicus GLO-30

## Otros archivos

- `edificios_expuestos.geojson`: se publica, pero no está activada en el manifiesto (se puede añadir como capa).
- `parque_zonificacion.geojson`: se publica, pero no está activada en el manifiesto (se puede añadir como capa).
- `capas.json`: manifiesto (grupos, estilos, leyendas y encuadres). Especificación en `04-especificacion-capas-json.md`.
- `resumen_exposicion.json`: edificios y población expuestos por isla.
- `raster/limites.json`: encuadre de cada PNG.
- `area_interes.geojson`: área de interés (zona agrícola y urbana completas, cuencas que drenan a poblados y márgenes de 500 m alrededor de las zonas pobladas y de 300 m alrededor de las vías).
