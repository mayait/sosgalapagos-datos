"""Figuras del informe técnico sobre La Cascada (Puerto Ayora, Santa Cruz).

Lee los resultados de 12_cascada_analisis.py en estudios/la-cascada/datos/ y escribe PNG en estudios/la-cascada/figuras/.
Uso: .venv/bin/python -I scripts/13_cascada_figuras.py
"""
import json, pathlib, csv, re
import numpy as np, rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from rasterio import features
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import shape, Point
from shapely.ops import transform as stransform, unary_union
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
import os
DAT = pathlib.Path(os.environ.get("CASCADA_DATOS", ROOT / "estudios/la-cascada/datos"))
FIG = pathlib.Path(os.environ.get("CASCADA_FIG", ROOT / "estudios/la-cascada/figuras")); FIG.mkdir(parents=True, exist_ok=True)
DEM = ROOT / "descargas/dem_recortes/santa_cruz_dem.tif"
T = Transformer.from_crs(4326, 32715, always_xy=True).transform

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                     "savefig.dpi": 220, "savefig.bbox": "tight", "axes.spines.top": False, "axes.spines.right": False})
C_BARRIO, C_RUTA, C_CUENCA, C_AGUA, C_QUEB = "#d62728", "#7b2cbf", "#111111", "#1f78b4", "#2b8cbe"
TERR = LinearSegmentedColormap.from_list("terr", ["#e8e2c8", "#c9c08f", "#9bb06f", "#5f8f4e", "#3f6b3a", "#6b5a45", "#9c8f80"])


def gj(name, base=DAT):
    p = base / name
    return json.loads(p.read_text())["features"] if p.exists() else []

def utm(g): return stransform(T, g)

def dem_utm():
    with rasterio.open(DEM) as s:
        tr, w, h = calculate_default_transform(s.crs, "EPSG:32715", s.width, s.height, *s.bounds, resolution=30)
        z = np.full((h, w), np.nan, "float32")
        reproject(s.read(1).astype("float32"), z, src_transform=s.transform, src_crs=s.crs, src_nodata=-9999,
                  dst_transform=tr, dst_crs="EPSG:32715", dst_nodata=np.nan, resampling=Resampling.bilinear)
    return z, tr

Z, TR = dem_utm()

def crop(xmin, ymin, xmax, ymax):
    c0, r0 = ~TR * (xmin, ymax); c1, r1 = ~TR * (xmax, ymin)
    r0, r1, c0, c1 = int(r0), int(np.ceil(r1)), int(c0), int(np.ceil(c1))
    z = Z[r0:r1, c0:c1].copy()
    xs = TR.c + TR.a * (np.arange(c0, c1) + .5); ys = TR.f + TR.e * (np.arange(r0, r1) + .5)
    return z, xs, ys

def zline(geom, z, xs, ys, off=8):
    """Coordenadas 3D de una línea (o borde) sobre la superficie."""
    out = []
    lines = [geom] if geom.geom_type in ("LineString", "LinearRing") else list(getattr(geom, "geoms", [geom]))
    for ln in lines:
        if ln.geom_type == "Polygon": ln = ln.exterior
        ln = ln.segmentize(15)
        X, Y = np.array(ln.coords)[:, 0], np.array(ln.coords)[:, 1]
        ci = np.clip(((X - xs[0]) / (xs[1] - xs[0])).round().astype(int), 0, len(xs) - 1)
        ri = np.clip(((Y - ys[0]) / (ys[1] - ys[0])).round().astype(int), 0, len(ys) - 1)
        out.append((X, Y, np.nan_to_num(z[ri, ci], nan=0) + off))
    return out

def surface_colors(z, mask_in=None, vmax=None, dx=30):
    ls = LightSource(azdeg=315, altdeg=40)
    zz = np.nan_to_num(z, nan=0)
    vmax = vmax or np.nanpercentile(z, 99)
    rgb = ls.shade(zz, cmap=TERR, vert_exag=2, blend_mode="soft", vmin=0, vmax=vmax, dx=dx, dy=dx)
    sea = (zz <= 0.5)
    rgb[sea] = [0.78, 0.86, 0.93, 1]
    if mask_in is not None:                       # fuera de la cuenca: desaturado
        g = rgb[..., :3].mean(-1, keepdims=True)
        rgb[~mask_in & ~sea, :3] = 0.55 * g[~mask_in & ~sea] + 0.45 * 0.92
    return rgb



def barrio_utm():
    """Polígono del barrio: unión de OSM «La Cascada» y CGREG «LA CASCADA» (como en 12_cascada_analisis.py)."""
    a = shape(next(f for f in gj("zonas_pobladas.geojson", ROOT / "capas/final") if f["properties"].get("nombre") == "La Cascada")["geometry"])
    b = [shape(f["geometry"]) for f in gj("barrios.geojson", ROOT / "capas/final") if f["properties"].get("nombre") == "LA CASCADA"]
    return utm(unary_union([a.buffer(0)] + [g.buffer(0) for g in b]))

def ruta(lado, cota, rama="rama 2", corte=3.0):
    """Trazado de desvío elegido (UTM) de rutas_desvio.geojson."""
    for f in gj("rutas_desvio.geojson"):
        q = f["properties"]
        if q.get("lado") == lado and q.get("cota_toma_m") == cota and q.get("rama") == rama and q.get("corte_max_admitido_m") == corte:
            return utm(shape(f["geometry"])), q
    return None, None

def fig_3d_cuenca():
    cu = unary_union([utm(shape(f["geometry"])).buffer(1) for f in gj("cuenca_cascada.geojson")])
    barrio = barrio_utm()
    xmin, ymin, xmax, ymax = cu.bounds
    xmin -= 1200; xmax += 1200; ymin -= 1500; ymax += 400
    z, xs, ys = crop(xmin, ymin, xmax, ymax)
    st = 2                                                     # 60 m para el render
    z, xs, ys = z[::st, ::st], xs[::st], ys[::st]
    tr2 = rasterio.transform.from_origin(xs[0] - 30 * st / 2, ys[0] + 30 * st / 2, 30 * st, 30 * st)
    inside = features.rasterize([(cu, 1)], out_shape=z.shape, transform=tr2).astype(bool)
    X, Y = np.meshgrid(xs, ys)
    fig = plt.figure(figsize=(9, 7.2)); ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    ax.plot_surface((X - xs[0]) / 1000, (Y - ys[-1]) / 1000, np.nan_to_num(z, nan=0), facecolors=surface_colors(z, inside),
                    rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    def draw(geom, **kw):
        for x, y, zz in zline(geom, z, xs, ys, off=15):
            ax.plot((x - xs[0]) / 1000, (y - ys[-1]) / 1000, zz, zorder=10, **kw)
    draw(cu, color=C_CUENCA, lw=1.4, label="Cuenca que drena a La Cascada (42 km²)")
    for f in gj("cauce_principal.geojson"):
        draw(utm(shape(f["geometry"])), color=C_QUEB, lw=1.6, label="Cauces principales (dos ramas, D8)")
    g, _ = ruta("ESTE", 40)
    if g: draw(g, color=C_RUTA, lw=2.2, label="Interceptor hipotético al este (toma a 40 m)")
    draw(barrio, color=C_BARRIO, lw=2.5, label="Barrio La Cascada")
    h, l = ax.get_legend_handles_labels(); d = dict(zip(l, h))
    ax.legend(d.values(), d.keys(), loc="upper left", fontsize=8, frameon=False)
    ax.set_box_aspect(((xs[-1] - xs[0]), (ys[0] - ys[-1]), 900 * 3.5)); ax.view_init(elev=32, azim=-112)
    ax.set_xlabel("E (km)"); ax.set_ylabel("N (km)"); ax.set_zlabel("Cota (m)")
    ax.set_title("Cuenca aportante a La Cascada vista desde el sur-suroeste (exageración vertical ≈3,5×)")
    fig.text(0.5, 0.04, "Fuente: Copernicus GLO-30 (DSM, 30 m, remuestreado a 60 m para el render); cuenca y cauce: modelo D8 propio.", ha="center", fontsize=7, color="#555")
    fig.savefig(FIG / "f3d_cuenca.png"); plt.close(fig)


def fig_3d_barrio():
    barrio = barrio_utm()
    cx, cy = barrio.centroid.x, barrio.centroid.y
    R = 900
    z, xs, ys = crop(cx - R, cy - R, cx + R, cy + R)
    # interpolación bicúbica ×4 solo para suavizar el render (no añade información)
    from scipy.ndimage import zoom
    k = 4; zf = zoom(np.nan_to_num(z, nan=0), k, order=3)
    xf = np.linspace(xs[0], xs[-1], zf.shape[1]); yf = np.linspace(ys[0], ys[-1], zf.shape[0])
    X, Y = np.meshgrid(xf, yf)
    fig = plt.figure(figsize=(9, 7)); ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    rgb = surface_colors(zf, vmax=60, dx=30 / k)
    nivel = 13.0
    manchas = [utm(shape(f["geometry"])) for f in gj(f"mancha_{int(nivel)}m.geojson")]
    if manchas:
        tr2 = rasterio.transform.from_origin(xf[0], yf[0], xf[1] - xf[0], yf[0] - yf[1])
        wet = features.rasterize([(g, 1) for g in manchas], out_shape=zf.shape, transform=tr2).astype(bool) & (zf < nivel)
        rgb[wet, :3] = 0.35 * rgb[wet, :3] + 0.65 * np.array([0.12, 0.47, 0.71])
    ax.plot_surface(X - cx, Y - cy, zf, facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    for x, y, zz in zline(barrio, zf, xf, yf, off=1.5):
        ax.plot(x - cx, y - cy, zz, zorder=10, color=C_BARRIO, lw=2.2, label="Barrio La Cascada (OSM ∪ CGREG)")
    g, _ = ruta("ESTE", 40)
    if g:
            g = g.intersection(Point(cx, cy).buffer(R * 0.98))
            if not g.is_empty:
                for x, y, zz in zline(g, zf, xf, yf, off=2):
                    ax.plot(x - cx, y - cy, zz, zorder=10, color=C_RUTA, lw=2, label="Interceptor hipotético")
    h, l = ax.get_legend_handles_labels(); d = dict(zip(l, h))
    if manchas:
        from matplotlib.patches import Patch
        d[f"Llenado hasta ≈{nivel:.0f} m (rebose; compatible con el testimonio de ≈2 m)"] = Patch(color=C_AGUA)
    ax.legend(d.values(), d.keys(), loc="upper left", fontsize=8, frameon=False)
    ax.set_box_aspect((2 * R, 2 * R, 60 * 12)); ax.view_init(elev=30, azim=-120)
    ax.set_xlabel("E (m)"); ax.set_ylabel("N (m)"); ax.set_zlabel("Cota (m)"); ax.set_zlim(0, 70)
    ax.set_title("La Cascada: depresión al pie del escarpe (exageración vertical ≈12×)")
    fig.text(0.5, 0.04, "Fuente: Copernicus GLO-30 (DSM 30 m, interpolado ×4 solo para el render; incluye vegetación y edificios).", ha="center", fontsize=7, color="#555")
    fig.savefig(FIG / "f3d_barrio.png"); plt.close(fig)



def capa_bbox(path, bbox, filtro=None):
    from shapely.geometry import box
    b = box(*bbox); out = []
    for f in json.loads(pathlib.Path(path).read_text())["features"]:
        if filtro and not filtro(f["properties"]): continue
        g = utm(shape(f["geometry"]))
        if g.intersects(b): out.append((g, f["properties"]))
    return out

def plot_geom(ax, g, **kw):
    gs = list(getattr(g, "geoms", [g]))
    for x in gs:
        if x.geom_type == "Polygon":
            ax.fill(*x.exterior.xy, **{k: v for k, v in kw.items() if k not in ("lw",)}, lw=kw.get("lw", 0.6))
        elif x.geom_type in ("LineString", "LinearRing"):
            ax.plot(*x.xy, **{k: v for k, v in kw.items() if k not in ("fc", "ec", "alpha_fill")})

def hill2d(ax, xmin, ymin, xmax, ymax, vmax=None, alpha=1.0):
    z, xs, ys = crop(xmin, ymin, xmax, ymax)
    ls = LightSource(azdeg=315, altdeg=45)
    zz = np.nan_to_num(z, nan=0)
    rgb = ls.shade(zz, cmap=TERR, vert_exag=3, blend_mode="soft", vmin=0, vmax=vmax or np.nanpercentile(z, 99.5), dx=30, dy=30)
    rgb[zz <= 0.5] = [0.80, 0.88, 0.94, 1]
    ax.imshow(rgb, extent=(xs[0] - 15, xs[-1] + 15, ys[-1] - 15, ys[0] + 15), origin="upper", alpha=alpha, zorder=0)
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax); ax.set_aspect("equal")
    return z, xs, ys

def km_axes(ax, x0, y0, paso=1000, unidad="km"):
    from matplotlib.ticker import FuncFormatter
    x1, y1 = ax.get_xlim()[1], ax.get_ylim()[1]
    ax.set_xticks(x0 + np.arange(0, x1 - x0 + 1, paso)); ax.set_yticks(y0 + np.arange(0, y1 - y0 + 1, paso))
    f = 1000 if unidad == "km" else 1
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{(v - x0) / f:g}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{(v - y0) / f:g}"))
    ax.set_xlabel(f"{unidad} (UTM 15S, origen relativo)"); ax.set_ylabel(unidad)

def norte(ax):
    ax.annotate("N", xy=(0.96, 0.95), xytext=(0.96, 0.86), xycoords="axes fraction", ha="center", fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.2))

def escala(ax, L=1000, txt="1 km"):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    x = x0 + 0.05 * (x1 - x0); y = y0 + 0.05 * (y1 - y0)
    ax.plot([x, x + L], [y, y], color="k", lw=3, solid_capstyle="butt"); ax.text(x + L / 2, y + 0.015 * (y1 - y0), txt, ha="center", fontsize=8)


def fig_mapa_cuenca():
    from shapely.geometry import box
    cu_f = [f for f in gj("cuenca_cascada.geojson") if f["properties"].get("subcuenca", "").startswith("rama")]
    cu = unary_union([utm(shape(f["geometry"])).buffer(1) for f in gj("cuenca_cascada.geojson")])
    barrio = barrio_utm()
    xmin, ymin, xmax, ymax = cu.bounds; xmin -= 1500; xmax += 2500; ymin -= 1600; ymax += 500
    bb = (xmin, ymin, xmax, ymax)
    fig, ax = plt.subplots(figsize=(7.2, 9))
    hill2d(ax, *bb)
    sc = lambda p: p.get("isla", "Santa Cruz") == "Santa Cruz"
    for g, _ in capa_bbox(ROOT / "export/galapagos/limite_parque.geojson", bb):
        plot_geom(ax, g.boundary if g.geom_type.endswith("Polygon") else g, color="#2e7d32", lw=1.0, ls=(0, (4, 2)), label="Límite Parque Nacional Galápagos")
    for g, _ in capa_bbox(ROOT / "capas/final/zonas_pobladas.geojson", bb, sc):
        plot_geom(ax, g, fc="#9e9e9e", ec="none", alpha=0.55, label="Zona poblada")
    for g, _ in capa_bbox(ROOT / "capas/final/quebradas.geojson", bb, sc):
        plot_geom(ax, g, color=C_QUEB, lw=0.6, label="Quebradas IGM 1:25 000 + OSM")
    cols = ["#000000", "#555555"]
    if len(cu_f) > 1:
        for i, f in enumerate(cu_f):
            g = utm(shape(f["geometry"])); nm = {"rama 1": "Rama norte", "rama 2": "Rama noroeste"}.get(f["properties"].get("subcuenca"), f["properties"].get("subcuenca", ""))
            plot_geom(ax, g.boundary, color=cols[i % 2], lw=1.0, ls="--")
            a = f["properties"].get("area_km2"); ax.text(g.representative_point().x, g.representative_point().y, f"{nm}\n{a} km²" if a else nm, ha="center", fontsize=8, fontweight="bold")
    plot_geom(ax, cu.boundary, color=C_CUENCA, lw=1.6, label="Cuenca que drena a La Cascada")
    for f in gj("cauce_principal.geojson"):
        plot_geom(ax, utm(shape(f["geometry"])), color="#08519c", lw=2, label="Cauces principales (dos ramas, D8)")
    g, _ = ruta("ESTE", 40)
    if g: plot_geom(ax, g, color=C_RUTA, lw=2.2, label="Interceptor hipotético al este (toma a 40 m)")
    g, _ = ruta("OESTE", 80)
    if g: plot_geom(ax, g, color="#e6a700", lw=1.8, ls=":", label="Alternativa oeste (toma a 80 m, rama NO)")
    plot_geom(ax, barrio, fc=C_BARRIO, ec=C_BARRIO, alpha=0.9, label="Barrio La Cascada")
    h, l = ax.get_legend_handles_labels(); d = dict(zip(l, h))
    ax.legend(d.values(), d.keys(), loc="upper left", fontsize=7.5, framealpha=0.9)
    km_axes(ax, xmin, ymin, 2000); norte(ax); escala(ax, 2000, "2 km")
    ax.set_title("Cuenca aportante, quebradas y trazados de desvío evaluados")
    fig.text(0.5, 0.01, "Fuentes: Copernicus GLO-30; IGM 1:25 000; OpenStreetMap; DPNG/CGREG (límite PNG). Proyección UTM 15S.", ha="center", fontsize=7, color="#555")
    fig.savefig(FIG / "f_mapa_cuenca.png"); plt.close(fig)


def fig_mapa_barrio():
    barrio = barrio_utm(); cx, cy = barrio.centroid.x, barrio.centroid.y
    R = 1300; bb = (cx - R, cy - 1500, cx + R, cy + 900)
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    hill2d(ax, *bb, vmax=80, alpha=0.9)
    # curvas cada 5 m a partir del DSM
    z, xs, ys = crop(*bb)
    cs = ax.contour(xs, ys, z, levels=np.arange(5, 80, 5), colors="#5d4037", linewidths=0.35, alpha=0.7)
    ax.clabel(cs, levels=[10, 15, 20, 30, 40, 60], fontsize=6, fmt="%d m")
    sc = lambda p: p.get("isla", "Santa Cruz") == "Santa Cruz"
    for g, _ in capa_bbox(ROOT / "capas/final/edificios_exposicion.geojson", bb, sc):
        plot_geom(ax, g, fc="#424242", ec="none", alpha=0.75, label="Edificaciones (OSM + Google Open Buildings)")
    for g, _ in capa_bbox(ROOT / "export/galapagos/vias.geojson", bb):
        plot_geom(ax, g, color="#ffffff", lw=0.8, alpha=0.9)
    for f in gj("mancha_14m.geojson"):
        g = utm(shape(f["geometry"]))
        plot_geom(ax, g.boundary, color="#08519c", lw=1.1, ls="--", label="Cota 14 m: lámina hipotética si la salida se obstruye (no observada)")
    for f in gj("mancha_13m.geojson"):
        plot_geom(ax, utm(shape(f["geometry"])), fc="#4292c6", ec="#4292c6", alpha=0.5, lw=0.5, label="Llenado hasta ≈13 m (rebose; compatible con el testimonio)")
    for g, _ in capa_bbox(ROOT / "capas/final/quebradas.geojson", bb, sc):
        plot_geom(ax, g, color=C_QUEB, lw=1.2, label="Quebradas IGM + OSM")
    urb = DAT / "urbano"
    for f in gj("ruta_salida_urbana.geojson", urb):
        plot_geom(ax, utm(shape(f["geometry"])), color="#00897b", lw=2.2, ls="--", label="Salida natural del agua hacia el mar")
    ESTILO = {"rebose": dict(marker="^", color="#e65100", ms=13, zorder=9, label="Umbral que fija la cota de rebose (+1,4 m)"),
              "umbral topográfico": dict(marker="^", color="#ffb74d", ms=6, label="Otro umbral (cabecera de Marchena, +3 m; parte puede ser techos)"),
              "cruce de vía transversal": dict(marker="o", color="#fdd835", ms=5, label="Cruce de vía sobre la salida natural"),
              "edificación sobre el cauce natural": dict(marker="s", color="#e65100", ms=3.5, label="Edificación sobre la salida natural"),
              "desembocadura": dict(marker="*", color="#00897b", ms=11, label="Llegada al mar")}
    for f in gj("tapones.geojson", urb):
        g = utm(shape(f["geometry"])); p = g.representative_point()
        tipo = f["properties"].get("tipo")
        if tipo == "umbral topográfico" and "rebose" in (f["properties"].get("nombre") or "").lower(): tipo = "rebose"
        st = ESTILO.get(tipo, dict(marker="x", color="k", ms=5, label="Otro"))
        st.setdefault("zorder", 6); ax.plot(p.x, p.y, mec="k", mew=0.5, ls="none", **st)
    g, _ = ruta("ESTE", 40)
    if g: plot_geom(ax, g, color=C_RUTA, lw=2, label="Interceptor hipotético (toma a 40 m)")
    plot_geom(ax, barrio.boundary, color=C_BARRIO, lw=2, label="Barrio La Cascada (OSM ∪ CGREG)")
    h, l = ax.get_legend_handles_labels(); d = dict(zip(l, h))
    fig.legend(d.values(), d.keys(), loc="lower center", bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=7, frameon=False)
    km_axes(ax, bb[0], bb[1], 500, "m"); norte(ax); escala(ax, 500, "500 m")
    ax.set_title("La Cascada: relieve, edificaciones, llenado de la depresión y salida natural del agua")
    fig.text(0.5, -0.15, "Curvas cada 5 m derivadas del DSM GLO-30 (incluye edificios y vegetación: ±2–4 m). Manchas: llenado estático tipo «bañera», no simulación hidráulica.",
             ha="center", fontsize=7, color="#555")
    fig.savefig(FIG / "f_mapa_barrio.png"); plt.close(fig)


def rcsv(name, base=None):
    p = (base or DAT) / name
    if not p.exists(): return []
    with open(p) as f: return list(csv.DictReader(f))

def num(rows, k): return np.array([float(r[k]) if r[k] not in ("", "None", "nan") else np.nan for r in rows])

def fuente(fig, txt, y=0.0):
    fig.text(0.01, y, txt, fontsize=6.8, color="#555", ha="left", va="bottom")


def fig_perfil_cauce():
    rows = rcsv("perfil_cauce.csv")
    fig, ax = plt.subplots(figsize=(8, 3.8)); ax2 = ax.twinx()
    nombres = {"rama 1": "Rama norte (29,5 km²)", "rama 2": "Rama noroeste (12,2 km²)"}
    for rama, c in (("rama 1", "#08519c"), ("rama 2", "#6baed6")):
        r = [x for x in rows if x["rama"] == rama]
        if not r: continue
        d = num(r, "distancia_m") / 1000; z = num(r, "cota_m"); a = num(r, "area_acumulada_km2")
        ax.plot(d, z, color=c, lw=1.8, label=f"Cota del cauce, {nombres[rama]}")
        ax2.plot(d, a, color=c, lw=1, ls="--", label=f"Área acumulada, {nombres[rama]}")
    ax.set_xlabel("Distancia desde la cabecera (km)"); ax.set_ylabel("Cota (m s. n. m.)"); ax2.set_ylabel("Área drenada acumulada (km²)")
    ax2.spines["right"].set_visible(True)
    ax.axhspan(10, 18, color=C_BARRIO, alpha=0.08); ax.text(ax.get_xlim()[1] * 0.99, 22, "La Cascada (10,5–18 m)", ha="right", fontsize=7.5, color=C_BARRIO)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="center left", frameon=False)
    ax.set_title("Perfil longitudinal de los cauces principales hasta la entrada al barrio")
    ax.grid(alpha=0.25)
    fuente(fig, "Cauce D8 sobre GLO-30 con quebradas IGM quemadas. Cotas del DSM (incluye vegetación).", -0.03)
    fig.savefig(FIG / "f_perfil_cauce.png"); plt.close(fig)


def fig_secciones():
    rows = rcsv("secciones_barrio.csv")
    perfiles = list(dict.fromkeys(r["perfil"] for r in rows))
    ns = [p for p in perfiles if p.startswith("N-S")]; eo = [p for p in perfiles if p.startswith("E-O")]
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, grupo, tit, xl in ((axs[0], ns, "Perfiles norte–sur", "← Norte   distancia al centro (m)   Sur →"),
                               (axs[1], eo, "Perfiles este–oeste", "← Este   distancia al centro (m)   Oeste →")):
        def etiqueta(pfl):
            k = pfl.split(" ", 1)[1] if " " in pfl else pfl
            m = re.match(r"([xy])([+-]\d+)m", k)
            if not m: return k
            v = int(m.group(2))
            if v == 0: return "por el centro"
            lado = ("este" if v > 0 else "oeste") if m.group(1) == "x" else ("norte" if v > 0 else "sur")
            return f"{abs(v)} m al {lado}"
        for i, pfl in enumerate(grupo):
            r = [x for x in rows if x["perfil"] == pfl]
            ax.plot(num(r, "distancia_m"), num(r, "cota_m"), lw=1.8 if "+0m" in pfl else 1, color={0: "#777", 1: "#000", 2: "#bbb"}[i % 3],
                    label=etiqueta(pfl))
        ax.axhline(12.95, color=C_AGUA, lw=1, ls="--"); ax.text(ax.get_xlim()[0], 13.3, " cota de rebose ≈13,0 m", fontsize=7, color=C_AGUA)
        b = barrio_utm(); c = b.centroid; x0, y0, x1, y1 = b.bounds
        if grupo is ns: ax.axvspan(-(y1 - c.y), (c.y - y0), color=C_BARRIO, alpha=0.07)
        else: ax.axvspan(-(x1 - c.x), (c.x - x0), color=C_BARRIO, alpha=0.07)
        ax.set_title(tit); ax.set_xlabel(xl); ax.grid(alpha=0.25); ax.legend(fontsize=7, frameon=False)
    axs[0].set_ylabel("Cota (m)")
    fuente(fig, "Secciones de ±600 m por el centro del barrio sobre el DSM GLO-30 (interpolación bilineal). Banda roja: ancho aproximado del barrio.", -0.04)
    fig.savefig(FIG / "f_secciones.png"); plt.close(fig)


def fig_cota_volumen():
    r = rcsv("curva_cota_volumen.csv")
    if not r: return
    z = num(r, "cota_m"); v = num(r, "volumen_m3"); e = num(r, "edificios_afectados"); pb = num(r, "poblacion_estimada")
    fig, ax = plt.subplots(figsize=(8, 4)); ax2 = ax.twinx(); ax2.spines["right"].set_visible(True)
    ax.plot(z, v / 1e3, color=C_AGUA, lw=2, marker="o", ms=3, label="Volumen bajo la cota (miles de m³; no almacenado sobre 12,95 m)")
    ax2.plot(z, e, color="#444", lw=1.5, marker="s", ms=3, label="Edificaciones alcanzadas")
    ax2.plot(z, pb / 4, color="#999", lw=1, ls=":", label="Población estimada ÷ 4")
    ax.axvline(12.95, color=C_AGUA, ls="--", lw=1); ax.text(13.05, ax.get_ylim()[1] * 0.45, "rebose\n12,95 m", fontsize=7.5, color=C_AGUA)
    ax.axvspan(12.5, 13.0, color="#fdd", alpha=0.6); ax.text(12.0, ax.get_ylim()[1] * 0.55, "cota según\ntestimonio\n(≈2 m)", fontsize=7, color="#a33", ha="center")
    ax.set_xlabel("Cota de la lámina de agua (m, DSM EGM2008)"); ax.set_ylabel("Volumen (miles de m³)"); ax2.set_ylabel("Edificaciones / población ÷ 4")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc="upper left", bbox_to_anchor=(0.36, 1.0), frameon=False); ax.grid(alpha=0.25)
    ax.set_title("Curva cota–volumen–exposición de la zona baja de La Cascada (llenado estático)")
    fuente(fig, "Sobre la cota 13 m la lámina deja de estar confinada: el agua rebosa hacia la ciudad y el «volumen» es solo indicativo. DSM GLO-30; edificios OSM + Open Buildings; población INEC por manzana.", -0.05)
    fig.savefig(FIG / "f_cota_volumen.png"); plt.close(fig)


def fig_hidrogramas():
    r = rcsv("hidrogramas.csv")
    if not r: return
    t = num(r, "tiempo_h"); cols = [k for k in r[0] if k != "tiempo_h"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.9))
    ax = axs[0]; pal = {"50": "#c6dbef", "100": "#6baed6", "150": "#2171b5", "200": "#08306b"}
    for k in cols:
        if k.startswith("EVENTO") or not k.endswith("CN70"): continue
        P = k.split("mm")[0].lstrip("P"); ax.plot(t, num(r, k), color=pal[P], lw=1.7, label=f"{P} mm/24 h, CN 70")
    for cn, ls in (("60", ":"), ("80", "-.")):
        ax.plot(t, num(r, f"P100mm_CN{cn}"), color=pal["100"], lw=1, ls=ls, label=f"100 mm/24 h, CN {cn}")
    ax.set_xlim(8, 32); ax.set_xlabel("Horas desde el inicio de la tormenta tipo II"); ax.set_ylabel("Caudal en la entrada al barrio (m³/s)")
    ax.set_title("a) Escenarios de diseño"); ax.grid(alpha=0.25); ax.legend(fontsize=7, frameon=False)
    ax = axs[1]
    import datetime as dt, matplotlib.dates as mdates
    t0 = dt.datetime(2026, 10, 30, 22)
    T = [t0 + dt.timedelta(hours=float(x)) for x in t]
    est = {"EVENTO31oct_ecmwf_ifs_9km_cota200_CN76": ("ECMWF 9 km, 110 mm, CN 76 (central)", C_BARRIO, "-", 2),
           "EVENTO31oct_ecmwf_ifs_9km_cota200_CN83": ("ECMWF 9 km, 110 mm, CN 83 (suelo húmedo)", C_BARRIO, ":", 1.2),
           "EVENTO31oct_ecmwf_ifs_9km_thiessen_CN83": ("ECMWF 9 km Thiessen, 117 mm, CN 83", "#7f0000", "--", 1.2),
           "EVENTO31oct_ecmwf_ifs025_cota200_CN76": ("ECMWF 0,25°, 26 mm, CN 76", "#555", "-", 1.4)}
    for k, (lab, c, ls, lw) in est.items():
        if k in r[0]: ax.plot(T, num(r, k), color=c, ls=ls, lw=lw, label=lab)
    ax.set_xlim(t0, t0 + dt.timedelta(hours=22))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b\n%H:%M")); ax.tick_params(axis="x", labelsize=7)
    ax.set_title("b) Evento 30–31 oct 2026 (lluvia de modelo)"); ax.set_xlabel("Hora de Galápagos (UTC−6)"); ax.grid(alpha=0.25); ax.legend(fontsize=7, frameon=False)
    fuente(fig, "SCS-CN + hidrograma unitario SCS con tc de Témez (3,6 h); con tc de Kirpich (1,4 h) los picos serían ≈1,5–1,9 veces mayores. Sin calibrar: no hay aforos, pluviómetros del evento ni curvas IDF.", -0.06)
    fig.tight_layout(); fig.savefig(FIG / "f_hidrogramas.png"); plt.close(fig)


def fig_perfil_interceptor():
    r = rcsv("perfil_interceptor_este.csv")
    if not r: return
    d = num(r, "distancia_m") / 1000; zt = num(r, "cota_terreno_m"); zc = num(r, "cota_canal_m")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.fill_between(d, 0, zt, color="#d9cfb8", label="Terreno (DSM)")
    ax.plot(d, zt, color="#6d5d3f", lw=1)
    ax.plot(d, zc, color=C_RUTA, lw=2, label="Rasante del canal (pendiente ≥ 0,5 %; sin calado)")
    ax.fill_between(d, zc, zt, where=zt > zc, color=C_RUTA, alpha=0.25, label="Corte sobre la rasante (la excavación real suma ≈2,5 m de calado)")
    ax.axhspan(-2, 0, color="#cfe0ee"); ax.set_ylim(-2, max(np.nanmax(zt) + 5, 45))
    ax.set_xlabel("Distancia a lo largo del trazado (km)"); ax.set_ylabel("Cota (m)")
    ax.set_title("Perfil del interceptor hipotético al este (toma a 40 m, rama noroeste)"); ax.grid(alpha=0.25); ax.legend(fontsize=7.5, frameon=False)
    fuente(fig, "Trazado de mínimo corte sobre GLO-30 (corte ≤ 3 m). La incertidumbre vertical del DSM (±2–4 m) es del mismo orden que el corte calculado.", -0.05)
    fig.savefig(FIG / "f_perfil_interceptor.png"); plt.close(fig)


def fig_perfil_cauce_este():
    r = rcsv("perfil_cauce_este.csv")
    if not r: return
    d = num(r, "distancia_m") / 1000; z = num(r, "cota_dsm_m"); zmin = num(r, "cota_min_franja_180m_m"); u = num(r, "umbral_acumulado_desde_barrio_m")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.plot(d, z, color="#6d5d3f", lw=1.4, label="Cota del DSM sobre el trazado cartografiado")
    ax.plot(d, zmin, color=C_AGUA, lw=1.2, label="Cota mínima en una franja de ±90 m")
    if np.isfinite(u).any(): ax.plot(d, u, color=C_BARRIO, lw=1, ls="--", label="Umbral acumulado desde el barrio")
    ax.axhline(12.95, color=C_AGUA, lw=0.8, ls=":"); ax.text(d[-1], 13.5, "rebose del barrio ≈13 m", ha="right", fontsize=7, color=C_AGUA)
    ax.set_xlabel("Distancia a lo largo del trazado OSM desde su extremo oeste (km; el barrio queda a ≈0,5 km)"); ax.set_ylabel("Cota (m)")
    ax.set_title("Cauce cartografiado al pie del escarpe hacia el este: ¿drena por gravedad?"); ax.grid(alpha=0.25); ax.legend(fontsize=7.5, frameon=False)
    fuente(fig, "Si el umbral acumulado supera la cota de rebose del barrio, el agua no puede seguir ese trazado sin excavación (según el DSM, que incluye vegetación).", -0.05)
    fig.savefig(FIG / "f_perfil_cauce_este.png"); plt.close(fig)


LL = DAT / "lluvias"

def fig_lluvias():
    r = rcsv("lluvia_diaria.csv", LL)
    if not r: return
    import datetime as dt
    fechas = sorted({x["fecha"] for x in r})
    D = [dt.date.fromisoformat(f) for f in fechas]
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.8), gridspec_kw=dict(width_ratios=[2.2, 1]))
    ax = axs[0]; w = 0.4
    for j, (pt, c, nm) in enumerate((("puerto_ayora", "#6baed6", "Puerto Ayora (costa)"), ("bellavista", "#08519c", "Bellavista (parte alta)"))):
        ref = {x["fecha"]: float(x["mm"]) for x in r if x["punto"] == pt and x["fuente"].endswith("ecmwf_ifs")}
        y = [ref.get(f, np.nan) for f in fechas]
        x = np.arange(len(fechas)) + (j - 0.5) * w
        ax.bar(x, y, width=w, color=c, label=f"{nm}: ECMWF IFS 9 km")
        otros = [x2 for x2 in r if x2["punto"] == pt and not x2["fuente"].endswith("ecmwf_ifs")]
        for i, f in enumerate(fechas):
            vs = [float(o["mm"]) for o in otros if o["fecha"] == f and o["mm"] not in ("", "nan")]
            if vs: ax.plot([x[i], x[i]], [min(vs), max(vs)], color="#333", lw=0.7)
    ax.plot([], [], color="#333", lw=0.7, label="Rango de otros 6 modelos y ERA5")
    ax.set_xticks(np.arange(len(fechas))[::2]); ax.set_xticklabels([d.strftime("%d-%b") for d in D][::2], rotation=45, ha="right", fontsize=7.5)
    ax.set_ylabel("Precipitación diaria (mm)"); ax.set_title("Lluvia diaria estimada por modelos, 15-oct a 1-nov-2026")
    ax.legend(fontsize=7, frameon=False); ax.grid(axis="y", alpha=0.25)
    c = rcsv("climatologia_cdf_1991_2020.csv", LL)
    ax = axs[1]
    if c:
        for j, (est, col) in enumerate((("puerto-ayora", "#6baed6"), ("bellavista", "#08519c"))):
            q = [x for x in c if x["estacion"] == est]
            m = num(q, "mes"); ax.bar(m + (j - 0.5) * 0.4, num(q, "media_mm"), width=0.4, color=col, label=est.replace("-", " ").title())
        ax.set_xticks(range(1, 13)); ax.set_xticklabels(list("EFMAMJJASOND"), fontsize=7.5)
        ax.set_title("Climatología medida (FCD; P. Ayora 1991–2020, Bellavista 1991–2019)", fontsize=8.5); ax.set_ylabel("Media mensual (mm)"); ax.legend(fontsize=7, frameon=False); ax.grid(axis="y", alpha=0.25)
    fuente(fig, "Izq.: estimaciones de modelos vía Open-Meteo, días en UTC−5 (no son mediciones; no hay datos medidos públicos del evento). Der.: estaciones de la Fundación Charles Darwin, medias 1991–2020.", -0.08)
    fig.tight_layout(); fig.savefig(FIG / "f_lluvias.png"); plt.close(fig)


def fig_lluvia_horaria():
    r = rcsv("lluvia_horaria.csv", LL)
    if not r: return
    import datetime as dt
    fig, ax = plt.subplots(figsize=(8, 3.4)); ax2 = ax.twinx(); ax2.spines["right"].set_visible(True)
    for pt, c, nm in (("puerto_ayora", "#6baed6", "Celda costera"), ("bellavista", "#08519c", "Celda de la parte alta")):
        q = [x for x in r if x["punto"] == pt and x["fuente"].endswith("ecmwf_ifs")]
        t = [dt.datetime.fromisoformat(x["fecha_hora_local"]) - dt.timedelta(hours=1) for x in q]; mm = num(q, "mm")  # Open-Meteo pedido en UTC−5 → Galápagos UTC−6
        sel = [i for i, tt in enumerate(t) if dt.datetime(2026, 10, 30, 12) <= tt <= dt.datetime(2026, 11, 1, 12)]
        t = [t[i] for i in sel]; mm = mm[sel]
        ax.bar(t, mm, width=1 / 24 * (0.45), align="edge" if pt == "bellavista" else "center", color=c, label=f"{nm}: mm/h")
        ax2.plot(t, np.nancumsum(mm), color=c, lw=1.4, ls="--", label=f"{nm}: acumulado")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M")); plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7.5)
    ax.set_ylabel("Intensidad (mm/h)"); ax2.set_ylabel("Acumulado (mm)")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=7, frameon=False, loc="upper left")
    ax.set_title("Hietograma horario estimado del evento (ECMWF IFS 9 km; hora de Galápagos, UTC−6)"); ax.grid(alpha=0.25)
    fuente(fig, "Estimación de modelo (celda de 9 km), no medición. Cada barra es la lluvia de la hora que termina en la marca. Los modelos suelen subestimar los máximos convectivos y orográficos en islas pequeñas.", -0.16)
    fig.savefig(FIG / "f_lluvia_horaria.png"); plt.close(fig)


if __name__ == "__main__":
    import sys
    quien = sys.argv[1:] or [n for n in dir() if n.startswith("fig_")]
    for n in quien:
        print("→", n); globals()[n]()
