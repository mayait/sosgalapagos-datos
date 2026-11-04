"""Señal satelital de vigilancia por zona (solo biblioteca estándar).

Lee las series de la fuente 'goes' (las que escribe colector.py) y dice si en los últimos
30 min hay algo que vigilar. Es una ESTIMACIÓN SATELITAL: no cambia por sí sola el nivel de
inundación y no es una alerta oficial. Los umbrales salen de la evaluación S0
(satelite/evaluacion-s0.md) y deben revisarse con más eventos.

series: {variable: [[ts_iso, valor], ...]} en orden de ts.
"""
from __future__ import annotations

import datetime as dt

UMBRALES = {
    # variable: (umbral, texto). Cualquiera activa la vigilancia.
    "rayos_n_25km": (1, "rayos a menos de 25 km"),
    "frio_pct_25km": (10, "topes de nube muy fríos (convección profunda) cerca"),
    "lluvia_sat_max_mmh": (10, "lluvia satelital intensa sobre la zona"),
}
VENTANA_MIN = 30
VIGENCIA_MIN = 25  # sin datos más recientes que esto, «sin datos»


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def evaluar(series: dict, ahora: dt.datetime | None = None) -> dict:
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    motivos, ultimo = [], None
    for var, (umbral, texto) in UMBRALES.items():
        pts = [(_t(t), v) for t, v in series.get(var, []) if v is not None]
        if pts:
            ultimo = max(ultimo or pts[-1][0], pts[-1][0])
        rec = [v for t, v in pts if ahora - t <= dt.timedelta(minutes=VENTANA_MIN + 10)]
        if var.startswith("rayos"):
            val = sum(rec[-3:]) if rec else None  # 3 intervalos de 10 min = 30 min
        else:
            val = max(rec) if rec else None
        if val is not None and val >= umbral:
            motivos.append({"variable": var, "valor": round(val, 1), "umbral": umbral, "texto": texto})
    if ultimo is None or ahora - ultimo > dt.timedelta(minutes=VIGENCIA_MIN + 10):
        return {"estado": "sin datos", "motivos": motivos}
    return {"estado": "vigilancia" if motivos else "sin señal", "motivos": motivos}
