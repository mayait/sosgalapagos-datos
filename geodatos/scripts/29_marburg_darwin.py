#!/usr/bin/env python3
"""Proyecto DARWIN (U. de Marburgo) y reanálisis GAR (TU Berlín): inventario y climatología de lluvia.

Qué hace
  A. INVENTARIO de la plataforma de datos del proyecto DARWIN («Dynamics of precipitation in transition»,
     DFG FOR 816, LCRS-Marburgo): https://vhrz669.hrz.uni-marburg.de/darwin/data_pre.do?cmd=showall
     Solo se leen las páginas PÚBLICAS (listado y metadatos). Las series NO se descargan: la descarga exige
     dar nombre y correo y aceptar el «Darwin project data agreement for external data users», cuyo §3
     prohíbe redistribuir y exige aprobación del titular y coautoría para publicar. Eso lo decide el
     responsable del estudio, no este script.
  B. GAR, «Galápagos Archipelago Refined analysis» (Schmidt et al. 2025, IJC 45:e8924; WRF 4.3.3 forzado
     con ERA5, 2 km, 1980–2025). Es el producto del mismo consorcio que SÍ es abierto (CC BY 4.0):
     https://data.klima.tu-berlin.de/GAR/v1/d02km/  (y validación en doi:10.5281/zenodo.11916492).
     Se usan la lluvia diaria (d/2d/prcp, media diaria en mm/h, día UTC) y la cota del modelo (static/hgt).
     Es lluvia MODELADA [E], no medida.
  C. Contraste de GAR con los pluviómetros diarios de la FCD (Puerto Ayora desde 1965 y Bellavista
     1987–2019). Solo se LEEN de ../clima/datos/fcd/ (no se ejecuta ni se escribe nada allí).

Salidas (datos/marburg_darwin/):
  inventario_darwin.csv, gar_puntos.csv, gar_max_anual_puntos.csv, gar_total_anual_puntos.csv, gar_periodo_retorno.csv,
  gar_transferencia.csv,
  gar_gradiente_altitud.csv, gar_nino_puntos.csv, fcd_max_anual.csv, fcd_nino.csv, gar_vs_fcd.csv, resumen_marburg.json
Figuras (prefijo marburg_):
  estudios/santa-cruz/figuras/marburg_gar_gradiente.png, marburg_max_anual_santa_cruz.png, marburg_inventario.png
  estudios/san-cristobal/figuras/marburg_gar_san_cristobal.png

Uso, desde geodatos/:
  .venv/bin/python -I scripts/29_marburg_darwin.py              # procesa lo que ya está en bruto/
  .venv/bin/python -I scripts/29_marburg_darwin.py --descargar  # además baja páginas públicas DARWIN y GAR
Horas: el día de GAR es el día UTC (00–24 UTC = 18:00–18:00 en Galápagos). El día pluviométrico de la FCD
es de lectura manual. Ninguno coincide con el día natural en UTC−6; afecta poco a los máximos anuales.
"""
import html
import json
import re
import sys
import time
import urllib.request
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import xarray as xr  # noqa: E402
from scipy import stats  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

GEO = Path(__file__).resolve().parent.parent
OUT = GEO / "datos" / "marburg_darwin"
BRUTO = OUT / "bruto"
META = BRUTO / "metadatos"
GAR = BRUTO / "gar"
FCD = GEO.parent / "clima" / "datos" / "fcd"
FIG_SC = GEO / "estudios" / "santa-cruz" / "figuras"
FIG_SX = GEO / "estudios" / "san-cristobal" / "figuras"

DARWIN = "https://vhrz669.hrz.uni-marburg.de/darwin"
GAR_URL = "https://data.klima.tu-berlin.de/GAR/v1/d02km"
ANIOS = range(1980, 2026)

# Lluvia medida del 30-oct-2026 (red IERSE-WSN; estudio de Santa Cruz, sección de lluvias). Son mínimos.
EVENTO = {"Los Guayabillos": (178.8, 178), "Santa Rosa": (237.6, 416)}
UMBRALES = [60, 100, 150, 179, 238]

# Puntos: (isla, lat, lon, cota de la estación en m, fuente de la coordenada)
PUNTOS = {
    "Puerto Ayora (CDRS/DARWIN)": ("Santa Cruz", -0.743708, -90.3027, 2, "Tenelanda et al. 2025, tab. 1"),
    "Bellavista (FCD)": ("Santa Cruz", -0.6935, -90.3275, 223, "aprox., centro de Bellavista"),
    "Los Guayabillos (IERSE)": ("Santa Cruz", -0.6991, -90.3420, 178, "API IERSE-WSN"),
    "Santa Rosa (DARWIN/IERSE)": ("Santa Cruz", -0.654530, -90.4035, 422, "Tenelanda et al. 2025, tab. 1"),
    "Minas Rojas (DARWIN)": ("Santa Cruz", -0.618625, -90.3673, 619, "Tenelanda et al. 2025, tab. 1"),
    "Cerro Crocker (DARWIN)": ("Santa Cruz", -0.642398, -90.3260, 849, "Tenelanda et al. 2025, tab. 1"),
    "Militar, Baltra (DARWIN)": ("Santa Cruz", -0.489962, -90.2808, 22, "Tenelanda et al. 2025, tab. 1"),
    "Puerto Baquerizo Moreno": ("San Cristóbal", -0.9015, -89.6105, 25, "estudio SC, sección 3.3"),
    "El Progreso": ("San Cristóbal", -0.9071, -89.5569, 250, "estudio SC, sección 3.3"),
    "El Junco": ("San Cristóbal", -0.894, -89.480, 684, "estudio SC, sección 3.3"),
    "Toma Cerro Gato": ("San Cristóbal", -0.91979, -89.47821, None, "cuencas_tomas.json (AG-01)"),
    "Toma Los Americanos": ("San Cristóbal", -0.91354, -89.48683, None, "cuencas_tomas.json (AG-02)"),
    "Toma La Toma (El Progreso)": ("San Cristóbal", -0.91109, -89.50649, None, "cuencas_tomas.json (AG-03)"),
    "Manantial El Chino": ("San Cristóbal", -0.90218, -89.45692, None, "cuencas_tomas.json (AG-04)"),
}
# Cajas para separar las islas en la malla de GAR
CAJAS = {"Santa Cruz": (-90.60, -90.15, -0.84, -0.50), "San Cristóbal": (-89.66, -89.22, -0.98, -0.66)}
# Transectos de barlovento (ladera sur/sureste) para el gradiente: celdas a <= 3 km de la recta
TRANSECTOS = {"Santa Cruz": [(-90.3027, -0.7437), (-90.3260, -0.6424)],
              "San Cristóbal": [(-89.6105, -0.9015), (-89.4800, -0.8940)]}
CORR_TOTAL = {"Puerto Baquerizo Moreno": 500}
NINO = {"1982-83": ("1982-09-01", "1983-08-31"), "1997-98": ("1997-06-01", "1998-07-31"),
        "2015-16": ("2015-06-01", "2016-05-31"), "2023-24": ("2023-06-01", "2024-05-31")}


# ------------------------------------------------------------------ utilidades
def get(url, dest, timeout=300):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "sosgalapagos-geodatos/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    time.sleep(1)
    return dest


def lineas(p):
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t)
    t = re.sub(r"(?i)<br\s*/?>|</tr>|</p>|</div>|</h\d>|</li>|</td>|</th>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [re.sub(r"\s+", " ", x).strip() for x in t.split("\n") if x.strip()]


def tras(L, clave, n=1):
    for i, x in enumerate(L):
        if x.rstrip(": ").strip() == clave:
            return L[i + 1:i + 1 + n]
    return []


def descargar():
    print("Descargando páginas públicas de DARWIN (listado y metadatos)…")
    for p in range(1, 5):
        get(f"{DARWIN}/data_pre.do?cmd=showall&page={p}", BRUTO / f"lista_p{p}.html")
    get(f"{DARWIN}/data_pre.do?cmd=showall", BRUTO / "showall.html")
    get(f"{DARWIN}/publications.do?cmd=showall", BRUTO / "publicaciones.html")
    for i in ids_darwin():
        get(f"{DARWIN}/viewmetadata.do?datasetid={i}", META / f"meta_{i}.html")
    print("Descargando GAR (CC BY 4.0): cota, máscara y lluvia diaria 1980–2025 (~3 GB)…")
    get(f"{GAR_URL}/static/GAR_d02km_static_hgt.nc", GAR / "GAR_d02km_static_hgt.nc")
    get(f"{GAR_URL}/static/GAR_d02km_static_landmask.nc", GAR / "GAR_d02km_static_landmask.nc")
    for a in ANIOS:
        get(f"{GAR_URL}/d/2d/GAR_d02km_d_2d_prcp_{a}.nc", GAR / f"GAR_d02km_d_2d_prcp_{a}.nc", timeout=1800)


def ids_darwin():
    ids = set()
    for f in list(BRUTO.glob("lista_p*.html")) + [BRUTO / "showall.html"]:
        if f.exists():
            ids |= {int(x) for x in re.findall(r"viewmetadata\.do[^\"]*datasetid=(\d+)", f.read_text(errors="replace"))}
    return sorted(ids)


def dois_darwin():
    """DOI de cada conjunto según el listado público (Dataset ID … DOI: 10.5678/…)."""
    out, actual = {}, None
    for f in [BRUTO / "showall.html"] + sorted(BRUTO.glob("lista_p*.html")):
        if not f.exists():
            continue
        L = lineas(f)
        for k, x in enumerate(L[:-1]):
            if x.startswith("Dataset ID"):
                actual = int(L[k + 1]) if L[k + 1].isdigit() else None
            elif x.startswith("DOI") and actual is not None and L[k + 1].startswith("10.5678/"):
                out[actual] = L[k + 1]
    return out


# ------------------------------------------------------------------ A. inventario DARWIN
def inventario():
    filas, dois = [], dois_darwin()
    for i in ids_darwin():
        p = META / f"meta_{i}.html"
        if not p.exists():
            continue
        L = lineas(p)
        titulo = (tras(L, "Title") or [""])[0]
        cita = ""
        for k, x in enumerate(L):
            if x.startswith("Cite as"):
                cita = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", L[k + 1]))).strip() if k + 1 < len(L) else ""
                break
        attrs = list(dict.fromkeys(L[k - 1] for k, x in enumerate(L) if x == "--" and k > 0))
        ficheros = sorted({L[k + 1] for k, x in enumerate(L) if x == "Object Name:"})
        cota = (tras(L, "Max") or [""])[0]
        tipo = titulo.split()[0] if titulo else ""
        isla = next((n for n, pat in [("Santa Cruz", r"S\.? ?Cruz|Santa ?Cruz"), ("San Cristóbal", r"San Cristobal"),
                                      ("Isabela", r"Isabela"), ("Floreana", r"Floreana")] if re.search(pat, titulo)), "")
        estacion = re.sub(r"^(AWS-[RP]|MRR-R|BIRAL-R|ASOS-E|INAMHI_E|MET-E)\s+", "", titulo).split(",")[0].strip()
        lluvia = [a for a in attrs if a.startswith("PCP")]
        filas.append({
            "id": i, "titulo": titulo, "tipo": tipo, "isla": isla, "estacion": estacion,
            "cota_m": float(cota) if re.fullmatch(r"[\d.]+", cota or "") else None,
            "inicio": (tras(L, "Begin") or [""])[0], "fin": (tras(L, "End") or [""])[0],
            "publicado": (tras(L, "Publication Date") or [""])[0], "actualizado": (tras(L, "Last Update Date") or [""])[0],
            "licencia": re.sub(r"<[^>]+>", "", (tras(L, "License and Usage Rights") or [""])[0]).strip(),
            "variables_lluvia": ";".join(lluvia),
            "lluvia_balancin": any("bucket" in a for a in lluvia),
            "lluvia_radar": any("radar" in a for a in lluvia),
            "humedad_suelo_Vwc": "Vwc" in attrs, "niebla_FOG": "FOG" in attrs,
            "n_variables": len(attrs), "n_ficheros": len(ficheros),
            "coordenadas": "solo con usuario (no públicas)" if any("not publicly available" in x for x in L) else "",
            "cita": cita, "doi": dois.get(i, ""),
            "acceso": "metadatos públicos; descarga con nombre, correo y acuerdo de uso",
        })
    inv = pd.DataFrame(filas).sort_values(["isla", "tipo", "cota_m"])
    inv.to_csv(OUT / "inventario_darwin.csv", index=False)
    return inv


# ------------------------------------------------------------------ B. GAR
def cargar_gar():
    hg = xr.open_dataset(GAR / "GAR_d02km_static_hgt.nc")
    lm = xr.open_dataset(GAR / "GAR_d02km_static_landmask.nc")
    lat, lon = hg.lat.values, hg.lon.values
    z = hg.hgt.values[0]
    tierra = lm.landmask.values[0] > 0.5
    sel = np.zeros_like(tierra)
    for (x0, x1, y0, y1) in CAJAS.values():
        sel |= (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
    ii, jj = np.where(sel)
    i0, i1, j0, j1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    series, faltan = [], []
    for a in ANIOS:
        f = GAR / f"GAR_d02km_d_2d_prcp_{a}.nc"
        if not f.exists():
            faltan.append(a)
            continue
        try:
            with xr.open_dataset(f) as d:
                # media diaria en mm/h -> mm/día
                v = d.prcp.isel(south_north=slice(i0, i1), west_east=slice(j0, j1))
                v = v.drop_vars([c for c in ("lat", "lon", "south_north", "west_east") if c in v.coords])
                series.append((v * 24.0).load())
        except OSError:  # fichero incompleto o dañado: se vuelve a bajar con --descargar tras borrarlo
            faltan.append(a)
    pr = xr.concat(series, "time") if series else None
    return dict(lat=lat[i0:i1, j0:j1], lon=lon[i0:i1, j0:j1], z=z[i0:i1, j0:j1], tierra=tierra[i0:i1, j0:j1],
                pr=pr, faltan=faltan)


def celda(g, la, lo):
    d = (g["lat"] - la) ** 2 + (g["lon"] - lo) ** 2
    d = np.where(g["tierra"], d, np.inf)
    return np.unravel_index(np.argmin(d), d.shape)


def max_anual(s):
    s = s.dropna()
    return s.groupby(s.index.year).max()


def ajustes(am, valores, T=(2, 5, 10, 25, 50, 100)):
    """Gumbel (MV) y GEV (MV) sobre máximos anuales. Devuelve T de 'valores' y niveles de retorno."""
    am = np.asarray(am, float)
    am = am[np.isfinite(am)]
    loc, esc = stats.gumbel_r.fit(am)
    c, gl, ge = stats.genextreme.fit(am)
    r = {"n_anios": len(am), "gumbel_loc": loc, "gumbel_esc": esc, "gev_xi": -c, "gev_loc": gl, "gev_esc": ge}
    for v in valores:
        pg = stats.gumbel_r.sf(v, loc, esc)
        pe = stats.genextreme.sf(v, c, gl, ge)
        r[f"T_gumbel_{v}mm"] = 1 / pg if pg > 1e-9 else None
        r[f"T_gev_{v}mm"] = 1 / pe if pe > 1e-9 else None
        r[f"anios_excede_{v}mm"] = int((am >= v).sum())
    for t in T:
        r[f"P{t}_gumbel_mm"] = stats.gumbel_r.isf(1 / t, loc, esc)
        r[f"P{t}_gev_mm"] = stats.genextreme.isf(1 / t, c, gl, ge)
    return r


def dist_recta(lon, lat, a, b):
    """Distancia (km) de cada celda al segmento a-b (lon, lat)."""
    k = 111.32
    x, y = (lon - a[0]) * k, (lat - a[1]) * k
    bx, by = (b[0] - a[0]) * k, (b[1] - a[1]) * k
    t = np.clip((x * bx + y * by) / (bx * bx + by * by), 0, 1)
    return np.hypot(x - t * bx, y - t * by)


def gar_analisis(g):
    pr = g["pr"]
    t = pd.to_datetime(pr.time.values)
    anios_completos = sorted(set(t.year))
    # ---- puntos
    filas_p, am_p, at_p, rt, nino = [], {}, {}, [], []
    for nom, (isla, la, lo, cota, fuente) in PUNTOS.items():
        i, j = celda(g, la, lo)
        s = pd.Series(pr.values[:, i, j], index=t)
        am = max_anual(s)
        am_p[nom] = am
        at_p[nom] = s.groupby(s.index.year).sum()
        on = s[s.index.month.isin([10, 11])]
        filas_p.append({
            "punto": nom, "isla": isla, "lat": la, "lon": lo, "cota_estacion_m": cota, "fuente_coord": fuente,
            "celda_lat": round(float(g["lat"][i, j]), 4), "celda_lon": round(float(g["lon"][i, j]), 4),
            "cota_celda_gar_m": round(float(g["z"][i, j])),
            "lluvia_media_anual_mm": round(float(s.groupby(s.index.year).sum().mean()), 0),
            "media_max_diario_anual_mm": round(float(am.mean()), 1),
            "max_diario_mm": round(float(s.max()), 1), "fecha_max": s.idxmax().strftime("%Y-%m-%d"),
            "max_diario_oct_nov_mm": round(float(on.max()), 1), "fecha_max_oct_nov": on.idxmax().strftime("%Y-%m-%d"),
            "p99_dias_lluvia_mm": round(float(s[s >= 1].quantile(0.99)), 1),
            "dias_ge_60mm": int((s >= 60).sum()), "dias_ge_100mm": int((s >= 100).sum()),
            "dias_ge_179mm": int((s >= 179).sum()), "dias_ge_238mm": int((s >= 238).sum()),
        })
        r = ajustes(am.values, UMBRALES)
        rt.append({"punto": nom, "isla": isla, **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}})
        for ev, (a, b) in NINO.items():
            w = s[a:b]
            if len(w):
                nino.append({"punto": nom, "isla": isla, "evento": ev, "total_mm": round(float(w.sum())),
                             "max_diario_mm": round(float(w.max()), 1), "fecha_max": w.idxmax().strftime("%Y-%m-%d"),
                             "dias_ge_60mm": int((w >= 60).sum()), "dias_ge_100mm": int((w >= 100).sum())})
    P = pd.DataFrame(filas_p)
    P.to_csv(OUT / "gar_puntos.csv", index=False)
    AM = pd.DataFrame(am_p)
    AM.index.name = "anio"
    AM.round(1).to_csv(OUT / "gar_max_anual_puntos.csv")
    AT = pd.DataFrame(at_p)
    AT.index.name = "anio"
    AT.round(0).to_csv(OUT / "gar_total_anual_puntos.csv")
    RT = pd.DataFrame(rt)
    RT.to_csv(OUT / "gar_periodo_retorno.csv", index=False)
    NI = pd.DataFrame(nino)
    NI.to_csv(OUT / "gar_nino_puntos.csv", index=False)

    # ---- gradiente con la cota (celdas de tierra por isla, y transecto de barlovento)
    anual = pr.groupby("time.year").sum().mean("year").values
    amax = pr.groupby("time.year").max().mean("year").values
    on = pr.sel(time=pr["time.month"].isin([10, 11]))
    amax_on = on.groupby("time.year").max().mean("year").values
    filas_g = []
    for isla, (x0, x1, y0, y1) in CAJAS.items():
        m = g["tierra"] & (g["lon"] >= x0) & (g["lon"] <= x1) & (g["lat"] >= y0) & (g["lat"] <= y1)
        tr = m & (dist_recta(g["lon"], g["lat"], *TRANSECTOS[isla]) <= 3.0)
        for nom_sel, mm in (("isla", m), ("transecto_barlovento", tr)):
            bins = np.arange(0, 1000, 100)
            zb = np.digitize(g["z"], bins) - 1
            for b in range(len(bins)):
                k = mm & (zb == b)
                if k.sum() == 0:
                    continue
                filas_g.append({"isla": isla, "seleccion": nom_sel, "cota_min_m": bins[b], "cota_max_m": bins[b] + 100,
                                "n_celdas": int(k.sum()),
                                "lluvia_media_anual_mm": round(float(anual[k].mean())),
                                "media_max_diario_anual_mm": round(float(amax[k].mean()), 1),
                                "media_max_diario_oct_nov_mm": round(float(amax_on[k].mean()), 1)})
    G = pd.DataFrame(filas_g)
    # factor respecto a la franja costera (0–100 m) de cada isla y selección
    for (isla, sel), d in G.groupby(["isla", "seleccion"]):
        base = d[d.cota_min_m == 0]
        if len(base):
            for c in ("lluvia_media_anual_mm", "media_max_diario_anual_mm", "media_max_diario_oct_nov_mm"):
                G.loc[d.index, "factor_" + c.replace("_mm", "")] = (d[c] / float(base[c].iloc[0])).round(2)
    G.to_csv(OUT / "gar_gradiente_altitud.csv", index=False)
    # malla para la figura
    malla = {"z": g["z"], "anual": anual, "amax": amax, "tierra": g["tierra"], "lon": g["lon"], "lat": g["lat"]}
    return P, AM, AT, RT, NI, G, malla, anios_completos


# ------------------------------------------------------------------ C. pluviómetros FCD
def fcd():
    out, nino_fcd = {}, []
    for nom, f, cota in (("Puerto Ayora (CDRS/DARWIN)", "climate_puerto-ayora.csv", 2), ("Bellavista (FCD)", "climate_bellavista.csv", 223)):
        p = FCD / f
        if not p.exists():
            continue
        d = pd.read_csv(p, usecols=["observation_date", "precipitation"], parse_dates=["observation_date"])
        s = d.set_index("observation_date").precipitation.astype(float).sort_index()
        s = s[~s.index.duplicated()]
        n = s.notna().groupby(s.index.year).sum()
        am = s.groupby(s.index.year).max()
        out[nom] = pd.DataFrame({"max_diario_mm": am, "total_mm": s.groupby(s.index.year).sum(), "dias_con_dato": n})
        for ev, (a, b) in NINO.items():
            w = s[a:b]
            if w.notna().sum() > 0.9 * len(pd.date_range(a, b)):
                nino_fcd.append({"estacion": nom, "evento": ev, "total_mm": round(float(w.sum())), "max_diario_mm": float(w.max()),
                                 "fecha_max": w.idxmax().strftime("%Y-%m-%d"), "dias_ge_60mm": int((w >= 60).sum()),
                                 "dias_ge_100mm": int((w >= 100).sum())})
    filas = []
    for nom, d in out.items():
        for a, r in d.iterrows():
            filas.append({"estacion": nom, "anio": a, "max_diario_mm": r.max_diario_mm, "total_mm": round(r.total_mm, 1),
                          "dias_con_dato": int(r.dias_con_dato),
                          "anio_completo": bool(r.dias_con_dato >= 330)})
    F = pd.DataFrame(filas)
    F.to_csv(OUT / "fcd_max_anual.csv", index=False)
    pd.DataFrame(nino_fcd).to_csv(OUT / "fcd_nino.csv", index=False)
    return F


def gar_vs_fcd(AM, AT, F):
    filas = []
    for est in F.estacion.unique():
        f = F[(F.estacion == est) & F.anio_completo].set_index("anio").max_diario_mm
        gg = AM[est] if est in AM else None
        if gg is None:
            continue
        com = sorted(set(f.index) & set(gg.index))
        if len(com) < 5:
            continue
        a, b = f.loc[com], gg.loc[com]
        rho = stats.spearmanr(a, b).correlation
        ft = F[(F.estacion == est) & F.anio_completo].set_index("anio").total_mm.loc[com]
        gt = AT[est].loc[com]
        filas.append({"estacion": est, "anios_comunes": len(com), "desde": min(com), "hasta": max(com),
                      "media_max_anual_pluviometro_mm": round(float(a.mean()), 1), "media_max_anual_gar_mm": round(float(b.mean()), 1),
                      "cociente_gar_pluviometro": round(float(b.mean() / a.mean()), 2),
                      "mediana_max_anual_pluviometro_mm": round(float(a.median()), 1), "mediana_max_anual_gar_mm": round(float(b.median()), 1),
                      "max_pluviometro_mm": round(float(a.max()), 1), "anio_max_pluviometro": int(a.idxmax()),
                      "max_gar_mm": round(float(b.max()), 1), "anio_max_gar": int(b.idxmax()),
                      "spearman_max_anuales": round(float(rho), 2),
                      "media_total_anual_pluviometro_mm": round(float(ft.mean())), "media_total_anual_gar_mm": round(float(gt.mean())),
                      "cociente_total_gar_pluviometro": round(float(gt.mean() / ft.mean()), 2),
                      "spearman_totales_anuales": round(float(stats.spearmanr(ft, gt).correlation), 2)})
    V = pd.DataFrame(filas)
    V.to_csv(OUT / "gar_vs_fcd.csv", index=False)
    return V


def transferencia(AM, AT, rt_fcd, T=(2, 10, 25, 50, 100)):
    """Escala los cuantiles MEDIDOS de un pluviómetro de referencia con el cociente de GAR entre el punto y la celda
    del pluviómetro (mediana de los máximos anuales, que es robusta a los días extremos dudosos del modelo).
    Referencias: Puerto Ayora (1965–2025, costa) y Bellavista (1988–2018, parte media). Es un escenario [E]."""
    filas = []
    for ref in ("Puerto Ayora (CDRS/DARWIN)", "Bellavista (FCD)"):
        if ref not in rt_fcd or ref not in AM:
            continue
        for p_ in AM.columns:
            k = float(AM[p_].median() / AM[ref].median())
            ka = float(AT[p_].mean() / AT[ref].mean())
            fila = {"punto": p_, "referencia": ref, "cociente_mediana_max_anual": round(k, 2), "cociente_total_anual": round(ka, 2)}
            for t in T:
                fila[f"P{t}_escalado_mm"] = round(k * rt_fcd[ref][f"P{t}_gumbel_mm"], 0)
            filas.append(fila)
    # Corrección cruda del sesgo húmedo de GAR en la costa de San Cristóbal: se escala la serie de máximos por el cociente
    # entre el total anual publicado (≈500 mm/año, Schmidt et al. 2025 citando a Paltán et al. 2021) y el de GAR.
    for p_, obs in CORR_TOTAL.items():
        if p_ in AM:
            f = obs / float(AT[p_].mean())
            r = ajustes((AM[p_] * f).values, UMBRALES)
            fila = {"punto": p_, "referencia": f"GAR escalado por total anual publicado ({obs} mm)", "cociente_total_anual": round(f, 3)}
            for t in T:
                fila[f"P{t}_escalado_mm"] = round(r[f"P{t}_gumbel_mm"], 0)
            for v in UMBRALES:
                fila[f"T_gumbel_{v}mm"] = None if r[f"T_gumbel_{v}mm"] is None else round(r[f"T_gumbel_{v}mm"], 1)
            filas.append(fila)
    TR = pd.DataFrame(filas)
    TR.to_csv(OUT / "gar_transferencia.csv", index=False)
    return TR


# ------------------------------------------------------------------ figuras
NOTA = "Fuente: GAR v1 (Schmidt et al. 2025; TU Berlín, CC BY 4.0), lluvia MODELADA (WRF 2 km, ERA5). "


def fig_gradiente(G, malla):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharey=False)
    col = {"Santa Cruz": "#c0392b", "San Cristóbal": "#2471a3"}
    for isla, c in col.items():
        x0, x1, y0, y1 = CAJAS[isla]
        m = malla["tierra"] & (malla["lon"] >= x0) & (malla["lon"] <= x1) & (malla["lat"] >= y0) & (malla["lat"] <= y1)
        tr = m & (dist_recta(malla["lon"], malla["lat"], *TRANSECTOS[isla]) <= 3.0)
        for ax, v in zip(axs, ("anual", "amax")):
            ax.scatter(malla["z"][m], malla[v][m], s=6, color=c, alpha=0.18, lw=0)
            ax.scatter(malla["z"][tr], malla[v][tr], s=16, color=c, alpha=0.9, lw=0, label=f"{isla}, transecto de barlovento")
    for nom, (mm, cota) in EVENTO.items():
        axs[1].scatter([cota], [mm], marker="*", s=160, color="k", zorder=5)
        axs[1].annotate(f"{nom}\n30-oct-2026: ≥{mm:.0f} mm", (cota, mm), xytext=(8, -4), textcoords="offset points", fontsize=8)
    axs[0].set_title("Lluvia media anual (1980–2025)", fontsize=10)
    axs[1].set_title("Media de los máximos diarios anuales (1980–2025)", fontsize=10)
    for ax in axs:
        ax.set_xlabel("Cota de la celda del modelo (m)")
        ax.set_ylabel("mm" if ax is axs[1] else "mm/año")
        ax.grid(alpha=0.3)
    axs[0].legend(fontsize=8, frameon=False, loc="upper left")
    axs[1].set_ylim(30, 265)
    fig.suptitle("Lluvia y cota en Santa Cruz y San Cristóbal según el reanálisis GAR (celdas de 2 km; claro: toda la isla)", fontsize=10.5)
    fig.text(0.01, 0.01, NOTA + "Estrellas: lluvia MEDIDA (IERSE-WSN), mínimos.", fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(FIG_SC / "marburg_gar_gradiente.png", dpi=160)
    plt.close(fig)


def fig_max_anual_sc(AM, F):
    fig, ax = plt.subplots(figsize=(11, 4.6))
    for a, b in NINO.values():
        ax.axvspan(int(a[:4]) - 0.5, int(b[:4]) + 0.5, color="#f5cba7", alpha=0.5, lw=0)
    est = [("Bellavista (FCD)", "#c0392b"), ("Puerto Ayora (CDRS/DARWIN)", "#7f8c8d"), ("Santa Rosa (DARWIN/IERSE)", "#2471a3")]
    for nom, c in est:
        if nom in AM:
            ax.plot(AM.index, AM[nom], "-", color=c, lw=1.2, label=f"GAR, celda de {nom.split(' (')[0]}")
        f = F[(F.estacion == nom) & F.anio_completo] if len(F) else F
        if len(f):
            ax.plot(f.anio, f.max_diario_mm, "o", color=c, ms=4, mfc="white", label=f"Pluviómetro FCD, {nom.split(' (')[0]}")
    for nom, (mm, _) in EVENTO.items():
        ax.axhline(mm, color="k", ls="--", lw=0.9)
        ax.text(1980.3, mm + 4, f"{nom}, 30-oct-2026: ≥{mm:.0f} mm (medido)", fontsize=8)
    ax.set_xlim(1979.5, 2026.5)
    ax.set_ylim(0, 360)
    f8 = F[(F.estacion == "Bellavista (FCD)") & (F.anio == 2008)] if len(F) else F
    if len(f8) and float(f8.max_diario_mm.iloc[0]) > 360:
        ax.annotate(f"Bellavista 2008: {float(f8.max_diario_mm.iloc[0]):.0f} mm (dudoso) ↑", (2008, 352), ha="center", fontsize=7.5, color="#c0392b")
    ax.set_ylabel("Máximo diario del año (mm)")
    ax.set_title("Máximo diario de cada año en Santa Cruz: reanálisis GAR frente a pluviómetros (sombreado: El Niño)", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=2, frameon=False, loc="upper right")
    fig.text(0.01, 0.01, NOTA + "Pluviómetros: FCD dataZone (años con ≥330 días). El dato de Bellavista de marzo de 2008 está en duda.",
             fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG_SC / "marburg_max_anual_santa_cruz.png", dpi=160)
    plt.close(fig)


def fig_san_cristobal(AM, RT):
    pts = ["Puerto Baquerizo Moreno", "El Progreso", "El Junco", "Toma La Toma (El Progreso)", "Manantial El Chino"]
    col = ["#7f8c8d", "#d68910", "#2471a3", "#27ae60", "#7d3c98"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axs[0]
    for a, b in NINO.values():
        ax.axvspan(int(a[:4]) - 0.5, int(b[:4]) + 0.5, color="#f5cba7", alpha=0.5, lw=0)
    for p, c in zip(pts, col):
        if p in AM:
            ax.plot(AM.index, AM[p], "-", color=c, lw=1.1, label=p)
    ax.set_ylabel("Máximo diario del año (mm)")
    ax.set_title("Máximo diario de cada año (GAR, sombreado: El Niño)", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, frameon=False, loc="upper right")
    ax = axs[1]
    T = [2, 5, 10, 25, 50, 100]
    for p, c in zip(pts, col):
        r = RT[RT.punto == p]
        if len(r):
            ax.plot(T, [float(r[f"P{t}_gumbel_mm"].iloc[0]) for t in T], "-o", color=c, ms=3, lw=1.1)
    ax.set_xscale("log")
    ax.set_xticks(T)
    ax.set_xticklabels([str(t) for t in T])
    ax.set_xlabel("Periodo de retorno (años)")
    ax.set_ylabel("Lluvia diaria (mm)")
    ax.set_title("Lluvia diaria por periodo de retorno (Gumbel)", fontsize=10)
    ax.grid(alpha=0.3, which="both")
    fig.suptitle("San Cristóbal: lluvia diaria extrema MODELADA por GAR, 1980–2025 (sin validar en la isla: no hay serie medida larga pública)", fontsize=10.5)
    fig.text(0.01, 0.01, NOTA + "Escenario, no dato de diseño: en la costa GAR da ≈1 270 mm/año frente a ≈500 publicados (Paltán et al. 2021).",
             fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(FIG_SX / "marburg_gar_san_cristobal.png", dpi=160)
    plt.close(fig)


def fig_inventario(inv):
    d = inv[inv.tipo.isin(["AWS-P", "AWS-R", "MET-E", "INAMHI_E", "MRR-R", "BIRAL-R", "ASOS-E"])].copy()
    d["ini"] = pd.to_datetime(d.inicio, errors="coerce")
    d["fin_"] = pd.to_datetime(d.fin, errors="coerce")
    d = d.dropna(subset=["ini", "fin_"])
    d["es_hist"] = d.tipo.isin(["MET-E", "INAMHI_E"])
    d["nom"] = d.estacion.replace({"S.Rosa": "Santa Rosa", "SEGS": "Aeropuerto Baltra (SEGS)", "SEST": "Aeropuerto (SEST)",
                                   "M221": "INAMHI M221 Pto. Baquerizo", "M193": "INAMHI M193 El Progreso"})
    d["et"] = d.isla + " · " + d.nom + d.cota_m.map(lambda v: f" ({v:.0f} m)" if pd.notna(v) and v > 0 else "") + d["es_hist"].map(
        {True: " ", False: ""})
    d = d.sort_values(["es_hist", "isla", "cota_m"]).groupby("et", sort=False).agg(
        ini=("ini", "min"), fin_=("fin_", "max"), es_hist=("es_hist", "first"), tipo=("tipo", lambda x: "/".join(sorted({t.split("-")[0].split("_")[0] for t in x}))))
    cmap = {"MET": "#7f8c8d", "INA": "#d68910", "AWS": "#2471a3", "MRR": "#7d3c98", "BIR": "#7d3c98", "ASO": "#27ae60"}
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True, gridspec_kw={"width_ratios": [1, 1.5]})
    for k, (et, r) in enumerate(d.iterrows()):
        c = cmap.get(r.tipo[:3], "0.4")
        ax = axs[0] if r.es_hist else axs[1]
        ax.plot([r.ini, r.fin_], [k, k], color=c, lw=6, solid_capstyle="butt")
        ax.text(r.fin_, k, f" {r.fin_:%m-%Y}", va="center", fontsize=7)
    axs[0].set_xlim(pd.Timestamp("1955-01-01"), pd.Timestamp("2026-12-31"))
    axs[1].set_xlim(pd.Timestamp("2022-01-01"), pd.Timestamp("2027-03-01"))
    axs[1].axvline(pd.Timestamp("2026-10-30"), color="k", ls="--", lw=1)
    axs[1].text(pd.Timestamp("2026-10-30"), len(d) - 0.3, "30-oct ", fontsize=8, ha="right", va="top")
    axs[0].xaxis.set_major_locator(matplotlib.dates.YearLocator(20))
    axs[0].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    axs[0].set_yticks(range(len(d)))
    axs[0].set_yticklabels([e.strip() if h else f"{e}  [{t}]" for e, t, h in zip(d.index, d.tipo, d.es_hist)], fontsize=7.5)
    axs[0].invert_yaxis()
    axs[0].set_title("Series históricas de terceros (FCD, INAMHI)", fontsize=9.5)
    axs[1].set_title("Red DARWIN y METAR de aeropuertos (2022–2026)", fontsize=9.5)
    for ax in axs:
        ax.grid(axis="x", alpha=0.3)
    fig.suptitle("Portal de datos DARWIN (U. de Marburgo): periodo publicado de cada serie. Ninguna estación propia llega al 30-oct-2026",
                 fontsize=10)
    fig.text(0.01, 0.01, "Fuente: metadatos públicos de vhrz669.hrz.uni-marburg.de/darwin, consultados el 2-nov-2026. "
             "Descarga con registro y acuerdo de uso. AWS = estación automática (10 min); MRR/BIRAL = radar y sensor óptico.",
             fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(FIG_SC / "marburg_inventario.png", dpi=160)
    plt.close(fig)


def limpio(o):
    """Convierte tipos de numpy y NaN/inf a JSON válido."""
    if isinstance(o, dict):
        return {str(k): limpio(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpio(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (float, np.floating)):
        return None if not np.isfinite(o) else round(float(o), 3)
    return o


# ------------------------------------------------------------------ main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if "--descargar" in sys.argv:
        descargar()
    inv = inventario()
    print(f"Inventario DARWIN: {len(inv)} conjuntos de datos")
    fig_inventario(inv)
    g = cargar_gar()
    if g["pr"] is None:
        print("No hay ficheros GAR en", GAR)
        return
    if g["faltan"]:
        print("AVISO: faltan años GAR:", g["faltan"])
    P, AM, AT, RT, NI, G, malla, anios = gar_analisis(g)
    F = fcd()
    V = gar_vs_fcd(AM, AT, F) if len(F) else pd.DataFrame()
    # periodo de retorno con los pluviómetros FCD (años completos), para comparar con GAR
    rt_fcd = {}
    for est in F.estacion.unique() if len(F) else []:
        f = F[(F.estacion == est) & F.anio_completo]
        rt_fcd[est] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in ajustes(f.max_diario_mm.values, UMBRALES).items()}
        rt_fcd[est]["anios"] = f"{f.anio.min()}–{f.anio.max()}"
    TR = transferencia(AM, AT, rt_fcd)
    fig_gradiente(G, malla)
    fig_max_anual_sc(AM, F)
    fig_san_cristobal(AM, RT)
    resumen = {
        "consultado": "2026-11-02",
        "darwin": {"n_conjuntos": int(len(inv)), "por_tipo": inv.tipo.value_counts().to_dict(),
                   "url": f"{DARWIN}/data_pre.do?cmd=showall",
                   "acceso": "metadatos públicos; descarga con nombre, correo y aceptación del acuerdo de uso (§3: no redistribuir; "
                             "publicar requiere aprobación del titular y coautoría)"},
        "gar": {"anios": f"{min(anios)}–{max(anios)}", "faltan": g["faltan"], "licencia": "CC BY 4.0",
                "url": GAR_URL, "doi_validacion": "10.5281/zenodo.11916492"},
        "puntos": P.set_index("punto").to_dict(orient="index"),
        "periodo_retorno_gar": RT.set_index("punto").to_dict(orient="index"),
        "periodo_retorno_fcd": rt_fcd,
        "gar_vs_fcd": V.to_dict(orient="records"),
        "transferencia": TR.to_dict(orient="records"),
    }
    (OUT / "resumen_marburg.json").write_text(json.dumps(limpio(resumen), ensure_ascii=False, indent=1))
    print("Listo:", OUT)


if __name__ == "__main__":
    main()
