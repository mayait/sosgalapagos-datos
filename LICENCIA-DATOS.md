# Licencias del repositorio

© 2026 **Universidad San Francisco de Quito (USFQ)**, USFQ Galápagos. Responsable: **Julián Maya** (jamaya@usfq.edu.ec).

El repositorio tiene dos licencias propias, según el tipo de material, y respeta las de las fuentes externas.

| Qué | Licencia | Archivo |
|---|---|---|
| **Código**: scripts, recolector, web y plantillas | [Apache 2.0](LICENSE). Toda copia o trabajo derivado debe conservar el aviso [`NOTICE`](NOTICE), que atribuye la autoría a la USFQ | `LICENSE`, `NOTICE` |
| **Contenido propio**: textos, informes técnicos (`informes/`), estudios, figuras, mapas, capas y salidas de los modelos propios (HAND, cuencas, modelo 2D, tormentas sintéticas, curvas IDF, umbrales, pronóstico) | [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](LICENCIA-CC-BY-4.0.txt) | `LICENCIA-CC-BY-4.0.txt` |
| **Datos de terceros** y lo que se deriva de ellos | La licencia de cada fuente (tabla de abajo). Si es más restrictiva, **prevalece sobre CC BY 4.0** | — |

## Atribución obligatoria

La licencia CC BY 4.0 exige atribuir el material cada vez que se reproduce, se adapta o se publica: en artículos, tesis, informes, mapas, medios o software. La atribución debe incluir el autor, la institución, el título, el enlace y la licencia, e indicar si se hicieron cambios. Use esta forma:

> Maya, J. (2026). *SOS Galápagos: datos, modelos y herramientas para las inundaciones de 2026 en Santa Cruz y San Cristóbal (Galápagos)*. Universidad San Francisco de Quito (USFQ). https://github.com/mayait/sosgalapagos-datos. Licencia CC BY 4.0.

Para un informe técnico concreto, cite el informe. La forma de citarlo aparece al pie de su primera página.

Si usa los modelos o resultados en una publicación académica, cite además el informe técnico que los describe. GitHub muestra la cita en formato BibTeX y APA en «Cite this repository», a partir de [`CITATION.cff`](CITATION.cff).

> **Alcance de la obligación.** Una licencia rige la **copia y la adaptación** del material: código, textos, figuras, capas y datos. No puede obligar a citar ideas o resultados que se describen con palabras propias sin reproducir el material. Para esos casos se aplica la norma académica de citar la fuente, y por eso se publican `CITATION.cff` y las citas de cada informe.

## Datos de terceros

Estas fuentes conservan su licencia. Los productos que se derivan de ellas quedan sujetos a esas condiciones.

| Fuente | Licencia o condición | Efecto en lo derivado |
|---|---|---|
| OpenStreetMap | ODbL 1.0 | Las bases de datos derivadas se publican bajo ODbL, con «© colaboradores de OpenStreetMap» |
| Copernicus GLO-30 DEM | Licencia Copernicus DEM, libre con atribución | Texto de atribución de `mapas-galapagos/documentacion/03-fuentes-y-licencias.md` |
| **SGIAR**, Subsecretaría de Gestión de la Información y Análisis de Riesgo: DTM de 1 m de Santa Cruz (producto Vricon/Maxar) | EULA de Vricon/Maxar; entregado por la SGIAR, que autorizó publicarlo aquí. Cita obligatoria a la SGIAR (`geodatos/datos/dtm_sgiar/LEEME.md`) | No queda bajo CC BY 4.0. Lo derivado (HAND, cuencas, modelo 2D) cita a la SGIAR como fuente del relieve |
| Google Open Buildings v3 | CC BY 4.0 (u ODbL) | Atribución «Google Open Buildings» |
| IGM, CGREG, SNGR, INOCAR, INEC, MSP, MINEDUC, CONALI | Información pública con cita a la institución | Citar a la institución. Para usos formales, confirmar con ella |
| IERSE (Universidad del Azuay), red WSN | CC BY-NC-ND 4.0, con cita obligatoria (`clima/datos/LEEME.md`) | Sin uso comercial y **sin obras derivadas**. Los modelos que usan su lluvia necesitan el permiso escrito del titular |
| Fundación Charles Darwin (FCD), series climáticas | CC BY-NC-SA | Lo derivado (p. ej., curvas IDF) se comparte **sin uso comercial y con la misma licencia** |
| USFQ GSC, estaciones de San Cristóbal | Licencia no declarada (#46) | No se redistribuyen sus series |
| Proyecto DARWIN (U. de Marburgo) | Acuerdo de datos que prohíbe redistribuir (#76) | Solo metadatos y DOI |
| GAR (TU Berlín) | CC BY 4.0 | Cita a Schmidt et al. (2025) |
| Open-Meteo | CC BY 4.0 | Atribución «Open-Meteo» |
| NOAA (GOES-19) | Dominio público | Se agradece la cita |

Catálogo completo de las fuentes: `mapas-galapagos/documentacion/03-fuentes-y-licencias.md` y `geodatos/docs/fuentes-oficiales.md`.

## Sin garantía

Todo se entrega **tal cual, sin garantía**: Apache 2.0, §7–8, y CC BY 4.0, §5. Los modelos son estimaciones propias, **no datos oficiales**. No sirven para delimitar zonas, normar ni diseñar obras.
