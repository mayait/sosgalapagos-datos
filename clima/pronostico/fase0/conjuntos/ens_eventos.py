#!/usr/bin/env python3
"""Fase 0 del pronóstico de lluvia: ¿los conjuntos de ECMWF (IFS ENS y AIFS ENS)
anticiparon con 1, 2 y 3 días las lluvias fuertes en Galápagos?

Fuente: datos abiertos de ECMWF (CC BY 4.0; bucket público en AWS, sin clave; endpoint en
CLIMA_ECMWF_S3, privado/fuentes.env). Para cada
corrida 00Z y paso se lee el `.index` (JSON por líneas) y se piden con `Range`
solo los campos `tp` (precipitación total acumulada desde el inicio, en m) de
todos los miembros publicados. Del campo global se guarda en caché solo una caja
alrededor de Galápagos.

Día local de Galápagos (UTC−6): 06Z de D a 06Z de D+1. Con la corrida 00Z de
D−L, el total del día es tp(24L+30) − tp(24L+6).

Uso (con un venv propio que tenga eccodes y numpy):
    .venv/bin/python -I ens_eventos.py --repo /ruta/al/repo [--hilos 8]
Primero descarga (reanudable, caché en ./cache) y luego escribe ens_eventos.csv.
    .venv/bin/python -I ens_eventos.py --repo ... --solo-analisis
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
def _base():
    """Endpoint del archivo abierto de ECMWF: CLIMA_ECMWF_S3 en el entorno o en clima/privado/fuentes.env."""
    import os
    clave = "CLIMA_ECMWF_S3"
    if clave not in os.environ:
        ruta = Path(__file__).resolve().parents[3] / "privado" / "fuentes.env"
        if ruta.exists():
            for linea in ruta.read_text().splitlines():
                if linea.strip().startswith(clave + "="):
                    os.environ[clave] = linea.split("=", 1)[1].strip().strip('"')
    if not os.environ.get(clave):
        raise SystemExit(f"Falta {clave} (privado/fuentes.env)")
    return os.environ[clave]


BASE = None  # se resuelve en main()
CACHE = AQUI / "cache"

# Caja guardada (rejilla 0,25°, lat de 90 a −90, lon empezando en 180°).
LAT_N, LAT_S = 0.0, -1.75
LON_W, LON_E = -91.25, -88.75
J0 = int(round((90 - LAT_N) / 0.25))
J1 = int(round((90 - LAT_S) / 0.25))
I0 = int(round(((LON_W - 180) % 360) / 0.25))
I1 = int(round(((LON_E - 180) % 360) / 0.25))
LATS = 90 - 0.25 * np.arange(J0, J1 + 1)
LONS = LON_W + 0.25 * np.arange(0, I1 - I0 + 1)

PUNTOS = {
    "santa_rosa": (-0.655, -90.404),
    "los_guayabillos": (-0.699, -90.342),
    "puerto_ayora": (-0.743, -90.302),
    "san_cristobal_alta": (-0.887, -89.531),
}

AIFS_ENS_INICIO = dt.date(2025, 7, 2)   # primera corrida en el bucket
IFS_ENS_INICIO = dt.date(2024, 2, 1)    # primera corrida a 0,25°
UMBRALES = (10, 20, 50, 100)
# Unidad de tp en cada producto y factor a mm
UNIDADES = {"ifs": "m", "aifs": "kg m**-2"}
A_MM = {"ifs": 1000.0, "aifs": 1.0}


# --------------------------------------------------------------------------
# Casos
# --------------------------------------------------------------------------
def leer_ierse(repo: Path):
    out = {}
    with open(repo / "clima/datos/ierse-wsn/diario.csv") as f:
        for r in csv.DictReader(f):
            out[(r["fecha"], r["estacion"])] = (float(r["lluvia_mm"]), float(r["cobertura_pct"]))
    return out


def leer_fcd(repo: Path):
    out = {}
    with open(repo / "clima/datos/fcd/climate_puerto-ayora.csv") as f:
        for r in csv.DictReader(f):
            if r["precipitation"] not in ("", None):
                out[r["observation_date"]] = float(r["precipitation"])
    return out


def construir_casos(repo: Path):
    """Lista de (fecha, tipo, grupo, {punto: observado_mm}, anticipaciones)."""
    ierse = leer_ierse(repo)
    fcd = leer_fcd(repo)

    def obs_sc(fecha):
        o = {}
        for p, est in (("santa_rosa", "Santa Rosa"), ("los_guayabillos", "Los Guayabillos")):
            v = ierse.get((fecha, est))
            o[p] = f"{v[0]:.1f} (cob {v[1]:.0f}%)" if v else ""
        return o

    casos = []
    for d in ("2026-10-30", "2026-10-23", "2026-10-03", "2026-06-14"):
        casos.append((d, "evento", "santa_cruz_alta", obs_sc(d), (1, 2, 3)))
    for d in ("2024-02-22", "2024-02-13", "2025-03-26"):
        casos.append((d, "evento", "puerto_ayora", {"puerto_ayora": f"{fcd.get(d, float('nan')):.1f}"}, (1, 2, 3)))
    sc_obs = {"2025-03-08": "124-133", "2026-04-15": "130", "2026-04-17": "128"}
    for d, v in sc_obs.items():
        casos.append((d, "evento", "san_cristobal_alta", {"san_cristobal_alta": v}, (1, 2, 3)))
    eventos = {c[0] for c in casos}

    rng = random.Random(20261103)
    # 15 días secos de 2026 en Santa Rosa (<2 mm, cobertura >= 90 %)
    secos_sr = sorted(
        f for (f, est), (mm, cob) in ierse.items()
        if est == "Santa Rosa" and f.startswith("2026") and mm < 2 and cob >= 90 and f not in eventos
    )
    for d in sorted(rng.sample(secos_sr, 15)):
        mm, cob = ierse[(d, "Santa Rosa")]
        casos.append((d, "seco", "seco_santa_rosa_2026", {"santa_rosa": f"{mm:.1f} (cob {cob:.0f}%)"}, (1,)))
    # 10 días secos de la temporada lluviosa 2025 (ene–may) en Puerto Ayora
    secos_pa = sorted(f for f, mm in fcd.items() if "2025-01-01" <= f <= "2025-05-31" and mm < 2 and f not in eventos)
    for d in sorted(rng.sample(secos_pa, 10)):
        casos.append((d, "seco", "seco_puerto_ayora_2025", {"puerto_ayora": f"{fcd[d]:.1f}"}, (1,)))
    # Extensión: 10 días secos de la temporada lluviosa 2026 en Puerto Ayora,
    # porque AIFS ENS no existe en ene–may 2025.
    secos_pa26 = sorted(f for f, mm in fcd.items() if "2026-01-01" <= f <= "2026-05-31" and mm < 2 and f not in eventos)
    for d in sorted(rng.sample(secos_pa26, 10)):
        casos.append((d, "seco", "seco_puerto_ayora_2026", {"puerto_ayora": f"{fcd[d]:.1f}"}, (1,)))
    return casos


def pasos(lead: int):
    return 24 * lead + 6, 24 * lead + 30


# --------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------
def get(url: str, rango: tuple[int, int] | None = None, intentos: int = 25) -> bytes | None:
    for k in range(intentos):
        req = urllib.request.Request(url)
        if rango:
            req.add_header("Range", f"bytes={rango[0]}-{rango[1]}")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(min(10 * (k + 1), 120) * (0.5 + random.random()))  # S3 responde 503 SlowDown
        except Exception:
            time.sleep(min(10 * (k + 1), 120) * (0.5 + random.random()))  # S3 responde 503 SlowDown
    raise RuntimeError(f"falló {url} {rango}")


def urls(modelo: str, run: dt.date, paso: int):
    d = run.strftime("%Y%m%d")
    nombre = f"{d}000000-{paso}h-enfo"
    if modelo == "ifs":
        return [f"{BASE}/{d}/00z/ifs/0p25/enfo/{nombre}-ef", f"{BASE}/{d}/00z/0p25/enfo/{nombre}-ef"]
    return [f"{BASE}/{d}/00z/aifs-ens/0p25/enfo/{nombre}-cf", f"{BASE}/{d}/00z/aifs-ens/0p25/enfo/{nombre}-pf"]


def ruta_cache(modelo, run, paso):
    return CACHE / modelo / f"{run:%Y%m%d}_{paso:03d}.npz"


def descargar_campo(modelo: str, run: dt.date, paso: int, hilos: int) -> str:
    import eccodes as ec

    dest = ruta_cache(modelo, run, paso)
    if dest.exists():
        return "caché"
    entradas = []
    if modelo == "ifs":
        for base in urls(modelo, run, paso):  # ruta nueva y, si no existe, la de feb-2024
            idx = get(base + ".index")
            if idx is not None:
                entradas = [(base, json.loads(l)) for l in idx.decode().splitlines() if l.strip()]
                break
    else:
        for base in urls(modelo, run, paso):
            idx = get(base + ".index")
            if idx is not None:
                entradas += [(base, json.loads(l)) for l in idx.decode().splitlines() if l.strip()]
    tp = [(b, e) for b, e in entradas if e.get("param") == "tp"]
    if not tp:
        return "sin datos"

    def bajar(b, e):
        raw = get(b + ".grib2", (e["_offset"], e["_offset"] + e["_length"] - 1))
        h = ec.codes_new_from_message(raw)
        try:
            assert ec.codes_get(h, "shortName") == "tp"
            # IFS ENS publica tp en m (paramId 228); AIFS ENS en kg m-2 = mm (paramId 228228).
            unidad = ec.codes_get(h, "units")
            assert unidad == UNIDADES[modelo], (modelo, unidad)
            assert ec.codes_get(h, "startStep") == 0  # acumulado desde el inicio
            ni, nj = ec.codes_get(h, "Ni"), ec.codes_get(h, "Nj")
            assert (ni, nj) == (1440, 721)
            assert ec.codes_get(h, "longitudeOfFirstGridPointInDegrees") == 180.0
            assert ec.codes_get(h, "latitudeOfFirstGridPointInDegrees") == 90.0
            num = int(ec.codes_get(h, "number")) if e.get("type") == "pf" else 0
            v = ec.codes_get_values(h).reshape(nj, ni)[J0:J1 + 1, I0:I1 + 1].astype("float32")
        finally:
            ec.codes_release(h)
        return num, v

    res = []
    with ThreadPoolExecutor(hilos) as ex:
        futs = [ex.submit(bajar, b, e) for b, e in tp]
        for f in as_completed(futs):
            res.append(f.result())
    res.sort(key=lambda t: t[0])
    nums = np.array([r[0] for r in res])
    vals = np.stack([r[1] for r in res])
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f"{dest.stem}.{os.getpid()}.tmp.npz")
    np.savez_compressed(tmp, number=nums, tp=vals)
    tmp.rename(dest)
    return f"{len(nums)} miembros"


def tareas(casos):
    out = []
    for fecha, tipo, grupo, obs, leads in casos:
        D = dt.date.fromisoformat(fecha)
        for L in leads:
            run = D - dt.timedelta(days=L)
            for modelo in ("ifs", "aifs"):
                if modelo == "ifs" and run < IFS_ENS_INICIO:
                    continue
                if modelo == "aifs" and run < AIFS_ENS_INICIO:
                    continue
                for p in pasos(L):
                    t = (0 if tipo == "evento" else 1, modelo, run, p)
                    if t not in out:
                        out.append(t)
    out.sort(key=lambda t: (t[0], t[2], t[1], t[3]))
    return [(m, r, p) for _, m, r, p in out]


# --------------------------------------------------------------------------
# Análisis
# --------------------------------------------------------------------------
def celdas(lat, lon):
    j = int(np.argmin(np.abs(LATS - lat)))
    i = int(np.argmin(np.abs(LONS - lon)))
    return j, i


def stats(x):
    x = np.asarray(x, dtype=float)
    d = {
        "mediana_mm": np.median(x), "p75_mm": np.percentile(x, 75), "p90_mm": np.percentile(x, 90),
        "max_mm": x.max(), "media_mm": x.mean(),
    }
    for u in UMBRALES:
        d[f"frac_gt{u}"] = float(np.mean(x > u))
    return d


def analizar(casos, salida: Path):
    filas = []
    for fecha, tipo, grupo, obs, leads in casos:
        D = dt.date.fromisoformat(fecha)
        for modelo in ("ifs", "aifs"):
            for L in leads:
                run = D - dt.timedelta(days=L)
                p0, p1 = pasos(L)
                base = dict(fecha=fecha, tipo=tipo, grupo=grupo, modelo=f"{modelo}-ens", anticipacion_d=L,
                            corrida=f"{run:%Y-%m-%d} 00Z", pasos=f"{p0}-{p1}")
                f0, f1 = ruta_cache(modelo, run, p0), ruta_cache(modelo, run, p1)
                inicio = IFS_ENS_INICIO if modelo == "ifs" else AIFS_ENS_INICIO
                nota = ""
                if run < inicio:
                    nota = f"sin archivo: {modelo.upper()} ENS empieza {inicio}"
                elif not (f0.exists() and f1.exists()):
                    nota = "sin datos en el bucket"
                if nota:
                    for punto, o in obs.items():
                        filas.append({**base, "punto": punto, "observado_mm": o, "celda": "", "n_miembros": 0, "nota": nota})
                    continue
                a, b = np.load(f0), np.load(f1)
                assert (a["number"] == b["number"]).all()
                dia = (b["tp"] - a["tp"]) * A_MM[modelo]  # a mm
                dia = np.clip(dia, 0, None)  # ruido de empaquetado puede dar −0,2 mm
                for punto, o in obs.items():
                    j, i = celdas(*PUNTOS[punto])
                    cerca = dia[:, j, i]
                    vec = dia[:, max(j - 1, 0):j + 2, max(i - 1, 0):i + 2].reshape(len(dia), -1).max(axis=1)
                    for nombre, x, (cl, co) in (
                        ("cercano", cerca, (LATS[j], LONS[i])),
                        ("vecindad3x3_max", vec, (LATS[j], LONS[i])),
                    ):
                        s = stats(x)
                        filas.append({**base, "punto": punto, "observado_mm": o, "celda": nombre,
                                      "celda_centro": f"{cl:.2f},{co:.2f}", "n_miembros": len(x),
                                      **{k: round(v, 3) if k.startswith("frac") else round(v, 1) for k, v in s.items()},
                                      "nota": ("cf + 50 pf" if 0 in a["number"] else "solo 50 pf (sin cf en el archivo abierto)")})
    campos = ["fecha", "tipo", "grupo", "punto", "observado_mm", "modelo", "anticipacion_d", "corrida", "pasos",
              "celda", "celda_centro", "n_miembros", "mediana_mm", "p75_mm", "p90_mm", "max_mm", "media_mm",
              *[f"frac_gt{u}" for u in UMBRALES], "nota"]
    with open(salida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--hilos", type=int, default=8)
    ap.add_argument("--solo-analisis", action="store_true")
    ap.add_argument("--inverso", action="store_true", help="bajar en orden inverso (para correr un segundo proceso en paralelo)")
    ap.add_argument("--salida", type=Path, default=AQUI / "ens_eventos.csv")
    args = ap.parse_args()

    casos = construir_casos(args.repo)
    with open(AQUI / "casos.json", "w") as f:
        json.dump(casos, f, indent=1, ensure_ascii=False)
    if not args.solo_analisis:
        global BASE
        BASE = _base()
        ts = tareas(casos)
        if args.inverso:
            ts = ts[::-1]
        print(f"{len(ts)} campos (modelo, corrida, paso) por bajar", flush=True)
        for vuelta in range(1, 6):  # S3 a veces corta con 503 SlowDown: se reintenta en otra vuelta
            fallos = 0
            for k, (m, r, p) in enumerate(ts, 1):
                if ruta_cache(m, r, p).exists():
                    continue
                t0 = time.time()
                try:
                    estado = descargar_campo(m, r, p, args.hilos)
                except Exception as e:  # noqa: BLE001
                    estado, fallos = f"FALLÓ ({e})", fallos + 1
                print(f"[v{vuelta} {k}/{len(ts)}] {m} {r} +{p}h: {estado} ({time.time() - t0:.0f} s)", flush=True)
            if not fallos:
                break
            time.sleep(300)
    filas = analizar(casos, args.salida)
    print(f"{len(filas)} filas -> {args.salida}")


if __name__ == "__main__":
    sys.exit(main())
