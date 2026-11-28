# Validación del HAND y del modelo 2D de Santa Cruz con lo observado

Aquí se mide qué tanto aciertan los modelos de inundación de Santa Cruz contra tres fuentes de observación. La salida es una tabla de contingencia completa: aciertos, falsas alarmas, fallos y secos bien clasificados.

| Archivo | Qué es | Cómo se hace |
|---|---|---|
| `huellas_muestra.geojson` | 120 puntos al azar, 30 por clase HAND, sobre las ortofotos del GAD del 3 y el 5-nov-2026. Cada punto trae su partición fija (`uso`: calibración o validación) y `revisar_humano` para un 20 % | `42_validacion_muestra.py`, con semilla fija. **No se rehace**: cambiaría la partición |
| `huellas_marcas.csv` | Lo que se ve en cada punto: `estado` (mojado, seco o dudoso), `evidencia`, `confianza`, `marcado_por` y `fecha_marca` | **A mano**. Es un dato de observación. Se marca a ciegas, sobre las hojas que genera 42 (`estudios/santa-cruz/figuras/validacion/`, solo locales), sin ver la clase HAND ni el modelo |
| `contraste.json` | Métricas contra la foto aérea del 21-nov, los reportes ciudadanos y las huellas | `43_validacion_contraste.py` |

## Cómo sumar una revisión

Quien revise agrega filas a `huellas_marcas.csv` con su propio `marcado_por`. Puede revisar los puntos con `revisar_humano = true` o cualquier otro. Después se corre 43: la salida trae el acuerdo entre las personas que marcaron, y las métricas siguen usando a la primera persona que aparece en el archivo.

## Límites

- **Las huellas no tienen fecha exacta.** Las ortofotos del 3 y el 5-nov muestran lo que dejaron las lluvias del **30-oct y el 2-nov**, sin poder separar un evento del otro.
- **La muestra solo cubre suelo visible.** Está tomada a 40 m o menos de una vía o un edificio, porque bajo los árboles no se ve el suelo. Bajo copas y techos el punto queda «dudoso».
- **Muestra estratificada.** Tiene el mismo número de puntos por clase HAND, no proporcional al área, así que las métricas por punto no equivalen a las de área. La **fracción mojada por clase** sí se lee directa.
- **La primera pasada la hizo Claude a ciegas sobre las fotos.** Hay que confirmarla con alguien que conozca la zona.
- **El HAND es el publicado sin el ajuste del 21-nov.** Contra el ajuste el contraste sería circular, porque se calibró con la foto y los reportes del 21-nov.
- **El modelo 2D del 30-oct se corrió con el relieve anterior** al DEM de 10 m de SIGTIERRAS.
