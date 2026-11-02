#!/usr/bin/env python3
"""Lluvias del 15-oct al 2-nov-2026 en San Cristóbal: resumen de modelos (de script 15)
y tiempo presente observado en los METAR del aeropuerto de San Cristóbal (SEST) y de
Baltra (SEGS), descargados del archivo ASOS/METAR de Iowa Environmental Mesonet.

Los METAR de Ecuador no reportan cantidad de lluvia (p01i siempre 0): solo sirven para
saber CUÁNDO llovió y con qué intensidad cualitativa (-RA, RA, +RA) y visibilidad.
Los aeropuertos solo emiten METAR en horario diurno (~08:00-16:00 hora de Galápagos).

Uso, desde geodatos/:  .venv/bin/python -I scripts/17_lluvias_san_cristobal.py
"""
import re
import urllib.request
from pathlib import Path

import pandas as pd

GEO = Path(__file__).resolve().parent.parent
OUT = GEO / "estudios" / "san-cristobal" / "datos" / "lluvias"
METAR = OUT / "crudo" / "metar_SEST_SEGS_20261015_20261103.csv"
URL = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=SEST&station=SEGS&data=all"
       "&year1=2026&month1=10&day1=15&year2=2026&month2=11&day2=3&tz=Pacific%2FGalapagos&format=onlycomma"
       "&latlon=yes&elev=yes&missing=M&trace=T&direct=no&report_type=3&report_type=4")
INTENS = {"+": "fuerte", "-": "débil", "": "moderada"}


def main():
    if not METAR.exists():
        with urllib.request.urlopen(URL, timeout=120) as r:
            METAR.write_bytes(r.read())
    m = pd.read_csv(METAR)
    m["hora_local"] = pd.to_datetime(m.valid)
    filas = []
    for _, r in m.iterrows():
        cuerpo = r.metar.split(" RMK")[0]
        fen = re.findall(r"\s((?:\+|-)?(?:TS)?(?:SH)?(?:RA|DZ)+)\b", cuerpo)
        vis = re.search(r"\s(\d{4})\s", cuerpo)
        vc = "VCSH" in cuerpo or "VCTS" in cuerpo
        if fen or vc:
            f = fen[0] if fen else ""
            filas.append({"aeropuerto": r.station, "hora_local": r.hora_local, "fenomeno": f or "VCSH",
                          "intensidad": INTENS[f[0] if f[:1] in "+-" else ""] if f else "chubasco en las cercanías",
                          "visibilidad_m": int(vis.group(1)) if vis else None, "metar": r.metar})
    t = pd.DataFrame(filas)
    t.to_csv(OUT / "metar_lluvia_observada.csv", index=False, date_format="%Y-%m-%dT%H:%M")
    n = m.groupby([m.station, m.hora_local.dt.date]).size().unstack(0)
    print(n.tail(5))
    print(t[t.hora_local >= "2026-10-29"][["aeropuerto", "hora_local", "fenomeno", "visibilidad_m"]].to_string())

    # Resumen de modelos por punto (de 15_lluvias_openmeteo.py), hora de Galápagos
    d = pd.read_csv(OUT / "modelos_diaria.csv")
    h = pd.read_csv(OUT / "modelos_horaria.csv", parse_dates=["fecha_hora_local_fin"])
    c = pd.read_csv(OUT / "modelos_celdas.csv")
    piv = d.pivot_table(index=["punto", "modelo"], columns="fecha", values="mm")
    res = pd.DataFrame({
        "15_27oct": piv.loc[:, "2026-10-15":"2026-10-27"].sum(axis=1),
        "28_29oct": piv.loc[:, "2026-10-28":"2026-10-29"].sum(axis=1),
        "30oct": piv["2026-10-30"], "31oct": piv["2026-10-31"], "1nov": piv["2026-11-01"],
        "total_15oct_1nov": piv.sum(axis=1)}).round(1)
    hm = h[(h.fecha_hora_local_fin > "2026-10-30") & (h.fecha_hora_local_fin <= "2026-11-01")]
    mx = hm.loc[hm.groupby(["punto", "modelo"]).mm.idxmax()].set_index(["punto", "modelo"])
    res["max_1h_30_31oct"] = mx.mm
    res["hora_fin_max_1h"] = mx.fecha_hora_local_fin.dt.strftime("%d-%b %H:%M")
    res = res.join(c.set_index(["punto", "modelo"])[["lat_celda", "lon_celda"]])
    res.to_csv(OUT / "resumen_modelos.csv")
    print(res.to_string())


if __name__ == "__main__":
    main()
