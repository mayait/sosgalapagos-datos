# GOES-19 frente a la lluvia medida en Santa Cruz: evaluación S0

*SOS Galápagos · 4-nov-2026 · preliminar.* Scripts: `s0_extraer.py` y `s0_evaluar.py`. Cifras completas: `resumen.json`. Figuras: `figuras/`.

> ⚠️ Es una **estimación satelital** evaluada con **tres eventos** y una muestra pequeña de días. No es lluvia medida ni una alerta oficial. Las conclusiones pueden cambiar con más eventos.

## 1. Resumen

- **El satélite solo ve la lluvia convectiva (topes de nube muy fríos), y en esos casos sí da horas de aviso.** El 30-oct, la señal apareció **90–100 min antes** de que la regla de lluvia medida llegara a «medio» (RRQPE ≥ 10 mm/h a menos de 25 km) y **180–200 min antes** sobre la parte alta (≥ 10 % de la zona con topes < 221 K). Frente al pico de las 19–21 h, el adelanto fue de 3 a 5,5 h.
- **No vio los otros dos eventos.** El 23-oct (Santa Rosa 31 mm en 1 h) y el 3-oct (Los Guayabillos 68 mm) fueron lluvia orográfica de nubes bajas y medias: topes de 242–262 K, RRQPE ≈ 0 y sin rayos. Tampoco se activó en ninguno de los 5 días de la muestra con ≥ 10 mm en 1 h (mayo–octubre). **Que no haya señal satelital no quiere decir que no vaya a llover fuerte.**
- **Casi no da falsas alarmas.**
  - En la zona y a 25 km, ninguna señal se activó en los 14 días secos o moderados de la muestra (abril–octubre).
  - En octubre, día a día con la banda 13 cada hora: hubo topes < 221 K sin lluvia intensa en 2 de 28 días (7 %) en cada zona. Esos dos días llovió algo (5–12 mm en 1 h).
  - Ningún día seco de octubre tuvo señal.
- **Rayos (GLM): casi no hay en Galápagos.** En las ~530 h con datos del GLM (las 70 h de los eventos completas y 19 días muestreados a 1/6) hubo 141 destellos en una caja de ~500 × 450 km. El 30-oct los rayos llegaron **con** el pico de lluvia, no antes. No sirven como aviso.
- **RRQPE acierta la hora, no la cantidad.** El 30-oct dio la misma hora pico que Santa Rosa y Los Guayabillos (r = 0,8), pero subestimó la lluvia de 4 a 9 veces en el píxel. En lluvia cálida dio 0. Además, la NOAA dejó de producirlo el 2-nov y seguía sin producirlo el 4-nov: es un **riesgo operativo**.
- **Propuesta (§6):** usar el satélite como **señal de vigilancia aparte**, que se muestra junto al nivel de inundación pero **nunca lo baja y por ahora tampoco lo sube**. Regla v1 en `vigilancia.py`. Pronóstico y satélite se complementan: el consenso de modelos sí avisó del 23-oct con 4 días, y el satélite ve llegar la convección en las horas previas.

## 2. Datos y método

- **Satélite.** GOES-19 (GOES-East), disco completo cada 10 min, archivo abierto de la NOAA en AWS:
  - banda 13 (CMIP, 10,3 µm, temperatura de brillo Tb ≈ temperatura del tope de nube);
  - RRQPE (tasa de lluvia estimada, mm/h);
  - GLM (destellos de rayos).
  - Se leyeron por rangos solo los recortes: Santa Cruz con ~55 km de margen para el ABI y una caja de ~2° para el GLM.
- **Lluvia medida.** Tabla `obs` de `clima.db`, leída en modo solo lectura: IERSE (Santa Cruz, cada 5 min), INAMHI M0191 (Puerto Ayora; horaria hasta el 2-nov) y Tempest (Punta Estrada). Todas las horas en UTC.
- **Referencia: la regla de inundación v0.2 tal cual** (`recolector/inundacion.py`, sin persistencia), evaluada cada 10 min. Mismas estaciones, pesos, cobertura y humedad previa.
  - `t_medio`: primer momento en que la zona llega a «medio».
  - `t_alto`: primer momento en que llega a «alto».
  - `t_pico`: final de la hora con más lluvia.
  - El satélite solo es útil si se activa **antes** de `t_medio`: después, la regla ya avisa con lluvia medida.
- **Zonas** (`zonas_geo.json`): `la-cascada` (6 × 10 km) y `santa-cruz-alta` (22 × 13 km). Las otras zonas no tienen estaciones en estos eventos. Cada señal se mide en la zona, en la zona ampliada 25 km y en la ampliada 50 km.
- **Señales.**
  - Rayos: destellos GLM en 30 min.
  - Topes fríos: porcentaje de píxeles con Tb < 221 K (−52 °C, convección profunda) o < 235 K, y Tb mínima.
  - RRQPE: máxima y media.
  - Umbrales en `SENALES` y `COMBOS` de `s0_evaluar.py`.
- **Adelanto.** Se toma el episodio de señal que precede a la referencia, uniendo disparos separados por huecos de hasta 60 min. Solo cuenta si su último disparo está a menos de 3 h de la referencia. El adelanto es el tiempo desde el inicio del episodio.
- **Falsas alarmas.**
  - Muestra de días UTC con semilla fija entre abril y octubre de 2026:
    - 8 días secos: menos de 2 mm al día en todas las estaciones IERSE con al menos 80 % de cobertura; uno o dos por mes.
    - 6 días moderados: 5–25 mm en el día y menos de 10 mm en 1 h.
    - 5 días de lluvia fuerte: al menos 10 mm en 1 h, fuera de los tres eventos.
  - Cadencia de la muestra: ABI cada 30 min y 1 de cada 6 archivos GLM, con los conteos multiplicados por 6. Los eventos se reevalúan con esa misma cadencia para comparar.
  - Además, **todo octubre y el 1–2 de noviembre** con la banda 13 cada hora: tabla de contingencia día a día de los topes fríos frente a la lluvia intensa medida (R1h ≥ 15 mm o R3h ≥ 30 mm).
- **Coste.** ~4–5 GB bajados con un enlace de ~1 MB/s desde Galápagos. La lectura por rangos baja ~1 MB de los 24 MB de cada imagen de la banda 13 y ~55 KB de los 320 KB de cada archivo GLM.

## 3. Los tres eventos

| Evento | Zona | R1h máx. | R3h máx. | «medio» | «alto» | Tb mín. (zona / 25 km) | RRQPE máx. (zona / 25 km) | Rayos (zona / 25 km) |
|---|---|---|---|---|---|---|---|---|
| 30-oct | La Cascada | 61,0 | 133,0 | 15:10 | 15:50 | 202 / 191 K | 48 / 100 mm/h | 3 / 36 |
| 30-oct | Santa Cruz alta | 69,6 | 139,2 | 15:00 | 15:20 | 192 / 191 K | 100 / 100 mm/h | 10 / 39 |
| 23-oct | La Cascada | 23,4 | 36,9 | 04:40 | — | 242 / 231 K | 1,0 / 2,2 mm/h | 0 / 0 |
| 23-oct | Santa Cruz alta | 31,2 | 49,2 | 05:20 | 05:40 | 245 / 231 K | 1,0 / 2,2 mm/h | 0 / 0 |
| 3-oct | ambas | 15,6 | 27,4 | 18:30 | — | 261 / 260 K | 0 / 0 | 0 / 0 |

Horas de Galápagos (UTC−6). R1h y R3h en mm: el máximo de las estaciones válidas de la zona, con su peso.

### 30-oct: evento convectivo, detectado

![Santa Cruz alta, 30-oct](figuras/evento_2026-10-30_santa-cruz-alta.png)

- **Topes muy fríos sobre la parte alta desde las ~10:30.** Al menos 10 % de la zona tenía topes por debajo de 221 K desde las 11:40, **200 min antes del «medio»** (15:00) y 220 min antes del «alto». Después hubo una pausa de ~2 h con topes de 225–255 K. El primer chubasco fuerte de Santa Rosa (14–15 h, 43 mm en 1 h) cayó con topes de ~225 K, no por debajo de 221 K.
- **RRQPE ≥ 10 mm/h a menos de 25 km**: 90–100 min antes del «medio» en las dos zonas. Con ≥ 5 mm/h, 250–260 min antes.
- **Rayos: casi ninguno antes del pico.** Hubo 36–39 destellos a menos de 25 km en todo el evento, concentrados entre las 20:30 y las 21:30, en plena lluvia máxima. El GLM **no** dio aviso previo.
- La lluvia máxima (19–21 h, 61–70 mm en 1 h) coincidió con el escudo frío más intenso (Tb de 191–200 K) y con RRQPE saturada en 100 mm/h.
- **Si se exige además lluvia en curso en el suelo** (R1h ≥ 5 mm), el adelanto frente al «medio» desaparece: cuando aparece la señal satelital todavía no llueve fuerte en las estaciones.

![2 h antes del nivel medio](figuras/mapa_2026-10-30_menos2h.png)

### 23-oct y 3-oct: lluvia «cálida», invisible para el satélite

![Santa Cruz alta, 23-oct](figuras/evento_2026-10-23_santa-cruz-alta.png)

- **23-oct.** Santa Rosa midió 31 mm en 1 h y 81 mm en el evento. El tope más frío fue de 242–245 K sobre la zona (≈ −30 °C: nubes medias, no convección profunda), RRQPE nunca pasó de 2 mm/h y no hubo rayos. Los topes se enfriaron poco a poco durante ~6 h y lo más frío coincidió con la lluvia, sin aviso previo.
- **3-oct.** Los Guayabillos midió 68 mm (15,6 mm en 1 h). Los topes estuvieron a 255–262 K, RRQPE en 0 y no hubo rayos.
- Es la lluvia orográfica de nubes bajas y medias de la parte alta de Santa Cruz. El infrarrojo no la ve, porque los topes no son fríos y RRQPE se basa en el infrarrojo. **Ninguna señal satelital puede avisar de este tipo de evento.**
- Según la evaluación del pronóstico (sesión del pronóstico, `pronostico/`), el consenso de modelos sí daba «señal alta» para el 23-oct desde 4 días antes. **Pronóstico y satélite se complementan**: el pronóstico ve los días con ambiente lluvioso, incluida la lluvia orográfica; el satélite ve llegar la convección profunda en las horas previas.

## 4. RRQPE frente a los pluviómetros

Media horaria de RRQPE en el píxel de la estación y máximo en 3 × 3 y 5 × 5 píxeles (~6 y ~10 km; compensa el paralaje de 4–5 km), frente a la lluvia horaria medida.

| Estación | Evento | Medido (mm) | RRQPE píxel / máx. 5×5 (mm) | Máx. 1 h medido / RRQPE 5×5 | Misma hora pico | r (horario, 5×5) |
|---|---|---|---|---|---|---|
| Santa Rosa | 30-oct | 216 | 47 / 104 | 66 / 56 | sí (02Z) | 0,81 |
| Los Guayabillos | 30-oct | 153 | 17 / 52 | 61 / 26 | sí (02Z) | 0,80 |
| Puerto Ayora INAMHI | 30-oct | 206 | 48 / 128 | 37 / 41 | no (06Z / 03Z) | 0,29 |
| Punta Estrada (Tempest) | 30-oct | 69 | 70 / 146 | 19 / 42 | no (06Z / 03Z) | 0,39 |
| Cerro Crocker | 30-oct | 5 | 31 / 93 | 0,8 / 47 | — | −0,07 |
| Militar | 30-oct | 2 | 12 / 33 | 0,8 / 7 | — | 0,41 |
| Santa Rosa | 23-oct | 81 | 0 / 0,3 | 28 / 0,3 | — | — |
| Los Guayabillos | 3-oct | 68 | 0 / 0 | 13 / 0 | — | — |

- En el evento convectivo, RRQPE acierta **cuándo** llueve más en la parte alta (r = 0,8 y la misma hora pico), pero **subestima la cantidad**: de 4 a 9 veces en el píxel y de 1,6 a 3 veces en el máximo 5×5 en Santa Rosa, Los Guayabillos y Puerto Ayora. Además pone lluvia donde casi no llovió (Crocker, Militar). En Puerto Ayora el pico medido llegó 3 h después del de RRQPE (ojo: el respaldo horario del INAMHI tiene una hora de resolución y su hora de origen es la continental).
- En la lluvia orográfica cálida, RRQPE da **cero**.
- **RRQPE no sirve como dato de lluvia.** A lo sumo sirve como indicador de convección intensa cerca de la zona.
- **Riesgo operativo:** la NOAA dejó de producir RRQPE el 2-nov a las 16:50 UTC (también en GOES-18) y seguía sin producirlo el 4-nov. Una señal que dependa solo de RRQPE puede quedarse sin datos durante días.

## 5. Falsas alarmas

### 5.1 Muestra de días (abril–octubre, ABI cada 30 min y GLM 1/6)

Días con al menos un disparo de la señal, sobre los días con datos:

| Señal | Zona | Secos (8) | Moderados (6) | Lluvia fuerte (5) | Adelanto el 30-oct, misma cadencia (min antes del «medio») |
|---|---|---|---|---|---|
| ≥ 10 % de topes < 221 K | Santa Cruz alta (zona) | 0 | 0 | 0 | 180 |
| ≥ 10 % de topes < 221 K | La Cascada (zona) | 0 | 0 | 0 | — |
| RRQPE ≥ 10 mm/h | 25 km | 0 | 0 | 0 | 90–100 |
| RRQPE ≥ 10 mm/h | 50 km | 1 | 0 | 0 | 210 |
| ≥ 1 rayo en 30 min | 25 km | 0 | 0 | 0 | — |
| ≥ 1 rayo en 30 min | 50 km | 0 | 1 | 0 | — |
| **Regla v1** (RRQPE ≥ 10 a 25 km, o ≥ 10 % < 221 K en la zona, o rayo a 25 km) | ambas | **0** | **0** | **0** | **90–100** (antes, de 180 a 200 min, hubo un episodio de topes fríos sobre la parte alta, separado por una pausa de más de 1 h) |

- Los días de lluvia fuerte de la muestra fueron el 7-may (Militar, 22 mm en 1 h; fuera de las dos zonas), el 12-may (Santa Rosa, 16 mm), el 14-jun (Crocker 23 mm, Santa Rosa 13 mm), el 12-sep (Los Guayabillos, 13 mm) y el 10-oct (Los Guayabillos, 11 mm). En ninguno hubo topes < 221 K ni RRQPE ≥ 10 mm/h cerca. Fueron lluvias cálidas, como las del 3 y el 23-oct.
- La primera versión de la regla (v0: porcentaje de topes fríos a 25 km y RRQPE en la zona) no daba ningún adelanto el 30-oct, porque a 25 km el porcentaje de píxeles fríos se diluye. Por eso se cambió a v1.
- Si además se exige lluvia en curso (R1h ≥ 5 mm en alguna estación válida), las falsas alarmas siguen en 0, pero se pierde el adelanto frente al «medio».

### 5.2 Octubre completo, día a día (banda 13 cada hora)

Día de Galápagos con lluvia intensa medida: R1h ≥ 15 mm o R3h ≥ 30 mm, las ventanas cortas de «medio». Señal: ≥ 10 % de la zona con Tb < 221 K en alguna imagen horaria.

| Zona | Días | Aciertos | Fallos | Falsas alarmas | Días sin lluvia intensa con señal |
|---|---|---|---|---|---|
| La Cascada | 33 | 3 (30-oct, 31-oct, 2-nov) | 2 (3-oct, 23-oct) | 2 (24-oct: 4,9 mm en 1 h; 1-nov: 11,7 mm) | 2 de 28 (7 %) |
| Santa Cruz alta | 32 | 2 (30-oct, 1-nov) | 2 (3-oct, 23-oct) | 2 (24-oct: 6,6 mm; 2-nov: 11,2 mm) | 2 de 28 (7 %) |

- Las «falsas alarmas» fueron días con lluvia moderada. En los días secos de octubre no hubo ningún tope < 221 K sobre las zonas.
- Con un umbral más estricto (Tb mínima ≤ 210 K en la zona) no hay falsas alarmas, pero solo se detectan 1–2 días.
- **Adelanto fuera del 30-oct: ninguno.** El 1 y el 2-nov los topes fríos aparecieron a la vez que la lluvia intensa o después. Con imágenes horarias, el único día con aviso previo fue el 30-oct (180 min sobre la parte alta).
- En resumen: la señal de topes fríos es **específica** (casi no se activa sin lluvia) pero **poco sensible** (no ve la lluvia cálida, que en octubre fue la mitad de los días con lluvia intensa), y solo dio adelanto en un evento.

## 6. Propuesta para `recolector/inundacion.py`

**No se cambian los umbrales de la regla.** Con la evidencia actual (un solo evento convectivo con adelanto), la propuesta es prudente y por fases.

**Fase A (ya implementada en el colector y en el panel; falta integrarla en `inundacion.py`):** una **«vigilancia satelital»** aparte del nivel.

1. `inundacion.calcular()` añade a cada zona un campo `vigilancia_satelital`, calculado con `satelite/vigilancia.evaluar()` sobre las series `goes` de los últimos 40 min en `clima.db`:
   - `estado`: `"vigilancia"`, `"sin señal"` o `"sin datos"`;
   - `motivos`;
   - `desde`: primer disparo del episodio.
   `vigilancia.py` solo usa la biblioteca estándar. En el servidor está en `/opt/sosgalapagos-clima/satelite/`, así que habría que añadir esa carpeta a `sys.path` o copiar el archivo junto a `inundacion.py`.
2. **Regla v1:** RRQPE máxima ≥ 10 mm/h a menos de 25 km, **o** ≥ 10 % de la zona con topes < 221 K, **o** al menos un rayo a menos de 25 km en 30 min. Se mantiene 3 h después del último disparo.
3. **El nivel no cambia.** La tarjeta de la zona muestra «nivel bajo · vigilancia satelital: convección profunda cerca» y recomienda mirar las estaciones en las próximas horas.
   - **Nunca baja el nivel**: no tener señal no dice nada sobre la lluvia cálida.
   - **No lo sube por sí sola.**
   - Solo se calcula en las zonas con imagen; Isabela y San Cristóbal no están evaluadas.
4. **Silencio de las estaciones.** El 30-oct, las estaciones de la parte alta dejaron de transmitir hacia las 21:45, en pleno evento.
   - Si las estaciones callan y la vigilancia satelital está activa, la tarjeta debería decirlo de forma explícita: «sin datos de estaciones · el satélite muestra convección profunda».
   - Esto refuerza la regla actual de «silencio en alerta = alarma», sin cambiar sus umbrales.

**Fase B (solo cuando haya más evidencia):** que la vigilancia **adelante el «medio»**.

- Propuesta para entonces: si la vigilancia v1 lleva al menos 2 imágenes seguidas (20 min) en una zona calibrada y el nivel es «bajo», mostrar «medio (por satélite)», con persistencia de 3 h y sin escalar más allá de «medio».
- Requisitos antes de activarla:
  - al menos 3 eventos convectivos evaluados con adelanto;
  - una temporada completa de falsas alarmas con la cadencia real (10 min), sobre todo de enero a mayo, cuando la convección es más frecuente en Galápagos;
  - la revisión del especialista en gestión de riesgos del comité de estudios, como se hizo con la regla v0.2.
- El colector ya guarda todas las variables en `clima.db` desde que se publique. Esa serie servirá para la evaluación.

**Siguientes pasos de evaluación:** San Cristóbal, que tuvo lluvia intensa el 1 y el 2-nov según el GSC y aún no se ha evaluado; los eventos que vengan; y probar la tendencia de enfriamiento (Tb que baja más de 20 K en 1 h) como señal más temprana.

## 7. Operación en tiempo real (fase 3)

- **Latencia medida:** cada barrido ABI llega al bucket **9,7–10,2 min después de empezar** (el disco completo tarda ~10 min). El GLM llega en menos de 1 min. Con el timer cada 5 min, el panel muestra datos de 10–15 min de antigüedad.
- **Descarga por corrida:** ~1,3 MB de la banda 13, ~0,5 MB de RRQPE y ~10 MB de GLM cada 10 min. No se guarda ningún netCDF. En la Mac en Galápagos (~1 MB/s) una corrida tarda ~20 s; en el servidor, menos.
- `satelite.json`: 10–40 KB. Viaja dentro de `estado.json` (clave `satelite`), porque Caddy solo sirve los tres JSON conocidos.
- Probado en local en tiempo real y repitiendo el pico del 30-oct (`colector.py --ahora 2026-10-31T02:30:00Z`). **No se ha publicado.**

## 8. Limitaciones

- Tres eventos, de los que solo uno fue convectivo, y todos en Santa Cruz. Nada en San Cristóbal ni en Isabela.
- Las estaciones tienen cortes. El 30-oct, las de la parte alta dejaron de transmitir hacia las 21:45.
- Paralaje de 4–5 km hacia el oeste y píxel de ~2 km: la zona de La Cascada tiene ~15 píxeles.
- La muestra de falsas alarmas usa una cadencia menor (ABI cada 30 min, GLM 1/6), y la contingencia de octubre solo usa la banda 13 cada hora.
- El RRQPE tiene un techo de 100 mm/h y cortes de producción.
