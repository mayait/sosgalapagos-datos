"""Fase S0 · evalúa la señal de GOES-19 (rayos GLM, topes fríos de la banda 13 y RRQPE)
frente a la lluvia medida en Santa Cruz.

Entradas:
- satelite/cache/ (lo que deja s0_extraer.py);
- lluvia medida: un CSV fuente,estacion,ts(UTC),valor exportado en modo solo lectura de clima.db
  (--obs). Sin --obs usa datos/ierse-wsn/serie_5min.csv.gz (solo IERSE, hora UTC−6).

Salidas: satelite/resumen.json y satelite/figuras/*.png. El informe es evaluacion-s0.md.

Todo lo de aquí es una estimación satelital: no es lluvia medida ni una alerta oficial.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
CLIMA = AQUI.parent
sys.path.insert(0, str(CLIMA / "recolector"))
sys.path.insert(0, str(AQUI))
import inundacion  # noqa: E402
from s0_extraer import EVENTOS  # noqa: E402

UTC = dt.timezone.utc
CACHE = AQUI / "cache"
FIG = AQUI / "figuras"
ZONAS_SC = ["la-cascada", "santa-cruz-alta"]  # las únicas zonas con estaciones en los eventos
ANILLOS_KM = {"zona": 0, "25km": 25, "50km": 50}
SUB_ABI_MIN, SUB_GLM = 30, 6  # cadencia de la muestra: ABI cada 30 min, 1 de cada 6 archivos GLM
ORDEN = ["muy alto", "alto", "medio", "bajo"]

# Días de la muestra (UTC), elegidos con semilla fija entre abr y oct-2026 (ver evaluacion-s0.md §2):
#   seco: máx. diario < 2 mm en todas las estaciones IERSE con ≥ 80 % de cobertura;
#   moderado: 5–25 mm en el día y < 10 mm en 1 h;
#   fuerte: días con ≥ 10 mm en 1 h fuera de los tres eventos.
MUESTRA = {
    "seco": ["2026-05-09", "2026-06-13", "2026-07-10", "2026-07-30", "2026-08-08", "2026-09-21",
             "2026-10-02", "2026-10-16"],
    "moderado": ["2026-05-16", "2026-06-20", "2026-07-14", "2026-07-18", "2026-09-16", "2026-10-19"],
    "fuerte": ["2026-05-07", "2026-05-12", "2026-06-14", "2026-09-12", "2026-10-10"],
}

ESTACIONES = {  # (lat, lon) de la tabla estaciones de clima.db
    "ierse/n_glps01": ("Cerro Crocker", -0.642398, -90.326),
    "ierse/n_glps05": ("Los Guayabillos", -0.699079, -90.341962),
    "ierse/n_glps06": ("Militar", -0.489962, -90.2808),
    "ierse/n_glps09": ("Santa Rosa", -0.654547, -90.403519),
    "inamhi/M0191": ("Puerto Ayora (INAMHI)", -0.743056, -90.3025),
    "tempest/punta_estrada": ("Punta Estrada", -0.7499, -90.31081),
}

# Señales candidatas: (nombre, campo, umbral, texto)
SENALES = [
    ("rayos_1", "rayos_30min", 1, "≥ 1 destello GLM en 30 min"),
    ("rayos_5", "rayos_30min", 5, "≥ 5 destellos GLM en 30 min"),
    ("frio221_10", "frio221_pct", 10, "≥ 10 % de píxeles con Tb < 221 K"),
    ("frio235_25", "frio235_pct", 25, "≥ 25 % de píxeles con Tb < 235 K"),
    ("tbmin_210", "tb_frio_k", 210, "Tb mínima ≤ 210 K"),
    ("rrqpe_5", "rrqpe_max", 5, "RRQPE máx. ≥ 5 mm/h"),
    ("rrqpe_10", "rrqpe_max", 10, "RRQPE máx. ≥ 10 mm/h"),
    ("rrqpe_20", "rrqpe_max", 20, "RRQPE máx. ≥ 20 mm/h"),
    ("rrqpe_media5", "rrqpe_media", 5, "RRQPE media ≥ 5 mm/h"),
]


# Reglas combinadas (O lógico): (anillo, campo, umbral). «v0» es la que usa hoy satelite/vigilancia.py.
COMBOS = {
    "v0": [("25km", "rayos_30min", 1), ("25km", "frio221_pct", 10), ("zona", "rrqpe_max", 10)],
    "frio_25km_o_rrqpe10": [("25km", "frio221_pct", 10), ("25km", "rrqpe_max", 10)],
    "rrqpe10_25km": [("25km", "rrqpe_max", 10)],
    "frio_zona": [("zona", "frio221_pct", 10)],
    "frio_y_rrqpe_25km": "y",  # topes < 221 K (≥ 10 %) Y RRQPE ≥ 10 mm/h, ambos a 25 km
}


def combo(sats: dict, zid: str, nombre: str) -> pd.Series:
    if COMBOS[nombre] == "y":
        a = activa(sats[f"{zid}|25km"], "frio221_pct", 10)
        b = activa(sats[f"{zid}|25km"], "rrqpe_max", 10)
        return a & b.reindex(a.index, fill_value=False)
    s = None
    for an, campo, u in COMBOS[nombre]:
        x = activa(sats[f"{zid}|{an}"], campo, u)
        s = x if s is None else (s | x.reindex(s.index, fill_value=False))
    return s


# --------------------------------------------------------------------------- datos

def cargar_obs(ruta: str | None) -> pd.DataFrame:
    if ruta:
        d = pd.read_csv(ruta)
        d["ts"] = pd.to_datetime(d["ts"], utc=True)
        return d[["fuente", "estacion", "ts", "valor"]]
    s = pd.read_csv(CLIMA / "datos/ierse-wsn/serie_5min.csv.gz", usecols=["estacion_id", "fecha_hora_local", "lluvia_mm"])
    s = s.dropna(subset=["lluvia_mm"])
    ts = pd.to_datetime(s["fecha_hora_local"]) + pd.Timedelta(hours=6)  # UTC−6 -> UTC
    return pd.DataFrame({"fuente": "ierse", "estacion": s["estacion_id"], "ts": ts.dt.tz_localize("UTC"),
                         "valor": s["lluvia_mm"]})


def base_memoria(obs: pd.DataFrame) -> sqlite3.Connection:
    """clima.db mínima en memoria para reutilizar recolector/inundacion.py tal cual."""
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE obs (fuente TEXT, estacion TEXT, variable TEXT, ts TEXT, valor REAL)")
    con.execute("CREATE INDEX i ON obs(fuente, estacion, ts)")
    con.executemany("INSERT INTO obs VALUES (?,?,?,?,?)",
                    ((f, e, "lluvia_mm", t.strftime("%Y-%m-%dT%H:%M:%SZ"), v)
                     for f, e, t, v in obs.itertuples(index=False)))
    return con


def cargar_abi(producto: str) -> tuple[list[dt.datetime], np.ndarray, np.ndarray, np.ndarray]:
    archivos = sorted((CACHE / producto).glob("*.npz"))
    tiempos, pilas, lat, lon = [], [], None, None
    for a in archivos:
        with np.load(a) as z:
            if lat is None:
                lat, lon = z["lat"], z["lon"]
            if z["datos"].shape != lat.shape:
                continue
            pilas.append(z["datos"])
            tiempos.append(dt.datetime.strptime(a.stem, "%Y%m%d%H%M").replace(tzinfo=UTC))
    return tiempos, np.stack(pilas), lat, lon


def cargar_glm() -> tuple[pd.DataFrame, dict]:
    """Destellos y cobertura por intervalo de 10 min (fracción de los 30 archivos de 20 s leídos)."""
    partes, cobertura = [], {}
    for a in sorted((CACHE / "glm").glob("*.npz")):
        with np.load(a) as z:
            if len(a.stem) == 10:  # archivo de una hora (formato antiguo): 180 archivos GLM
                h = dt.datetime.strptime(a.stem, "%Y%m%d%H").replace(tzinfo=UTC)
                for m in range(0, 60, 10):
                    cobertura[h.replace(minute=m)] = int(z["leidos"]) / 180.0
            else:
                b = dt.datetime.strptime(a.stem, "%Y%m%d%H%M").replace(tzinfo=UTC)
                cobertura[b] = int(z["leidos"]) / 30.0
            if z["t"].size:
                partes.append(pd.DataFrame({"t": z["t"], "lat": z["lat"], "lon": z["lon"], "energia": z["energia"]}))
    d = pd.concat(partes) if partes else pd.DataFrame(columns=["t", "lat", "lon", "energia"])
    d["ts"] = pd.to_datetime(d["t"], unit="s", utc=True)
    return d, cobertura


def zonas_geo() -> dict:
    return json.loads((CLIMA / "recolector/zonas_geo.json").read_text())["zonas"]


def ampliar(bbox, km):
    g = km / 111.0
    return [bbox[0] - g, bbox[1] - g, bbox[2] + g, bbox[3] + g]


def dentro(lat, lon, b):
    return (lon >= b[0]) & (lon <= b[2]) & (lat >= b[1]) & (lat <= b[3])


# --------------------------------------------------------------------------- señales

def series_satelite(c13, rr, glm, cob, zonas, submuestra=False) -> dict[str, pd.DataFrame]:
    """Una tabla por zona y anillo, con paso de 10 min (20 min si submuestra)."""
    t13, a13, la, lo = c13
    trr, arr, _, _ = rr
    paso = SUB_ABI_MIN if submuestra else 10
    i13 = {t: i for i, t in enumerate(t13) if t.minute % paso == 0}
    irr = {t: i for i, t in enumerate(trr) if t.minute % paso == 0}
    g = glm
    if submuestra:  # un archivo GLM de 20 s cada 2 min, como en los días de la muestra
        g = g[((g["t"] % (20 * SUB_GLM)) // 20) == 0]
        cob = {k: min(v, 1 / SUB_GLM) for k, v in cob.items()}
    tiempos = sorted(set(i13) | set(irr))
    salida = {}
    for zid in zonas:
        bb0 = zonas[zid]["bbox"]
        for anillo, km in ANILLOS_KM.items():
            bb = ampliar(bb0, km)
            m = dentro(la, lo, bb)
            gz = g[dentro(g["lat"].values, g["lon"].values, bb)]
            cuenta = gz.set_index("ts").resample("10min").size() if len(gz) else pd.Series(dtype=float)
            filas = []
            for t in tiempos:
                fila = {"ts": t}
                if t in i13:
                    v = a13[i13[t]][m]
                    v = v[np.isfinite(v)]
                    if v.size:
                        fila.update(tb_min_k=float(v.min()), frio235_pct=100 * float((v < 235).mean()),
                                    frio221_pct=100 * float((v < 221).mean()))
                if t in irr:
                    v = arr[irr[t]][m]
                    v = v[np.isfinite(v)]
                    if v.size:
                        fila.update(rrqpe_max=float(v.max()), rrqpe_media=float(v.mean()))
                # destellos en los 30 min que terminan con el barrido (bins de 10 min que empiezan en
                # t-20, t-10 y t), corregidos por la fracción de archivos GLM leídos en esa hora
                n, c = 0.0, []
                for k in range(3):
                    tb = pd.Timestamp(t) - pd.Timedelta(minutes=10 * k)
                    n += float(cuenta.get(tb, 0.0))
                    c.append(cob.get(tb.to_pydatetime(), 0.0))
                cmed = float(np.mean(c))
                fila["rayos_30min"] = n / cmed if cmed > 0 else np.nan
                fila["glm_cobertura"] = cmed
                filas.append(fila)
            d = pd.DataFrame(filas).set_index("ts")
            d["tb_frio_k"] = -d.get("tb_min_k", np.nan)  # para usar «≥ umbral» con -Tb
            salida[f"{zid}|{anillo}"] = d
    return salida


def activa(d: pd.DataFrame, campo: str, umbral: float) -> pd.Series:
    if campo not in d:
        return pd.Series(False, index=d.index)
    if campo == "tb_frio_k":
        return d[campo] >= -umbral
    return d[campo] >= umbral


# --------------------------------------------------------------------------- lluvia medida

def niveles(con, zona_regla, ini, fin, paso_min=10) -> pd.DataFrame:
    """Nivel instantáneo de la regla v0.2 (sin persistencia) y R1h/R3h/R24h cada paso."""
    claves = [c for c, _ in zona_regla["estaciones"]]
    desde = ini - dt.timedelta(days=7)
    series = {}
    for c in claves:
        f, s = inundacion._serie(con, c, desde)
        if s:
            series[c] = (f, s)
    filas, t = [], ini
    while t <= fin:
        nv, R, ant, _ = inundacion._evaluar(series, zona_regla, t, {})
        filas.append({"ts": t, "nivel": nv["nivel"] if nv else None, **(R or {})})
        t += dt.timedelta(minutes=paso_min)
    return pd.DataFrame(filas).set_index("ts")


def lluvia_horaria(obs: pd.DataFrame, clave: str) -> pd.Series:
    f, e = clave.split("/")
    s = obs[(obs.fuente == f) & (obs.estacion == e)].set_index("ts")["valor"]
    if s.empty:
        return s
    # el registro de las HH:MM cierra el intervalo previo: se asigna a la hora del inicio
    s.index = s.index - pd.Timedelta(seconds=1)
    h = s.resample("1h").sum(min_count=1)
    n = s.resample("1h").count()
    esperado = 12
    return h.where(n >= 0.8 * esperado)


# --------------------------------------------------------------------------- análisis

def adelanto(sig: pd.Series, t_ref: pd.Timestamp, hueco_min=60, max_previo_h=3, antes_h=12):
    """Inicio del episodio de señal que antecede a t_ref (huecos ≤ hueco_min).

    Devuelve (minutos de adelanto respecto de t_ref, primera señal en las 12 h previas) o None.
    Si el último disparo antes de t_ref está a más de max_previo_h, no se considera precursor.
    """
    s = sig[(sig.index >= t_ref - pd.Timedelta(hours=antes_h)) & (sig.index <= t_ref)]
    on = s[s].index
    primera = (t_ref - on[0]).total_seconds() / 60 if len(on) else None
    if not len(on) or (t_ref - on[-1]) > pd.Timedelta(hours=max_previo_h):
        return None, primera
    ini = on[-1]
    for t in reversed(on[:-1]):
        if (ini - t) <= pd.Timedelta(minutes=hueco_min):
            ini = t
        else:
            break
    return (t_ref - ini).total_seconds() / 60, primera


def comparar_rrqpe(rr, obs, ventanas) -> dict:
    """RRQPE (media horaria en el píxel de la estación y máximo en 3×3 y 5×5) vs. pluviómetro."""
    trr, arr, la, lo = rr
    tt = pd.DatetimeIndex(trr)
    out = {}
    for clave, (nombre, plat, plon) in ESTACIONES.items():
        h = lluvia_horaria(obs, clave)
        if h.empty:
            continue
        d2 = (la - plat) ** 2 + ((lo - plon) * np.cos(np.radians(plat))) ** 2
        i, j = np.unravel_index(np.nanargmin(d2), d2.shape)
        px = pd.Series(arr[:, i, j], index=tt)
        m3 = pd.Series(np.nanmax(arr[:, max(i - 1, 0):i + 2, max(j - 1, 0):j + 2], axis=(1, 2)), index=tt)
        m5 = pd.Series(np.nanmax(arr[:, max(i - 2, 0):i + 3, max(j - 2, 0):j + 3], axis=(1, 2)), index=tt)
        filas = []
        for nombre_v, (a, b) in ventanas.items():
            a, b = pd.Timestamp(a, tz="UTC"), pd.Timestamp(b, tz="UTC")
            for serie, etiqueta in ((px, "pixel"), (m3, "max3x3"), (m5, "max5x5")):
                hs = serie[(serie.index >= a) & (serie.index < b)].resample("1h")
                mm = hs.mean().where(hs.count() >= 4)
                g = h[(h.index >= a) & (h.index < b)]
                j2 = pd.concat([g.rename("medida"), mm.rename("sat")], axis=1).dropna()
                if len(j2) < 3:
                    continue
                filas.append({
                    "ventana": nombre_v, "satelite": etiqueta, "horas": int(len(j2)),
                    "total_medido_mm": round(float(j2.medida.sum()), 1),
                    "total_rrqpe_mm": round(float(j2.sat.sum()), 1),
                    "max_1h_medido_mm": round(float(j2.medida.max()), 1),
                    "hora_max_medido": j2.medida.idxmax().strftime("%Y-%m-%dT%H:%MZ"),
                    "max_1h_rrqpe_mm": round(float(j2.sat.max()), 1),
                    "hora_max_rrqpe": j2.sat.idxmax().strftime("%Y-%m-%dT%H:%MZ"),
                    "r_pearson": round(float(j2.medida.corr(j2.sat)), 2) if j2.medida.std() > 0 and j2.sat.std() > 0 else None,
                })
        if filas:
            out[clave] = {"nombre": nombre, "pixel": [int(i), int(j)], "filas": filas}
    return out


def figura_evento(nombre, zid, niv, sats, glm_zona, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    gal = dt.timezone(dt.timedelta(hours=-6))
    fig, ax = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
    ax[0].plot(niv.index, niv["R1h"], color="#1d4ed8", label="R1h medida (máx. estaciones de la zona)")
    ax[0].plot(niv.index, niv["R3h"], color="#60a5fa", label="R3h medida")
    for u, c in ((15, "#d97706"), (30, "#dc2626"), (45, "#7f1d1d")):
        ax[0].axhline(u, color=c, lw=0.7, ls="--")
    ax[0].set_ylabel("mm"); ax[0].legend(fontsize=8, loc="upper left")
    for an, c in (("zona", "#111827"), ("25km", "#6b7280"), ("50km", "#d1d5db")):
        d = sats[f"{zid}|{an}"]
        ax[1].plot(d.index, d["rrqpe_max"], color=c, label=f"RRQPE máx. ({an})")
        ax[2].plot(d.index, d["tb_min_k"], color=c, label=f"Tb mín. banda 13 ({an})")
        ax[3].plot(d.index, d["rayos_30min"], color=c, label=f"destellos GLM en 30 min ({an})")
    ax[1].set_ylabel("mm/h"); ax[2].set_ylabel("K"); ax[2].invert_yaxis(); ax[3].set_ylabel("destellos")
    ax[2].axhline(221, color="#7c3aed", lw=0.7, ls="--"); ax[2].axhline(235, color="#a78bfa", lw=0.7, ls="--")
    for a in ax:
        a.legend(fontsize=7, loc="upper left")
        a.grid(alpha=0.3)
    t_medio = niv.index[niv["nivel"].isin(ORDEN[:3])]
    if len(t_medio):
        for a in ax:
            a.axvline(t_medio[0], color="#d97706", lw=1)
    ax[3].xaxis.set_major_formatter(mdates.DateFormatter("%d %H:%M", tz=gal))
    ax[3].set_xlabel("hora de Galápagos (UTC−6)")
    fig.suptitle(f"Evento {nombre} · {zid} · GOES-19 (estimación satelital) frente a lluvia medida", fontsize=11)
    fig.tight_layout()
    fig.savefig(ruta, dpi=110)
    plt.close(fig)


def figura_mapa(c13, rr, glm, t, zonas, ruta, titulo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t13, a13, la, lo = c13
    trr, arr, _, _ = rr
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.8))
    k = min(range(len(t13)), key=lambda i: abs(t13[i] - t))
    im = ax[0].pcolormesh(lo, la, a13[k], cmap="turbo_r", vmin=190, vmax=300, shading="auto")
    fig.colorbar(im, ax=ax[0], label="Tb banda 13 (K)")
    k2 = min(range(len(trr)), key=lambda i: abs(trr[i] - t))
    im2 = ax[1].pcolormesh(lo, la, np.where(arr[k2] > 0.2, arr[k2], np.nan), cmap="viridis", vmin=0, vmax=40, shading="auto")
    fig.colorbar(im2, ax=ax[1], label="RRQPE (mm/h)")
    g = glm[(glm.ts >= pd.Timestamp(t) - pd.Timedelta(minutes=30)) & (glm.ts < pd.Timestamp(t) + pd.Timedelta(minutes=10))]
    for a in ax:
        a.scatter(g.lon, g.lat, s=8, c="#ef4444", marker="+", lw=0.8, label="destellos GLM (30 min)")
        for zid in ZONAS_SC:
            b = zonas[zid]["bbox"]
            a.plot([b[0], b[2], b[2], b[0], b[0]], [b[1], b[1], b[3], b[3], b[1]], color="w" if a is ax[0] else "k", lw=1)
        for n, plat, plon in ESTACIONES.values():
            a.plot(plon, plat, "k^", ms=4)
        a.set_xlim(lo.min(), lo.max()); a.set_ylim(la.min(), la.max()); a.set_aspect("equal")
    ax[1].legend(fontsize=7, loc="lower left")
    gal = (t - dt.timedelta(hours=6)).strftime("%d-%b %H:%M")
    fig.suptitle(f"{titulo} · {gal} hora de Galápagos (GOES-19; estimación satelital)", fontsize=10)
    fig.tight_layout()
    fig.savefig(ruta, dpi=100)
    plt.close(fig)


# --------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obs", help="CSV fuente,estacion,ts,valor (lluvia_mm, UTC) exportado de clima.db")
    ap.add_argument("--sin-figuras", action="store_true")
    a = ap.parse_args()

    obs = cargar_obs(a.obs)
    con = base_memoria(obs)
    zonas = zonas_geo()
    regla = {z["id"]: z for z in inundacion.REGLA["zonas"]}
    c13, rr = cargar_abi("c13"), cargar_abi("rrqpe")
    glm, cob = cargar_glm()
    print(f"ABI: {len(c13[0])} C13, {len(rr[0])} RRQPE · GLM: {len(glm)} destellos en {len(cob)} h")

    sats = series_satelite(c13, rr, glm, cob, {z: zonas[z] for z in ZONAS_SC})
    sats_sub = series_satelite(c13, rr, glm, cob, {z: zonas[z] for z in ZONAS_SC}, submuestra=True)
    FIG.mkdir(exist_ok=True)

    res = {"generado": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "advertencia": "Estimación satelital (GOES-19 ABI y GLM) evaluada contra pocas estaciones y tres eventos. "
                          "No es lluvia medida ni una alerta oficial.",
           "fuente_lluvia": "clima.db (solo lectura)" if a.obs else "datos/ierse-wsn/serie_5min.csv.gz",
           "senales": {s[0]: s[3] for s in SENALES}, "anillos_km": ANILLOS_KM, "eventos": {}, "muestra": {}}

    # ---- eventos
    for nombre, (i, f) in EVENTOS.items():
        ini, fin = (dt.datetime.fromisoformat(x).replace(tzinfo=UTC) for x in (i, f))
        ev = {"ventana_utc": [i, f], "zonas": {}}
        for zid in ZONAS_SC:
            niv = niveles(con, regla[zid], ini, fin)
            if niv["R1h"].isna().all():
                continue
            t_medio = niv.index[niv["nivel"].isin(ORDEN[:3])]
            t_alto = niv.index[niv["nivel"].isin(ORDEN[:2])]
            t_pico = niv["R1h"].idxmax()
            z = {"R1h_max": float(niv["R1h"].max()), "R3h_max": float(niv["R3h"].max()),
                 "R24h_max": float(niv["R24h"].max()),
                 "t_medio": t_medio[0].strftime("%Y-%m-%dT%H:%MZ") if len(t_medio) else None,
                 "t_alto": t_alto[0].strftime("%Y-%m-%dT%H:%MZ") if len(t_alto) else None,
                 "t_pico_R1h": t_pico.strftime("%Y-%m-%dT%H:%MZ"), "senales": {}}
            refs = {"medio": t_medio[0] if len(t_medio) else None, "alto": t_alto[0] if len(t_alto) else None,
                    "pico": t_pico}
            for an in ANILLOS_KM:
                d = sats[f"{zid}|{an}"]
                d = d[(d.index >= ini) & (d.index <= fin)]
                for sid, campo, u, _ in SENALES:
                    s = activa(d, campo, u)
                    r = {}
                    for ref, tr in refs.items():
                        if tr is None:
                            continue
                        ad, primera = adelanto(s, pd.Timestamp(tr))
                        r[f"adelanto_min_{ref}"] = ad
                        r[f"primera_12h_min_{ref}"] = primera
                    # ¿se activó en algún momento entre el nivel medio y 1 h después del pico?
                    a0 = refs["medio"] or t_pico - pd.Timedelta(hours=1)
                    r["activa_durante"] = bool(s[(s.index >= a0) & (s.index <= t_pico + pd.Timedelta(hours=1))].any())
                    z["senales"].setdefault(an, {})[sid] = r
                # valores máximos en la ventana
                z.setdefault("maximos", {})[an] = {
                    "rrqpe_max": round(float(d["rrqpe_max"].max()), 1) if "rrqpe_max" in d else None,
                    "tb_min_k": round(float(d["tb_min_k"].min()), 1) if "tb_min_k" in d else None,
                    "frio221_pct_max": round(float(d["frio221_pct"].max()), 1) if "frio221_pct" in d else None,
                    "rayos_30min_max": round(float(d["rayos_30min"].max()), 1),
                    "rayos_total": int(round(float(d["rayos_30min"].sum()) / 3)),
                }
            ev["zonas"][zid] = z
            if not a.sin_figuras:
                figura_evento(nombre, zid, niv, {k: v[(v.index >= ini) & (v.index <= fin)] for k, v in sats.items()},
                              None, FIG / f"evento_{nombre}_{zid}.png")
        res["eventos"][nombre] = ev
        if not a.sin_figuras:
            zc = ev["zonas"].get("la-cascada") or next(iter(ev["zonas"].values()), None)
            if zc and zc["t_medio"]:
                tm = dt.datetime.strptime(zc["t_medio"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)
                for h in (2, 0):
                    figura_mapa(c13, rr, glm, tm - dt.timedelta(hours=h), zonas, FIG / f"mapa_{nombre}_menos{h}h.png",
                                f"Evento {nombre}: {h} h antes del nivel medio" if h else f"Evento {nombre}: nivel medio")

    # ---- RRQPE frente a pluviómetros
    ventanas = dict(EVENTOS)
    for clase, dias in MUESTRA.items():
        for d in dias:
            ventanas[f"{clase}:{d}"] = (d + "T00:00", (pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%dT00:00"))
    res["rrqpe_vs_pluviometros"] = comparar_rrqpe(rr, obs, ventanas)

    # ---- falsas alarmas y detección con la misma cadencia de la muestra (ABI cada 20 min, GLM 1/3)
    tabla = {}
    for zid in ZONAS_SC:
        for an in ANILLOS_KM:
            d = sats_sub[f"{zid}|{an}"]
            for sid, campo, u, _ in SENALES:
                s = activa(d, campo, u)
                fila = {}
                for clase, dias in MUESTRA.items():
                    disparos, horas = [], []
                    for dia in dias:
                        a0 = pd.Timestamp(dia, tz="UTC")
                        sd = s[(s.index >= a0) & (s.index < a0 + pd.Timedelta(days=1))]
                        if len(sd) < 0.8 * 24 * 60 / SUB_ABI_MIN:  # día incompleto en la caché
                            continue
                        disparos.append(bool(sd.any()))
                        horas.append(int(sd.groupby(sd.index.floor("1h")).any().sum()))
                    fila[clase] = {"dias": len(disparos), "dias_con_disparo": int(sum(disparos)),
                                   "horas_con_disparo_media": round(float(np.mean(horas)), 2) if horas else None}
                det = []
                for nombre in EVENTOS:
                    z = res["eventos"][nombre]["zonas"].get(zid)
                    if not z:
                        continue
                    tr = z["t_medio"] or z["t_pico_R1h"]
                    tr = pd.Timestamp(tr.replace("Z", ""), tz="UTC")
                    ad, _ = adelanto(s, tr)
                    det.append(ad)
                fila["eventos_adelanto_min"] = det
                tabla.setdefault(f"{zid}|{an}", {})[sid] = fila
    # ---- reglas combinadas: adelanto en los eventos (cadencia completa) y días con disparo (muestra)
    comb = {}
    for zid in ZONAS_SC:
        for nombre in COMBOS:
            fila = {"eventos": {}, "muestra": {}}
            s_full = combo(sats, zid, nombre)
            s_sub = combo(sats_sub, zid, nombre)
            for ev in EVENTOS:
                z = res["eventos"][ev]["zonas"].get(zid)
                if not z:
                    continue
                r = {}
                for ref in ("t_medio", "t_alto", "t_pico_R1h"):
                    if z[ref]:
                        tr = pd.Timestamp(z[ref].replace("Z", ""), tz="UTC")
                        r[ref] = {"completa": adelanto(s_full, tr)[0], "muestra": adelanto(s_sub, tr)[0]}
                fila["eventos"][ev] = r
            for clase, dias in MUESTRA.items():
                n, k = 0, 0
                for dia in dias:
                    a0 = pd.Timestamp(dia, tz="UTC")
                    sd = s_sub[(s_sub.index >= a0) & (s_sub.index < a0 + pd.Timedelta(days=1))]
                    if len(sd) < 0.8 * 24 * 60 / SUB_ABI_MIN:
                        continue
                    n += 1
                    k += bool(sd.any())
                fila["muestra"][clase] = [k, n]
            comb.setdefault(zid, {})[nombre] = fila
    res["reglas_combinadas"] = {"definicion": {k: v if v != "y" else "frio221_pct ≥ 10 Y rrqpe_max ≥ 10 (25 km)"
                                               for k, v in COMBOS.items()}, "resultados": comb}

    res["muestra"] = {"dias": MUESTRA, "cadencia": "ABI cada 30 min; GLM un archivo de 20 s cada 2 min (conteos ×6)",
                      "tabla": tabla}

    (AQUI / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print("escrito satelite/resumen.json")


if __name__ == "__main__":
    main()
