#!/usr/bin/env python3
"""Figuras y tabla propias del informe 2026-03 (lluvia observada, climatología y nivel del mar).

Solo LEE archivos versionados del repositorio (no descarga nada ni modifica otras carpetas):
  clima/datos/fcd/climate_puerto-ayora.csv, climate_bellavista.csv   lluvia diaria FCD (CC BY-NC-SA)
  geodatos/datos/mareas/resumen_mareas.json                           anomalía mensual del nivel del mar

Escribe en esta carpeta:
  datos/gumbel_momentos.csv     Gumbel por momentos de los máximos anuales FCD (mismo criterio que
                                clima/recolector/estacionalidad.py: años con ≥ 80 % de días)
  figuras/gumbel_fcd.png        gráfico de probabilidad de Gumbel con la lluvia del 30-oct-2026
  figuras/anomalia_nivel_mar.png  anomalía mensual del nivel del mar en Puerto Ayora y Baltra

Uso, desde la raíz del repositorio:
  geodatos/.venv/bin/python -I informes/2026-03-lluvia-clima/figuras.py
"""
import csv
import datetime as dt
import json
import math
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
FCD = RAIZ / "clima" / "datos" / "fcd"
MAREAS = RAIZ / "geodatos" / "datos" / "mareas" / "resumen_mareas.json"
(AQUI / "datos").mkdir(exist_ok=True)
(AQUI / "figuras").mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
EULER = 0.5772
PERIODOS = (2, 5, 10, 25, 50, 100)
# Lluvia MEDIDA del 30-oct-2026 (mínimos por corte de transmisión), de geodatos/estudios/santa-cruz/datos/lluvias/
EVENTO = [("Santa Rosa (IERSE), 30-oct", 237.6), ("Los Guayabillos (IERSE), 30-oct", 178.8),
          ("Puerto Ayora (INAMHI M0191), 30-oct", 118.5)]


def maximos(nombre, excluir=()):
    dias = {}
    with open(FCD / nombre, newline="") as f:
        for r in csv.DictReader(f):
            try:
                v = float(r["precipitation"])
            except (TypeError, ValueError):
                continue
            if 0 <= v < 1000:
                dias[dt.date.fromisoformat(r["observation_date"])] = v
    anios = {}
    for d, v in dias.items():
        anios.setdefault(d.year, []).append(v)
    return {y: max(v) for y, v in anios.items() if len(v) >= 0.8 * 365 and y not in excluir}


def gumbel_momentos(xs):
    beta = statistics.stdev(xs) * math.sqrt(6) / math.pi
    mu = statistics.mean(xs) - EULER * beta
    return mu, beta


def nivel(mu, beta, T):
    return mu - beta * math.log(-math.log(1 - 1 / T))


def periodo(mu, beta, x):
    F = math.exp(-math.exp(-(x - mu) / beta))
    return 1 / (1 - F) if F < 1 else float("inf")


def main():
    series = {"Puerto Ayora (FCD)": maximos("climate_puerto-ayora.csv"),
              "Bellavista (FCD)": maximos("climate_bellavista.csv"),
              "Bellavista (FCD), sin 2008": maximos("climate_bellavista.csv", excluir=(2008,))}
    filas = []
    for nombre, m in series.items():
        xs = list(m.values())
        mu, beta = gumbel_momentos(xs)
        fila = {"serie": nombre, "anios": len(xs), "desde": min(m), "hasta": max(m),
                "media_mm": round(statistics.mean(xs), 1), "desv_mm": round(statistics.stdev(xs), 1),
                "mu_mm": round(mu, 1), "beta_mm": round(beta, 1), "max_mm": round(max(xs), 1),
                "anio_max": max(m, key=m.get)}
        for T in PERIODOS:
            fila[f"P{T}_mm"] = round(nivel(mu, beta, T))
        for _, x in EVENTO:
            fila[f"T_{x:g}mm_anios"] = round(periodo(mu, beta, x), 1)
        filas.append(fila)
    with open(AQUI / "datos" / "gumbel_momentos.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    for fl in filas:
        print(fl)

    # ---------------------------------------------------------------- gráfico de Gumbel
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    colores = {"Puerto Ayora (FCD)": "#6baed6", "Bellavista (FCD)": "#08519c"}
    for nombre in ("Puerto Ayora (FCD)", "Bellavista (FCD)"):
        xs = sorted(series[nombre].values())
        n = len(xs)
        # posiciones de Gringorten
        yv = [-math.log(-math.log((i + 1 - 0.44) / (n + 0.12))) for i in range(n)]
        ax.plot(yv, xs, "o", ms=3.5, color=colores[nombre], label=f"{nombre}: máximos anuales ({n} años)")
        mu, beta = gumbel_momentos(xs)
        y = [-1.6 + 0.05 * k for k in range(140)]
        ax.plot(y, [mu + beta * t for t in y], "-", lw=1.4, color=colores[nombre],
                label=f"Gumbel por momentos ($\\mu$ = {mu:.0f} mm; $\\beta$ = {beta:.0f} mm)".replace(".", ","))
    for (et, x), ls in zip(EVENTO, ("--", "-.", ":")):
        ax.axhline(x, color="0.25", lw=0.9, ls=ls)
        ax.text(-1.55, x + 6, f"{et}: ≥{x:g} mm".replace(".", ","), fontsize=7.5, color="0.2")
    sec = ax.secondary_xaxis("top", functions=(lambda t: t, lambda t: t))
    sec.set_xticks([-math.log(-math.log(1 - 1 / T)) for T in PERIODOS])
    sec.set_xticklabels([str(T) for T in PERIODOS])
    sec.set_xlabel("Periodo de retorno (años)")
    ax.set_xlabel("Variable reducida de Gumbel  $y = -\\ln(-\\ln F)$")
    ax.set_ylabel("Lluvia máxima diaria del año (mm)")
    ax.set_xlim(-1.6, 5.4)
    ax.set_ylim(0, 520)
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=7.2, frameon=False, bbox_to_anchor=(0.0, 0.93))
    fig.tight_layout()
    fig.savefig(AQUI / "figuras" / "gumbel_fcd.png", dpi=200)
    plt.close(fig)

    # ---------------------------------------------------------------- anomalía del nivel del mar
    r = json.loads(MAREAS.read_text())
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    for cod, col, mk in (("puerto_ayora", "#08519c", "o"), ("baltra", "#e6550d", "s")):
        e = r["estaciones"][cod]
        a = e["anomalia_mensual_uhslc_m"]
        meses = sorted(a)
        x = [dt.date.fromisoformat(m + "-15") for m in meses]
        ax.plot(x, [100 * a[m] for m in meses], marker=mk, ms=3.5, lw=1.3, color=col, label=e["nombre"])
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_ylabel("Anomalía mensual (cm)")
    ax.set_title("Nivel medio mensual observado (UHSLC) menos el nivel medio de 2017–2024", fontsize=8.5)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    fig.tight_layout()
    fig.savefig(AQUI / "figuras" / "anomalia_nivel_mar.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
