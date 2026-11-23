#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Fase 0, anexo: ¿aporta el CAPE de los modelos a la probabilidad de lluvia fuerte?

Prueba, con el mismo esquema que 07_pronostico_evaluacion.py, si añadir el CAPE (energía disponible
para la convección) de los modelos globales a la curva logística del consenso mejora la probabilidad
de que alguna estación del grupo mida ≥ 20 mm en el día. **No cambia la calibración publicada:** no
llama a calibrar() ni a escribir_calibracion() de 07 y no toca recolector/pronostico_calibracion.json.

Fuente: archivo de corridas anteriores de Open-Meteo (CC BY 4.0). En ese archivo el CAPE con
anticipación (`cape_previous_dayN`) solo existe para GFS, UK Met Office, ARPEGE y GEM; ECMWF IFS,
AIFS e ICON no lo tienen. El endpoint se lee de CLIMA_OPENMETEO_PREVIOUS_API (entorno o
privado/fuentes.env), como en 06.

Pasos:
  1. descarga (incremental, en caché): lluvia de los 7 modelos del consenso y CAPE de los 4 que lo
     tienen, con 1, 2 y 5 días de anticipación, en las estaciones de 06;
  2. consenso de lluvia: el mismo de 07 (consenso(), con sus funciones importadas);
  3. «percentil de CAPE»: máximo horario del CAPE en el día de Galápagos, como percentil dentro del
     propio modelo (punto y anticipación), promediado entre los modelos con dato (≥ 3 de 4);
  4. logística base (consenso) frente a consenso + CAPE (y con interacción), en las mismas filas y
     con los mismos bloques de validación cruzada que 07 (fuera un año; fuera un mes si hay uno solo);
  5. diferencias de Brier y AUC con bootstrap pareado por fechas.

Salida (pronostico/fase0/): cape.md (informe, generado), cape_metricas.csv, cape_octubre.csv,
cape_eventos.csv (solo grupos con datos públicos) y cape_validacion_cruzada.csv.gz (no versionado).
Caché: datos/pronostico-archivo/cape/ (no versionado).

Uso:
    geodatos/.venv/bin/python -I clima/scripts/09_pronostico_cape.py            # descarga lo que falte y evalúa
    geodatos/.venv/bin/python -I clima/scripts/09_pronostico_cape.py --sin-descarga
"""
import argparse
import csv
import datetime as dt
import gzip
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent


def _modulo(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, AQUI / archivo)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


A06 = _modulo("archivo06", "06_pronostico_archivo.py")
E07 = _modulo("evaluacion07", "07_pronostico_evaluacion.py")

RAIZ = E07.RAIZ
SAL = E07.SAL
CACHE = RAIZ / "datos" / "pronostico-archivo" / "cape"
HASTA = "2026-11-01"  # mismo final que el archivo de la fase 0: así los percentiles se parecen a los publicados
MODELOS_CONSENSO = ["ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless", "ukmo_seamless",
                    "meteofrance_seamless", "gem_seamless"]
MODELOS_CAPE = ["gfs_seamless", "ukmo_seamless", "meteofrance_seamless", "gem_seamless"]  # con cape_previous_dayN
ANTICIPACIONES = [1, 2, 5]  # «hoy», «mañana» y 4 días (ver 07: anticipación 1 = recuadro «hoy»)
MIN_MODELOS_CAPE = 3
UMBRAL = 20
N_BOOT = 1000
RNG = np.random.default_rng(20261122)
GRUPOS_PUBLICOS = ["santa_cruz_alta", "costa"]  # sin series del GSC
EVENTOS = ["2026-10-30", "2026-10-23", "2026-10-03", "2026-10-04", "2026-06-14", "2024-02-22"]

# Regla de decisión, fijada ANTES de ver los resultados: el CAPE «aporta» solo si, con anticipación 1 o 2,
# en al menos una celda grupo × temporada con ≥ 10 días de evento, el IC del 90 % de ΔBrier (CAPE − base)
# queda entero por debajo de 0, y en ninguna otra celda con ≥ 10 eventos queda entero por encima de 0.
MIN_EVENTOS_REGLA = 10


# ---------------------------------------------------------------- descarga

def _var(nombre, n):
    return f"{nombre}_previous_day{n}"


def descargar(desde, hasta):
    api = A06._api()
    import urllib.parse
    puntos = A06.PUNTOS
    for modelo in MODELOS_CONSENSO:
        vars_ = [_var("precipitation", n) for n in ANTICIPACIONES]
        if modelo in MODELOS_CAPE:
            vars_ += [_var("cape", n) for n in ANTICIPACIONES]
        for d0, d1 in A06.tramos(desde, hasta):
            ruta = CACHE / "estaciones" / modelo / f"{d0}_{d1}.json.gz"
            if ruta.exists():
                continue
            ruta.parent.mkdir(parents=True, exist_ok=True)
            q = urllib.parse.urlencode({
                "latitude": ",".join(str(p[1]) for p in puntos.values()),
                "longitude": ",".join(str(p[2]) for p in puntos.values()),
                "hourly": ",".join(vars_), "models": modelo, "timezone": "GMT",
                "start_date": d0.isoformat(), "end_date": d1.isoformat()})
            t = time.time()
            datos = _pedir(f"{api}?{q}", modelo, d0)
            with gzip.open(ruta, "wt") as fh:
                json.dump(datos, fh)
            print(f"{modelo} {d0}→{d1}: {time.time() - t:.1f} s", flush=True)
            time.sleep(6)  # ~35 llamadas de peso por petición: se queda bajo el límite por minuto


def _pedir(url, modelo, d0):
    import urllib.error
    import urllib.request
    for intento in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": A06.UA}), timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(60 * (intento + 1))
                continue
            raise RuntimeError(f"{modelo} {d0}: HTTP {e.code} {e.read()[:200]!r}")
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (intento + 1))
    raise RuntimeError(f"{modelo} {d0}: sin respuesta")


def tablas():
    """Lluvia en el formato largo de 06 (para usar pronosticos() de 07) y CAPE horario."""
    lluvia, cape = CACHE / "pronostico_horario.csv.gz", CACHE / "cape_horario.csv.gz"
    with gzip.open(lluvia, "wt", newline="") as fl, gzip.open(cape, "wt", newline="") as fc:
        wl, wc = csv.writer(fl), csv.writer(fc)
        wl.writerow(["punto", "modelo", "anticipacion_dias", "hora_utc", "lluvia_mm", "lat_celda", "lon_celda"])
        wc.writerow(["punto", "modelo", "anticipacion_dias", "hora_utc", "cape"])
        for carpeta in sorted(p for p in (CACHE / "estaciones").iterdir() if p.is_dir()):
            for ruta in sorted(carpeta.glob("*.json.gz")):
                with gzip.open(ruta, "rt") as f:
                    datos = json.load(f)
                datos = datos if isinstance(datos, list) else [datos]
                for punto, p in zip(A06.PUNTOS, datos):
                    h = p.get("hourly", {})
                    for n in ANTICIPACIONES:
                        for t, v in zip(h.get("time", []), h.get(_var("precipitation", n)) or []):
                            if v is not None:
                                wl.writerow([punto, carpeta.name, n, t, v, p["latitude"], p["longitude"]])
                        for t, v in zip(h.get("time", []), h.get(_var("cape", n)) or []):
                            if v is not None:
                                wc.writerow([punto, carpeta.name, n, t, v])
    return lluvia, cape


# ---------------------------------------------------------------- CAPE diario

def cape_diario(ruta):
    """Máximo horario del CAPE en el día de Galápagos. El CAPE es instantáneo en hora_utc: el día es el
    de hora_utc − 6 h (no − 7 h, como la lluvia, que es la suma de la hora que termina)."""
    c = pd.read_csv(ruta, parse_dates=["hora_utc"])
    c["fecha"] = (c.hora_utc - pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")
    d = c.groupby(["punto", "modelo", "anticipacion_dias", "fecha"]).cape.agg(["max", "size"]).reset_index()
    d = d[d["size"] >= 20].rename(columns={"max": "cape_max"}).drop(columns="size")
    d["pct"] = d.groupby(["punto", "modelo", "anticipacion_dias"]).cape_max.rank(pct=True)
    por_modelo = d.pivot_table(index=["punto", "anticipacion_dias", "fecha"], columns="modelo", values="cape_max")
    agg = d.groupby(["punto", "anticipacion_dias", "fecha"]).agg(cape_pct=("pct", "mean"), n_cape=("pct", "size"),
                                                                 cape_jkg=("cape_max", "median")).reset_index()
    agg = agg[agg.n_cape >= MIN_MODELOS_CAPE]
    return agg, por_modelo


# ---------------------------------------------------------------- logística con varias variables

def logistica(X, y, l2=1e-2):
    X = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X.shape[1])
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ w))
        H = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.eye(X.shape[1])
        paso = np.linalg.solve(H, X.T @ (y - p) - l2 * w)
        w += paso
        if np.abs(paso).max() < 1e-8:
            break
    return w


def prob(w, X):
    return 1 / (1 + np.exp(-(w[0] + np.asarray(X) @ w[1:])))


VARIANTES = {  # nombre: columnas
    "base": lambda d: d[["cons"]].to_numpy(),
    "cape": lambda d: d[["cons", "cape"]].to_numpy(),
    "interaccion": lambda d: np.column_stack([d.cons, d.cape, d.cons * d.cape]),
    "solo_cape": lambda d: d[["cape"]].to_numpy(),
}


def validacion_cruzada(d, y):
    """Predicciones fuera de muestra de cada variante, con los bloques de 07."""
    bloque = d.fecha.str[:4] if d.fecha.str[:4].nunique() > 1 else d.fecha.str[:7]
    out = {k: np.full(len(d), np.nan) for k in VARIANTES}
    clim = np.full(len(d), np.nan)
    for b in bloque.unique():
        dentro = (bloque != b).to_numpy()
        if y[dentro].sum() < 2:
            continue
        for k, f in VARIANTES.items():
            X = f(d)
            out[k][~dentro] = prob(logistica(X[dentro], y[dentro]), X[~dentro])
        clim[~dentro] = y[dentro].mean()
    return out, clim


def bootstrap_pareado(fechas, y, pa, pb):
    """IC del 90 % de ΔBrier y ΔAUC (b − a), remuestreando fechas."""
    uf = np.unique(fechas)
    idx = {f: np.flatnonzero(fechas == f) for f in uf}
    db, da = [], []
    for _ in range(N_BOOT):
        s = np.concatenate([idx[f] for f in RNG.choice(uf, len(uf))])
        if y[s].sum() == 0:
            continue
        db.append(np.mean((pb[s] - y[s]) ** 2) - np.mean((pa[s] - y[s]) ** 2))
        da.append(E07.auc(pb[s], y[s].astype(bool)) - E07.auc(pa[s], y[s].astype(bool)))
    return np.nanpercentile(db, [5, 95]), np.nanpercentile(da, [5, 95])


# ---------------------------------------------------------------- evaluación

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2024-01-01")
    ap.add_argument("--hasta", default=HASTA)
    ap.add_argument("--sin-descarga", action="store_true")
    a = ap.parse_args()
    if not a.sin_descarga:
        descargar(dt.date.fromisoformat(a.desde), dt.date.fromisoformat(a.hasta))
    ruta_lluvia, ruta_cape = tablas()

    o = E07.observaciones()
    hay_gsc = (RAIZ / "privado" / "gsc_diario.csv").exists()
    dia, _ = E07.pronosticos(ruta_lluvia)
    cons = E07.consenso(dia)
    cons = cons[cons.modelo == "consenso"].drop(columns="modelo").rename(columns={"fc_mm": "cons"})
    cap, cap_mod = cape_diario(ruta_cape)
    j = cons.merge(o, on=["punto", "fecha"]).merge(cap, how="left", on=["punto", "fecha", "anticipacion_dias"])
    j["temporada"] = np.where(pd.to_datetime(j.fecha).dt.month.isin(E07.LLUVIOSA), "lluviosa", "garua")

    filas, cvs, octubre = [], [], []
    for g, (puntos, _) in E07.GRUPOS.items():
        sub = j[j.punto.isin(puntos)]
        if sub.empty:
            continue
        # Promedio en el grupo; el CAPE solo si todos los puntos del grupo con consenso lo tienen.
        z = sub.groupby(["fecha", "anticipacion_dias", "temporada"]).agg(
            cons=("cons", "mean"), obs=("obs_mm", "max"), cape=("cape_pct", "mean"),
            n_pt=("cons", "size"), n_cape=("cape_pct", "count"), cape_jkg=("cape_jkg", "median")).reset_index()
        for temp in ("lluviosa", "garua"):
            for n in ANTICIPACIONES:
                todo = z[(z.temporada == temp) & (z.anticipacion_dias == n)].reset_index(drop=True)
                d = todo[todo.n_cape == todo.n_pt].reset_index(drop=True)
                y_todo = (todo.obs >= UMBRAL).to_numpy(float)
                y = (d.obs >= UMBRAL).to_numpy(float)
                fila = {"grupo": g, "temporada": temp, "anticipacion_dias": n, "umbral_mm": UMBRAL,
                        "dias_todo": len(todo), "eventos_todo": int(y_todo.sum()), "dias": len(d), "eventos": int(y.sum())}
                # Reproducción de la base publicada: logística de 07 en todas las filas (sin exigir CAPE).
                if y_todo.sum() >= 5:
                    p07, c07 = validacion_cruzada(todo.assign(cape=0.0), y_todo)
                    ok = ~np.isnan(p07["base"])
                    bs, bs0 = np.mean((p07["base"][ok] - y_todo[ok]) ** 2), np.mean((c07[ok] - y_todo[ok]) ** 2)
                    fila["bss_base_todas_filas"] = round(1 - bs / bs0, 3)
                if y.sum() >= 5:
                    pcv, clim = validacion_cruzada(d, y)
                    ok = ~np.isnan(pcv["base"])
                    yk, fk = y[ok], d.fecha.to_numpy()[ok]
                    bs0 = np.mean((clim[ok] - yk) ** 2)
                    for k in VARIANTES:
                        bs = np.mean((pcv[k][ok] - yk) ** 2)
                        fila[f"brier_{k}"] = round(bs, 4)
                        fila[f"bss_{k}"] = round(1 - bs / bs0, 3)
                        fila[f"auc_{k}"] = round(E07.auc(pcv[k][ok], yk.astype(bool)), 3)
                    for k in ("cape", "interaccion"):
                        (b_lo, b_hi), (a_lo, a_hi) = bootstrap_pareado(fk, yk, pcv["base"][ok], pcv[k][ok])
                        fila[f"dbrier_{k}"] = round(fila[f"brier_{k}"] - fila["brier_base"], 4)
                        fila[f"dbrier_{k}_ic90"] = f"{b_lo:+.4f} a {b_hi:+.4f}"
                        fila[f"dbrier_{k}_lo"], fila[f"dbrier_{k}_hi"] = round(b_lo, 4), round(b_hi, 4)
                        fila[f"dauc_{k}"] = round(fila[f"auc_{k}"] - fila["auc_base"], 3)
                        fila[f"dauc_{k}_ic90"] = f"{a_lo:+.3f} a {a_hi:+.3f}"
                        fila[f"dauc_{k}_lo"], fila[f"dauc_{k}_hi"] = round(a_lo, 3), round(a_hi, 3)
                    w = logistica(VARIANTES["cape"](d), y)
                    fila["coef_cons"], fila["coef_cape"] = round(w[1], 2), round(w[2], 2)
                    fila["auc_cape_crudo"] = round(E07.auc(d.cape, y.astype(bool)), 3)
                    fila["auc_cons_crudo"] = round(E07.auc(d.cons, y.astype(bool)), 3)
                    fila["corr_cons_cape"] = round(float(np.corrcoef(d.cons, d.cape)[0, 1]), 3)
                    cvs.append(d.assign(grupo=g, p_base=pcv["base"], p_cape=pcv["cape"], p_inter=pcv["interaccion"]))
                filas.append(fila)
        # ¿El CAPE separa los días de evento de los demás DENTRO de octubre (El Niño)? Sin calibrar: AUC cruda.
        for n in ANTICIPACIONES:
            for etiqueta, mes in (("oct-2026", "2026-10"), ("resto", None)):
                s = z[(z.anticipacion_dias == n) & (z.n_cape == z.n_pt)]
                s = s[s.fecha.str[:7] == mes] if mes else s[s.fecha.str[:7] != "2026-10"]
                y = (s.obs >= UMBRAL).to_numpy(bool)
                octubre.append({"grupo": g, "anticipacion_dias": n, "periodo": etiqueta, "dias": len(s), "eventos": int(y.sum()),
                                "cape_pct_medio": round(s.cape.mean(), 3) if len(s) else None,
                                "cape_pct_medio_eventos": round(s.cape[y].mean(), 3) if y.any() else None,
                                "auc_cape": round(E07.auc(s.cape, y), 3) if 0 < y.sum() < len(s) else None,
                                "auc_cons": round(E07.auc(s.cons, y), 3) if 0 < y.sum() < len(s) else None})

    met = pd.DataFrame(filas)
    met.to_csv(SAL / "cape_metricas.csv", index=False)
    pd.DataFrame(octubre).to_csv(SAL / "cape_octubre.csv", index=False)
    cv = pd.concat(cvs, ignore_index=True) if cvs else pd.DataFrame()
    if len(cv):
        cv.to_csv(SAL / "cape_validacion_cruzada.csv.gz", index=False, float_format="%.3f")

    # Eventos de los grupos con datos públicos.
    ev = []
    for g in GRUPOS_PUBLICOS:
        puntos = E07.GRUPOS[g][0]
        for f in EVENTOS:
            for n in ANTICIPACIONES:
                s = j[j.punto.isin(puntos) & (j.fecha == f) & (j.anticipacion_dias == n)]
                if s.empty:
                    continue
                fila = {"grupo": g, "fecha": f, "anticipacion_dias": n, "obs_max_mm": s.obs_mm.max(),
                        "consenso": round(s.cons.mean(), 2), "cape_pct": round(s.cape_pct.mean(), 2) if s.cape_pct.notna().any() else None}
                for m in MODELOS_CAPE:
                    try:
                        fila[f"cape_{m}_jkg"] = round(float(cap_mod.loc[[(p, n, f) for p in puntos if (p, n, f) in cap_mod.index], m].median()))
                    except (KeyError, ValueError):
                        fila[f"cape_{m}_jkg"] = None
                if len(cv):
                    c = cv[(cv.grupo == g) & (cv.fecha == f) & (cv.anticipacion_dias == n)]
                    if len(c):
                        fila.update({"p_base": round(c.p_base.iloc[0], 2), "p_cape": round(c.p_cape.iloc[0], 2)})
                ev.append(fila)
    eventos = pd.DataFrame(ev)
    eventos.to_csv(SAL / "cape_eventos.csv", index=False)
    informe(met, pd.DataFrame(octubre), eventos, hay_gsc, dia)
    print(met[["grupo", "temporada", "anticipacion_dias", "eventos", "bss_base_todas_filas", "bss_base", "bss_cape",
               "dbrier_cape_ic90", "auc_base", "auc_cape"]].to_string())


# ---------------------------------------------------------------- informe

NOMBRE_GRUPO = {"santa_cruz_alta": "Santa Cruz alta", "san_cristobal_alta": "San Cristóbal alta", "costa": "Costa"}
PUBLICADO = {("santa_cruz_alta", "garua", 1): 0.14, ("santa_cruz_alta", "garua", 2): 0.06, ("santa_cruz_alta", "garua", 5): 0.09,
             ("costa", "lluviosa", 1): 0.10, ("costa", "lluviosa", 2): 0.10, ("costa", "lluviosa", 5): 0.08,
             ("san_cristobal_alta", "lluviosa", 1): 0.25, ("san_cristobal_alta", "lluviosa", 2): 0.17,
             ("san_cristobal_alta", "lluviosa", 5): 0.15}


def _f(x, nd=2):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}".replace(".", ",")


def veredicto(met):
    m = met.dropna(subset=["dbrier_cape_lo"])
    m = m[(m.eventos >= MIN_EVENTOS_REGLA) & m.anticipacion_dias.isin([1, 2])]
    mejora = m[m.dbrier_cape_hi < 0]
    empeora = m[m.dbrier_cape_lo > 0]
    if len(mejora) and not len(empeora):
        return True, len(m), mejora
    return False, len(m), mejora


def informe(met, octubre, eventos, hay_gsc, dia):
    aporta, n_celdas, mejora = veredicto(met)
    L = ["# Anexo de la fase 0: ¿aporta el CAPE?", "",
         f"Generado por `clima/scripts/09_pronostico_cape.py` el {pd.Timestamp.now(tz='UTC'):%d-%m-%Y}. **No edites este archivo a mano.**",
         "", "> El CAPE, la lluvia y las probabilidades de este anexo son estimaciones de modelos, no datos oficiales. "
         "El pronóstico oficial lo emite el INAMHI. **Esta prueba no cambia la calibración publicada.**", "",
         "## Qué se probó", "",
         "- **CAPE** (energía disponible para la convección, J/kg): el máximo horario del día de Galápagos, como percentil "
         "dentro del propio modelo (punto y anticipación), promediado entre los modelos que lo tienen y luego entre los puntos del grupo.",
         "- **Modelos con CAPE en el archivo de corridas anteriores de Open-Meteo:** GFS, UK Met Office, ARPEGE y GEM "
         f"(hacen falta {MIN_MODELOS_CAPE} de 4). ECMWF IFS, AIFS e ICON no guardan el CAPE con anticipación.",
         "- **Base:** la logística de 07 sobre el consenso de lluvia (los mismos 7 modelos y la misma función). "
         "**Con CAPE:** la logística sobre consenso + percentil de CAPE; también con su interacción.",
         f"- **Evento:** la estación más lluviosa del grupo mide ≥ {UMBRAL} mm. Anticipaciones 1, 2 y 5 días (recuadros «hoy», «mañana» y 4 días).",
         "- **Validación cruzada:** los mismos bloques que 07 (fuera un año; si hay un solo año, fuera un mes). Base y CAPE se comparan "
         "en las mismas filas (las que tienen CAPE). ΔBrier y ΔAUC con bootstrap pareado por fechas (IC del 90 %).",
         f"- **Regla fijada antes de ver los resultados:** el CAPE aporta solo si, con anticipación 1 o 2, en al menos una celda con "
         f"≥ {MIN_EVENTOS_REGLA} días de evento, el IC de ΔBrier queda entero bajo 0, y en ninguna otra queda entero sobre 0.", ""]
    if not hay_gsc:
        L += ["**San Cristóbal no se evaluó:** faltan las series del GSC (`privado/gsc_diario.csv`, que no se versiona). "
              "Es el grupo con más eventos (54 días-grupo con ≥ 20 mm en temporada lluviosa); la prueba debe repetirse con él.", ""]
    L += ["## Resultado", "",
          f"**Veredicto: {'el CAPE aporta' if aporta else 'no hay evidencia de que el CAPE mejore la probabilidad'}** "
          f"({len(mejora)} de {n_celdas} celdas evaluables con mejora clara según la regla).", "",
          "| Grupo | Temporada | Ant. | Días (eventos) | BSS publicado | BSS base, mismas filas | BSS con CAPE | ΔBrier (IC90) | AUC base → con CAPE | ΔAUC (IC90) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in met.dropna(subset=["brier_base"]).iterrows():
        pub = PUBLICADO.get((r.grupo, r.temporada, r.anticipacion_dias))
        L.append(f"| {NOMBRE_GRUPO[r.grupo]} | {r.temporada} | {r.anticipacion_dias} | {r.dias} ({r.eventos}) | {_f(pub)} "
                 f"(aquí {_f(r.bss_base_todas_filas)}) | {_f(r.bss_base)} | {_f(r.bss_cape)} | {_f(r.dbrier_cape, 4)} ({_f(r.dbrier_cape_lo, 4)} a {_f(r.dbrier_cape_hi, 4)}) | "
                 f"{_f(r.auc_base)} → {_f(r.auc_cape)} | {_f(r.dauc_cape_lo, 3)} a {_f(r.dauc_cape_hi, 3)} |")
    L += ["", "- «BSS publicado» es el de `informe.md`; «aquí» es la misma curva rehecha con este archivo (todas las filas, sin exigir CAPE): "
          "si se parecen, la base está bien reproducida.",
          "- ΔBrier negativo = mejor con CAPE. Un ΔAUC positivo solo dice que el CAPE ordena mejor los días; si el Brier no baja, "
          "la probabilidad publicada no sería mejor.",
          *[f"- {NOMBRE_GRUPO[r.grupo]}, {r.temporada}, anticipación {r.anticipacion_dias}: sin calibrar, el CAPE solo ordena los días "
            f"más o menos como el consenso (AUC {_f(r.auc_cape_crudo)} frente a {_f(r.auc_cons_crudo)}), y los dos se mueven juntos "
            f"(correlación {_f(r.corr_cons_cape)}): el CAPE trae casi la misma información que el consenso. La subida del AUC en validación "
            f"cruzada ({_f(r.auc_base)} → {_f(r.auc_cape)}) no es fiable: la base pierde AUC al rehacer la curva mes a mes "
            f"({_f(r.auc_cons_crudo)} sin validación), y los días fuertes vienen en rachas de varios días, así que el bootstrap por día "
            f"da un intervalo demasiado estrecho."
            for _, r in met.dropna(subset=["dauc_cape_lo"]).iterrows() if r.dauc_cape_lo > 0],
          "- Las tablas completas (interacción, CAPE solo, coeficientes, correlación con el consenso) "
          "están en `cape_metricas.csv`.", ""]
    L += ["## Octubre de 2026 (El Niño)", "",
          "Si el CAPE solo dijera «es octubre», distinguiría octubre del resto pero no los días de lluvia fuerte dentro de octubre. "
          "AUC cruda (sin calibrar) dentro y fuera de octubre, anticipación 1:", "",
          "| Grupo | Periodo | Días (eventos) | Percentil de CAPE medio | en días de evento | AUC del CAPE | AUC del consenso |", "|---|---|---|---|---|---|---|"]
    for _, r in octubre[octubre.anticipacion_dias == 1].iterrows():
        L.append(f"| {NOMBRE_GRUPO[r.grupo]} | {r.periodo} | {r.dias} ({r.eventos}) | {_f(r.cape_pct_medio)} | {_f(r.cape_pct_medio_eventos)} | "
                 f"{_f(r.auc_cape)} | {_f(r.auc_cons)} |")
    L += ["", "## Eventos (anticipación 1, «hoy»)", "",
          "El 30-oct fue convectivo; el 3 y el 23-oct, orográficos «cálidos». Probabilidad de ≥ 20 mm en validación cruzada "
          "(«—»: celda sin curva). En la costa, desde jun-2026 solo hay la estación Militar (la serie de la FCD llega a jun-2026).", "",
          "| Grupo | Día | Medido (mm) | Consenso | Percentil de CAPE | CAPE GFS / UKMO / ARPEGE / GEM (J/kg) | P base | P con CAPE |",
          "|---|---|---|---|---|---|---|---|"]
    for _, r in eventos[eventos.anticipacion_dias == 1].iterrows():
        capes = " / ".join("—" if pd.isna(r.get(f"cape_{m}_jkg")) else f"{int(r[f'cape_{m}_jkg'])}" for m in MODELOS_CAPE)
        L.append(f"| {NOMBRE_GRUPO[r.grupo]} | {r.fecha} | {_f(r.obs_max_mm, 1)} | {_f(r.consenso)} | {_f(r.cape_pct)} | {capes} | "
                 f"{_f(r.get('p_base'))} | {_f(r.get('p_cape'))} |")
    L += ["", "## Disponibilidad en Open-Meteo (sondeo del 22-nov-2026 en Santa Cruz)", "",
          "| Variable | Pronóstico en vivo | Corridas anteriores (con anticipación, 2024 y 2026) | Histórico de pronósticos (corrida más reciente) | Conjuntos |",
          "|---|---|---|---|---|",
          "| CAPE | IFS 0,25°, IFS 9 km, GFS, ICON, UKMO, ARPEGE, GEM (no AIFS) | GFS, UKMO, ARPEGE, GEM | GFS, ICON, UKMO, ARPEGE, GEM desde 2024; IFS 0,25° e IFS 9 km solo en 2026 | IFS ENS, GEFS, MOGREPS-G |",
          "| Inhibición convectiva | GFS, UKMO, IFS 9 km | ninguno | GFS, UKMO; IFS 9 km en 2026 | GEFS |",
          "| Índice de levantamiento | GFS | GFS | GFS | ninguno |",
          "| Agua precipitable | IFS 0,25°, IFS 9 km, GFS | ninguno | IFS 0,25°; GFS e IFS 9 km en 2026 | IFS ENS |",
          "| Chubascos (showers) | todos menos UKMO | todos menos AIFS y UKMO | todos menos UKMO | todos |",
          "| Probabilidad de lluvia | IFS 0,25°, IFS 9 km, GFS, ICON, UKMO, GEM | ninguno | solo en 2026 (los mismos) | no se ofrece |",
          "| Humedad y viento a 850 hPa | todos menos IFS 9 km | rechazados con el nombre `<variable>_previous_dayN` | todos menos IFS 9 km (UKMO solo en 2026) | IFS ENS, AIFS ENS |", "",
          "El histórico de pronósticos solo trae la corrida más reciente (anticipación ≈ 0): no sirve para evaluar «hoy» ni «mañana». "
          "Es la única vía al CAPE de ICON en 2024–2026.", "",
          "**Costo:** Open-Meteo cobra por punto máx(1, variables × modelos / 10), y en los conjuntos multiplica por los miembros. "
          "Añadir el CAPE a los 8 deterministas sube su peso de 1 a 1,6 por punto (≈ +100 llamadas al día con 7 puntos). "
          "En los conjuntos lo duplicaría (≈ +500 al día): no vale la pena.", "",
          "## Recomendación", "",
          ("- **Recoger** el CAPE de los deterministas desde ya (barato) para evaluarlo con el archivo propio, con ECMWF incluido. "
           + ("Con lo medido, **sí** podría entrar en la calibración, tras repetir la prueba con San Cristóbal."
              if aporta else "**No usarlo** en la calibración publicada: con estos datos no la mejora."))
          + " Repetir esta prueba con San Cristóbal (GSC) y con la temporada lluviosa de 2027.", ""]
    L += ["## Incertidumbre y límites", "",
          "- **Muestra pequeña:** cada celda tiene de 5 a 20 días de evento. Un IC de ΔBrier que cruza 0 quiere decir «no se puede distinguir», "
          "no «es igual».",
          "- **Santa Cruz** solo tiene abr–nov-2026 (IERSE), casi todo en un octubre anómalo; la validación cruzada deja fuera un mes.",
          "- **Solo 4 modelos con CAPE** y ninguno de ECMWF, que es el más constante en la lluvia. El CAPE de ECMWF IFS sí está en el "
          "pronóstico en vivo: si se recoge desde ahora, podrá evaluarse con una temporada de archivo propio.",
          "- **El CAPE es de la celda del modelo (9–25 km)**, no del punto. En Galápagos buena parte de la lluvia fuerte es orográfica, "
          "y ahí el CAPE no tiene por qué ayudar.",
          f"- Archivo: corridas anteriores de Open-Meteo (CC BY 4.0), {dia.fecha.min()} → {dia.fecha.max()}.", ""]
    (SAL / "cape.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
