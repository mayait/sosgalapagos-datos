#!/usr/bin/env python3
"""Lluvia MEDIDA del evento del 30/31-oct-2026 en Santa Cruz (red IERSE-WSN) y su
comparación con los modelos (Open-Meteo, script 15) y con la climatología de la FCD.

Solo LEE los datos de ../clima/ (no ejecuta sus scripts):
  ../clima/datos/ierse-wsn/serie_5min.csv.gz   (30 y 31-oct, consolidados)
  ../clima/datos/ierse-wsn/crudos/*/*.csv.gz   (histórico desde abril, para verificar Cerro Crocker)
y los registros del 1 y 2-nov bajados de la API pública el 2-nov ~13:10 (hora de Galápagos)
en estudios/santa-cruz/datos/lluvias/crudo/ierse_1_2nov/.

Hora: local de Galápagos (UTC−6). Cada registro es la lluvia desde el registro anterior
(balancín de 0,2 mm). Los tramos sin registros NO se midieron (no se acumulan).

Uso, desde geodatos/:  .venv/bin/python -I scripts/16_lluvias_ierse_evento.py
"""
import glob
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

GEO = Path(__file__).resolve().parent.parent
CLIMA = GEO.parent / "clima" / "datos" / "ierse-wsn"
OUT = GEO / "estudios" / "santa-cruz" / "datos" / "lluvias"
FIG = GEO / "estudios" / "santa-cruz" / "figuras"
EXTRA = OUT / "crudo" / "ierse_1_2nov"

EST = {  # id: (nombre, lat, lon, cota aprox. DSM GLO-30)
    "n_glps05": ("Los Guayabillos", -0.6991, -90.3420, 178),
    "n_glps09": ("Santa Rosa", -0.6545, -90.4035, 416),
    "n_glps01": ("Cerro Crocker", -0.6424, -90.3260, 861),
    "n_glps06": ("Militar (Baltra)", -0.4900, -90.2808, 14),
}
OM_PUNTO = {"n_glps05": "los_guayabillos", "n_glps09": "santa_rosa_ierse",
            "n_glps01": "cerro_crocker", "n_glps06": "militar_baltra"}
CORTE = pd.Timedelta(minutes=12)


def leer_crudos(desde, hasta):
    """Lluvia (RAIN) de los crudos de ../clima entre dos fechas (incluidas)."""
    fs = []
    for d in pd.date_range(desde, hasta):
        f = CLIMA / "crudos" / f"{d:%Y-%m}" / f"{d:%Y-%m-%d}.csv.gz"
        if f.exists():
            fs.append(f)
    r = pd.concat([pd.read_csv(f) for f in fs])
    r = r[r.variable == "RAIN"]
    return pd.DataFrame({"estacion_id": r.estacion_id,
                         "fecha_hora_local": pd.to_datetime(r.fecha_hora_local.str[:19]),
                         "lluvia_mm": r.valor.astype(float)})


def serie_evento():
    s = leer_crudos("2026-10-29", "2026-11-02")
    extra = []  # respaldo: registros del 1 y 2-nov bajados de la API el 2-nov ~13:10
    for f in sorted(EXTRA.glob("rain_*.json")):
        nodo = f.stem.split("_", 2)[2]
        for p in json.loads(f.read_text()):
            extra.append((nodo, pd.Timestamp(p["timestamp"][:19]), float(p["sensor_value"])))
    e = pd.DataFrame(extra, columns=["estacion_id", "fecha_hora_local", "lluvia_mm"])
    s = pd.concat([s, e]).drop_duplicates(["estacion_id", "fecha_hora_local"]).sort_values(
        ["estacion_id", "fecha_hora_local"])
    s = s[s.fecha_hora_local >= "2026-10-30"]
    s["estacion"] = s.estacion_id.map(lambda k: EST[k][0])
    return s.reset_index(drop=True)


def diaria_periodo():
    """Lluvia diaria medida del 15-oct al 2-nov y la de ECMWF 9 km en la celda de cada estación."""
    r = leer_crudos("2026-10-15", "2026-11-02")
    r["fecha"] = r.fecha_hora_local.dt.strftime("%Y-%m-%d")
    g = r.groupby(["fecha", "estacion_id"]).lluvia_mm.agg(["sum", "count"]).reset_index()
    om = pd.read_csv(OUT / "modelos_diaria.csv")
    filas = []
    for _, x in g.iterrows():
        e = om[(om.punto == OM_PUNTO[x.estacion_id]) & (om.fecha == x.fecha) & (om.modelo == "ecmwf_ifs")]
        filas.append({"fecha": x.fecha, "estacion": EST[x.estacion_id][0], "medido_mm": round(x["sum"], 1),
                      "registros": int(x["count"]), "cobertura_pct": round(100 * x["count"] / 288),
                      "ecmwf9km_mm": e.mm.iloc[0] if len(e) else None})
    return pd.DataFrame(filas)


def cortes(s):
    filas = []
    for k, g in s.groupby("estacion_id"):
        t = g.fecha_hora_local.reset_index(drop=True)
        d = t.diff()
        for i in d[d > CORTE].index:
            filas.append((EST[k][0], t[i - 1], t[i], round((t[i] - t[i - 1]).total_seconds() / 3600, 2)))
    return pd.DataFrame(filas, columns=["estacion", "ultimo_registro", "siguiente_registro", "horas_sin_datos"])


def resumen(s, h):
    filas = []
    for k, g in s.groupby("estacion_id"):
        g = g.set_index("fecha_hora_local")
        hk = h[h.estacion_id == k].set_index("hora_inicio").lluvia_mm
        mov60 = g.lluvia_mm.rolling("60min").sum()
        mov180 = g.lluvia_mm.rolling("180min").sum()
        ev = g.loc["2026-10-30"]
        dia = {d: g.loc[d].lluvia_mm.sum() if d in g.index.strftime("%Y-%m-%d") else None
               for d in ["2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02"]}
        cnt = {d: (g.index.strftime("%Y-%m-%d") == d).sum() for d in ["2026-10-30", "2026-10-31", "2026-11-01"]}
        hk30 = hk.loc["2026-10-30"]
        filas.append({
            "estacion": EST[k][0], "estacion_id": k, "lat": EST[k][1], "lon": EST[k][2], "cota_m_aprox": EST[k][3],
            "lluvia_30oct_mm": round(dia["2026-10-30"], 1),
            "lluvia_31oct_mm": round(dia["2026-10-31"], 1),
            "lluvia_1nov_mm": round(dia["2026-11-01"], 1),
            "lluvia_2nov_hasta_13h_mm": round(dia["2026-11-02"], 1),
            "lluvia_30oct_14_22h_mm": round(ev.between_time("14:00", "21:59").lluvia_mm.sum(), 1),
            "max_5min_mm": round(ev.lluvia_mm.max(), 1),
            "max_1h_reloj_mm": round(hk30.max(), 1),
            "hora_max_1h_reloj": hk30.idxmax().strftime("%H:%M") + "-" + (hk30.idxmax() + pd.Timedelta(hours=1)).strftime("%H:%M"),
            "max_60min_movil_mm": round(mov60.loc["2026-10-30"].max(), 1),
            "max_3h_movil_mm": round(mov180.loc["2026-10-30"].max(), 1),
            "registros_30oct": cnt["2026-10-30"], "cobertura_30oct_pct": round(100 * cnt["2026-10-30"] / 288),
            "registros_31oct": cnt["2026-10-31"], "cobertura_31oct_pct": round(100 * cnt["2026-10-31"] / 288),
            "cobertura_1nov_pct": round(100 * cnt["2026-11-01"] / 288),
            "ultimo_registro_30oct": ev.index.max().strftime("%H:%M"),
            "lluvia_ultimo_registro_mm": ev.lluvia_mm.iloc[-1],
        })
    return pd.DataFrame(filas)


def historico_crocker():
    fs = sorted(glob.glob(str(CLIMA / "crudos" / "*" / "*.csv.gz")))
    r = pd.concat([pd.read_csv(f) for f in fs])
    r = r[r.variable == "RAIN"].copy()
    r["t"] = pd.to_datetime(r.fecha_hora_local.str[:19])
    r["v"] = r.valor.astype(float)
    r = r[r.t < "2026-10-30"]
    cortes_t = pd.to_datetime(["2026-04-23", "2026-06-01", "2026-07-01", "2026-08-01", "2026-08-11",
                               "2026-09-01", "2026-10-30"])
    per = pd.cut(r.t, cortes_t, right=False)
    tot = r.groupby([per, "estacion_id"], observed=True).v.sum().unstack()
    h = r.set_index("t").groupby("estacion_id").v.resample("1h").sum().unstack(0)
    hm = h.groupby(pd.cut(h.index, cortes_t, right=False), observed=True).max()
    t = tot.round(1).add_prefix("total_").join(hm.round(1).add_prefix("max1h_"))
    t.index = [f"{i.left:%Y-%m-%d} a {i.right - pd.Timedelta(days=1):%Y-%m-%d}" for i in t.index]
    t.index.name = "periodo"
    t.columns = [c.replace("n_glps01", "crocker").replace("n_glps05", "guayabillos")
                 .replace("n_glps06", "militar").replace("n_glps09", "santa_rosa") for c in t.columns]
    dia = r.groupby([r.t.dt.date, "estacion_id"]).v.sum().unstack()
    ultimo = str(r.t.max().date())
    return t, dia, ultimo


def serie_completa():
    """Serie diaria completa (tablas consolidadas de ../clima): mayores días, humedad de Crocker y figura."""
    d = pd.read_csv(CLIMA / "diario.csv", parse_dates=["fecha"])
    h = pd.read_csv(CLIMA / "horario.csv", parse_dates=["fecha_hora_local"])
    d.to_csv(OUT / "serie_diaria_ierse.csv", index=False, date_format="%Y-%m-%d")
    top = (d.sort_values("lluvia_mm", ascending=False).groupby("estacion").head(5)
           .sort_values(["estacion", "lluvia_mm"], ascending=[True, False])
           [["estacion", "fecha", "lluvia_mm", "lluvia_max_1h_mm", "cobertura_pct"]])
    top.to_csv(OUT / "mayores_dias_por_estacion.csv", index=False, date_format="%Y-%m-%d")
    c = h[h.estacion == "Cerro Crocker"].copy()
    c["mes"] = c.fecha_hora_local.dt.strftime("%Y-%m")
    cm = c.groupby("mes").agg(lluvia_mm=("lluvia_mm", "sum"),
                              horas_con_lluvia=("lluvia_mm", lambda x: int((x > 0).sum())),
                              horas_con_dato=("registros", lambda x: int((x > 0).sum())),
                              hr_media_pct=("hr_pct_media", "mean"),
                              pct_horas_hr_100=("hr_pct_media", lambda x: (x >= 99.9).mean() * 100)).round(1)
    m = d.assign(mes=d.fecha.dt.strftime("%Y-%m")).pivot_table(index="mes", columns="estacion",
                                                               values="lluvia_mm", aggfunc="sum").round(1)
    cm = cm.join(m.add_prefix("lluvia_mes_"))
    cm.to_csv(OUT / "cerro_crocker_mensual.csv")
    ant = (d[(d.fecha >= "2026-10-25") & (d.fecha <= "2026-10-29")].groupby("estacion").lluvia_mm.sum().round(1))

    fig, axs = plt.subplots(4, 1, figsize=(11, 8.5), sharex=True)
    orden = ["Los Guayabillos", "Santa Rosa", "Cerro Crocker", "Militar"]
    colr = {"Los Guayabillos": "#c0392b", "Santa Rosa": "#2471a3", "Cerro Crocker": "#7d3c98", "Militar": "#d68910"}
    for ax, e in zip(axs, orden):
        g = d[d.estacion == e]
        ev = g.fecha.isin(pd.to_datetime(["2026-10-30"]))
        ax.bar(g.fecha[~ev], g.lluvia_mm[~ev], width=0.9, color=colr[e], alpha=0.75)
        ax.bar(g.fecha[ev], g.lluvia_mm[ev], width=0.9, color="k")
        baja = g[g.cobertura_pct < 75]
        ax.plot(baja.fecha, [-6] * len(baja), "|", color="0.5", ms=6)
        mx = g.lluvia_mm.max()
        ax.set_ylim(-10, max(60, mx * 1.18))
        ax.text(0.005, 0.86, e + (" (indicios de obstrucción desde el 11-ago)" if e == "Cerro Crocker" else ""),
                transform=ax.transAxes, fontsize=9, weight="bold")
        r30 = g[g.fecha == "2026-10-30"].lluvia_mm
        if len(r30):
            ax.annotate(f"30-oct: {r30.iloc[0]:.1f} mm", (pd.Timestamp("2026-10-30"), r30.iloc[0]),
                        xytext=(-95, -4), textcoords="offset points", fontsize=8.5, va="top")
        ax.set_ylabel("mm/día")
        ax.grid(axis="y", alpha=0.3)
        if e == "Cerro Crocker":
            ax.axvline(pd.Timestamp("2026-08-11"), color="0.4", ls=":", lw=1)
    axs[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    axs[0].set_title("Lluvia diaria medida por la red IERSE-WSN en Santa Cruz, 23-abr a 2-nov-2026 (en negro, el 30-oct)")
    fig.text(0.01, 0.005, "Fuente: red IERSE-WSN, Universidad del Azuay. Marcas grises bajo el eje: días con cobertura < 75 % (totales mínimos). "
             "El 30-oct es un mínimo: las estaciones se cortaron a las 21:22-21:25.", fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG / "f_lluvia_diaria_serie.png", dpi=160)
    print(top.to_string(index=False))
    print(cm.to_string())
    print("antecedente 25-29 oct:", ant.to_dict())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = serie_evento()
    s[["fecha_hora_local", "estacion_id", "estacion", "lluvia_mm"]].to_csv(
        OUT / "hietograma_5min.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S")
    h = (s.set_index("fecha_hora_local").groupby("estacion_id").lluvia_mm
          .resample("1h").agg(["sum", "count"]).reset_index())
    h.columns = ["estacion_id", "hora_inicio", "lluvia_mm", "registros"]
    h["estacion"] = h.estacion_id.map(lambda k: EST[k][0])
    h["completa"] = h.registros >= 11
    h["lluvia_mm"] = h.lluvia_mm.round(1)
    h[["hora_inicio", "estacion_id", "estacion", "lluvia_mm", "registros", "completa"]].to_csv(
        OUT / "hietograma_1h.csv", index=False, date_format="%Y-%m-%dT%H:%M")
    c = cortes(s)
    c.to_csv(OUT / "cortes_transmision.csv", index=False, date_format="%Y-%m-%dT%H:%M")
    r = resumen(s, h)
    r.to_csv(OUT / "resumen_estaciones.csv", index=False)

    # Comparación con modelos (script 15, Open-Meteo en hora de Galápagos)
    om = pd.read_csv(OUT / "modelos_horaria.csv", parse_dates=["fecha_hora_local_fin"])
    om["hora_inicio"] = om.fecha_hora_local_fin - pd.Timedelta(hours=1)
    comp = []
    for k, punto in OM_PUNTO.items():
        med = h[h.estacion_id == k].set_index("hora_inicio").lluvia_mm
        m_ev = med.loc["2026-10-30 14:00":"2026-10-30 21:00"].sum()
        for mod, g in om[om.punto == punto].groupby("modelo"):
            g = g.set_index("hora_inicio").mm
            comp.append({
                "estacion": EST[k][0], "modelo": mod,
                "medido_30oct_14_22h_mm": round(m_ev, 1),
                "modelo_30oct_14_22h_mm": round(g.loc["2026-10-30 14:00":"2026-10-30 21:00"].sum(), 1),
                "modelo_30oct_dia_mm": round(g.loc["2026-10-30"].sum(), 1),
                "modelo_31oct_dia_mm": round(g.loc["2026-10-31"].sum(), 1),
                "modelo_30_31oct_mm": round(g.loc["2026-10-30":"2026-10-31"].sum(), 1),
                "modelo_max1h_mm": round(g.loc["2026-10-30":"2026-10-31"].max(), 1),
                "modelo_hora_max1h": g.loc["2026-10-30":"2026-10-31"].idxmax().strftime("%d-%b %H:%M"),
                "medido_max1h_mm": round(med.loc["2026-10-30"].max(), 1),
                "medido_hora_max1h": med.loc["2026-10-30"].idxmax().strftime("%d-%b %H:%M"),
            })
    pd.DataFrame(comp).to_csv(OUT / "comparacion_modelos.csv", index=False)

    serie_completa()
    dp = diaria_periodo()
    dp.to_csv(OUT / "diaria_15oct_2nov.csv", index=False)
    print(dp.pivot(index="fecha", columns="estacion", values="medido_mm").to_string())
    t, dia, ultimo = historico_crocker()
    t.to_csv(OUT / "verificacion_cerro_crocker.csv")
    d5 = dia[(dia.n_glps09 >= 5) & dia.n_glps01.notna()].copy()
    d5["despues"] = pd.to_datetime(d5.index) >= pd.Timestamp("2026-08-11")
    v = {
        "historico_hasta": ultimo,
        "dias_SR_ge5_antes_11ago": int((~d5.despues).sum()),
        "dias_SR_ge5_antes_con_crocker_ge1": int(((~d5.despues) & (d5.n_glps01 >= 1)).sum()),
        "dias_SR_ge5_desde_11ago": int(d5.despues.sum()),
        "dias_SR_ge5_desde_con_crocker_ge1": int((d5.despues & (d5.n_glps01 >= 1)).sum()),
        "suma_crocker_antes": round(d5[~d5.despues].n_glps01.sum(), 1),
        "suma_SR_antes": round(d5[~d5.despues].n_glps09.sum(), 1),
        "suma_crocker_desde": round(d5[d5.despues].n_glps01.sum(), 1),
        "suma_SR_desde": round(d5[d5.despues].n_glps09.sum(), 1),
        "corr_diaria_guayabillos_santarosa": round(dia[["n_glps05", "n_glps09"]].corr().iloc[0, 1], 2),
    }
    (OUT / "verificacion_cerro_crocker.json").write_text(json.dumps(v, indent=1, ensure_ascii=False))

    # Figura: hietograma horario medido (30-oct 12:00 a 2-nov 13:00) frente a ECMWF 9 km
    fig, ax = plt.subplots(figsize=(11, 4.6))
    col = {"n_glps05": "#c0392b", "n_glps09": "#2471a3", "n_glps01": "#7d3c98", "n_glps06": "#d68910"}
    off = {"n_glps05": -0.3, "n_glps09": -0.1, "n_glps01": 0.1, "n_glps06": 0.3}
    w = pd.Timedelta(minutes=12)
    for k in ["n_glps05", "n_glps09", "n_glps01", "n_glps06"]:
        g = h[(h.estacion_id == k) & (h.hora_inicio >= "2026-10-30 12:00")]
        ax.bar(g.hora_inicio + pd.Timedelta(minutes=30) + off[k] * pd.Timedelta(hours=1), g.lluvia_mm,
               width=w, color=col[k], label=f"{EST[k][0]} (medido)")
    for punto, est_id, ls in [("los_guayabillos", "n_glps05", "-"), ("santa_rosa_ierse", "n_glps09", "--")]:
        g = om[(om.punto == punto) & (om.modelo == "ecmwf_ifs") & (om.hora_inicio >= "2026-10-30 12:00")]
        ax.step(g.hora_inicio + pd.Timedelta(hours=1), g.mm, where="pre", color="k", ls=ls, lw=1.1,
                label=f"ECMWF 9 km, celda de {EST[est_id][0]}")
    for _, cc in c.iterrows():
        if cc.estacion in ("Los Guayabillos", "Santa Rosa") and cc.horas_sin_datos > 3:
            ax.axvspan(cc.ultimo_registro, cc.siguiente_registro, color="0.85", zorder=0)
    ax.text(pd.Timestamp("2026-10-31 06:00"), 62, "Sin transmisión en\nLos Guayabillos y Santa Rosa\n(30-oct 21:25 a 31-oct 18:45)",
            ha="center", va="top", fontsize=8.5, color="0.3")
    ax.set_xlim(pd.Timestamp("2026-10-30 12:00"), pd.Timestamp("2026-11-02 13:00"))
    ax.set_ylabel("Lluvia (mm/h)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8, ncol=2, loc="upper right", frameon=False)
    ax.set_title("Lluvia horaria medida (red IERSE-WSN) y estimada por ECMWF 9 km, hora de Galápagos (UTC−6)")
    fig.text(0.01, 0.005, "Medido: red IERSE-WSN, Universidad del Azuay (pluviómetros de balancín, 0,2 mm). Las zonas grises son cortes de transmisión: "
             "esa lluvia no se midió.\nLa barra de 21:00-22:00 del 30-oct cubre solo ~25 min. Cerro Crocker: pluviómetro con indicios de obstrucción desde agosto. "
             "ECMWF: Open-Meteo, hasta el 2-nov 00:00.", fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "f_lluvia_medida.png", dpi=170)
    print(r.T.to_string())
    print(c.to_string())
    print(pd.DataFrame(comp).to_string())
    print(t.to_string())
    print(v)


if __name__ == "__main__":
    main()
