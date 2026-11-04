# Fase 0: ¿sirven los pronósticos globales para anticipar la lluvia fuerte en Galápagos?

Evaluación del archivo de pronósticos 2024–2026, hecha antes de publicar un pronóstico en `sosgalapagos.org/clima`. Fecha: 4-nov-2026. Versión 2, corregida tras la revisión independiente (al final hay una lista de los cambios).

- **Scripts:** `clima/scripts/06_pronostico_archivo.py` (descarga) y `07_pronostico_evaluacion.py` (evaluación y calibración).
- **Resultados:** las tablas y las figuras están en esta carpeta.

> Los pronósticos son estimaciones de modelos, no datos oficiales. El pronóstico oficial lo emite el INAMHI.

## Resumen

1. **En las islas, los modelos globales se quedan muy cortos en milímetros.** El 22-feb-2024, la FCD midió 215 mm en Puerto Ayora y los modelos daban 1–5 mm. Para el 30-oct-2026, la víspera, daban entre 0 y 33 mm en la parte alta de Santa Cruz (mediana de unos 9 mm), y en Santa Rosa llovieron 238 mm. Ni sus milímetros ni la probabilidad cruda de sus conjuntos sirven tal cual.
2. **Aun así, los modelos «suben» los días en que llueve fuerte.** Se mide con el **consenso**: el percentil de cada modelo dentro de lo que ese modelo suele pronosticar en ese punto, promediado entre 7 modelos (5 a 7 según la fecha).
   - En temporada lluviosa, el consenso distingue los días con 20 mm o más con un AUC de 0,85–0,92 para hoy, mañana y pasado mañana, y de 0,82–0,86 a 4 días.
   - Sin modelo, la climatología del mes da 0,64 y la persistencia, 0,54–0,74.
3. **Una curva logística por anticipación,** calibrada con la lluvia medida, convierte el consenso en la probabilidad de que alguna estación de la zona mida 20 mm o más ese día.
   - En validación cruzada, para hoy, mejora a la frecuencia climatológica en todos los grupos (BSS): parte alta de San Cristóbal en temporada lluviosa, 0,25; parte alta de Santa Cruz en la garúa de 2026, 0,14; costa de Puerto Ayora en temporada lluviosa, 0,10.
4. **El 23-oct y el 30-oct tuvieron «señal alta» desde 4 días antes, en validación cruzada** (al calibrar se dejó fuera todo octubre). El 3-oct (68 mm) y el 4-oct (44 mm) no tuvieron señal.
5. **En la costa funciona peor.** La probabilidad nunca pasó del 30 %, y de 8 días con 50 mm o más en Puerto Ayora, 6 no tuvieron señal.
6. **Estos modelos no pronostican la intensidad en 1–3 h.** Lo de las horas previas se vigila con las estaciones y con el satélite (GOES-19, trabajo aparte en `clima/satelite/`).

**Decisión:** se publica una señal diaria calibrada para hoy y los 4 días siguientes: la probabilidad de ≥ 20 mm, tres niveles con colores neutros (no de alerta) y lo «normal en esta época» como referencia. Va rotulada como pronóstico experimental y no oficial, y con su evaluación a la vista.

- No se publican los milímetros de los modelos como cantidad esperada.
- No se muestra la probabilidad de 50 mm en los recuadros, porque tiene poca habilidad.
- Los conjuntos se guardan para calibrarlos más adelante. Por ahora solo muestran cuándo se concentra la lluvia, en bloques de 6 h.

## Datos

| Qué | Fuente | Periodo | Uso |
|---|---|---|---|
| Pronósticos con 0, 1, 2, 3, 5 y 7 días de anticipación, hora a hora | Archivo de corridas anteriores de Open-Meteo (CC BY 4.0): ECMWF IFS 0,25°, ECMWF AIFS (IA, desde feb-2025), NOAA GFS, DWD ICON, UK Met Office, Météo-France ARPEGE y Canadá GEM. ECMWF IFS 9 km, solo desde fines de 2025 | ene-2024 → 1-nov-2026 | Todo |
| Lluvia diaria, parte alta de San Cristóbal | GSC-USFQ: El Junco, Cerro Alto, El Mirador y Merceditas (privado; se exporta del servidor) | 2015 → may-2026 | Grupo `san_cristobal_alta` |
| Lluvia diaria, Puerto Ayora | Fundación Charles Darwin (CC BY-NC-SA) | 1965 → jun-2026 | Grupo `costa` |
| Lluvia cada 5 min, Santa Cruz | IERSE: Santa Rosa, Los Guayabillos, Cerro Crocker y Militar (días con ≥ 80 % de cobertura) | 25-abr → 31-oct-2026 | Grupos `santa_cruz_alta` y `costa` |

- **Día:** el de Galápagos, de 00 a 24 h (UTC−6). El GSC marca el día continental (UTC−5); esa hora de desfase se ignora. Para el GSC, IERSE y la FCD se probó un desfase de −1, 0 y +1 día frente al modelo, y el mejor fue 0.
- **Anticipación N:** cada hora pronosticada N×24 h antes (`precipitation_previous_dayN`).
  - Cada corrida reemplaza su tramo de 24 h, y el retraso de publicación de 3–8 h no se descuenta.
  - Por eso, la «anticipación 1» de un día usa corridas que estuvieron listas hasta la madrugada de ese mismo día: equivale al recuadro **«hoy»** de la web.
  - La anticipación 2 equivale a **«mañana»**, la 3 a **«pasado mañana»** y la 5 a los días 3 y 4. El pronóstico en vivo aplica esa correspondencia (`pronostico.py`, día k → anticipación k+1).
- **Referencias sin modelo:**
  - **Climatología:** la lluvia media del mes en la estación, sin el año evaluado. Para la parte alta de IERSE se usa la serie FCD de Bellavista.
  - **Persistencia:** la lluvia medida N días antes.

## Discriminación (AUC para estación-días con ≥ 20 mm; 0,5 = azar)

| Grupo y temporada | Estación-días ≥ 20 mm | Consenso: hoy (ant. 1) | mañana (2) | pasado (3) | 4 días (5) | Climatología | Persistencia (1–3) |
|---|---|---|---|---|---|---|---|
| San Cristóbal alta, lluviosa | 105 | **0,89** (IC90 0,86–0,92) | 0,85 | 0,85 | 0,82 | 0,64 | 0,66–0,74 |
| Costa (Puerto Ayora), lluviosa | 17 | **0,90** (0,86–0,94) | 0,90 | 0,92 | 0,86 | 0,64 | 0,54–0,73 |
| Santa Cruz alta, garúa 2026 | 22 | **0,88** (0,81–0,93) | 0,82 | 0,80 | 0,76 | 0,24 | 0,44–0,61 |
| Santa Cruz alta, lluviosa (solo may-2026) | 3 | 0,44 (sin muestra) | | | | | |

- **El consenso queda a la altura del mejor modelo de cada celda y es más estable.** No siempre es mejor: en Santa Cruz, AIFS da 0,85 para mañana, y en la costa, UKMO da 0,94 a 4 días; las muestras de cada modelo son distintas.
- **El AIFS de ECMWF (IA) es el modelo individual más constante.** Coincide con la evaluación de ECMWF con el INAMHI para Ecuador continental.
- **ICON no sirve en la parte alta de Santa Cruz** (AUC 0,54–0,62).
- **IFS 9 km no gana a los modelos de 25 km** con un día o más de anticipación.
- **En la garúa de San Cristóbal** hay solo 2 días con 20 mm o más en 2024–2026: no se puede evaluar.

En Santa Cruz en temporada lluviosa no hay evidencia local: los únicos datos (mayo de 2026, 3 días de lluvia fuerte) dan un AUC de 0,44. Por eso, de enero a mayo, Santa Cruz usa la curva de San Cristóbal.

Las tablas completas, por modelo, anticipación y temporada, están en `metricas.csv`. Las figuras son `f_auc_20mm.png` y `f_auc_50mm.png`.

## Calibración: del consenso a una probabilidad

- **Evento:** la estación más lluviosa del grupo mide 10, 20 o 50 mm o más en el día. Las estaciones de cada grupo son:
  - parte alta de Santa Cruz: Santa Rosa, Los Guayabillos y Cerro Crocker;
  - parte alta de San Cristóbal: El Junco, Cerro Alto, El Mirador y Merceditas;
  - costa: FCD Puerto Ayora y Militar.
- **Curva:** una logística sobre el consenso promedio del grupo, por grupo, temporada y anticipación.
- **Validación cruzada:** se deja fuera un año; en Santa Cruz, que solo tiene 2026, se deja fuera un mes.
- **Datos:** `calibracion_logistica.csv`.

| Grupo y temporada | Días-grupo ≥ 20 mm (de n) | Frecuencia normal | Ant. | P si consenso 0,80 | 0,90 | 0,95 | BSS (validación cruzada) |
|---|---|---|---|---|---|---|---|
| San Cristóbal alta, lluviosa | 54 (388) | 14 % | 1 | 23 % | 40 % | 51 % | 0,25 |
| | | | 2 | 23 % | 38 % | 47 % | 0,17 |
| | | | 5 | 24 % | 40 % | 49 % | 0,15 |
| Costa, lluviosa | 17 (404) | 4 % | 1 | 3 % | 10 % | 17 % | 0,10 |
| | | | 2 | 4 % | 10 % | 17 % | 0,10 |
| | | | 5 | 3 % | 8 % | 11 % | 0,08 |
| Santa Cruz alta, garúa | 15 (148) | 10 % | 1 | 47 % | 64 % | 72 % | 0,14 |
| | | | 2 | 41 % | 55 % | 62 % | 0,06 |
| | | | 5 | 41 % | 55 % | 62 % | 0,09 |

**Casos especiales** (`pronostico_calibracion.json`, columna `estado`):
- **Santa Cruz alta, temporada lluviosa:** usa la curva de San Cristóbal alta (`prestada_de`).
- **Costa y San Cristóbal alta en garúa:** hubo 0 y 2 días con 20 mm o más, así que no hay con qué calibrar. Usan la curva de su propia temporada lluviosa, pero muestran la frecuencia normal de la garúa.
  - En 2024–2026, esa curva no habría dado ninguna «señal alta» en garúa y solo 1 día de «señal moderada» (sin lluvia fuerte).
  - Un «sin señal» fijo habría sido peligroso. La primera versión daba 0 % en Puerto Ayora el 30-oct, con el consenso en 0,97, cuando el INAMHI midió 94 mm ese día y 135 mm el 31.
  - Con la curva prestada, ese día habría salido «señal moderada» (≈ 20 %). El problema apareció al reconstruir el 30-oct con el código de producción.
- **Curvas sin habilidad:** si el BSS de validación cruzada es menor de 0,03, la curva queda como `sin_habilidad` y se publica «no evaluable».
- **50 mm:** el BSS va de 0,00 (costa) a 0,16 (Santa Cruz, con 5 días). Solo se muestra en el detalle, marcado «poco fiable».
- **Isabela:** sin estaciones. Usa San Cristóbal alta (parte alta) y la costa (pueblo), rotulado «orientativo».

## Niveles publicados y qué pasó con ellos (validación cruzada)

Los niveles se definen por la probabilidad de ≥ 20 mm:
- **señal alta:** ≥ 35 %;
- **señal moderada:** 15–35 %;
- **sin señal:** < 15 %;
- **no evaluable:** sin curva con habilidad.

| Grupo y temporada | Día de la web | Nivel | Días | Con ≥ 20 mm | Con ≥ 50 mm |
|---|---|---|---|---|---|
| San Cristóbal alta, lluviosa | hoy | señal alta | 63 | 49 % | 16 % |
| | | señal moderada | 51 | 20 % | 2 % |
| | | sin señal | 274 | 5 % | 2 % |
| | mañana | señal alta | 46 | 37 % | 15 % |
| | | señal moderada | 83 | 33 % | 5 % |
| | | sin señal | 258 | 4 % | 2 % |
| Costa, lluviosa | hoy | señal moderada | 49 | 16 % | 4 % |
| | | sin señal | 355 | 3 % | 2 % |
| | mañana | señal moderada | 45 | 18 % | 4 % |
| | | sin señal | 358 | 3 % | 2 % |
| Santa Cruz alta, garúa 2026 | hoy | señal alta | 5 | 3 de 5 | 2 de 5 |
| | | señal moderada | 21 | 19 % | 5 % |
| | | sin señal | 122 | 7 % | 2 % |

**Días con 50 mm o más:**

| Grupo | Días | hoy: alta / moderada / sin señal | mañana: alta / moderada / sin señal |
|---|---|---|---|
| San Cristóbal alta | 15 | 10 / 1 / 4 | 7 / 4 / 4 |
| Costa | 8 | 0 / 2 / 6 | 0 / 2 / 6 |
| Santa Cruz alta | 5 | 2 / 1 / 2 | 2 / 0 / 3 |

**Eventos de Santa Cruz (probabilidad de ≥ 20 mm en validación cruzada):**

| Día | Medido | hoy | mañana | pasado | 4 días |
|---|---|---|---|---|---|
| 30-oct | 238 mm | 82 % | 79 % | 77 % | 65 % |
| 23-oct | 97 mm | 61 % | 55 % | 58 % | 52 % |
| 14-jun | 65 mm | 32 % | 13 % | 16 % | 12 % |
| 3-oct | 68 mm | 10 % | 5 % | 8 % | 13 % |
| 4-oct | 44 mm | 4 % | 3 % | 7 % | 14 % |

**Sobreconfianza en Santa Cruz:** con probabilidades altas la curva se pasa. Los días con señal alta anuncian en promedio un 67–70 % y en la mitad de ellos llovió 20 mm o más. Por eso la web redondea a múltiplos de 5 %, rotula la zona como «calibración provisional» y muestra junto al porcentaje lo «normal en esta época».

Las tablas son `senal_niveles.csv` y `senal_dias_fuertes.csv`. La serie con validación cruzada (`senal_validacion_cruzada.csv.gz`) no se versiona, porque lleva series del GSC; se regenera con el script.

## Intensidad en 3 h (IERSE, abr–oct-2026)

- Los modelos distinguen algo los 8 días con un máximo de ≥ 20 mm en 3 h: AUC de 0,6–0,9 según el modelo (`metricas_3h.csv`).
- En milímetros, ninguno se acerca con un día de anticipación: el máximo es 23 mm (IFS 9 km), frente a 118 mm medidos en 3 h el 30-oct.
- La corrida más reciente de IFS 9 km sí dio un pico de 98 mm en 3 h, pero entre las 03 y las 06 h del 31-oct, unas 8 h después del pico medido. Ese tramo coincide con un corte de transmisión de IERSE, así que no se puede verificar.
- **Conclusión:** no se publica un nivel de inundación pronosticado. La regla de inundación sigue usando solo la lluvia medida.

## Limitaciones

- **Santa Cruz tiene una muestra pequeña:** 6 meses, 15 días-grupo con 20 mm o más y 5 con 50 mm o más, casi todos en un octubre anómalo con El Niño. Su calibración es provisional hasta tener una temporada lluviosa (ene–may-2027).
- **El consenso no siempre tiene los mismos modelos.** En la evaluación, el 24 % de los punto-días tuvo 5 modelos, el 31 % tuvo 6 y el 45 %, 7 (AIFS empieza en feb-2025 y UKMO tiene huecos). En vivo siempre habrá 7. La diferencia debería ser pequeña, pero hay que vigilarla con el archivo en vivo.
- **Percentiles con todo el archivo:** la climatología de los modelos se calcula con todo el archivo, incluido el periodo evaluado. La revisión recalculó el consenso con percentiles que excluyen el bloque evaluado y el BSS no cambió (0,200 frente a 0,202).
- **Las estaciones tienen sus propios límites:**
  - la FCD de Puerto Ayora es un pluviómetro manual de lectura diaria;
  - el GSC tiene años con huecos;
  - IERSE tiene cortes de transmisión (sus totales son mínimos) y su balancín subestima por encima de 50 mm/h.
- **Conjuntos:** Open-Meteo no guarda sus corridas viejas con la anticipación. El pronóstico en vivo las archiva desde ahora. La prueba con los conjuntos de ECMWF en los eventos principales está en `conjuntos_eventos.md`.

## Cambios tras la revisión independiente (v2)

- Correspondencia anticipación ↔ día de la web (anticipación 1 = «hoy»), una curva por anticipación y la señal limitada a 5 días.
- Estados `sin_eventos`, `pocos_eventos` y `sin_habilidad`, con «no evaluable» en lugar de una cifra sin respaldo. En garúa, la costa y San Cristóbal usan la curva de la temporada lluviosa (ver «Casos especiales»).
- Prueba de punta a punta: se reconstruyeron con el código de producción (`senal()`) varios días de 2026 a partir del archivo en los puntos de zona. En la cuenca alta de La Cascada, el 30-oct sale «señal alta» del día 0 al 4 (55–69 %) y el 23-oct también (38–54 %). El 3-oct sale «sin señal» hasta el día 2 y «moderada» a 4 días (17 %). El 15-sep, un día seco, sale «sin señal» (2–4 %).
- Colores neutros. «Atención» pasa a «señal moderada». El aviso sube a la cabecera. Se muestra lo «normal en esta época». La probabilidad de 50 mm sale de los recuadros. Se nombran las estaciones de cada grupo.
- Correcciones del 30-oct: lo que daban los modelos la víspera (0–33 mm, no «10–30») y el pico de IFS 9 km (el 31-oct de madrugada, no «el mismo día»).
- Se cuentan días-grupo en lugar de estación-días donde corresponde. La persistencia va de 0,54 a 0,74. Se aclara que el consenso no siempre es mejor que el mejor modelo.
- Los deterministas con corrida conocida de más de 30 h salen del consenso.

## Qué falta

- **Recalibrar con los pronósticos archivados en vivo** y comprobar que «hoy» y «mañana» en vivo se comportan como las anticipaciones 1 y 2 del archivo.
- **Calibrar los conjuntos** (IFS ENS, AIFS ENS) con su archivo propio, cuando haya al menos una temporada.
- **Combinar con la vigilancia satelital de 0–6 h** (`clima/satelite/`).
