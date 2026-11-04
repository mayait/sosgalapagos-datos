"""Señal satelital de vigilancia por zona (solo biblioteca estándar).

Lee las series de la fuente 'goes' (las que escribe colector.py) y dice si en los últimos
30 min hay algo que vigilar. Es una ESTIMACIÓN SATELITAL: no cambia por sí sola el nivel de
inundación y no es una alerta oficial. Los umbrales salen de la evaluación S0
(satelite/evaluacion-s0.md) y deben revisarse con más eventos.

series: {variable: [[ts_iso, valor], ...]} en orden de ts (las últimas 3 h, como en satelite.json).
La vigilancia se mantiene PERSISTENCIA_H horas después del último disparo; cada motivo dice si sigue
activo («ahora») o cuándo fue su último disparo («ts»).
"""
from __future__ import annotations

import datetime as dt

UMBRALES = {
    # variable: (umbral, texto). Cualquiera activa la vigilancia (regla «v1» de evaluacion-s0.md §6).
    # El 30-oct, RRQPE a 25 km adelantó el «medio» 90–100 min y los topes fríos en la parte alta, 180–200 min.
    # Ninguna se activó en 14 días secos o moderados de la muestra. Ninguna ve la lluvia orográfica «cálida».
    "lluvia_sat_max_mmh_25km": (10, "lluvia estimada por el satélite de 10 mm/h o más a menos de 25 km"),
    "frio_pct": (10, "topes de nube por debajo de −52 °C (convección profunda) en el 10 % de la zona o más"),
    "rayos_n_25km": (1, "al menos un rayo a menos de 25 km en 30 min"),
}
VENTANA_MIN = 30
VIGENCIA_MIN = 25    # sin datos más recientes que esto, «sin datos»
PERSISTENCIA_H = 3   # la vigilancia se mantiene 3 h después del último disparo


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _disparos(series: dict, var: str, umbral: float) -> list[tuple[dt.datetime, float]]:
    """(ts, valor) de los momentos en que la variable pasa el umbral (rayos: suma de 30 min)."""
    pts = [(_t(t), v) for t, v in series.get(var, []) if v is not None]
    out = []
    for i, (t, v) in enumerate(pts):
        if var.startswith("rayos"):
            v = sum(x for tt, x in pts[max(0, i - 2):i + 1] if t - tt < dt.timedelta(minutes=VENTANA_MIN))
        if v >= umbral:
            out.append((t, v))
    return out


def evaluar(series: dict, ahora: dt.datetime | None = None) -> dict:
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    pasados = [_t(t) for var in UMBRALES for t, v in series.get(var, []) if v is not None and _t(t) <= ahora]
    if not pasados or ahora - max(pasados) > dt.timedelta(minutes=VIGENCIA_MIN + 10):
        return {"estado": "sin datos", "motivos": []}
    motivos, ultimos = [], []
    for var, (umbral, texto) in UMBRALES.items():
        d = [(t, v) for t, v in _disparos(series, var, umbral)
             if dt.timedelta(0) <= ahora - t <= dt.timedelta(hours=PERSISTENCIA_H)]
        if not d:
            continue
        t, v = d[-1]
        ultimos.append(t)
        reciente = ahora - t <= dt.timedelta(minutes=VENTANA_MIN + 10)
        motivos.append({"variable": var, "valor": round(v, 1), "umbral": umbral, "texto": texto,
                        "ts": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "ahora": reciente})
    if not motivos:
        return {"estado": "sin señal", "motivos": []}
    return {"estado": "vigilancia", "motivos": motivos,
            "ultimo_disparo": max(ultimos).strftime("%Y-%m-%dT%H:%M:%SZ")}
