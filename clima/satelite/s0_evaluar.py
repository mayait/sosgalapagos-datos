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
import goes  # noqa: E402
import inundacion  # noqa: E402
from s0_extraer import EVENTOS as EVENTOS_EXTRAIDOS  # noqa: E402

# Eventos evaluados: los tres de referencia y el 1–2-nov (banda 13 y RRQPE cada 10 min; sin GLM;
# RRQPE solo hasta el 2-nov a las 16:50 UTC, cuando la NOAA dejó de producirlo).
EVENTOS = dict(EVENTOS_EXTRAIDOS)
EVENTOS["2026-11-01"] = ("2026-11-01T00:00", "2026-11-03T00:00")
PARALAJE = True  # --sin-paralaje para reproducir la primera versión

UTC = dt.timezone.utc
CACHE = AQUI / "cache"
FIG = AQUI / "figuras"
ZONAS_SC = ["la-cascada", "santa-cruz-alta"]  # las únicas zonas con estaciones en los eventos
ANILLOS_KM = {"zona": 0, "25km": 25, "50km": 50}
LLUVIA_EN_CURSO_MM = 5
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


# Reglas combinadas (O lógico): (anillo, campo, umbral). «v0» fue la primera de satelite/vigilancia.py; «v1» la sustituye.
COMBOS = {
    "v0": [("25km", "rayos_30min", 1), ("25km", "frio221_pct", 10), ("zona", "rrqpe_max", 10)],
    # v1: la propuesta tras S0 (satelite/vigilancia.py)
    "v1": [("25km", "rrqpe_max", 10), ("zona", "frio221_pct", 10)],  # sin rayos: nunca adelantaron nada
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

def series_satelite(c13, rr, glm, cob, zonas, submuestra=False, paso=None) -> dict[str, pd.DataFrame]:
    """Una tabla por zona y anillo, con paso de 10 min (20 min si submuestra)."""
    t13, a13, la, lo = c13
    trr, arr, _, _ = rr
    paso = paso or (SUB_ABI_MIN if submuestra else 10)
    i13 = {t: i for i, t in enumerate(t13) if t.minute % paso == 0}
    irr = {t: i for i, t in enumerate(trr) if t.minute % paso == 0}
    g = glm
    if submuestra:  # un archivo GLM de 20 s cada 2 min, como en los días de la muestra
        g = g[((g["t"] % (20 * SUB_GLM)) // 20) == 0]
        cob = {k: min(v, 1 / SUB_GLM) for k, v in cob.items()}
    tiempos = sorted(set(i13) | set(irr))
    todos13 = {t: i for i, t in enumerate(t13)}
    coords = {}

    def coords_de(t, producto):
        """lat/lon de cada píxel con el paralaje corregido (altura del tope desde la Tb de la banda 13)."""
        k = (t, producto)
        if k not in coords:
            if not PARALAJE:
                coords[k] = (la, lo)
            elif t in todos13:
                coords[k] = goes.corregir_paralaje(la, lo, goes.altura_tope_km(a13[todos13[t]]))
            else:  # RRQPE sin banda 13 a la misma hora: 12 km donde hay lluvia
                coords[k] = goes.corregir_paralaje(la, lo, np.where(arr[irr[t]] > 0, 12.0, 0.0))
            if producto == "rrqpe" and t in todos13:
                coords[k] = coords_de(t, "c13")
        return coords[k]

    salida = {}
    for zid in zonas:
        bb0 = zonas[zid]["bbox"]
        for anillo, km in ANILLOS_KM.items():
            bb = ampliar(bb0, km)
            gz = g[dentro(g["lat"].values, g["lon"].values, bb)]
            cuenta = gz.set_index("ts").resample("10min").size() if len(gz) else pd.Series(dtype=float)
            filas = []
            for t in tiempos:
                fila = {"ts": t}
                if t in i13:
                    m = dentro(*coords_de(t, "c13"), bb)
                    v = a13[i13[t]][m]
                    v = v[np.isfinite(v)]
                    if v.size:
                        fila.update(tb_min_k=float(v.min()), frio235_pct=100 * float((v < 235).mean()),
                                    frio221_pct=100 * float((v < 221).mean()))
                if t in irr:
                    m = dentro(*coords_de(t, "rrqpe"), bb)
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
        nv, R, ant, *_ = inundacion._evaluar(series, zona_regla, t, {})
        filas.append({"ts": t, "nivel": nv["nivel"] if nv else None, **(R or {})})
        t += dt.timedelta(minutes=paso_min)
    return pd.DataFrame(filas).set_index("ts")


def lluvia_horaria(obs: pd.DataFrame, clave: str) -> pd.Series:
    f, e = clave.split("/")
    s = obs[(obs.fuente == f) & (obs.estacion == e)].set_index("ts")["valor"]
    if s.empty:
        return s
    # el registro de las HH:MM cierra el intervalo previo: se asigna a la hora del inicio.
    # INAMHI: las filas con segundos :30 son el respaldo horario (la hora que termina en ts) y valen 12 registros.
    horaria = (s.index.second == 30) if f == "inamhi" else np.zeros(len(s), bool)
    s.index = s.index - pd.to_timedelta(np.where(horaria, 31, 1), unit="s")
    h = s.resample("1h").sum(min_count=1)
    n = pd.Series(np.where(horaria, 12, 1), index=s.index).resample("1h").sum()
    return h.where(n >= 0.8 * 12)


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
    lac, loc = goes.corregir_paralaje(la, lo, goes.altura_tope_km(a13[k])) if PARALAJE else (la, lo)
    im = ax[0].scatter(loc.ravel(), lac.ravel(), c=a13[k].ravel(), cmap="turbo_r", vmin=190, vmax=300, s=9, marker="s", lw=0)
    fig.colorbar(im, ax=ax[0], label="Tb banda 13 (K), paralaje corregido" if PARALAJE else "Tb banda 13 (K)")
    k2 = min(range(len(trr)), key=lambda i: abs(trr[i] - t))
    r2 = np.where(arr[k2] > 0.2, arr[k2], np.nan)
    im2 = ax[1].scatter(loc.ravel(), lac.ravel(), c=r2.ravel(), cmap="viridis", vmin=0, vmax=40, s=9, marker="s", lw=0)
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


OCT_INI, OCT_FIN = "2026-10-01T06:00", "2026-11-03T06:00"  # días de Galápagos (00:00 local = 06:00 UTC)
OCT_SENALES = {"frio221_10_25km": ("25km", "frio221_pct", 10), "frio221_10_zona": ("zona", "frio221_pct", 10),
               "frio235_25_25km": ("25km", "frio235_pct", 25), "tbmin_210_zona": ("zona", "tb_frio_k", 210)}


def contingencia_octubre(con, regla, c13, rr, glm, cob, zonas) -> dict:
    """Por día de Galápagos: ¿hubo topes fríos? ¿hubo lluvia intensa medida (R1h ≥ 15 o R3h ≥ 30 mm)?

    En la salida, «medio» quiere decir lluvia intensa según esas dos ventanas de la regla v0.2."""
    ini = dt.datetime.fromisoformat(OCT_INI).replace(tzinfo=UTC)
    fin = dt.datetime.fromisoformat(OCT_FIN).replace(tzinfo=UTC)
    vacio = pd.DataFrame({"x": [np.nan]})
    sats_h = series_satelite(c13, rr, glm.iloc[0:0] if len(glm) else glm, cob,
                             {z: zonas[z] for z in ZONAS_SC}, paso=60)
    out = {"periodo_utc": [OCT_INI, OCT_FIN], "cadencia": "banda 13 cada hora (imagen de las HH:00)",
           "senales": {k: f"{c} ≥ {u} ({an})" if c != "tb_frio_k" else f"Tb mín. ≤ {u} K ({an})"
                       for k, (an, c, u) in OCT_SENALES.items()}, "zonas": {}}
    for zid in ZONAS_SC:
        niv = niveles(con, regla[zid], ini, fin)
        # «intensa»: lluvia corta e intensa (umbrales de «medio» en 1 h y 3 h, sin el arrastre de 24 h)
        niv["medio"] = (niv["R1h"] >= 15) | (niv["R3h"] >= 30)
        niv["dia"] = (niv.index - pd.Timedelta(hours=6)).date
        dias = []
        for d, g in niv.groupby("dia"):
            fila = {"dia": str(d), "R1h_max": None if g["R1h"].isna().all() else float(g["R1h"].max()),
                    "cobertura_10min": round(float(g["nivel"].notna().mean()), 2),
                    "medio": bool(g["medio"].any()),
                    "t_medio": g.index[g["medio"]][0].strftime("%Y-%m-%dT%H:%MZ") if g["medio"].any() else None}
            a0 = pd.Timestamp(d).tz_localize("UTC") + pd.Timedelta(hours=6)
            for k, (an, campo, u) in OCT_SENALES.items():
                sd = sats_h[f"{zid}|{an}"]
                sd = sd[(sd.index >= a0) & (sd.index < a0 + pd.Timedelta(days=1))]
                fila[f"imagenes_{k}"] = int(len(sd))
                act = activa(sd, campo, u) if len(sd) else pd.Series(dtype=bool)
                fila[k] = bool(act.any()) if len(sd) >= 18 else None
                fila[f"horas_{k}"] = int(act.sum()) if len(sd) else 0
                if fila["t_medio"] and len(sd):
                    tm = pd.Timestamp(fila["t_medio"].replace("Z", ""), tz="UTC")
                    previas = act[(act.index <= tm) & (act.index >= tm - pd.Timedelta(hours=12))]
                    on = previas[previas].index
                    fila[f"primera_antes_min_{k}"] = (tm - on[0]).total_seconds() / 60 if len(on) else None
            dias.append(fila)
        tablas = {}
        for k in OCT_SENALES:
            v = [x for x in dias if x[k] is not None and x["cobertura_10min"] >= 0.5]
            a = sum(x[k] and x["medio"] for x in v)
            b = sum(x[k] and not x["medio"] for x in v)
            c = sum((not x[k]) and x["medio"] for x in v)
            dd = sum((not x[k]) and not x["medio"] for x in v)
            tablas[k] = {"dias": len(v), "aciertos": a, "falsas_alarmas": b, "fallos": c, "negativos": dd,
                         "POD": round(a / (a + c), 2) if a + c else None,
                         "FAR": round(b / (a + b), 2) if a + b else None,
                         "dias_con_senal_sin_medio_pct": round(100 * b / (b + dd), 1) if b + dd else None}
        out["zonas"][zid] = {"contingencia": tablas, "dias": dias}
    return out



# --------------------------------------------------------------------------- vigilancia continua (v1 + persistencia)

PERSISTENCIA_H = 3
LATENCIA_MIN = 20  # 10 min hasta el bucket + hasta 5 del timer + hasta 5 de la exportación (15–25 min)
PERIODOS = {"ene-abr": ("2026-01-01T00:00", "2026-05-01T00:00"), "oct-nov": ("2026-10-01T06:00", "2026-11-03T00:00")}
HUECO_EPISODIO_H = 6  # dos ratos de lluvia intensa separados por menos de 6 h son el mismo episodio


def estado_vigilancia(disparo: pd.Series, ini, fin) -> pd.Series:
    """Rejilla de 10 min: True si hubo un disparo de la v1 en las PERSISTENCIA_H horas previas."""
    rej = pd.date_range(ini, fin, freq="10min", inclusive="left")
    t = disparo[disparo].index
    t = t[(t >= ini - pd.Timedelta(hours=PERSISTENCIA_H)) & (t < fin)]
    if not len(t):
        return pd.Series(False, index=rej)
    pos = np.searchsorted(t.values, rej.values, side="right") - 1
    ultimo = np.where(pos >= 0, t.values[np.clip(pos, 0, None)], np.datetime64("NaT", "ns"))
    edad = (rej.values - ultimo).astype("timedelta64[m]").astype("float64")
    return pd.Series((pos >= 0) & (edad >= 0) & (edad <= PERSISTENCIA_H * 60), index=rej)


def episodios(b: pd.Series, hueco=pd.Timedelta(0)) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Tramos contiguos donde b es True (uniendo huecos ≤ hueco)."""
    on = b[b].index
    out = []
    for t in on:
        if out and t - out[-1][1] <= max(hueco, pd.Timedelta(minutes=10)):
            out[-1][1] = t
        else:
            out.append([t, t])
    return [(a, z + pd.Timedelta(minutes=10)) for a, z in out]


def fcd_diaria() -> pd.Series:
    """Lluvia diaria de la FCD en Puerto Ayora (día de la observación; privada, CC BY-NC-SA)."""
    p = CLIMA / "datos/fcd/climate_puerto-ayora.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(p, usecols=["observation_date", "precipitation"])
    return d.set_index(pd.to_datetime(d["observation_date"]).dt.date)["precipitation"]


def vigilancia_continua(con, regla, sats, rr_tiempos) -> dict:
    out = {"regla": "v1: RRQPE máx. ≥ 10 mm/h a 25 km O ≥ 10 % de la zona con Tb < 221 K; persistencia 3 h",
           "metodo": "banda 13 cada hora en todo el periodo y, alrededor de cada hora con Tb < 235 K a menos "
                     "de 50 km (±60 min), banda 13 y RRQPE cada 10 min (s0_cribado.py). Fuera de esas "
                     "ventanas se supone que la v1 no se dispara.", "periodos": {}}
    fcd = fcd_diaria()
    rr_t = pd.DatetimeIndex(rr_tiempos)
    for nombre, (i, f) in PERIODOS.items():
        ini, fin = pd.Timestamp(i, tz="UTC"), pd.Timestamp(f, tz="UTC")
        per = {}
        for zid in ZONAS_SC:
            disparo = combo(sats, zid, "v1")
            d13 = sats[f"{zid}|zona"]
            d13 = d13[(d13.index >= ini) & (d13.index < fin)]
            con13 = d13["tb_min_k"].notna() if "tb_min_k" in d13 else pd.Series(dtype=bool)
            pasos10 = int(con13.sum())
            sin_rr = int(sum(1 for t in con13[con13].index if t not in rr_t))
            v = estado_vigilancia(disparo, ini, fin)
            meses = {}
            for mes, g in v.groupby(v.index.strftime("%Y-%m")):
                meses[mes] = {"horas_vigilancia": round(g.sum() / 6, 1), "horas_total": round(len(g) / 6, 1),
                              "pct": round(100 * g.mean(), 2)}
            eps = []
            if nombre == "oct-nov":
                niv = niveles(con, regla[zid], ini.to_pydatetime(), fin.to_pydatetime())
            for a, z in episodios(v):
                e = {"inicio": a.strftime("%Y-%m-%dT%H:%MZ"), "fin": z.strftime("%Y-%m-%dT%H:%MZ"),
                     "horas": round((z - a).total_seconds() / 3600, 1)}
                if nombre == "oct-nov":
                    x = niv[(niv.index >= a) & (niv.index <= z + pd.Timedelta(hours=1))]
                    e["R1h_max_medido"] = None if x["R1h"].isna().all() else float(x["R1h"].max())
                    e["R3h_max_medido"] = None if x["R3h"].isna().all() else float(x["R3h"].max())
                else:
                    dias = sorted({(a - pd.Timedelta(hours=6)).date(), (z - pd.Timedelta(hours=6)).date()})
                    e["fcd_puerto_ayora_mm"] = {str(dd): (None if dd not in fcd.index or pd.isna(fcd[dd]) else float(fcd[dd]))
                                                for dd in dias}
                eps.append(e)
            per[zid] = {"pasos_banda13": pasos10, "pasos_sin_rrqpe": sin_rr, "meses": meses, "episodios": eps}
        out["periodos"][nombre] = per
    return out


def contingencia_episodios(con, regla, sats) -> dict:
    """Octubre–2-nov por episodios: lluvia intensa medida (R1h ≥ 15 o R3h ≥ 30, huecos < 6 h) frente a
    los episodios de vigilancia v1 (persistencia 3 h)."""
    ini, fin = pd.Timestamp(PERIODOS["oct-nov"][0], tz="UTC"), pd.Timestamp(PERIODOS["oct-nov"][1], tz="UTC")
    out = {}
    for zid in ZONAS_SC:
        niv = niveles(con, regla[zid], ini.to_pydatetime(), fin.to_pydatetime())
        intensa = ((niv["R1h"] >= 15) | (niv["R3h"] >= 30)).fillna(False)
        lluvia = episodios(intensa, pd.Timedelta(hours=HUECO_EPISODIO_H))
        v = estado_vigilancia(combo(sats, zid, "v1"), ini, fin)
        vig = episodios(v)
        filas_ll, usados = [], set()
        for a, z in lluvia:
            cruza = [k for k, (va, vz) in enumerate(vig) if va <= z and vz >= a - pd.Timedelta(hours=6)]
            usados.update(cruza)
            antes = [vig[k][0] for k in cruza if vig[k][0] <= a]
            filas_ll.append({"inicio": a.strftime("%Y-%m-%dT%H:%MZ"), "fin": z.strftime("%Y-%m-%dT%H:%MZ"),
                             "R1h_max": float(niv["R1h"][(niv.index >= a) & (niv.index <= z)].max()),
                             "detectado": bool(cruza),
                             "adelanto_min": (a - min(antes)).total_seconds() / 60 if antes else None,
                             "vigilancia_inicio": vig[min(cruza)][0].strftime("%Y-%m-%dT%H:%MZ") if cruza else None})
        falsas = []
        for k, (va, vz) in enumerate(vig):
            if k in usados:
                continue
            x = niv[(niv.index >= va) & (niv.index <= vz)]
            falsas.append({"inicio": va.strftime("%Y-%m-%dT%H:%MZ"), "fin": vz.strftime("%Y-%m-%dT%H:%MZ"),
                           "R1h_max_medido": None if x["R1h"].isna().all() else float(x["R1h"].max())})
        det = sum(f["detectado"] for f in filas_ll)
        out[zid] = {"episodios_lluvia": filas_ll, "episodios_vigilancia": len(vig), "falsas_alarmas": falsas,
                    "resumen": {"episodios_lluvia_intensa": len(filas_ll), "detectados": det,
                                "con_adelanto": sum(1 for f in filas_ll if f["adelanto_min"]),
                                "episodios_vigilancia_sin_lluvia_intensa": len(falsas)}}
    return out


def estaciones_dudosas(obs: pd.DataFrame) -> list[dict]:
    """Horas en que una estación de Santa Cruz marca 0 mientras otra mide ≥ 5 mm (pluviómetro obstruido)."""
    claves = ["ierse/n_glps05", "ierse/n_glps09", "ierse/n_glps01", "inamhi/M0191"]
    H = pd.DataFrame({c: lluvia_horaria(obs, c) for c in claves})
    H = H[H.index >= "2026-09-01"]
    out = []
    for c in claves[:3]:
        otras = H.drop(columns=[c]).max(axis=1)
        m = (H[c] == 0) & (otras >= 5)
        for d, g in m[m].groupby(m[m].index.date):
            out.append({"estacion": c, "nombre": ESTACIONES[c][0], "dia": str(d), "horas": int(len(g)),
                        "otra_max_mm": float(otras[g.index].max())})
    ult = {}
    for c in claves[:3]:
        x = H[c][H[c] > 0]
        ult[c] = x.index.max().strftime("%Y-%m-%dT%H:%MZ") if len(x) else None
    return {"horas_cero_con_lluvia_cerca": out, "ultima_hora_con_lluvia": ult}

# --------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obs", help="CSV fuente,estacion,ts,valor (lluvia_mm, UTC) exportado de clima.db")
    ap.add_argument("--sin-figuras", action="store_true")
    ap.add_argument("--sin-paralaje", action="store_true", help="reproduce la primera versión (sin corregir)")
    ap.add_argument("--salida", default=str(AQUI / "resumen.json"))
    a = ap.parse_args()
    global PARALAJE
    PARALAJE = not a.sin_paralaje

    obs = cargar_obs(a.obs)
    con = base_memoria(obs)
    zonas = zonas_geo()
    regla = {z["id"]: z for z in inundacion.REGLA["zonas"]}
    c13, rr = cargar_abi("c13"), cargar_abi("rrqpe")
    glm, cob = cargar_glm()
    print(f"ABI: {len(c13[0])} C13, {len(rr[0])} RRQPE · GLM: {len(glm)} destellos en {len(cob)} intervalos de 10 min")

    sats = series_satelite(c13, rr, glm, cob, {z: zonas[z] for z in ZONAS_SC})
    sats_sub = series_satelite(c13, rr, glm, cob, {z: zonas[z] for z in ZONAS_SC}, submuestra=True)
    FIG.mkdir(exist_ok=True)

    res = {"generado": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "advertencia": "Estimación satelital (GOES-19 ABI y GLM) evaluada contra pocas estaciones de Santa Cruz: "
                          "un solo evento convectivo con adelanto (30-oct-2026), reglas ajustadas a ese evento. "
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
            # sin mapa si el «medio» ya venía de antes de la ventana (1–2-nov): no hay un «antes» que mostrar
            if zc and zc["t_medio"] and not zc["t_medio"].startswith(i[:13]):
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
    r1h = {}  # R1h (máx. de las estaciones válidas de la zona) en eventos y días de la muestra
    for zid in ZONAS_SC:
        partes = []
        for i, f in EVENTOS.values():
            partes.append(niveles(con, regla[zid], dt.datetime.fromisoformat(i).replace(tzinfo=UTC),
                                  dt.datetime.fromisoformat(f).replace(tzinfo=UTC))["R1h"])
        for dias in MUESTRA.values():
            for dia in dias:
                a0 = dt.datetime.fromisoformat(dia).replace(tzinfo=UTC)
                partes.append(niveles(con, regla[zid], a0, a0 + dt.timedelta(days=1) - dt.timedelta(minutes=10))["R1h"])
        r1h[zid] = pd.concat(partes).sort_index()
        r1h[zid] = r1h[zid][~r1h[zid].index.duplicated()]
    variantes = [(n, False) for n in COMBOS] + [(n, True) for n in COMBOS]
    for zid in ZONAS_SC:
        for nombre, con_lluvia in variantes:
            fila = {"eventos": {}, "muestra": {}}
            s_full = combo(sats, zid, nombre)
            s_sub = combo(sats_sub, zid, nombre)
            if con_lluvia:  # además, lluvia en curso en el suelo: R1h ≥ 5 mm en alguna estación válida
                llueve = (r1h[zid] >= LLUVIA_EN_CURSO_MM)
                s_full = s_full & llueve.reindex(s_full.index, method="nearest", tolerance=pd.Timedelta("6min")).fillna(False).astype(bool)
                s_sub = s_sub & llueve.reindex(s_sub.index, method="nearest", tolerance=pd.Timedelta("6min")).fillna(False).astype(bool)
                nombre = nombre + "+lluvia5"
            for ev in EVENTOS:
                z = res["eventos"][ev]["zonas"].get(zid)
                if not z:
                    continue
                r = {}
                i_ev, f_ev = (pd.Timestamp(x, tz="UTC") for x in EVENTOS[ev])
                vig = estado_vigilancia(s_full, i_ev - pd.Timedelta(hours=12), f_ev)
                for ref in ("t_medio", "t_alto", "t_pico_R1h"):
                    if z[ref]:
                        tr = pd.Timestamp(z[ref].replace("Z", ""), tz="UTC")
                        # con persistencia de 3 h (la regla operativa): desde el inicio del episodio de
                        # vigilancia activo en tr; «efectivo» resta la latencia (~20 min: 10 de llegada
                        # al bucket, hasta 5 del timer y hasta 5 de la exportación en estado.json)
                        ep = [a for a, b in episodios(vig) if a <= tr < b]
                        con_p = (tr - ep[0]).total_seconds() / 60 if ep else None
                        r[ref] = {"completa": adelanto(s_full, tr)[0], "muestra": adelanto(s_sub, tr)[0],
                                  "persistencia_3h": con_p,
                                  "efectivo_menos_latencia": None if con_p is None else max(con_p - LATENCIA_MIN, 0)}
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

    # ---- octubre completo: topes fríos (banda 13 cada hora) frente a la regla de lluvia medida, día a día
    res["octubre"] = contingencia_octubre(con, regla, c13, rr, glm, cob, zonas)

    # ---- vigilancia v1 continua (con persistencia), episodios y estaciones dudosas
    res["vigilancia_continua"] = vigilancia_continua(con, regla, sats, rr[0])
    res["contingencia_episodios"] = contingencia_episodios(con, regla, sats)
    res["estaciones_dudosas"] = estaciones_dudosas(obs)
    res["paralaje"] = "corregido (altura del tope = (300 K − Tb) / 6,5 K/km, entre 0 y 16 km)" if PARALAJE else "sin corregir"

    Path(a.salida).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print(f"escrito {a.salida}")


if __name__ == "__main__":
    main()
