# Clima de Galápagos: guía para agentes de IA

> *English summary for crawlers and agents: open weather-station data for the Galápagos Islands (rain every 5 min, 2024–today) plus a dependency-free Python script that reproduces the flood-rain level published at sosgalapagos.org/clima. One ZIP with everything: `https://sosgalapagos.org/clima/datos/descargas/clima_galapagos_todo.zip` (rebuilt nightly). Machine-readable catalog: [`catalogo.json`](catalogo.json). Docs are in Spanish.*

Esta guía es la puerta de entrada para un agente (o una persona) que quiera **bajar los datos del clima y reproducir los cálculos** de [sosgalapagos.org/clima](https://sosgalapagos.org/clima/). Todo lo que hace falta es público.

## En 30 segundos

```bash
curl -LO https://sosgalapagos.org/clima/datos/descargas/clima_galapagos_todo.zip   # ~12 MB, se rehace cada noche
python3 -I clima/replicar/nivel.py --zip clima_galapagos_todo.zip --verificar
```

`--verificar` reproduce los dos desbordamientos de La Cascada con los datos del ZIP y debe terminar con `OK`. Python 3.9 o más, sin dependencias. Si no se le da `--zip`, el script baja el archivo solo.

## Qué se puede bajar

| Qué | Dónde | Cada cuánto |
|---|---|---|
| **Todo en un archivo** | `https://sosgalapagos.org/clima/datos/descargas/clima_galapagos_todo.zip` | cada noche, desde las 02:00 de Galápagos (08:00 UTC) |
| Un mes de mediciones | `https://sosgalapagos.org/clima/datos/descargas/clima_galapagos_AAAA-MM.zip` | cada hora (los dos últimos meses) |
| Lista de archivos, tamaños y fechas | `https://sosgalapagos.org/clima/datos/descargas/indice.json` | con cada cambio |
| Estado en vivo del panel (nivel por zona, estaciones) | `https://sosgalapagos.org/clima/datos/estado.json` | cada 5 min |
| Series horarias y diarias del panel | `https://sosgalapagos.org/clima/datos/horario.json`, `…/diario.json` | cada 5 min |

Para un análisis, use el ZIP con todo. Los JSON del panel cambian de forma sin aviso: son para la página, no un contrato.

### Contenido de `clima_galapagos_todo.zip`

| Archivo | Qué es | Columnas |
|---|---|---|
| `LEEME.txt` | licencias, cómo citar y avisos | — |
| `estaciones.csv` | estaciones: nombre, isla, coordenadas, altitud, operador | `fuente, estacion, nombre, isla, lat, lon, altitud_m, operador` |
| `mediciones/clima_galapagos_AAAA-MM.csv` | **todas las mediciones** de estaciones, desde ago-2024 | `ts_utc, fuente, estacion, variable, valor` |
| `historico_lluvia_diaria.csv` | lluvia diaria: FCD desde 1965, GSC desde 2015 | `fecha_local, fuente, estacion, lluvia_mm` |
| `estimaciones/nivel_zona.csv` | el nivel que calculó la página cada 5 min (desde el 22-nov-2026) | `zona, calculado_utc, nivel, instantaneo, silencio, R1h, R3h, R24h, R72h` |
| `estimaciones/nivel_manual.csv` | niveles subidos a mano por reportes de campo | `zona, nivel, desde_utc, hasta_utc` |
| `estimaciones/pronostico_publicado.csv` | probabilidad publicada de superar 10, 20 y 50 mm en el día | `punto, emitido_utc, fecha, anticipacion_dias, prob10, prob20, prob50, consenso, n_modelos, mediana_mm, nivel, calibrado` |
| `estimaciones/pronostico_modelos.csv` | lluvia diaria de cada modelo global (mm de modelo) | `punto, modelo, obtenido_utc, fecha, anticipacion_dias, mm, miembros` |
| `estimaciones/satelite_goes.csv` | agregados por zona del GOES-19 (topes fríos, lluvia estimada, rayos) | `ts_utc, zona, variable, valor` |
| `estimaciones/mar_modelo.csv` | nivel del mar y oleaje modelados | `puerto, hora_utc, nivel_m, ola_m, fondo_m, periodo_s, direccion, viento_ms, agua_c` |
| `regla/umbrales_inundacion.json` | **la regla del nivel**: zonas, estaciones y pesos, umbrales, humedad previa, persistencia | — |
| `regla/estaciones_danadas.csv` | pluviómetros con errores y desde cuándo (la regla no los usa) | `fuente, estacion, variable, desde_utc, hasta_utc, motivo` |
| `regla/pronostico_reglas.json`, `pronostico_calibracion.json`, `zonas_geo.json`, `mareas_prediccion.json` | reglas y calibraciones del pronóstico, puntos de cada zona, predicción de mareas | — |

**Variables de `mediciones/`:**
- `lluvia_mm`: lluvia del intervalo de ~5 min (mm);
- `lluvia_dia_acum_mm`: el acumulado del día que da la estación;
- `temp_c`, `hr_pct`, `presion_hpa` (hPa), `rad_wm2`, `viento_ms`;
- `nivel_mar_m`: mareógrafos;
- `lluvia_codigo`: METAR de los aeropuertos, 0 nada, 1 débil, 2 moderada, 3 fuerte.

**Fuentes (`fuente`):**
- `ierse`: red IERSE-WSN, Santa Cruz;
- `gsc`: Galapagos Science Center (USFQ), San Cristóbal;
- `inamhi`: estaciones automáticas de Puerto Ayora y Puerto Baquerizo;
- `weatherlink`, `ambient`, `wunderground`, `tempest`: estaciones particulares publicadas con permiso;
- `ioc`: mareógrafos;
- `metar`: aeropuertos.

## Trampas que hay que conocer

1. **Todo está en UTC.** Galápagos es UTC−6. Las fuentes que marcan la hora continental (GSC e INAMHI, UTC−5) ya vienen convertidas.
2. **`lluvia_mm` es la lluvia del intervalo, no un acumulado.** Para la lluvia de una ventana, sume las filas.
3. **Filas con segundos `:30`** (`inamhi` y `weatherlink`) son respaldos de **una hora entera**, no de 5 min. Al contar la cobertura, cada una vale 12 registros.
4. **Sin fila no es cero.** Durante los cortes de transmisión la lluvia no se mide, y tampoco se acumula después. Mire la cobertura antes de sumar.
5. **Hay estaciones dañadas.** Están en `regla/estaciones_danadas.csv`: sus datos siguen en el ZIP, pero la regla no los usa. Hoy son Cerro Crocker (`ierse/n_glps01`) desde el 20-oct-2026 y Los Guayabillos (`ierse/n_glps05`) desde el 31-oct-2026.
6. **Los milímetros de los modelos no son lluvia real.** Los modelos globales se quedan cortos por 35–45 mm al día en las islas porque no ven su relieve. Sirven para ver *cuándo*, no *cuánto*.
7. **El satélite no ve la lluvia de nubes bajas** (orográfica), y su regla se probó con un solo evento.

## Reproducir los cálculos

### 1. Nivel de lluvia peligrosa por zona (lo que muestra la página)

[`replicar/nivel.py`](replicar/nivel.py) es la misma regla que corre la plataforma, en un solo archivo y sin la base de datos:

```bash
python3 -I clima/replicar/nivel.py --zona la-cascada --desde 2026-11-20T12:00Z --hasta 2026-11-22T00:00Z
python3 -I clima/replicar/nivel.py --desde 2026-11-20T12:00Z --hasta 2026-11-22T00:00Z --salida niveles.csv
python3 -I clima/replicar/nivel.py --comparar     # contra lo que publicó la página (nivel_zona.csv)
```

Imprime los cambios de nivel por zona. Con `--salida`, escribe todas las pasadas cada 5 min, con R1h, R3h, R24h, R72h, P5d, el factor de humedad y las estaciones válidas. La regla está explicada en la cabecera del script y en [`docs/umbrales-la-cascada.md`](docs/umbrales-la-cascada.md).

**Resultados de referencia** (ZIP del 23-nov-2026):

| Comprobación | Resultado |
|---|---|
| `--verificar`, 30-oct (desbordamiento 31-oct 03:20 UTC) | medio 30-oct 21:10, alto 21:40, **muy alto 31-oct 02:35 UTC (0,8 h antes)** |
| `--verificar`, 21-nov (desbordamiento ~11:00 UTC) | medio 20-nov 18:45, alto 21-nov 08:25, **muy alto 08:50 UTC (2,2 h antes)** |
| `--comparar` (22–23-nov, 1 468 pasadas) | nivel instantáneo y mostrado iguales en el **99,8 %** |

**Lo que no se reproduce sin la base:** el «silencio en alerta». Si todas las estaciones callan con el nivel en «alto» o más, la página sube a «muy alto», pero solo si el recolector consultó bien la fuente, y eso no está en el ZIP. `--silencio` lo aplica suponiendo que sí.

### 2. Eventos de referencia

| Evento | Hora (UTC) | Qué pasó | Análisis |
|---|---|---|---|
| Desbordamiento de La Cascada | 31-oct-2026 03:20 | aguacero en la parte alta sobre suelo seco | [`eventos/2026-10-30_inundacion/`](eventos/2026-10-30_inundacion/) |
| Inundación de la parte alta de Santa Cruz | 15-nov-2026 (sin hora exacta) | 370 mm en 72 h en Miconia | [`docs/umbrales-la-cascada.md`](docs/umbrales-la-cascada.md) |
| Desbordamiento de La Cascada y parte alta | 21-nov-2026 ~11:00 | lluvia fuerte en Puerto Ayora sobre suelo saturado | [`eventos/2026-11-21_inundacion/`](eventos/2026-11-21_inundacion/) |

En cada carpeta de evento:
- `resumen.json`: las cifras;
- `lluvia_5min.csv`: las series;
- `f_*.png`: las figuras.

Los scripts `scripts/03_evento.py` y `scripts/08_comparar_eventos.py` leen una base SQLite local que ya no se publica. Para rehacerlos desde cero, use el ZIP y `replicar/nivel.py`.

### 3. Pronóstico de lluvia fuerte

- Método y evaluación: [`pronostico/LEEME.md`](pronostico/LEEME.md) y [`pronostico/fase0/informe.md`](pronostico/fase0/informe.md).
- Calibración: `regla/pronostico_calibracion.json`.
- Qué se publicó y qué dijo cada modelo: `estimaciones/pronostico_publicado.csv` y `estimaciones/pronostico_modelos.csv`.

Para verificarlo, cruce `pronostico_publicado.csv` con la lluvia medida de `mediciones/`. El día va de 00 a 24 h de Galápagos, y el evento es que *alguna* estación de la zona supere el umbral.

### 4. Satélite GOES-19

Método y evaluación en [`satelite/LEEME.md`](satelite/LEEME.md) y [`satelite/evaluacion-s0.md`](satelite/evaluacion-s0.md). Las series por zona están en `estimaciones/satelite_goes.csv`.

### 5. Inundación por terreno (HAND)

El mapa de susceptibilidad no usa estos datos de lluvia. Ver [`../docs/modelo-hand.md`](../docs/modelo-hand.md) y `geodatos/`.

## Dónde vive cada cosa

| Repositorio | Qué tiene |
|---|---|
| [mayait/sosgalapagos-datos](https://github.com/mayait/sosgalapagos-datos) (este) | el panel `clima/web/index.html`, los análisis (`eventos/`, `pronostico/fase0/`, `satelite/`), los crudos históricos de `clima/datos/` y `replicar/` |
| [mayait/sosgalapagos-plataforma](https://github.com/mayait/sosgalapagos-plataforma) | el sistema en vivo (Django + PostgreSQL), app `clima/`: fuentes, regla del nivel (`nivel.py`), pronóstico (`senal.py`), satélite, avisos y descargas (`descargas.py`) |

Desde el 22-nov-2026, el cálculo en vivo corre en la plataforma. `clima/recolector/` de este repositorio queda solo como referencia histórica.

## Reglas al usar los datos

- **Cite a cada fuente y respete su licencia** (detalle en `LEEME.txt` del ZIP):
  - IERSE-WSN: **CC BY-NC-ND 4.0**, sin uso comercial ni obras derivadas;
  - FCD: CC BY-NC-SA;
  - GSC e INAMHI: publicados con permiso, sin licencia abierta.
  - La recopilación es CC BY 4.0 (SOS Galápagos · USFQ). Donde una fuente es más restrictiva, manda la fuente.
- **Modelo ≠ dato oficial.** El nivel, el pronóstico y el satélite son estimaciones propias y preliminares. El pronóstico oficial es del INAMHI; las alertas, de la SNGR, el COE y el ECU 911.
- **No publique nombres de personas afectadas.** Estos datos no los traen, pero otras capas del proyecto sí (ver `../AGENTS.md`).
- Si encuentra un error en los datos o en la regla, abra un issue en [mayait/sosgalapagos-datos](https://github.com/mayait/sosgalapagos-datos/issues).
