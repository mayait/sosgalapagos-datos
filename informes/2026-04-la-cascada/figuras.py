"""Figuras propias del Informe técnico 2026-04 (La Cascada: cuenca aportante, vaso cerrado y desvío).

Lee solo resultados ya calculados por geodatos/scripts/12_cascada_analisis.py (estudios/la-cascada/datos/resumen.json);
no recalcula nada. Escribe en informes/2026-04-la-cascada/figuras/.

Uso (desde la raíz del repositorio):
    geodatos/.venv/bin/python -I informes/2026-04-la-cascada/figuras.py
"""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
RESUMEN = RAIZ / "geodatos/estudios/la-cascada/datos/resumen.json"
FIG = AQUI / "figuras"
FIG.mkdir(exist_ok=True)

coma = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def transito_vaso():
    """Cota máxima del agua en el vaso frente a la longitud efectiva del frente de desborde (evento medido del 30-oct)."""
    R = json.loads(RESUMEN.read_text())
    esc = R["evento_30oct_medido"]["escenarios"]
    rebose = R["depresion"]["cota_rebose_m"]
    defs = [d["cota_rebose_m"] for d in R["rebose"]["definiciones"]]
    obs = R["evento_31oct"]["observacion_referencia"]["cota_agua_m"]
    metodos = {"G_ARF": ("Reducción areal (152 mm)", "#7f7f7f"),
               "G_uniforme": ("Los Guayabillos uniforme (179 mm, central)", "#c0392b"),
               "gradiente_cota_G_SR": ("Gradiente con la cota (208 mm)", "#5b1a12")}
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.axhspan(min(defs), max(defs), color="#dddddd", zorder=0, label=f"Cota de rebose según la definición ({min(defs):.2f}–{max(defs):.2f} m)".replace(".", ","))
    ax.axhspan(*obs, facecolor="none", edgecolor="#c0392b", hatch="///", lw=0, alpha=0.5, zorder=0,
               label="Cota compatible con el testimonio («hasta dos metros»)")
    ax.axhline(rebose, color="k", lw=0.8, ls="--")
    ax.text(1150, rebose + 0.03, f"rebose de referencia {rebose:.2f} m".replace(".", ","), fontsize=7, ha="right", va="bottom")
    xs = [100, 300, 1000]
    for clave, (etq, col) in metodos.items():
        for cn in ("CN68", "CN76"):
            for tc, ls in (("temez", "-"), ("kirpich", ":")):
                e = next(e for e in esc if e["escenario"] == f"MEDIDO30oct_{clave}_{cn}_{tc}")
                ys = [e["transito_vaso"][f"L{x}m"]["cota_max_m"] for x in xs]
                ax.plot(xs, ys, ls=ls, color=col, lw=1.6 if cn == "CN76" else 0.9, marker="o", ms=3,
                        label=etq if (cn == "CN76" and tc == "temez") else None)
    ax.set_xscale("log")
    ax.set_xticks(xs, ["100", "300", "1000"])
    ax.minorticks_off()
    ax.yaxis.set_major_formatter(coma)
    ax.set_xlabel("Longitud efectiva del frente de desborde (m)")
    ax.set_ylabel("Cota máxima del agua (m, DSM)")
    ax.set_xlim(85, 1180)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=6.6, loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "transito_vaso.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    transito_vaso()
    print("figuras ->", FIG)
