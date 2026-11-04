# Satélite GOES-19 (ABI + GLM): vigilancia de las horas previas

Otra fuente de vigilancia del dashboard de clima. Ningún modelo de pronóstico anticipó con 24 h la inundación de La Cascada (30-oct-2026). Lo útil es mirar las horas previas, y GOES-19 (GOES-East, 75,2° O) ve Galápagos en disco completo cada 10 min:

- **ABI banda 13** (10,3 µm): temperatura del tope de nube. Un tope por debajo de 221 K (−52 °C) indica convección profunda.
- **ABI RRQPE**: tasa de lluvia **estimada** por la NOAA a partir del infrarrojo (mm/h, ~2 km).
- **GLM**: rayos detectados desde el espacio, en archivos de 20 s.

> ⚠️ Todo lo de aquí es una **estimación satelital**: no es lluvia medida ni una alerta oficial. La señal satelital **no cambia** el nivel de inundación (`recolector/inundacion.py`), que se calcula solo con la lluvia medida. La lluvia de nubes bajas y la garúa casi no se ven desde el satélite.

Evaluación con los eventos de octubre de 2026 y una muestra de días: [`evaluacion-s0.md`](evaluacion-s0.md) (cifras en `resumen.json`).

## Fuente y acceso

- Archivo abierto de la NOAA en AWS (NOAA Open Data Dissemination), sin clave. La raíz del bucket va en `CLIMA_GOES_S3` (`privado/fuentes.env`; ver `../fuentes.env.ejemplo`). En el repositorio solo se nombra la fuente.
- Productos: `ABI-L2-CMIPF` (banda 13), `ABI-L2-RRQPEF` y `GLM-L2-LCFA`.
- **No se guardan netCDF completos.** `goes.py` lee por rangos HTTP con h5py solo los trozos del recorte:

| Producto | Archivo completo | Lo que se baja | Frecuencia |
|---|---|---|---|
| Banda 13 (CMIP, disco completo) | ~24 MB | ~1,3 MB (recorte de Galápagos) | 10 min |
| RRQPE | ~1,4 MB | ~0,5 MB | 10 min |
| GLM | ~320 KB cada 20 s | colector: completo (~10 MB cada 10 min, en hilos); S0: ~55 KB por rangos | 20 s |

- **Latencia medida** (nov-2026): cada barrido ABI llega al bucket **~10 min después de empezar** (el disco completo tarda ~10 min). Con el timer cada 5 min, el dato tiene 10–15 min de antigüedad en el panel. El GLM llega en menos de 1 min.
- **Riesgo operativo: cortes de la NOAA.** La producción de RRQPE se detuvo el 2-nov-2026 a las 16:50 UTC (también en GOES-18) y seguía detenida el 4-nov. El colector sigue con la banda 13 y el GLM, y el panel avisa que la lluvia estimada no se está produciendo.
- **Hora:** UTC en todos los archivos. El panel muestra la hora de Galápagos (UTC−6).
- **Paralaje:** un tope de 15 km se ve unos 4–5 km al oeste de su posición real desde 75° O. Por eso las señales se miran también en la zona ampliada 25 km.
- Licencia: datos de la NOAA, dominio público. Citar «NOAA GOES-19, archivo abierto en AWS».

## Archivos

| Archivo | Qué hace |
|---|---|
| `goes.py` | Listado del bucket, lectura por rangos, proyección geoestacionaria (lat/lon ↔ píxel) |
| `colector.py` | Colector en tiempo real (timer cada 5 min): agregados por zona en `clima.db` y `satelite.json` |
| `vigilancia.py` | «Señal satelital» por zona (biblioteca estándar; la puede importar `inundacion.py`) |
| `s0_extraer.py` | Fase S0: recortes de los eventos y de la muestra en `cache/` (no versionada) |
| `s0_evaluar.py` | Fase S0: adelantos, RRQPE frente a pluviómetros y falsas alarmas → `resumen.json` y `figuras/` |
| `evaluacion-s0.md` | Informe de la evaluación y propuesta para `inundacion.py` |

Zonas: `../recolector/zonas_geo.json` (bbox por zona; los ids son los de `umbrales_inundacion.json`). El colector también calcula cada variable en la zona ampliada 25 km (`*_25km`).

## Variables en `clima.db` (tabla `obs`, `fuente='goes'`)

`estacion` es el id de la zona. `ts` en UTC: inicio del barrido en el ABI, inicio del intervalo de 10 min en el GLM.

| Variable | Qué es |
|---|---|
| `tb_min_k` | Temperatura de brillo mínima de la banda 13 en la zona (K) |
| `frio_pct`, `frio_pct_25km` | % de píxeles con Tb < 221 K en la zona y en la zona ampliada 25 km |
| `lluvia_sat_max_mmh`, `lluvia_sat_media_mmh` | RRQPE máxima y media en la zona (mm/h) |
| `lluvia_sat_max_mmh_25km` | RRQPE máxima en la zona ampliada 25 km |
| `rayos_n`, `rayos_n_25km` | Destellos GLM en los 10 min que empiezan en `ts` |
| `glm_archivos` (`estacion='galapagos'`) | Archivos GLM leídos en el intervalo (30 = completo) |

Son ~150 filas por hora para las cuatro zonas. No se escribe en la tabla `corridas`: el estado de cada corrida va en `satelite.json` (`corrida`), para no mezclar el satélite con las estaciones en el panel de fuentes.

## `satelite.json` (público)

Lo escribe `colector.py` en `CLIMA_SALIDA` (está en `PUBLICOS` de `recolector.py`). Pesa 10–40 KB. **Caddy solo sirve `estado.json`, `horario.json` y `diario.json`** (Caddyfile del repo mayait/sosgalapagos), así que `recolector.exportar()` lo copia en la clave `satelite` de `estado.json`, y de ahí lo lee el panel. Llega con hasta 5 min de retraso adicional, porque el recolector exporta en `*:0/5` y el colector escribe en `*:2/5`. Si algún día Caddy deja pasar `/datos/satelite.json`, el panel puede leerlo directamente.

- `zonas.<id>.series`: las variables de arriba en las últimas 3 h (`[ts, valor]`).
- `zonas.<id>.vigilancia`: `{estado: "sin señal" | "vigilancia" | "sin datos", motivos: [...]}`.
- `rayos`: `[lat, lon, minutos desde el destello]` de las últimas 3 h en una caja amplia (para ver lo que se acerca).
- `nucleos`: celdas de 0,05° con Tb < 235 K en la última imagen (`[lat, lon, Tb mín.]`).
- `lluvia_sat`: celdas de 0,05° con RRQPE ≥ 1 mm/h en la última imagen.
- `ultima_imagen`, `glm_ultimo_intervalo`, `corrida`: horas y estado.

## Correr en local

```bash
cd clima
uv venv .venv --python 3.12 && uv pip install -p .venv -r requirements.txt -r satelite/requirements.txt
# tiempo real, con base y salida de prueba
CLIMA_DB=/tmp/sat/clima.db CLIMA_SALIDA=/tmp/sat/salida CLIMA_SATELITE_DIR=/tmp/sat/estado \
  .venv/bin/python -I satelite/colector.py --horas 1
# repetir un momento del evento (pico del 30-oct, 20:30 hora de Galápagos)
CLIMA_DB=/tmp/rep/clima.db CLIMA_SALIDA=/tmp/rep/salida CLIMA_SATELITE_DIR=/tmp/rep/estado \
  .venv/bin/python -I satelite/colector.py --ahora 2026-10-31T02:30:00Z --horas 1
```

Fase S0 (tarda horas con un enlace de ~1 MB/s; es reanudable):

```bash
.venv/bin/python -I satelite/s0_extraer.py --eventos
.venv/bin/python -I satelite/s0_extraer.py --abi-cada 30 --glm-cada 6 --dias 2026-05-07 ...   # ver MUESTRA en s0_evaluar.py
ssh root@152.44.45.89 "sqlite3 -readonly -csv -header /var/lib/sosgalapagos-clima/clima.db \
  \"SELECT fuente, estacion, ts, valor FROM obs WHERE variable='lluvia_mm' AND fuente IN ('ierse','inamhi','tempest')\"" \
  | gzip > /tmp/lluvia.csv.gz
.venv/bin/python -I satelite/s0_evaluar.py --obs /tmp/lluvia.csv.gz
```

## Servidor

`deploy/sosgalapagos-clima-satelite.service` y `.timer` (cada 5 min, en `*:2/5`, 2 min después del recolector). Código en `/opt/sosgalapagos-clima/satelite/`, venv propio en `/opt/sosgalapagos-clima/.venv-satelite` (numpy y h5py), estado en `/var/lib/sosgalapagos-clima/satelite/`. Lo instala `deploy/publicar.sh`. En el servidor cada corrida baja ~12 MB.
