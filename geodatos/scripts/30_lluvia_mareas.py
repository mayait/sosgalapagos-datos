#!/usr/bin/env python3
"""Lluvia medida en Santa Cruz y San Cristóbal (sep–nov 2026) contrastada con la marea.

Qué hace
  1. Reúne todas las series de lluvia disponibles y hace un inventario por estación (isla, cota, periodo,
     resolución, cobertura, huecos y calidad):
       - IERSE-WSN (Santa Cruz, 5 min): ../clima/datos/ierse-wsn/serie_5min.csv.gz (hora UTC−6).
       - INAMHI M0191 Puerto Ayora y estaciones USFQ-GSC M5300–M5303 de San Cristóbal (horario, 16-oct → 2-nov):
         ../clima/datos/inamhi/historial/historial_estaciones_pais_20261102.json (hora continental UTC−5,
         etiqueta = inicio de la hora).
       - Archivo del recolector de sosgalapagos.org/clima (CSV privados, hora UTC): INAMHI de 5 min, GSC-USFQ,
         WeatherLink (estación de Erna) y el último tramo de IERSE.
       - Tempest de Punta Estrada (1 min → 5 min), bajado de su API con el token de solo lectura del dueño.
  2. Nivel del mar:
       - Puerto Ayora (Academy Bay) y Baltra OBSERVADO: mareógrafos de la IOC (sensor radar «ras»), 1 min,
         llevado al cero de UHSLC con el solape de septiembre y expresado respecto del nivel medio 2017–2024.
       - Marea astronómica PREDICHA: UTide sobre las series horarias UHSLC fast-delivery (2022 → 30-sep-2026),
         que bajó la sesión de /clima en ../clima/datos/uhslc/ (se leen, no se modifican).
       - Puerto Baquerizo Moreno no tiene mareógrafo (UHSLC no tiene serie; INOCAR no respondió). Se ESTIMA
         trasladando la serie observada de Puerto Ayora con el desfase y la razón de amplitudes de la onda M2
         entre las dos bahías, que se sacan del modelo de nivel del mar de Open-Meteo Marine.
  3. Contraste de cada evento de lluvia con el nivel del mar y la fase de la marea (pleamar/bajamar,
     sicigia/cuadratura) y con el nivel fijo de +0,75 m del modelo 2D de Santa Cruz.
  4. Figuras mareas_*.png y CSV derivados.

Entradas crudas (no versionadas, datos no confiables; se validan tipos y rangos):
  descargas/lluvia_mareas/   IOC, Tempest, Open-Meteo Marine y CSV del recolector.
Los endpoints, el token de Tempest y el del enlace de investigadores se leen de ../clima/privado/ y NUNCA se
escriben en las salidas.

Salidas:
  datos/mareas/nivel_mar_{puerto_ayora,baltra}_10min.csv     observado, predicho y residuo (m sobre el NMM 2017–2024)
  datos/mareas/nivel_mar_puerto_baquerizo_estimado_10min.csv
  datos/mareas/pleamares_bajamares.csv, constituyentes.csv, resumen_mareas.json
  estudios/santa-cruz/datos/lluvia_mareas_{inventario,horaria,diaria,eventos}.csv
  estudios/san-cristobal/datos/lluvia_mareas_{inventario,horaria,diaria,eventos}.csv
  estudios/{santa-cruz,san-cristobal}/figuras/mareas_*.png

Uso, desde geodatos/:
  .venv/bin/python -I scripts/30_lluvia_mareas.py --bajar   # descarga (incremental) y análisis
  .venv/bin/python -I scripts/30_lluvia_mareas.py           # solo análisis con lo ya descargado
"""
import argparse
import datetime as dt
import gzip
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import utide  # noqa: E402

GEO = Path(__file__).resolve().parent.parent
CLIMA = GEO.parent / "clima"
PRIV = CLIMA / "privado"
DESC = GEO / "descargas" / "lluvia_mareas"
OUT_M = GEO / "datos" / "mareas"
SC = GEO / "estudios" / "santa-cruz"
SCB = GEO / "estudios" / "san-cristobal"

UTC = dt.timezone.utc
GAL = pd.Timedelta(hours=-6)          # Galápagos = UTC−6
INI = pd.Timestamp("2026-09-01", tz="UTC")
FIN_PRED = pd.Timestamp("2026-11-10", tz="UTC")
REF = ("2017-01-01", "2024-12-31")    # nivel medio de referencia (el mismo que usa clima/scripts/05_mareas.py)
AJUSTE_DESDE = "2022-01-01"
NIVEL_MAR_2D = 0.75                   # m, nivel fijo del mar en scripts/24_modelo2d_santa_cruz.py

# ---------------------------------------------------------------- estaciones de lluvia
# clave: (nombre, isla, fuente, cota m, lat, lon, resolución, nota de calidad)
ESTACIONES = {
    "n_glps05": ("Los Guayabillos", "Santa Cruz", "IERSE-WSN", 178, -0.6991, -90.3420, "5 min",
                 "Corte de 21,3 h desde el 30-oct 21:25; marca 0,0 mm desde que volvió (31-oct 18:45): probable obstrucción, sin verificar"),
    "n_glps09": ("Santa Rosa", "Santa Cruz", "IERSE-WSN", 416, -0.6545, -90.4035, "5 min",
                 "Corte de 21,3 h desde el 30-oct 21:22"),
    "n_glps01": ("Cerro Crocker", "Santa Cruz", "IERSE-WSN", 861, -0.6424, -90.3260, "5 min",
                 "No fiable desde el 11-ago-2026 (probable obstrucción del embudo); hueco todas las noches ≈01:00–05:30"),
    "n_glps06": ("Militar (Baltra)", "Santa Cruz", "IERSE-WSN", 14, -0.4900, -90.2808, "5 min",
                 "Costa norte, lejos de Puerto Ayora; dudoso según la página de lluvia"),
    "M0191": ("Puerto Ayora, Charles Darwin (M0191)", "Santa Cruz", "INAMHI", 6, -0.7431, -90.3025, "1 h (historial) y 5 min desde el 1-nov",
              "Historial horario del INAMHI (solo guarda 90 días); hora continental UTC−5 convertida a UTC−6"),
    "punta_estrada": ("Punta Estrada, Puerto Ayora (Tempest)", "Santa Cruz", "Tempest", 8, -0.7499, -90.3108, "1 min → 5 min",
                      "Estación particular; sensor de lluvia háptico, puede subestimar chubascos intensos"),
    "pa_weatherlink": ("Puerto Ayora, estación de Erna (WeatherLink)", "Santa Cruz", "WeatherLink", 10, -0.7534, -90.3120, "≈5 min (por diferencia del acumulado diario)",
                       "Solo se recoge desde el 2-nov-2026; no hay histórico del evento"),
    "M5300": ("Merceditas (M5300)", "San Cristóbal", "USFQ-GSC vía INAMHI", 100, -0.8897, -89.4420, "1 h (historial); 5 min (GSC) desde el 1-nov",
              "Hora continental UTC−5 convertida a UTC−6"),
    "M5301": ("El Junco (M5301)", "San Cristóbal", "USFQ-GSC vía INAMHI", 584, -0.8965, -89.4816, "1 h (historial); 5 min (GSC) desde el 1-nov",
              "Hora continental UTC−5 convertida a UTC−6"),
    "M5302": ("Cerro Alto (M5302)", "San Cristóbal", "USFQ-GSC vía INAMHI", 517, -0.8870, -89.5310, "1 h (historial); 5 min (GSC) desde el 1-nov",
              "Hora continental UTC−5 convertida a UTC−6"),
    "M5303": ("El Mirador (M5303)", "San Cristóbal", "USFQ-GSC vía INAMHI", 387, -0.8862, -89.5396, "1 h (historial); 5 min (GSC) desde el 1-nov",
              "Hora continental UTC−5 convertida a UTC−6"),
    "M0221": ("Puerto Baquerizo Moreno (M0221)", "San Cristóbal", "INAMHI", 6, -0.9041, -89.6143, "5 min",
              "Solo desde el 2-nov-2026 14:05 UTC; no está en el historial horario"),
}
GSC_A_INAMHI = {"merceditas": "M5300", "junco": "M5301", "cerro_alto": "M5302", "mirador": "M5303"}

# ---------------------------------------------------------------- eventos (hora UTC−6)
# ventana de búsqueda del pico de lluvia; horas de interés hidráulico
EVENTOS = [
    ("03-oct", "Santa Cruz", "2026-10-03 00:00", "2026-10-05 00:00", {}),
    ("23-oct", "Santa Cruz", "2026-10-23 00:00", "2026-10-24 00:00", {}),
    ("30-oct", "Santa Cruz", "2026-10-30 06:00", "2026-10-31 06:00",
     {"Llegada del agua al centro de La Cascada (2D, b)": "2026-10-30 20:53",
      "Pico de entrada a La Cascada (2D, b)": "2026-10-30 22:12",
      "Calado máximo en el barrio (2D, b)": "2026-10-30 22:24",
      "Pico de salida al mar (2D, b)": "2026-10-30 22:34"}),
    ("1-nov", "Santa Cruz", "2026-11-01 00:00", "2026-11-02 00:00", {}),
    ("2-nov", "Santa Cruz", "2026-11-02 00:00", "2026-11-02 16:00", {}),
    ("23-oct", "San Cristóbal", "2026-10-22 00:00", "2026-10-24 00:00", {}),
    ("30/31-oct", "San Cristóbal", "2026-10-30 06:00", "2026-10-31 18:00",
     {"METAR SEST: lluvia fuerte (+RA)": "2026-10-30 15:00",
      "Desborde de Barrio Frío y Divino Niño («mañana», SNGR): 08:00": "2026-10-31 08:00",
      "Desborde de Barrio Frío y Divino Niño («mañana», SNGR): 12:00": "2026-10-31 12:00"}),
    ("1-nov", "San Cristóbal", "2026-11-01 00:00", "2026-11-02 00:00", {}),
    ("2-nov", "San Cristóbal", "2026-11-02 00:00", "2026-11-02 16:00", {}),
]


# ================================================================ utilidades
def env():
    out = {k: v for k, v in os.environ.items() if k.startswith("CLIMA_")}
    f = PRIV / "fuentes.env"
    if f.exists():
        for linea in f.read_text().splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                out.setdefault(k.strip(), v.strip())
    return out


def http(url, timeout=120, intentos=3):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sosgalapagos-datos/30_lluvia_mareas"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == intentos - 1:
                raise RuntimeError(f"descarga fallida ({type(e).__name__})") from None
            time.sleep(3 * (i + 1))


def loc(ts_utc):
    """UTC → hora de Galápagos sin zona (para tablas y figuras)."""
    return (pd.DatetimeIndex(ts_utc).tz_convert("UTC") + GAL).tz_localize(None)


def fmt(x, d=2):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


# ================================================================ 1. descargas
def bajar():
    e = env()
    DESC.mkdir(parents=True, exist_ok=True)
    hoy = pd.Timestamp.now(tz="UTC").floor("D")
    # --- IOC: tramos de 5 días; los cerrados no se repiten
    for cod in ("sant", "balt"):
        t = INI
        while t < hoy + pd.Timedelta(days=1):
            t1 = t + pd.Timedelta(days=5)
            f = DESC / f"ioc_{cod}_{t:%Y%m%d}.json.gz"
            if not f.exists() or t1 > hoy - pd.Timedelta(days=1):
                q = urllib.parse.urlencode({"query": "data", "code": cod, "format": "json",
                                            "timestart": t.strftime("%Y-%m-%dT%H:%M:%S"),
                                            "timestop": t1.strftime("%Y-%m-%dT%H:%M:%S")})
                d = json.loads(http(f"{e['CLIMA_IOC_API']}?{q}"))
                if not isinstance(d, list):
                    raise ValueError(f"IOC {cod}: respuesta inesperada")
                d = [{"stime": str(x["stime"])[:19], "sensor": str(x["sensor"])[:4], "slevel": float(x["slevel"])}
                     for x in d if isinstance(x, dict) and isinstance(x.get("slevel"), (int, float))]
                with gzip.open(f, "wt") as g:
                    json.dump(d, g)
                print(f"  IOC {cod} {t:%Y-%m-%d}: {len(d)} registros")
            t = t1
    # --- Tempest: un archivo por día (UTC)
    dev = e["CLIMA_TEMPEST_EQUIPOS"].split(",")[0].split(":")[0]
    for d0 in pd.date_range(INI, hoy, freq="D"):
        f = DESC / f"tempest_{d0:%Y%m%d}.json.gz"
        if f.exists() and d0 < hoy - pd.Timedelta(days=1):
            continue
        q = urllib.parse.urlencode({"token": e["CLIMA_TEMPEST_TOKEN"], "time_start": int(d0.timestamp()),
                                    "time_end": int((d0 + pd.Timedelta(days=1)).timestamp()) - 1})
        d = json.loads(http(f"{e['CLIMA_TEMPEST_API']}/observations/device/{dev}?{q}", timeout=90))
        obs = d.get("obs") or []
        filas = []
        for o in obs:  # obs_st: 0 tiempo, 12 lluvia del minuto (mm), 19 lluvia corregida «Rain Check» si existe
            if isinstance(o, list) and len(o) > 12 and isinstance(o[0], int):
                r = o[12] if isinstance(o[12], (int, float)) else None
                rc = o[19] if len(o) > 19 and isinstance(o[19], (int, float)) else None
                filas.append([o[0], r, rc])
        with gzip.open(f, "wt") as g:
            json.dump(filas, g)
    print("  Tempest: listo")
    # --- Open-Meteo Marine: nivel del mar modelado (marea incluida) en las dos bahías
    q = urllib.parse.urlencode({"latitude": "-0.902,-0.755", "longitude": "-89.612,-90.309",
                                "hourly": "sea_level_height_msl", "timezone": "GMT",
                                "start_date": INI.strftime("%Y-%m-%d"), "end_date": (hoy + pd.Timedelta(days=1)).strftime("%Y-%m-%d")})
    api = os.environ.get("CLIMA_OPENMETEO_MARINE_API") or e.get("CLIMA_OPENMETEO_MARINE_API")
    if not api:
        raise RuntimeError("Falta CLIMA_OPENMETEO_MARINE_API en clima/privado/fuentes.env")
    d = json.loads(http(f"{api}?{q}"))
    (DESC / "openmeteo_marine.json").write_text(json.dumps(d))
    print("  Open-Meteo Marine: listo")
    # --- CSV del recolector (enlace de investigadores; token en privado/)
    tok = (PRIV / "token_investigadores.txt").read_text().strip()
    for nombre in ["clima_galapagos_2026-09.csv.gz", "clima_galapagos_2026-10.csv.gz", "clima_galapagos_2026-11.csv.gz",
                   "estaciones.csv"]:
        (DESC / nombre).write_bytes(http(f"https://sosgalapagos.org/datos-clima/{tok}/csv/{nombre}", timeout=300))
    print("  recolector: listo")


# ================================================================ 2. lluvia
def lluvia_5min():
    """Tabla larga: estacion, t (UTC, inicio del intervalo), mm, paso (min)."""
    partes = []
    # IERSE: cada registro es la lluvia desde el anterior; se asigna al instante del registro
    s = pd.read_csv(CLIMA / "datos" / "ierse-wsn" / "serie_5min.csv.gz", usecols=["estacion_id", "fecha_hora_local", "lluvia_mm"])
    s["t"] = pd.to_datetime(s.fecha_hora_local.str[:19]).dt.tz_localize("UTC") - GAL
    partes.append(pd.DataFrame({"estacion": s.estacion_id, "t": s.t, "mm": s.lluvia_mm.astype(float), "paso": 5}))
    # recolector (UTC): IERSE posterior, INAMHI 5 min, GSC, WeatherLink
    rec = []
    for f in sorted(DESC.glob("clima_galapagos_2026-*.csv.gz")):
        d = pd.read_csv(f)
        rec.append(d[d.variable == "lluvia_mm"])
    rec = pd.concat(rec)
    rec["t"] = pd.to_datetime(rec.ts_utc, utc=True)
    rec["mm"] = pd.to_numeric(rec.valor, errors="coerce")
    rec = rec[(rec.mm >= 0) & (rec.mm < 200)]
    ier = rec[(rec.fuente == "ierse")]
    ultimo = partes[0].groupby("estacion").t.max()
    ier = ier[ier.t > ier.estacion.map(ultimo)]
    partes.append(pd.DataFrame({"estacion": ier.estacion, "t": ier.t, "mm": ier.mm, "paso": 5}))
    ina = rec[(rec.fuente == "inamhi") & (rec.ts_utc.str[17:19] == "00")]          # filas de 5 min (las horarias van a :30)
    partes.append(pd.DataFrame({"estacion": ina.estacion, "t": ina.t, "mm": ina.mm, "paso": 5}))
    gsc = rec[rec.fuente == "gsc"]
    partes.append(pd.DataFrame({"estacion": gsc.estacion.map(GSC_A_INAMHI).fillna(gsc.estacion), "t": gsc.t, "mm": gsc.mm, "paso": 5}))
    wl = rec[rec.fuente == "weatherlink"]
    partes.append(pd.DataFrame({"estacion": wl.estacion, "t": wl.t, "mm": wl.mm, "paso": 5}))
    # Tempest: 1 min → 5 min
    filas = []
    for f in sorted(DESC.glob("tempest_*.json.gz")):
        for ts, r, rc in json.loads(gzip.open(f, "rt").read()):
            if r is not None and 0 <= r < 50:
                filas.append((ts, r, rc))
    tp = pd.DataFrame(filas, columns=["ts", "mm", "mm_rc"]).drop_duplicates("ts")
    tp["t"] = pd.to_datetime(tp.ts, unit="s", utc=True).dt.floor("5min")
    tp5 = tp.groupby("t").agg(mm=("mm", "sum"), n=("mm", "size")).reset_index()
    partes.append(pd.DataFrame({"estacion": "punta_estrada", "t": tp5.t, "mm": tp5.mm, "paso": 5}))
    s5 = pd.concat(partes).dropna(subset=["mm"]).drop_duplicates(["estacion", "t"]).sort_values(["estacion", "t"])
    return s5[s5.t >= INI - pd.Timedelta(days=1)].reset_index(drop=True)


def lluvia_horaria_inamhi():
    """Historial horario INAMHI (UTC−5, etiqueta = inicio de la hora) → UTC."""
    d = json.load(open(CLIMA / "datos" / "inamhi" / "historial" / "historial_estaciones_pais_20261102.json"))
    filas = [(f["codigo"], f["hora"], f.get("lluvia_mm"), f.get("n_lluvia")) for f in d["filas"]
             if f.get("codigo") in ESTACIONES and f.get("lluvia_mm") is not None]
    h = pd.DataFrame(filas, columns=["estacion", "hora", "mm", "n"])
    h["t"] = pd.to_datetime(h.hora).dt.tz_localize("UTC") + pd.Timedelta(hours=5)
    h["mm"] = h.mm.astype(float)
    return h[(h.mm >= 0) & (h.mm < 300)][["estacion", "t", "mm", "n"]]


def horaria(s5, hin):
    """Lluvia horaria (UTC) por estación con su cobertura. INAMHI: historial horario; 5 min solo donde no hay historial."""
    s5 = s5.copy()
    s5["h"] = s5.t.dt.floor("h")
    g = s5.groupby(["estacion", "h"]).agg(mm=("mm", "sum"), n=("mm", "size")).reset_index()
    g["cobertura"] = (g.n / 12).clip(upper=1)
    hh = hin.rename(columns={"t": "h"})
    hh["cobertura"] = (pd.to_numeric(hh.n, errors="coerce").fillna(12) / 12).clip(upper=1)  # n_lluvia = registros de 5 min en la hora
    clave = set(zip(hh.estacion, hh.h))
    g = g[[(e, h) not in clave for e, h in zip(g.estacion, g.h)]]
    return pd.concat([g[["estacion", "h", "mm", "cobertura"]], hh[["estacion", "h", "mm", "cobertura"]]]).sort_values(["estacion", "h"])


def inventario(s5, hin, h):
    filas = []
    v0, v1 = INI, pd.Timestamp("2026-11-02 22:00", tz="UTC")
    for k, (nom, isla, fuente, cota, lat, lon, res, nota) in ESTACIONES.items():
        tt = pd.concat([s5[s5.estacion == k].t, hin[hin.estacion == k].t]).sort_values()
        tt = tt[(tt >= v0) & (tt <= v1)]
        if tt.empty:
            continue
        hk = h[(h.estacion == k) & (h.h >= v0) & (h.h <= v1)]
        ini, fin = tt.min(), tt.max()
        horas_posibles = (fin.floor("h") - ini.floor("h")) / pd.Timedelta(hours=1) + 1
        cob = hk.cobertura.sum() / horas_posibles
        dif = tt.diff()
        paso = pd.Timedelta(hours=1) if k.startswith("M5") or k == "M0191" else pd.Timedelta(minutes=5)
        huecos = dif[dif > paso * 2.5]
        mayor = huecos.max() if len(huecos) else pd.Timedelta(0)
        i_may = huecos.idxmax() if len(huecos) else None
        desde_hueco = loc([tt.loc[:i_may].iloc[-2]])[0] if i_may is not None else None
        tot = hk.mm.sum()
        filas.append({
            "clave": k, "estacion": nom, "isla": isla, "fuente": fuente, "cota_m": cota, "lat": lat, "lon": lon,
            "resolucion": res, "desde_utc6": loc([ini])[0].strftime("%Y-%m-%d %H:%M"),
            "hasta_utc6": loc([fin])[0].strftime("%Y-%m-%d %H:%M"),
            "cobertura_horaria_pct": round(100 * cob, 1), "huecos_mayores_que_2,5_pasos": len(huecos),
            "hueco_mayor_h": round(mayor / pd.Timedelta(hours=1), 1),
            "hueco_mayor_desde_utc6": desde_hueco.strftime("%Y-%m-%d %H:%M") if desde_hueco is not None else "",
            "lluvia_total_periodo_mm": round(tot, 1), "calidad": nota})
    return pd.DataFrame(filas)


# ================================================================ 3. nivel del mar
def uhslc(uid):
    d = pd.read_csv(CLIMA / "datos" / "uhslc" / f"global_hourly_fast_{uid}.csv.gz", skiprows=[1])
    s = pd.Series(pd.to_numeric(d.sea_level, errors="coerce").values, index=pd.to_datetime(d.time, utc=True))
    s[(s < -10000) | (s > 10000)] = np.nan
    return s.dropna() / 1000.0  # m


def ajustar(s, lat):
    return utide.solve(s.index.tz_convert(None).to_pydatetime(), s.values, lat=lat, method="ols",
                       conf_int="none", trend=False, verbose=False)


def reconstruir(coef, idx):
    """Marea astronómica pura: sin el nivel medio del ajuste ni las ondas estacionales SA/SSA (que van al residuo)."""
    const = [c for c in coef.name if c not in ("SA", "SSA")]
    h = utide.reconstruct(idx.tz_convert(None).to_pydatetime(), coef, constit=const, verbose=False).h
    return pd.Series(h - coef["mean"], index=idx)


def ioc(cod, sensor="ras"):
    xs = []
    for f in sorted(DESC.glob(f"ioc_{cod}_*.json.gz")):
        xs += [x for x in json.loads(gzip.open(f, "rt").read()) if x["sensor"] == sensor]
    o = pd.DataFrame(xs).drop_duplicates("stime")
    s = pd.Series(o.slevel.values, index=pd.to_datetime(o.stime, utc=True)).sort_index()
    s = s[(s > -20) & (s < 20)]
    # control de calidad sencillo: fuera picos > 0,15 m respecto de la mediana móvil de 31 min y tramos congelados
    med = s.rolling("31min", center=True).median()
    s = s[(s - med).abs() < 0.15]
    cong = s.rolling("60min").std() < 1e-4
    return s[~cong]


def mareas():
    est = {"puerto_ayora": ("sant", 30, -0.7552, "Puerto Ayora (Academy Bay)"),
           "baltra": ("balt", 3, -0.4366, "Baltra")}
    idx = pd.date_range(INI, FIN_PRED, freq="10min")
    res, series = {}, {}
    for clave, (cod, uid, lat, nombre) in est.items():
        s = uhslc(uid)
        msl = float(s[REF[0]:REF[1]].mean())
        tramo = s[AJUSTE_DESDE:] - msl
        # validación fuera de muestra (ajuste hasta jun-2026, prueba jul–sep-2026)
        cv = ajustar(tramo[:"2026-06-30"], lat)
        pr = tramo["2026-07-01":]
        r = pr - reconstruir(cv, pr.index)
        r_sin_media = r - r.rolling("3D", center=True).mean()
        rms = float(np.sqrt(np.nanmean(r_sin_media ** 2)))
        coef = ajustar(tramo, lat)
        pred = reconstruir(coef, idx)
        # observado IOC → cero UHSLC (solape de septiembre, medias horarias) → respecto del NMM
        o = ioc(cod)
        oh = o.resample("1h").mean()
        oh.index = oh.index  # etiqueta = inicio de la hora; UHSLC da el valor horario centrado en la hora
        oh_c = o.rolling("60min", center=True).mean().reindex(s.index, method=None)
        comun = s.index.intersection(oh_c.dropna().index)
        comun = comun[(comun >= INI)]
        desf = float((oh_c[comun] - s[comun]).median())
        disp = float((oh_c[comun] - s[comun]).std())
        obs = o.resample("10min").mean() - desf - msl
        obs = obs.reindex(idx)
        # el observado de 10 min promedia el minuto; se suaviza con 30 min para quitar la agitación
        obs_s = obs.rolling(3, center=True, min_periods=2).mean()
        resid = obs_s - pred
        df = pd.DataFrame({"obs_m": obs_s, "pred_m": pred, "residuo_m": resid})
        series[clave] = df
        res[clave] = {"nombre": nombre, "ioc": cod, "uhslc_id": uid, "nivel_medio_ref_m_cero_uhslc": round(msl, 3),
                      "desfase_ioc_ras_menos_uhslc_m": round(desf, 3), "dispersion_desfase_m": round(disp, 3),
                      "horas_solape": int(len(comun)), "validacion_rms_m": round(rms, 3),
                      "constituyentes_m": {n: round(float(a), 3) for n, a in sorted(zip(coef.name, coef.A), key=lambda x: -x[1])[:10]},
                      "fase_M2_grados": round(float(coef.g[list(coef.name).index("M2")]), 1),
                      "anomalia_mensual_uhslc_m": {k.strftime("%Y-%m"): round(float(v), 3)
                                                   for k, v in (s["2025-09":] - msl).resample("MS").mean().items() if pd.notna(v)},
                      "obs_desde": str(obs.dropna().index.min()), "obs_hasta": str(obs.dropna().index.max()),
                      "_coef": coef}
    return res, series


def baquerizo(series, res):
    """Puerto Baquerizo Moreno estimado desde Puerto Ayora con el desfase y la razón de M2 de Open-Meteo Marine."""
    d = json.loads((DESC / "openmeteo_marine.json").read_text())
    om = {}
    for p, clave in zip(d, ("baquerizo", "puerto_ayora")):
        hh = p["hourly"]
        s = pd.Series(pd.to_numeric(pd.Series(hh["sea_level_height_msl"]), errors="coerce").values,
                      index=pd.to_datetime(hh["time"], utc=True)).dropna()
        om[clave] = s
    c = {k: ajustar(v - v.mean(), lat) for (k, v), lat in zip(om.items(), (-0.902, -0.755))}
    m2 = {k: (float(v.A[list(v.name).index("M2")]), float(v.g[list(v.name).index("M2")])) for k, v in c.items()}
    razon = m2["baquerizo"][0] / m2["puerto_ayora"][0]
    dfase = (m2["baquerizo"][1] - m2["puerto_ayora"][1] + 180) % 360 - 180
    lag_min = dfase / 28.9841042 * 60  # M2: 28,984° por hora
    # comparación del modelo con la marea de UHSLC en Puerto Ayora
    a_pa, g_pa = res["puerto_ayora"]["constituyentes_m"]["M2"], res["puerto_ayora"]["fase_M2_grados"]
    pa = series["puerto_ayora"]
    lag = pd.Timedelta(minutes=round(lag_min))
    idx = pa.index
    pred = (pa.pred_m.shift(freq=lag) * razon).reindex(idx)
    resid = pa.residuo_m.shift(freq=lag).reindex(idx)
    df = pd.DataFrame({"pred_m": pred, "residuo_pa_m": resid, "est_m": pred + resid})
    info = {"metodo": "Puerto Ayora observado (IOC) trasladado con la razón de amplitud y el desfase de M2 entre las celdas de "
                      "Open-Meteo Marine de Puerto Baquerizo Moreno y Puerto Ayora; el residuo no astronómico se toma igual al de Puerto Ayora",
            "razon_amplitud_M2": round(razon, 3), "desfase_M2_min": round(lag_min, 1),
            "om_M2_puerto_ayora_m": round(m2["puerto_ayora"][0], 3), "om_M2_fase_pa": round(m2["puerto_ayora"][1], 1),
            "uhslc_M2_puerto_ayora_m": a_pa, "uhslc_M2_fase_pa": g_pa,
            "om_M2_baquerizo_m": round(m2["baquerizo"][0], 3)}
    return df, info


def extremos(s):
    """Pleamares y bajamares de una serie suave de 10 min."""
    v = s.values
    d = np.diff(v)
    i = np.where(((d[:-1] > 0) & (d[1:] <= 0)) | ((d[:-1] < 0) & (d[1:] >= 0)))[0] + 1
    out = []
    for j in i:
        ventana = s.iloc[max(0, j - 18):j + 19]
        if v[j] in (ventana.max(), ventana.min()):
            out.append((s.index[j], float(v[j]), "pleamar" if v[j] == ventana.max() else "bajamar"))
    return out


def luna(t):
    """Fase lunar aproximada (fase media, error < 1 día): días desde la última luna nueva y edad en fracción."""
    sin = 29.530588853
    ref = pd.Timestamp("2000-01-06 18:14", tz="UTC")
    edad = ((t - ref) / pd.Timedelta(days=1)) % sin
    return edad


def fases_lunares(t0, t1):
    sin = 29.530588853
    ref = pd.Timestamp("2000-01-06 18:14", tz="UTC")
    n0 = math.floor((t0 - ref) / pd.Timedelta(days=1) / sin) - 1
    out = []
    for n in range(n0, n0 + 6):
        for frac, nom in ((0, "luna nueva"), (0.25, "cuarto creciente"), (0.5, "luna llena"), (0.75, "cuarto menguante")):
            t = ref + pd.Timedelta(days=(n + frac) * sin)
            if t0 <= t <= t1:
                out.append((t, nom))
    return out


def rango_diario(pred):
    """Rango de marea (pleamar − bajamar) en ventanas de 25 h centradas, para clasificar sicigia/cuadratura."""
    mx = pred.rolling("25h", center=True).max()
    mn = pred.rolling("25h", center=True).min()
    return mx - mn


def fase(t, serie_pred, serie_obs, ext, rango, p25, p75, ext_obs=()):
    """Estado de la marea en el instante t (UTC)."""
    t = pd.Timestamp(t)
    po = serie_obs.get(t, np.nan) if serie_obs is not None else np.nan
    pp = serie_pred.get(t, np.nan)
    ant = [e for e in ext if e[0] <= t]
    sig = [e for e in ext if e[0] > t]
    a, b = (ant[-1] if ant else None), (sig[0] if sig else None)
    if a and b:
        sube = b[2] == "pleamar"
        estado = "subiendo" if sube else "bajando"
        h_a = (t - a[0]) / pd.Timedelta(hours=1)
        h_b = (b[0] - t) / pd.Timedelta(hours=1)
        if h_a < 1.0:
            estado = f"cerca de la {a[2]} ({h_a:.1f} h después)"
        elif h_b < 1.0:
            estado = f"cerca de la {b[2]} ({h_b:.1f} h antes)"
        else:
            estado = f"{estado}: {h_a:.1f} h tras la {a[2]}, {h_b:.1f} h antes de la {b[2]}"
    else:
        estado = ""
    r = rango.get(t, np.nan)
    ciclo = "sicigia (mareas vivas)" if r >= p75 else ("cuadratura (mareas muertas)" if r <= p25 else "intermedia")
    ple_ant = [e for e in ext_obs if e[0] <= t and e[2] == "pleamar"]
    baj_sig = [e for e in ext_obs if e[0] > t and e[2] == "bajamar"]
    return {"nivel_obs_m": po, "marea_pred_m": pp, "estado": estado, "rango_25h_m": r, "ciclo": ciclo,
            "pleamar_anterior": ple_ant[-1] if ple_ant else None, "bajamar_siguiente": baj_sig[0] if baj_sig else None}


# ================================================================ 4. eventos
def pico_lluvia(s5, h, ests, t0, t1):
    """Máximo de 60 min móviles (5 min) o de 1 h de reloj (horario) por estación en la ventana [t0, t1) UTC."""
    out = []
    for k in ests:
        x5 = s5[(s5.estacion == k) & (s5.t >= t0 - pd.Timedelta(hours=1)) & (s5.t < t1)]
        xh = h[(h.estacion == k) & (h.h >= t0) & (h.h < t1)]
        if xh.empty and x5.empty:
            continue
        total = xh.mm.sum()
        cob = xh.cobertura.mean() * len(xh) / max(1, (t1 - t0) / pd.Timedelta(hours=1))
        if k in ("M0191",) or k.startswith("M5") and len(x5[(x5.t >= t0)]) < 0.5 * len(xh) * 12:
            # resolución horaria
            if xh.mm.max() <= 0:
                out.append((k, total, 0.0, None, "1 h", cob))
                continue
            j = xh.mm.idxmax()
            out.append((k, total, float(xh.mm[j]), xh.h[j] + pd.Timedelta(minutes=30), "1 h", cob))
        else:
            s = x5.set_index("t").mm.sort_index()
            m60 = s.rolling("60min").sum()
            m60 = m60[(m60.index >= t0) & (m60.index < t1)]
            if m60.empty or m60.max() <= 0:
                out.append((k, total, 0.0, None, "60 min", cob))
                continue
            tf = m60.idxmax()
            out.append((k, total, float(m60.max()), tf - pd.Timedelta(minutes=30), "60 min", cob))
    return out


# ================================================================ 5. figuras
COL = {"n_glps05": "#1f78b4", "n_glps09": "#33a02c", "M0191": "#e31a1c", "punta_estrada": "#ff7f00", "pa_weatherlink": "#6a3d9a",
       "n_glps01": "#999999", "n_glps06": "#b15928",
       "M5300": "#1f78b4", "M5301": "#33a02c", "M5302": "#e31a1c", "M5303": "#ff7f00", "M0221": "#6a3d9a"}


def figura_serie(isla, h, mar, ests, nombre_mar, archivo, marcas, linea_2d=False, ext=None, fases=None, nota=""):
    t0, t1 = pd.Timestamp("2026-10-28"), pd.Timestamp("2026-11-03")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.6), sharex=True, gridspec_kw={"height_ratios": [1.1, 1]})
    n = len(ests)
    w = 1 / 24 / (n + 0.5)
    for i, k in enumerate(ests):
        x = h[h.estacion == k]
        if x.empty:
            continue
        tl = loc(x.h)
        sel = (tl >= t0) & (tl < t1)
        a1.bar(tl[sel] + pd.Timedelta(hours=1) * (i + 0.5) / (n + 0.5), x.mm[sel], width=w, color=COL[k],
               label=ESTACIONES[k][0] + f" ({ESTACIONES[k][3]} m)", align="edge")
    a1.set_ylabel("Lluvia horaria (mm)")
    a1.legend(fontsize=7.5, ncol=2, frameon=False, loc="upper left")
    a1.grid(alpha=0.25)
    a1.set_title(f"{isla}: lluvia medida y nivel del mar, 28-oct al 2-nov de 2026 (hora de Galápagos, UTC−6)", fontsize=10.5)
    ml = mar.copy()
    ml.index = loc(ml.index)
    ml = ml[(ml.index >= t0) & (ml.index < t1)]
    if "obs_m" in ml:
        a2.plot(ml.index, ml.pred_m, color="0.55", lw=1.0, ls="--", label="Marea astronómica predicha (UTide sobre UHSLC)")
        a2.plot(ml.index, ml.obs_m, color="#08519c", lw=1.4, label=f"Nivel observado, {nombre_mar} (IOC)")
    else:
        a2.plot(ml.index, ml.pred_m, color="0.55", lw=1.0, ls="--", label="Marea astronómica estimada (traslado desde Puerto Ayora)")
        a2.plot(ml.index, ml.est_m, color="#08519c", lw=1.4, label=f"Nivel estimado, {nombre_mar} (Puerto Ayora observado, trasladado)")
    a2.axhline(0, color="k", lw=0.6)
    if linea_2d:
        a2.axhline(NIVEL_MAR_2D, color="#d62728", lw=1.0, ls=":")
        a2.text(t1 - pd.Timedelta(hours=1), NIVEL_MAR_2D + 0.04, "nivel fijo del modelo 2D: +0,75 m (cero EGM2008 del relieve, supuesto ≈ nivel medio)",
                fontsize=7.5, color="#d62728", ha="right", va="bottom", bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
    for tm, lab, col in marcas:
        for ax in (a1, a2):
            ax.axvspan(pd.Timestamp(tm[0]), pd.Timestamp(tm[1]), color=col, alpha=0.18, lw=0)
        if lab:
            a2.text(pd.Timestamp(tm[0]), 1.42, lab + " ", fontsize=7, color="0.2", va="top", ha="right")
        else:
            a1.text(pd.Timestamp(tm[0]) + (pd.Timestamp(tm[1]) - pd.Timestamp(tm[0])) / 2, a1.get_ylim()[1] * 0.97,
                    "sin datos IERSE\n(corte de transmisión)", fontsize=7, color="0.35", ha="center", va="top")
    if fases:
        for tf, nom in fases:
            tl = loc([tf])[0]
            if t0 <= tl < t1:
                a2.annotate(nom + " (aprox.)", (tl, 1.5), xytext=(0, -2), textcoords="offset points", fontsize=7, color="0.3", ha="center", va="top")
                a2.axvline(tl, color="0.5", lw=0.6, ls="-.")
    a2.set_ylim(-1.15, 1.5)
    a2.set_ylabel("Nivel del mar (m sobre el\nnivel medio 2017–2024)")
    a2.legend(fontsize=7.5, frameon=False, loc="lower right")
    a2.grid(alpha=0.25)
    a2.xaxis.set_major_locator(mdates.DayLocator())
    a2.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    a2.set_xlim(t0, t1)
    import textwrap
    fig.text(0.01, 0.005, "\n".join(textwrap.wrap(nota, 190)), fontsize=6.8, color="0.35")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(archivo, dpi=160)
    plt.close(fig)


def figura_tabla(df, archivo, titulo):
    cols = ["Evento", "Estación (pico) u hora clave", "Máx. 1 h (mm)", "Hora", "Nivel del mar (m)", "Estado de la marea", "Ciclo"]
    filas = df[cols].values.tolist()
    fig, ax = plt.subplots(figsize=(14, 0.27 * len(filas) + 0.6))
    ax.axis("off")
    tb = ax.table(cellText=filas, colLabels=cols, loc="upper center", cellLoc="left", colLoc="left",
                  colWidths=[0.07, 0.29, 0.07, 0.09, 0.08, 0.28, 0.14])
    tb.auto_set_font_size(False)
    tb.set_fontsize(7.4)
    tb.scale(1, 1.35)
    for (r, c), cel in tb.get_celld().items():
        cel.set_edgecolor("0.8")
        if r == 0:
            cel.set_facecolor("#e8eef5")
            cel.set_text_props(weight="bold")
    ax.set_title(titulo, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(archivo, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ================================================================ 6. modelo 2D: celdas costeras
def celdas_2d(niveles):
    """Celdas de tierra del dominio 2D (b_central) con cota DSM entre 0,3 m (umbral de «mar») y cada nivel dado."""
    import rasterio
    from rasterio.warp import Resampling, reproject
    ref = rasterio.open(SC / "datos" / "modelo2d" / "b_central" / "calado_max_m.tif")
    act = ref.read(1) != ref.nodata
    src = rasterio.open(GEO / "descargas" / "dem_recortes" / "santa_cruz_dem.tif")
    z = np.full(ref.shape, -9999, "float32")
    reproject(rasterio.band(src, 1), z, src_transform=src.transform, src_crs=src.crs, dst_transform=ref.transform,
              dst_crs=ref.crs, resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    tierra = act & (z > 0.3)
    out = {}
    for n in niveles:
        c = int((tierra & (z <= n)).sum())
        out[n] = {"celdas": c, "ha": round(c * 900 / 1e4, 1)}
    return out


# ================================================================ principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bajar", action="store_true")
    a = ap.parse_args()
    if a.bajar:
        bajar()
    for p in (OUT_M, SC / "datos", SCB / "datos"):
        p.mkdir(parents=True, exist_ok=True)

    # ---------------- lluvia
    s5 = lluvia_5min()
    hin = lluvia_horaria_inamhi()
    h = horaria(s5, hin)
    inv = inventario(s5, hin, h)

    # ---------------- mareas
    res, series = mareas()
    pb, info_pb = baquerizo(series, res)
    pa = series["puerto_ayora"]
    ext_pa_pred = extremos(pa.pred_m)
    ext_pa_obs = extremos(pa.obs_m.interpolate(limit=3).rolling(5, center=True, min_periods=3).mean().dropna())
    ext_pb = extremos(pb.pred_m.dropna())
    ext_pb_est = extremos(pb.est_m.interpolate(limit=3).rolling(5, center=True, min_periods=3).mean().dropna())
    rango_pa = rango_diario(pa.pred_m)
    rango_pb = rango_diario(pb.pred_m.dropna())
    ref_r = rango_pa["2026-09-01":"2026-11-09"]
    p25, p75 = float(ref_r.quantile(0.25)), float(ref_r.quantile(0.75))
    ref_rb = rango_pb["2026-09-01":"2026-11-09"]
    p25b, p75b = float(ref_rb.quantile(0.25)), float(ref_rb.quantile(0.75))
    lun = fases_lunares(INI, FIN_PRED)

    # ---------------- salidas de nivel del mar
    for clave, df in series.items():
        o = df.copy()
        o.insert(0, "fecha_hora_utc6", loc(o.index).strftime("%Y-%m-%d %H:%M"))
        o.insert(0, "fecha_hora_utc", o.index.strftime("%Y-%m-%d %H:%M"))
        o = o[o.index <= pd.Timestamp("2026-11-03", tz="UTC")]
        o.round(3).to_csv(OUT_M / f"nivel_mar_{clave}_10min.csv", index=False)
    o = pb.copy()
    o.insert(0, "fecha_hora_utc6", loc(o.index).strftime("%Y-%m-%d %H:%M"))
    o.insert(0, "fecha_hora_utc", o.index.strftime("%Y-%m-%d %H:%M"))
    o[o.index <= pd.Timestamp("2026-11-03", tz="UTC")].round(3).to_csv(OUT_M / "nivel_mar_puerto_baquerizo_estimado_10min.csv", index=False)
    pd.DataFrame([{"puerto": "Puerto Ayora (predicha)", "fecha_hora_utc6": loc([t])[0].strftime("%Y-%m-%d %H:%M"), "tipo": k, "nivel_m": round(v, 3)}
                  for t, v, k in ext_pa_pred]
                 + [{"puerto": "Puerto Ayora (observada)", "fecha_hora_utc6": loc([t])[0].strftime("%Y-%m-%d %H:%M"), "tipo": k, "nivel_m": round(v, 3)}
                    for t, v, k in ext_pa_obs]
                 + [{"puerto": "Puerto Baquerizo Moreno (estimada)", "fecha_hora_utc6": loc([t])[0].strftime("%Y-%m-%d %H:%M"), "tipo": k, "nivel_m": round(v, 3)}
                    for t, v, k in ext_pb_est]).to_csv(OUT_M / "pleamares_bajamares.csv", index=False)
    pd.DataFrame([{"estacion": res[c]["nombre"], "constituyente": n, "amplitud_m": v} for c in res for n, v in res[c]["constituyentes_m"].items()]
                 ).to_csv(OUT_M / "constituyentes.csv", index=False)

    # ---------------- eventos
    filas_ev = []
    for ev, isla, a0, a1, horas in EVENTOS:
        t0 = pd.Timestamp(a0, tz="UTC") - GAL
        t1 = pd.Timestamp(a1, tz="UTC") - GAL
        ests = [k for k, v in ESTACIONES.items() if v[1] == isla and k not in ("n_glps01",)]
        picos = pico_lluvia(s5, h, ests, t0, t1)
        es_sc = isla == "Santa Cruz"
        ser_obs = pa.obs_m if es_sc else pb.est_m
        ser_pred = pa.pred_m if es_sc else pb.pred_m
        ext = ext_pa_pred if es_sc else ext_pb
        ext_o = ext_pa_obs if es_sc else ext_pb_est
        rg, q25, q75 = (rango_pa, p25, p75) if es_sc else (rango_pb, p25b, p75b)
        momentos = []
        for k, tot, mx, tp, base, cob in picos:
            if tp is not None and mx >= 5:
                momentos.append((f"Pico de lluvia: {ESTACIONES[k][0]}", k, tot, mx, base, cob, tp))
            else:
                filas_ev.append({"isla": isla, "evento": ev, "momento": f"Sin pico relevante: {ESTACIONES[k][0]}", "estacion": ESTACIONES[k][0],
                                 "lluvia_ventana_mm": round(tot, 1), "max_mm": round(mx, 1), "base_max": base,
                                 "cobertura_ventana_pct": round(100 * min(cob, 1), 0), "hora_utc6": ""})
        for lab, hh in horas.items():
            momentos.append((lab, None, None, None, None, None, pd.Timestamp(hh, tz="UTC") - GAL))
        for lab, k, tot, mx, base, cob, tm in momentos:
            tr = tm.round("10min")
            f = fase(tr, ser_pred, ser_obs, ext, rg, q25, q75, ext_o)
            ple, baj = f["pleamar_anterior"], f["bajamar_siguiente"]
            filas_ev.append({
                "isla": isla, "evento": ev, "momento": lab, "estacion": ESTACIONES[k][0] if k else "",
                "lluvia_ventana_mm": round(tot, 1) if tot is not None else "", "max_mm": round(mx, 1) if mx is not None else "",
                "base_max": base or "", "cobertura_ventana_pct": round(100 * min(cob, 1), 0) if cob is not None else "",
                "hora_utc6": loc([tr])[0].strftime("%Y-%m-%d %H:%M"),
                ("nivel_obs_m" if es_sc else "nivel_est_m"): round(float(f["nivel_obs_m"]), 2) if pd.notna(f["nivel_obs_m"]) else "",
                "marea_astronomica_m": round(float(f["marea_pred_m"]), 2),
                "residuo_m": round(float(f["nivel_obs_m"] - f["marea_pred_m"]), 2) if pd.notna(f["nivel_obs_m"]) else "",
                "estado_marea": f["estado"], "rango_marea_25h_m": round(float(f["rango_25h_m"]), 2), "ciclo": f["ciclo"],
                "pleamar_anterior_utc6": loc([ple[0]])[0].strftime("%Y-%m-%d %H:%M") if ple else "",
                "pleamar_anterior_m": round(ple[1], 2) if ple else "",
                "bajamar_siguiente_utc6": loc([baj[0]])[0].strftime("%Y-%m-%d %H:%M") if baj else "",
                "bajamar_siguiente_m": round(baj[1], 2) if baj else "",
                "edad_lunar_dias": round(float(luna(tr)), 1)})
    ev = pd.DataFrame(filas_ev)

    # ---------------- modelo 2D
    t_2d = [pd.Timestamp(x, tz="UTC") - GAL for x in ("2026-10-30 22:00", "2026-10-30 22:15", "2026-10-30 22:30", "2026-10-30 22:34")]
    nivel_2d = {loc([t])[0].strftime("%H:%M"): round(float(pa.obs_m.get(t.round("10min"), np.nan)), 3) for t in t_2d}
    vent = pa.loc[(pa.index >= pd.Timestamp("2026-10-31 02:00", tz="UTC")) & (pa.index <= pd.Timestamp("2026-10-31 06:00", tz="UTC"))]
    niv_max_vent = float(vent.obs_m.max())
    try:
        cel = celdas_2d([0.30, round(niv_max_vent, 2), NIVEL_MAR_2D, 1.0])
    except Exception as e:  # noqa: BLE001
        cel = {"error": type(e).__name__}

    # ---------------- CSV por isla
    hl = h.copy()
    hl["hora_inicio_utc6"] = loc(hl.h).strftime("%Y-%m-%d %H:%M")
    for isla, carpeta, mar, col in (("Santa Cruz", SC, pa, "obs_m"), ("San Cristóbal", SCB, pb, "est_m")):
        ks = [k for k, v in ESTACIONES.items() if v[1] == isla]
        # Las estaciones particulares (Erna, Punta Estrada) se publican con nombre y ubicación por decisión del 2-nov-2026.
        inv[inv.isla == isla].to_csv(carpeta / "datos" / "lluvia_mareas_inventario.csv", index=False)
        x = hl[hl.estacion.isin(ks) & (hl.h >= pd.Timestamp("2026-10-28 06:00", tz="UTC")) & (hl.h < pd.Timestamp("2026-11-03 06:00", tz="UTC"))]
        tab = x.pivot_table(index="hora_inicio_utc6", columns="estacion", values="mm").round(1)
        tab.columns = [ESTACIONES[c][0] + " (mm)" for c in tab.columns]
        m = mar.copy()
        m["hh"] = loc(m.index).floor("h").strftime("%Y-%m-%d %H:%M")
        mh = m.groupby("hh").agg({col: "mean", "pred_m": "mean"}).round(3)
        mh.columns = [("nivel_mar_obs_m" if isla == "Santa Cruz" else "nivel_mar_est_m"), "marea_astronomica_m"]
        tab = tab.join(mh, how="left")
        tab.index.name = "hora_inicio_utc6"
        tab.to_csv(carpeta / "datos" / "lluvia_mareas_horaria.csv")
        # Lluvia diaria (día natural en UTC−6) a partir de la horaria; horas_con_dato = horas con registro (de 24).
        cols = [c for c in tab.columns if c.endswith(" (mm)")]
        dd = tab[cols].copy()
        dd["dia"] = dd.index.str[:10]
        suma = dd.groupby("dia")[cols].sum(min_count=1).round(1)
        n = dd.groupby("dia")[cols].count()
        diaria = (suma.stack().rename("lluvia_mm").to_frame()
                  .join(n.stack().rename("horas_con_dato")).reset_index()
                  .rename(columns={"level_1": "estacion"}))
        diaria["estacion"] = diaria.estacion.str.replace(" (mm)", "", regex=False)
        diaria = diaria[["estacion", "dia", "lluvia_mm", "horas_con_dato"]].sort_values(["estacion", "dia"])
        if isla == "Santa Cruz":   # lluvia de la costa después del corte de IERSE (30-oct 22:00 → 31-oct 03:00)
            m0191 = [c for c in cols if "(M0191)" in c][0]
            v = tab.loc[(tab.index >= "2026-10-30 22:00") & (tab.index < "2026-10-31 03:00"), m0191]
            diaria = pd.concat([diaria, pd.DataFrame([{"estacion": m0191.replace(" (mm)", ""), "dia": "30-oct 22:00 a 31-oct 03:00",
                                                        "lluvia_mm": round(float(v.sum()), 1), "horas_con_dato": int(v.count())}])])
        diaria.to_csv(carpeta / "datos" / "lluvia_mareas_diaria.csv", index=False)
        ev[ev.isla == isla].drop(columns="isla").to_csv(carpeta / "datos" / "lluvia_mareas_eventos.csv", index=False)

    # ---------------- resumen
    resumen = {"generado": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
               "referencia_vertical": "metros sobre el nivel medio del mar 2017–2024 de cada mareógrafo (UHSLC)",
               "estaciones": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in res.items()},
               "puerto_baquerizo": info_pb,
               "sicigia_cuadratura": {"rango_25h_p25_m": round(p25, 3), "rango_25h_p75_m": round(p75, 3)},
               "fases_lunares_aprox": [(loc([t])[0].strftime("%Y-%m-%d %H:%M"), n) for t, n in lun],
               "modelo2d_santa_cruz": {"nivel_fijo_m": NIVEL_MAR_2D, "nivel_observado_m_sobre_nmm": nivel_2d,
                                       "nivel_observado_max_20h_24h_m": round(niv_max_vent, 3),
                                       "celdas_tierra_entre_0,3m_y_nivel": cel}}
    (OUT_M / "resumen_mareas.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str))

    # ---------------- figuras
    fuente_sc = ("Lluvia: IERSE-WSN (Universidad del Azuay), INAMHI M0191 (horaria), Tempest de Punta Estrada. En gris, el corte de transmisión de Los Guayabillos y Santa Rosa; "
                 "en rojo, de la llegada del agua a La Cascada al pico de salida al mar en el modelo 2D (juego b). Nivel del mar: mareógrafo IOC de Puerto Ayora (radar), al cero UHSLC; marea predicha con UTide (UHSLC 2022–sep-2026).")
    figura_serie("Santa Cruz (Puerto Ayora)", h, pa, ["n_glps05", "n_glps09", "M0191", "punta_estrada"], "Puerto Ayora",
                 SC / "figuras" / "mareas_lluvia_28oct_2nov.png",
                 [(("2026-10-30 21:25", "2026-10-31 18:45"), "", "0.6"),
                  (("2026-10-30 20:53", "2026-10-30 22:34"), "La Cascada (2D)", "#d62728")],
                 linea_2d=True, fases=lun, nota=fuente_sc)
    fuente_scb = ("Lluvia: estaciones USFQ-GSC (historial horario del INAMHI hasta el 2-nov; 5 min del GSC desde el 1-nov). Nivel del mar: ESTIMADO, sin mareógrafo en "
                  "San Cristóbal (Puerto Ayora observado trasladado con la onda M2 de Open-Meteo Marine).")
    figura_serie("San Cristóbal (Puerto Baquerizo Moreno)", h, pb, ["M5300", "M5301", "M5302", "M5303", "M0221"], "Puerto Baquerizo Moreno",
                 SCB / "figuras" / "mareas_lluvia_28oct_2nov.png",
                 [(("2026-10-31 08:00", "2026-10-31 12:00"), "Desborde de cañadas («mañana», SNGR)", "#d62728")],
                 fases=lun, nota=fuente_scb)
    for isla, carpeta, colniv in (("Santa Cruz", SC, "nivel_obs_m"), ("San Cristóbal", SCB, "nivel_est_m")):
        x = ev[(ev.isla == isla) & (ev.hora_utc6 != "")].copy()
        x["Evento"] = x.evento
        x["Estación (pico) u hora clave"] = [m.replace("Pico de lluvia: ", "") if m.startswith("Pico") else m for m in x.momento]
        x["Máx. 1 h (mm)"] = [fmt(v, 1).replace(".", ",") if v != "" and pd.notna(v) else "" for v in x.max_mm]
        meses = {"09": "sep", "10": "oct", "11": "nov"}
        x["Hora"] = [f"{int(t[8:10])}-{meses[t[5:7]]} {t[11:]}" for t in x.hora_utc6]
        x["Nivel del mar (m)"] = [f"{v:+.2f}".replace(".", ",") if v != "" and pd.notna(v) else "" for v in x[colniv]]
        x["Estado de la marea"] = x.estado_marea.str.replace(r"(\d)\.(\d)", r"\1,\2", regex=True)
        x["Ciclo"] = x.ciclo
        figura_tabla(x, carpeta / "figuras" / "mareas_tabla_eventos.png",
                     f"{isla}: lluvia y marea en cada evento (hora UTC−6; nivel en m sobre el nivel medio 2017–2024"
                     + ("; observado en Puerto Ayora)" if isla == "Santa Cruz" else "; ESTIMADO para Puerto Baquerizo Moreno)"))
    print(json.dumps({k: v for k, v in resumen.items() if k != "fases_lunares_aprox"}, ensure_ascii=False, indent=1, default=str)[:4000])
    print(inv[["estacion", "desde_utc6", "hasta_utc6", "cobertura_horaria_pct", "hueco_mayor_h", "lluvia_total_periodo_mm"]].to_string())


if __name__ == "__main__":
    sys.exit(main())
