[[SALTO]]

# 2. Contexto, área de estudio y datos

## 2.1 Contexto

En la tarde y la noche del 30 de octubre y la madrugada del 31 de octubre de 2026, lluvias intensas asociadas a un evento de El Niño fuerte provocaron el desbordamiento de varias quebradas y cañadas en Santa Cruz (Galápagos). El cantón declaró la emergencia el 30 de octubre.

En Puerto Ayora, el barrio **La Cascada** fue uno de los sectores más afectados. La SNGR registró daños en la UPC y en el edificio de la DINAF del sector, y la alcaldía lo señaló como el sector donde «han perdido todo». La SNGR también registró **un fallecido en Bellavista**, en la cuenca alta. La SNGR y la prensa sitúan las personas afectadas entre varios cientos y más de 3 000, con cifras preliminares e incoherentes entre sí (sección 3.4). El barrio ya figuraba en el registro de inundaciones de la SNGR de abril de 2023.

La coordinación de respuesta de USFQ Galápagos pidió este análisis para responder a una pregunta concreta: **¿se pueden desviar las quebradas que bajan hacia La Cascada?** También pidió identificar los problemas de fondo y las opciones desde lo urbano y desde la gestión del riesgo.

## 2.2 Área de estudio

La Cascada está en el **norte de Puerto Ayora**, a 0,9–1,25 km del mar. Su centroide aproximado es −90,3137; −0,7335. El polígono del barrio, que une las capas de OSM y del CGREG, ocupa 6,1 ha a una cota de entre 10,5 y 18 m. Al norte se levanta un escarpe de unos 20–25 m, el borde de una fosa tectónica (graben), por encima del cual comienza el Parque Nacional Galápagos. Más arriba, la cuenca atraviesa la zona agrícola y Bellavista (≈200 m) y llega hasta unos 860 m de altitud.

## 2.3 Datos utilizados

Tabla: Fuentes de datos.

| Tema | Fuente | Resolución / fecha | Uso |
|---|---|---|---|
| Elevación | Copernicus GLO-30 (DSM) | 30 m; ±2–4 m en vertical | Cuenca, vaso, perfiles, corredores y vistas 3D |
| Hidrografía | IGM 1:25 000 (WFS); OpenStreetMap | Sin fecha / 31-oct-2026 | Quebradas, quemado del DSM y puntos acotados |
| Edificaciones | OSM + Google Open Buildings v3 | 2023–2026 | Exposición |
| Población | INEC (manzanas, estimación); SNGR (viviendas) | 2021–2025 | Exposición |
| Vías | OSM con nombres | 31-oct-2026 | Corredores urbanos y cruces |
| Riesgos y suelo | CGREG/SIIG (flujos de lodo, suelo urbano, franja de quebradas); SNGR (eventos 2010–2025, refugios) | Varias | Amenaza, recurrencia y normativa |
| Parque Nacional | DPNG/CGREG (límite y zonificación de 2017) | 2017 | Encaje legal del desvío |
| Lluvia (evento) | Open-Meteo: ECMWF IFS 9 km y 0,25°, GFS, ICON, UKMO, Météo-France, JMA y ERA5 | Horaria y diaria, 15-oct a 1-nov-2026 | Estimación del evento |
| Lluvia (clima) | Fundación Charles Darwin, dataZone (Puerto Ayora 1965–2026; Bellavista 1987–2019) | Diaria | Climatología y Niños de referencia |
| Océano | NOAA OISST v2.1; NOAA CPC; ERFEN | Diaria y semanal | Contexto de El Niño |
| Afectación | SNGR (SitRep 01 de Galápagos, SitRep 67 nacional); prensa | 31-oct a 1-nov-2026 | Contexto y validación |

## 2.4 Herramientas

El análisis se hizo íntegramente con **software libre** en Python 3.12, en un Mac con Apple Silicon:
- **rasterio** y **pyproj**: lectura y reproyección del modelo de elevación;
- **pysheds**: dirección de flujo D8, acumulación, cuencas y relleno de depresiones;
- **shapely** y **scipy**: geometrías, búsquedas de caminos de mínimo umbral y de corredores (Dijkstra) y llenado conectado;
- **SCS-CN** con hidrograma unitario SCS, programado ad hoc;
- **matplotlib**: mapas, perfiles y vistas 3D;
- **reportlab**: este documento.

Los scripts `12_cascada_analisis.py`, `13_cascada_figuras.py` y `14_cascada_informe.py` regeneran todos los resultados, las figuras y el PDF (anexo A). La sección 9 detalla las herramientas que harían falta para pasar del reconocimiento al diseño.
