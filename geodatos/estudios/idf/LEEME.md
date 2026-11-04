# Curvas IDF provisionales y tormentas en la escala de años

> **Modelo propio, no dato oficial.** Estas curvas IDF (intensidad, duración y frecuencia) son un **orden de magnitud**. Sirven para poner las tormentas sintéticas y el 30-oct en una escala de años. **No sirven para diseñar obras.** La referencia oficial sería el estudio de intensidades del INAMHI de 2015, que todavía no tenemos (#77).

Issues: #24 (curvas IDF) y #26 (modelo 2D y periodos de retorno). Script: `scripts/34_curvas_idf.py`.

## Qué es una curva IDF

Dice cuánta lluvia cae en un lugar en cierto tiempo, y cada cuántos años pasa. Por ejemplo, «en Los Guayabillos, 57 mm en 1 hora caen una vez cada 10 años». Cada curva corresponde a un periodo de retorno (2, 5, 10, 25, 50 y 100 años).

## Cómo se armaron

1. **Lluvia de 1 día.** Son los máximos anuales medidos por los pluviómetros de la FCD:
   - Puerto Ayora: 61 años, de 1965 a 2025;
   - Bellavista: 31 años, de 1988 a 2018.

   Se ajustó una distribución de Gumbel como valor central y una GEV como sensibilidad. Los intervalos salen de remuestrear los años.
2. **Paso a horas.** Se usa el reanálisis GAR horario (TU Berlín: modelo WRF de 2 km forzado con ERA5, 1980–2025, CC BY 4.0), que es **lluvia modelada**:
   - en cada punto se calcula qué fracción de la lluvia del día cae en 1, 2, 3, 6 y 12 h: es la media de los máximos anuales de cada duración dividida por la media de los máximos de 1 día;
   - GAR horario pesa ≈30 GB, así que solo se bajaron los **5 días más lluviosos de cada año en cada isla**: 385 días, leídos uno por uno por HTTP;
   - las ventanas no cruzan la medianoche UTC, que son las 18:00 en Galápagos;
   - para pasar de 1 día a 24 h móviles se usa el factor de Weiss (×1,13);
   - las horas de GAR suman exactamente su lluvia diaria.
3. **Cada pluviómetro** toma la curva de 1 día de la FCD más parecida en altura (Puerto Ayora para menos de 100 m; Bellavista para el resto). **No se escala con GAR**, porque su gradiente de altura no está validado: en la celda de Santa Rosa, GAR da 1,8 veces la lluvia de Bellavista. Lo que diría GAR queda en `factor_gar_informativo`.
4. **San Cristóbal** no tiene una serie larga medida (#78), así que toma prestada la curva de Santa Cruz a la misma altura. Las fracciones horarias sí son las de GAR en sus propios puntos.

**Contraste con lo medido.** En los días de 40 mm o más en las estaciones del IERSE desde abril de 2026, la hora más fuerte trae el 16–47 % de la lluvia del día (mediana 27 %). En GAR esa fracción es del 31–39 %, y el 30-oct fue del 30–36 %.

## Resultados

### Cuánta lluvia y cada cuánto (Gumbel; entre corchetes, el intervalo del 90 %)

| Pluviómetro | 1 h, 10 años | 3 h, 10 años | 24 h, 10 años | 1 h, 100 años | 24 h, 100 años |
|---|---|---|---|---|---|
| INAMHI Puerto Ayora (costa) | 41 mm [34–48] | 67 mm | 150 mm | 69 mm | 250 mm |
| Los Guayabillos (178 m) | 57 mm [43–77] | 95 mm | 164 mm | 92 mm | 265 mm |
| INAMHI Puerto Baquerizo (prestada) | 44 mm | 85 mm | 150 mm | 73 mm | 250 mm |

El umbral **«alto» de la v0.2 (30 mm en 1 h) equivale a la lluvia de ≈2 años** en Los Guayabillos y de ≈4 años en la costa.

### El 30-oct-2026 en la escala de años (lluvia medida por el IERSE)

| | 1 h | 3 h | 6 h | 24 h |
|---|---|---|---|---|
| Los Guayabillos | 63 mm, ≈15 años | 133 mm, **≈43 años** | 155 mm, ≈36 años | 179 mm, ≈14 años |
| Santa Rosa | 71 mm, ≈32 años | 139 mm, ≈42 años | 175 mm, ≈43 años | 240 mm, **≈56 años** |

Con la GEV, que tiene la cola más pesada, los periodos bajan a 11–27 años. En resumen, **el 30-oct fue una lluvia de unos 15 a 55 años**, más rara en 3–6 h que en 1 h o en el día. Que en 24 h salga más frecuente que en el estudio de Santa Cruz (≈23 años) es porque aquí se compara con 24 h móviles y no con el día de lectura fija.

### ¿Cada cuánto se inunda cada zona? (500 tormentas sintéticas por isla, `figuras/fragilidad_*.png`)

A cada tormenta se le asignó el periodo de retorno de la lluvia que marcan los pluviómetros de su zona: el máximo entre 1, 3, 6 y 24 h. Con eso se ajustó una curva «probabilidad de inundarse según el periodo de retorno», que luego se combina con la probabilidad de cada lluvia en un año.

| Zona | Se inunda (≥ 0,3 m) la mitad de las veces con una lluvia de… | Se inundaría ≈1 vez cada… | «Alto» v0.2 ≈1 vez cada… | Falsas alarmas por año |
|---|---|---|---|---|
| La Cascada | 29 años | **12 años** | 1,6 años | ≈0,6 |
| Tomás de Berlanga | más de 400 años | 50 años | 1,6 años | ≈0,6 |
| Bellavista | 22 años | 10 años | 1,6 años | ≈0,5 |
| Barrio Frío | 21 años | **8 años** | 1,9 años | ≈0,4 |
| El Manzanillo | 91 años | 28 años | 1,9 años | ≈0,5 |
| El Progreso | 94 años | 36 años | 1,9 años | ≈0,5 |

- **La regla v0.2 daría «alto» más o menos una vez cada año y medio a dos años.** Casi todas esas veces no habría inundación: una falsa alarma cada ≈2 años por zona. Es el precio de avisar casi todas las inundaciones (#30).
- La Cascada y Barrio Frío serían las zonas que más se inundan, con algo así como una vez cada 10 años. **No hay registro histórico con qué contrastarlo** (#80).
- Los mapas `figuras/mapa_retorno_*.png` muestran dónde se junta el agua con lluvias de 2–10, 10–50 y más de 50 años, y la combinación «una vez cada… años».

## Límites (léase antes de usar una cifra)

- **Una sola fuente medida por isla, y prestada en San Cristóbal.**
  - La cola de 50–100 años sale de 31 a 61 años de datos: el intervalo del 90 % es amplio, y la GEV da hasta un 45 % más que la Gumbel a 100 años.
  - El dato de Bellavista de marzo de 2008 (490 mm) está en duda (#73) y pesa en la cola.
- **GAR es lluvia modelada en una malla de 2 km.** Suaviza los chubascos cortos, así que en 1 h puede quedarse corto frente a un pluviómetro. Los días candidatos no cruzan la medianoche UTC.
- **Lo que se mide es la lluvia, no la inundación.** El periodo de retorno de una tormenta es el de la lluvia en los pluviómetros, que no es el mismo que el de la inundación.
- **Las frecuencias por año arrastran todos los límites del modelo 2D:**
  - el DSM incluye techos y árboles;
  - no hay red pluvial;
  - la pérdida del suelo no está calibrada en San Cristóbal;
  - el conjunto de tormentas es sintético.
- **Qué las mejoraría:**
  - el estudio del INAMHI (#77);
  - las series de San Cristóbal (#78);
  - la tesis de la USFQ (#79);
  - las inundaciones históricas con hora (#80);
  - más años de lluvia medida cada 5 minutos.

## Archivos

| Archivo | Qué es |
|---|---|
| `datos/idf_puntos.csv` | Lluvia (mm y mm/h) por punto, duración y periodo de retorno, con el intervalo del 90 % y la variante GEV |
| `datos/razones_puntos.csv` | Fracción de la lluvia del día que cae en 1–24 h (GAR), referencia FCD y factor GAR informativo |
| `datos/periodo_retorno_30oct.csv` | El 30-oct en años (Gumbel y GEV) |
| `datos/ierse_dias_40mm.csv` | Días de ≥ 40 mm medidos por el IERSE y sus razones |
| `datos/periodo_tormentas_<isla>.csv` | Periodo de retorno de cada tormenta sintética en cada pluviómetro |
| `datos/tormentas_por_periodo.json` | Curvas logísticas, probabilidad anual, «alto» por año y tabla por intervalos |
| `datos/resumen_idf.json` | Ajustes, sesgo informativo GAR/FCD y medianas del IERSE |
| `figuras/idf_<isla>.png`, `idf_metodo.png`, `fragilidad_<isla>.png`, `mapa_retorno_<isla>.png` | Figuras |
| `cache/` (no versionado) | Días de GAR horario (`descargar`) y pilas para los mapas |

Rehacer:
1. `scripts/34_curvas_idf.py descargar`: ≈1 h desde Galápagos; solo hace falta una vez.
2. `scripts/flujo.py --solo curvas_idf`.

El paso necesita la lluvia diaria de GAR del script 29 (`29_marburg_darwin.py --descargar`).
