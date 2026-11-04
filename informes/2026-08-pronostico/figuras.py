#!/usr/bin/env python3
"""Figuras propias del informe 2026-08 (pronóstico experimental de lluvia fuerte, fase 0).

Solo LEE tablas versionadas de clima/pronostico/fase0/ (las genera clima/scripts/07_pronostico_evaluacion.py):
  calibracion_logistica.csv   coeficientes a, b de cada curva logística y su BSS en validación cruzada
  senal_niveles.csv           probabilidad media anunciada y frecuencia observada por nivel (validación cruzada)

Escribe en figuras/:
  curvas_logisticas.png   P(≥ 20 mm) frente al consenso, por grupo, temporada y anticipación
  fiabilidad.png          probabilidad anunciada frente a frecuencia observada de ≥ 20 mm, por nivel

Uso, desde la raíz del repositorio:
  geodatos/.venv/bin/python -I informes/2026-08-pronostico/figuras.py
"""
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AQUI = Path(__file__).resolve().parent
FASE0 = AQUI.parent.parent / "clima" / "pronostico" / "fase0"
(AQUI / "figuras").mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

GRUPOS = [("san_cristobal_alta", "lluviosa", "San Cristóbal alta, lluviosa"),
          ("santa_cruz_alta", "garua", "Santa Cruz alta, garúa 2026"),
          ("costa", "lluviosa", "Costa (Puerto Ayora), lluviosa")]
PLAZOS = [("1", "hoy (ant. 1)", "-"), ("2", "mañana (ant. 2)", "--"), ("5", "4 días (ant. 5)", ":")]
COLOR = {"san_cristobal_alta": "#08519c", "santa_cruz_alta": "#d94801", "costa": "#238b45"}


def leer(nombre):
    with open(FASE0 / nombre, newline="") as f:
        return list(csv.DictReader(f))


def coma(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def main():
    cal = leer("calibracion_logistica.csv")
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7), sharey=True)
    xs = [0.40 + 0.6 * k / 200 for k in range(201)]
    for ax, (g, t, titulo) in zip(axs, GRUPOS):
        for plazo, etiqueta, ls in PLAZOS:
            r = next((r for r in cal if r["grupo"] == g and r["temporada"] == t and r["plazo"] == plazo
                      and r["umbral_mm"] == "20" and r["a"]), None)
            if r is None:
                continue
            a, b = float(r["a"]), float(r["b"])
            ax.plot(xs, [100 / (1 + math.exp(-(a + b * x))) for x in xs], ls=ls, color=COLOR[g], lw=1.6,
                    label=f"{etiqueta}; BSS {coma(float(r['bss_cv']))}")
            if plazo == "1":
                base = float(r["frec_base"])
        ax.axhline(100 * base, color="0.5", lw=0.8, ls="-.")
        ax.text(0.41, 100 * base + 1.5, f"frecuencia normal (hoy) {coma(100 * base, 0)} %", fontsize=6.8, color="0.35")
        for lim in (15, 35):
            ax.axhline(lim, color="0.8", lw=0.7)
        ax.set_title(titulo, fontsize=8.5)
        ax.set_xlabel("Consenso (percentil medio)")
        ax.set_xlim(0.4, 1.0)
        ax.set_ylim(0, 80)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    axs[0].set_ylabel("P(≥ 20 mm en el día) (%)")
    fig.tight_layout()
    fig.savefig(AQUI / "figuras" / "curvas_logisticas.png", dpi=200)
    plt.close(fig)

    niv = leer("senal_niveles.csv")
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    marcas = {"1": "o", "2": "s", "3": "^", "5": "D"}
    for g, t, titulo in GRUPOS:
        primero = True
        for r in niv:
            if r["grupo"] != g or r["temporada"] != t:
                continue
            n = int(r["n"])
            ax.scatter(100 * float(r["p_media"]), 100 * float(r["frec_20"]), s=8 + 1.2 * n ** 0.9 if n < 300 else 8 + 1.2 * 300 ** 0.9,
                       marker=marcas[r["plazo"]], color=COLOR[g], alpha=0.75, edgecolor="white", lw=0.5,
                       label=titulo if primero else None)
            primero = False
    ax.plot([0, 80], [0, 80], color="0.4", lw=0.8, ls="--", label="calibración perfecta")
    for lim in (15, 35):
        ax.axvline(lim, color="0.85", lw=0.7)
    ax.set_xlabel("Probabilidad media anunciada de ≥ 20 mm (%)")
    ax.set_ylabel("Frecuencia observada de ≥ 20 mm (%)")
    ax.set_xlim(0, 75)
    ax.set_ylim(0, 75)
    ax.grid(alpha=0.2)
    ax.legend(fontsize=6.8, frameon=False, loc="upper left")
    ax.text(73, 2, "marcador: ○ hoy  □ mañana  △ pasado  ◇ 4 días\ntamaño: número de días",
            fontsize=6.5, ha="right", va="bottom", color="0.3")
    fig.tight_layout()
    fig.savefig(AQUI / "figuras" / "fiabilidad.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
