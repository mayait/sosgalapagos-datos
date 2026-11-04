"""Figura de síntesis del Informe técnico 2026-09 (vigilancia satelital GOES-19 sobre Santa Cruz).

Uso (desde la raíz del repositorio):
    geodatos/.venv/bin/python -I informes/2026-09-satelite/figuras.py

Lee SOLO clima/satelite/resumen.json (lo genera clima/satelite/s0_evaluar.py); no baja datos.
Salida (en figuras/):
  vigilancia_sintesis.png  (a) % del tiempo en vigilancia v1 por mes y zona;
                           (b) cronología de octubre a 3-nov: episodios de vigilancia v1 frente a
                               episodios de lluvia intensa medida, en hora de Galápagos (UTC−6).
Todo es una ESTIMACIÓN SATELITAL contrastada con lluvia medida: no es una alerta oficial.
"""
import datetime as dt
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
R = json.loads((RAIZ / "clima/satelite/resumen.json").read_text())
OUT = AQUI / "figuras"
OUT.mkdir(exist_ok=True)
G6 = dt.timezone(dt.timedelta(hours=-6))
ZONAS = {"la-cascada": "La Cascada", "santa-cruz-alta": "Parte alta de Santa Cruz"}
COL = {"la-cascada": "#1f4e79", "santa-cruz-alta": "#8fb3d9"}


def t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(G6).replace(tzinfo=None)


fig = plt.figure(figsize=(10, 6.4))
gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.15], hspace=0.42)

# (a) porcentaje del tiempo en vigilancia por mes
ax = fig.add_subplot(gs[0])
vc = R["vigilancia_continua"]["periodos"]
meses = [("ene-abr", "2026-01", "ene"), ("ene-abr", "2026-02", "feb"), ("ene-abr", "2026-03", "mar"),
         ("ene-abr", "2026-04", "abr"), ("oct-nov", "2026-10", "oct"), ("oct-nov", "2026-11", "1–2 nov")]
x = range(len(meses))
for i, z in enumerate(ZONAS):
    vals = [vc[p][z]["meses"][m]["pct"] for p, m, _ in meses]
    xs = [k + (i - 0.5) * 0.38 for k in x]
    ax.bar(xs, vals, width=0.38, color=COL[z], label=ZONAS[z])
    for xx, v in zip(xs, vals):
        ax.text(xx, v + 0.8, f"{v:.1f}".replace(".", ","), ha="center", va="bottom", fontsize=7.5)
ax.set_xticks(list(x), [e for _, _, e in meses])
ax.set_ylabel("% del tiempo en vigilancia")
ax.set_ylim(0, 40)
ax.axvline(3.5, color="0.6", lw=0.8, ls=":")
ax.text(3.55, 37, "mayo–sep: no evaluado", fontsize=7.5, color="0.4", va="top")
ax.legend(fontsize=8, frameon=False, loc="upper left")
ax.set_title("(a) Regla v1 con 3 h de persistencia, por mes (2026)", fontsize=10, loc="left")
ax.grid(axis="y", alpha=0.3)

# (b) cronología octubre–3-nov
ax = fig.add_subplot(gs[1])
ce = R["contingencia_episodios"]
for i, z in enumerate(ZONAS):
    y = 1 - i
    for e in vc["oct-nov"][z]["episodios"]:
        a, b = t(e["inicio"]), t(e["fin"])
        ax.barh(y + 0.17, (b - a).total_seconds() / 86400, left=mdates.date2num(a), height=0.28,
                color="#d4a017", edgecolor="none")
    for e in ce[z]["episodios_lluvia"]:
        a, b = t(e["inicio"]), t(e["fin"])
        w = max((b - a).total_seconds() / 86400, 0.12)
        ax.barh(y - 0.17, w, left=mdates.date2num(a), height=0.28,
                color="#1f4e79" if e["detectado"] else "#c0392b", edgecolor="none")
        ax.text(mdates.date2num(a) + w / 2, y - 0.36,
                f"{e['R1h_max']:.0f}".replace(".", ","), fontsize=7, va="top", ha="center")
ax.set_yticks([1, 0], [ZONAS[z] for z in ZONAS], fontsize=8.5)
ax.set_ylim(-0.7, 1.6)
ax.set_xlim(dt.datetime(2026, 10, 1), dt.datetime(2026, 11, 3, 18))
ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 5, 10, 15, 20, 25]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
ax.set_xlabel("fecha (hora de Galápagos, UTC−6)")
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color="#d4a017", label="vigilancia v1 (estimación satelital)"),
                   Patch(color="#1f4e79", label="lluvia intensa medida, detectada"),
                   Patch(color="#c0392b", label="lluvia intensa medida, no detectada")],
          fontsize=7.5, frameon=False, loc="upper left", ncol=3)
ax.set_title("(b) Episodios de octubre a 3-nov (cifra: R1h máx. medida, mm); lluvia intensa = R1h ≥ 15 o R3h ≥ 30 mm",
             fontsize=10, loc="left")
ax.grid(axis="x", alpha=0.3)

fig.savefig(OUT / "vigilancia_sintesis.png", dpi=180, bbox_inches="tight")
print("✔", OUT / "vigilancia_sintesis.png")
