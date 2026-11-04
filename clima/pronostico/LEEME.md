# Pronóstico de lluvia (experimental, no oficial)

Señal diaria de lluvia fuerte para los próximos 7 días por zona, publicada en `sosgalapagos.org/clima`. Sale de modelos meteorológicos globales y está calibrada con la lluvia medida en las islas. **No es un pronóstico oficial ni una alerta.** El pronóstico oficial es del INAMHI, y las alertas, de la SNGR, el COE y el ECU 911.

La evaluación que justifica cada decisión está en [`fase0/informe.md`](fase0/informe.md).

## Cómo funciona

```
Open-Meteo (deterministas: ECMWF IFS y AIFS, GFS, ICON, UKMO, ARPEGE, GEM; conjuntos: IFS ENS, AIFS ENS,
            GEFS, ICON-EPS, MOGREPS-G)
   │  recolector/pronostico.py · fuente_pronostico(), una vez por hora dentro del recolector
   ▼
/var/lib/sosgalapagos-clima/pronostico/
   ├── archivo/AAAA-MM/*.json.gz   respuestas crudas (para verificar y recalibrar)
   ├── ultimo/*.json               resumen de la última corrida de cada modelo
   └── estado.json
   │  pronostico.exportar() + recolector/pronostico_calibracion.json (generado por la fase 0)
   ▼
/srv/sosgalapagos-clima/datos/pronostico.json ──► sección «Pronóstico de lluvia fuerte» de web/index.html
```

1. **Lluvia diaria de cada modelo determinista en cada punto** de `recolector/zonas_geo.json`. El día va de 00 a 24 h, hora de Galápagos.
2. **Percentil de ese valor en la climatología del propio modelo**, para ese punto y esa anticipación. La climatología son los cuantiles 2024–2026 que guarda `pronostico_calibracion.json`.
3. **Consenso:** el promedio de los percentiles de los 7 modelos. Hacen falta al menos 5.
4. **Probabilidad:** una curva logística (grupo × temporada × plazo) convierte el consenso en la probabilidad de que **alguna estación de la zona mida ≥ 10, 20 o 50 mm** ese día.
5. **Nivel, según la probabilidad de ≥ 20 mm:**
   - «señal de lluvia fuerte»: ≥ 35 %;
   - «atención»: 15–35 %;
   - «sin señal»: el resto.
   - Los cortes y los textos están en `recolector/pronostico_reglas.json`.
6. **Conjuntos:** solo dan los bloques de 6 h de las próximas 72 h, es decir, cuándo se concentra la lluvia. **No** se usan para la probabilidad: sin calibrar, subestiman mucho (ver la fase 0).

**Las horas:** todo se guarda en UTC y se muestra en hora de Galápagos (UTC−6). La página dice de qué corrida sale cada modelo (hora de arranque y hora en que estuvo disponible). Si un modelo pasa de 30 horas, se deja fuera.

## Archivos

| Archivo | Qué es | ¿A mano? |
|---|---|---|
| `recolector/pronostico.py` | Descarga, archivo y resumen público | código |
| `recolector/zonas_geo.json` | Puntos y bbox de cada zona. Los comparte con el satélite (`clima/satelite/`) | sí |
| `recolector/pronostico_reglas.json` | Cortes de los niveles, textos de la página y edad máxima | sí; si cambian las cifras de la evaluación, actualiza el texto |
| `recolector/pronostico_calibracion.json` | Climatologías de los modelos y curvas logísticas | **no**: lo genera `scripts/07_pronostico_evaluacion.py` |
| `scripts/06_pronostico_archivo.py` | Baja el archivo de pronósticos pasados: estaciones (`--puntos estaciones`) y zonas (`--puntos zonas`) | — |
| `scripts/07_pronostico_evaluacion.py` | Evaluación, calibración y figuras (`pronostico/fase0/`) | — |
| `pronostico/fase0/` | Informe, tablas y figuras de la evaluación | generados, salvo `informe.md` |

## Rehacer la evaluación y la calibración

```bash
cd clima
python3 -I scripts/06_pronostico_archivo.py                       # estaciones (incremental, ~25 min la primera vez)
python3 -I scripts/06_pronostico_archivo.py --puntos zonas --modelos ecmwf_ifs025,ecmwf_aifs025_single,gfs_seamless,icon_seamless,ukmo_seamless,meteofrance_seamless,gem_seamless
ssh root@152.44.45.89 'sqlite3 -readonly -header -csv /var/lib/sosgalapagos-clima/clima.db \
  "SELECT fuente,estacion,ts,valor FROM obs WHERE variable=\"lluvia_dia_mm\""' > privado/gsc_diario.csv
../geodatos/.venv/bin/python -I scripts/07_pronostico_evaluacion.py   # ~3 min
./deploy/publicar.sh                                               # solo desde main y si te lo piden
```

- **Licencia y versionado:** el archivo de Open-Meteo es CC BY 4.0. No se versiona (`datos/pronostico-archivo/` pesa 30 MB y se regenera con 06). Los pares diarios con lluvia medida tampoco, porque llevan series del GSC.
- **Endpoints:** van en `privado/fuentes.env` (`CLIMA_OPENMETEO_FORECAST_API`, `CLIMA_OPENMETEO_PREVIOUS_API` y `CLIMA_OPENMETEO_ENSEMBLE_API`).
- **Límites:** el plan gratuito, sin fines de lucro, permite 10 000 llamadas al día. El recolector usa unas 1 000.

## Limitaciones que hay que decir siempre

- **Santa Cruz:** su calibración se apoya en 7 meses (abr–nov-2026) y casi todo en octubre. En temporada lluviosa usa la curva de San Cristóbal.
- **Costa:** no anticipa la mayoría de los aguaceros fuertes.
- **Isabela:** no tiene estaciones, así que su señal es solo orientativa.
- **Intensidad:** no se pronostica la intensidad en 1–3 h. Para eso están las estaciones (regla de inundación) y el satélite.
