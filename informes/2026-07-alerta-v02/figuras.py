"""Figuras y prueba retrospectiva del Informe técnico 2026-07 (regla v0.2 de la alerta por lluvia).

Uso (desde la raíz del repositorio):
    geodatos/.venv/bin/python -I informes/2026-07-alerta-v02/figuras.py

Reproduce la regla v0.2 con el MISMO código que usa el recolector (clima/recolector/inundacion.py y
umbrales_inundacion.json), sobre una base SQLite en memoria construida con la lluvia archivada en el
repositorio (solo lectura):
  - IERSE-WSN, serie de 5 min (clima/datos/ierse-wsn/serie_5min.csv.gz, hora UTC−6);
  - INAMHI M0191 Puerto Ayora, historial horario (clima/datos/inamhi/historial/, hora UTC−5,
    etiqueta = inicio de la hora; se guarda a HH:30:30 como hace fuentes_extra.inamhi_historial).
La estación particular WeatherLink de Puerto Ayora no tiene serie archivada en el repositorio y no entra.

Salidas (en figuras/):
  retro_30oct.png       índice R/U_alto y nivel mostrado el 30-oct, con hitos del modelo hidrológico
  umbrales_eventos.png  umbrales por nivel y ventana, con los máximos ponderados de los días de referencia
  retrospectiva.json    horas de cada nivel, días con «medio» o más, sensibilidad al ajuste en seco de la v0.1
                        y cifras citadas en el informe
"""
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "clima/recolector"))
import inundacion  # noqa: E402

OUT = AQUI / "figuras"
OUT.mkdir(exist_ok=True)
UTC = dt.timezone.utc
G6 = dt.timezone(dt.timedelta(hours=-6))   # Galápagos
C5 = dt.timezone(dt.timedelta(hours=-5))   # continental (INAMHI)
NOMBRES = {"n_glps01": "Cerro Crocker", "n_glps05": "Los Guayabillos", "n_glps06": "Militar", "n_glps09": "Santa Rosa"}
REGLA = inundacion.REGLA
ZONAS = {z["id"]: z for z in REGLA["zonas"]}
COLOR = {n["nivel"]: n["color"] for n in REGLA["niveles"]}
COLOR[None] = "#9ca3af"
ORDEN = ["bajo", "medio", "alto", "muy alto"]


def base(con_inamhi=True):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE obs (fuente, estacion, variable, ts, valor)")
    con.execute("CREATE TABLE estaciones (fuente, estacion, nombre)")
    con.execute("CREATE TABLE corridas (fuente, ts, ok)")
    s = pd.read_csv(RAIZ / "clima/datos/ierse-wsn/serie_5min.csv.gz", parse_dates=["fecha_hora_local"])
    s = s.dropna(subset=["lluvia_mm"])
    ts = (s.fecha_hora_local.dt.tz_localize(G6).dt.tz_convert(UTC)).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    con.executemany("INSERT INTO obs VALUES ('ierse', ?, 'lluvia_mm', ?, ?)",
                    zip(s.estacion_id, ts, s.lluvia_mm.astype(float)))
    con.executemany("INSERT INTO estaciones VALUES ('ierse', ?, ?)", NOMBRES.items())
    if con_inamhi:
        d = json.load(open(RAIZ / "clima/datos/inamhi/historial/historial_estaciones_pais_20261102.json"))
        filas = []
        for f in d["filas"]:
            if f.get("codigo") == "M0191" and f.get("n_lluvia") and f.get("lluvia_mm") is not None:
                t = dt.datetime.fromisoformat(f["hora"]).replace(tzinfo=C5) + dt.timedelta(minutes=30, seconds=30)
                filas.append((t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), float(f["lluvia_mm"])))
        con.executemany("INSERT INTO obs VALUES ('inamhi', 'M0191', 'lluvia_mm', ?, ?)", filas)
        con.execute("INSERT INTO estaciones VALUES ('inamhi', 'M0191', 'INAMHI Puerto Ayora')")
    con.execute("CREATE INDEX i ON obs (fuente, estacion, ts)")
    return con


def series(con, desde):
    claves = {c for z in REGLA["zonas"] for c, _ in z["estaciones"]}
    out = {}
    for c in claves:
        f, s = inundacion._serie(con, c, desde)
        if s:
            out[c] = (f, s)
    return out


def indice(R, factor):
    """max_v R_v / (factor × U_alto,v): 0,5 = medio, 1 = alto, 1,5 = muy alto (los tres niveles son proporcionales)."""
    alto = next(n for n in REGLA["niveles"] if n["nivel"] == "alto")["si_alguno"]
    return max(R[k] / (alto[k] * factor) for k in alto) if R else None


def a6(t):
    return t.astimezone(G6).strftime("%d-%b %H:%M")


# ------------------------------------------------------------------ 30-oct: evaluación cada 5 min
def evento_30oct(con, etiqueta):
    filas = []
    t = dt.datetime(2026, 10, 30, 12, 0, tzinfo=G6).astimezone(UTC)
    fin = dt.datetime(2026, 10, 31, 8, 0, tzinfo=G6).astimezone(UTC)
    while t <= fin:
        r = inundacion.calcular(con, ahora=t, recoleccion_ok=lambda f, x: True)
        for z in r["zonas"]:
            if z["id"] not in ("la-cascada", "santa-cruz-alta"):
                continue
            filas.append(dict(variante=etiqueta, zona=z["id"], t_utc6=t.astimezone(G6).replace(tzinfo=None),
                              nivel=z["nivel"], instantaneo=z["nivel_instantaneo"], silencio=z["silencio"],
                              R1h=z["R"].get("R1h"), R3h=z["R"].get("R3h"), R24h=z["R"].get("R24h"),
                              P5d=z["P5d"], factor=z["factor"],
                              indice=indice(z["R"], z["factor"] or 1.0) if z["R"] else None))
        t += dt.timedelta(minutes=5)
    return pd.DataFrame(filas)


def primeras(df):
    out = {}
    for (v, zid), g in df.groupby(["variante", "zona"]):
        d = {}
        for nv in ["medio", "alto", "muy alto"]:
            x = g[g.nivel.isin(ORDEN[ORDEN.index(nv):])]
            d[nv] = x.t_utc6.min().strftime("%H:%M") if len(x) else None
        sil = g[g.silencio]
        d["silencio_desde"] = sil.t_utc6.min().strftime("%d-%b %H:%M") if len(sil) else None
        sd = g[g.nivel == "sin datos"]
        d["sin_datos_desde"] = sd.t_utc6.min().strftime("%d-%b %H:%M") if len(sd) else None
        i = g.indice.idxmax() if g.indice.notna().any() else None
        if i is not None:
            d["R_max"] = {k: float(g[k].max()) for k in ("R1h", "R3h", "R24h")}
            d["indice_max"] = round(float(g.indice.max()), 2)
        p = g.dropna(subset=["P5d"])
        d["P5d_inicio"] = float(p.P5d.iloc[0]) if len(p) else None
        d["humedad_factor_inicio"] = float(p.factor.iloc[0]) if len(p) else None
        out[f"{v}/{zid}"] = d
    return out


# ------------------------------------------------------------------ registro completo: instantáneo horario
def registro(con):
    ini = dt.datetime(2026, 4, 23, tzinfo=UTC)
    ser = series(con, ini - dt.timedelta(days=6))
    nombres = {f"{f}/{e}": n for f, e, n in con.execute("SELECT fuente, estacion, nombre FROM estaciones")}
    fin = dt.datetime(2026, 11, 2, 18, tzinfo=UTC)
    filas = []
    t = ini
    while t <= fin:
        for zid in ("la-cascada", "santa-cruz-alta"):
            nv, R, ant, _ = inundacion._evaluar(ser, ZONAS[zid], t, nombres)
            filas.append(dict(zona=zid, t_utc6=t.astimezone(G6).replace(tzinfo=None), nivel=nv["nivel"] if nv else "sin datos",
                              R1h=R.get("R1h"), R3h=R.get("R3h"), R24h=R.get("R24h"),
                              P5d=ant[0] if ant else None, humedad=ant[1] if ant else None))
        t += dt.timedelta(hours=1)
    df = pd.DataFrame(filas)
    # nivel mostrado con persistencia de 8 h (sin la regla de silencio, que exige saber si la fuente respondía)
    pers = REGLA["persistencia_horas"]
    rango = {n: i for i, n in enumerate(ORDEN)}
    df["mostrado"] = "sin datos"
    for zid, g in df.groupby("zona", sort=False):
        niv = list(g.nivel)
        mostr = []
        for i in range(len(niv)):
            ventana = [y for y in niv[max(0, i - pers):i + 1] if y in rango]
            mostr.append(max(ventana, key=rango.get) if ventana else "sin datos")
        df.loc[g.index, "mostrado"] = mostr
    return df


def resumen_registro(df):
    out = {}
    for zid, g in df.groupby("zona"):
        g = g.copy()
        g["dia"] = g.t_utc6.dt.date
        horas = g.nivel.value_counts().to_dict()
        horas_m = g.mostrado.value_counts().to_dict()
        rango = {n: i for i, n in enumerate(ORDEN)}
        dmax = g[g.nivel.isin(ORDEN)].groupby("dia").nivel.agg(lambda s: max(s, key=rango.get))
        dias = {nv: [str(d) for d, x in dmax.items() if x == nv] for nv in ["medio", "alto", "muy alto"]}
        hum = g.dropna(subset=["humedad"]).groupby("dia").humedad.first().value_counts().to_dict()
        out[zid] = dict(horas_evaluadas=len(g), horas_instantaneo=horas, horas_mostrado=horas_m,
                        dias_por_nivel_max=dias, dias_validos=int(dmax.size),
                        dias_por_humedad=hum,
                        dias_ref={d: dmax.get(pd.Timestamp(d).date()) for d in ("2026-10-03", "2026-10-23", "2026-10-30")})
    return out


# ------------------------------------------------------------------ figuras
def fig_30oct(df):
    g = df[(df.zona == "la-cascada")]
    fig, (ax, axn) = plt.subplots(2, 1, figsize=(9.2, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[3.2, 1.1], hspace=0.08))
    for y, nv in [(0.5, "medio"), (1.0, "alto"), (1.5, "muy alto")]:
        ax.axhline(y, color=COLOR[nv], lw=1, ls="--")
        ax.text(pd.Timestamp("2026-10-31 07:55"), y + 0.03, f"umbral «{nv}»", color=COLOR[nv], ha="right", va="bottom", fontsize=8)
    alto = next(n for n in REGLA["niveles"] if n["nivel"] == "alto")["si_alguno"]
    estilos = {"A": "-", "B": ":"}
    for v, gg in g.groupby("variante"):
        for k, c in [("R1h", "#1d4ed8"), ("R3h", "#7c3aed"), ("R24h", "#0f766e")]:
            ax.plot(gg.t_utc6, gg[k] / (alto[k] * gg.factor.fillna(1.0)), color=c, ls=estilos[v[0]], lw=1.4 if v[0] == "A" else 1.6,
                    label=f"{k[1:]} ({'IERSE' if v[0] == 'A' else 'IERSE + INAMHI'})")
    ax.set_ylabel("R / umbral «alto»")
    ax.set_ylim(0, 2.95)
    ax.axvspan(pd.Timestamp("2026-10-30 21:25"), pd.Timestamp("2026-10-31 08:00"), color="0.9", zorder=0)
    ax.text(pd.Timestamp("2026-10-30 23:00"), 2.88, "IERSE sin transmisión desde 21:22–21:25", fontsize=8, color="0.3", va="top")
    hitos = [("2026-10-30 16:50", "2026-10-30 18:10", "vaso lleno\n(modelo)"), ("2026-10-30 21:40", "2026-10-30 22:50", "pico\n(modelo)")]
    for a, b, txt in hitos:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="#fca5a5", alpha=0.35, zorder=0)
        ax.text(pd.Timestamp(a) + (pd.Timestamp(b) - pd.Timestamp(a)) / 2, 2.3, txt, ha="center", fontsize=8, color="#7f1d1d")
    ax.legend(ncol=2, fontsize=7.5, loc="upper right", bbox_to_anchor=(1.0, 0.93), frameon=False)
    ax.set_xlim(pd.Timestamp("2026-10-30 12:00"), pd.Timestamp("2026-10-31 08:00"))
    ax.grid(alpha=0.25)
    for i, (v, gg) in enumerate(g.groupby("variante")):
        y = 1 - i
        t = list(gg.t_utc6)
        for j in range(len(t) - 1):
            axn.fill_between([t[j], t[j + 1]], y - 0.4, y + 0.4, color=COLOR.get(gg.nivel.iloc[j] if gg.nivel.iloc[j] != "sin datos" else None, "#9ca3af"), lw=0)
        axn.text(t[0], y, " " + ("IERSE" if v[0] == "A" else "IERSE + INAMHI"), va="center", fontsize=8, color="white")
    axn.set_yticks([])
    axn.set_ylim(-0.6, 1.6)
    axn.set_ylabel("nivel\nmostrado", fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[n]) for n in ORDEN] + [plt.Rectangle((0, 0), 1, 1, color="#9ca3af")]
    axn.legend(handles, ORDEN + ["sin datos"], ncol=5, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.45), frameon=False)
    axn.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axn.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    axn.set_xlabel("30–31 de octubre de 2026, hora de Galápagos (UTC−6)")
    fig.savefig(OUT / "retro_30oct.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def maximos_dia(con, dias):
    """Máximo de R (cada 5 min) en cada día de referencia (00:00–24:00, UTC−6), por zona."""
    ser = series(con, dt.datetime(2026, 9, 20, tzinfo=UTC))
    nombres = {f"{f}/{e}": n for f, e, n in con.execute("SELECT fuente, estacion, nombre FROM estaciones")}
    filas = []
    for et, d in dias.items():
        t0 = dt.datetime.fromisoformat(d).replace(tzinfo=G6)
        for zid in ("la-cascada", "santa-cruz-alta"):
            m = {"R1h": 0.0, "R3h": 0.0, "R24h": 0.0}
            for i in range(1, 289):
                _, R, _, _ = inundacion._evaluar(ser, ZONAS[zid], (t0 + dt.timedelta(minutes=5 * i)).astimezone(UTC), nombres)
                for k in m:
                    m[k] = max(m[k], R.get(k) or 0.0)
            filas.append(dict(dia=et, zona=zid, **m))
    return pd.DataFrame(filas)


def fig_umbrales(mx):
    dias = ["3-oct", "23-oct", "30-oct"]
    fig, axs = plt.subplots(1, 3, figsize=(9.2, 3.3))
    for ax, (k, ventana, top) in zip(axs, [("R1h", "1 h", 80), ("R3h", "3 h", 160), ("R24h", "24 h", 260)]):
        lim = [0] + [n["si_alguno"][k] for n in REGLA["niveles"][::-1] if "si_alguno" in n] + [top]
        for i, nv in enumerate(ORDEN):
            ax.axhspan(lim[i], lim[i + 1], color=COLOR[nv], alpha=0.22, lw=0)
            ax.text(0.03, (lim[i] + lim[i + 1]) / 2, nv, transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=COLOR[nv])
            if 0 < i:
                ax.axhline(lim[i], color=COLOR[nv], lw=0.8)
                ax.axhline(lim[i] * REGLA["humedad_antecedente"]["humedo"]["factor"], color=COLOR[nv], lw=0.6, ls=":")
        for j, et in enumerate(dias):
            for dx, zid, c in [(-0.17, "la-cascada", "#1f2937"), (0.17, "santa-cruz-alta", "#6b7280")]:
                x = float(mx[(mx.dia == et) & (mx.zona == zid)][k].iloc[0])
                ax.bar(j + 1 + dx, x, width=0.32, color=c, label={"la-cascada": "La Cascada", "santa-cruz-alta": "Parte alta"}[zid] if j == 0 else None)
                ax.text(j + 1 + dx, x + top * 0.015, f"{x:.0f}", ha="center", fontsize=7)
        ax.set_xticks([1, 2, 3], dias)
        if k == "R1h":
            ax.legend(fontsize=7, loc="upper center", frameon=True, bbox_to_anchor=(0.62, 0.98))
        ax.set_xlim(0, 3.6)
        ax.set_ylim(0, top)
        ax.set_title(f"Ventana de {ventana}", fontsize=10)
        ax.set_ylabel("mm" if k == "R1h" else "")
    fig.tight_layout()
    fig.savefig(OUT / "umbrales_eventos.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    a = base(con_inamhi=False)
    b = base(con_inamhi=True)
    ev = pd.concat([evento_30oct(a, "A_ierse"), evento_30oct(b, "B_ierse_inamhi")])
    reg = registro(b)
    res = dict(nota="Generado por informes/2026-07-alerta-v02/figuras.py con clima/recolector/inundacion.py (regla "
                    + REGLA["version"] + "). Horas UTC−6. Variante A: solo IERSE; B: IERSE + INAMHI M0191 horario. "
                    "Sin la estación particular WeatherLink (no archivada).",
               evento_30oct=primeras(ev), registro=resumen_registro(reg))
    # cifras puntuales del 30-oct (variante B, La Cascada) a horas de referencia
    g = ev[(ev.variante == "B_ierse_inamhi") & (ev.zona == "la-cascada")].set_index("t_utc6")
    res["la_cascada_B_horas"] = {h: g.loc[pd.Timestamp(f"2026-10-{h}")][["nivel", "R1h", "R3h", "R24h"]].to_dict()
                                 for h in ("30 15:40", "30 18:55", "30 20:55", "30 21:20", "30 22:00", "31 01:00", "31 03:00", "31 06:00")}
    # sensibilidad: la misma regla con el ajuste en seco de la v0.1 (umbrales ×1,2 si P5d < 36 mm)
    seco = REGLA["humedad_antecedente"]["seco"]["factor"]
    REGLA["humedad_antecedente"]["seco"]["factor"] = 1.2
    res["sensibilidad_seco_x1_2"] = primeras(evento_30oct(b, "B_ierse_inamhi"))
    REGLA["humedad_antecedente"]["seco"]["factor"] = seco
    (OUT / "retrospectiva.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    fig_30oct(ev)
    mx = maximos_dia(b, {"3-oct": "2026-10-03", "23-oct": "2026-10-23", "30-oct": "2026-10-30"})
    res["maximos_dia_5min"] = mx.round(1).to_dict(orient="records")
    (OUT / "retrospectiva.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    fig_umbrales(mx)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
