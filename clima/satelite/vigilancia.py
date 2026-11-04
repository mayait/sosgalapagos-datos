"""Señal satelital de vigilancia por zona (solo biblioteca estándar).

Lee las series de la fuente 'goes' (las que escribe colector.py) y dice si hay convección profunda
cerca de la zona. Es una ESTIMACIÓN SATELITAL: no cambia el nivel de inundación y no es una alerta
oficial. Se probó con UN solo evento convectivo (30-oct-2026), con reglas ajustadas a ese evento:
ver satelite/evaluacion-s0.md. No ve la lluvia orográfica de nubes bajas.

series: {variable: [[ts_iso, valor], ...]} en orden de ts (las últimas 3 h, como en satelite.json).

Estados:
  "vigilancia"   alguna condición se cumplió en las últimas PERSISTENCIA_H horas
  "sin señal"    los dos productos están al día y ninguna condición se cumplió
  "incompleta"   no hay disparo y falta al menos un producto (p. ej., RRQPE detenido por la NOAA):
                 no se puede decir «sin señal»
  "sin datos"    no llega ningún producto
  "sin_evaluar"  zona sin evaluación con lluvia medida: se muestran los datos, no un estado
"""
from __future__ import annotations

import datetime as dt

UMBRALES = {
    # variable: (umbral, producto, texto). Basta con una (regla «v1» de evaluacion-s0.md §6).
    # Los rayos no entran: nunca adelantaron nada y casi no hay en Galápagos.
    "lluvia_sat_max_mmh_25km": (10, "RRQPE", "lluvia estimada por el satélite de 10 mm/h o más a menos de 25 km"),
    "frio_pct": (10, "ABI", "topes de nube por debajo de −52 °C (convección profunda) en el 10 % de la zona o más"),
}
PRODUCTOS = {"ABI": "tb_min_k", "RRQPE": "lluvia_sat_max_mmh"}  # variable que dice si el producto llega
VIGENCIA_MIN = 25    # un producto sin datos más recientes que esto «falta»
PERSISTENCIA_H = 3   # la vigilancia se mantiene 3 h después del último disparo
ZONAS_EVALUADAS = {"la-cascada", "santa-cruz-alta"}


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _ultimo(series: dict, var: str, ahora: dt.datetime) -> dt.datetime | None:
    ts = [_t(t) for t, v in series.get(var, []) if v is not None and _t(t) <= ahora]
    return max(ts) if ts else None


def evaluar(series: dict, ahora: dt.datetime | None = None, zona: str | None = None) -> dict:
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    vigencia = dt.timedelta(minutes=VIGENCIA_MIN + 10)  # +10: el barrido dura 10 min
    llegan = {p: _ultimo(series, v, ahora) for p, v in PRODUCTOS.items()}
    faltan = [p for p, t in llegan.items() if t is None or ahora - t > vigencia]
    base = {"faltan": faltan, "productos_ultimo": {p: _iso(t) if t else None for p, t in llegan.items()}}
    if zona is not None and zona not in ZONAS_EVALUADAS:
        return {"estado": "sin_evaluar", "motivos": [], **base}
    if len(faltan) == len(PRODUCTOS):
        return {"estado": "sin datos", "motivos": [], **base}
    motivos, ultimos = [], []
    for var, (umbral, producto, texto) in UMBRALES.items():
        disparos = [(_t(t), v) for t, v in series.get(var, [])
                    if v is not None and v >= umbral and dt.timedelta(0) <= ahora - _t(t) <= dt.timedelta(hours=PERSISTENCIA_H)]
        if not disparos:
            continue
        t, v = disparos[-1]
        ultimos.append(t)
        motivos.append({"variable": var, "producto": producto, "valor": round(v, 1), "umbral": umbral,
                        "texto": texto, "ultimo_disparo": _iso(t),
                        "activo": ahora - t <= vigencia})  # True: se cumple en la última imagen
    if motivos:
        u = max(ultimos)
        return {"estado": "vigilancia", "motivos": motivos, "ultimo_disparo": _iso(u),
                "vigilancia_hasta": _iso(u + dt.timedelta(hours=PERSISTENCIA_H)), **base}
    return {"estado": "incompleta" if faltan else "sin señal", "motivos": [], **base}
