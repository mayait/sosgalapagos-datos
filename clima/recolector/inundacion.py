"""Nivel PRELIMINAR de inundación por zona (regla v0.2 de umbrales_inundacion.json).

R_v = máx. sobre las estaciones válidas de (peso × lluvia en la ventana v), v ∈ {1 h, 3 h, 24 h}.
Una estación es válida si tiene ≥ 80 % de cobertura en las ventanas cortas (1 h y 3 h) y no marca
0 mm en 3 h mientras otra válida marca ≥ 10 mm (pluviómetro obstruido). Con suelo húmedo (lluvia
de los 5 días previos > 53 mm) los umbrales bajan un 20 %. El nivel se mantiene 8 h. Si las
estaciones callan cuando el nivel era «alto» o más en las últimas 8 h, el nivel pasa a «muy alto»
(silencio en alerta = alarma). Sin estaciones válidas ni alerta previa: «sin datos», nunca «bajo».
"""
import bisect
import datetime as dt
import json
from pathlib import Path

UTC = dt.timezone.utc
REGLA = json.loads((Path(__file__).resolve().parent / "umbrales_inundacion.json").read_text())
PASO_MIN = {"ierse": 5, "gsc": 5, "inamhi": 5, "weatherlink": 5, "tempest": 5}  # resolución esperada por fuente


def _serie(con, clave, desde):
    f, e = clave.split("/", 1)
    filas = con.execute("SELECT ts, valor FROM obs WHERE fuente=? AND estacion=? AND variable='lluvia_mm' "
                        "AND ts>=? ORDER BY ts", (f, e, desde.strftime("%Y-%m-%dT%H:%M:%SZ"))).fetchall()
    ts_l, cs, cn = [], [0.0], [0]
    for ts, v in filas:
        ts_l.append(dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
        horaria = f == "inamhi" and ts[17:19] == "30"  # fila horaria de respaldo (cuenta como 12 registros)
        cs.append(cs[-1] + (v or 0.0))
        cn.append(cn[-1] + (12 if horaria else 1))
    return f, (ts_l, cs, cn) if ts_l else None


def _ventana(serie, fin, horas, paso):
    ts_l, cs, cn = serie
    a = bisect.bisect_right(ts_l, (fin - dt.timedelta(hours=horas)).timestamp())
    b = bisect.bisect_right(ts_l, fin.timestamp())
    return cs[b] - cs[a], min(1.0, (cn[b] - cn[a]) / (horas * 60 / paso))


def _nivel(R, factor):
    for nv in REGLA["niveles"][:-1]:
        if any(R.get(k) is not None and R[k] >= u * factor for k, u in nv["si_alguno"].items()):
            return nv
    return REGLA["niveles"][-1]


def _evaluar(series, zona, fin, nombres):
    cob_min = REGLA["cobertura_minima"]
    detalle, cand = [], {}
    for clave, peso in zona["estaciones"]:
        if clave not in series:
            detalle.append({"estacion": nombres.get(clave, clave), "usada": False, "motivo": "sin datos"})
            continue
        f, s = series[clave]
        paso = PASO_MIN.get(f, 5)
        v = {k: _ventana(s, fin, h, paso) for k, h in (("R1h", 1), ("R3h", 3), ("R24h", 24))}
        p5 = _ventana(s, fin - dt.timedelta(hours=24), 120, paso)
        cand[clave] = (peso, v, p5)
    cortas = REGLA.get("cobertura_ventanas", ["R1h", "R3h", "R24h"])
    cob = lambda v: min(v[k][1] for k in cortas)  # noqa: E731
    validas = {c: x for c, x in cand.items() if cob(x[1]) >= cob_min}
    otros3h = {c: x[1]["R3h"][0] for c, x in validas.items()}
    for c in list(validas):
        if otros3h[c] == 0 and any(o >= REGLA["excluir_cero_si_otra_mm_3h"] for k, o in otros3h.items() if k != c):
            validas.pop(c)
    for c, (peso, v, p5) in cand.items():
        motivo = None if c in validas else (
            "cobertura menor del 80 % en la última hora o 3 h" if cob(v) < cob_min
            else "marca 0 mm mientras otra estación registra lluvia")
        detalle.append({"estacion": nombres.get(c, c), "peso": peso, "usada": c in validas, "motivo": motivo,
                        "mm": {k: round(x[0], 1) for k, x in v.items()}})
    if not validas:
        return None, {}, None, detalle
    R = {k: round(max(p * v[k][0] for p, v, _ in validas.values()), 1) for k in ("R1h", "R3h", "R24h")}
    p5 = [p * x[0] for p, _, x in validas.values() if x[1] >= cob_min]
    P5d = round(max(p5), 1) if p5 else None
    ha = REGLA["humedad_antecedente"]
    if P5d is None:
        amc, factor = "desconocida", ha["normal"]["factor"]
    elif P5d < ha["seco"]["max"]:
        amc, factor = "seca", ha["seco"]["factor"]
    elif P5d > ha["humedo"]["min"]:
        amc, factor = "húmeda", ha["humedo"]["factor"]
    else:
        amc, factor = "normal", ha["normal"]["factor"]
    return _nivel(R, factor), R, (P5d, amc, factor), detalle


def _recoleccion_viva(con):
    """Para cada fuente, horas (UTC, 'AAAA-MM-DDTHH') en que el recolector la consultó con éxito."""
    vivas = {}
    for f, ts in con.execute("SELECT fuente, ts FROM corridas WHERE ok=1"):
        vivas.setdefault(f, set()).add(ts[:13])
    return vivas


def calcular(con, ahora=None, recoleccion_ok=None):
    """recoleccion_ok(fuente, t) -> bool. Por defecto, según la tabla de corridas: el silencio de una
    estación solo escala el nivel si el recolector consultó su fuente con éxito en ese momento (si
    falló nuestra recolección, no es un silencio de la estación)."""
    ahora = ahora or dt.datetime.now(UTC)
    if recoleccion_ok is None:
        vivas = _recoleccion_viva(con)

        def recoleccion_ok(fuente, t):
            hs = vivas.get(fuente, set())
            return any((t - dt.timedelta(minutes=m)).strftime("%Y-%m-%dT%H") in hs for m in (0, 15))
    nombres = {f"{f}/{e}": n for f, e, n in con.execute("SELECT fuente, estacion, nombre FROM estaciones")}
    desde = ahora - dt.timedelta(hours=72 + 24 + 120 + 1)
    claves = {c for z in REGLA["zonas"] for c, _ in z["estaciones"]}
    series = {}
    for c in claves:
        f, s = _serie(con, c, desde)
        if s:
            series[c] = (f, s)
    orden = [n["nivel"] for n in REGLA["niveles"]]  # de mayor a menor
    info_n = {n["nivel"]: n for n in REGLA["niveles"]}
    pers, sil = REGLA["persistencia_horas"], REGLA.get("silencio_en_alerta")
    alerta = orden[:orden.index(sil["desde_nivel"]) + 1] if sil else []

    def aplicar(inst, previos, fuentes_ok=True):
        """Nivel mostrado a partir del instantáneo y de los instantáneos de las horas previas."""
        recientes = [x for x in previos[-pers:] if x]
        if inst is None:
            if sil and fuentes_ok and any(x in alerta for x in recientes):
                return sil["nivel"], True
            return (min(recientes, key=orden.index), False) if recientes else (None, False)
        return min(recientes + [inst], key=orden.index), False

    zonas = []
    for z in REGLA["zonas"]:
        # instantáneos horarios de las últimas 72 + 8 h (para la persistencia y el gráfico)
        fin0 = ahora.replace(minute=0, second=0, microsecond=0)
        inst = []
        for h in range(72 + pers - 1, -1, -1):
            nv, *_ = _evaluar(series, z, fin0 - dt.timedelta(hours=h), nombres)
            inst.append(nv["nivel"] if nv else None)
        fuentes = {c.split("/")[0] for c, _ in z["estaciones"]}
        ok = lambda t: bool(fuentes) and all(recoleccion_ok(f, t) for f in fuentes)  # noqa: E731
        hist = [aplicar(inst[i], inst[i - pers:i], ok(fin0 - dt.timedelta(hours=len(inst) - 1 - i)))[0]
                for i in range(pers, len(inst))]
        nv, R, ant, detalle = _evaluar(series, z, ahora, nombres)
        actual = nv["nivel"] if nv else None
        nivel, silencio = aplicar(actual, inst, ok(ahora))
        if actual is None and not ok(ahora) and nivel:
            nivel = None  # fallo de nuestra recolección: se informa «sin datos» con el último nivel
        ultimo = next((x for x in reversed(inst) if x), None)
        info = info_n.get(nivel)
        zonas.append({"id": z["id"], "zona": z["zona"], "isla": z["isla"], "calibrada": z["calibrada"], "nota": z["nota"],
                      "nivel": nivel or "sin datos", "nivel_instantaneo": actual, "silencio": silencio,
                      "ultimo_nivel": ultimo if actual is None else None,
                      "color": info["color"] if info else "#6b6a64",
                      "probabilidad": info["probabilidad"] if info else None,
                      "R": R, "P5d": ant[0] if ant else None, "humedad": ant[1] if ant else None,
                      "factor": ant[2] if ant else None, "estaciones": detalle,
                      "historial_72h": hist})
    umbrales = [{"nivel": n["nivel"], "color": n["color"], "prob": n["probabilidad"], **n.get("si_alguno", {})}
                for n in REGLA["niveles"]]
    return {"version": REGLA["version"], "advertencia": REGLA["advertencia"], "umbrales": umbrales,
            "persistencia_horas": pers, "zonas": zonas, "calculado": ahora.strftime("%Y-%m-%dT%H:%M:%SZ")}
