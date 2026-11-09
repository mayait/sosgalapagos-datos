"""Estaciones marcadas como dañadas a mano (estaciones_danadas.json).

Los datos crudos se siguen guardando; desde la fecha «desde», las variables marcadas no se usan
para el nivel de inundación ni se publican en estado, horario y diario.
"""
import datetime as dt
import json
from pathlib import Path

_RUTA = Path(__file__).resolve().parent / "estaciones_danadas.json"


def _cargar():
    try:
        d = json.loads(_RUTA.read_text())
    except (OSError, ValueError):
        return {}
    out = {}
    for clave, x in d.items():
        if clave.startswith("_") or not isinstance(x, dict) or "desde" not in x:
            continue
        x = dict(x)
        x["desde_dt"] = dt.datetime.fromisoformat(x["desde"].replace("Z", "+00:00"))
        x.setdefault("variables", ["lluvia_mm"])
        out[clave] = x
    return out


DANADAS = _cargar()


def danada(clave, variable="lluvia_mm", cuando=None):
    """Devuelve la marca si la variable de la estación «fuente/estacion» está dañada en `cuando`
    (por defecto, ahora)."""
    x = DANADAS.get(clave)
    if not x or variable not in x["variables"]:
        return None
    if cuando is not None and cuando < x["desde_dt"]:
        return None
    return x


def publica(clave):
    """Marca que se publica en estado.json (sin la fecha interna)."""
    x = DANADAS.get(clave)
    return None if not x else {"desde": x["desde"], "variables": x["variables"], "motivo": x.get("motivo")}
