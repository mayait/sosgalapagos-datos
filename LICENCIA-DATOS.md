# Licencias del repositorio

© 2026 **Universidad San Francisco de Quito (USFQ) · SOS Galápagos**. Autor y responsable: **Julián Maya** (jamaya@usfq.edu.ec).

El repositorio tiene dos licencias propias, según el tipo de material, y respeta las de las fuentes externas.

| Qué | Licencia | Archivo |
|---|---|---|
| **Código**: scripts, modelos como programa, web y plantillas | [Apache 2.0](LICENSE): se puede usar, copiar, modificar y redistribuir, también con fines comerciales. Toda copia o trabajo derivado conserva el [`NOTICE`](NOTICE) y el aviso de autoría de cada archivo | [`LICENSE`](LICENSE), [`NOTICE`](NOTICE) |
| **Contenido propio**: datos, textos, estudios, figuras, mapas, capas y salidas de los modelos propios (HAND, cuencas, modelo 2D, tormentas sintéticas, curvas IDF, umbrales, pronóstico, nivel de lluvia) | [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.es): se puede copiar, adaptar y usar, también con fines comerciales, **dando crédito** | este archivo |
| **Datos de terceros** y lo que se deriva de ellos | La licencia de cada fuente (tabla de abajo), que **prevalece** sobre CC BY 4.0. Se publican con permiso de cada operador | — |

**Crédito en toda atribución:** SOS Galápagos · Universidad San Francisco de Quito (USFQ) · Julián Maya <jamaya@usfq.edu.ec>.

**Donde una fuente es más restrictiva, manda la fuente.** Por ejemplo: las bases de datos derivadas de OpenStreetMap se publican bajo ODbL; lo derivado de las series de la Fundación Charles Darwin, bajo CC BY-NC-SA; la lluvia de IERSE, bajo CC BY-NC-ND 4.0. En esos casos no rige CC BY 4.0.

## Atribución obligatoria

La licencia CC BY 4.0 exige atribuir el material cada vez que se reproduce, se adapta o se publica: en artículos, tesis, informes, mapas, medios o software. La atribución debe incluir el autor, la institución, el título, el enlace y la licencia, e indicar si se hicieron cambios. Use esta forma corta:

> SOS Galápagos · Universidad San Francisco de Quito (USFQ) · Julián Maya <jamaya@usfq.edu.ec>. Licencia CC BY 4.0.

O esta, para una cita académica:

> Maya, J. (2026). *SOS Galápagos: datos, modelos y herramientas para las inundaciones de 2026 en Santa Cruz y San Cristóbal (Galápagos)*. Universidad San Francisco de Quito (USFQ). https://github.com/mayait/sosgalapagos-datos. Licencia CC BY 4.0.

Si usa los modelos o resultados en una publicación académica, cite el repositorio. GitHub muestra la cita en formato BibTeX y APA en «Cite this repository», a partir de [`CITATION.cff`](CITATION.cff).

> **Alcance de la obligación.** Una licencia rige la **copia y la adaptación** del material: código, textos, figuras, capas y datos. No puede obligar a citar ideas o resultados que se describen con palabras propias sin reproducir el material. Para esos casos se aplica la norma académica de citar la fuente, y por eso se publica `CITATION.cff`.

## Datos de terceros

Estas fuentes conservan su licencia. Los productos que se derivan de ellas quedan sujetos a esas condiciones.

| Fuente | Licencia o condición | Efecto en lo derivado |
|---|---|---|
| OpenStreetMap | ODbL 1.0 | Las bases de datos derivadas se publican bajo ODbL, con «© colaboradores de OpenStreetMap» |
| Copernicus GLO-30 DEM | Licencia Copernicus DEM, libre con atribución | Texto de atribución de `mapas-galapagos/documentacion/03-fuentes-y-licencias.md` |
| **SGIAR**, Subsecretaría de Gestión de la Información y Análisis de Riesgo: DTM de 1 m de Santa Cruz (producto Vricon/Maxar) | EULA de Vricon/Maxar; entregado por la SGIAR, que autorizó publicarlo aquí. Cita obligatoria a la SGIAR (`geodatos/datos/dtm_sgiar/LEEME.md`) | No queda bajo nuestra licencia. Lo derivado (HAND, cuencas, modelo 2D) cita a la SGIAR como fuente del relieve |
| **SIGTIERRAS** (MAG): DEM de 10 m de Santa Cruz, y sus cuencas, subcuencas y drenaje procesados por el **Instituto de Geografía de la USFQ** (María Belén Zapata) | Información pública con cita a SIGTIERRAS; las capas del Instituto, con crédito al Instituto de Geografía USFQ (`geodatos/datos/usfq_geografia/LEEME.md`). El DEM no se redistribuye por ahora | Lo derivado (HAND y cauces de Santa Cruz fuera del DTM de la SGIAR) cita «DEM 10 m: SIGTIERRAS» |
| **ESPOL** (Maurizio Mulas, Daniel Garcés, Erwin Larreta, Victoria Rosado y Valeria Vaca): cuencas hidrográficas de interés de Santa Cruz | De sus autores; se publican con su crédito con nombre (`geodatos/docs/fuentes-oficiales.md` §3.1d) | Cualquier mapa o descarga que las use nombra a los cinco autores |
| **Foto aérea del 21-nov-2026 en Puerto Ayora** (Tui De Roy) | De su autora. Se publica con el crédito «Foto: Tui De Roy» (`geodatos/datos/foto_aerea_21nov/LEEME.md`) | La foto rectificada y sus teselas no quedan bajo nuestra licencia. La zona afectada y los edificios derivados citan la foto |
| Google Open Buildings v3 | CC BY 4.0 (u ODbL) | Atribución «Google Open Buildings» |
| IGM, CGREG, SNGR, INOCAR, INEC, MSP, MINEDUC, CONALI | Información pública con cita a la institución | Citar a la institución. Para usos formales, confirmar con ella |
| IERSE (Universidad del Azuay), red WSN | CC BY-NC-ND 4.0, con cita obligatoria (`clima/datos/LEEME.md`). **Publicado con su permiso** (confirmado por Julián Maya el 22-nov-2026) | Sin uso comercial y sin obras derivadas para terceros. Quien quiera derivar de su lluvia pide permiso a IERSE |
| Fundación Charles Darwin (FCD), series climáticas | CC BY-NC-SA. **Publicado con su permiso** (22-nov-2026) | Lo derivado (p. ej., curvas IDF) se comparte **sin uso comercial y con la misma licencia** |
| USFQ GSC, estaciones de San Cristóbal | No declara una licencia abierta. **Publicado con su permiso** (22-nov-2026) | Sus series se publican con la cita que pide el GSC. Para reutilizarlas, pedir permiso al GSC |
| INAMHI, estaciones automáticas, pronóstico y advertencias | No declara una licencia abierta. **Publicado con su permiso** (22-nov-2026) | Citar al INAMHI. El documento oficial manda |
| Proyecto DARWIN (U. de Marburgo) | Acuerdo de datos que prohíbe redistribuir (#76) | Solo metadatos y DOI |
| GAR (TU Berlín) | CC BY 4.0 | Cita a Schmidt et al. (2025) |
| Open-Meteo | CC BY 4.0 | Atribución «Open-Meteo» |
| NOAA (GOES-19) | Dominio público | Se agradece la cita |

Catálogo completo de las fuentes: `mapas-galapagos/documentacion/03-fuentes-y-licencias.md` y `geodatos/docs/fuentes-oficiales.md`.

## Sin garantía

Todo se entrega **tal cual, sin garantía de ningún tipo** y sin responsabilidad del autor ni de la USFQ por su uso: para el código, según la Licencia Apache 2.0, secciones 7 (exclusión de garantía) y 8 (limitación de responsabilidad); para el contenido propio, según CC BY 4.0, sección 5. Los modelos son estimaciones propias, **no datos oficiales**. No sirven para delimitar zonas, normar ni diseñar obras.

## Historia

Hasta el 22-nov-2026 el repositorio salió bajo Apache 2.0 y CC BY 4.0. Del 22 al 23-nov-2026 el código tuvo todos los derechos reservados y lo propio, CC BY-NC-ND 4.0. Desde el 23-nov-2026 vuelven Apache 2.0 y CC BY 4.0. Los textos anteriores están en `Archivo/licencias-anteriores/`.
