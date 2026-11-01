# Fuentes y licencias

Todas las fuentes se consultaron el **1 de noviembre de 2026**. Hay un catálogo extendido de los servicios probados, con sus URL y capas, en `geodatos/docs/fuentes-oficiales.md`.

## Fuentes usadas

| Fuente | Qué aporta | Acceso | Licencia y atribución |
|---|---|---|---|
| **IGM**, cartografía 1:25 000 de Galápagos | Quebradas, límite urbano, terreno inundable, lagunas, poblados, vías y edificios | WFS `https://www.geoportaligm.gob.ec/galapagos25/ows` | Información pública del Estado ecuatoriano. Citar «Instituto Geográfico Militar del Ecuador (IGM), 1:25 000». |
| **CGREG** (publicado en el GeoNode de la Fundación Charles Darwin) | Zonificación del PNG 2017, suelo urbano y rural, riesgo de inundación (Puerto Ayora y Puerto Villamil), flujos de lodo por El Niño, derrumbes, encañadas con buffer de 20 m y barrios | `https://geodata.fcdarwin.org.ec` | Uso con cita al CGREG y a la FCD. Para usos formales, confirmar la licencia con el CGREG. |
| **SNGR** (servidor ArcGIS) | Inundación por tsunami (INOCAR), rutas de evacuación, zonas seguras, sirenas, albergues, eventos históricos y viviendas con población estimada | `https://sgrportal.gestionderiesgos.gob.ec/server/rest/services` | Servicio público; licencia no declarada. Citar a la SNGR y, para el tsunami, al INOCAR. |
| **MSP** (vía SNGR) | Establecimientos de salud, 2023 | Ídem | Citar al MSP. |
| **MINEDUC** (vía SNGR) | Instituciones educativas, 2021; la lista está incompleta | Ídem | Citar al MINEDUC. |
| **INEC**, Marco Geoestadístico 2026 | Manzanas y sectores censales | `https://idgn.ecuadorencifras.gob.ec` | Información pública. Citar al INEC. |
| **CONALI** (vía SNGR) | Parroquias 2026 | SNGR | Citar a CONALI. |
| **OpenStreetMap** (Geofabrik, 31-oct-2026) | Vías, edificios, servicios y uso del suelo | `download.geofabrik.de` | **ODbL 1.0**: obligatorio «© colaboradores de OpenStreetMap». Las bases de datos derivadas deben mantener la ODbL. |
| **Google Open Buildings v3** | Huellas de edificios en Santa Cruz e Isabela | Google Research | **CC BY 4.0** (con la ODbL como alternativa). Citar «Google Open Buildings». |
| **Copernicus GLO-30 DEM** | Relieve y todas las capas modeladas | AWS Open Data `copernicus-dem-30m` | Licencia Copernicus DEM, libre con atribución: «produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA». |
| **Mapas base** | Esri Light Gray y World Imagery, OSM, OpenTopoMap | Teselas en línea | Las atribuciones aparecen en el mapa. OpenTopoMap es CC-BY-SA. |

## Atribución sugerida para el mapa

> Fuentes: IGM 1:25 000; CGREG/FCD (zonificación PNG 2017, riesgos, encañadas, barrios); SNGR/INOCAR; MSP; MINEDUC; INEC MGN 2026; © colaboradores de OpenStreetMap (ODbL); Google Open Buildings (CC BY 4.0); Copernicus GLO-30 © DLR, Airbus, UE/ESA. Capas modeladas: elaboración propia (USFQ Galápagos), noviembre de 2026.

## Datos personales y privacidad

- **Eliminados** de las capas finales: nombres y teléfonos de responsables de albergues (SNGR), nombres y teléfonos de las fuentes de los eventos de la SNGR y responsables de actualización.
- Los datos crudos de `geodatos/descargas/oficiales/` **sí contienen** esos campos. **No publicarlos ni compartirlos.**
- No hay datos de personas afectadas. La población es agregada por manzana.

## Lo que no existe o no se pudo obtener

- **Mapa oficial de amenaza por inundación pluvial para Galápagos:** no existe. Las capas nacionales de la SNGR y del INEC no tienen entidades en las islas.
- **Activaciones satelitales:** no hay ninguna de Copernicus EMS ni del Charter para estas inundaciones.
- **Catastro municipal** de los tres GAD: hay que pedirlo a cada municipio.
- **SIIG del CGREG:** requiere usuario.
- **Delimitación oficial de las áreas afectadas del 30–31 de octubre:** pendiente. Hay que pedirla al COE cantonal y a la SNGR, o levantarla con dron.

## Aviso de seguridad (para comunicar a las instituciones)

Al revisar las fuentes se detectó que algunos servicios públicos del INEC (`mgnwms2026/FeatureServer`) y de la SNGR **permiten crear, editar y borrar sin token**. Solo se hicieron lecturas. Conviene avisar a esas instituciones por un canal oficial.
