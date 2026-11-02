#!/usr/bin/env python3
"""Extrae y grafica la lluvia medida por las estaciones IERSE-WSN en una ventana de tiempo.

Pensado para cruzar las mediciones con un evento (p. ej. la inundación de La Cascada,
30/31-oct-2026) y con la estimación de los modelos (ECMWF) del informe de geodatos.

Uso, desde clima/:
    ../geodatos/.venv/bin/python -I scripts/03_evento.py \
        --inicio 2026-10-29T00:00 --fin 2026-11-02T00:00 --carpeta eventos/2026-10-30_inundacion

Salidas en la carpeta indicada:
  lluvia_5min.csv          lluvia de cada registro (≈5 min) por estación
  lluvia_horaria.csv       una columna por estación (mm/h) y, si existe, ECMWF 9 km (costa y parte alta)
  cortes_transmision.csv   intervalos sin registros de más de 15 min (la lluvia de esos tramos no se midió)
  resumen.json             totales, máximos en 5 min, 1 h, 3 h y 6 h, y cobertura por estación
  f_hietograma.png         barras horarias por estación, con los cortes sombreados
  f_acumulada.png          lluvia acumulada por estación frente a ECMWF
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "datos" / "ierse-wsn"
ECMWF = RAIZ.parent / "geodatos" / "estudios" / "la-cascada" / "datos" / "lluvia_evento_ecmwf_horaria.csv"
CORTE_MIN = pd.Timedelta(minutes=15)
COLORES = {"Los Guayabillos": "#c0392b", "Santa Rosa": "#2471a3", "Cerro Crocker": "#7d3c98", "Militar": "#d68910"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--carpeta", required=True)
    a = ap.parse_args()
    ini, fin = pd.Timestamp(a.inicio), pd.Timestamp(a.fin)
    out = RAIZ / a.carpeta
    out.mkdir(parents=True, exist_ok=True)

    est = json.loads((DIR / "estaciones.json").read_text())
    nombre = {k: v["node_name"] for k, v in est.items()}
    s = pd.read_csv(DIR / "serie_5min.csv.gz", parse_dates=["fecha_hora_local"])
    s = s[(s.fecha_hora_local >= ini) & (s.fecha_hora_local < fin)].copy()
    s["estacion"] = s["estacion_id"].map(nombre)
    s[["fecha_hora_local", "estacion_id", "estacion", "lluvia_mm"]].to_csv(
        out / "lluvia_5min.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S")

    # Lluvia horaria (columna por estación) + ECMWF
    h = (s.set_index("fecha_hora_local").groupby("estacion")["lluvia_mm"]
          .resample("1h").sum(min_count=1).unstack(0))
    h = h.reindex(pd.date_range(ini, fin, freq="1h", inclusive="left"))
    h.index.name = "fecha_hora_local"
    ecm = None
    if ECMWF.exists():
        ecm = pd.read_csv(ECMWF, parse_dates=["fecha_hora_local"])
        # Las etiquetas de Open-Meteo están en UTC−5 (America/Guayaquil) y marcan el FIN de la hora
        # (ver DESFASE_A_GALAPAGOS_H en geodatos/scripts/12_cascada_analisis.py). Aquí las barras
        # son de inicio de hora en UTC−6: etiqueta − 1 h (zona) − 1 h (fin → inicio).
        ecm["fecha_hora_local"] = ecm["fecha_hora_local"] - pd.Timedelta(hours=2)
        ecm = ecm.set_index("fecha_hora_local")
        ecm = ecm[["costa_ecmwf_ifs_9km_mm", "alta_ecmwf_ifs_9km_mm"]].reindex(h.index)
        h = h.join(ecm)
    h.round(2).to_csv(out / "lluvia_horaria.csv", date_format="%Y-%m-%dT%H:%M")

    # Cortes de transmisión (incluye el inicio y el fin de la ventana)
    cortes = []
    for eid, g in s.groupby("estacion_id"):
        t = pd.concat([pd.Series([ini]), g["fecha_hora_local"].sort_values(), pd.Series([fin])]).reset_index(drop=True)
        dif = t.diff()
        for i in dif[dif > CORTE_MIN].index:
            cortes.append({"estacion_id": eid, "estacion": nombre[eid], "desde": t[i - 1], "hasta": t[i],
                           "horas": round((t[i] - t[i - 1]).total_seconds() / 3600, 2)})
    for eid in set(est) - set(s["estacion_id"]):
        cortes.append({"estacion_id": eid, "estacion": nombre[eid], "desde": ini, "hasta": fin,
                       "horas": round((fin - ini).total_seconds() / 3600, 2)})
    cortes = pd.DataFrame(cortes)
    cortes.to_csv(out / "cortes_transmision.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S")

    # Resumen
    res = {"ventana": [ini.isoformat(), fin.isoformat()], "hora": "local de Galápagos (UTC−6), según la fuente",
           "estaciones": {}}
    horas = (fin - ini).total_seconds() / 3600
    for est_n, g in s.groupby("estacion"):
        r = g.set_index("fecha_hora_local")["lluvia_mm"]
        hh = r.resample("1h").sum()
        sin = cortes[cortes.estacion == est_n]["horas"].sum() if len(cortes) else 0
        res["estaciones"][est_n] = {
            "lluvia_total_mm": round(float(r.sum()), 1),
            "max_5min_mm": round(float(r.max()), 1),
            "max_1h_mm": round(float(hh.max()), 1),
            "hora_max_1h": hh.idxmax().isoformat(),
            "max_3h_mm": round(float(hh.rolling(3).sum().max()), 1),
            "max_6h_mm": round(float(hh.rolling(6).sum().max()), 1),
            "horas_sin_transmision": round(float(sin), 1),
            "cobertura_pct": round(100 * (1 - sin / horas)),
            "altitud_m_dem": None,
        }
    geo = DIR / "estaciones.geojson"
    if geo.exists():
        for f in json.loads(geo.read_text())["features"]:
            p = f["properties"]
            if p["nombre"] in res["estaciones"]:
                res["estaciones"][p["nombre"]]["altitud_m_dem"] = p["altitud_m_dem"]
    if ecm is not None:
        res["ecmwf_ifs_9km_mm"] = {"costa": round(float(ecm.iloc[:, 0].sum()), 1),
                                    "parte_alta": round(float(ecm.iloc[:, 1].sum()), 1),
                                    "nota": "solo cubre las horas con datos en el informe de La Cascada"}
    (out / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")

    # Figuras
    orden = sorted(res["estaciones"], key=lambda e: -(res["estaciones"][e]["altitud_m_dem"] or 0))
    fig, axs = plt.subplots(len(orden), 1, figsize=(11, 2.1 * len(orden)), sharex=True, sharey=True)
    axs = axs if len(orden) > 1 else [axs]
    for ax, e in zip(axs, orden):
        ax.bar(h.index, h[e], width=1 / 24, align="edge", color=COLORES.get(e, "#555"), label=f"{e} (medida)")
        if ecm is not None:
            col = "alta_ecmwf_ifs_9km_mm" if (res["estaciones"][e]["altitud_m_dem"] or 0) > 100 else "costa_ecmwf_ifs_9km_mm"
            ax.step(h.index, h[col], where="post", color="k", lw=1, ls="--",
                    label="ECMWF 9 km " + ("parte alta" if "alta" in col else "costa"))
        for _, c in cortes[cortes.estacion == e].iterrows():
            ax.axvspan(c["desde"], c["hasta"], color="#bbb", alpha=0.45, lw=0)
        alt = res["estaciones"][e]["altitud_m_dem"]
        ax.set_title(f"{e} · {alt} m · total medido {res['estaciones'][e]['lluvia_total_mm']} mm",
                     loc="left", fontsize=9)
        ax.set_ylabel("mm/h")
        ax.legend(fontsize=7, loc="upper right", frameon=False)
        ax.grid(axis="y", alpha=0.3)
    axs[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d-%b\n%H:%M"))
    fig.suptitle("Lluvia horaria medida (IERSE-WSN) · gris: sin transmisión · hora de Galápagos", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "f_hietograma.png", dpi=150)

    fig, ax = plt.subplots(figsize=(11, 4))
    for e in orden:
        acc = h[e].fillna(0).cumsum()
        ax.plot(h.index, acc, color=COLORES.get(e, "#555"), lw=2, label=e)
    if ecm is not None:
        ax.plot(h.index, h["alta_ecmwf_ifs_9km_mm"].fillna(0).cumsum(), "k--", lw=1, label="ECMWF 9 km parte alta")
        ax.plot(h.index, h["costa_ecmwf_ifs_9km_mm"].fillna(0).cumsum(), "k:", lw=1, label="ECMWF 9 km costa")
    ax.set_ylabel("mm acumulados")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b\n%H:%M"))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("Lluvia acumulada (las curvas se aplanan también durante los cortes de transmisión)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(out / "f_acumulada.png", dpi=150)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(cortes.to_string())


if __name__ == "__main__":
    main()
