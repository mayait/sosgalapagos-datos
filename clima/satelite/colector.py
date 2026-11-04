#!/usr/bin/env python3
"""Colector satelital GOES-19 (ABI + GLM) para el dashboard de clima. Una corrida cada 5 min.

Qué hace en cada corrida:
1. ABI (disco completo cada 10 min): para cada barrido nuevo de la banda 13 (temperatura del tope
   de nube) y del producto RRQPE (tasa de lluvia estimada), lee por rangos HTTP solo el recorte de
   Galápagos y guarda agregados por zona en clima.db (tabla obs, fuente='goes').
2. GLM (archivos de 20 s): cuenta los destellos por zona en intervalos de 10 min. Rehace los
   intervalos recientes hasta tener sus 30 archivos.
3. Escribe satelite.json (público y pequeño): últimas 3 h por zona, destellos y núcleos fríos.

Zonas: recolector/zonas_geo.json (los ids son los de umbrales_inundacion.json).
Horas: todo en UTC. ts de ABI = inicio del barrido; ts del GLM = inicio del intervalo de 10 min.

Es una ESTIMACIÓN SATELITAL: no es lluvia medida ni una alerta oficial.

Entorno: CLIMA_DB, CLIMA_SALIDA, CLIMA_SATELITE_DIR (estado propio), CLIMA_GOES_S3 (privado).
Dependencias: numpy y h5py (venv propio; el recolector principal sigue con la biblioteca estándar).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import goes  # noqa: E402
import vigilancia  # noqa: E402

UTC = dt.timezone.utc
DB = Path(os.environ.get("CLIMA_DB", AQUI.parent / "recolector" / "clima.db"))
SALIDA = Path(os.environ.get("CLIMA_SALIDA", AQUI.parent / "recolector" / "salida"))
ESTADO = Path(os.environ.get("CLIMA_SATELITE_DIR", AQUI / "estado-local"))

FUENTE = "goes"
# Recorte ABI: las islas habitadas con ~50 km de margen. Caja de rayos más amplia para ver lo que se acerca.
REGION_ABI = [-91.70, -1.50, -89.00, 0.05]
REGION_GLM = [-93.50, -3.00, -87.50, 2.00]
ANILLO_KM = 25
FRIO_K = 221.0           # tope muy frío: convección profunda (−52 °C)
CELDA_GRADOS = 0.05      # rejilla gruesa (~5,5 km) para el mapa público
HORAS_PUBLICAS = 3
ABI_POR_CORRIDA = 6      # máximo de barridos por producto en una corrida (recuperación tras un corte)
GLM_BINS_POR_CORRIDA = 9

VARIABLES = {  # documentadas en satelite/LEEME.md
    "tb_min_k": "Tb mínima de la banda 13 en la zona (K)",
    "frio_pct": f"% de píxeles de la zona con Tb < {FRIO_K:.0f} K",
    "frio_pct_25km": f"ídem en la zona ampliada {ANILLO_KM} km",
    "lluvia_sat_max_mmh": "RRQPE máxima en la zona (mm/h)",
    "lluvia_sat_media_mmh": "RRQPE media en la zona (mm/h)",
    "lluvia_sat_max_mmh_25km": f"RRQPE máxima en la zona ampliada {ANILLO_KM} km (mm/h)",
    "rayos_n": "destellos GLM en la zona en los 10 min que empiezan en ts",
    "rayos_n_25km": f"ídem en la zona ampliada {ANILLO_KM} km",
}


def zonas() -> dict:
    for p in (AQUI.parent / "recolector" / "zonas_geo.json", AQUI.parent / "zonas_geo.json"):
        if p.exists():
            return json.loads(p.read_text())["zonas"]
    raise SystemExit("No encuentro zonas_geo.json")


def ampliar(b, km):
    g = km / 111.0
    return [b[0] - g, b[1] - g, b[2] + g, b[3] + g]


def dentro(lat, lon, b):
    return (lon >= b[0]) & (lon <= b[2]) & (lat >= b[1]) & (lat <= b[3])


def iso(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def conectar() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS obs (
      fuente TEXT NOT NULL, estacion TEXT NOT NULL, variable TEXT NOT NULL,
      ts TEXT NOT NULL, valor REAL, PRIMARY KEY (fuente, estacion, variable, ts)) WITHOUT ROWID""")
    return con


def guardar(con, filas):
    with con:
        con.executemany("INSERT OR REPLACE INTO obs VALUES (?,?,?,?,?)",
                        [(FUENTE, e, v, t, None if x is None or not np.isfinite(x) else round(float(x), 3))
                         for e, v, t, x in filas])


def leer_estado(nombre, defecto):
    p = ESTADO / nombre
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return defecto


def escribir_json(ruta: Path, obj) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    os.replace(tmp, ruta)


# ---------------------------------------------------------------- ABI

def rejilla(lat, lon, val, modo, umbral):
    """Celdas de CELDA_GRADOS con el mínimo (Tb) o el máximo (lluvia) que pasan el umbral."""
    m = np.isfinite(val) & ((val < umbral) if modo == "min" else (val >= umbral))
    if not m.any():
        return []
    ci = np.floor(lat[m] / CELDA_GRADOS).astype(int)
    cj = np.floor(lon[m] / CELDA_GRADOS).astype(int)
    v = val[m]
    celdas = {}
    for a, b, x in zip(ci, cj, v):
        k = (a, b)
        if k not in celdas or (x < celdas[k] if modo == "min" else x > celdas[k]):
            celdas[k] = x
    return [[round((a + 0.5) * CELDA_GRADOS, 3), round((b + 0.5) * CELDA_GRADOS, 3), round(float(x), 1)]
            for (a, b), x in sorted(celdas.items())]


def procesar_abi(con, zs, ahora, horas_atras, log) -> dict:
    """Barridos nuevos de C13 y RRQPE. Devuelve info del último barrido para el JSON."""
    ult = leer_estado("abi_ultimo.json", {})
    for producto, var_control in (("c13", "tb_min_k"), ("rrqpe", "lluvia_sat_max_mmh")):
        hechos = {r[0] for r in con.execute(
            "SELECT ts FROM obs WHERE fuente=? AND estacion='la-cascada' AND variable=? AND ts>=?",
            (FUENTE, var_control, iso(ahora - dt.timedelta(hours=horas_atras + 1))))}
        pend = []
        for h in range(horas_atras, -1, -1):
            hora = (ahora - dt.timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
            try:
                pend += [x for x in goes.listar(producto, hora) if iso(goes.inicio_de(x[0])) not in hechos
                         and goes.SUBIDO.get(x[0], goes.inicio_de(x[0]) + dt.timedelta(minutes=10)) <= ahora]
            except FileNotFoundError:
                continue
        pend = pend[::-1][:ABI_POR_CORRIDA]  # primero lo más reciente; tras un corte largo, recupera hacia atrás
        for clave, tam in pend:
            t0 = goes.inicio_de(clave)
            try:
                r = goes.leer_abi(producto, clave, tam, REGION_ABI)
            except Exception as e:
                log(f"ABI {producto} {iso(t0)} falló: {e}")
                continue
            d, la, lo = r["datos"], r["lat"], r["lon"]
            filas = []
            for zid, z in zs.items():
                m0 = dentro(la, lo, z["bbox"])
                m1 = dentro(la, lo, ampliar(z["bbox"], ANILLO_KM))
                v0, v1 = d[m0 & np.isfinite(d)], d[m1 & np.isfinite(d)]
                if producto == "c13":
                    filas += [(zid, "tb_min_k", iso(t0), v0.min() if v0.size else None),
                              (zid, "frio_pct", iso(t0), 100 * (v0 < FRIO_K).mean() if v0.size else None),
                              (zid, "frio_pct_25km", iso(t0), 100 * (v1 < FRIO_K).mean() if v1.size else None)]
                else:
                    filas += [(zid, "lluvia_sat_max_mmh", iso(t0), v0.max() if v0.size else None),
                              (zid, "lluvia_sat_media_mmh", iso(t0), v0.mean() if v0.size else None),
                              (zid, "lluvia_sat_max_mmh_25km", iso(t0), v1.max() if v1.size else None)]
            guardar(con, filas)
            # latencia: del inicio del barrido a la subida al bucket (el barrido de disco completo dura ~10 min)
            lat_sub = round((goes.SUBIDO[clave] - t0).total_seconds() / 60, 1) if clave in goes.SUBIDO else None
            log(f"ABI {producto} {iso(t0)} · {r['bytes'] / 1e6:.1f} MB · en el bucket {lat_sub} min tras el inicio del barrido"
                if lat_sub is not None else f"ABI {producto} {iso(t0)} · {r['bytes'] / 1e6:.1f} MB")
            previo = ult.get(producto, {}).get("ts")
            if previo is None or iso(t0) >= previo:
                celdas = rejilla(la, lo, d, "min", 235.0) if producto == "c13" else rejilla(la, lo, d, "max", 1.0)
                ult[producto] = {"ts": iso(t0), "celdas": celdas, "latencia_min": lat_sub,
                                 "bytes": r["bytes"]}
    escribir_json(ESTADO / "abi_ultimo.json", ult)
    return ult


# ---------------------------------------------------------------- GLM

def procesar_glm(con, zs, ahora, horas_atras, log) -> None:
    """Destellos por zona en intervalos de 10 min. Guarda los puntos de las últimas horas en el estado."""
    puntos = leer_estado("glm_puntos.json", {})  # bin ISO -> [[lat, lon, t_epoch], ...]
    fin = ahora - dt.timedelta(minutes=1)
    ini = (ahora - dt.timedelta(hours=horas_atras)).replace(second=0, microsecond=0)
    ini = ini - dt.timedelta(minutes=ini.minute % 10)
    leidos = {r[0]: r[1] for r in con.execute(
        "SELECT ts, valor FROM obs WHERE fuente=? AND estacion='galapagos' AND variable='glm_archivos' AND ts>=?",
        (FUENTE, iso(ini)))}
    bins, t = [], ini
    while t + dt.timedelta(minutes=10) <= fin + dt.timedelta(minutes=1):
        k = iso(t)
        reciente = ahora - t < dt.timedelta(minutes=60)
        if k not in leidos or (leidos[k] < 30 and reciente):
            bins.append(t)
        t += dt.timedelta(minutes=10)
    bins = bins[-GLM_BINS_POR_CORRIDA:]
    listados = {}
    for b in bins:
        hora = b.replace(minute=0)
        if hora not in listados:
            try:
                listados[hora] = goes.listar("glm", hora)
            except FileNotFoundError:
                listados[hora] = []
        archivos = [x for x in listados[hora] if b <= goes.inicio_de(x[0]) < b + dt.timedelta(minutes=10)]
        lat, lon, tt, n_ok, bajado = [], [], [], 0, 0
        # descarga en hilos (solo E/S) y lectura con h5py en el hilo principal (h5py no es multihilo)
        with ThreadPoolExecutor(10) as ex:
            futuros = {ex.submit(goes.bajar, c): (c, t) for c, t in archivos}
            crudos = []
            for f in as_completed(futuros):
                try:
                    crudos.append((futuros[f], f.result()))
                except Exception as e:
                    log(f"GLM {futuros[f][0][-60:]} falló: {e}")
        for (clave, tam), datos in crudos:
            try:
                g = goes.leer_glm(clave, tam, REGION_GLM, datos=datos)
            except Exception as e:
                log(f"GLM {clave[-60:]} ilegible: {e}")
                continue
            n_ok += 1
            bajado += g["bytes"]
            lat.append(g["lat"]); lon.append(g["lon"]); tt.append(g["base"].timestamp() + g["dt"])
        if not n_ok and archivos:
            continue
        la = np.concatenate(lat) if lat else np.array([])
        lo = np.concatenate(lon) if lon else np.array([])
        te = np.concatenate(tt) if tt else np.array([])
        filas = [("galapagos", "glm_archivos", iso(b), n_ok)]
        for zid, z in zs.items():
            filas += [(zid, "rayos_n", iso(b), int(dentro(la, lo, z["bbox"]).sum())),
                      (zid, "rayos_n_25km", iso(b), int(dentro(la, lo, ampliar(z["bbox"], ANILLO_KM)).sum()))]
        guardar(con, filas)
        puntos[iso(b)] = [[round(float(a), 3), round(float(o), 3), int(x)] for a, o, x in zip(la, lo, te)]
        log(f"GLM {iso(b)} · {n_ok}/30 archivos · {la.size} destellos en la región · {bajado / 1e6:.1f} MB")
    corte = iso(ahora - dt.timedelta(hours=HORAS_PUBLICAS + 1))
    puntos = {k: v for k, v in puntos.items() if k >= corte}
    escribir_json(ESTADO / "glm_puntos.json", puntos)


# ---------------------------------------------------------------- exportación

def exportar(con, zs, ahora, ult, estado_corrida) -> dict:
    desde = iso(ahora - dt.timedelta(hours=HORAS_PUBLICAS))
    series = {}
    for e, v, t, x in con.execute("SELECT estacion, variable, ts, valor FROM obs WHERE fuente=? AND ts>=? "
                                  "AND ts<=? ORDER BY ts", (FUENTE, desde, iso(ahora))):
        series.setdefault(e, {}).setdefault(v, []).append([t, x])
    zonas_out = {}
    for zid, z in zs.items():
        s = series.get(zid, {})
        zonas_out[zid] = {"nombre": z["nombre"], "bbox": z["bbox"], "series": s,
                          "vigilancia": vigilancia.evaluar(s, ahora)}
    puntos = leer_estado("glm_puntos.json", {})
    t_ahora = ahora.timestamp()
    rayos = [[a, o, int((t_ahora - x) // 60)] for pts in puntos.values() for a, o, x in pts
             if 0 <= t_ahora - x <= HORAS_PUBLICAS * 3600]
    arch = series.get("galapagos", {}).get("glm_archivos", [])
    return {
        "generado": iso(ahora),
        "advertencia": "Estimación satelital (GOES-19, NOAA): no es lluvia medida ni una alerta oficial. "
                       "Siga siempre las indicaciones del COE, la SNGR y el ECU 911.",
        "fuente": "GOES-19 (GOES-East, NOAA): ABI banda 13 y RRQPE cada 10 min; rayos del GLM",
        "horas": "UTC",
        "region_abi": REGION_ABI, "region_glm": REGION_GLM, "anillo_km": ANILLO_KM, "frio_k": FRIO_K,
        "celda_grados": CELDA_GRADOS,
        "variables": VARIABLES,
        "vigilancia_umbrales": {k: [u, t] for k, (u, t) in vigilancia.UMBRALES.items()},
        "ultima_imagen": {p: {"ts": u.get("ts"), "latencia_min": u.get("latencia_min")} for p, u in ult.items()},
        "glm_ultimo_intervalo": arch[-1][0] if arch else None,
        "zonas": zonas_out,
        "rayos": rayos,                                   # [lat, lon, minutos desde el destello]
        "nucleos": ult.get("c13", {}).get("celdas", []),  # [lat, lon, Tb mín. K] con Tb < 235 K
        "lluvia_sat": ult.get("rrqpe", {}).get("celdas", []),  # [lat, lon, mm/h] con ≥ 1 mm/h
        "corrida": estado_corrida,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--horas", type=float, default=1.0, help="horas hacia atrás para recuperar ABI y GLM")
    ap.add_argument("--solo-exportar", action="store_true")
    ap.add_argument("--sin-glm", action="store_true")
    ap.add_argument("--ahora", help="repetir un momento pasado (ISO UTC), p. ej. 2026-10-31T02:30:00Z; "
                                    "solo para pruebas, con CLIMA_DB y CLIMA_SALIDA propios")
    a = ap.parse_args()
    ahora = dt.datetime.fromisoformat(a.ahora.replace("Z", "+00:00")) if a.ahora else dt.datetime.now(UTC)
    t0 = time.time()
    mensajes = []

    def log(m):
        print(m, flush=True)
        mensajes.append(m)

    zs = zonas()
    con = conectar()
    ESTADO.mkdir(parents=True, exist_ok=True)
    ult, errores = leer_estado("abi_ultimo.json", {}), []
    if not a.solo_exportar:
        horas = max(0, int(np.ceil(a.horas)))
        for nombre, fn in (("abi", lambda: procesar_abi(con, zs, ahora, horas, log)),
                           ("glm", None if a.sin_glm else lambda: procesar_glm(con, zs, ahora, a.horas, log))):
            if fn is None:
                continue
            try:
                r = fn()
                if nombre == "abi":
                    ult = r
            except Exception as e:  # un producto caído no detiene al otro
                traceback.print_exc()
                errores.append(f"{nombre}: {str(e)[:150]}")
    estado = {"ts": iso(ahora), "segundos": round(time.time() - t0, 1), "ok": not errores, "errores": errores}
    out = exportar(con, zs, ahora, ult, estado)
    escribir_json(SALIDA / "satelite.json", out)
    tam = (SALIDA / "satelite.json").stat().st_size
    log(f"satelite.json · {tam / 1024:.0f} KB · {len(out['rayos'])} destellos · {len(out['nucleos'])} celdas frías · "
        f"{estado['segundos']} s")
    if errores:
        sys.exit(1)


if __name__ == "__main__":
    main()
