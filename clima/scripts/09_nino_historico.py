#!/usr/bin/env python3
"""Series históricas de El Niño para los estudios: índices de la NOAA y temperatura del mar en Galápagos.

Escribe en clima/datos/nino/:
  oni.csv                     ONI (NOAA CPC), por temporada de tres meses, desde 1950
  indices_mensuales.csv       Niño 1+2, 3, 3.4 y 4 (NOAA CPC, base 1991–2020), mensual, desde 1982
  indices_semanales.csv       los mismos, semanales (semana centrada en el miércoles), desde 1981
  galapagos_crw_mensual.csv   temperatura y anomalía mensual media del mar alrededor del archipiélago
                              (NOAA Coral Reef Watch 5 km, caja 1,5° N–1,5° S, 92°–89° O, cada 0,2°), desde 1985
  galapagos_oisst_diario.csv  lo mismo, diario, con OISST v2.1 (cada 0,5°), desde sep-1981 (con --diario)

Todo es dominio público de la NOAA (citar la fuente). Es contexto: la voz oficial sobre El Niño en
Ecuador es el comité ERFEN. Las anomalías de CRW (base 1985–2012) y de OISST/CPC (base 1991–2020) no
se mezclan: en Niño 1+2, CRW da unos 0,6 °C más.

Uso, desde la raíz del repositorio:
  geodatos/.venv/bin/python -I clima/scripts/09_nino_historico.py [--diario]
Necesita en clima/privado/fuentes.env (o en el entorno): CLIMA_CPC_ONI_URL, CLIMA_CPC_SEMANAL_URL,
CLIMA_CPC_MENSUAL_URL, CLIMA_CRW_MENSUAL_ERDDAP y, para --diario, CLIMA_OISST_FINAL_ERDDAP.
Solo biblioteca estándar.
"""
import argparse
import csv
import datetime as dt
import io
import math
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "nino"
CAJA = (1.5, -1.5, -92.0, -89.0)  # norte, sur, oeste, este
MESES = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
TEMPORADAS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def env(nombre):
    if nombre not in os.environ:
        f = RAIZ / "privado" / "fuentes.env"
        if f.exists():
            for linea in f.read_text().splitlines():
                if linea.startswith(nombre + "="):
                    os.environ[nombre] = linea.split("=", 1)[1].strip()
    valor = os.environ.get(nombre)
    if not valor:
        raise SystemExit(f"Falta {nombre} en clima/privado/fuentes.env")
    return valor


def bajar(url, espera=180, intentos=3):
    for i in range(intentos):
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": "sosgalapagos.org (estudios de clima)"})
            with urllib.request.urlopen(pedido, timeout=espera) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(5 * (i + 1))


def escribir(nombre, cabecera, filas):
    SALIDA.mkdir(parents=True, exist_ok=True)
    with open(SALIDA / nombre, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cabecera)
        w.writerows(filas)
    print(f"{nombre}: {len(filas)} filas")


def oni():
    filas = []
    for linea in bajar(env("CLIMA_CPC_ONI_URL")).splitlines():
        p = linea.split()
        if len(p) == 4 and p[0] in TEMPORADAS and p[1].isdigit():
            filas.append([p[0], p[1], f"{p[1]}-{TEMPORADAS.index(p[0]) + 1:02d}", p[2], p[3]])
    escribir("oni.csv", ["temporada", "anio", "mes_central", "sst_c", "anom_c"], filas)


def mensuales():
    filas = []
    for linea in bajar(env("CLIMA_CPC_MENSUAL_URL")).splitlines():
        p = linea.split()
        if len(p) == 10 and p[0].isdigit():
            filas.append([f"{int(p[0])}-{int(p[1]):02d}", *p[2:]])
    escribir("indices_mensuales.csv", ["mes", "nino12_sst", "nino12_anom", "nino3_sst", "nino3_anom", "nino4_sst", "nino4_anom", "nino34_sst", "nino34_anom"], filas)


def semanales():
    filas = []
    for linea in bajar(env("CLIMA_CPC_SEMANAL_URL")).splitlines():
        m = re.match(r"\s*(\d{2})([A-Z]{3})(\d{4})(.*)", linea)
        if m and m.group(2) in MESES:
            v = re.findall(r"-?\d+\.\d", m.group(4))  # los negativos vienen pegados al número anterior
            if len(v) == 8:
                filas.append([dt.date(int(m.group(3)), MESES[m.group(2)], int(m.group(1))).isoformat(), *v])
    escribir("indices_semanales.csv", ["semana", "nino12_sst", "nino12_anom", "nino3_sst", "nino3_anom", "nino34_sst", "nino34_anom", "nino4_sst", "nino4_anom"], filas)


def _media_por_fecha(texto, variables):
    """CSV de ERDDAP → {fecha: [media ponderada por coseno de cada variable]} (las celdas de tierra se saltan)."""
    lector = csv.reader(io.StringIO(texto))
    cab = next(lector)
    next(lector)
    it, ila = cab.index("time"), cab.index("latitude")
    iv = [cab.index(v) for v in variables]
    acum = {}
    for fila in lector:
        w = math.cos(math.radians(float(fila[ila])))
        a = acum.setdefault(fila[it][:10], [[0.0, 0.0] for _ in variables])
        for k, i in enumerate(iv):
            try:
                x = float(fila[i])
            except ValueError:
                continue
            if not math.isnan(x):
                a[k][0] += w * x
                a[k][1] += w
    return {d: [round(s / p, 3) if p else None for s, p in a] for d, a in sorted(acum.items())}


def crw_mensual():
    base, (n, s, o, e) = env("CLIMA_CRW_MENSUAL_ERDDAP"), CAJA
    filas = []
    hoy = dt.date.today().year
    for desde in range(1985, hoy + 1, 5):
        fin = "last" if desde + 4 >= hoy else f"({desde + 4}-12-31)"  # pedir más allá del último dato da error
        sel = f"[({desde}-01-01):{fin}][({n}):4:({s})][({o}):4:({e})]"
        consulta = ",".join(f"{v}{sel}" for v in ("sea_surface_temperature", "sea_surface_temperature_anomaly"))
        try:
            texto = bajar(f"{base}.csv?{urllib.parse.quote(consulta, safe='[]():,')}")
        except Exception as ex:
            print(f"  {desde}: {type(ex).__name__}")
            continue
        for d, (t, a) in _media_por_fecha(texto, ["sea_surface_temperature", "sea_surface_temperature_anomaly"]).items():
            filas.append([d[:7], t, a])
        print(f"  CRW mensual {desde}: listo")
    escribir("galapagos_crw_mensual.csv", ["mes", "sst_c", "anom_c_base_1985_2012"], filas)


def oisst_diario():
    base, (n, s, o, e) = env("CLIMA_OISST_FINAL_ERDDAP"), CAJA
    cache = SALIDA / ".cache_oisst"
    cache.mkdir(parents=True, exist_ok=True)
    filas = []
    hoy = dt.date.today()
    for anio in range(1981, hoy.year + 1):
        f = cache / f"{anio}.csv"
        if not f.exists() or anio >= hoy.year - 1:  # el año en curso y el anterior se vuelven a bajar
            desde = "1981-09-01" if anio == 1981 else f"{anio}-01-01"
            fin = "last" if anio == hoy.year else f"({anio}-12-31T12:00:00Z)"
            sel = f"[({desde}T12:00:00Z):{fin}][(0.0)][({s}):2:({n})][({o}):2:({e})]"
            consulta = ",".join(f"{v}{sel}" for v in ("sst", "anom"))
            try:
                f.write_text(bajar(f"{base}.csv?{urllib.parse.quote(consulta, safe='[]():,')}"))
            except Exception as ex:
                print(f"  {anio}: {type(ex).__name__}")
                continue
        for d, (t, a) in _media_por_fecha(f.read_text(), ["sst", "anom"]).items():
            filas.append([d, t, a])
    escribir("galapagos_oisst_diario.csv", ["fecha", "sst_c", "anom_c_base_1991_2020"], filas)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--diario", action="store_true", help="también la serie diaria de OISST (≈ 45 consultas, unos minutos)")
    a = ap.parse_args()
    oni()
    mensuales()
    semanales()
    crw_mensual()
    if a.diario:
        oisst_diario()
