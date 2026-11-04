"""Figuras del informe 2026-01 (base geoespacial y HAND). Solo lee capas ya generadas del repositorio
(geodatos/capas/raster/ y geodatos/export/galapagos/); no recalcula ningún modelo.

Uso (desde la raíz del repositorio):
    geodatos/.venv/bin/python -I informes/2026-01-base-hand/figuras.py
Salidas: informes/2026-01-base-hand/figuras/{area_estudio,hand_poblados,exposicion}.png y solape_cgreg.json
(indicador descriptivo del solape del HAND publicado con los polígonos del CGREG; no es una validación)
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon as MplPolygon
from PIL import Image
from shapely.geometry import shape

RAIZ = pathlib.Path(__file__).resolve().parents[2]
RAS = RAIZ / "geodatos/capas/raster"
EXP = RAIZ / "geodatos/export/galapagos"
OUT = pathlib.Path(__file__).resolve().parent / "figuras"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.titlesize": 9})
LIM = json.loads((RAS / "limites.json").read_text())
CLAVE = {"Santa Cruz": "santa_cruz", "San Cristóbal": "san_cristobal", "Isabela": "isabela_sur"}
C_SUSC = {3: "#1e3a8a", 2: "#3b82f6", 1: "#93c5fd"}


def capa(nombre):
    return json.loads((EXP / f"{nombre}.geojson").read_text())["features"]


def extent(key):
    (s, w), (n, e) = LIM[key]["bounds"]
    return [w, e, s, n]


def relieve(ax, key):
    im = Image.open(RAS / f"{key}_relieve.png")
    tierra = np.asarray(im)[..., 3] > 0
    fondo = np.zeros(tierra.shape + (4,), np.uint8)
    fondo[tierra] = (246, 243, 236, 255); fondo[~tierra] = (219, 233, 243, 255)
    ax.imshow(fondo, extent=extent(key), zorder=0)
    ax.imshow(im, extent=extent(key), zorder=1)


def poligonos(ax, geoms, **kw):
    parches = []
    for g in geoms:
        for p in getattr(g, "geoms", [g]):
            if p.geom_type == "Polygon":
                parches.append(MplPolygon(list(p.exterior.coords), closed=True))
    ax.add_collection(PatchCollection(parches, **kw))


def lineas(ax, geoms, **kw):
    segs = []
    for g in geoms:
        for l in getattr(g, "geoms", [g]):
            if l.geom_type == "LineString":
                segs.append(list(l.coords))
    ax.add_collection(LineCollection(segs, **kw))


def ejes(ax, x0, x1, y0, y1, km):
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    d = km / 111.32
    xb, yb = x0 + 0.05 * (x1 - x0), y0 + 0.05 * (y1 - y0)
    ax.plot([xb, xb + d], [yb, yb], color="k", lw=2, zorder=20)
    ax.text(xb + d / 2, yb + 0.02 * (y1 - y0), f"{km:g} km".replace(".", ","), ha="center", va="bottom", fontsize=7, zorder=20)


# ------------------------------------------------------------------ 1. Área de estudio, cuencas y red de drenaje
aoi = capa("area_interes"); cu = capa("cuencas_localidad"); qb = capa("quebradas"); dr = capa("drenaje_adicional")
VENT = {"Santa Cruz": (-90.48, -90.20, -0.78, -0.55, 5), "San Cristóbal": (-89.64, -89.40, -0.96, -0.84, 2),
        "Isabela": (-91.10, -90.90, -0.98, -0.80, 2)}
DESPL = {"Bellavista": (-90.395, -0.665), "Puerto Ayora": (-90.255, -0.735), "Tomás de Berlanga": (-91.02, -0.825),
         "Puerto Baquerizo Moreno": (-89.565, -0.94)}
fig, axs = plt.subplots(1, 3, figsize=(7.2, 3.3), gridspec_kw={"width_ratios": [1.25, 1.0, 0.9]})
for ax, (isla, (x0, x1, y0, y1, km)) in zip(axs, VENT.items()):
    relieve(ax, CLAVE[isla])
    poligonos(ax, [shape(f["geometry"]) for f in cu if f["properties"]["isla"] == isla],
              facecolor="#f59e0b", edgecolor="#b45309", alpha=0.28, lw=0.8, zorder=3)
    poligonos(ax, [shape(f["geometry"]) for f in aoi if f["properties"]["isla"] == isla],
              facecolor="none", edgecolor="#374151", lw=0.7, linestyle="--", zorder=4)
    for o, w in ((1, 0.3), (2, 0.5), (3, 0.8), (4, 1.1), (5, 1.4), (6, 1.7)):
        lineas(ax, [shape(f["geometry"]) for f in dr if f["properties"]["isla"] == isla and f["properties"].get("orden") == o],
               colors="#0f766e", linewidths=w, zorder=5)
    lineas(ax, [shape(f["geometry"]) for f in qb if f["properties"]["isla"] == isla and "IGM" in f["properties"]["fuente"]],
           colors="#1d4ed8", linewidths=0.7, zorder=6)
    for f in cu:
        p = f["properties"]
        if p["isla"] == isla and p["area_aguas_arriba_km2"] >= 1:
            c = shape(f["geometry"]).representative_point()
            cx, cy = DESPL.get(p["destino"], (c.x, c.y))
            ax.text(cx, cy, f"{p['destino']}\n{p['area_aguas_arriba_km2']:.1f} km²".replace(".", ","), fontsize=6,
                    ha="center", va="center", zorder=8, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    ejes(ax, x0, x1, y0, y1, km)
    ax.set_title(isla if isla != "Isabela" else "Isabela (sur)")
fig.legend(handles=[Patch(fc="#f59e0b", ec="#b45309", alpha=0.4, label="Cuenca completa de la localidad (modelo D8)"),
                    Line2D([], [], color="#374151", ls="--", lw=0.8, label="Área de interés"),
                    Line2D([], [], color="#1d4ed8", lw=0.8, label="Quebradas IGM 1:25 000"),
                    Line2D([], [], color="#0f766e", lw=1.2, label="Cauces D8 no mapeados (grosor = orden de Strahler)")],
           loc="lower center", ncol=2, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.1, 1, 1))
fig.savefig(OUT / "area_estudio.png", dpi=220)
plt.close(fig)

# ------------------------------------------------------------------ 2. HAND en los poblados frente a capas oficiales
of = capa("zonas_inundables_oficiales"); lu = capa("limite_urbano")
ZOOM = [("Santa Cruz", "Puerto Ayora", (-90.337, -90.297, -0.762, -0.722, 0.5)),
        ("San Cristóbal", "Puerto Baquerizo Moreno", (-89.627, -89.587, -0.918, -0.885, 0.5)),
        ("Isabela", "Puerto Villamil", (-90.985, -90.945, -0.968, -0.935, 0.5))]
fig, axs = plt.subplots(1, 3, figsize=(7.2, 3.0))
for ax, (isla, nombre, (x0, x1, y0, y1, km)) in zip(axs, ZOOM):
    key = CLAVE[isla]
    relieve(ax, key)
    ax.imshow(Image.open(RAS / f"{key}_susc_inundacion.png"), extent=extent(key), zorder=2, interpolation="nearest")
    poligonos(ax, [shape(f["geometry"]) for f in lu if f["properties"]["isla"] == isla],
              facecolor="none", edgecolor="#111827", lw=0.8, linestyle=":", zorder=4)
    lineas(ax, [shape(f["geometry"]) for f in qb if f["properties"]["isla"] == isla], colors="#06b6d4", linewidths=0.8, zorder=5)
    poligonos(ax, [shape(f["geometry"]) for f in of if f["properties"]["isla"] == isla and f["properties"]["tipo"] == "Riesgo de inundación"],
              facecolor="none", edgecolor="#dc2626", lw=1.3, zorder=6)
    poligonos(ax, [shape(f["geometry"]) for f in of if f["properties"]["isla"] == isla and f["properties"]["tipo"].startswith("Flujos lodo")],
              facecolor="none", edgecolor="#92400e", lw=1.1, linestyle="--", zorder=6)
    ejes(ax, x0, x1, y0, y1, km)
    ax.set_title(nombre)
fig.legend(handles=[Patch(fc=C_SUSC[3], label="HAND ≤ 1 m (alta)"), Patch(fc=C_SUSC[2], label="1–2,5 m (media)"),
                    Patch(fc=C_SUSC[1], label="2,5–5 m (baja)"),
                    Line2D([], [], color="#dc2626", lw=1.3, label="Riesgo de inundación (CGREG)"),
                    Line2D([], [], color="#92400e", lw=1.1, ls="--", label="Flujos de lodo por El Niño (CGREG)"),
                    Line2D([], [], color="#06b6d4", lw=0.8, label="Quebradas IGM y OSM"),
                    Line2D([], [], color="#111827", lw=0.8, ls=":", label="Límite urbano (IGM)")],
           loc="lower center", ncol=4, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.13, 1, 0.97))
fig.savefig(OUT / "hand_poblados.png", dpi=220)
plt.close(fig)

# ------------------------------------------------------------------ 2b. Solape del HAND publicado con los polígonos del CGREG
# Indicador descriptivo (no es una validación): fracción del área de cada polígono oficial cubierta por cada clase
# acumulada de susceptibilidad_inundacion.geojson. Áreas en grados² → proporciones (misma latitud).
from shapely.ops import unary_union
su = capa("susceptibilidad_inundacion")
solape = {}
for f in of:
    p = f["properties"]
    if p["tipo"] not in ("Riesgo de inundación", "Flujos lodo y escombros (El Niño)"):
        continue
    g = shape(f["geometry"]).buffer(0)
    clave = f"{p['isla']} · {p['tipo']}" + (f" · {p['localidad']}" if p.get("localidad") else "")
    d = solape.setdefault(clave, {"area_ha": 0.0, "nivel_ge_3": 0.0, "nivel_ge_2": 0.0, "nivel_ge_1": 0.0})
    d["area_ha"] += g.area * 111320 ** 2 / 1e4
    for lv in (3, 2, 1):
        u = unary_union([shape(h["geometry"]).buffer(0) for h in su if h["properties"]["isla"] == p["isla"] and h["properties"]["nivel"] >= lv])
        d[f"nivel_ge_{lv}"] += g.intersection(u).area * 111320 ** 2 / 1e4
for d in solape.values():
    for lv in (3, 2, 1):
        d[f"frac_nivel_ge_{lv}"] = round(d.pop(f"nivel_ge_{lv}") / d["area_ha"], 3)
    d["area_ha"] = round(d["area_ha"], 1)
(OUT / "solape_cgreg.json").write_text(json.dumps(solape, ensure_ascii=False, indent=1))
print(json.dumps(solape, ensure_ascii=False, indent=1))

# ------------------------------------------------------------------ 3. Exposición (resumen_exposicion.json)
R = json.loads((EXP / "resumen_exposicion.json").read_text())
islas = ["Santa Cruz", "San Cristóbal", "Isabela"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.5))
x = range(len(islas)); base = [0] * 3
for k, lab, c in (("susc_alta", "Alta", C_SUSC[3]), ("susc_media", "Media", C_SUSC[2]), ("susc_baja", "Baja", C_SUSC[1])):
    v = [100 * R[i][k] / R[i]["edificios"] for i in islas]
    a1.bar(x, v, bottom=base, color=c, label=lab, width=0.6)
    base = [b + vv for b, vv in zip(base, v)]
for xi, i in zip(x, islas):
    a1.text(xi, base[xi] + 1, f"{R[i]['edificios']:,} edif.".replace(",", " "), ha="center", fontsize=7)
a1.set_xticks(list(x), islas); a1.set_ylabel("% de edificios"); a1.set_ylim(0, 48)
a1.set_title("Edificios por clase HAND (máxima que tocan)"); a1.legend(frameon=False, fontsize=7, loc="upper center", ncol=3)
for k, lab, c, dx in (("pob_susc_alta_media", "HAND alta o media", C_SUSC[2], -0.2), ("pob_zona_tsunami", "Zona de tsunami (INOCAR)", "#f97316", 0.2)):
    v = [100 * R[i][k] / R[i]["pob_total"] for i in islas]
    a2.bar([xi + dx for xi in x], v, width=0.38, color=c, label=lab)
    for xi, vv, i in zip(x, v, islas):
        a2.text(xi + dx, vv + 0.8, f"{R[i][k]:,}".replace(",", " "), ha="center", fontsize=6.5)
a2.set_xticks(list(x), islas); a2.set_ylabel("% de la población estimada"); a2.set_ylim(0, 48)
a2.set_title("Población estimada (viviendas SNGR)"); a2.legend(frameon=False, fontsize=7, loc="upper left")
for a in (a1, a2):
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "exposicion.png", dpi=220)
plt.close(fig)
print("ok:", sorted(p.name for p in OUT.glob("*.png")))
