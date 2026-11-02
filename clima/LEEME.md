# Clima Galápagos: datos medidos para analizar eventos y simular

Proyecto para **ir guardando las mediciones meteorológicas** de Galápagos y cruzarlas con lo que pasó en cada emergencia (por ejemplo, la inundación de La Cascada del 30/31-oct-2026). La meta es tener, con el tiempo, una serie propia y continua que sirva para calibrar modelos de lluvia y escorrentía (ver `../geodatos/estudios/la-cascada/`).

Por ahora tiene una fuente: la red de estaciones **IERSE-WSN** de la Universidad del Azuay. El diseño permite añadir otras (FCD, INAMHI, Open-Meteo, pluviómetros ciudadanos) como carpetas hermanas dentro de `datos/`.

## Actualizar

```bash
./actualizar.sh            # baja los días que faltan y regenera las tablas
```

- La descarga es incremental. Los días ya «cerrados» (más de 2 días de antigüedad) no se vuelven a pedir. Hoy y ayer se piden en cada corrida, porque las estaciones transmiten con retraso.
- Para rehacer un día: `python3 -I scripts/01_ierse_descargar.py --rehacer 2026-10-31`.
- El archivo continuo lo lleva ahora el servidor (ver «Plataforma en vivo»). Estos scripts sirven para análisis locales.

## Fuente: IERSE-WSN, red Galápagos

- **Responsable:** IERSE, Universidad del Azuay, con la Fundación Charles Darwin, la DPNG, el MAG y otros socios (logos del visor).
- **API:** pública y sin clave (la misma que usa su visor), con peticiones POST en JSON. El endpoint está en `privado/fuentes.env` (no versionado; ver `fuentes.env.ejemplo`):
  - `/networks`
  - `/sensors`
  - `/oper_nodes`
  - `/nodes_var_date`, que dice qué estaciones tienen datos de una variable en una fecha
  - `/node_data`, que da la serie de un día para una estación y una variable
- **Datos desde:** abril/mayo de 2026. No hay datos antes del 1-abr-2026; se comprobó el 2-nov-2026.
- **Frecuencia:** un registro cada ~5 minutos (288 al día si no hay cortes).
- **Variables con datos en Galápagos:**
  - lluvia (`RAIN`, mm por registro; el pluviómetro de balancín cuenta en pasos de 0,2 mm)
  - temperatura del aire (°C)
  - humedad relativa (%)
  - presión (el servidor la da en Pa; en las tablas consolidadas va en hPa)
- **Variables sin datos en Galápagos:** el servidor también ofrece UV, material particulado y ruido, pero en esta red vienen vacías.
- **Hora:** el servidor no documenta la zona horaria. El ciclo diario indica que es la **hora local de Galápagos (UTC−6)**: la temperatura sube a partir de las 06:00 y la marea barométrica semidiurna cae en las horas esperadas.
- **Licencia:** CC BY-NC-ND 4.0 (atribución, no comercial, **sin obras derivadas**). Cita obligatoria: Orellana-Samaniego, M.L., Cabrera-Lituma, A., Omar, D., Célleri, R., Bendix, J., y Ballari, D. 2023. Proyecto DARWIN. Versión 2023.1. IERSE, Universidad del Azuay. <http://opengeodata.uazuay.edu.ec/EstudioDarwin/>, fecha de acceso.
- **GSC-USFQ (cita que pide el GSC; no publica licencia):** Universidad San Francisco de Quito; Galapagos Science Center. (2026). Weather Data - GSC. Recuperado el <fecha> de https://weathergsc.usfq.edu.ec/

| Estación | ID | Lat | Lon | Altitud (DEM) |
|---|---|---|---|---|
| Cerro Crocker | n_glps01 | −0,6424 | −90,3260 | ≈ 861 m |
| Santa Rosa | n_glps09 | −0,6545 | −90,4035 | ≈ 416 m |
| Los Guayabillos | n_glps05 | −0,6991 | −90,3420 | ≈ 178 m |
| Militar | n_glps06 | −0,4900 | −90,2808 | ≈ 14 m |

La altitud sale del DEM Copernicus GLO-30 (`../geodatos`) y es aproximada. Las cuatro estaciones están en Santa Cruz. Ninguna está en Puerto Ayora: la más cercana a La Cascada es Los Guayabillos, en la parte media de la cuenca.

## Plataforma en vivo: sosgalapagos.org/clima

```
IERSE (Santa Cruz) ──► Mac en Galápagos: puente/puente_ierse.sh (launchd, cada 5 min) ──ssh──┐
GSC-USFQ (San Cristóbal) ──► servidor: sosgalapagos-clima.timer (cada 5 min) ────────────────┤
                                                                                             ▼
                        /var/lib/sosgalapagos-clima/clima.db (SQLite, horas en UTC)
                                 │ exportar()
                                 ▼
          /srv/sosgalapagos-clima/datos/{estado,horario,diario}.json ──► Caddy /clima/ (web/index.html)
```

- **Instalar o actualizar:** `./deploy/publicar.sh`. Con `--historico` carga además los crudos de IERSE y el histórico diario del GSC.
- **El servidor (EE. UU.) no alcanza a IERSE:** la conexión se agota, probablemente por un bloqueo geográfico. Por eso IERSE entra por el **puente** desde una máquina en Ecuador. La llave `~/.ssh/id_clima_puente` solo puede ejecutar `recibir.sh` en el servidor (`command=…,restrict`).
  - Se instala con `puente/org.sosgalapagos.clima-puente.plist.ejemplo` en `~/Library/LaunchAgents/`.
  - **Si la Mac duerme o se apaga, IERSE deja de actualizarse.** Al volver, recupera hasta 3 días.
  - Lo ideal es pasarlo a una máquina siempre encendida en Ecuador.
- **Qué es público:** solo la página y los tres JSON agregados. Caddy da 404 a todo lo demás y la página lleva `noindex`. No hay descargas ni enlaces a las fuentes, y solo se nombra «IERSE-WSN» y «GSC-USFQ», porque algunas fuentes aún no son públicas. Los CSV mensuales completos van a `/var/lib/sosgalapagos-clima/privado/csv` (`sosgalapagos-clima-csv.timer`, cada hora). La base se respalda a diario en `respaldos/`.
- **Horas:**
  - IERSE marca la hora de Galápagos (UTC−6).
  - **GSC marca la hora continental (UTC−5), aunque diga «Z» o «UTC−6»**. Se verificó con la hora actual y con el ciclo de la radiación solar.
  - El INAMHI también usa UTC−5.
  - En la base, todo está en UTC.
- **Eventos de referencia** para comparar en el dashboard: lista `EVENTOS` en `recolector/recolector.py`.

## Fuentes en el dashboard (cada 5 min)

| Fuente | Estaciones | Cómo llega |
|---|---|---|
| IERSE-WSN | Santa Cruz: Cerro Crocker, Santa Rosa, Los Guayabillos, Militar | puente desde la Mac |
| GSC-USFQ | San Cristóbal: El Junco, Cerro Alto, El Mirador, Merceditas (más la del GSC, sin datos desde ago-2026) | servidor (websocket) |
| INAMHI | Puerto Ayora M0191 (a 1,4 km de La Cascada), Puerto Baquerizo M0221 | servidor; serie de 5 min y respaldo horario |
| IOC | mareógrafos de Puerto Ayora y Baltra (nivel del mar) | servidor |
| METAR | aeropuertos de Baltra y San Cristóbal (tiempo presente, temperatura, presión, viento) | servidor |
| WeatherLink | estación particular en Puerto Ayora (Davis Vantage Vue), pública en el mapa de WeatherLink; se muestra sin nombre ni ubicación exacta hasta tener el consentimiento del propietario | servidor; da la lluvia acumulada del día y el intervalo se calcula por diferencia |

- **Nivel preliminar de inundación:** `recolector/inundacion.py` y `umbrales_inundacion.json`. Detalle en `docs/umbrales-la-cascada.md`.
- **Estacionalidad:** `recolector/estacionalidad.py`. Usa las series diarias de la FCD (`datos/fcd/`, privadas; en el servidor, `/var/lib/sosgalapagos-clima/fcd`), el histórico diario del GSC y los días completos que va juntando el recolector. Calcula el rango mensual habitual, un compuesto de años El Niño, la probabilidad semanal y periodos de retorno con Gumbel.
- **Enlace oculto para investigadores:** los CSV completos y un LEEME se regeneran cada hora en `/srv/sosgalapagos-privado/sitios/clima-<token>/`, que se sirve en `/datos-clima/<token>/`.
  - El token solo está en el servidor (`/srv/sosgalapagos-privado/caddy/clima-investigadores.caddy` y el drop-in `sosgalapagos-clima-csv.service.d/investigadores.conf`) y en `privado/token_investigadores.txt`.
  - Para revocarlo: borrar el archivo `.caddy` y recargar Caddy.

## Otras fuentes

Inventario verificado, con endpoints, en `privado/fuentes.md` (no versionado). Lo más útil:
- **INAMHI M0191, en Puerto Ayora a 1,4 km de La Cascada:** lluvia cada 5 min. Su historial horario solo guarda **90 días**. El del 16-oct al 2-nov ya está archivado en `datos/inamhi/historial/`. Midió 93,6 mm el 30-oct y 135,4 mm el 31-oct (días en UTC−5).
- **Mareógrafos IOC:** Puerto Ayora y Baltra.
- **METAR:** Baltra y San Cristóbal.


## Repositorio

- Los endpoints y el inventario de fuentes viven en `privado/` (en `.gitignore`). En el código y la documentación versionados las fuentes solo se nombran.
- Para correr los scripts: copiar `fuentes.env.ejemplo` a `privado/fuentes.env` y completarlo.

## Estructura

```
clima/
├── actualizar.sh
├── scripts/
│   ├── 01_ierse_descargar.py   descarga incremental (solo biblioteca estándar)
│   ├── 02_ierse_consolidar.py  tablas 5 min / horaria / diaria y estaciones.geojson (pandas)
│   └── 03_evento.py            recorte de una ventana, hietograma, cortes y comparación con ECMWF
├── datos/ierse-wsn/
│   ├── crudos/AAAA-MM/AAAA-MM-DD.csv.gz   tal cual los da el servidor (formato largo)
│   ├── estado.json             qué días se bajaron, cuándo y cuántos registros por estación/variable
│   ├── estaciones.json         metadatos del servidor
│   ├── estaciones.geojson      estaciones con altitud y rango de fechas
│   ├── serie_5min.csv.gz       una fila por registro, variables en columnas
│   ├── horario.csv             lluvia (suma), temperatura (media/mín/máx), humedad, presión
│   └── diario.csv              ídem por día + lluvia máx. en 1 h + cobertura_pct
└── eventos/
    └── 2026-10-30_inundacion/  cruce con la inundación de La Cascada
```

## Cuidado al usar los datos

- **Cortes de transmisión:** cuando una estación deja de transmitir, la lluvia de ese tramo **no se mide**. No queda en cero ni se acumula para después. Por eso los totales de los días con cortes son **mínimos**. Hay que mirar siempre `cobertura_pct` en `diario.csv` o `cortes_transmision.csv` en los eventos.
- Los pluviómetros de balancín subestiman la lluvia muy intensa (más de 50 mm/h).
- En la parte alta, la humedad marca 100 % casi siempre por la garúa. No es un error.
- Los crudos no se corrigen. Cualquier filtro de calidad se hace en los scripts de consolidación o de análisis.
