"""Modelos de estacionalidad de la lluvia por estación (series diarias largas).

Para cada serie calcula:
  - climatología mensual de totales: media, p10, mediana, p90 (meses con ≥ 80 % de días);
  - compuesto de años El Niño fuerte (ONI ≥ 1,5): media mensual de jul(Y)–jun(Y+1);
  - probabilidad suavizada (±15 días, circular) de un día con ≥ 1, ≥ 10 y ≥ 25 mm, por semana del año;
  - lluvia en 24 h para periodos de retorno de 2, 5, 10, 25 y 50 años (Gumbel, método de momentos,
    sobre máximos anuales de años con ≥ 80 % de días);
  - totales mensuales del año en curso y del anterior.

Fuentes: FCD (Puerto Ayora desde 1965 y Bellavista 1987–2019, archivos privados), histórico diario del
GSC desde 2015 y los días completos (≥ 20 h) que va acumulando el recolector (p. ej. INAMHI M0191
continúa la serie de Puerto Ayora).
"""
import csv
import datetime as dt
import math
import os
import statistics
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FCD_DIR = Path(os.environ.get("CLIMA_FCD_DIR", AQUI.parent / "datos" / "fcd"))
NINO = [1965, 1972, 1982, 1987, 1991, 1997, 2009, 2015, 2023]  # año de inicio del episodio (ONI ≥ 1,5)
SERIES = [  # id, nombre, isla, operador, altitud, fuentes: (tipo, ref)
    ("puerto-ayora", "Puerto Ayora", "Santa Cruz", "FCD + INAMHI", 6, [("fcd", "climate_puerto-ayora.csv"), ("db", "inamhi/M0191")]),
    ("bellavista", "Bellavista", "Santa Cruz", "FCD", 194, [("fcd", "climate_bellavista.csv")]),
    ("junco", "El Junco", "San Cristóbal", "GSC-USFQ", 548, [("db", "gsc/junco")]),
    ("cerro_alto", "Cerro Alto", "San Cristóbal", "GSC-USFQ", 517, [("db", "gsc/cerro_alto")]),
    ("mirador", "El Mirador", "San Cristóbal", "GSC-USFQ", 387, [("db", "gsc/mirador")]),
    ("merceditas", "Merceditas", "San Cristóbal", "GSC-USFQ", 100, [("db", "gsc/merceditas")]),
]


def _fcd(nombre):
    ruta = FCD_DIR / nombre
    out = {}
    if ruta.exists():
        with open(ruta, newline="") as f:
            for r in csv.DictReader(f):
                try:
                    out[dt.date.fromisoformat(r["observation_date"])] = float(r["precipitation"])
                except (ValueError, KeyError, TypeError):
                    pass
    return out


def _db(con, clave):
    f, e = clave.split("/", 1)
    out = {}
    for d, v in con.execute("SELECT date(ts, '-5 hours'), valor FROM obs WHERE fuente=? AND estacion=? "
                            "AND variable='lluvia_dia_mm' AND valor IS NOT NULL", (f, e)):
        out[dt.date.fromisoformat(d)] = v
    # días completos acumulados por el recolector (día de Galápagos, ≥ 20 h con datos)
    for d, v, h in con.execute("SELECT date(ts, '-6 hours') d, SUM(valor), COUNT(DISTINCT substr(ts,1,13)) "
                               "FROM obs WHERE fuente=? AND estacion=? AND variable='lluvia_mm' GROUP BY d", (f, e)):
        if h >= 20:
            out.setdefault(dt.date.fromisoformat(d), round(v, 1))
    return out


def _pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p
    i = int(k)
    return xs[i] + (xs[min(i + 1, len(xs) - 1)] - xs[i]) * (k - i)


def _modelo(dias):
    if len(dias) < 365:
        return None
    meses = {}
    for d, v in dias.items():
        meses.setdefault((d.year, d.month), []).append(v)
    tot = {k: sum(v) for k, v in meses.items()
           if len(v) >= 0.8 * (dt.date(k[0] + k[1] // 12, k[1] % 12 + 1, 1) - dt.date(k[0], k[1], 1)).days}
    mensual = []
    for m in range(1, 13):
        xs = [v for (y, mm), v in tot.items() if mm == m]
        mensual.append({"mes": m, "n": len(xs), "media": round(statistics.mean(xs), 1) if xs else None,
                        "p10": round(_pct(xs, .1), 1) if xs else None, "p50": round(_pct(xs, .5), 1) if xs else None,
                        "p90": round(_pct(xs, .9), 1) if xs else None})
    nino = []
    for m in range(1, 13):
        xs = [tot[(y + (1 if m <= 6 else 0), m)] for y in NINO if (y + (1 if m <= 6 else 0), m) in tot]
        nino.append(round(statistics.mean(xs), 1) if xs else None)
    # probabilidad por día del año, suavizada ±15 días
    por_doy = [[] for _ in range(366)]
    for d, v in dias.items():
        por_doy[min(d.timetuple().tm_yday, 365) - 1].append(v)
    prob = {}
    for u in (1, 10, 25):
        semanal = []
        for w in range(52):
            centro = w * 7 + 3
            xs = [v for k in range(centro - 15, centro + 16) for v in por_doy[k % 365]]
            semanal.append(round(sum(x >= u for x in xs) / len(xs), 4) if xs else None)
        prob[str(u)] = semanal
    # máximos anuales y Gumbel
    anios = {}
    for d, v in dias.items():
        anios.setdefault(d.year, []).append(v)
    maximos = {y: max(v) for y, v in anios.items() if len(v) >= 0.8 * 365}
    retorno = None
    if len(maximos) >= 8:
        xs = list(maximos.values())
        beta = statistics.stdev(xs) * math.sqrt(6) / math.pi
        mu = statistics.mean(xs) - 0.5772 * beta
        retorno = {str(T): round(mu - beta * math.log(-math.log(1 - 1 / T)), 0) for T in (2, 5, 10, 25, 50)}
    hoy = dt.date.today()
    actual = {str(y): [round(tot[(y, m)], 1) if (y, m) in tot else (round(sum(meses[(y, m)]), 1) if (y, m) in meses else None)
                       for m in range(1, 13)] for y in (hoy.year - 1, hoy.year)}
    completo = {str(y): [(y, m) in tot for m in range(1, 13)] for y in (hoy.year - 1, hoy.year)}
    top = sorted(maximos.items(), key=lambda x: -x[1])[:5]
    return {"desde": min(dias).isoformat(), "hasta": max(dias).isoformat(), "dias": len(dias),
            "anios_completos": len(maximos), "mensual": mensual, "nino": nino, "nino_anios": NINO,
            "prob_semanal": prob, "retorno_24h": retorno, "max_anual_top": [[y, round(v, 1)] for y, v in top],
            "anios": actual, "mes_completo": completo}


def calcular(con):
    out = []
    for sid, nombre, isla, operador, alt, fuentes in SERIES:
        dias = {}
        for tipo, ref in fuentes:
            datos = _fcd(ref) if tipo == "fcd" else _db(con, ref)
            for d, v in datos.items():
                dias.setdefault(d, v)  # la primera fuente manda; las siguientes rellenan
        m = _modelo(dias)
        if m:
            out.append({"id": sid, "nombre": nombre, "isla": isla, "operador": operador, "altitud_m": alt, **m})
    return {"generado": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "series": out}
