"""Figura de la cronología del 30-oct-2026 en Santa Cruz: lluvia medida (10 min), hidrograma de La Cascada e hitos.

Uso: .venv/bin/python -I scripts/20_cronologia_figura.py
Salida: estudios/santa-cruz/figuras/cronologia_30oct.png
"""
import csv, datetime as dt, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = pathlib.Path(__file__).resolve().parents[1]
LC = ROOT / "estudios/la-cascada/datos"; SC = ROOT / "estudios/santa-cruz/datos"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "savefig.dpi": 200, "savefig.bbox": "tight",
                     "axes.spines.top": False, "axes.spines.right": False})
T0, T1 = dt.datetime(2026, 10, 30, 12), dt.datetime(2026, 10, 31, 8)

# lluvia 5 min → 10 min
ll = {}
for r in csv.DictReader(open(LC / "lluvia_ierse_30oct_5min.csv")):
    t = dt.datetime.fromisoformat(r["fecha_hora_local"][:19])
    if not (T0 <= t <= T1): continue
    k = t.replace(minute=t.minute // 10 * 10, second=0)
    ll.setdefault(r["estacion"], {}).setdefault(k, 0.0)
    ll[r["estacion"]][k] += float(r["lluvia_mm"] or 0)

# hidrograma
H = list(csv.DictReader(open(LC / "hidrogramas_evento_30oct.csv")))
def tt(s):
    return dt.datetime.strptime("2026 " + s, "%Y %d-%b %H:%M")
th = [tt(r["fecha_hora_utc6"]) for r in H]
def col(k): return np.array([float(r[k]) for r in H]) if k in H[0] else None
qt, qk = col("MEDIDO30oct_G_uniforme_CN76_temez"), col("MEDIDO30oct_G_uniforme_CN76_kirpich")
rango = [col(k) for k in H[0] if k.startswith("MEDIDO30oct") and col(k) is not None]

fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, gridspec_kw=dict(height_ratios=[1, 1.1], hspace=0.08))
w = dt.timedelta(minutes=10) / 2.3
for i, (est, c) in enumerate((("Los Guayabillos", "#08519c"), ("Santa Rosa", "#6baed6"))):
    d = ll.get(est, {})
    ks = sorted(d)
    a1.bar([k + (i - 0.5) * w + dt.timedelta(minutes=5) for k in ks], [d[k] for k in ks], width=w, color=c,
           label=f"{est}: {sum(d.values()):.0f} mm medidos de 12:00 a 21:25")
a1.set_ylabel("Lluvia en 10 min (mm)")
a1.axvspan(dt.datetime(2026, 10, 30, 21, 25), T1, color="#bbb", alpha=0.35)
a1.text(dt.datetime(2026, 10, 30, 21, 35), a1.get_ylim()[1] * 0.82, "Las estaciones dejan de transmitir (21:22–21:25):\nla lluvia posterior no se midió", fontsize=8, color="#444")
a1.legend(loc="upper left", fontsize=8, frameon=False); a1.grid(axis="y", alpha=0.25)
a1.set_title("Santa Cruz, 30 de octubre de 2026: lluvia medida, crecida estimada en La Cascada e hitos de alerta (hora de Galápagos, UTC−6)", fontsize=10)

if rango:
    R = np.vstack(rango); a2.fill_between(th, R.min(0), R.max(0), color="#d62728", alpha=0.13, label="Rango de escenarios (lluvia areal, CN 68–83, Témez–Kirpich)")
if qt is not None: a2.plot(th, qt, color="#d62728", lw=2, label="Escenario central (CN 76, tc Témez)")
if qk is not None: a2.plot(th, qk, color="#d62728", lw=1.2, ls="--", label="Escenario central (CN 76, tc Kirpich)")
a2.set_ylabel("Caudal en la entrada a La Cascada (m³/s)"); a2.grid(axis="y", alpha=0.25)
a2.axvspan(dt.datetime(2026, 10, 30, 16, 51), dt.datetime(2026, 10, 30, 18, 12), color="#2171b5", alpha=0.18)
a2.text(dt.datetime(2026, 10, 30, 16, 55), a2.get_ylim()[1] * 0.93, "vaso de\nLa Cascada\nlleno", fontsize=7.5, color="#08306b", va="top")
hitos = [(dt.datetime(2026, 10, 30, 18, 51), "18:51 Los Guayabillos\nsupera 30 mm en 1 h", "#ff7f0e", 0.80, "right"),
         (dt.datetime(2026, 10, 30, 19, 36), "19:36 supera\n50 mm en 3 h", "#ff7f0e", 0.62, "left"),
         (dt.datetime(2026, 10, 30, 21, 40), "21:40–22:50\npico estimado", "#d62728", 0.98, "left")]
for t, txt, c, y, ha in hitos:
    for a in (a1, a2): a.axvline(t, color=c, lw=1, ls=":")
    a2.text(t + dt.timedelta(minutes=6 if ha == "left" else -6), a2.get_ylim()[1] * y, txt, fontsize=7.5, color=c, va="top", ha=ha,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
a2.legend(loc="upper right", fontsize=7.5, frameon=False, bbox_to_anchor=(1, 0.75))
a2.set_xlim(T0, T1); a2.xaxis.set_major_locator(mdates.HourLocator(interval=2)); a2.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b\n%H:%M"))
fig.text(0.01, -0.04, "Contexto: alerta naranja (SNGR, desde 20-jul) y roja nacional (desde 29-ago) vigentes; la advertencia INAMHI n.º 84 preveía «eventos leves» en el archipiélago. "
         "Lluvia: red IERSE-WSN (Universidad del Azuay). Hidrograma: SCS-CN con lluvia areal de Los Guayabillos; modelo preliminar sin calibrar.", fontsize=7, color="#555", wrap=True)
out = ROOT / "estudios/santa-cruz/figuras/cronologia_30oct.png"; out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out); print(out)
