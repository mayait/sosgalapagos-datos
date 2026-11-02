#!/usr/bin/env python3
"""Marea astronómica de Puerto Ayora (Santa Cruz) y Baltra a partir de las series horarias de UHSLC.

1. Ajusta las constantes armónicas con UTide sobre un tramo reciente y continuo (2022 → último dato).
2. Valida fuera de muestra: ajuste hasta jun-2026, prueba en jul–sep-2026.
3. Escribe recolector/mareas_prediccion.json: predicción cada 10 min (cm respecto del nivel medio de
   referencia), pleamares y bajamares, nivel medio de referencia en el cero de UHSLC y la anomalía
   mensual reciente (la señal de El Niño en el nivel del mar).
4. Calcula el desfase entre el cero del mareógrafo IOC (tiempo real) y el de UHSLC, con el tramo en
   que ambos se solapan, para que el recolector exprese el dato en vivo respecto del nivel medio.

Uso, desde clima/:  .venv/bin/python -I scripts/05_mareas.py [--hasta 2027-12-31]
Necesita utide, pandas y, para el desfase IOC, CLIMA_IOC_API en privado/fuentes.env.
"""
import argparse
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import utide

RAIZ = Path(__file__).resolve().parent.parent
UHSLC = RAIZ / "datos" / "uhslc"
SALIDA = RAIZ / "recolector" / "mareas_prediccion.json"
ESTACIONES = {  # código IOC: (id UHSLC, nombre, latitud)
    "sant": (30, "Puerto Ayora (Academy Bay)", -0.7552),
    "balt": (3, "Baltra", -0.4366),
}
REF = ("2017-01-01", "2024-12-31")  # nivel medio de referencia («normal»): 8 años, incluye El Niño 2023
AJUSTE_DESDE = "2022-01-01"


def env(nombre):
    if nombre not in os.environ:
        f = RAIZ / "privado" / "fuentes.env"
        if f.exists():
            for linea in f.read_text().splitlines():
                if linea.startswith(nombre + "="):
                    os.environ[nombre] = linea.split("=", 1)[1].strip()
    return os.environ.get(nombre)


def serie(uid):
    df = pd.read_csv(UHSLC / f"global_hourly_fast_{uid}.csv.gz", skiprows=[1], parse_dates=["time"])
    s = df.set_index("time")["sea_level"].astype(float)
    s[s < -10000] = np.nan
    return s.dropna() / 10.0  # mm → cm


def ajustar(s, lat):
    t = s.index.tz_convert(None).to_pydatetime()
    return utide.solve(t, s.values, lat=lat, method="ols", conf_int="none", trend=False, verbose=False)


def predecir(coef, t):
    return utide.reconstruct(t, coef, verbose=False).h


def extremos(t, h):
    d = np.diff(h)
    idx = np.where((d[:-1] > 0) & (d[1:] <= 0) | (d[:-1] < 0) & (d[1:] >= 0))[0] + 1
    return [(t[i], h[i], "P" if h[i] > h[i - 1] else "B") for i in idx]


def desfase_ioc(cod, s_uhslc):
    """Mediana de (IOC − UHSLC) en el solape de los últimos días con datos UHSLC."""
    api = env("CLIMA_IOC_API")
    if not api:
        return None
    fin = s_uhslc.index.max()
    ini = fin - pd.Timedelta(days=10)
    q = urllib.parse.urlencode({"query": "data", "code": cod, "format": "json",
                                "timestart": ini.strftime("%Y-%m-%dT%H:%M:%S"), "timestop": fin.strftime("%Y-%m-%dT%H:%M:%S")})
    try:
        datos = json.load(urllib.request.urlopen(f"{api}?{q}", timeout=120))
    except Exception as e:
        print("  IOC sin solape:", e)
        return None
    mejores = {}
    for x in datos:
        if x.get("sensor") in ("rad", "ras") and x.get("slevel") is not None:
            mejores.setdefault(x["sensor"], []).append(x)
    res = {}
    for sen, xs in mejores.items():
        o = pd.Series([x["slevel"] * 100 for x in xs], index=pd.to_datetime([x["stime"] for x in xs], utc=True))
        o = o.resample("1h").mean().dropna()
        comun = o.index.intersection(s_uhslc.index)
        if len(comun) > 48 and o.std() > 1:
            dif = (o[comun] - s_uhslc[comun])
            res[sen] = {"desfase_cm": round(float(dif.median()), 1), "dispersion_cm": round(float(dif.std()), 1), "horas": len(comun)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", default="2027-12-31")
    a = ap.parse_args()
    out = {"generado": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "metodo": "UTide (OLS, constituyentes automáticos) sobre series horarias UHSLC fast-delivery; "
                     f"ajuste {AJUSTE_DESDE} → último dato; nivel medio de referencia {REF[0][:4]}–{REF[1][:4]}",
           "paso_min": 10, "estaciones": {}}
    t0 = pd.Timestamp("2026-10-01", tz="UTC")
    tt = pd.date_range(t0, pd.Timestamp(a.hasta, tz="UTC"), freq="10min")
    tpy = tt.tz_convert(None).to_pydatetime()
    for cod, (uid, nombre, lat) in ESTACIONES.items():
        s = serie(uid)
        msl = float(s[REF[0]:REF[1]].mean())
        tramo = s[AJUSTE_DESDE:] - msl
        # validación fuera de muestra
        ent, prueba = tramo[:"2026-06-30"], tramo["2026-07-01":]
        c_val = ajustar(ent, lat)
        tp = prueba.index.tz_convert(None).to_pydatetime()
        resid = prueba.values - predecir(c_val, tp)
        resid_sin_media = resid - pd.Series(resid, index=prueba.index).rolling("3D", center=True).mean().values
        rms = float(np.sqrt(np.nanmean(resid_sin_media ** 2)))
        rango = float(np.percentile(prueba.values, 99) - np.percentile(prueba.values, 1))
        # ajuste final
        coef = ajustar(tramo, lat)
        h = predecir(coef, tpy)
        ext = extremos(tt, h)
        mensual = (s["2022-01":] - msl).resample("MS").mean().round(1)
        print(f"{nombre}: nivel medio ref {msl:.1f} cm (cero UHSLC) · validación jul–sep-2026: RMS {rms:.1f} cm "
              f"sobre un rango de marea de {rango:.0f} cm · anomalía sep-2026 {mensual.iloc[-1]:+.1f} cm")
        consts = sorted(zip(coef.name, coef.A), key=lambda x: -x[1])[:8]
        print("   principales:", ", ".join(f"{n} {A:.1f} cm" for n, A in consts))
        out["estaciones"][cod] = {
            "nombre": nombre, "uhslc_id": uid, "nivel_medio_ref_cm_cero_uhslc": round(msl, 1),
            "validacion": {"rms_cm": round(rms, 1), "rango_marea_cm": round(rango), "periodo": "2026-07 → 2026-09"},
            "constituyentes": {n: round(float(A), 1) for n, A in consts},
            "anomalia_mensual_cm": {k.strftime("%Y-%m"): v for k, v in mensual.items() if pd.notna(v)},
            "ultimo_dato_uhslc": s.index.max().strftime("%Y-%m-%dT%H:%MZ"),
            "ioc": desfase_ioc(cod, s),
            "t0": t0.strftime("%Y-%m-%dT%H:%MZ"),
            "h_cm": [int(round(x)) for x in h],
            "extremos": [[t.strftime("%Y-%m-%dT%H:%MZ"), round(float(v), 1), k] for t, v, k in ext],
        }
        print("   desfase IOC:", out["estaciones"][cod]["ioc"])
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"→ {SALIDA} ({SALIDA.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
