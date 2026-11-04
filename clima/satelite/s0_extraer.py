"""Fase S0 · extrae de GOES-19 los recortes necesarios para la evaluación.

Guarda en satelite/cache/ (no versionado) solo recortes pequeños:
- c13/AAAAMMDDHHMM.npz    temperatura de brillo de la banda 13 (K) en la región de análisis
- rrqpe/AAAAMMDDHHMM.npz  tasa de lluvia RRQPE (mm/h) en la misma región
- glm/AAAAMMDDHH.npz      destellos del GLM en una caja amplia, con cuántos archivos se leyeron

Uso (desde clima/):
  .venv/bin/python -I satelite/s0_extraer.py --eventos            # los 3 eventos de referencia
  .venv/bin/python -I satelite/s0_extraer.py --dias 2026-05-03 ... --abi-cada 20 --glm-cada 3

Es reanudable: no vuelve a pedir lo que ya está en la caché.
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goes  # noqa: E402

CACHE = Path(__file__).resolve().parent / "cache"

# Región de análisis ABI: Santa Cruz con ~55 km de margen (cubre los bbox de zonas_geo.json
# de Santa Cruz y sus anillos de 25 y 50 km).
REGION_ABI = [-90.95, -1.22, -89.75, -0.12]
# Caja amplia para los rayos (sistemas que se acercan): ~2° alrededor de Santa Cruz.
REGION_GLM = [-92.5, -2.5, -88.0, 1.5]

# Ventanas de los eventos de referencia (UTC). Las horas pico vienen de las estaciones
# (IERSE en UTC−6, INAMHI en UTC−5; aquí todo convertido a UTC).
EVENTOS = {
    "2026-10-30": ("2026-10-30T06:00", "2026-10-31T10:00"),
    "2026-10-23": ("2026-10-22T22:00", "2026-10-23T16:00"),
    "2026-10-03": ("2026-10-03T06:00", "2026-10-04T06:00"),
}


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def horas(ini: datetime, fin: datetime):
    h = ini.replace(minute=0, second=0, microsecond=0)
    while h < fin:
        yield h
        h += timedelta(hours=1)


def _indice20(t: datetime) -> int:
    """Número del archivo GLM de 20 s dentro de la hora (0–179)."""
    return t.minute * 3 + t.second // 20


def _tarea_abi(producto: str, clave: str, tamano: int, destino: str) -> tuple[str, int]:
    r = goes.leer_abi(producto, clave, tamano, REGION_ABI)
    np.savez_compressed(destino, datos=r["datos"].astype("float32"),
                        lat=r["lat"].astype("float32"), lon=r["lon"].astype("float32"),
                        inicio=r["inicio"].isoformat())
    return destino, r["bytes"]


def _tarea_glm(hora_iso: str, archivos: list, esperados: int, destino: str) -> tuple[str, int]:
    lat, lon, t, e = [], [], [], []
    bajado = 0
    leidos = 0
    for clave, tamano in archivos:
        try:
            g = goes.leer_glm(clave, tamano, REGION_GLM)
        except Exception as ex:  # archivo dañado o corte puntual: se cuenta como no leído
            print(f"  GLM falló {clave}: {ex}", flush=True)
            continue
        leidos += 1
        bajado += g["bytes"]
        base = g["base"].timestamp()
        lat.append(g["lat"]); lon.append(g["lon"]); e.append(g["energia"])
        t.append(base + g["dt"])
    cat = (lambda xs: np.concatenate(xs) if xs else np.array([]))
    np.savez_compressed(destino, lat=cat(lat).astype("float32"), lon=cat(lon).astype("float32"),
                        t=cat(t), energia=cat(e).astype("float32"),
                        leidos=leidos, esperados=esperados, hora=hora_iso)
    return destino, bajado


def extraer(ini: datetime, fin: datetime, abi_cada: int = 10, glm_cada: int = 1,
            trabajadores: int = 10, productos=("c13", "rrqpe", "glm")) -> None:
    for p in ("c13", "rrqpe", "glm"):
        (CACHE / p).mkdir(parents=True, exist_ok=True)
    tareas = []
    for h in horas(ini, fin):
        for p in ("c13", "rrqpe"):
            if p not in productos:
                continue
            try:
                lista = goes.listar(p, h)
            except Exception as ex:
                print(f"  listar {p} {h:%Y-%m-%d %H}Z falló: {ex}", flush=True)
                continue
            for clave, tam in lista:
                t0 = goes.inicio_de(clave)
                if t0 < ini or t0 >= fin or t0.minute % abi_cada:
                    continue
                dest = CACHE / p / f"{t0:%Y%m%d%H%M}.npz"
                if not dest.exists():
                    tareas.append(("abi", p, clave, tam, str(dest)))
        if "glm" in productos:
            hecho_h = CACHE / "glm" / f"{h:%Y%m%d%H}.npz"  # formato antiguo (una hora por archivo)
            if hecho_h.exists():
                with np.load(hecho_h) as z:
                    if int(z["esperados"]) >= 180 // glm_cada:
                        continue
            try:
                lista = goes.listar("glm", h)
            except Exception as ex:
                print(f"  listar glm {h:%Y-%m-%d %H}Z falló: {ex}", flush=True)
                continue
            # 30 archivos de 20 s por intervalo de 10 min; con glm_cada=3 se lee uno por minuto
            for m in range(0, 60, 10):
                b = h.replace(minute=m)
                if b < ini or b >= fin:
                    continue
                dest = CACHE / "glm" / f"{b:%Y%m%d%H%M}.npz"
                if dest.exists():
                    with np.load(dest) as z:
                        if int(z["esperados"]) >= 30 // glm_cada:
                            continue
                elegidos = [x for x in lista if b <= goes.inicio_de(x[0]) < b + timedelta(minutes=10)
                            and _indice20(goes.inicio_de(x[0])) % glm_cada == 0]
                tareas.append(("glm", b.isoformat(), elegidos, 30 // glm_cada, str(dest)))

    print(f"{len(tareas)} tareas ({ini:%Y-%m-%d %H:%M} → {fin:%Y-%m-%d %H:%M} UTC)", flush=True)
    total, t_ini, hechas = 0, time.time(), 0
    with ProcessPoolExecutor(trabajadores) as ex:
        futs = []
        for t in tareas:
            if t[0] == "abi":
                futs.append(ex.submit(_tarea_abi, *t[1:]))
            else:
                futs.append(ex.submit(_tarea_glm, *t[1:]))
        for f in as_completed(futs):
            try:
                _, b = f.result()
                total += b
            except Exception as e:
                print(f"  tarea falló: {e}", flush=True)
            hechas += 1
            if hechas % 25 == 0 or hechas == len(futs):
                dt = time.time() - t_ini
                print(f"  {hechas}/{len(futs)} · {total / 1e6:.0f} MB · {total / 1e6 / max(dt, 1):.2f} MB/s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eventos", action="store_true", help="los eventos de referencia")
    ap.add_argument("--dias", nargs="*", default=[], help="días completos (UTC) AAAA-MM-DD")
    ap.add_argument("--abi-cada", type=int, default=10, help="minutos entre imágenes ABI (10, 20, 30)")
    ap.add_argument("--glm-cada", type=int, default=1, help="1 = todos los archivos GLM; 3 = uno por minuto")
    ap.add_argument("--trabajadores", type=int, default=10)
    a = ap.parse_args()
    if a.eventos:
        for nombre, (i, f) in EVENTOS.items():
            print(f"== evento {nombre}", flush=True)
            extraer(_utc(i), _utc(f), 10, 1, a.trabajadores)
    for d in a.dias:
        print(f"== día {d}", flush=True)
        i = _utc(d + "T00:00")
        extraer(i, i + timedelta(days=1), a.abi_cada, a.glm_cada, a.trabajadores)


if __name__ == "__main__":
    main()
