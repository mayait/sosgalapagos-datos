#!/usr/bin/env python3
"""Fase 0 del pronóstico: ¿cuánto sirven los modelos globales para anticipar la lluvia en Galápagos?

Compara el archivo de pronósticos (06_pronostico_archivo.py) con la lluvia medida:
  - IERSE (Santa Cruz, abr–nov 2026): datos/ierse-wsn/diario.csv y horario.csv (hora UTC−6)
  - GSC-USFQ (San Cristóbal, diario 2015–may 2026): privado/gsc_diario.csv (no versionado;
    se exporta del servidor, ver LEEME de pronostico/)
  - FCD Puerto Ayora (diario desde 1965): datos/fcd/climate_puerto-ayora.csv

Unidad de verificación: el día de Galápagos (00–24 h, UTC−6) en el punto de la estación. Los
modelos dan la lluvia media de una celda de 9–25 km; una estación mide un punto. Por eso se mira
sobre todo la **discriminación** (si el modelo sube cuando llueve más, AUC), que no depende del sesgo,
además del sesgo y de los aciertos con umbrales fijos.

Salida en pronostico/fase0/: resumen.json, tablas CSV, figuras PNG.

Uso:
    geodatos/.venv/bin/python -I clima/scripts/07_pronostico_evaluacion.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "datos" / "pronostico-archivo" / "pronostico_horario.csv.gz"
SAL = RAIZ / "pronostico" / "fase0"
RNG = np.random.default_rng(20261103)
N_BOOT = 400

GRUPOS = {  # grupo: (puntos, descripción)
    "santa_cruz_alta": (["ierse/n_glps09", "ierse/n_glps05", "ierse/n_glps01"], "Santa Cruz, parte alta y media (IERSE)"),
    "san_cristobal_alta": (["gsc/junco", "gsc/cerro_alto", "gsc/mirador", "gsc/merceditas"], "San Cristóbal, parte alta (GSC)"),
    "costa": (["fcd/puerto_ayora", "ierse/n_glps06"], "Costa: Puerto Ayora (FCD) y Militar (IERSE)"),
}
NOMBRE_MODELO = {"ecmwf_ifs": "ECMWF IFS 9 km", "ecmwf_ifs025": "ECMWF IFS 0,25°", "ecmwf_aifs025_single": "ECMWF AIFS (IA)",
                 "gfs_seamless": "NOAA GFS", "icon_seamless": "DWD ICON", "ukmo_seamless": "UK Met Office",
                 "meteofrance_seamless": "Météo-France ARPEGE", "gem_seamless": "Canadá GEM",
                 "consenso": "Consenso de modelos", "consenso_retardado": "Consenso + corridas anteriores",
                 "ref_climatologia": "Referencia: climatología del mes", "ref_persistencia": "Referencia: persistencia"}
UMBRALES = [10, 20, 50]
LLUVIOSA = {1, 2, 3, 4, 5}  # meses de la temporada cálida y lluviosa


# ---------------------------------------------------------------- observaciones

def observaciones():
    obs = []
    d = pd.read_csv(RAIZ / "datos" / "ierse-wsn" / "diario.csv")
    d = d[d.cobertura_pct >= 80]  # con cortes el total es un mínimo; 80 % deja dentro el 30-oct (88–89 %)
    obs.append(pd.DataFrame({"punto": "ierse/" + d.estacion_id, "fecha": d.fecha, "obs_mm": d.lluvia_mm}))

    gsc = RAIZ / "privado" / "gsc_diario.csv"
    if gsc.exists():
        g = pd.read_csv(gsc)
        g = g[g.estacion.isin(["junco", "cerro_alto", "mirador", "merceditas"])]
        # El GSC marca el día continental (UTC−5): una hora de desfase con el día de Galápagos. Se ignora.
        fecha = (pd.to_datetime(g.ts.str.replace("Z", "")) - pd.Timedelta(hours=5)).dt.strftime("%Y-%m-%d")
        obs.append(pd.DataFrame({"punto": "gsc/" + g.estacion, "fecha": fecha, "obs_mm": g.valor}))
    else:
        print("Aviso: falta privado/gsc_diario.csv; se evalúa sin San Cristóbal")

    f = pd.read_csv(RAIZ / "datos" / "fcd" / "climate_puerto-ayora.csv")
    f = f[f.observation_date >= "2023-12-01"].dropna(subset=["precipitation"])
    obs.append(pd.DataFrame({"punto": "fcd/puerto_ayora", "fecha": f.observation_date, "obs_mm": f.precipitation}))
    o = pd.concat(obs, ignore_index=True)
    o = o[(o.obs_mm >= 0) & (o.obs_mm < 400)]
    return o.drop_duplicates(["punto", "fecha"])


def obs_3h():
    """Máximo de lluvia en 3 h por día (IERSE, horas completas)."""
    h = pd.read_csv(RAIZ / "datos" / "ierse-wsn" / "horario.csv", parse_dates=["fecha_hora_local"])
    h = h[h.registros >= 10]  # ≥ 10 de 12 registros de 5 min
    filas = []
    for est, s in h.groupby("estacion_id"):
        s = s.set_index("fecha_hora_local").lluvia_mm.asfreq("h")
        r3 = s.rolling(3, min_periods=3).sum()
        dia = r3.groupby(r3.index.strftime("%Y-%m-%d")).max()
        filas.append(pd.DataFrame({"punto": "ierse/" + est, "fecha": dia.index, "obs3h_mm": dia.values}))
    return pd.concat(filas).dropna()


# ---------------------------------------------------------------- pronósticos

def pronosticos(ruta=ARCHIVO):
    p = pd.read_csv(ruta, parse_dates=["hora_utc"])
    # La lluvia de Open-Meteo es la suma de la hora que TERMINA en hora_utc. Día de Galápagos (UTC−6):
    # la hora pertenece al día en que empieza.
    inicio_local = p.hora_utc - pd.Timedelta(hours=7)
    p["fecha"] = inicio_local.dt.strftime("%Y-%m-%d")
    p["hora_local"] = inicio_local.dt.hour
    dia = p.groupby(["punto", "modelo", "anticipacion_dias", "fecha"]).agg(
        fc_mm=("lluvia_mm", "sum"), horas=("lluvia_mm", "size")).reset_index()
    dia = dia[dia.horas >= 24].drop(columns="horas")

    # Máximo en 3 h por día (ventanas que empiezan en el día).
    p = p.sort_values("hora_utc")
    p["r3"] = p.groupby(["punto", "modelo", "anticipacion_dias"]).lluvia_mm.transform(
        lambda s: s.rolling(3, min_periods=3).sum())
    m3 = p.groupby(["punto", "modelo", "anticipacion_dias", "fecha"]).r3.max().rename("fc3h_mm").reset_index()
    celdas = p.groupby(["punto", "modelo"])[["lat_celda", "lon_celda"]].first().reset_index()
    return dia.merge(m3, how="left"), celdas


def consenso(dia):
    """Promedio, entre modelos, del percentil de cada pronóstico dentro de su propia climatología
    (por punto y anticipación). No depende del sesgo de cada modelo. Se excluye IFS 9 km, que solo
    tiene archivo desde fines de 2025, para que el consenso sea homogéneo en todo el periodo."""
    base = dia[dia.modelo != "ecmwf_ifs"].copy()
    base["pct"] = base.groupby(["punto", "modelo", "anticipacion_dias"]).fc_mm.rank(pct=True)
    c = base.groupby(["punto", "anticipacion_dias", "fecha"]).agg(fc_mm=("pct", "mean"), n=("pct", "size")).reset_index()
    c = c[c.n >= 5].drop(columns="n")
    c["modelo"] = "consenso"
    # Consenso retardado: lo que se sabe en D−N con las corridas de N, N+1 y N+2 días antes.
    r = []
    for n in (1, 2, 3, 5):
        sub = c[c.anticipacion_dias.isin([n, n + 1, n + 2])]
        g = sub.groupby(["punto", "fecha"]).agg(fc_mm=("fc_mm", "mean"), k=("fc_mm", "size")).reset_index()
        g = g[g.k == 3].drop(columns="k")
        g["anticipacion_dias"], g["modelo"] = n, "consenso_retardado"
        r.append(g)
    return pd.concat([c] + r, ignore_index=True)


def referencias(o, dia):
    """Pronósticos sin modelo, para saber cuánto aporta un modelo de verdad:
    - climatología: lluvia media diaria del mes calendario en la estación, calculada sin el año evaluado
      (GSC desde 2015; FCD Puerto Ayora desde 1965; las estaciones de IERSE, que solo tienen 2026, usan
      la serie FCD de Bellavista 1987–2019 en la parte alta y la de Puerto Ayora en Militar);
    - persistencia: la lluvia medida N días antes (para la anticipación N); es algo optimista, porque al
      emitir el pronóstico ese día aún no ha terminado."""
    larga = []
    gsc = RAIZ / "privado" / "gsc_diario.csv"
    if gsc.exists():
        g = pd.read_csv(gsc)
        g["fecha"] = (pd.to_datetime(g.ts.str.replace("Z", "")) - pd.Timedelta(hours=5)).dt.strftime("%Y-%m-%d")
        larga.append(pd.DataFrame({"punto": "gsc/" + g.estacion, "fecha": g.fecha, "mm": g.valor}))
    for nombre, puntos in (("climate_puerto-ayora.csv", ["fcd/puerto_ayora", "ierse/n_glps06"]),
                           ("climate_bellavista.csv", ["ierse/n_glps01", "ierse/n_glps05", "ierse/n_glps09"])):
        f = pd.read_csv(RAIZ / "datos" / "fcd" / nombre).dropna(subset=["precipitation"])
        f = f[(f.precipitation >= 0) & (f.precipitation < 400)]
        for pt in puntos:
            larga.append(pd.DataFrame({"punto": pt, "fecha": f.observation_date, "mm": f.precipitation}))
    larga = pd.concat(larga)
    larga["mes"], larga["anio"] = larga.fecha.str[5:7], larga.fecha.str[:4]
    base = dia[["punto", "fecha", "anticipacion_dias"]].drop_duplicates()
    base["mes"], base["anio"] = base.fecha.str[5:7], base.fecha.str[:4]
    suma = larga.groupby(["punto", "mes", "anio"]).mm.agg(["sum", "count"]).reset_index()
    tot = suma.groupby(["punto", "mes"])[["sum", "count"]].sum().reset_index()
    c = base.merge(suma, how="left", on=["punto", "mes", "anio"]).merge(tot, on=["punto", "mes"], suffixes=("_a", ""))
    c["fc_mm"] = (c["sum"] - c["sum_a"].fillna(0)) / (c["count"] - c["count_a"].fillna(0))
    c["modelo"] = "ref_climatologia"
    clim = c[["punto", "fecha", "anticipacion_dias", "modelo", "fc_mm"]]

    pe = []
    for n in sorted(base.anticipacion_dias.unique()):
        if n == 0:
            continue
        x = o.copy()
        x["fecha"] = (pd.to_datetime(x.fecha) + pd.Timedelta(days=int(n))).dt.strftime("%Y-%m-%d")
        x = x.rename(columns={"obs_mm": "fc_mm"})
        x["anticipacion_dias"], x["modelo"] = n, "ref_persistencia"
        pe.append(x)
    return pd.concat([clim.dropna()] + pe, ignore_index=True)


# ---------------------------------------------------------------- calibración (consenso → probabilidad)

# Una curva por anticipación. OJO: en el archivo de Open-Meteo, «1 día» (previous_day1) usa corridas que
# estuvieron listas hasta la madrugada del mismo día: equivale al recuadro «hoy» de la web, «2 días» a
# «mañana», etc. (pronostico.py usa la anticipación k+1 para el día k).
PLAZOS = {"1": [1], "2": [2], "3": [3], "5": [5]}
BSS_MINIMO = 0.03  # por debajo, la curva no muestra habilidad: se publica «no evaluable»
# Curvas prestadas. En garúa casi nunca llueve fuerte en la costa ni en San Cristóbal (0 y 2 días en
# 2024–2026): no hay con qué calibrar, pero «sin señal» fijo sería peligroso en un día anómalo como el
# 30-oct (consenso 0,97 en Puerto Ayora; el INAMHI midió 94 y 135 mm el 30 y el 31). Se usa la curva de
# la temporada lluviosa: en 2024–2026 no habría dado ninguna «señal alta» en garúa y solo 1 «moderada».
PRESTADA = {("santa_cruz_alta", "lluviosa"): ("san_cristobal_alta", "lluviosa"),  # IERSE empezó en abr-2026: solo mayo
            ("costa", "garua"): ("costa", "lluviosa"),
            ("san_cristobal_alta", "garua"): ("san_cristobal_alta", "lluviosa")}
NIVELES = [("alta", 0.35), ("moderada", 0.15), ("sin_senal", 0.0)]  # por probabilidad calibrada de ≥ 20 mm


def logistica(x, y, l2=1e-2):
    X = np.column_stack([np.ones_like(x), x])
    w = np.zeros(2)
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ w))
        H = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.eye(2)
        paso = np.linalg.solve(H, X.T @ (y - p) - l2 * w)
        w += paso
        if np.abs(paso).max() < 1e-8:
            break
    return w


def prob(w, x):
    return 1 / (1 + np.exp(-(w[0] + w[1] * np.asarray(x))))


def calibrar(j):
    """Probabilidad de que la estación más lluviosa del grupo supere u mm, según el consenso (promedio
    en el grupo), con una curva logística por grupo, temporada y anticipación. Validación cruzada
    dejando fuera un año (o un mes, si solo hay un año)."""
    c = j[j.modelo == "consenso"]
    filas, curvas, cvs = [], {}, []
    for g, (puntos, _) in GRUPOS.items():
        z = c[c.punto.isin(puntos)].groupby(["fecha", "anticipacion_dias", "temporada"]).agg(
            cons=("fc_mm", "mean"), obs=("obs_mm", "max")).reset_index()
        for temp in ("lluviosa", "garua"):
            for plazo, ns in PLAZOS.items():
                d = z[(z.temporada == temp) & z.anticipacion_dias.isin(ns)]
                for u in UMBRALES:
                    y = (d.obs >= u).to_numpy(float)
                    fila = {"grupo": g, "temporada": temp, "plazo": plazo, "umbral_mm": u, "n": len(d),
                            "dias": int(d.fecha.nunique()), "eventos": int(y.sum()), "frec_base": round(y.mean(), 4) if len(y) else None}
                    if len(d) and y.sum() >= 5:
                        w = logistica(d.cons.to_numpy(), y)
                        # Validación cruzada: fuera un año; si solo hay un año, fuera un mes.
                        bloque = d.fecha.str[:4] if d.fecha.str[:4].nunique() > 1 else d.fecha.str[:7]
                        pcv = np.full(len(d), np.nan)
                        base_cv = np.full(len(d), np.nan)
                        for b in bloque.unique():
                            dentro = (bloque != b).to_numpy()
                            if y[dentro].sum() >= 2:
                                pcv[~dentro] = prob(logistica(d.cons.to_numpy()[dentro], y[dentro]), d.cons.to_numpy()[~dentro])
                                base_cv[~dentro] = y[dentro].mean()
                        ok = ~np.isnan(pcv)
                        if u == 20:
                            cvs.append(pd.DataFrame({"grupo": g, "temporada": temp, "plazo": plazo, "fecha": d.fecha.to_numpy(),
                                                     "anticipacion_dias": d.anticipacion_dias.to_numpy(), "cons": d.cons.to_numpy(),
                                                     "p_cv": pcv, "obs_max": d.obs.to_numpy()}))
                        bs, bs0 = np.mean((pcv[ok] - y[ok]) ** 2), np.mean((base_cv[ok] - y[ok]) ** 2)
                        fila.update({"a": round(w[0], 4), "b": round(w[1], 4),
                                     "brier_cv": round(bs, 4), "bss_cv": round(1 - bs / bs0, 3) if bs0 else None,
                                     "auc": round(auc(d.cons, y.astype(bool)), 3),
                                     **{f"p_cons_{x:.2f}": round(float(prob(w, x)), 3) for x in (0.5, 0.7, 0.8, 0.9, 0.95)}})
                        curvas[(g, temp, plazo, u)] = {"a": float(w[0]), "b": float(w[1]), "n": len(d), "eventos": int(y.sum()),
                                                       "bss_cv": fila["bss_cv"], "frec_base": fila["frec_base"],
                                                       "estado": "ok" if (fila["bss_cv"] or 0) >= BSS_MINIMO else "sin_habilidad"}
                    elif len(d):
                        curvas[(g, temp, plazo, u)] = {"a": None, "b": None, "n": len(d), "eventos": int(y.sum()),
                                                       "frec_base": fila["frec_base"],
                                                       "estado": "sin_eventos" if y.sum() == 0 else "pocos_eventos"}
                    filas.append(fila)
    cal = pd.DataFrame(filas)
    cal.to_csv(SAL / "calibracion_logistica.csv", index=False)
    # ¿Qué pasó cuando la señal (con validación cruzada) estuvo en cada nivel? Solo 20 mm.
    cv = pd.concat(cvs, ignore_index=True)
    cv["nivel"] = [next(nv for nv, lim in NIVELES if x >= lim) if x == x else None for x in cv.p_cv]
    cv.to_csv(SAL / "senal_validacion_cruzada.csv.gz", index=False, float_format="%.3f")
    niv = cv.dropna(subset=["nivel"]).groupby(["grupo", "temporada", "plazo", "nivel"]).agg(
        n=("obs_max", "size"), p_media=("p_cv", "mean"), frec_10=("obs_max", lambda x: (x >= 10).mean()),
        frec_20=("obs_max", lambda x: (x >= 20).mean()), frec_50=("obs_max", lambda x: (x >= 50).mean())).round(3).reset_index()
    # De los días con ≥ 20 y ≥ 50 mm, ¿qué nivel tuvieron, según la anticipación?
    fuertes = pd.concat([cv[cv.obs_max >= u].groupby(["grupo", "temporada", "plazo"]).nivel.value_counts().unstack(fill_value=0)
                         .assign(umbral_mm=u) for u in (20, 50)]).reset_index()
    niv.to_csv(SAL / "senal_niveles.csv", index=False)
    fuertes.to_csv(SAL / "senal_dias_fuertes.csv", index=False)
    return cal, curvas


def climatologia_zonas():
    """Cuantiles de la lluvia diaria pronosticada por cada modelo en cada punto de zonas_geo.json y
    cada anticipación: con eso el pronóstico en vivo convierte milímetros en percentiles."""
    ruta = RAIZ / "datos" / "pronostico-archivo" / "pronostico_horario_zonas.csv.gz"
    if not ruta.exists():
        print("Aviso: falta pronostico_horario_zonas.csv.gz (06 --puntos zonas); no se escribe la climatología")
        return None
    dia, _ = pronosticos(ruta)
    q = np.linspace(0, 1, 101)
    out = {}
    for (pt, mod, n), s in dia.groupby(["punto", "modelo", "anticipacion_dias"]):
        if len(s) >= 300:
            out.setdefault(pt.split("/", 1)[1], {}).setdefault(mod, {})[str(int(n))] = [round(float(x), 2) for x in np.quantile(s.fc_mm, q)]
    return out


# ---------------------------------------------------------------- métricas

def auc(score, evento):
    """Área bajo la curva ROC (Mann–Whitney), con empates a la mitad."""
    score, evento = np.asarray(score, float), np.asarray(evento, bool)
    n1, n0 = evento.sum(), (~evento).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(score).rank().to_numpy()
    return (r[evento].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def auc_ic(df, umbral, col="fc_mm", obs="obs_mm"):
    """AUC con intervalo bootstrap del 90 % remuestreando fechas (los puntos de un mismo día van juntos)."""
    ev = df[obs] >= umbral
    a = auc(df[col], ev)
    if np.isnan(a) or ev.sum() < 3:
        return a, np.nan, np.nan, int(ev.sum())
    fechas = df.fecha.unique()
    idx = {f: np.flatnonzero(df.fecha.to_numpy() == f) for f in fechas}
    bs = []
    for _ in range(N_BOOT):
        sel = np.concatenate([idx[f] for f in RNG.choice(fechas, len(fechas))])
        bs.append(auc(df[col].to_numpy()[sel], ev.to_numpy()[sel]))
    lo, hi = np.nanpercentile(bs, [5, 95])
    return a, lo, hi, int(ev.sum())


def tabla_contingencia(fc, ob, u_fc, u_ob):
    s, o = fc >= u_fc, ob >= u_ob
    a, b, c, d = (s & o).sum(), (s & ~o).sum(), (~s & o).sum(), (~s & ~o).sum()
    n = a + b + c + d
    ar = (a + b) * (a + c) / n if n else 0
    return {"aciertos": int(a), "falsas_alarmas": int(b), "fallos": int(c),
            "POD": round(a / (a + c), 3) if a + c else None,
            "FAR": round(b / (a + b), 3) if a + b else None,
            "ETS": round((a - ar) / (a + b + c - ar), 3) if (a + b + c - ar) else None}


def metricas(df):
    """df: punto, fecha, fc_mm, obs_mm (un modelo y una anticipación)."""
    m = {"n_dias": int(df.fecha.nunique()), "n": int(len(df)),
         "obs_media_mm": round(df.obs_mm.mean(), 2), "fc_media_mm": round(df.fc_mm.mean(), 2),
         "spearman": round(df[["fc_mm", "obs_mm"]].corr("spearman").iloc[0, 1], 3)}
    for u in UMBRALES:
        a, lo, hi, n1 = auc_ic(df, u)
        m[f"auc_{u}"] = None if np.isnan(a) else round(a, 3)
        m[f"auc_{u}_ic90"] = None if np.isnan(lo) else [round(lo, 3), round(hi, 3)]
        m[f"eventos_{u}"] = n1
        # Umbral del pronóstico con la misma frecuencia que el evento observado (sin sesgo de frecuencia).
        if n1 >= 3:
            q = df.fc_mm.quantile(1 - n1 / len(df))
            m[f"ets_frec_{u}"] = tabla_contingencia(df.fc_mm, df.obs_mm, q, u)["ETS"]
    return m


def main():
    SAL.mkdir(parents=True, exist_ok=True)
    o = observaciones()
    dia, celdas = pronosticos()
    o3 = obs_3h()

    # ¿El día de la FCD coincide con el día del modelo? Se prueba con un desfase de −1, 0 y +1 día.
    fcd = o[o.punto == "fcd/puerto_ayora"].set_index("fecha").obs_mm
    ref = dia[(dia.punto == "fcd/puerto_ayora") & (dia.modelo == "ecmwf_ifs025") & (dia.anticipacion_dias == 0)].set_index("fecha").fc_mm
    desfases = {}
    for k in (-1, 0, 1):
        f2 = fcd.copy()
        f2.index = (pd.to_datetime(f2.index) + pd.Timedelta(days=k)).strftime("%Y-%m-%d")
        j = pd.concat([f2, ref], axis=1, join="inner").dropna()
        desfases[k] = round(j.corr("spearman").iloc[0, 1], 3)
    mejor = max(desfases, key=desfases.get)
    if mejor != 0:
        idx = o.punto == "fcd/puerto_ayora"
        o.loc[idx, "fecha"] = (pd.to_datetime(o.loc[idx, "fecha"]) + pd.Timedelta(days=mejor)).dt.strftime("%Y-%m-%d")

    todo = pd.concat([dia, consenso(dia), referencias(o, dia)], ignore_index=True)
    j = todo.merge(o, on=["punto", "fecha"])
    # Las referencias se evalúan solo en los días y puntos en que hay pronóstico (IFS 0,25°, el archivo más largo).
    comun = j[j.modelo == "ecmwf_ifs025"][["punto", "fecha", "anticipacion_dias"]].drop_duplicates()
    refs = j[j.modelo.str.startswith("ref_")]
    refs = refs.merge(comun)
    j = pd.concat([j[~j.modelo.str.startswith("ref_")], refs], ignore_index=True)
    j["temporada"] = np.where(pd.to_datetime(j.fecha).dt.month.isin(LLUVIOSA), "lluviosa", "garua")
    j.to_csv(SAL / "pares_diarios.csv.gz", index=False, float_format="%.2f")

    # Métricas por grupo × modelo × anticipación (y por temporada).
    filas = []
    for g, (puntos, _) in GRUPOS.items():
        for (mod, n), df in j[j.punto.isin(puntos)].groupby(["modelo", "anticipacion_dias"]):
            for temp, sub in [("todo", df)] + list(df.groupby("temporada")):
                if len(sub) < 30:
                    continue
                filas.append({"grupo": g, "modelo": mod, "anticipacion_dias": int(n), "temporada": temp,
                              "desde": sub.fecha.min(), "hasta": sub.fecha.max(), **metricas(sub)})
    met = pd.DataFrame(filas)
    met.to_csv(SAL / "metricas.csv", index=False)

    # Mismo periodo para todos los modelos (IFS 9 km tiene archivo más corto): comparación justa.
    ini9 = dia[dia.modelo == "ecmwf_ifs"].fecha.min()
    filas = []
    if isinstance(ini9, str):
        for g, (puntos, _) in GRUPOS.items():
            sub0 = j[j.punto.isin(puntos) & (j.fecha >= ini9)]
            for (mod, n), df in sub0.groupby(["modelo", "anticipacion_dias"]):
                if len(df) >= 30:
                    filas.append({"grupo": g, "modelo": mod, "anticipacion_dias": int(n), "desde": df.fecha.min(),
                                  "hasta": df.fecha.max(), **metricas(df)})
    pd.DataFrame(filas).to_csv(SAL / "metricas_periodo_ifs9km.csv", index=False)

    # Intensidad en 3 h (Santa Cruz, IERSE).
    j3 = dia.dropna(subset=["fc3h_mm"]).merge(o3, on=["punto", "fecha"])
    f3 = []
    for (mod, n), df in j3.groupby(["modelo", "anticipacion_dias"]):
        a, lo, hi, n1 = auc_ic(df.rename(columns={"fc3h_mm": "x"}), 20, col="x", obs="obs3h_mm")
        f3.append({"modelo": mod, "anticipacion_dias": int(n), "n": len(df), "eventos_3h_20": n1,
                   "auc_3h_20": None if np.isnan(a) else round(a, 3),
                   "fc3h_max_mm": round(df.fc3h_mm.max(), 1), "obs3h_max_mm": round(df.obs3h_mm.max(), 1)})
    pd.DataFrame(f3).to_csv(SAL / "metricas_3h.csv", index=False)

    # Eventos: los días más lluviosos de cada grupo y qué decía cada modelo con 1–3 días.
    ev_filas = []
    for g, (puntos, _) in GRUPOS.items():
        sub = o[o.punto.isin(puntos) & (o.fecha >= "2024-01-01")]
        top = sub.sort_values("obs_mm", ascending=False).drop_duplicates("fecha").head(12)
        for _, r in top.iterrows():
            fila = {"grupo": g, "fecha": r.fecha, "punto": r.punto, "obs_mm": r.obs_mm}
            for mod in NOMBRE_MODELO:
                for n in (0, 1, 2, 3):
                    x = todo[(todo.punto == r.punto) & (todo.fecha == r.fecha) & (todo.modelo == mod) & (todo.anticipacion_dias == n)]
                    if len(x):
                        fila[f"{mod}_d{n}"] = round(float(x.fc_mm.iloc[0]), 2 if mod.startswith("consenso") else 1)
            ev_filas.append(fila)
    eventos = pd.DataFrame(ev_filas)
    eventos.to_csv(SAL / "eventos.csv", index=False)

    # Calibración orientativa: frecuencia observada de días ≥ 20 mm según el percentil del consenso a 1 día.
    cal = []
    c1 = j[(j.modelo == "consenso_retardado") & (j.anticipacion_dias == 1)]
    for g, (puntos, _) in GRUPOS.items():
        sub = c1[c1.punto.isin(puntos)]
        if sub.empty:
            continue
        for lo, hi in [(0, .5), (.5, .75), (.75, .9), (.9, .95), (.95, 1.01)]:
            s = sub[(sub.fc_mm >= lo) & (sub.fc_mm < hi)]
            for temp, s2 in [("todo", s)] + list(s.groupby("temporada")):
                if len(s2):
                    cal.append({"grupo": g, "temporada": temp, "percentil_consenso": f"{lo:.2f}–{min(hi, 1):.2f}", "n": len(s2),
                                "frec_10mm": round((s2.obs_mm >= 10).mean(), 3), "frec_20mm": round((s2.obs_mm >= 20).mean(), 3),
                                "frec_50mm": round((s2.obs_mm >= 50).mean(), 3)})
    pd.DataFrame(cal).to_csv(SAL / "calibracion_consenso.csv", index=False)

    figuras(met, j)
    cal, curvas = calibrar(j)
    clim = climatologia_zonas()
    escribir_calibracion(curvas, clim, dia)
    resumen = {
        "generado": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "periodo_obs": [o.fecha.min(), o.fecha.max()],
        "desfase_fcd_dias": {"spearman_por_desfase": desfases, "aplicado": mejor},
        "inicio_archivo_por_modelo": dia.groupby("modelo").fecha.min().to_dict(),
        "celdas": celdas.to_dict("records"),
        "dias_por_grupo": {g: int(j[j.punto.isin(p) & (j.modelo == "ecmwf_ifs025") & (j.anticipacion_dias == 1)].fecha.nunique())
                           for g, (p, _) in GRUPOS.items()},
    }
    (SAL / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(resumen["desfase_fcd_dias"]), resumen["dias_por_grupo"])


GRUPO_PUNTO = {  # punto de zonas_geo.json → grupo de calibración; «sin_calibrar» si no hay estación cerca
    "cascada-alta": ("santa_cruz_alta", True), "santa-rosa": ("santa_cruz_alta", True), "bellavista": ("santa_cruz_alta", True),
    "puerto-ayora": ("costa", True), "el-junco": ("san_cristobal_alta", True), "puerto-baquerizo": ("costa", False),
    "sierra-negra": ("san_cristobal_alta", False), "puerto-villamil": ("costa", False)}


def escribir_calibracion(curvas, clim, dia):
    """recolector/pronostico_calibracion.json: lo que necesita el pronóstico en vivo (archivo generado)."""
    cal = {}
    for g in GRUPOS:
        for temp in ("lluviosa", "garua"):
            for plazo in PLAZOS:
                for u in UMBRALES:
                    k = (g, temp, plazo, u)
                    alt = PRESTADA.get((g, temp))
                    if alt:
                        c = curvas.get((alt[0], alt[1], plazo, u))
                        propia = curvas.get(k) or {}
                        c = {**c, "prestada_de": f"{alt[0]} ({alt[1]})", "frec_base": propia.get("frec_base", c.get("frec_base")),
                             "eventos_propios": propia.get("eventos"), "bss_cv": None, "bss_cv_origen": c.get("bss_cv")} if c else None
                    else:
                        c = curvas.get(k)
                    cal.setdefault(g, {}).setdefault(temp, {}).setdefault(plazo, {})[str(u)] = c or {"a": None, "b": None, "estado": "sin_datos"}
    out = {"generado_por": "clima/scripts/07_pronostico_evaluacion.py (no editar a mano)",
           "generado": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
           "modelos_consenso": sorted(m for m in dia.modelo.unique() if m != "ecmwf_ifs"),
           "temporada_lluviosa_meses": sorted(LLUVIOSA), "plazos": PLAZOS,
           "grupo_punto": {k: {"grupo": v[0], "calibrado": v[1]} for k, v in GRUPO_PUNTO.items()},
           "calibracion": cal, "climatologia": clim}
    (RAIZ / "recolector" / "pronostico_calibracion.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))


def figuras(met, j):
    for umbral in (20, 50):
        fig, ejes = plt.subplots(1, len(GRUPOS), figsize=(5 * len(GRUPOS), 4), sharey=True)
        for ax, (g, (_, desc)) in zip(ejes, GRUPOS.items()):
            sub = met[(met.grupo == g) & (met.temporada == "todo")]
            for mod in NOMBRE_MODELO:
                s = sub[sub.modelo == mod].sort_values("anticipacion_dias")
                if s.empty or s[f"auc_{umbral}"].isna().all():
                    continue
                estilo = dict(lw=2.5, color="k") if mod.startswith("consenso") else dict(lw=1, alpha=.8)
                if mod == "consenso_retardado":
                    estilo["ls"] = "--"
                if mod.startswith("ref_"):
                    estilo = dict(lw=2, color="grey", ls=":" if mod == "ref_persistencia" else "-.")
                ax.plot(s.anticipacion_dias, s[f"auc_{umbral}"], marker="o", label=NOMBRE_MODELO[mod], **estilo)
            ax.axhline(.5, color="grey", lw=.8, ls=":")
            ax.set_title(desc, fontsize=9)
            ax.set_xlabel("anticipación (días)")
            ax.set_ylim(.4, 1)
        ejes[0].set_ylabel(f"AUC para días con ≥ {umbral} mm (0,5 = azar)")
        ejes[-1].legend(fontsize=7, loc="lower left")
        fig.tight_layout()
        fig.savefig(SAL / f"f_auc_{umbral}mm.png", dpi=130)
        plt.close(fig)


if __name__ == "__main__":
    main()
