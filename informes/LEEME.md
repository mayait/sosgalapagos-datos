# Informes técnicos (borradores para discusión)

Serie de informes en formato de artículo académico que documentan los modelos, los datos y la metodología del proyecto. Cada informe es un `.tex` que se compila a PDF con la clase común `plantilla/sosg-informe.cls`.

- **Responsable y firma:** Julián Maya, Universidad San Francisco de Quito (USFQ), jamaya@usfq.edu.ec. La clase pone la firma, la licencia y la forma de citar en la primera página.
- **Estado:** todos son *borradores para discusión*. **Modelo propio ≠ dato oficial** (AGENTS.md, regla 3).
- **Licencia:** texto, figuras y modelos propios bajo CC BY 4.0, con atribución obligatoria a la USFQ. Los datos de terceros conservan su licencia; ver `LICENCIA-DATOS.md` en la raíz.

## Serie

| Número | Carpeta | Tema |
|---|---|---|
| 2026-01 | `2026-01-base-hand/` | Base geoespacial y susceptibilidad topográfica (HAND) |
| 2026-02 | `2026-02-tormentas-idf/` | Tormentas sintéticas y curvas IDF provisionales |
| 2026-03 | `2026-03-lluvia-clima/` | Lluvia observada del 30–31-oct, climatología y nivel del mar |
| 2026-04 | `2026-04-la-cascada/` | La Cascada: cuenca aportante, vaso cerrado y desvío |
| 2026-05 | `2026-05-reconocimiento/` | Reconocimiento hidrológico de gabinete (puntos, cruces y San Cristóbal) |
| 2026-06 | `2026-06-modelo-2d/` | Modelo hidrodinámico 2D *rain-on-grid* del 30-oct |
| 2026-07 | `2026-07-alerta-v02/` | Nivel preliminar de inundación por lluvia medida (regla v0.2) |
| 2026-08 | `2026-08-pronostico/` | Pronóstico experimental de lluvia fuerte (fase 0) |
| 2026-09 | `2026-09-satelite/` | Vigilancia satelital GOES-19 de convección profunda (evaluación S0) |
| 2026-10 | `2026-10-infraestructura/` | Infraestructura abierta de datos, flujo reproducible y gobernanza |

## Compilar

```bash
informes/compilar.sh 2026-02-tormentas-idf     # → informes/2026-02-tormentas-idf/informe.pdf
informes/compilar.sh todos
```

- **Requisitos:** pdfLaTeX, BibTeX y latexmk, que vienen con TinyTeX (`~/Library/TinyTeX`) o con TeX Live.
- **Paquetes que falten:** `~/Library/TinyTeX/bin/universal-darwin/tlmgr install <paquete>`. Para saber cuál es: `tlmgr search --global --file /<archivo>.sty`.
- **Auxiliares:** quedan en `<informe>/.build/`, que no se versiona.

## Cómo se escribe uno

1. **Carpeta:** `AAAA-NN-tema/` con:
   - `informe.tex`;
   - `bib-AAAA-NN.bib`, con las referencias propias del informe;
   - opcionalmente `figuras/` y un `figuras.py` que las genere.
2. **Preámbulo mínimo:**
   ```latex
   \documentclass{sosg-informe}
   \graphicspath{{../../geodatos/estudios/santa-cruz/figuras/}{figuras/}}
   \title{Título largo\\en varias líneas}
   \titulocorto{Título corto (cabecera)}
   \titulocita{Título largo en una línea (para la cita)}
   \numero{2026-NN}
   \relacionados{Issues \issue{12} y \issue{34} · repositorio mayait/sosgalapagos-datos}
   \date{4 de noviembre de 2026}
   ...
   \bibliographystyle{sosg}
   \bibliography{referencias,bib-2026-NN}
   ```
   La firma (Julián Maya, USFQ, correo) va por omisión. Solo se cambia con `\autores{}`, `\autorescita{}`, `\afiliacion{}` y `\correo{}`.
3. **Estructura:**
   - resumen y palabras clave (`abstract`, `\palabrasclave{}`);
   - recuadro `aviso` («modelo propio, no dato oficial»; preparado con asistencia de agentes de IA, sin visita de campo ni revisión profesional externa; licencias de los datos usados);
   - Introducción;
   - Área de estudio y datos;
   - Métodos, con ecuaciones numeradas y la cita de cada método;
   - Resultados, con tablas `booktabs` y figuras con leyenda completa;
   - Discusión y limitaciones;
   - Conclusiones y trabajo futuro (issues);
   - Disponibilidad de datos y código (scripts y carpetas exactos);
   - Referencias.
4. **Referencias:**
   - `referencias.bib` es común: no la edites en paralelo con otras sesiones. Lo nuevo va en el `bib-AAAA-NN.bib` del informe.
   - Si no estás seguro de un título, de los autores o de las páginas, dilo en el campo `note` («por completar»). **No inventes referencias.**

## Reglas (además de AGENTS.md)

- **Cifras:**
  - Salen de los `resumen*.json`, CSV y textos del repositorio. No inventes resultados.
  - Si una cifra no está, dilo («no calculado»).
  - Cita los scripts por su nombre completo, porque hay números repetidos (#57).
- **Sin URL ni endpoints de las fuentes meteorológicas** (IERSE, WeatherLink, Tempest, Open-Meteo, buckets de GOES, plataforma DARWIN).
  - Solo se nombra la fuente, o se da su DOI.
  - No se escribe la IP ni la configuración de los servidores.
- **Sin datos personales:**
  - Nunca nombres de personas afectadas.
  - La estación Tempest es «estación particular».
  - No describas fallas de seguridad de servicios oficiales.
- **Sin recomendaciones en voz de la universidad:**
  - Nada de «se recomienda» ni «recomendamos».
  - Escribe riesgos, observaciones o «los resultados no justifican…», o atribuye la medida a quien la propone.
- **Distingue siempre** lo medido, lo estimado por modelo y lo de referencia u oficial.
- **Horas:** UTC−6. INAMHI y GSC marcan UTC−5.
- **Idioma:** español claro; «refugio», nunca «albergue»; coma decimal; `\enquote{}` para las comillas «».
- **Archivos generados:** no edites a mano los de otros directorios. Las figuras nuevas se generan con el `figuras.py` del informe.
