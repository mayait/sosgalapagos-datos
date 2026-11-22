# Anexo de la fase 0: ¿aporta el CAPE?

Generado por `clima/scripts/09_pronostico_cape.py` el 22-11-2026. **No edites este archivo a mano.**

> El CAPE, la lluvia y las probabilidades de este anexo son estimaciones de modelos, no datos oficiales. El pronóstico oficial lo emite el INAMHI. **Esta prueba no cambia la calibración publicada.**

## Qué se probó

- **CAPE** (energía disponible para la convección, J/kg): el máximo horario del día de Galápagos, como percentil dentro del propio modelo (punto y anticipación), promediado entre los modelos que lo tienen y luego entre los puntos del grupo.
- **Modelos con CAPE en el archivo de corridas anteriores de Open-Meteo:** GFS, UK Met Office, ARPEGE y GEM (hacen falta 3 de 4). ECMWF IFS, AIFS e ICON no guardan el CAPE con anticipación.
- **Base:** la logística de 07 sobre el consenso de lluvia (los mismos 7 modelos y la misma función). **Con CAPE:** la logística sobre consenso + percentil de CAPE; también con su interacción.
- **Evento:** la estación más lluviosa del grupo mide ≥ 20 mm. Anticipaciones 1, 2 y 5 días (recuadros «hoy», «mañana» y 4 días).
- **Validación cruzada:** los mismos bloques que 07 (fuera un año; si hay un solo año, fuera un mes). Base y CAPE se comparan en las mismas filas (las que tienen CAPE). ΔBrier y ΔAUC con bootstrap pareado por fechas (IC del 90 %).
- **Regla fijada antes de ver los resultados:** el CAPE aporta solo si, con anticipación 1 o 2, en al menos una celda con ≥ 10 días de evento, el IC de ΔBrier queda entero bajo 0, y en ninguna otra queda entero sobre 0.

**San Cristóbal no se evaluó:** faltan las series del GSC (`privado/gsc_diario.csv`, que no se versiona). Es el grupo con más eventos (54 días-grupo con ≥ 20 mm en temporada lluviosa); la prueba debe repetirse con él.

## Resultado

**Veredicto: no hay evidencia de que el CAPE mejore la probabilidad** (0 de 4 celdas evaluables con mejora clara según la regla).

| Grupo | Temporada | Ant. | Días (eventos) | BSS publicado | BSS base, mismas filas | BSS con CAPE | ΔBrier (IC90) | AUC base → con CAPE | ΔAUC (IC90) |
|---|---|---|---|---|---|---|---|---|---|
| Santa Cruz alta | garua | 1 | 145 (14) | 0,14 (aquí 0,14) | 0,13 | 0,12 | 0,0014 (-0,0032 a 0,0062) | 0,77 → 0,85 | 0,012 a 0,155 |
| Santa Cruz alta | garua | 2 | 141 (13) | 0,06 (aquí 0,06) | 0,07 | 0,07 | -0,0002 (-0,0052 a 0,0052) | 0,65 → 0,80 | 0,028 a 0,278 |
| Santa Cruz alta | garua | 5 | 127 (14) | 0,09 (aquí 0,09) | 0,07 | 0,07 | 0,0006 (-0,0017 a 0,0028) | 0,59 → 0,55 | -0,096 a 0,008 |
| Costa | lluviosa | 1 | 403 (17) | 0,10 (aquí 0,10) | 0,10 | 0,10 | -0,0001 (-0,0003 a 0,0002) | 0,88 → 0,88 | -0,006 a 0,007 |
| Costa | lluviosa | 2 | 399 (17) | 0,10 (aquí 0,10) | 0,10 | 0,10 | -0,0001 (-0,0006 a 0,0004) | 0,86 → 0,86 | -0,013 a 0,013 |
| Costa | lluviosa | 5 | 173 (5) | 0,08 (aquí 0,08) | 0,04 | 0,04 | 0,0001 (-0,0006 a 0,0008) | 0,81 → 0,81 | -0,035 a 0,044 |

- «BSS publicado» es el de `informe.md`; «aquí» es la misma curva rehecha con este archivo (todas las filas, sin exigir CAPE): si se parecen, la base está bien reproducida.
- ΔBrier negativo = mejor con CAPE. Un ΔAUC positivo solo dice que el CAPE ordena mejor los días; si el Brier no baja, la probabilidad publicada no sería mejor.
- Santa Cruz alta, garua, anticipación 1: sin calibrar, el CAPE solo ordena los días más o menos como el consenso (AUC 0,85 frente a 0,83), y los dos se mueven juntos (correlación 0,75): el CAPE trae casi la misma información que el consenso. La subida del AUC en validación cruzada (0,77 → 0,85) no es fiable: la base pierde AUC al rehacer la curva mes a mes (0,83 sin validación), y los días fuertes vienen en rachas de varios días, así que el bootstrap por día da un intervalo demasiado estrecho.
- Santa Cruz alta, garua, anticipación 2: sin calibrar, el CAPE solo ordena los días más o menos como el consenso (AUC 0,83 frente a 0,76), y los dos se mueven juntos (correlación 0,78): el CAPE trae casi la misma información que el consenso. La subida del AUC en validación cruzada (0,65 → 0,80) no es fiable: la base pierde AUC al rehacer la curva mes a mes (0,76 sin validación), y los días fuertes vienen en rachas de varios días, así que el bootstrap por día da un intervalo demasiado estrecho.
- Las tablas completas (interacción, CAPE solo, coeficientes, correlación con el consenso) están en `cape_metricas.csv`.

## Octubre de 2026 (El Niño)

Si el CAPE solo dijera «es octubre», distinguiría octubre del resto pero no los días de lluvia fuerte dentro de octubre. AUC cruda (sin calibrar) dentro y fuera de octubre, anticipación 1:

| Grupo | Periodo | Días (eventos) | Percentil de CAPE medio | en días de evento | AUC del CAPE | AUC del consenso |
|---|---|---|---|---|---|---|
| Santa Cruz alta | oct-2026 | 31 (5) | 0,65 | 0,74 | 0,78 | 0,77 |
| Santa Cruz alta | resto | 148 (12) | 0,59 | 0,71 | 0,76 | 0,74 |
| Costa | oct-2026 | 31 (0) | 0,66 | — | — | — |
| Costa | resto | 928 (17) | 0,49 | 0,92 | 0,94 | 0,96 |

## Eventos (anticipación 1, «hoy»)

El 30-oct fue convectivo; el 3 y el 23-oct, orográficos «cálidos». Probabilidad de ≥ 20 mm en validación cruzada («—»: celda sin curva). En la costa, desde jun-2026 solo hay la estación Militar (la serie de la FCD llega a jun-2026).

| Grupo | Día | Medido (mm) | Consenso | Percentil de CAPE | CAPE GFS / UKMO / ARPEGE / GEM (J/kg) | P base | P con CAPE |
|---|---|---|---|---|---|---|---|
| Santa Cruz alta | 2026-10-30 | 237,6 | 0,94 | 0,91 | 730 / 3380 / 1260 / 1770 | 0,77 | 0,84 |
| Santa Cruz alta | 2026-10-23 | 97,2 | 0,82 | 0,81 | 620 / 2620 / 310 / 1000 | 0,55 | 0,60 |
| Santa Cruz alta | 2026-10-03 | 68,2 | 0,54 | 0,64 | 20 / 1630 / 60 / 1070 | 0,10 | 0,11 |
| Santa Cruz alta | 2026-10-04 | 43,8 | 0,43 | 0,68 | 120 / 1780 / 60 / 860 | 0,04 | 0,09 |
| Santa Cruz alta | 2026-06-14 | 65,2 | 0,78 | 0,74 | 250 / — / 250 / 890 | 0,32 | 0,25 |
| Costa | 2026-10-30 | 2,0 | 0,91 | 0,92 | 805 / 3365 / 1105 / 1770 | — | — |
| Costa | 2026-10-23 | 0,0 | 0,75 | 0,80 | 620 / 2880 / 200 / 1000 | — | — |
| Costa | 2026-10-03 | 0,0 | 0,45 | 0,70 | 50 / 1665 / 55 / 1070 | — | — |
| Costa | 2026-10-04 | 0,0 | 0,47 | 0,67 | 120 / 1665 / 45 / 860 | — | — |
| Costa | 2026-06-14 | 0,0 | 0,80 | 0,76 | 320 / — / 245 / 890 | — | — |
| Costa | 2024-02-22 | 215,0 | 0,87 | 0,89 | 890 / — / 965 / 1590 | 0,06 | 0,06 |

## Disponibilidad en Open-Meteo (sondeo del 22-nov-2026 en Santa Cruz)

| Variable | Pronóstico en vivo | Corridas anteriores (con anticipación, 2024 y 2026) | Histórico de pronósticos (corrida más reciente) | Conjuntos |
|---|---|---|---|---|
| CAPE | IFS 0,25°, IFS 9 km, GFS, ICON, UKMO, ARPEGE, GEM (no AIFS) | GFS, UKMO, ARPEGE, GEM | GFS, ICON, UKMO, ARPEGE, GEM desde 2024; IFS 0,25° e IFS 9 km solo en 2026 | IFS ENS, GEFS, MOGREPS-G |
| Inhibición convectiva | GFS, UKMO, IFS 9 km | ninguno | GFS, UKMO; IFS 9 km en 2026 | GEFS |
| Índice de levantamiento | GFS | GFS | GFS | ninguno |
| Agua precipitable | IFS 0,25°, IFS 9 km, GFS | ninguno | IFS 0,25°; GFS e IFS 9 km en 2026 | IFS ENS |
| Chubascos (showers) | todos menos UKMO | todos menos AIFS y UKMO | todos menos UKMO | todos |
| Probabilidad de lluvia | IFS 0,25°, IFS 9 km, GFS, ICON, UKMO, GEM | ninguno | solo en 2026 (los mismos) | no se ofrece |
| Humedad y viento a 850 hPa | todos menos IFS 9 km | rechazados con el nombre `<variable>_previous_dayN` | todos menos IFS 9 km (UKMO solo en 2026) | IFS ENS, AIFS ENS |

El histórico de pronósticos solo trae la corrida más reciente (anticipación ≈ 0): no sirve para evaluar «hoy» ni «mañana». Es la única vía al CAPE de ICON en 2024–2026.

**Costo:** Open-Meteo cobra por punto máx(1, variables × modelos / 10), y en los conjuntos multiplica por los miembros. Añadir el CAPE a los 8 deterministas sube su peso de 1 a 1,6 por punto (≈ +100 llamadas al día con 7 puntos). En los conjuntos lo duplicaría (≈ +500 al día): no vale la pena.

## Recomendación

- **Recoger** el CAPE de los deterministas desde ya (barato) para evaluarlo con el archivo propio, con ECMWF incluido. **No usarlo** en la calibración publicada: con estos datos no la mejora. Repetir esta prueba con San Cristóbal (GSC) y con la temporada lluviosa de 2027.

## Incertidumbre y límites

- **Muestra pequeña:** cada celda tiene de 5 a 20 días de evento. Un IC de ΔBrier que cruza 0 quiere decir «no se puede distinguir», no «es igual».
- **Santa Cruz** solo tiene abr–nov-2026 (IERSE), casi todo en un octubre anómalo; la validación cruzada deja fuera un mes.
- **Solo 4 modelos con CAPE** y ninguno de ECMWF, que es el más constante en la lluvia. El CAPE de ECMWF IFS sí está en el pronóstico en vivo: si se recoge desde ahora, podrá evaluarse con una temporada de archivo propio.
- **El CAPE es de la celda del modelo (9–25 km)**, no del punto. En Galápagos buena parte de la lluvia fuerte es orográfica, y ahí el CAPE no tiene por qué ayudar.
- Archivo: corridas anteriores de Open-Meteo (CC BY 4.0), 2024-01-20 → 2026-10-31.
