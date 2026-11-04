"""Figuras y animaciones de la biblioteca de tormentas sintéticas (script 32).

  .venv/bin/python -I scripts/33_tormentas_figuras.py todo <isla>          generador, frecuencia, umbrales, mapa de pluviómetros
  .venv/bin/python -I scripts/33_tormentas_figuras.py animar <isla> [id …] animaciones MP4 + GIF (sin id: elige 3 tormentas tipo)
  .venv/bin/python -I scripts/33_tormentas_figuras.py red -                  efecto de añadir estaciones (tras «todo» en las dos islas)

Salidas: estudios/tormentas/figuras/. Todo es simulación propia (no oficial); cada figura lo dice.
"""
import csv, json, math, pathlib, sys, subprocess, importlib.util, warnings
warnings.filterwarnings("ignore")
import numpy as np, rasterio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap, BoundaryNorm
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("m32", ROOT / "scripts/32_tormentas_sinteticas.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
FIG = M.EST / "figuras"; FIG.mkdir(parents=True, exist_ok=True)
NOMBRE = {"santa-cruz": "Santa Cruz", "san-cristobal": "San Cristóbal"}
AVISO = "Simulación propia de SOS Galápagos (modelo 2D, DSM 30 m, tormentas sintéticas). No es un dato oficial."
REGLA_V02 = {"niveles": {"medio": dict(R1h=15, R3h=30, R24h=50), "alto": dict(R1h=30, R3h=60, R24h=100), "muy alto": dict(R1h=45, R3h=90, R24h=150)},
             "factor_suelo_humedo": {"P5d_min_mm": 53, "factor": 0.8}}      # clima/recolector/umbrales_inundacion.json (v0.2)
NIVELES = [("bajo", "#16a34a"), ("medio", "#d97706"), ("alto", "#dc2626"), ("muy alto", "#7f1d1d")]
CM_AGUA = ListedColormap(["#c6dbef", "#6baed6", "#2171b5", "#08306b"]); B_AGUA = [0.1, 0.3, 1, 2, 5]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
# vista de detalle (lon0, lat0, lon1, lat1)
ZOOM = {"santa-cruz": (-90.327, -0.752, -90.301, -0.705), "san-cristobal": (-89.622, -0.916, -89.544, -0.888)}
ZOOM_ANIM = {"santa-cruz": (-90.338, -0.7525, -90.296, -0.7215), "san-cristobal": (-89.622, -0.916, -89.544, -0.888)}
EVENTOS_REALES = {"santa-cruz": [  # lo medido en la regla v0.2 (clima/docs/umbrales-la-cascada.md), para situar lo sintético
    dict(nombre="30-oct-2026 (inundó)", R1h=58, R3h=131, inunda=True), dict(nombre="23-oct (sin reporte)", R1h=28 * 0.75, R3h=50 * 0.75, inunda=False),
    dict(nombre="3-oct (sin reporte)", R1h=12.6, R3h=30, inunda=False)]}


def dom(isla):
    d = M.dominio(isla); d["isla"] = isla; return d


def ext_dom(d):
    tr = d["tr"]; H, W = d["z"].shape
    return [tr.c, tr.c + W * tr.a, tr.f + H * tr.e, tr.f]


def ext_amplia(d):
    atr = rasterio.Affine(*d["amplia_tr"]); h, w = d["amplia_z"].shape
    return [atr.c, atr.c + w * atr.a, atr.f + h * atr.e, atr.f]


def vista_general(d):
    """Encuadre: dominio + estaciones + 1,5 km."""
    e = ext_dom(d); xs = [v[0] for v in d["estaciones_xy"].values()]; ys = [v[1] for v in d["estaciones_xy"].values()]
    return [min(e[0], min(xs)) - 1500, max(e[1], max(xs)) + 1500, min(e[2], min(ys)) - 1500, max(e[3], max(ys)) + 1500]


def sombra(z, celda, mask=None):
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(z, nan=0), vert_exag=2.5, dx=celda, dy=celda)
    if mask is not None: hs = np.where(mask, hs, np.nan)
    return hs


def fondo(ax, d, ext=None, detalle=False):
    za = d["amplia_z"].astype(float); tierra_a = za > 0.5
    ax.set_facecolor("#dbe9f6")
    ax.imshow(np.where(tierra_a, 1, np.nan), extent=ext_amplia(d), cmap=ListedColormap(["#efe9dc"]), zorder=0)
    ax.imshow(sombra(za, 150, tierra_a), extent=ext_amplia(d), cmap="gray", vmin=0, vmax=1, alpha=0.45, zorder=1)
    if detalle:
        ax.imshow(sombra(d["z"], 30, d["tierra"]), extent=ext_dom(d), cmap="gray", vmin=0, vmax=1, alpha=0.5, zorder=1)
    # contorno del dominio del modelo
    ax.contour(np.flipud(d["act"].astype(float)), levels=[0.5], extent=ext_dom(d), colors="#555", linewidths=0.6, linestyles="--", zorder=3, origin="lower")
    if ext: ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_visible(True); s.set_color("#999")


def escala(ax, km=2):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    xa = x0 + 0.05 * (x1 - x0); ya = y0 + 0.04 * (y1 - y0)
    ax.plot([xa, xa + km * 1000], [ya, ya], color="k", lw=2, zorder=9); ax.text(xa + km * 500, ya + 0.012 * (y1 - y0), f"{km} km", ha="center", fontsize=7, zorder=9)


def estaciones(ax, d, tam=None, colores=None, etiquetas=True, fs=7):
    for i, (nm, (x, y, cota, lo, la)) in enumerate(d["estaciones_xy"].items()):
        c = colores[nm] if colores else "#111"
        ax.plot(x, y, marker="^", ms=(tam[nm] if tam else 7), mfc=c, mec="white", mew=0.8, zorder=8)
        if etiquetas: ax.text(x + 250, y + 150, nm, fontsize=fs, zorder=8, color="#111",
                              bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))


def campo_lluvia_amplia(p, d, t_s, dt_s=600):
    """Lluvia (mm/h) de los dt_s segundos anteriores a t_s sobre la rejilla amplia (150 m)."""
    atr = rasterio.Affine(*d["amplia_tr"]); h, w = d["amplia_z"].shape
    X = atr.c + atr.a * (np.arange(w) + .5); Y = atr.f + atr.e * (np.arange(h) + .5); MX, MY = np.meshgrid(X, Y)
    za = np.maximum(d["amplia_z"].astype(float), 0)
    nb = int(round(t_s / M.DT_B)) + 1
    w_ = M.pesos_tiempo(p, max(nb, int(round(p["dur_h"] * 3600 / M.DT_B)) + 1))
    k1 = int(round(t_s / M.DT_B)); k0 = max(k1 - int(dt_s / M.DT_B), 0)
    out = np.zeros_like(MX)
    for k in range(k0, k1):
        if k < len(w_) and w_[k] > 0: out += p["D_mm"] * w_[k] * M.factor_espacial(p, MX, MY, za, (k + 0.5) * M.DT_B)
    return out * 3600 / dt_s


def total_lluvia_amplia(p, d):
    atr = rasterio.Affine(*d["amplia_tr"]); h, w = d["amplia_z"].shape
    X = atr.c + atr.a * (np.arange(w) + .5); Y = atr.f + atr.e * (np.arange(h) + .5); MX, MY = np.meshgrid(X, Y)
    za = np.maximum(d["amplia_z"].astype(float), 0)
    nb = int(round(p["dur_h"] * 3600 / M.DT_B)) + 1; w_ = M.pesos_tiempo(p, nb)
    out = np.zeros_like(MX)
    for k in np.flatnonzero(w_): out += p["D_mm"] * w_[k] * M.factor_espacial(p, MX, MY, za, (k + 0.5) * M.DT_B)
    return out


def describir(p):
    if p["tipo"] == "celda":
        txt = f"núcleo de {p['sigma_m'] / 1000:.1f} km" + (" sobre la parte alta" if p.get("centro") == "montaña" else "")
        if p["vel_ms"] and p["vel_ms"] > 0.5: txt += f", se desplaza a {p['vel_ms'] * 3.6:.0f} km/h"
    elif p["tipo"] == "orografica": txt = "más lluvia cuanto más alto"
    else: txt = "lluvia pareja en toda la zona"
    return (f"{p['D_mm']:.0f} mm en {p['dur_h']:.1f} h en el núcleo; {txt}; suelo {'húmedo' if p['P5d_mm'] > 53 else ('seco' if p['P5d_mm'] < 36 else 'normal')}"
            f" (P5d {p['P5d_mm']:.0f} mm); el suelo traga {p['F_mmh']:.0f} mm/h")


# ---------------------------------------------------------------- 1. el generador
def fig_generador(isla):
    d = dom(isla); cat = M.leer_catalogo(isla); rng = np.random.default_rng(3)
    ejemplos = []
    for tipo, centro in (("celda", "montaña"), ("celda", "montaña"), ("celda", "cualquiera"), ("orografica", None), ("uniforme", None), ("celda", "montaña")):
        cand = [p for p in cat if p["tipo"] == tipo and (centro is None or p.get("centro") == centro) and p["id"] not in [e["id"] for e in ejemplos]]
        ejemplos.append(cand[int(rng.integers(len(cand)))])
    st = d["estaciones_xy"]; nm_st = list(st)
    xs = np.array([st[k][0] for k in nm_st]); ys = np.array([st[k][1] for k in nm_st]); cz = np.array([st[k][2] for k in nm_st])
    vg = vista_general(d); cols = plt.cm.tab10(np.arange(len(nm_st)))
    ancho = (vg[1] - vg[0]) / (vg[3] - vg[2]) > 1.6
    if ancho:                                                   # San Cristóbal: dominio alargado → mapas en 2 filas de 3
        fig = plt.figure(figsize=(14, 8.4))
        gt = fig.add_gridspec(2, 3, left=0.04, right=0.92, top=0.9, bottom=0.42, wspace=0.04, hspace=0.25)
        celdas_mapa = [gt[i // 3, i % 3] for i in range(6)]
    else:
        fig = plt.figure(figsize=(14, 6.4))
        gt = fig.add_gridspec(1, 6, left=0.04, right=0.92, top=0.88, bottom=0.42, wspace=0.04)
        celdas_mapa = [gt[0, i] for i in range(6)]
    gb = fig.add_gridspec(1, 6, left=0.04, right=0.92, top=0.35, bottom=0.11, wspace=0.32)
    TIPO = {"celda": "núcleo de tormenta", "orografica": "orográfica", "uniforme": "uniforme"}
    for i, p in enumerate(ejemplos):
        ax = fig.add_subplot(celdas_mapa[i]); fondo(ax, d, vg)
        tot = total_lluvia_amplia(p, d)
        im = ax.imshow(np.where(tot >= 2, tot, np.nan), extent=ext_amplia(d), cmap="YlGnBu", vmin=0, vmax=150, alpha=0.8, zorder=4)
        estaciones(ax, d, etiquetas=False, colores={n: cols[j] for j, n in enumerate(nm_st)}, tam={n: 7 for n in nm_st})
        ax.set_title(f"#{p['id']} · {TIPO[p['tipo']]}" + (f"\n(centro: {p['centro']})" if p.get("centro") else "\n"), fontsize=8.5)
        ax2 = fig.add_subplot(gb[0, i]); nb = int(round(p["dur_h"] * 3600 / M.DT_B)) + 12
        ll = M.lluvia_puntos(p, xs, ys, cz, nb)
        for j, n in enumerate(nm_st):
            ax2.plot(np.arange(1, nb + 1) * M.DT_B / 3600, np.cumsum(ll[:, j]), color=cols[j], lw=1.4, label=n)
        ax2.set_xlabel("horas", fontsize=7.5); ax2.tick_params(labelsize=7)
        if i == 0: ax2.set_ylabel("lluvia acumulada en\ncada pluviómetro (mm)", fontsize=7.5)
        ax2.set_title(f"núcleo: {p['D_mm']:.0f} mm en {p['dur_h']:.1f} h", fontsize=7.5)
    cax = fig.add_axes([0.93, 0.47, 0.012, 0.38]); cb = fig.colorbar(im, cax=cax); cb.set_label("lluvia total (mm)", fontsize=8); cb.ax.tick_params(labelsize=7)
    h_, l_ = ax2.get_legend_handles_labels(); fig.legend(h_, l_, loc="lower center", ncol=len(nm_st), fontsize=8, frameon=False, bbox_to_anchor=(0.48, 0.0))
    fig.suptitle(f"{NOMBRE[isla]}: seis de las 500 tormentas sintéticas y lo que marcaría cada pluviómetro (▲)", fontsize=12.5, y=0.98)
    fig.text(0.04, -0.01, AVISO + " Línea discontinua: zona que simula el modelo 2D.", fontsize=7, color="#555")
    fig.savefig(FIG / f"generador_{isla}.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 2. frecuencia de inundación
def fig_frecuencia(isla):
    d = dom(isla); f = rasterio.open(M.EST / "datos" / isla / "frecuencia_inundacion.tif").read(1)
    res = json.loads((M.EST / "datos" / isla / "resumen.json").read_text())
    from pyproj import Transformer
    T = Transformer.from_crs(4326, d["epsg"], always_xy=True).transform
    lo0, la0, lo1, la1 = ZOOM[isla]; (x0, y0), (x1, y1) = T(lo0, la0), T(lo1, la1)
    if isla == "santa-cruz":
        fig, axs = plt.subplots(1, 2, figsize=(11, 7.2), gridspec_kw=dict(width_ratios=[1, 1.1], wspace=0.04)); vistas = (ext_dom(d), [x0, x1, y0, y1])
    else:
        fig, ax_ = plt.subplots(figsize=(14, 5.2)); axs = [ax_]; e_ = ext_dom(d); vistas = ([e_[0] + 300, e_[1] - 300, e_[2] + 300, e_[3] - 300],)
    cm = plt.cm.YlOrRd
    for k, (ax, ex) in enumerate(zip(axs, vistas)):
        fondo(ax, d, ex, detalle=True)
        im = ax.imshow(np.where(f >= 0.01, f * 100, np.nan), extent=ext_dom(d), cmap=cm, vmin=0, vmax=50, zorder=5)
        for zn, zc in M.ZONAS[isla].items():
            r, c, lo, la = d["puntos_rc"][zc["punto"]]; x, y = T(lo, la)
            ax.plot(x, y, "o", ms=6, mfc="none", mec="k", mew=1.4, zorder=9)
            if ex[0] < x < ex[1] and ex[2] < y < ex[3]:
                ax.text(x + 120, y + 60, zn, fontsize=8, zorder=9, clip_on=True, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
        if k == 0 and len(axs) > 1: ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="k", lw=1, zorder=9)); escala(ax, 2)
        else: escala(ax, 1)
    cb = fig.colorbar(im, ax=axs, shrink=0.6 if len(axs) > 1 else 0.85, pad=0.01); cb.set_label("% de las tormentas que dejan ≥ 0,3 m de agua")
    fig.suptitle(f"{NOMBRE[isla]}: dónde se acumula el agua con más frecuencia ({res['n_tormentas']} tormentas sintéticas)", fontsize=12)
    fig.text(0.01, 0.01, AVISO + " La frecuencia es la del conjunto de tormentas simuladas, no una probabilidad anual: "
             "el conjunto sobrerrepresenta tormentas fuertes a propósito.\nLos puntos sueltos son hoyos del DSM (techos, árboles, canteras): el modelo de superficie los llena aunque en la realidad drenen.", fontsize=7, color="#555")
    fig.savefig(FIG / f"frecuencia_{isla}.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 3. umbrales
def fig_umbrales(isla):
    res = json.loads((M.EST / "datos" / isla / "resumen.json").read_text())
    zonas = list(M.ZONAS[isla]); n = len(zonas)
    fig, axs = plt.subplots(1, n, figsize=(4.6 * n, 4.8), squeeze=False); axs = axs[0]
    for ax, zn in zip(axs, zonas):
        rz = res["zonas"][zn]
        rows = list(csv.DictReader(open(M.EST / "datos" / isla / f"previo_llegada_{M.slug(zn)}.csv")))
        R1 = np.array([float(r["R1h"]) for r in rows]); R3 = np.array([float(r["R3h"]) for r in rows])
        y = np.array([r["inunda"] == "True" for r in rows]); wet = np.array([float(r["P5d"]) > 53 for r in rows])
        ax.scatter(R1[~y], R3[~y], s=10, c="#9ca3af", alpha=0.6, lw=0, label="no se inunda")
        ax.scatter(R1[y & ~wet], R3[y & ~wet], s=13, c="#2563eb", alpha=0.85, lw=0, label="se inunda")
        ax.scatter(R1[y & wet], R3[y & wet], s=13, c="#2563eb", alpha=0.85, marker="s", lw=0, label="se inunda (suelo húmedo)")
        lim1 = max(100, np.percentile(R1, 99)); lim3 = max(200, np.percentile(R3, 99))
        for nv, col in NIVELES[1:]:
            u = rz["propuesta"][nv]["umbrales"]
            ax.plot([u["R1h"], u["R1h"], 0], [0, u["R3h"], u["R3h"]], color=col, lw=1.8)
            ax.text(u["R1h"] + 1, 3, nv, color=col, fontsize=7.5, rotation=90, va="bottom")
        if isla == "santa-cruz":
            u = rz["regla_v02"]["alto"]["umbrales"]
            ax.plot([u["R1h"], u["R1h"], 0], [0, u["R3h"], u["R3h"]], color="k", lw=1, ls=":", label="«alto» v0.2 (hoy)")
            if zn == "La Cascada":
                for e in EVENTOS_REALES[isla]:
                    ax.plot(e["R1h"], e["R3h"], marker="*", ms=13, mfc="#dc2626" if e["inunda"] else "white", mec="k", zorder=9)
                    ax.text(e["R1h"] + 2, e["R3h"] + 3, e["nombre"], fontsize=7)
        ax.set_xlim(0, lim1); ax.set_ylim(0, lim3)
        ax.set_xlabel("Lluvia máxima en 1 h antes de que llegue el agua (mm)")
        ax.set_ylabel("Lluvia máxima en 3 h (mm)")
        ax.set_title(f"{zn}\n{rz['inundan']} de {rz['n']} tormentas inundan · «alto»: detecta {rz['propuesta']['alto']['POD'] * 100:.0f} %, "
                     f"falsa alarma {rz['propuesta']['alto']['POFD'] * 100:.0f} %", fontsize=8.5)
    axs[0].legend(fontsize=7, loc="upper left", frameon=False)
    fig.suptitle(f"{NOMBRE[isla]}: qué marcan los pluviómetros de cada zona antes de que llegue el agua (máximo ponderado de sus estaciones)", fontsize=11)
    fig.text(0.01, -0.03, AVISO + " Regla «basta superar uno» con 1 h, 3 h y 24 h; aquí solo se dibujan 1 h y 3 h. Líneas de color: umbrales que optimizan el modelo (no adoptados)."
             + (" ★: lluvias medidas (Los Guayabillos y Santa Rosa ×0,75)." if isla == "santa-cruz" else " En San Cristóbal la regla v0.2 no está calibrada."),
             fontsize=7, color="#555")
    fig.tight_layout(); fig.savefig(FIG / f"umbrales_{isla}.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 4. ¿dónde poner el próximo pluviómetro?
def fig_mapa_pluviometros(isla, zona=None):
    d = dom(isla); cat = {p["id"]: p for p in M.leer_catalogo(isla)}
    zona = zona or list(M.ZONAS[isla])[0]
    rows = list(csv.DictReader(open(M.EST / "datos" / isla / f"previo_llegada_{M.slug(zona)}.csv")))
    atr = rasterio.Affine(*d["amplia_tr"]); za = d["amplia_z"]
    paso = 3
    rr, cc = np.mgrid[0:za.shape[0]:paso, 0:za.shape[1]:paso]; rr = rr.ravel(); cc = cc.ravel()
    ok = za[rr, cc] > 1; rr, cc = rr[ok], cc[ok]
    X = atr.c + atr.a * (cc + .5); Y = atr.f + atr.e * (rr + .5); Z = za[rr, cc].astype(float)
    S = np.zeros((len(rows), len(X))); yv = np.zeros(len(rows), bool)
    for i, r in enumerate(rows):
        p = cat[int(r["id"])]; f = M.CACHE / isla / "corridas" / f"t{p['id']:04d}.npz"
        nb = np.load(f)["serie"].shape[0]
        ll = M.lluvia_puntos(p, X, Y, Z, nb); V = M.ventanas(ll)[3]
        if r["inunda"] == "True":
            k_lim = int(int(r["llegada_min"]) * 60 / M.DT_B) - 1 - int(M.MIN_AVISO_S / M.DT_B)
            S[i] = V[:max(k_lim, 0) + 1].max(axis=0) if k_lim >= 0 else 0
            yv[i] = True
        else:
            S[i] = V.max(axis=0)
    A = np.array([M.auc(S[:, j], yv) for j in range(S.shape[1])])
    nr, nc = len(range(0, za.shape[0], paso)), len(range(0, za.shape[1], paso))
    G = np.full((nr, nc), np.nan); G[rr // paso, cc // paso] = A
    ea = ext_amplia(d); ext_g = [ea[0], ea[0] + nc * paso * atr.a, ea[3] - nr * paso * abs(atr.e), ea[3]]
    res = json.loads((M.EST / "datos" / isla / "resumen.json").read_text())["zonas"][zona]
    vg = vista_general(d); asp = (vg[1] - vg[0]) / (vg[3] - vg[2]); ancho = asp > 1.6
    fig, ax = plt.subplots(figsize=(14, 14 / asp + 2.2) if ancho else (8.5, 7.5)); fondo(ax, d, vg)
    v0 = max(0.5, float(np.floor(np.nanpercentile(A, 2) * 20) / 20)); v1 = float(np.ceil(np.nanmax(A) * 50) / 50)
    im = ax.imshow(G, extent=ext_g, cmap="viridis", vmin=v0, vmax=v1, alpha=0.8, zorder=4, interpolation="bilinear")
    niveles = [x for x in (0.7, 0.8, 0.85, 0.9, 0.95) if v0 < x < v1]
    if niveles:
        cs = ax.contour(np.nan_to_num(G, nan=0), levels=niveles, extent=[ext_g[0], ext_g[1], ext_g[3], ext_g[2]], colors="w", linewidths=0.8, zorder=5, origin="upper")
        ax.clabel(cs, fontsize=6.5, fmt="%.2f")
    from pyproj import Transformer
    T = Transformer.from_crs(4326, d["epsg"], always_xy=True).transform
    r_, c_, lo, la = d["puntos_rc"][M.ZONAS[isla][zona]["punto"]]; x, y = T(lo, la)
    ax.plot(x, y, "o", ms=10, mfc="#dc2626", mec="white", mew=1.5, zorder=9); ax.text(x + 300, y - 300, zona, fontsize=9, color="#7f1d1d", weight="bold", zorder=9)
    puestas = []
    for nm, (x_, y_, cota, lo_, la_) in d["estaciones_xy"].items():
        a_ = res["auc_R3h_por_estacion"].get(nm)
        ax.plot(x_, y_, "^", ms=9, mfc="white", mec="k", zorder=9)
        n_cerca = sum(1 for (px, py) in puestas if math.hypot(px - x_, py - y_) < 1500)
        puestas.append((x_, y_))
        der = x_ > (vg[0] + vg[1]) / 2
        ax.text(x_ + (-300 if der else 300), y_ + 150 - n_cerca * 750, f"{nm} · AUC {a_:.2f}" if a_ == a_ else nm, fontsize=7, zorder=9,
                ha="right" if der else "left", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    i_b = int(np.nanargmax(A)); ax.plot(X[i_b], Y[i_b], marker="*", ms=16, mfc="#facc15", mec="k", zorder=10)
    ax.text(X[i_b] + 350, Y[i_b] - 500, f"mejor sitio · AUC {A[i_b]:.2f}", fontsize=7.5, ha="left", zorder=10, weight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="#fef9c3", ec="none", alpha=0.9))
    escala(ax, 2)
    if ancho:
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", shrink=0.5, pad=0.03, aspect=40)
        cb.set_label(f"Qué tan bien anticipa un pluviómetro ahí la inundación de {zona} (AUC de la lluvia en 3 h)")
    else:
        cb = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.01)
        cb.set_label(f"Qué tan bien anticipa un pluviómetro ahí\nla inundación de {zona} (AUC de la lluvia en 3 h)")
    ax.set_title(f"{NOMBRE[isla]}: ¿dónde conviene el próximo pluviómetro para avisar a {zona}?", fontsize=11)
    fig.text(0.01, 0.01, AVISO + " AUC 0,5 = no anticipa nada; 1 = separa perfectamente las tormentas que inundan de las que no. Se usa la lluvia en 3 h hasta 15 min antes de que llegue el agua.",
             fontsize=6.8, color="#555")
    fig.savefig(FIG / f"pluviometros_{isla}_{M.slug(zona)}.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    i = int(np.nanargmax(A)); TI = Transformer.from_crs(d["epsg"], 4326, always_xy=True).transform
    lo_b, la_b = TI(X[i], Y[i])
    return dict(zona=zona, mejor_auc=round(float(A[i]), 3), mejor_lon=round(lo_b, 4), mejor_lat=round(la_b, 4), mejor_cota_m=round(float(Z[i])))


# ---------------------------------------------------------------- 5. regla de hoy frente a la propuesta
def fig_comparacion(isla):
    res = json.loads((M.EST / "datos" / isla / "resumen.json").read_text())
    zonas = list(M.ZONAS[isla]); fig, axs = plt.subplots(1, len(zonas), figsize=(3.6 * len(zonas), 3.6), squeeze=False); axs = axs[0]
    for ax, zn in zip(axs, zonas):
        rz = res["zonas"][zn]; x = np.arange(3)
        for k, (clave, lab, hatch) in enumerate((("regla_v02", "v0.2 (hoy)", ""), ("propuesta", "propuesta", "//"))):
            pod = [rz[clave][nv]["POD"] * 100 for nv in ("medio", "alto", "muy alto")]
            pofd = [rz[clave][nv]["POFD"] * 100 for nv in ("medio", "alto", "muy alto")]
            ax.bar(x + (k - 0.5) * 0.38, pod, 0.36, color="#2563eb", alpha=0.85 if k else 0.45, hatch=hatch, label=f"detecta (POD), {lab}")
            ax.bar(x + (k - 0.5) * 0.38, [-v for v in pofd], 0.36, color="#dc2626", alpha=0.85 if k else 0.45, hatch=hatch, label=f"falsa alarma, {lab}")
        ax.axhline(0, color="k", lw=0.6); ax.set_xticks(x); ax.set_xticklabels(["medio", "alto", "muy alto"])
        ax.set_ylim(-100, 100); ax.set_yticks([-100, -50, 0, 50, 100]); ax.set_yticklabels(["100 %", "50 %", "0", "50 %", "100 %"])
        ax.set_title(zn, fontsize=9)
    axs[0].set_ylabel("↑ inundaciones avisadas · ↓ tormentas sin\ninundación que igual disparan el nivel", fontsize=8)
    h_, l_ = axs[0].get_legend_handles_labels(); fig.legend(h_, l_, loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.1))
    fig.suptitle(f"{NOMBRE[isla]}: la regla de hoy (v0.2) frente a la propuesta, probadas con las mismas tormentas sintéticas", fontsize=10.5)
    fig.text(0.01, -0.16, AVISO + " Aviso «a tiempo» = al menos 15 min antes de que el agua llegue a 0,3 m.", fontsize=7, color="#555")
    fig.tight_layout(); fig.savefig(FIG / f"comparacion_reglas_{isla}.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 5b. compromiso: falsas alarmas frente a minutos de aviso
def lluvia_real_30oct():
    """R1h, R3h, R24h de La Cascada con la lluvia IERSE medida (Los Guayabillos ×1, Santa Rosa ×0,75) del 29-oct al 1-nov."""
    import datetime as dt
    t0 = dt.datetime(2026, 10, 29, 0, 0); nb = int(4 * 86400 / M.DT_B); S = {}
    for f in ("lluvia_ierse_30oct_5min.csv", "lluvia_ierse_validacion_5min.csv"):
        for r in csv.DictReader(open(ROOT / "estudios/la-cascada/datos" / f)):
            k = int((dt.datetime.fromisoformat(r["fecha_hora_local"]) - t0).total_seconds() // M.DT_B)
            if 0 <= k < nb: S.setdefault(r["estacion"], np.zeros(nb))[k] += float(r["lluvia_mm"] or 0)
    ll = np.c_[S["Los Guayabillos"] * 1.0, S["Santa Rosa"] * 0.75]
    V = M.ventanas(ll); return t0, {v: V[v].max(axis=1) for v in (1, 3, 24)}


def fig_compromiso(isla, zona):
    import datetime as dt
    d = dom(isla); cat = M.leer_catalogo(isla); zc = M.ZONAS[isla][zona]; st = d["estaciones_xy"]; nm_st = list(st)
    xs = np.array([st[k][0] for k in nm_st]); ys = np.array([st[k][1] for k in nm_st]); cz = np.array([st[k][2] for k in nm_st])
    D_ = M.premax_por_tormenta(isla, zona, zc, cat, nm_st, xs, ys, cz, [s for s, _ in zc["v02"]], [w for _, w in zc["v02"]])
    base = np.array([30.0, 60.0, 100.0]); escalas = np.round(np.arange(0.5, 2.01, 0.05), 2)
    real = lluvia_real_30oct() if (isla == "santa-cruz" and zona == "La Cascada") else None
    filas = []
    for e in escalas:
        th = base * e; hits = fa = 0; leads = []; n1 = sum(x["imp"] for x in D_); n0 = len(D_) - n1
        for x in D_:
            f = 0.8 if x["P5d"] > 53 else 1.0
            cr = (x["Rz"][1] >= th[0] * f) | (x["Rz"][3] >= th[1] * f) | (x["Rz"][24] >= th[2] * f)
            if x["imp"]:
                lim = x["k_arr"] - int(M.MIN_AVISO_S / M.DT_B)
                if lim >= 0 and cr[:lim + 1].any():
                    hits += 1; leads.append((x["k_arr"] - int(np.argmax(cr))) * M.DT_B / 60)
            elif cr.any(): fa += 1
        fila = dict(escala=float(e), R1h=th[0], R3h=th[1], R24h=th[2], POD=hits / max(n1, 1), POFD=fa / max(n0, 1), aviso_mediano_min=float(np.median(leads)) if leads else None)
        if real is not None:
            t0, Rz = real
            cr = (Rz[1] >= th[0]) | (Rz[3] >= th[1]) | (Rz[24] >= th[2])
            fila["hora_30oct"] = (t0 + dt.timedelta(seconds=(int(np.argmax(cr)) + 1) * M.DT_B)).strftime("%H:%M") if cr.any() else None
        filas.append(fila)
    with open(M.EST / "datos" / isla / f"compromiso_{M.slug(zona)}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); [w.writerow(r) for r in filas]
    fig, ax = plt.subplots(figsize=(9.5, 4.8)); ax2 = ax.twinx()
    E = [r["escala"] for r in filas]
    ax.plot(E, [r["POD"] * 100 for r in filas], color="#2563eb", lw=2, label="inundaciones avisadas a tiempo (%)")
    ax.plot(E, [r["POFD"] * 100 for r in filas], color="#dc2626", lw=2, label="tormentas sin inundación que disparan «alto» (%)")
    ax2.plot(E, [r["aviso_mediano_min"] or np.nan for r in filas], color="#111", lw=1.6, ls="--", label="anticipación mediana (min, eje derecho)")
    ax.axvline(1.0, color="#555", lw=0.8); ax.text(1.01, 102, "v0.2 hoy\n30/60/100 mm", fontsize=7.5, va="top")
    ax.set_ylim(0, 105); ax2.set_ylim(0, max(r["aviso_mediano_min"] or 0 for r in filas) * 1.15)
    ax.set_xlabel("umbrales de «alto» = escala × (30 mm en 1 h, 60 mm en 3 h, 100 mm en 24 h)"); ax.set_ylabel("%"); ax2.set_ylabel("minutos de aviso antes de que llegue el agua")
    ax2.spines["right"].set_visible(True)
    if real is not None:
        for e_ in (0.75, 1.0, 1.25, 1.5, 1.75):
            r_ = min(filas, key=lambda r: abs(r["escala"] - e_))
            ax.text(e_, 3, f"30-oct:\n{r_['hora_30oct'] or '—'}", fontsize=7, ha="center", color="#7f1d1d",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#fef2f2", ec="none"))
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7.5, frameon=False, loc="center right")
    ax.set_title(f"{zona}: subir los umbrales quita falsas alarmas pero también minutos de aviso", fontsize=11)
    nota = AVISO + " Anticipación medida hasta que el agua llega a 0,3 m en el modelo 2D."
    if real is not None: nota += " Recuadros: hora en que cada versión habría dado «alto» con la lluvia medida del 30-oct (IERSE)."
    fig.text(0.01, -0.04, nota, fontsize=6.8, color="#555")
    fig.tight_layout(); fig.savefig(FIG / f"compromiso_{isla}_{M.slug(zona)}.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- 5c. ¿qué gana la regla v0.2 con otra estación?
def escenarios_red():
    """Regla v0.2 (medio y alto) con las estaciones de hoy, + Cerro Crocker (La Cascada) y + un pluviómetro en el mejor sitio."""
    out = {}
    for isla in ("santa-cruz", "san-cristobal"):
        d = dom(isla); cat = M.leer_catalogo(isla); st = dict(d["estaciones_xy"])
        T = Transformer.from_crs(4326, d["epsg"], always_xy=True).transform
        mejores = json.loads((M.EST / "datos" / isla / "mejor_sitio_pluviometro.json").read_text())
        for zn, zc in M.ZONAS[isla].items():
            mb = [m for m in mejores if m["zona"] == zn][0]; x, y = T(mb["mejor_lon"], mb["mejor_lat"])
            st2 = dict(st); st2["NUEVO"] = (x, y, mb["mejor_cota_m"], mb["mejor_lon"], mb["mejor_lat"])
            nm = list(st2); xs = np.array([st2[k][0] for k in nm]); ys = np.array([st2[k][1] for k in nm]); cz = np.array([st2[k][2] for k in nm])
            base = list(zc["v02"]); variantes = {"v0.2 (estaciones de hoy)": base}
            if isla == "santa-cruz" and zn == "La Cascada": variantes["+ Cerro Crocker"] = base + [("Cerro Crocker", 1.0)]
            variantes["+ pluviómetro nuevo en el mejor sitio"] = base + [("NUEVO", 1.0)]
            for vn, ests in variantes.items():
                D_ = M.premax_por_tormenta(isla, zn, zc, cat, nm, xs, ys, cz, [s for s, _ in ests], [w for _, w in ests])
                pm = np.array([x_["pm"] for x_ in D_]); imp = np.array([x_["imp"] for x_ in D_]); wet = np.array([x_["P5d"] for x_ in D_]) > 53
                r = {}
                for nv in ("medio", "alto"):
                    th = tuple(REGLA_V02["niveles"][nv][k] for k in ("R1h", "R3h", "R24h"))
                    pod, pofd = M.evaluar(np.array([th], float), pm, imp, wet, 0.8)
                    r[nv] = dict(POD=round(float(pod[0]), 3), POFD=round(float(pofd[0]), 3), aviso_min=M.anticipacion(D_, np.array(th, float), 0.8))
                out.setdefault(isla, {}).setdefault(zn, {})[vn] = r
    (M.EST / "datos" / "escenarios_red.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- 6. animaciones
def nivel_regla(Rz, regla, wet_f):
    """Nivel (0–3) en cada bloque de 5 min con la regla propuesta."""
    nb = len(Rz[1]); lv = np.zeros(nb, int)
    for k, nv in enumerate(("medio", "alto", "muy alto"), start=1):
        u = regla["niveles"][nv]; f = wet_f
        m = (Rz[1] >= u["R1h"] * f) | (Rz[3] >= u["R3h"] * f) | (Rz[24] >= u["R24h"] * f)
        lv[m] = k
    # persistencia de 8 h, como la v0.2
    out = lv.copy(); per = int(8 * 3600 / M.DT_B)
    for k in range(nb): out[k] = lv[max(0, k - per):k + 1].max()
    return out


def elegir_tormentas(isla):
    """Tres tormentas que cuentan la historia: aviso a tiempo, inundación que la red no ve, tormenta fuerte sin inundación."""
    zn = list(M.ZONAS[isla])[0]; zc = M.ZONAS[isla][zn]
    regla = REGLA_V02
    cat = {p["id"]: p for p in M.leer_catalogo(isla)}
    d = dom(isla); st = d["estaciones_xy"]; nm_st = list(st)
    est = [s for s, _ in zc["v02"]]; pes = [w for _, w in zc["v02"]]
    xs = np.array([st[k][0] for k in est]); ys = np.array([st[k][1] for k in est]); cz = np.array([st[k][2] for k in est])
    rows = list(csv.DictReader(open(M.EST / "datos" / isla / f"previo_llegada_{M.slug(zn)}.csv")))
    a_tiempo, ciega, susto = [], [], []
    for r in rows:
        p = cat[int(r["id"])]
        if p["dur_h"] > 9: continue
        nb = int(round((max(p["dur_h"] + 6, 8)) * 3600 / M.DT_B))
        ll = M.lluvia_puntos(p, xs, ys, cz, nb) * np.array(pes)[None, :]; V = M.ventanas(ll)
        Rz = {v: V[v].max(axis=1) for v in (1, 3, 24)}
        lv = nivel_regla(Rz, regla, regla["factor_suelo_humedo"]["factor"] if p["P5d_mm"] > 53 else 1.0)
        if r["inunda"] == "True":
            k_arr = int(int(r["llegada_min"]) * 60 / M.DT_B) - 1
            k_al = int(np.argmax(lv >= 2)) if (lv >= 2).any() else None
            if k_al is not None and k_arr - k_al >= 12 and p["tipo"] == "celda" and float(r["hmax"]) >= 0.6: a_tiempo.append((abs(k_arr - k_al - 18), p["id"]))
            if (lv[:max(k_arr - 2, 1)] < 1).all() and p["tipo"] == "celda": ciega.append((-float(r["hmax"]), p["id"]))
        elif lv.max() >= 2 and p["tipo"] == "celda":
            susto.append((-p["D_mm"], p["id"]))
    out = []
    for lista in (a_tiempo, ciega, susto):
        if lista: out.append(sorted(lista)[0][1])
    return out


def animar(isla, ids=None):
    import imageio.v2 as imageio
    d = dom(isla); cat = {p["id"]: p for p in M.leer_catalogo(isla)}
    ids = ids or elegir_tormentas(isla)
    zn = list(M.ZONAS[isla])[0]; zc = M.ZONAS[isla][zn]
    regla = REGLA_V02
    st = d["estaciones_xy"]; nm_st = list(st)
    xs = np.array([st[k][0] for k in nm_st]); ys = np.array([st[k][1] for k in nm_st]); cz = np.array([st[k][2] for k in nm_st])
    est = [s for s, _ in zc["v02"]]; pes = np.array([w for _, w in zc["v02"]])
    T = Transformer.from_crs(4326, d["epsg"], always_xy=True).transform
    lo0, la0, lo1, la1 = ZOOM_ANIM[isla]; (zx0, zy0), (zx1, zy1) = T(lo0, la0), T(lo1, la1)
    vg = vista_general(d); cols = dict(zip(nm_st, plt.cm.tab10(np.arange(len(nm_st)))))
    ancho = (vg[1] - vg[0]) / (vg[3] - vg[2]) > 1.6
    hs_a = sombra(d["amplia_z"].astype(float), 150, d["amplia_z"] > 0.5); hs_d = sombra(d["z"], 30, d["tierra"])
    hechos = []
    for tid in ids:
        p = cat[tid]
        r = M.correr_tormenta(p, d, guardar_cuadros=True)
        C = r["cuadros"].astype("float32"); nb = r["nb"]
        ll = M.lluvia_puntos(p, xs, ys, cz, nb); V = M.ventanas(ll)
        idx = [nm_st.index(s) for s in est]
        Rz = {v: (V[v][:, idx] * pes[None, :]).max(axis=1) for v in (1, 3, 24)}
        lv = nivel_regla(Rz, regla, regla["factor_suelo_humedo"]["factor"] if p["P5d_mm"] > 53 else 1.0)
        ser = r["serie"][:, r["puntos"].index(zc["punto"])]
        k_arr = int(np.argmax(ser >= M.H_IMPACTO)) if (ser >= M.H_IMPACTO).any() else None
        horas = np.arange(1, nb + 1) * M.DT_B / 3600
        dirn = FIG / f"_cuadros_{isla}_{tid}"; dirn.mkdir(exist_ok=True)
        for f_ in dirn.glob("*.png"): f_.unlink()
        nfr = len(C)
        for k in range(nfr):
            kb = 2 * (k + 1) - 1; t_s = (kb + 1) * M.DT_B
            fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
            if ancho:      # isla alargada: mapa general arriba a todo lo ancho; detalle y series abajo
                gs = fig.add_gridspec(3, 2, width_ratios=[1.0, 1.0], height_ratios=[1.15, 0.62, 0.62], left=0.01, right=0.985, top=0.9, bottom=0.07, wspace=0.12, hspace=0.38)
                ax = fig.add_subplot(gs[0, :]); pos_zoom, pos_a1, pos_a2 = gs[1:, 0], gs[1, 1], gs[2, 1]
            else:
                gs = fig.add_gridspec(3, 2, width_ratios=[1.05, 1.25], height_ratios=[1.5, 0.6, 0.6], left=0.01, right=0.985, top=0.9, bottom=0.07, wspace=0.07, hspace=0.32)
                ax = fig.add_subplot(gs[:, 0]); pos_zoom, pos_a1, pos_a2 = gs[0, 1], gs[1, 1], gs[2, 1]
            ax.set_facecolor("#dbe9f6")
            ax.imshow(np.where(d["amplia_z"] > 0.5, 1, np.nan), extent=ext_amplia(d), cmap=ListedColormap(["#efe9dc"]), zorder=0)
            ax.imshow(hs_a, extent=ext_amplia(d), cmap="gray", vmin=0, vmax=1, alpha=0.45, zorder=1)
            Rf = campo_lluvia_amplia(p, d, t_s)
            ax.imshow(np.where(Rf >= 2, Rf, np.nan), extent=ext_amplia(d), cmap="PuBu", vmin=0, vmax=120, alpha=0.8, zorder=4)
            ax.contour(np.flipud(d["act"].astype(float)), levels=[0.5], extent=ext_dom(d), colors="#444", linewidths=0.6, linestyles="--", zorder=5, origin="lower")
            h = C[k]; ax.imshow(np.where(h >= 0.1, np.clip(h, 0, 4.99), np.nan), extent=ext_dom(d), cmap=CM_AGUA, norm=BoundaryNorm(B_AGUA, CM_AGUA.N), zorder=6)
            ax.add_patch(plt.Rectangle((zx0, zy0), zx1 - zx0, zy1 - zy0, fill=False, ec="k", lw=0.9, zorder=7))
            puestas = []
            for j, nm in enumerate(nm_st):
                x, y = st[nm][:2]; r1 = V[1][kb, j]
                ax.plot(x, y, "^", ms=7 + min(r1, 80) / 6, mfc=cols[nm], mec="white", mew=0.9, zorder=9)
                n_c = sum(1 for (px, py) in puestas if math.hypot(px - x, py - y) < 1500); puestas.append((x, y))
                der = x > (vg[0] + vg[1]) / 2
                ax.text(x + (-350 if der else 350), y + 200 - n_c * 900, f"{nm}: {r1:.0f} mm en 1 h", fontsize=6.8, zorder=9, clip_on=True,
                        ha="right" if der else "left", bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
            ax.set_xlim(vg[0], vg[1]); ax.set_ylim(vg[2], vg[3]); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal"); escala(ax, 2)
            ax.set_title("Lluvia de los últimos 10 min (azul violáceo) y agua en superficie (azul)", fontsize=8.5)
            # detalle del pueblo
            az = fig.add_subplot(pos_zoom); az.set_facecolor("#dbe9f6")
            az.imshow(np.where(d["tierra"], 1, np.nan), extent=ext_dom(d), cmap=ListedColormap(["#efe9dc"]), zorder=0)
            az.imshow(hs_d, extent=ext_dom(d), cmap="gray", vmin=0, vmax=1, alpha=0.5, zorder=1)
            im = az.imshow(np.where(h >= 0.1, np.clip(h, 0, 4.99), np.nan), extent=ext_dom(d), cmap=CM_AGUA, norm=BoundaryNorm(B_AGUA, CM_AGUA.N), zorder=6)
            for zn2, zc2 in M.ZONAS[isla].items():
                _, _, lo, la = d["puntos_rc"][zc2["punto"]]; x, y = T(lo, la)
                az.plot(x, y, "o", ms=6, mfc="none", mec="#7f1d1d", mew=1.3, zorder=9)
                az.text(x + 80, y + 50, zn2, fontsize=7.5, zorder=9, color="#7f1d1d", clip_on=True, bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))
            az.set_xlim(zx0, zx1); az.set_ylim(zy0, zy1); az.set_xticks([]); az.set_yticks([]); az.set_aspect("equal")
            cb = fig.colorbar(im, ax=az, shrink=0.8, pad=0.01); cb.set_label("calado (m)", fontsize=7); cb.ax.tick_params(labelsize=7)
            # lluvia de la zona y nivel de alerta
            a1 = fig.add_subplot(pos_a1)
            for v, c_, lab in ((1, "#0ea5e9", "lluvia en 1 h"), (3, "#1e3a8a", "lluvia en 3 h")):
                a1.plot(horas[:kb + 1], Rz[v][:kb + 1], color=c_, lw=1.6, label=lab)
                a1.axhline(regla["niveles"]["alto"][f"R{v}h"], color=c_, lw=0.8, ls="--")
            for k2 in range(kb + 1):
                a1.axvspan(horas[k2] - M.DT_B / 3600, horas[k2], ymin=0.93, ymax=1, color=NIVELES[lv[k2]][1], lw=0)
            a1.set_xlim(0, horas[-1]); a1.set_ylim(0, max(Rz[3].max(), regla["niveles"]["alto"]["R3h"]) * 1.15)
            a1.set_ylabel("mm", fontsize=8); a1.tick_params(labelsize=7); a1.legend(fontsize=7, frameon=False, loc="upper right")
            a1.set_title(f"Pluviómetros de {zn} (máximo ponderado) · franja: nivel v0.2 · - - umbral «alto»", fontsize=8)
            a2 = fig.add_subplot(pos_a2)
            a2.fill_between(horas[:kb + 1], ser[:kb + 1], color="#2563eb", alpha=0.6); a2.axhline(M.H_IMPACTO, color="#dc2626", lw=0.8, ls="--")
            a2.set_xlim(0, horas[-1]); a2.set_ylim(0, max(ser.max() * 1.15, 0.5)); a2.set_xlabel("horas desde que empieza a llover", fontsize=8)
            a2.set_ylabel("m", fontsize=8); a2.tick_params(labelsize=7)
            a2.set_title(f"Agua en {zn} (modelo) · - - 0,3 m = inundación", fontsize=8)
            if k_arr is not None and k_arr <= kb:
                a2.axvline(horas[k_arr], color="#dc2626", lw=1)
            nv = NIVELES[lv[kb]]
            fig.text(0.01, 0.955, f"{NOMBRE[isla]} · tormenta sintética #{tid}", fontsize=13, weight="bold")
            fig.text(0.01, 0.925, describir(p), fontsize=9, color="#333")
            fig.text(0.985, 0.94, f"{(kb + 1) * M.DT_B / 3600:4.1f} h   nivel: {nv[0].upper()}", fontsize=13, ha="right", weight="bold", color=nv[1])
            fig.text(0.01, 0.012, AVISO, fontsize=7.5, color="#555")
            fig.savefig(dirn / f"{k:04d}.png"); plt.close(fig)
        mp4 = FIG / f"anim_{isla}_{tid}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "6", "-i", str(dirn / "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24",
                        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", str(mp4)], check=True)
        gif = FIG / f"anim_{isla}_{tid}.gif"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "6", "-i", str(dirn / "%04d.png"), "-vf",
                        "scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4", str(gif)], check=True)
        for f_ in dirn.glob("*.png"): f_.unlink()
        dirn.rmdir()
        # póster: el cuadro del máximo
        hechos.append(dict(id=tid, mp4=mp4.name, gif=gif.name, descripcion=describir(p), inunda=k_arr is not None,
                           llegada_h=round(float(horas[k_arr]), 2) if k_arr is not None else None,
                           nivel_max=NIVELES[int(lv.max())][0],
                           alto_h=round(float(horas[int(np.argmax(lv >= 2))]), 2) if (lv >= 2).any() else None))
        print("animación:", mp4, flush=True)
    f = M.EST / "datos" / isla / "animaciones.json"
    prev = json.loads(f.read_text()) if f.exists() else []
    prev = [x for x in prev if x["id"] not in [h["id"] for h in hechos]] + hechos
    f.write_text(json.dumps(prev, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    isla = a[1]
    if a[0] == "todo":
        fig_generador(isla); fig_frecuencia(isla); fig_umbrales(isla); fig_comparacion(isla)
        for zn in M.ZONAS[isla]: fig_compromiso(isla, zn)
        mejores = [fig_mapa_pluviometros(isla, zn) for zn in M.ZONAS[isla]]
        (M.EST / "datos" / isla / "mejor_sitio_pluviometro.json").write_text(json.dumps(mejores, ensure_ascii=False, indent=1))
        print(json.dumps(mejores, ensure_ascii=False, indent=1))
    elif a[0] == "red":
        escenarios_red()
    elif a[0] == "animar":
        animar(isla, [int(x) for x in a[2:]] or None)
