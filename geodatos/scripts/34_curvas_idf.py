#!/usr/bin/env python3
"""Curvas IDF (intensidad–duración–frecuencia) PROVISIONALES de Santa Cruz y San Cristóbal (#24) y periodo de retorno
de las 500 tormentas sintéticas de cada isla (#26).

Modelo propio, no dato oficial: sirven de orden de magnitud y para poner las tormentas sintéticas en una escala de años,
no para diseñar obras. La referencia oficial es el estudio de intensidades del INAMHI (2015), que no tenemos (#77).

Método («índice de crecida» con dos fuentes):
  1. Lluvia de 1 día: máximos anuales de los pluviómetros de la FCD (Puerto Ayora 1965–2025, Bellavista 1987–2019),
     ajustados con Gumbel (central) y GEV (sensibilidad), con intervalos por remuestreo de años.
  2. Paso a 1, 2, 3, 6, 12 y 24 h móviles: razones del reanálisis GAR horario (TU Berlín, WRF 2 km forzado con ERA5,
     1980–2025, CC BY 4.0): media de los máximos anuales de cada duración / media de los máximos anuales de 1 día.
     Lluvia MODELADA [E]. GAR horario pesa ≈30 GB: solo se leen, por HTTP y día a día, los días más lluviosos de cada
     año en cada isla (los 5 de mayor lluvia diaria), elegidos con la lluvia diaria de GAR del script 29. Las ventanas
     de 1–12 h se cuentan dentro del día UTC; 24 h móviles = 1 día fijo × 1,13 (Weiss 1964).
  3. Cada pluviómetro toma la lluvia de 1 día del pluviómetro FCD más parecido en altura (Puerto Ayora < 100 m;
     Bellavista arriba), sin escalarla con GAR: el gradiente espacial de GAR no está validado y en la parte alta
     exagera (Santa Rosa). Lo que diría GAR se guarda como «factor_gar_informativo».
  4. San Cristóbal no tiene serie medida larga (#78): toma prestada la curva de Santa Cruz a la misma altura, con las
     razones horarias de GAR en sus propios puntos. Valen aún menos que las de Santa Cruz.
  5. Contraste con la lluvia medida cada 5 min (IERSE, abr-2026 → hoy) y con el 30-oct-2026.
  6. Tormentas sintéticas: periodo de retorno de la lluvia que marcan los pluviómetros de cada zona (máximo entre
     duraciones), curvas «probabilidad de inundarse según el periodo de retorno» y mapas por periodo de retorno.

Uso, desde geodatos/:
  .venv/bin/python -I scripts/34_curvas_idf.py descargar [--procesos 3] [--completo AÑO …]   # --completo: años enteros para verificar (≈10 min c/u)
  .venv/bin/python -I scripts/34_curvas_idf.py analizar
  .venv/bin/python -I scripts/34_curvas_idf.py tormentas
  .venv/bin/python -I scripts/34_curvas_idf.py figuras
Horas: GAR en UTC (el valor horario de la hora k es la media de la hora que termina en k). IERSE en UTC−6.
"""
import argparse
import json
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

GEO = Path(__file__).resolve().parent.parent
EST = GEO / "estudios" / "idf"
CACHE = EST / "cache"
GAR_D = GEO / "datos" / "marburg_darwin" / "bruto" / "gar"      # lluvia diaria de GAR (script 29 --descargar)
GAR_H_URL = "https://data.klima.tu-berlin.de/GAR/v1/d02km/h/2d/GAR_d02km_h_2d_prcp_{a}.nc#mode=bytes"
FCD = GEO.parent / "clima" / "datos" / "fcd"
IERSE = GEO.parent / "clima" / "datos" / "ierse-wsn"
ANIOS = range(1980, 2026)
CAJAS = {"santa-cruz": (-90.60, -90.15, -0.84, -0.50), "san-cristobal": (-89.66, -89.22, -0.98, -0.66)}
K_DIAS = 5                     # días candidatos por isla y año. La conexión desde Galápagos da ≈0,1–0,5 MB/s y cada día de
                               # GAR horario pesa ≈1,8 MB: 46 años ≈ 420 días ≈ 1 h. Sin días vecinos: las ventanas no cruzan
                               # la medianoche UTC (18:00 local); el paso de 1 día fijo a 24 h móviles usa el factor de Weiss.
MIN_ANIOS = 30                  # años de GAR horario necesarios para analizar
WEISS = 1.13                   # 24 h móviles / 1 día de lectura fija (Weiss 1964)
DURACIONES = (1, 2, 3, 6, 12, 24)


# ------------------------------------------------------------------ malla de GAR
def malla():
    import xarray as xr
    hg = xr.open_dataset(GAR_D / "GAR_d02km_static_hgt.nc")
    lm = xr.open_dataset(GAR_D / "GAR_d02km_static_landmask.nc")
    lat, lon, z = hg.lat.values, hg.lon.values, hg.hgt.values[0]
    tierra = lm.landmask.values[0] > 0.5
    sel = np.zeros_like(tierra)
    isla = np.full(tierra.shape, "", dtype=object)
    for nom, (x0, x1, y0, y1) in CAJAS.items():
        m = (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
        sel |= m
        isla[m & tierra] = nom
    ii, jj = np.where(sel)
    i0, i1, j0, j1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    return dict(caja=(int(i0), int(i1), int(j0), int(j1)), lat=lat[i0:i1, j0:j1], lon=lon[i0:i1, j0:j1],
                z=z[i0:i1, j0:j1], tierra=tierra[i0:i1, j0:j1], isla=isla[i0:i1, j0:j1])


def dias_candidatos(a, g):
    """Días (índice desde el 1-ene) más lluviosos del año en cada isla según GAR diario."""
    import xarray as xr
    i0, i1, j0, j1 = g["caja"]
    with xr.open_dataset(GAR_D / f"GAR_d02km_d_2d_prcp_{a}.nc") as d:
        pr = d.prcp.values[:, i0:i1, j0:j1] * 24.0                  # mm/día (día UTC)
    nd = pr.shape[0]
    dias = set()
    for nom in CAJAS:
        m = g["isla"] == nom
        serie = np.nanmax(pr[:, m], axis=1)
        for k in np.argsort(serie)[::-1][:K_DIAS]:
            dias.add(int(k))
    return sorted(dias), pr


def _bajar_anio(args):
    a, completo = args
    dest = CACHE / "gar_h" / f"{a}.npz"
    if dest.exists():
        return a, "ya estaba", 0.0
    import netCDF4
    g = malla()
    i0, i1, j0, j1 = g["caja"]
    dias, _ = dias_candidatos(a, g)
    if completo:
        dias = list(range(366 if (a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)) else 365))
    t = time.time()
    for intento in range(5):
        try:
            ds = netCDF4.Dataset(GAR_H_URL.format(a=a))
            break
        except OSError:
            time.sleep(10 * (intento + 1))
    else:
        return a, "no se pudo abrir", 0.0
    v = ds["prcp"]
    bloques = []
    for k in dias:
        for intento in range(5):
            try:
                bloques.append(np.asarray(v[k * 24:(k + 1) * 24, i0:i1, j0:j1], dtype="float32"))
                break
            except (OSError, RuntimeError):
                time.sleep(5 * (intento + 1))
        else:
            ds.close()
            return a, f"falló el día {k}", time.time() - t
    ds.close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, dias=np.array(dias), prcp=np.stack(bloques).astype("float16"), completo=completo)
    tmp.rename(dest)
    return a, f"{len(dias)} días", time.time() - t


def descargar(procesos, completos):
    tareas = [(a, False) for a in ANIOS]      # los años completos (verificación) van aparte, al final
    with Pool(procesos) as pool:
        for a, msg, s in pool.imap_unordered(_bajar_anio, tareas):
            print(f"  {a}: {msg} ({s:.0f} s)", flush=True)
    for a in completos:
        dest = CACHE / "gar_h_completo" / f"{a}.npz"
        if dest.exists():
            continue
        r = _bajar_completo(a)
        print(f"  {a} completo: {r}", flush=True)


def _bajar_completo(a):
    """Un año entero (verificación de que los días candidatos atrapan los máximos de 1–24 h)."""
    import netCDF4
    g = malla()
    i0, i1, j0, j1 = g["caja"]
    ds = netCDF4.Dataset(GAR_H_URL.format(a=a))
    v = ds["prcp"]
    nd = v.shape[0] // 24
    bloques = []
    for k in range(nd):
        for intento in range(5):
            try:
                bloques.append(np.asarray(v[k * 24:(k + 1) * 24, i0:i1, j0:j1], dtype="float32"))
                break
            except (OSError, RuntimeError):
                time.sleep(5 * (intento + 1))
        else:
            ds.close()
            return f"falló el día {k}"
    ds.close()
    dest = CACHE / "gar_h_completo" / f"{a}.npz"
    dest.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(dest, dias=np.arange(nd), prcp=np.stack(bloques).astype("float16"), completo=True)
    return f"{nd} días"


# ------------------------------------------------------------------ máximos anuales de GAR
def am_por_duracion(dias, P):
    """Máximo de la lluvia en d horas móviles (mm) en cada celda, dentro de tramos de días consecutivos."""
    cortes = list(np.where(np.diff(dias) != 1)[0] + 1) + [len(dias)]
    out, ini = {}, 0
    for fin in cortes:
        S = P[ini:fin].reshape(-1, *P.shape[2:]).astype("float64")              # horas × celdas, mm en cada hora
        C = np.concatenate([np.zeros((1,) + S.shape[1:]), np.cumsum(S, axis=0)])
        for d in DURACIONES:
            m = (C[d:] - C[:-d]).max(axis=0) if C.shape[0] - 1 >= d else C[-1]
            out[d] = m if d not in out else np.maximum(out[d], m)
        ini = fin
    return out


def gar_max_anuales(g):
    """AM[d]: (años, ny, nx) por duración móvil, desde los días candidatos; AM1d: máximo diario fijo (día UTC) del año entero."""
    anios, AM, AM1d, chequeo = [], {d: [] for d in DURACIONES}, [], []
    for a in ANIOS:
        f = CACHE / "gar_h" / f"{a}.npz"
        if not f.exists():
            continue
        z = np.load(f)
        dias, P = z["dias"], z["prcp"].astype("float32")
        r = am_por_duracion(dias, P)
        _, pr = dias_candidatos(a, g)
        anios.append(a)
        for d in DURACIONES:
            AM[d].append(r[d])
        AM1d.append(pr.max(axis=0))
        # coherencia: suma de las horas de un día candidato frente a la lluvia diaria de GAR
        k = int(dias[len(dias) // 2])
        chequeo.append(float(np.nanmedian(np.abs(P[len(dias) // 2].sum(0) - pr[k]))))
    return np.array(anios), {d: np.stack(v) for d, v in AM.items()}, np.stack(AM1d), chequeo


def verificar_candidatos(g):
    """Años completos: ¿los días candidatos atrapan el máximo anual de cada duración?"""
    out = {}
    for f in sorted((CACHE / "gar_h_completo").glob("*.npz")):
        a = int(f.stem)
        z = np.load(f)
        full = am_por_duracion(z["dias"], z["prcp"].astype("float32"))
        zc = np.load(CACHE / "gar_h" / f"{a}.npz")
        cand = am_por_duracion(zc["dias"], zc["prcp"].astype("float32"))
        out[a] = {}
        for nom in CAJAS:
            m = g["isla"] == nom
            out[a][nom] = {f"{d}h": dict(captado_mediana=round(float(np.median(cand[d][m] / full[d][m])), 3),
                                         captado_p10=round(float(np.percentile(cand[d][m] / full[d][m], 10)), 3),
                                         celdas_exactas_pct=round(float((cand[d][m] >= 0.999 * full[d][m]).mean() * 100), 1))
                           for d in DURACIONES}
    return out


# ------------------------------------------------------------------ puntos y pluviómetros de la FCD
def cargar_m32():
    import importlib.util
    spec = importlib.util.spec_from_file_location("m32", GEO / "scripts" / "32_tormentas_sinteticas.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


REF_FCD = {"Puerto Ayora (FCD)": ("climate_puerto-ayora.csv", -0.743708, -90.3027, 2),
           "Bellavista (FCD)": ("climate_bellavista.csv", -0.6935, -90.3275, 223)}
EXTRA = {"san-cristobal": {"El Progreso": (-0.9071, -89.5569, 250)}}
T_LISTA = (2, 5, 10, 25, 50, 100)


def puntos():
    m = cargar_m32()
    P = {}
    for nom, (_, la, lo, z) in REF_FCD.items():
        P[nom] = dict(isla="santa-cruz", lat=la, lon=lo, cota=z)
    for isla, est in m.ESTACIONES.items():
        for nom, (la, lo, z) in est.items():
            P[nom] = dict(isla=isla, lat=la, lon=lo, cota=z)
    for isla, est in EXTRA.items():
        for nom, (la, lo, z) in est.items():
            P[nom] = dict(isla=isla, lat=la, lon=lo, cota=z)
    for nom, p in P.items():
        p["ref"] = "Puerto Ayora (FCD)" if p["cota"] < 100 else "Bellavista (FCD)"
    return P


def celda(g, la, lo):
    d = (g["lat"] - la) ** 2 + (g["lon"] - lo) ** 2
    d = np.where(g["tierra"], d, np.inf)
    return np.unravel_index(np.argmin(d), d.shape)


def fcd_max_anuales():
    out = {}
    for nom, (f, *_) in REF_FCD.items():
        d = pd.read_csv(FCD / f, usecols=["observation_date", "precipitation"], parse_dates=["observation_date"])
        s = d.set_index("observation_date").precipitation.astype(float).sort_index()
        s = s[~s.index.duplicated()]
        n = s.notna().groupby(s.index.year).sum()
        am = s.groupby(s.index.year).max()
        out[nom] = am[(n >= 330) & am.notna()]
    return out


class Ajuste:
    """Gumbel y GEV (máxima verosimilitud) sobre máximos anuales; curva de crecimiento x_T / media."""

    def __init__(self, am, n_boot=1000, semilla=24):
        from scipy import stats
        self.st = stats
        self.am = np.asarray(am, float)
        self.media = float(self.am.mean())
        self.gum = stats.gumbel_r.fit(self.am)
        self.gev = stats.genextreme.fit(self.am)
        rng = np.random.default_rng(semilla)
        self.boot = [stats.gumbel_r.fit(rng.choice(self.am, len(self.am))) for _ in range(n_boot)]

    def cuantil(self, T, dist="gumbel"):
        T = np.asarray(T, float)
        if dist == "gumbel":
            return self.st.gumbel_r.isf(1 / T, *self.gum)
        return self.st.genextreme.isf(1 / T, *self.gev)

    def banda(self, T, q=(5, 95)):
        v = np.array([self.st.gumbel_r.isf(1 / np.asarray(T, float), *b) for b in self.boot])
        return np.percentile(v, q[0], axis=0), np.percentile(v, q[1], axis=0)

    def periodo(self, x, dist="gumbel"):
        x = np.asarray(x, float)
        sf = self.st.gumbel_r.sf(x, *self.gum) if dist == "gumbel" else self.st.genextreme.sf(x, *self.gev)
        return np.clip(1 / np.maximum(sf, 1e-6), 1.0, 1e5)


# ------------------------------------------------------------------ análisis
def modelo_idf():
    """Todo lo necesario para dar mm(d, T) y T(mm, d) en cada punto. Se guarda en datos/ y se reutiliza."""
    g = malla()
    anios, AM, AM1d, chequeo = gar_max_anuales(g)
    if len(anios) < MIN_ANIOS:
        sys.exit(f"Solo hay {len(anios)} años de GAR horario en {CACHE / 'gar_h'}: corre «descargar» primero.")
    fcd = fcd_max_anuales()
    aj = {nom: Ajuste(am.values) for nom, am in fcd.items()}
    P = puntos()
    # media de los máximos anuales de GAR (1 día fijo) y razones por duración en la celda de cada punto
    for nom, p in P.items():
        i, j = celda(g, p["lat"], p["lon"])
        p["celda_gar"] = (int(i), int(j))
        p["cota_gar"] = float(g["z"][i, j])
        p["gar_media_am1d"] = float(AM1d[:, i, j].mean())
        p["razon"] = {d: float(AM[d][:, i, j].mean() / AM1d[:, i, j].mean()) for d in DURACIONES if d < 24}
        p["razon"][24] = WEISS
    # sesgo de GAR frente a la FCD en los años comunes (solo informativo)
    sesgo = {}
    for nom, am in fcd.items():
        i, j = P[nom]["celda_gar"]
        comunes = [a for a in am.index if a in set(anios)]
        idx = [list(anios).index(a) for a in comunes]
        sesgo[nom] = float(am.loc[comunes].mean() / AM1d[idx, i, j].mean()) if idx else float("nan")
    # La lluvia de 1 día de cada punto es la del pluviómetro FCD más parecido en altura, SIN escalar con GAR: su gradiente
    # espacial no está validado (en la celda de Santa Rosa supera los 179 mm en 21 de 46 años; estudio de Santa Cruz). San
    # Cristóbal toma prestada la curva de Santa Cruz a la misma altura. Lo que diría GAR queda en «factor_gar_informativo».
    for nom, p in P.items():
        ref = p["ref"]
        p["media_am1d"] = aj[ref].media
        p["factor_gar_informativo"] = p["gar_media_am1d"] / P[ref]["gar_media_am1d"]
        donde = "Puerto Ayora, costa" if ref.startswith("Puerto Ayora") else "Bellavista, 223 m"
        p["metodo"] = (f"1 día: FCD {donde}" + (" (prestada de Santa Cruz)" if p["isla"] == "san-cristobal" else "")
                       + "; horas: GAR en este punto")
    return dict(g=g, anios=anios, AM=AM, AM1d=AM1d, chequeo=chequeo, fcd=fcd, aj=aj, P=P, sesgo=sesgo)


def mm(Mo, nom, d, T, dist="gumbel"):
    """Lluvia (mm) en d horas móviles con periodo de retorno T en el punto."""
    p = Mo["P"][nom]
    a = Mo["aj"][p["ref"]]
    return p["media_am1d"] * p["razon"][d] * a.cuantil(T, dist) / a.media


def periodo(Mo, nom, d, x, dist="gumbel"):
    p = Mo["P"][nom]
    a = Mo["aj"][p["ref"]]
    return a.periodo(np.asarray(x, float) / (p["media_am1d"] * p["razon"][d]) * a.media, dist)


def ierse_razones():
    """Lluvia medida cada 5 min (IERSE): máximo de 1, 3, 6 y 24 h y razón frente al día, en los días de ≥ 40 mm."""
    s = pd.read_csv(IERSE / "serie_5min.csv.gz", parse_dates=["fecha_hora_local"])
    nombres = dict(pd.read_csv(IERSE / "horario.csv", usecols=["estacion_id", "estacion"]).drop_duplicates().values)
    filas = []
    for e, gdf in s.groupby("estacion_id"):
        r = gdf.set_index("fecha_hora_local").lluvia_mm.sort_index()
        r = r[~r.index.duplicated()].resample("5min").sum(min_count=1).fillna(0)
        rol = {h: r.rolling(f"{h}h").sum() for h in (1, 3, 6, 24)}
        dia = r.resample("D").sum()
        for k in dia[dia >= 40].index:
            w = slice(k, k + pd.Timedelta("1D"))
            fila = dict(estacion=nombres.get(e, e), fecha=k.strftime("%Y-%m-%d"), dia_mm=round(float(dia[k]), 1))
            for h in (1, 3, 6, 24):
                fila[f"R{h}h"] = round(float(rol[h][w].max()), 1)
                fila[f"razon_{h}h"] = round(fila[f"R{h}h"] / fila["dia_mm"], 3)
            filas.append(fila)
    return pd.DataFrame(filas)


def analizar():
    Mo = modelo_idf()
    od = EST / "datos"
    od.mkdir(parents=True, exist_ok=True)
    filas = []
    for nom, p in Mo["P"].items():
        for d in DURACIONES:
            for T in T_LISTA:
                v = float(mm(Mo, nom, d, T))
                vg = float(mm(Mo, nom, d, T, "gev"))
                filas.append(dict(punto=nom, isla=p["isla"], cota_m=p["cota"], duracion_h=d, T_anios=T, lluvia_mm=round(v, 1),
                                  intensidad_mmh=round(v / d, 1), lluvia_gev_mm=round(vg, 1)))
    idf = pd.DataFrame(filas)
    # bandas de confianza (remuestreo de años del pluviómetro de referencia; no incluye la incertidumbre de GAR)
    for i, r in idf.iterrows():
        p = Mo["P"][r.punto]
        a = Mo["aj"][p["ref"]]
        lo, hi = a.banda([r.T_anios])
        f = p["media_am1d"] * p["razon"][r.duracion_h] / a.media
        idf.loc[i, "ic5_mm"] = round(float(lo[0] * f), 1)
        idf.loc[i, "ic95_mm"] = round(float(hi[0] * f), 1)
    idf.to_csv(od / "idf_puntos.csv", index=False)
    pd.DataFrame([dict(punto=n, isla=p["isla"], cota_m=p["cota"], cota_gar_m=round(p["cota_gar"]), referencia=p["ref"], metodo=p["metodo"],
                       media_max_anual_1dia_mm=round(p["media_am1d"], 1), gar_media_max_anual_1dia_mm=round(p["gar_media_am1d"], 1),
                       factor_gar_informativo=round(p["factor_gar_informativo"], 2),
                       **{f"razon_{d}h": round(p["razon"][d], 3) for d in DURACIONES}) for n, p in Mo["P"].items()]
                 ).to_csv(od / "razones_puntos.csv", index=False)
    ie = ierse_razones()
    ie.to_csv(od / "ierse_dias_40mm.csv", index=False)
    # el 30-oct en la escala de años (lluvia medida, IERSE)
    oct30 = []
    for _, r in ie[ie.fecha == "2026-10-30"].iterrows():
        if r.estacion not in Mo["P"]:
            continue
        for d in (1, 3, 6, 24):
            oct30.append(dict(estacion=r.estacion, duracion_h=d, lluvia_mm=r[f"R{d}h"],
                              T_gumbel=round(float(periodo(Mo, r.estacion, d, r[f"R{d}h"])), 0),
                              T_gev=round(float(periodo(Mo, r.estacion, d, r[f"R{d}h"], "gev")), 0)))
    pd.DataFrame(oct30).to_csv(od / "periodo_retorno_30oct.csv", index=False)
    ver = verificar_candidatos(Mo["g"])
    res = dict(
        aviso="Curvas IDF provisionales de SOS Galápagos (modelo propio, no dato oficial). Orden de magnitud: no sirven para diseñar obras.",
        anios_gar=[int(Mo["anios"][0]), int(Mo["anios"][-1]), int(len(Mo["anios"]))],
        coherencia_gar_horario_diario_mm=round(float(np.median(Mo["chequeo"])), 3),
        fcd={n: dict(anios=int(len(a.am)), media_mm=round(a.media, 1), gumbel=[round(x, 2) for x in a.gum],
                     gev_xi=round(-a.gev[0], 3), gev=[round(x, 2) for x in a.gev]) for n, a in Mo["aj"].items()},
        sesgo_gar_fcd_informativo={n: round(v, 3) for n, v in Mo["sesgo"].items()},
        verificacion_dias_candidatos=ver,
        ierse_razon_mediana={f"{h}h": round(float(ie[f"razon_{h}h"].median()), 3) for h in (1, 3, 6)} if len(ie) else {},
        periodo_retorno_30oct=oct30)
    (od / "resumen_idf.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "periodo_retorno_30oct"}, ensure_ascii=False, indent=1)[:3000])
    print(pd.DataFrame(oct30).to_string())
    return Mo


# ------------------------------------------------------------------ tormentas sintéticas en la escala de años
BANDAS = [(1, 2), (2, 5), (5, 10), (10, 25), (25, 50), (50, 100), (100, np.inf)]
BANDAS_MAPA = [(2, 10), (10, 50), (50, np.inf)]
# pluviómetros que miden la lluvia sobre la cuenca de cada puerto (para los mapas)
MAPA_ESTACIONES = {"santa-cruz": ["Los Guayabillos", "INAMHI Puerto Ayora", "Erna (Puerto Ayora)", "Punta Estrada"],
                   "san-cristobal": ["El Junco", "Cerro Alto", "El Mirador", "INAMHI Puerto Baquerizo"]}
ALTO = dict(R1h=30, R3h=60, R24h=100)        # «alto» de clima/recolector/umbrales_inundacion.json (v0.2)


def p_banda(lo, hi):
    """Probabilidad de que el máximo anual caiga entre los periodos de retorno lo y hi."""
    return 1 / lo - (0 if np.isinf(hi) else 1 / hi)


def tasa(T):
    """Eventos por año a partir del periodo de retorno de máximos anuales (Langbein)."""
    T = np.asarray(T, float)
    return -np.log(np.clip(1 - 1 / T, 1e-9, 1))


def periodo_tormentas(Mo, isla, m32):
    """T de cada tormenta en cada pluviómetro (máximo entre 1, 3, 6 y 24 h), de la lluvia que marcó."""
    R = pd.read_csv(m32.EST / "datos" / isla / "resultados_tormentas.csv")
    out = pd.DataFrame({"id": R["id"]})
    for s in m32.ESTACIONES[isla]:
        Ts = np.ones(len(R))
        for d in (1, 3, 6, 24):
            Ts = np.maximum(Ts, periodo(Mo, s, d, R[f"{s}|R{d}h"].values))
        out[s] = Ts
    out["isla_T"] = out[list(m32.ESTACIONES[isla])].max(axis=1)
    out["cuenca_T"] = out[MAPA_ESTACIONES[isla]].max(axis=1)
    return R, out


def logistica(x, y):
    """P(y | x) = 1 / (1 + exp(-(a + b x))) por máxima verosimilitud."""
    from scipy.optimize import minimize

    def nll(t):
        z = t[0] + t[1] * x
        return np.sum(np.logaddexp(0, z)) - np.sum(y * z)
    r = minimize(nll, [0.0, 1.0], method="Nelder-Mead")
    return r.x


def prob_anual(curva):
    """∫ P(evento | T) dF: T del máximo anual con F = 1 − 1/T uniforme."""
    u = np.linspace(0, 0.9995, 4000)
    T = 1 / (1 - u)
    return float(np.mean(curva(T)))


def tormentas():
    m32 = cargar_m32()
    Mo = modelo_idf()
    od = EST / "datos"
    resumen = {}
    for isla in ("santa-cruz", "san-cristobal"):
        R, TT = periodo_tormentas(Mo, isla, m32)
        TT.round(2).to_csv(od / f"periodo_tormentas_{isla}.csv", index=False)
        resumen[isla] = {"T_cuenca_cuantiles": {q: round(float(np.percentile(TT.cuenca_T, q)), 1) for q in (10, 25, 50, 75, 90)},
                         "estaciones_mapa": MAPA_ESTACIONES[isla], "zonas": {}}
        for zn, zc in m32.ZONAS[isla].items():
            est = [s for s, _ in zc["v02"]]
            pes = dict(zc["v02"])
            Tz = TT[est].max(axis=1).values
            inunda = (R[f"{zn}|hmax"].values >= m32.H_IMPACTO)
            pv = pd.read_csv(m32.EST / "datos" / isla / f"previo_llegada_{m32.slug(zn)}.csv").set_index("id").reindex(R["id"])
            f = np.where(pv.P5d.values > 53, 0.8, 1.0)
            alto = (pv.R1h.values >= ALTO["R1h"] * f) | (pv.R3h.values >= ALTO["R3h"] * f) | (pv.R24h.values >= ALTO["R24h"] * f)
            a, b = logistica(np.log(Tz), inunda.astype(float))
            curva = lambda T, a=a, b=b: 1 / (1 + np.exp(-(a + b * np.log(T))))
            p_anual = prob_anual(curva)
            # «alto» por año con la v0.2 según las curvas IDF: el pluviómetro y la duración que lo dan más seguido (cota inferior)
            T_alto = min(float(periodo(Mo, s, d, ALTO[f"R{d}h"] / pes[s])) for s in est for d in (1, 3, 24))
            bandas = []
            for lo, hi in BANDAS:
                m = (Tz >= lo) & (Tz < hi)
                n = int(m.sum())
                bandas.append(dict(T_desde=lo, T_hasta=None if np.isinf(hi) else hi, tormentas=n, inundan=int(inunda[m].sum()),
                                   frac_inunda=round(float(inunda[m].mean()), 3) if n else None,
                                   frac_alto_sin_inundar=round(float((alto & ~inunda)[m].sum() / max((~inunda[m]).sum(), 1)), 3) if n else None,
                                   prob_anual_banda=round(p_banda(lo, hi), 4)))
            T50 = float(np.exp(-a / b)) if b > 0 else None
            resumen[isla]["zonas"][zn] = dict(
                logistica=dict(a=round(float(a), 3), b=round(float(b), 3)),
                T_con_50pct_de_inundarse=round(T50, 1) if T50 else None,
                prob_anual_inundacion=round(p_anual, 3), una_vez_cada_anios=round(1 / tasa(1 / max(p_anual, 1e-6)).item() if p_anual < 1 else 1, 1),
                alto_v02_una_vez_cada_anios=round(1 / float(tasa(T_alto)), 2),
                # «alto» sin inundación por año ≈ «alto» por año − inundaciones por año (casi todas dan «alto»): orden de magnitud
                falsas_alarmas_por_anio=round(max(float(tasa(T_alto)) - float(tasa(1 / max(p_anual, 1e-6))), 0), 2), bandas=bandas)
        mapas_retorno(isla, TT, m32)
    (od / "tormentas_por_periodo.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    for isla, r in resumen.items():
        print(isla, r["T_cuenca_cuantiles"])
        for zn, z in r["zonas"].items():
            print(f"  {zn}: T50={z['T_con_50pct_de_inundarse']}  P_anual={z['prob_anual_inundacion']}  (1 cada {z['una_vez_cada_anios']} años)  "
                  f"«alto» 1 cada {z['alto_v02_una_vez_cada_anios']} años")
            print("     ", [(b["T_desde"], b["tormentas"], b["frac_inunda"]) for b in z["bandas"]])


def mapas_retorno(isla, TT, m32):
    """Fracción de tormentas que dejan ≥ 0,3 m en cada celda, por banda de T (de la lluvia en los pluviómetros de la isla),
    y probabilidad anual combinando las bandas con su probabilidad."""
    import rasterio
    pila = np.load(m32.CACHE / isla / "pila_hmax.npz")
    ids = list(pila["ids"])
    H = pila["hmax"].astype("float32") >= m32.H_IMPACTO
    T = TT.set_index("id").loc[ids, "cuenca_T"].values
    d = m32.dominio(isla)
    out = {}
    for lo, hi in BANDAS_MAPA:
        m = (T >= lo) & (T < hi)
        out[(lo, hi)] = (H[m].mean(axis=0) if m.sum() else np.zeros(H.shape[1:]), int(m.sum()))
    fr, ns = [], []
    for lo, hi in BANDAS:
        m = (T >= lo) & (T < hi)
        ns.append(int(m.sum()))
        fr.append(H[m].mean(axis=0) if m.sum() else None)
    for k in range(len(fr)):                         # bandas con < 3 tormentas: la vecina más cercana con datos
        if ns[k] < 3:
            cand = sorted((abs(j - k), j) for j in range(len(fr)) if ns[j] >= 3)
            fr[k] = fr[cand[0][1]]
    anual = sum(p_banda(lo, hi) * f for (lo, hi), f in zip(BANDAS, fr))
    anual = np.where(d["act"], anual, np.nan).astype("float32")
    prof = dict(driver="GTiff", height=anual.shape[0], width=anual.shape[1], count=1, dtype="float32", crs=f"EPSG:{int(d['epsg'])}",
                transform=d["tr"], nodata=np.nan, compress="deflate")
    with rasterio.open(EST / "datos" / f"probabilidad_anual_inundacion_{isla}.tif", "w", **prof) as f_:
        f_.write(anual, 1)
    np.savez_compressed(CACHE / f"mapas_{isla}.npz", anual=anual,
                        **{f"banda_{lo}_{'inf' if np.isinf(hi) else hi}": v for (lo, hi), (v, _) in out.items()},
                        n=np.array([n for _, n in out.values()]))


# ------------------------------------------------------------------ figuras
AVISO = ("Curvas IDF provisionales de SOS Galápagos: modelo propio, no dato oficial. Lluvia de 1 día: pluviómetros de la FCD; "
         "paso a horas: reanálisis GAR (TU Berlín, lluvia modelada). Orden de magnitud, no sirven para diseñar obras.")
PANELES = {"santa-cruz": ["INAMHI Puerto Ayora", "Los Guayabillos", "Santa Rosa"],
           "san-cristobal": ["INAMHI Puerto Baquerizo", "El Progreso", "El Junco"]}
NOMBRE = {"santa-cruz": "Santa Cruz", "san-cristobal": "San Cristóbal"}
COL_T = {2: "#c6dbef", 5: "#9ecae1", 10: "#6baed6", 25: "#3182bd", 50: "#08519c", 100: "#08306b"}


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    return plt


def fmt_T(T):
    return "más de 500" if T >= 500 else f"{T:.0f}"


def fig_idf(Mo, isla, oct30):
    plt = _plt()
    fig, axs = plt.subplots(1, 3, figsize=(14, 5.2), sharey=True)
    dd = np.array(DURACIONES, float)
    dfino = np.array([1, 1.5, 2, 3, 4, 6, 9, 12, 18, 24])
    for ax, nom in zip(axs, PANELES[isla]):
        p = Mo["P"][nom]
        for T in T_LISTA:
            y = np.interp(np.log(dfino), np.log(dd), [float(mm(Mo, nom, d, T)) for d in DURACIONES])
            ax.plot(dfino, y, color=COL_T[T], lw=2, label=f"{T} años")
            ax.text(24.8, y[-1], f"{T}", color=COL_T[T], fontsize=8, va="center")
        a = Mo["aj"][p["ref"]]
        for T in (10, 100):
            f = np.array([p["media_am1d"] * p["razon"][d] / a.media for d in DURACIONES])
            lo, hi = a.banda([T])
            ax.fill_between(dd, lo[0] * f, hi[0] * f, color=COL_T[T], alpha=0.13, lw=0)
        ax.plot([1, 3, 24], [ALTO["R1h"], ALTO["R3h"], ALTO["R24h"]], "X", ms=9, mfc="#dc2626", mec="white", zorder=6,
                label="«alto» v0.2 (30 / 60 / 100 mm)")
        o = [r for r in oct30 if r["estacion"] == nom]
        if o:
            ax.plot([r["duracion_h"] for r in o], [r["lluvia_mm"] for r in o], "*", ms=14, mfc="#facc15", mec="k", zorder=7,
                    label="30-oct-2026 (medido, IERSE)")
            for r in o:
                izq = r["duracion_h"] >= 12
                ax.annotate(f"{r['lluvia_mm']:.0f} mm\n≈{fmt_T(r['T_gumbel'])} años", (r["duracion_h"], r["lluvia_mm"]),
                            xytext=(-8 if izq else 7, 8), textcoords="offset points", fontsize=7.5, ha="right" if izq else "left",
                            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
        ax.set_xscale("log")
        ax.set_xticks([1, 2, 3, 6, 12, 24])
        ax.set_xticklabels(["1 h", "2 h", "3 h", "6 h", "12 h", "24 h"])
        ax.set_xlim(0.9, 30)
        ax.grid(alpha=0.25)
        ax.set_title(f"{nom} ({p['cota']:.0f} m)", fontsize=10)
        ax.set_xlabel("Duración de la lluvia")
        ax.text(0.02, 0.98, f"Base: {p['metodo']}", transform=ax.transAxes, fontsize=7, va="top", color="#555")
    axs[0].set_ylabel("Lluvia acumulada (mm)")
    axs[0].legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0, 0.93), frameon=False, title="Periodo de retorno", title_fontsize=7.5)
    fig.suptitle(f"{NOMBRE[isla]}: cuánta lluvia cae en 1 a 24 horas una vez cada 2, 5, 10, 25, 50 y 100 años (curvas IDF provisionales)",
                 fontsize=11.5)
    extra = (" Sombreado: intervalo del 90 % para 10 y 100 años (solo la incertidumbre del pluviómetro)." +
             (" San Cristóbal no tiene serie medida larga: GAR corregido con su sesgo en Santa Cruz." if isla == "san-cristobal" else ""))
    fig.text(0.01, -0.02, AVISO + extra, fontsize=7, color="#555", wrap=True)
    fig.tight_layout()
    fig.savefig(EST / "figuras" / f"idf_{isla}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_metodo(Mo, ie):
    plt = _plt()
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    ax = axs[0]
    Tg = np.logspace(np.log10(1.05), np.log10(200), 100)
    for (nom, a), c in zip(Mo["aj"].items(), ("#7f8c8d", "#c0392b")):
        x = np.sort(a.am)
        n = len(x)
        Tp = (n + 1) / (n + 1 - np.arange(1, n + 1))                   # posición de Weibull
        ax.plot(Tp, x, "o", ms=4, mfc="white", mec=c, label=f"{nom}: {n} años medidos")
        ax.plot(Tg, a.cuantil(Tg), color=c, lw=1.8, label="Gumbel")
        ax.plot(Tg, a.cuantil(Tg, "gev"), color=c, lw=1.2, ls="--", label=f"GEV (ξ = {-a.gev[0]:.2f})".replace(".", ","))
    for v, nm in ((178.8, "Los Guayabillos"), (237.6, "Santa Rosa")):
        ax.axhline(v, color="#facc15", lw=1.2, zorder=0)
        ax.text(1.1, v + 4, f"30-oct: {nm} {v:.0f} mm", fontsize=7.5)
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 5, 10, 25, 50, 100, 200])
    ax.set_xticklabels(["1", "2", "5", "10", "25", "50", "100", "200"])
    ax.set_xlabel("Periodo de retorno (años)")
    ax.set_ylabel("Máximo diario del año (mm)")
    ax.set_title("1. Lluvia de 1 día: máximos anuales de la FCD", fontsize=10)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    ax.grid(alpha=0.25)
    ax = axs[1]
    for nom, c in (("INAMHI Puerto Ayora", "#7f8c8d"), ("Los Guayabillos", "#c0392b"), ("Santa Rosa", "#2471a3"), ("Cerro Crocker", "#6c3483"),
                   ("INAMHI Puerto Baquerizo", "#16a085"), ("El Junco", "#b9770e")):
        p = Mo["P"][nom]
        ax.plot(DURACIONES, [p["razon"][d] for d in DURACIONES], "-o", ms=3.5, color=c, lw=1.5,
                label=f"{nom} ({'San Cristóbal' if p['isla'] == 'san-cristobal' else 'Santa Cruz'})")
    if len(ie):
        for h, mk in ((1, "s"), (3, "D"), (6, "^")):
            ax.plot(np.full(len(ie), h) * np.exp(np.random.default_rng(h).uniform(-0.06, 0.06, len(ie))), ie[f"razon_{h}h"], mk,
                    ms=5, mfc="none", mec="k", alpha=0.6, label="IERSE 2026, días ≥ 40 mm (medido)" if h == 1 else None)
    ax.axhline(1, color="#999", lw=0.8)
    ax.annotate("24 h móviles = 1 día × 1,13\n(factor de Weiss)", (24, WEISS), xytext=(-10, 12), textcoords="offset points",
                ha="right", fontsize=7.5, color="#444")
    ax.set_xscale("log")
    ax.set_xticks(list(DURACIONES))
    ax.set_xticklabels([f"{d} h" for d in DURACIONES])
    ax.set_ylim(0, 1.35)
    ax.set_xlabel("Duración")
    ax.set_ylabel("Lluvia en d horas / lluvia del día")
    ax.set_title(f"2. Paso de 1 día a horas: reanálisis GAR horario ({Mo['anios'][0]}–{Mo['anios'][-1]})", fontsize=10)
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    ax.grid(alpha=0.25)
    fig.suptitle("Cómo se arman las curvas IDF provisionales", fontsize=12)
    fig.text(0.01, -0.03, AVISO + " GAR es una malla de 2 km: suaviza los chubascos cortos, por eso sus razones de 1 h pueden quedarse cortas "
             "frente a un pluviómetro.", fontsize=7, color="#555", wrap=True)
    fig.tight_layout()
    fig.savefig(EST / "figuras" / "idf_metodo.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_fragilidad(isla, res, m32):
    plt = _plt()
    zonas = list(res["zonas"])
    fig, axs = plt.subplots(1, len(zonas), figsize=(4.7 * len(zonas), 4.6), sharey=True, squeeze=False)
    TT = pd.read_csv(EST / "datos" / f"periodo_tormentas_{isla}.csv")
    R = pd.read_csv(m32.EST / "datos" / isla / "resultados_tormentas.csv")
    Tg = np.logspace(0, 3, 200)
    for ax, zn in zip(axs[0], zonas):
        z = res["zonas"][zn]
        est = [s for s, _ in m32.ZONAS[isla][zn]["v02"]]
        Tz = TT[est].max(axis=1).values
        y = R[f"{zn}|hmax"].values >= m32.H_IMPACTO
        jit = np.random.default_rng(1).uniform(-0.04, 0.04, len(y))
        ax.scatter(Tz, y + jit, s=7, c=np.where(y, "#2563eb", "#9ca3af"), alpha=0.45, lw=0)
        for b in z["bandas"]:
            if b["tormentas"] >= 3:
                hi = b["T_hasta"] or 1000
                xm = np.sqrt(b["T_desde"] * hi)
                ax.plot(xm, b["frac_inunda"], "o", ms=4 + b["tormentas"] / 12, mfc="#f59e0b", mec="k", zorder=5)
        a, bb = z["logistica"]["a"], z["logistica"]["b"]
        ax.plot(Tg, 1 / (1 + np.exp(-(a + bb * np.log(Tg)))), color="#b45309", lw=2)
        ax.set_xscale("log")
        ax.set_xticks([1, 2, 5, 10, 25, 50, 100, 1000])
        ax.set_xticklabels(["1", "2", "5", "10", "25", "50", "100", "1000"])
        ax.set_xlim(1, 1000)
        ax.set_ylim(-0.08, 1.08)
        ax.grid(alpha=0.25)
        ax.set_xlabel("Periodo de retorno de la lluvia en los pluviómetros de la zona (años)")
        cada = z["una_vez_cada_anios"]
        alto = f"{z['alto_v02_una_vez_cada_anios']:.1f}".replace(".", ",")
        ax.set_title(f"{zn}\nse inundaría ≈1 vez cada {cada:.0f} años · «alto» v0.2 ≈1 vez cada {alto} años",
                     fontsize=8.5)
    axs[0][0].set_ylabel("Probabilidad de que la zona se inunde (≥ 0,3 m)")
    fig.suptitle(f"{NOMBRE[isla]}: con qué lluvia se inunda cada zona (500 tormentas sintéticas puestas en la escala de años)", fontsize=11.5)
    fig.text(0.01, -0.04, "Simulación propia de SOS Galápagos (modelo 2D y curvas IDF provisionales). No es un dato oficial. Puntos: cada tormenta "
             "(arriba, inunda; abajo, no). Círculos naranjas: fracción por intervalo de años. Curva: ajuste logístico. Las frecuencias por año "
             "son órdenes de magnitud: dependen de las curvas IDF, del suelo y de que el modelo no tiene red pluvial.",
             fontsize=7, color="#555", wrap=True)
    fig.tight_layout()
    fig.savefig(EST / "figuras" / f"fragilidad_{isla}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_mapas(isla, m32):
    plt = _plt()
    import importlib.util
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from pyproj import Transformer
    spec = importlib.util.spec_from_file_location("m33", GEO / "scripts" / "33_tormentas_figuras.py")
    m33 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m33)
    z = np.load(CACHE / f"mapas_{isla}.npz")
    d = m33.dom(isla)
    Tr = Transformer.from_crs(4326, d["epsg"], always_xy=True).transform
    if isla == "santa-cruz":
        lo0, la0, lo1, la1 = m33.ZOOM[isla]
        (x0, y0), (x1, y1) = Tr(lo0, la0), Tr(lo1, la1)
        ext = [x0, x1, y0, y1]
        fig, axs = plt.subplots(2, 2, figsize=(12.5, 15), layout="constrained")
    else:
        e_ = m33.ext_dom(d)
        ext = [e_[0] + 300, e_[1] - 300, e_[2] + 300, e_[3] - 300]
        fig, axs = plt.subplots(4, 1, figsize=(13, 17), layout="constrained")
    axs = list(np.ravel(axs))
    claves = [k for k in z.files if k.startswith("banda_")]
    ns = list(z["n"])
    cm = plt.cm.YlOrRd
    for ax, k, n in zip(axs[:3], claves, ns):
        lo, hi = k.split("_")[1:]
        m33.fondo(ax, d, ext, detalle=True)
        v = z[k]
        im = ax.imshow(np.where(v >= 0.05, v * 100, np.nan), extent=m33.ext_dom(d), cmap=cm, vmin=0, vmax=100, zorder=5)
        t = f"Lluvia de {lo} a {hi} años" if hi != "inf" else f"Lluvia de más de {lo} años"
        ax.set_title(f"{t} en los pluviómetros ({n} tormentas):\n% que dejan ≥ 0,3 m de agua", fontsize=10)
        m33.escala(ax, 1)
    cb = fig.colorbar(im, ax=axs[1] if isla == "santa-cruz" else axs[:3], shrink=0.8 if isla == "santa-cruz" else 0.5, pad=0.01)
    cb.set_label("% de las tormentas de ese intervalo que dejan ≥ 0,3 m (misma escala en los tres)")
    ax = axs[3]
    m33.fondo(ax, d, ext, detalle=True)
    a = z["anual"]
    cada = np.where(a > 0, 1 / np.maximum(a, 1e-9), np.inf)
    lim = [1, 2, 5, 10, 25, 50, 100]
    cls = np.digitize(cada, lim).astype(float)
    cls[(cada > 100) | ~np.isfinite(cada)] = np.nan
    cmap = ListedColormap(["#7f1d1d", "#dc2626", "#f97316", "#facc15", "#fde68a", "#fef9c3"])
    im2 = ax.imshow(cls, extent=m33.ext_dom(d), cmap=cmap, norm=BoundaryNorm(np.arange(0.5, 7.5), 6), zorder=5)
    ax.set_title("Combinando todas con su probabilidad: ≥ 0,3 m de agua\nuna vez cada… años (orden de magnitud)", fontsize=10)
    cb2 = fig.colorbar(im2, ax=ax, shrink=0.8, pad=0.01, ticks=range(1, 7))
    cb2.ax.set_yticklabels(["1–2", "2–5", "5–10", "10–25", "25–50", "50–100"])
    cb2.set_label("una vez cada … años")
    m33.escala(ax, 1)
    for ax_ in axs:
        for zn, zc in m32.ZONAS[isla].items():
            r, c, lo_, la_ = d["puntos_rc"][zc["punto"]]
            x, y = Tr(lo_, la_)
            ax_.plot(x, y, "o", ms=5, mfc="none", mec="k", mew=1.2, zorder=9)
            if ext[0] < x < ext[1] and ext[2] < y < ext[3]:
                ax_.text(x + 100, y + 50, zn, fontsize=7, zorder=9, clip_on=True,
                         bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))
    fig.suptitle(f"{NOMBRE[isla]}: dónde se junta el agua según el periodo de retorno de la lluvia", fontsize=12)
    fig.get_layout_engine().set(h_pad=0.08)
    fig.text(0.01, -0.012,
             "Simulación propia de SOS Galápagos (modelo 2D, DSM 30 m, 500 tormentas sintéticas, curvas IDF provisionales). No es un dato oficial ni "
             f"un mapa de amenaza. El periodo de retorno es el de la lluvia que marcan los pluviómetros de la cuenca ({', '.join(MAPA_ESTACIONES[isla])}), no el de la inundación. "
             "Los puntos sueltos son hoyos del DSM (techos, árboles).", fontsize=7, color="#555", wrap=True)
    fig.savefig(EST / "figuras" / f"mapa_retorno_{isla}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figuras():
    m32 = cargar_m32()
    Mo = modelo_idf()
    (EST / "figuras").mkdir(parents=True, exist_ok=True)
    oct30 = json.loads((EST / "datos" / "resumen_idf.json").read_text())["periodo_retorno_30oct"]
    ie = pd.read_csv(EST / "datos" / "ierse_dias_40mm.csv")
    fig_metodo(Mo, ie)
    res = json.loads((EST / "datos" / "tormentas_por_periodo.json").read_text())
    for isla in ("santa-cruz", "san-cristobal"):
        fig_idf(Mo, isla, oct30)
        fig_fragilidad(isla, res[isla], m32)
        fig_mapas(isla, m32)


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["descargar", "analizar", "tormentas", "figuras", "todo"])
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--completo", type=int, nargs="*", default=[])
    a = ap.parse_args()
    if a.accion == "descargar":
        descargar(a.procesos, a.completo)
    if a.accion in ("analizar", "todo"):
        analizar()
    if a.accion in ("tormentas", "todo"):
        tormentas()
    if a.accion in ("figuras", "todo"):
        figuras()


if __name__ == "__main__":
    main()
