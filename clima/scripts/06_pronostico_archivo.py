#!/usr/bin/env python3
"""Fase 0 del pronóstico: baja el archivo de pronósticos pasados de los modelos globales
en las estaciones con lluvia medida, para comparar «lo que se pronosticó» con «lo que llovió».

Fuente: archivo de corridas anteriores de Open-Meteo (licencia CC BY 4.0). El endpoint se lee
de CLIMA_OPENMETEO_PREVIOUS_API (entorno o privado/fuentes.env; ver fuentes.env.ejemplo).

Para cada hora válida, `precipitation_previous_dayN` es la lluvia de esa hora pronosticada
N×24 h antes, es decir, con N días de anticipación. `precipitation` (anticipación 0) es la
corrida más reciente disponible, de pocas horas antes.

Salida:
  datos/pronostico-archivo/cache/<estaciones|zonas>/<modelo>/<tramo>.json.gz   respuesta cruda (no versionada)
  datos/pronostico-archivo/pronostico_horario.csv.gz        estaciones: punto, modelo, anticipación, hora UTC, mm
  datos/pronostico-archivo/pronostico_horario_zonas.csv.gz  ídem en los puntos de zonas_geo.json (--puntos zonas)

Solo usa la biblioteca estándar. Uso:
    python3 -I scripts/06_pronostico_archivo.py                 # 2024-01-01 → anteayer
    python3 -I scripts/06_pronostico_archivo.py --desde 2026-10-01 --modelos ecmwf_ifs
"""
import argparse
import csv
import datetime as dt
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "pronostico-archivo"
CACHE = SALIDA / "cache"

# Estaciones con lluvia medida (coordenadas de la tabla `estaciones` del recolector).
PUNTOS = {
    "ierse/n_glps01": ("Cerro Crocker", -0.6424, -90.3260),
    "ierse/n_glps05": ("Los Guayabillos", -0.6991, -90.3420),
    "ierse/n_glps06": ("Militar", -0.4900, -90.2808),
    "ierse/n_glps09": ("Santa Rosa", -0.6545, -90.4035),
    "gsc/junco": ("El Junco", -0.8965, -89.4816),
    "gsc/cerro_alto": ("Cerro Alto", -0.8870, -89.5310),
    "gsc/mirador": ("El Mirador", -0.8862, -89.5396),
    "gsc/merceditas": ("Merceditas", -0.8897, -89.4420),
    "fcd/puerto_ayora": ("Puerto Ayora (FCD; INAMHI M0191)", -0.7431, -90.3025),
}
# Puntos de las zonas (zonas_geo.json), para la climatología de cada modelo que usa el pronóstico en vivo.
def puntos_zonas():
    z = json.loads((RAIZ / "recolector" / "zonas_geo.json").read_text())["zonas"]
    return {f"zona/{p['id']}": (p["nombre"], p["lat"], p["lon"]) for zona in z.values() for p in zona["puntos"]}


# Modelos globales con archivo desde 2024 (ecmwf_ifs 9 km, desde fines de 2025).
MODELOS = ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless",
           "ukmo_seamless", "meteofrance_seamless", "gem_seamless"]
ANTICIPACIONES = [0, 1, 2, 3, 5, 7]  # días
UA = "sosgalapagos-clima/1.0 (pronostico, fase 0)"


def _api():
    nombre = "CLIMA_OPENMETEO_PREVIOUS_API"
    ruta = RAIZ / "privado" / "fuentes.env"
    if nombre not in os.environ and ruta.exists():
        for linea in ruta.read_text().splitlines():
            if linea.strip().startswith(nombre + "="):
                os.environ[nombre] = linea.split("=", 1)[1].strip().strip('"')
    if not os.environ.get(nombre):
        sys.exit(f"Falta {nombre} (privado/fuentes.env)")
    return os.environ[nombre]


def variable(n):
    return "precipitation" if n == 0 else f"precipitation_previous_day{n}"


def pedir(api, modelo, d0, d1, puntos):
    q = urllib.parse.urlencode({
        "latitude": ",".join(str(p[1]) for p in puntos.values()),
        "longitude": ",".join(str(p[2]) for p in puntos.values()),
        "hourly": ",".join(variable(n) for n in ANTICIPACIONES),
        "models": modelo, "timezone": "GMT", "start_date": d0.isoformat(), "end_date": d1.isoformat()})
    for intento in range(6):
        try:
            req = urllib.request.Request(f"{api}?{q}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            cuerpo = e.read()[:300].decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                espera = 60 * (intento + 1)
                print(f"  {modelo} {d0}: HTTP {e.code}; espero {espera} s ({cuerpo})", flush=True)
                time.sleep(espera)
                continue
            raise RuntimeError(f"{modelo} {d0}: HTTP {e.code} {cuerpo}")
        except (urllib.error.URLError, TimeoutError) as e:
            time.sleep(10 * (intento + 1))
            last = e
    raise RuntimeError(f"{modelo} {d0}: sin respuesta")


def tramos(desde, hasta, dias=91):
    d = desde
    while d <= hasta:
        f = min(hasta, d + dt.timedelta(days=dias - 1))
        yield d, f
        d = f + dt.timedelta(days=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2024-01-01")
    ap.add_argument("--hasta", default=(dt.date.today() - dt.timedelta(days=2)).isoformat())
    ap.add_argument("--modelos", default=",".join(MODELOS))
    ap.add_argument("--rehacer", action="store_true", help="vuelve a pedir tramos ya guardados")
    ap.add_argument("--solo-tabla", action="store_true", help="no descarga; rehace la tabla con lo guardado")
    ap.add_argument("--puntos", choices=["estaciones", "zonas"], default="estaciones")
    a = ap.parse_args()
    desde, hasta = dt.date.fromisoformat(a.desde), dt.date.fromisoformat(a.hasta)
    api = None if a.solo_tabla else _api()
    puntos = PUNTOS if a.puntos == "estaciones" else puntos_zonas()

    for modelo in ([] if a.solo_tabla else a.modelos.split(",")):
        for d0, d1 in tramos(desde, hasta):
            ruta = CACHE / a.puntos / modelo / f"{d0}_{d1}.json.gz"
            if ruta.exists() and not a.rehacer:
                continue
            ruta.parent.mkdir(parents=True, exist_ok=True)
            t = time.time()
            datos = pedir(api, modelo, d0, d1, puntos)
            with gzip.open(ruta, "wt") as fh:
                json.dump(datos, fh)
            print(f"{modelo} {d0}→{d1}: {time.time() - t:.1f} s", flush=True)
            time.sleep(3)

    # Tabla larga con todo lo guardado (solo horas con valor).
    filas = 0
    nombre = "pronostico_horario.csv.gz" if a.puntos == "estaciones" else "pronostico_horario_zonas.csv.gz"
    with gzip.open(SALIDA / nombre, "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["punto", "modelo", "anticipacion_dias", "hora_utc", "lluvia_mm", "lat_celda", "lon_celda"])
        for carpeta in sorted(p for p in (CACHE / a.puntos).iterdir() if p.is_dir()):
            for ruta in sorted(carpeta.glob("*.json.gz")):
                with gzip.open(ruta, "rt") as f:
                    datos = json.load(f)
                datos = datos if isinstance(datos, list) else [datos]
                for punto, p in zip(puntos, datos):
                    h = p.get("hourly", {})
                    for n in ANTICIPACIONES:
                        for t, v in zip(h.get("time", []), h.get(variable(n), [])):
                            if v is not None:
                                w.writerow([punto, carpeta.name, n, t, v, p["latitude"], p["longitude"]])
                                filas += 1
    print(f"{nombre}: {filas} filas")


if __name__ == "__main__":
    main()
