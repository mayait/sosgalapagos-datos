# Tormentas sintéticas: qué marcan los pluviómetros cuando algo se inunda abajo

> **Modelo propio, no dato oficial.** Todo lo que hay aquí sale de tormentas inventadas, aunque plausibles, pasadas por el modelo 2D de SOS Galápagos sobre un DSM de 30 m. Sirve para comparar reglas de alerta y decidir dónde poner pluviómetros. No sirve para delimitar zonas ni como alerta oficial.

Issues: #26 (modelo 2D) y #30 (alerta por lluvia). Idea tomada de los gemelos digitales de crecidas: por ejemplo, PGTEC (UPV, 2026) con TETIS e HIDRIS mueve y agranda tormentas para ver qué pasaría. Aquí se hace con herramientas propias y abiertas.

## Qué se hizo

1. **500 tormentas por isla** (`scripts/32_tormentas_sinteticas.py`), reproducibles con semilla:
   - **forma en el espacio:**
     - 55 %: núcleo convectivo gaussiano (radio 1,5–6 km), que puede desplazarse a 0–14 km/h; el 65 % de ellos se centra en la parte alta;
     - 25 %: orográfica (llueve más cuanto más alto);
     - 20 %: uniforme;
   - **duración:** 1–24 h, con el pico entre el 20 y el 80 % de la tormenta;
   - **lámina máxima en el núcleo:** hasta 90·d^0,42 mm (d en horas): 90 mm en 1 h, 141 mm en 3 h, 340 mm en 24 h. El 30-oct-2026 midió 61–66 mm/h, 117–131 mm en 3 h y 179–238 mm en el día;
   - **inciertos y muestreados:**
     - humedad antecedente P5d: 0–100 mm;
     - pérdida constante del suelo F: 15–35 mm/h en Santa Cruz, a partir del barrido F10–F35 del script 24; 5–35 mm/h en San Cristóbal, donde no está calibrada.
2. **Motor 2D**:
   - es el mismo esquema inercial de los scripts 24 y 25, en una sola función numba;
   - **valida igual que los originales** (`datos/*/validacion_motor.json`):

     | Comparación | Motor nuevo | Original |
     |---|---|---|
     | Santa Cruz, La Cascada: calado máximo | 1,85 m | 1,84 m |
     | Santa Cruz, La Cascada: llegada de 0,1 m | 20:55 | 20:53 |
     | Santa Cruz, La Cascada: hora del máximo | 22:25 | 22:24 |
     | San Cristóbal, puntos del script 25 | iguales al centímetro | — |

   - tarda **9 s por tormenta en Santa Cruz y 3 s en San Cristóbal**: con 9 procesos, el lote entero sale en ≈12 + 6 min.
3. **Lo que marca cada pluviómetro**: la lluvia del campo sintético en su posición, sin error de medida. Se usan las estaciones de `clima/` (IERSE-WSN, INAMHI, WeatherLink, Tempest, USFQ-GSC).
4. **Inundación**: calado ≥ 0,3 m en la celda de 30 m del punto clave. Un aviso es «a tiempo» si la regla salta al menos 15 min antes.

## Resultados

### La regla de hoy (v0.2) con 500 tormentas

Nivel «alto» = 30 mm en 1 h, 60 mm en 3 h o 100 mm en 24 h, en el máximo ponderado de las estaciones de la zona.

| Zona | Tormentas que inundan | Inundaciones avisadas a tiempo | Tormentas sin inundación que igual dan «alto» | Aviso típico |
|---|---|---|---|---|
| La Cascada | 141 | **98 %** | 37 % | **2 h** |
| Tomás de Berlanga | 50 | 100 % | 49 % | 70 min |
| Bellavista | 127 | 95 % | 47 % | 50 min |
| Barrio Frío (desembocadura), San Cristóbal | 153 | 87 % | 49 % | **25 min** |
| El Manzanillo | 74 | 96 % | 59 % | 50 min |
| El Progreso | 68 | 93 % | 59 % | 30 min |

El porcentaje de falsas alarmas es el del conjunto sintético, que tiene muchas tormentas fuertes a propósito. **No es la frecuencia de falsas alarmas en un año.**

### No conviene subir los umbrales de «alto» todavía

El modelo «preferiría» umbrales más altos (`datos/*/umbrales_propuestos.json`). En La Cascada serían 52,5 / 75 / 190 mm: detectan el 92 % con un 10 % de falsas alarmas. Pero con la lluvia medida el 30-oct pasa esto (`figuras/compromiso_santa-cruz_la_cascada.png`):

| Umbrales de «alto» | Hora del aviso el 30-oct |
|---|---|
| v0.2: 30 / 60 / 100 mm | **15:50** |
| ×1,1: 33 / 66 / 110 mm | 19:00 |
| ×1,35: 40 / 81 / 135 mm | 20:30 |

**La v0.2 está justo en el borde:** un 10 % más arriba y el único evento real se avisa tres horas más tarde. El modelo pone la llegada del agua al centro del barrio a las 20:55. El modelo agregado del informe de La Cascada llena el vaso entre las 16:51 y las 19:37. **No sabemos a qué hora entró el agua de verdad.** Por eso los umbrales propuestos quedan como referencia y **no se cambian en `clima/recolector/umbrales_inundacion.json`**.

### Qué pluviómetro avisa mejor (AUC de la lluvia en 3 h antes de la llegada; 0,5 = nada, 1 = perfecto)

- **La Cascada:**
  - estaciones actuales:

    | Estación | AUC |
    |---|---|
    | Los Guayabillos | 0,94 |
    | INAMHI Puerto Ayora | 0,93 |
    | Erna | 0,92 |
    | Punta Estrada | 0,92 |
    | Cerro Crocker | 0,90 |
    | Santa Rosa | 0,88 |

  - mejor sitio nuevo: −90,3112 / −0,7015, a ≈157 m, en la cuenca media; AUC 0,96;
  - con la regla v0.2, un pluviómetro ahí sube la detección de «alto» del 98 al 100 %;
  - añadir Cerro Crocker también llega al 100 %, pero con más falsas alarmas (48 %).
- **Bellavista:** ninguna estación pasa de 0,78. Se inunda con chubascos locales que la red no ve.
- **San Cristóbal:**
  - las estaciones del GSC en la parte alta (El Junco, Cerro Alto, El Mirador) anticipan **peor** (0,61–0,64) que el INAMHI de la costa (0,79) lo que pasa en Barrio Frío;
  - **El Progreso no lo anticipa ningún pluviómetro** (≤ 0,65): se encharca en depresiones con la lluvia local, dentro de la hora. Ahí sirve más un sensor de nivel que una alerta por lluvia;
  - La Planada (registro 2025) no se inunda en el modelo con ninguna tormenta. Probablemente es un problema de drenaje urbano, que el modelo no representa.

## Lo que falta (y la tarea de los registros históricos)

- **Validar con inundaciones reales.** De cada evento hace falta:
  - fecha y **hora** en que llegó el agua;
  - lugar (coordenadas o calle);
  - profundidad (foto con referencia: puerta, muro, auto);
  - cuánto duró.

  Con eso se contrasta la regla v0.2, se calibra la pérdida F y se corrigen las horas de llegada del modelo. Antes de abril de 2026 solo hay lluvia diaria (FCD desde 1965, GSC desde 2015): esos eventos solo prueban la ventana de 24 h. Issue **#80**.
- **Períodos de retorno (#26)**: requieren curvas IDF (#24). La frecuencia de los mapas es la del conjunto sintético, no una probabilidad anual. Plan:
  1. curvas IDF provisionales de Santa Cruz: la lluvia de 24 h sale de los máximos anuales de la FCD (script 29) y la fracción de 1 y 3 h, de la lluvia de 5–15 min de 2026 y de GPM IMERG (#20);
  2. un periodo de retorno para cada tormenta sintética y mapas «se inunda con la lluvia de T años»;
  3. contraste con las fuentes externas: el estudio de intensidades del INAMHI de 2015 (#77), las series diarias de San Cristóbal (#78) y la tesis USFQ de las encañadas (#79).
- **Sensores:**
  - pluviómetro nuevo en la cuenca media de La Cascada (#19);
  - sensor de nivel en El Progreso (#81).
- **Límites del modelo:**
  - el DSM incluye techos y árboles: los «hoyos» sueltos se llenan aunque en la realidad drenen;
  - no hay red pluvial ni alcantarillas;
  - los pluviómetros sintéticos no tienen error ni cortes.

## Archivos

| Archivo | Qué es |
|---|---|
| `datos/<isla>/catalogo_tormentas.csv` | Parámetros de cada tormenta |
| `datos/<isla>/resultados_tormentas.csv` | Lluvia en cada estación (1, 3, 6 y 24 h) y calado y llegada en cada zona |
| `datos/<isla>/previo_llegada_<zona>.csv` | Lluvia de la zona hasta 15 min antes de que llegue el agua |
| `datos/<isla>/resumen.json` | Regla v0.2, óptimo del modelo, AUC por estación y factor de suelo húmedo |
| `datos/<isla>/compromiso_<zona>.csv` | Detección, falsas alarmas y aviso al escalar «alto», y hora del 30-oct |
| `datos/<isla>/mejor_sitio_pluviometro.json` · `datos/escenarios_red.json` | Mejor sitio nuevo y efecto de añadir estaciones |
| `datos/<isla>/validacion_motor.json` | Motor nuevo frente a los scripts 24 y 25 |
| `figuras/` | Generador, frecuencia, umbrales, compromiso, pluviómetros, comparación de reglas y animaciones (MP4 y GIF) |
| `cache/` (no versionado) | Corridas individuales y pila de rasters |

Rehacer todo: `scripts/flujo.py --solo tormentas_sinteticas` y `--solo tormentas_figuras`, o los comandos de `flujo.toml`.
