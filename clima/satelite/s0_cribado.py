"""Fase S0 · cribado horario y refinamiento a 10 min para medir la vigilancia v1 en periodos largos.

Bajar la banda 13 y RRQPE cada 10 min durante meses no cabe en un enlace de ~1 MB/s (~40 GB).
La regla v1 solo puede dispararse con topes de nube muy fríos: ≥ 10 % de la zona por debajo de 221 K,
o RRQPE ≥ 10 mm/h, que es un producto infrarrojo y exige topes fríos. Por eso:

1. Se mira la banda 13 cada hora (imagen de las HH:00, ya en cache/c13).
2. Cada hora con Tb mínima < 235 K a menos de 50 km de las zonas de Santa Cruz es candidata.
3. Alrededor de cada candidata (±60 min) se baja la banda 13 y RRQPE cada 10 min.

Fuera de esas ventanas se supone que la v1 no se dispara: ninguna imagen horaria tenía topes fríos
cerca. Uso (desde clima/):
  .venv/bin/python -I satelite/s0_cribado.py --desde 2026-01-01 --hasta 2026-05-01
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from s0_extraer import CACHE, extraer  # noqa: E402

UMBRAL_K = 235.0
MARGEN_KM = 50
VENTANA = timedelta(minutes=60)


def caja_santa_cruz() -> list[float]:
    z = json.loads((AQUI.parent / "recolector" / "zonas_geo.json").read_text())["zonas"]
    bb = [min(z[k]["bbox"][0] for k in ("la-cascada", "santa-cruz-alta")),
          min(z[k]["bbox"][1] for k in ("la-cascada", "santa-cruz-alta")),
          max(z[k]["bbox"][2] for k in ("la-cascada", "santa-cruz-alta")),
          max(z[k]["bbox"][3] for k in ("la-cascada", "santa-cruz-alta"))]
    g = MARGEN_KM / 111.0
    return [bb[0] - g, bb[1] - g, bb[2] + g, bb[3] + g]


def candidatas(desde: datetime, hasta: datetime) -> tuple[list[datetime], int]:
    bb = caja_santa_cruz()
    horas, revisadas = [], 0
    for a in sorted((CACHE / "c13").glob("*.npz")):
        t = datetime.strptime(a.stem, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        if t.minute != 0 or not (desde <= t < hasta):
            continue
        with np.load(a) as z:
            d, la, lo = z["datos"], z["lat"], z["lon"]
        if d.shape != la.shape:
            continue
        m = (lo >= bb[0]) & (lo <= bb[2]) & (la >= bb[1]) & (la <= bb[3]) & np.isfinite(d)
        revisadas += 1
        if m.any() and d[m].min() < UMBRAL_K:
            horas.append(t)
    return horas, revisadas


def ventanas(horas: list[datetime]) -> list[tuple[datetime, datetime]]:
    out = []
    for t in horas:
        a, b = t - VENTANA, t + VENTANA + timedelta(minutes=10)
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--trabajadores", type=int, default=16)
    ap.add_argument("--solo-contar", action="store_true")
    a = ap.parse_args()
    d0 = datetime.fromisoformat(a.desde).replace(tzinfo=timezone.utc)
    d1 = datetime.fromisoformat(a.hasta).replace(tzinfo=timezone.utc)
    horas, revisadas = candidatas(d0, d1)
    vs = ventanas(horas)
    total_h = sum((b - a).total_seconds() for a, b in vs) / 3600
    print(f"{revisadas} imágenes horarias · {len(horas)} candidatas (Tb < {UMBRAL_K:.0f} K a {MARGEN_KM} km) · "
          f"{len(vs)} ventanas · {total_h:.0f} h a 10 min", flush=True)
    registro = {"desde": a.desde, "hasta": a.hasta, "imagenes_horarias": revisadas, "candidatas": len(horas),
                "umbral_k": UMBRAL_K, "margen_km": MARGEN_KM,
                "ventanas": [[x.isoformat(), y.isoformat()] for x, y in vs]}
    (CACHE / f"cribado_{a.desde}_{a.hasta}.json").write_text(json.dumps(registro, indent=1))
    if a.solo_contar:
        return
    for x, y in vs:
        extraer(x, y, 10, 1, a.trabajadores, ("c13", "rrqpe"))


if __name__ == "__main__":
    main()
