"""Figuras propias del Informe técnico 2026-06 (modelo hidrodinámico 2D «rain-on-grid» del 30-oct-2026).

Lee solo los resúmenes ya calculados por geodatos/scripts/24_modelo2d_santa_cruz.py
(geodatos/estudios/santa-cruz/datos/modelo2d/<escenario>/resumen_<escenario>.json); no corre el modelo.
Escribe en informes/2026-06-modelo-2d/figuras/.

Uso (desde la raíz del repositorio):
    geodatos/.venv/bin/python -I informes/2026-06-modelo-2d/figuras.py
"""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
M2D = RAIZ / "geodatos/estudios/santa-cruz/datos/modelo2d"
FIG = AQUI / "figuras"
FIG.mkdir(exist_ok=True)

coma = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def resumen(carpeta):
    """El resumen lleva el nombre del escenario base (sin el sufijo _F… del barrido)."""
    (f,) = (M2D / carpeta).glob("resumen_*.json")
    return json.loads(f.read_text())


def barrido_f():
    """Barrido de la pérdida constante F del juego (b): 30-oct (inunda) frente a 3-oct (sin inundación reportada)."""
    F = [10, 15, 20, 25, 30, 35]
    nombre = lambda base, f: base if f == 25 else f"{base}_F{f}"     # F = 25 mm/h es el escenario principal
    oct30 = [resumen(nombre("b_central", f)) for f in F]
    oct03 = [resumen(nombre("b_03oct", f)) for f in F]
    for r, f in zip(oct30 + oct03, F + F):                           # comprobación: la F del resumen es la del barrido
        assert r["perdidas_ilcl"]["F_mmh"]["parque"] == f, (r["escenario"], f)
    centro = lambda r: r["puntos"]["La Cascada (centro)"]["calado_max_m"]
    q_in = lambda r: r["entrada_la_cascada"]["q_max_m3s"]
    a = resumen("central")                                           # juego (a), SCS-CN, como referencia

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.9))
    ax1.plot(F, [q_in(r) for r in oct30], "o-", color="#1f77b4", label="30-oct")
    ax1.plot(F, [q_in(r) for r in oct03], "s--", color="#888", label="3–4-oct")
    ax1.axhline(q_in(a), color="#d62728", lw=0.9, ls=":")
    ax1.text(35.5, q_in(a) + 6, f"juego (a): {q_in(a):.0f}".replace(".", ","), color="#d62728", fontsize=7, ha="right", va="bottom")
    ax1.set_xlabel("Pérdida constante F (mm/h)")
    ax1.set_ylabel("Caudal pico de entrada (m³/s)")
    ax1.set_title("a) Caudal de entrada a La Cascada", fontsize=9)
    ax2.plot(F, [centro(r) for r in oct30], "o-", color="#1f77b4", label="30-oct (inundación reportada)")
    ax2.plot(F, [centro(r) for r in oct03], "s--", color="#888", label="3–4-oct (sin inundación reportada)")
    ax2.axhline(centro(a), color="#d62728", lw=0.9, ls=":", label="juego (a) SCS-CN, 30-oct")
    ax2.axhline(2.0, color="k", lw=0.6, ls="--")
    ax2.text(10, 2.03, "testimonio ≈2 m", fontsize=7, va="bottom")
    ax2.set_xlabel("Pérdida constante F (mm/h)")
    ax2.set_ylabel("Calado máximo, centro (m)")
    ax2.set_title("b) Calado en el centro del barrio", fontsize=9)
    ax2.set_ylim(-0.1, 2.8)
    for ax in (ax1, ax2):
        ax.axvspan(24, 26, color="#1f77b4", alpha=0.12)
        ax.set_xticks(F)
        ax.yaxis.set_major_formatter(coma)
        ax.grid(alpha=0.25)
    ax2.legend(fontsize=6.5, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG / "barrido_f.png", dpi=220)
    plt.close(fig)


def calado_ab():
    """Une los mapas de calado máximo de los juegos (b) y (a) del script 24, recortando el título y el margen vacío.
    Solo recorta y pega los PNG originales (no los modifica)."""
    import numpy as np
    from PIL import Image
    org = RAIZ / "geodatos/estudios/santa-cruz/figuras"
    pb = Image.open(org / "m2d_calado_max_b_central.png").convert("RGB").crop((110, 45, 793, 1300))   # sin título ni barra
    pa = Image.open(org / "m2d_calado_max_central.png").convert("RGB").crop((110, 45, 940, 1300))     # con barra de color
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 4.6), gridspec_kw={"width_ratios": [pb.width, pa.width]})
    for ax, im, tit in zip(axs, (pb, pa), ("Juego (b): pérdida inicial + constante", "Juego (a): SCS-CN distribuido")):
        ax.imshow(np.asarray(im)); ax.set_title(tit, fontsize=9); ax.axis("off")
    fig.tight_layout(w_pad=0.5)
    fig.savefig(FIG / "calado_max_ab.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    barrido_f()
    calado_ab()
    print("figuras ->", FIG)
