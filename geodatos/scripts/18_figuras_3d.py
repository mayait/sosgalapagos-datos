"""Vistas 3D (matplotlib) para los estudios de Santa Cruz y San Cristóbal, desde varios puntos de vista.

Uso: .venv/bin/python -I scripts/18_figuras_3d.py [nombre_vista ...]
Salida: estudios/<isla>/figuras/3d_<vista>.png
Las capas que aún no existan (cruces, puntos de inundación…) se omiten sin error.
"""
import json, pathlib, sys, csv
import numpy as np, rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from rasterio import features
from scipy.ndimage import zoom
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import shape, Point, box
from shapely.ops import unary_union
from shapely import transform as shp_transform
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIMA = ROOT.parent / "clima"
T = Transformer.from_crs(4326, 32715, always_xy=True)
TERR = LinearSegmentedColormap.from_list("terr", ["#e8e2c8", "#c9c08f", "#9bb06f", "#5f8f4e", "#3f6b3a", "#6b5a45", "#9c8f80"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "savefig.dpi": 200, "savefig.bbox": "tight"})
DEM = {"santa-cruz": ROOT / "descargas/dem_recortes/santa_cruz_dem.tif", "san-cristobal": ROOT / "descargas/dem_recortes/san_cristobal_dem.tif"}
_cache = {}


def utm(g):
    return shp_transform(g, lambda xy: np.column_stack(T.transform(xy[:, 0], xy[:, 1])))


def gj(p):
    p = pathlib.Path(p)
    return [f for f in json.loads(p.read_text())["features"] if f.get("geometry")] if p.exists() else []


def dem(isla):
    if isla not in _cache:
        with rasterio.open(DEM[isla]) as s:
            tr, w, h = calculate_default_transform(s.crs, "EPSG:32715", s.width, s.height, *s.bounds, resolution=30)
            z = np.full((h, w), np.nan, "float32")
            reproject(s.read(1).astype("float32"), z, src_transform=s.transform, src_crs=s.crs, src_nodata=-9999,
                      dst_transform=tr, dst_crs="EPSG:32715", dst_nodata=np.nan, resampling=Resampling.bilinear)
        _cache[isla] = (z, tr)
    return _cache[isla]


def crop(isla, x0, y0, x1, y1):
    Z, TR = dem(isla)
    c0, r0 = ~TR * (x0, y1); c1, r1 = ~TR * (x1, y0)
    r0, r1, c0, c1 = max(int(r0), 0), int(np.ceil(r1)), max(int(c0), 0), int(np.ceil(c1))
    z = Z[r0:r1, c0:c1].copy()
    xs = TR.c + TR.a * (np.arange(c0, c0 + z.shape[1]) + .5); ys = TR.f + TR.e * (np.arange(r0, r0 + z.shape[0]) + .5)
    return z, xs, ys


def render(isla, centro, ancho, alto, elev, azim, vexag, titulo, salida, capas=(), paso=1, interp=1,
           agua=None, marcadores=(), barras=(), nota=""):
    """centro=(lon,lat); ancho/alto en m; capas=[(geom_wgs84, estilo)]; marcadores=[(lon,lat,txt,color)];
    barras=[(lon,lat,altura_m,txt,color)] columnas verticales (p. ej., lluvia medida)."""
    cx, cy = T.transform(*centro)
    z, xs, ys = crop(isla, cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2)
    z = np.nan_to_num(z, nan=0)[::paso, ::paso]; xs, ys = xs[::paso], ys[::paso]
    if interp > 1:
        z = zoom(z, interp, order=3); xs = np.linspace(xs[0], xs[-1], z.shape[1]); ys = np.linspace(ys[0], ys[-1], z.shape[0])
    dx = abs(xs[1] - xs[0])
    vmax = max(np.percentile(z, 99.5), 30)
    rgb = LightSource(azdeg=315, altdeg=40).shade(z, cmap=TERR, vert_exag=2, blend_mode="soft", vmin=0, vmax=vmax, dx=dx, dy=dx)
    rgb[z <= 0.5] = [0.80, 0.88, 0.94, 1]
    leyenda = {}
    if agua is not None:
        geoms, nivel, etiqueta = agua
        tr2 = rasterio.transform.from_origin(xs[0] - dx / 2, ys[0] + dx / 2, dx, dx)
        g = [utm(x) for x in geoms]
        if g:
            wet = features.rasterize([(x, 1) for x in g], out_shape=z.shape, transform=tr2).astype(bool) & (z < nivel)
            rgb[wet, :3] = 0.3 * rgb[wet, :3] + 0.7 * np.array([0.13, 0.45, 0.75])
            leyenda[etiqueta] = Patch(color="#2272bf")
    X, Y = np.meshgrid((xs - cx), (ys - cy))
    fig = plt.figure(figsize=(9.5, 7.2)); ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    ax.plot_surface(X, Y, z, facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)

    def zat(x, y):
        ci = np.clip(np.round((x - xs[0]) / (xs[1] - xs[0])).astype(int), 0, len(xs) - 1)
        ri = np.clip(np.round((y - ys[0]) / (ys[1] - ys[0])).astype(int), 0, len(ys) - 1)
        return z[ri, ci]

    marco = box(cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2)
    for geom, est in capas:
        g = utm(geom).intersection(marco)
        if g.is_empty: continue
        partes = list(getattr(g, "geoms", [g]))
        for p in partes:
            lines = [p.exterior] if p.geom_type == "Polygon" else [p] if p.geom_type in ("LineString", "LinearRing") else []
            if p.geom_type == "Point":
                ax.scatter([p.x - cx], [p.y - cy], [zat(np.array([p.x]), np.array([p.y]))[0] + est.get("off", 6)],
                           s=est.get("s", 30), c=est["color"], marker=est.get("marker", "o"), edgecolors="k", linewidths=0.5, zorder=12, depthshade=False)
                continue
            for ln in lines:
                ln = ln.segmentize(max(dx / 2, 10)); a = np.array(ln.coords)
                ax.plot(a[:, 0] - cx, a[:, 1] - cy, zat(a[:, 0], a[:, 1]) + est.get("off", 6), color=est["color"],
                        lw=est.get("lw", 1.5), ls=est.get("ls", "-"), zorder=10)
        if est.get("label"):
            leyenda[est["label"]] = Line2D([], [], color=est["color"], lw=est.get("lw", 1.5), ls=est.get("ls", "-"),
                                           marker=est.get("marker") if "s" in est else None, linestyle=est.get("ls", "-") if "s" not in est else "none")
    for lon, lat, txt, col in marcadores:
        x, y = T.transform(lon, lat)
        if not marco.contains(Point(x, y)): continue
        z0 = zat(np.array([x]), np.array([y]))[0]
        h = vexag_offset = (z.max() - z.min()) * 0.12 + 10
        ax.plot([x - cx] * 2, [y - cy] * 2, [z0, z0 + h], color="k", lw=0.8, zorder=13)
        ax.text(x - cx, y - cy, z0 + h, txt, fontsize=7.5, color=col, fontweight="bold", zorder=14, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, lw=0.6, alpha=0.9))
    for lon, lat, hh, txt, col in barras:
        x, y = T.transform(lon, lat)
        if not marco.contains(Point(x, y)): continue
        z0 = zat(np.array([x]), np.array([y]))[0]
        ax.plot([x - cx] * 2, [y - cy] * 2, [z0, z0 + hh], color=col, lw=7, solid_capstyle="butt", zorder=13, alpha=0.9)
        ax.text(x - cx, y - cy, z0 + hh + 8, txt, fontsize=7.5, zorder=14, ha="center", va="bottom", color="#08306b", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#08306b", lw=0.5, alpha=0.9))
    if leyenda:
        ax.legend(leyenda.values(), leyenda.keys(), loc="upper left", fontsize=7.5, frameon=False)
    ax.set_box_aspect((ancho, alto, max(z.max(), 1) * vexag), zoom=1.3); ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(titulo, fontsize=10)
    rel = ("DTM 1 m SGIAR promediado a 30 m en Puerto Ayora, el escarpe y Bellavista; Copernicus GLO-30 (DSM) fuera"
           if isla == "santa-cruz" and (ROOT / "datos/dtm_sgiar/dtm_sgiar_1m.vrt").exists() else "Copernicus GLO-30 (DSM 30 m; incluye vegetación y edificios)")
    pie = f"{rel}, exageración vertical ≈{vexag:g}×. Vista con azimut {azim % 360:.0f}° y elevación {elev}°. {nota}"
    fig.text(0.5, 0.06, pie, ha="center", fontsize=6.8, color="#555", wrap=True)
    salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida); plt.close(fig)
    print("  ", salida.relative_to(ROOT))


# ---------- capas comunes ----------
LC = ROOT / "estudios/la-cascada/datos"; SCZ = ROOT / "estudios/santa-cruz/datos"; SCB = ROOT / "estudios/san-cristobal/datos"
_RC = json.loads((LC / "resumen.json").read_text()) if (LC / "resumen.json").exists() else {}
_COTA_M = _RC.get("depresion", {}).get("cotas_usadas", {}).get("manchas", {}).get("mancha_rebose.geojson", 13.0)
EST_C = {"color": "#111", "lw": 1.6, "label": f"Cuenca que drena a La Cascada ({_RC.get('cuenca', {}).get('area_aportante_km2', 42):.0f} km²)"}


def barrio():
    a = [shape(f["geometry"]) for f in gj(ROOT / "capas/final/zonas_pobladas.geojson") if f["properties"].get("nombre") == "La Cascada"]
    b = [shape(f["geometry"]) for f in gj(ROOT / "capas/final/barrios.geojson") if f["properties"].get("nombre") == "LA CASCADA"]
    return unary_union([g.buffer(0) for g in a + b])


def cuenca():
    return unary_union([shape(f["geometry"]).buffer(1e-5) for f in gj(LC / "cuenca_cascada.geojson")])


def interceptor():
    for f in gj(LC / "rutas_desvio.geojson"):
        q = f["properties"]
        if q.get("lado") == "ESTE" and q.get("cota_toma_m") == 40 and q.get("rama") == "rama 2" and q.get("corte_max_admitido_m") == 3.0:
            return shape(f["geometry"])


def quebradas(isla, bb_lonlat):
    b = box(*bb_lonlat)
    return [shape(f["geometry"]) for f in gj(ROOT / "capas/final/quebradas.geojson")
            if f["properties"].get("isla") == isla and shape(f["geometry"]).intersects(b)]


def zonas(isla, bb_lonlat):
    b = box(*bb_lonlat)
    return [shape(f["geometry"]) for f in gj(ROOT / "capas/final/zonas_pobladas.geojson")
            if f["properties"].get("isla") == isla and shape(f["geometry"]).intersects(b)]


def puntos(path, n=None, campo=None, valores=None):
    fs = gj(path)
    if campo: fs = [f for f in fs if str(f["properties"].get(campo)) in valores]
    return [shape(f["geometry"]).representative_point() if not shape(f["geometry"]).geom_type == "Point" else shape(f["geometry"]) for f in fs][:n]


def estaciones():
    out = []
    p = CLIMA / "datos/ierse-wsn/diario.csv"
    tot = {}
    if p.exists():
        for r in csv.DictReader(open(p)):
            if r["fecha"] == "2026-10-30": tot[r["estacion_id"]] = float(r["lluvia_mm"])
    for f in gj(CLIMA / "datos/ierse-wsn/estaciones.geojson"):
        q = f["properties"]; lon, lat = f["geometry"]["coordinates"][:2]
        out.append((lon, lat, q.get("node_name") or q.get("nombre") or q.get("estacion"), tot.get(q.get("node_id") or q.get("estacion_id") or q.get("id"))))
    return out


def capas_sc(bb, con_cuenca=True, con_interceptor=True):
    cs = []
    for z in zonas("Santa Cruz", bb): cs.append((z, {"color": "#7a7a7a", "lw": 0.6, "label": "Zona poblada", "off": 3}))
    for q in quebradas("Santa Cruz", bb): cs.append((q, {"color": "#2b8cbe", "lw": 0.9, "label": "Quebradas (IGM + OSM)", "off": 4}))
    if con_cuenca and gj(LC / "cuenca_cascada.geojson"): cs.append((cuenca(), EST_C))
    if con_interceptor and interceptor() is not None:
        cs.append((interceptor(), {"color": "#7b2cbf", "lw": 2.2, "label": "Interceptor hipotético (toma a ≈40 m)"}))
    cs.append((barrio(), {"color": "#d62728", "lw": 2.4, "label": "Barrio La Cascada"}))
    for p in puntos(SCZ / "cruces.geojson", campo="prioridad", valores=["alta"]):
        cs.append((p, {"color": "#fdd835", "marker": "o", "s": 14, "label": "Cruce quebrada–vía (prioridad alta)"}))
    for p in puntos(SCZ / "puntos_inundacion.geojson", campo="prioridad", valores=["Alta"]):
        cs.append((p, {"color": "#e65100", "marker": "^", "s": 45, "label": "Punto potencial de inundación (prioridad alta)"}))
    return cs


def manchas13():
    return [shape(f["geometry"]) for f in gj(LC / "mancha_rebose.geojson")]


VISTAS = {}
def vista(f): VISTAS[f.__name__] = f; return f


@vista
def sc_cuenca_desde_mar():
    bb = (-90.36, -0.76, -90.27, -0.63)
    render("santa-cruz", (-90.316, -0.695), 9000, 14500, 28, -75, 4, "Santa Cruz: cuenca de La Cascada vista desde el mar (sur-sureste)",
           ROOT / "estudios/santa-cruz/figuras/3d_cuenca_desde_mar.png", capas_sc(bb), paso=2,
           marcadores=[(-90.3137, -0.7335, "La Cascada", "#d62728"), (-90.3198, -0.7109, "Tomás de Berlanga", "#e65100"),
                       (-90.3270, -0.6925, "Bellavista", "#333")])


@vista
def sc_desde_parte_alta():
    bb = (-90.36, -0.76, -90.27, -0.63)
    render("santa-cruz", (-90.318, -0.708), 8000, 10000, 38, 100, 6, "Santa Cruz: desde la parte alta hacia Puerto Ayora (mirando al sur)",
           ROOT / "estudios/santa-cruz/figuras/3d_desde_parte_alta.png", capas_sc(bb), paso=2,
           marcadores=[(-90.3137, -0.7335, "La Cascada", "#d62728"), (-90.3198, -0.7109, "Tomás de Berlanga", "#e65100"),
                       (-90.3270, -0.6925, "Bellavista", "#333")])


@vista
def sc_lluvia_medida():
    est = estaciones()
    barras = [(lon, lat, (mm or 0) * 4 + 5, (f"{nm}: {mm:.0f} mm" + (" (dato no fiable)" if "Crocker" in str(nm) else "")) if mm is not None else f"{nm}: s/d", "#2171b5") for lon, lat, nm, mm in est]
    bb = (-90.45, -0.77, -90.25, -0.47)
    cs = [(cuenca(), EST_C)] if gj(LC / "cuenca_cascada.geojson") else []
    cs += [(z, {"color": "#7a7a7a", "lw": 0.6, "label": "Zona poblada", "off": 3}) for z in zonas("Santa Cruz", bb)]
    render("santa-cruz", (-90.345, -0.62), 22000, 32000, 30, -60, 4, "Lluvia MEDIDA el 30-oct-2026 (red IERSE-WSN): columnas proporcionales al total del día",
           ROOT / "estudios/santa-cruz/figuras/3d_lluvia_medida.png", cs, paso=4, barras=barras,
           nota="Totales mínimos: las estaciones dejaron de transmitir hacia las 21:30. Altura de columna ≈4 m por mm (escala del gráfico, no real).")


@vista
def cascada_desde_sur():
    render("santa-cruz", (-90.3137, -0.7345), 2000, 2000, 26, -95, 12, "La Cascada desde el sur: la depresión al pie del escarpe",
           ROOT / "estudios/santa-cruz/figuras/3d_cascada_desde_sur.png", capas_sc((-90.33, -0.75, -90.30, -0.72), con_cuenca=False), interp=4,
           agua=(manchas13(), _COTA_M, f"Llenado hasta ≈{_COTA_M:.0f} m (rebose)"))


@vista
def cascada_desde_noreste():
    render("santa-cruz", (-90.3137, -0.7345), 2000, 2000, 32, 40, 12, "La Cascada desde el noreste (por encima del escarpe)",
           ROOT / "estudios/santa-cruz/figuras/3d_cascada_desde_noreste.png", capas_sc((-90.33, -0.75, -90.30, -0.72), con_cuenca=False), interp=4,
           agua=(manchas13(), _COTA_M, f"Llenado hasta ≈{_COTA_M:.0f} m (rebose)"))


@vista
def cascada_desde_oeste():
    render("santa-cruz", (-90.3137, -0.7345), 2400, 2000, 20, 185, 12, "La Cascada desde el oeste: escarpe norte, vaso y salida hacia la bahía",
           ROOT / "estudios/santa-cruz/figuras/3d_cascada_desde_oeste.png", capas_sc((-90.33, -0.75, -90.30, -0.72), con_cuenca=False), interp=4,
           agua=(manchas13(), _COTA_M, f"Llenado hasta ≈{_COTA_M:.0f} m (rebose)"))


@vista
def tomas_de_berlanga():
    bb = (-90.335, -0.725, -90.305, -0.695)
    render("santa-cruz", (-90.3198, -0.7109), 2400, 2400, 30, -110, 8, "Sector Tomás de Berlanga (vía Puerto Ayora–Bellavista)",
           ROOT / "estudios/santa-cruz/figuras/3d_tomas_de_berlanga.png", capas_sc(bb, con_cuenca=False, con_interceptor=False), interp=3,
           marcadores=[(-90.3198, -0.7109, "Esc. Tomás de Berlanga", "#e65100")])


def capas_scb(bb):
    cs = [(z, {"color": "#7a7a7a", "lw": 0.6, "label": "Zona poblada", "off": 3}) for z in zonas("San Cristóbal", bb)]
    cs += [(q, {"color": "#2b8cbe", "lw": 0.9, "label": "Quebradas (IGM + OSM)", "off": 4}) for q in quebradas("San Cristóbal", bb)]
    for f in gj(SCB / "cuencas.geojson"):
        if f["properties"].get("tipo") == "cuenca de llegada":
            cs.append((shape(f["geometry"]), {"color": "#111", "lw": 1.1, "label": "Cuencas que llegan a zonas pobladas"}))
    for f in gj(SCB / "quebrada_usfq.geojson"):
        g = shape(f["geometry"])
        st = {"color": "#d62728", "lw": 2.2, "label": "Quebrada y cuenca del campus USFQ"} if "Line" in g.geom_type else {"color": "#d62728", "lw": 1.3, "ls": "--", "label": "Quebrada y cuenca del campus USFQ"}
        cs.append((g, st))
    for p in puntos(SCB / "cruces.geojson", campo="prioridad", valores=["alta"]):
        cs.append((p, {"color": "#fdd835", "marker": "o", "s": 14, "label": "Cruce quebrada–vía (prioridad alta)"}))
    for p in puntos(SCB / "puntos_inundacion.geojson"):
        cs.append((p, {"color": "#e65100", "marker": "^", "s": 40, "label": "Punto potencial de inundación"}))
    return cs


@vista
def scb_puerto_desde_mar():
    bb = (-89.66, -0.93, -89.55, -0.86)
    render("san-cristobal", (-89.598, -0.895), 9000, 7500, 28, -120, 5, "San Cristóbal: Puerto Baquerizo Moreno y su cuenca desde el mar (suroeste)",
           ROOT / "estudios/san-cristobal/figuras/3d_puerto_desde_mar.png", capas_scb(bb), paso=1,
           marcadores=[(-89.6089, -0.8955, "USFQ / GSC", "#d62728"), (-89.6150, -0.9020, "Pto. Baquerizo Moreno", "#333")])


@vista
def scb_isla_desde_sur():
    bb = (-89.65, -0.95, -89.40, -0.80)
    render("san-cristobal", (-89.53, -0.88), 26000, 17000, 30, -80, 5, "San Cristóbal: parte habitada, de Puerto Baquerizo Moreno a El Progreso y la parte alta",
           ROOT / "estudios/san-cristobal/figuras/3d_isla_desde_sur.png", capas_scb(bb), paso=3,
           marcadores=[(-89.6089, -0.8955, "USFQ", "#d62728"), (-89.5565, -0.9120, "El Progreso", "#333"),
                       (-89.4790, -0.8930, "El Junco", "#333")])


@vista
def scb_campus_usfq():
    bb = (-89.625, -0.905, -89.595, -0.885)
    render("san-cristobal", (-89.6089, -0.8955), 2400, 2400, 28, -135, 10, "Campus USFQ / Galapagos Science Center: llegada de la quebrada",
           ROOT / "estudios/san-cristobal/figuras/3d_campus_usfq.png", capas_scb(bb), interp=4,
           marcadores=[(-89.6089, -0.8955, "USFQ / GSC", "#d62728")])


@vista
def scb_tomas_agua():
    tom = [(f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1], f["properties"].get("nombre") or f["properties"]["id"])
           for f in gj(SCB / "agua/tomas.geojson") if f["properties"].get("id") in ("AG-01", "AG-02", "AG-03", "AG-04")]
    bb = (-89.53, -0.94, -89.44, -0.88)
    cs = capas_scb(bb)
    for f in gj(SCB / "agua/conducciones.geojson"):
        cs.append((shape(f["geometry"]), {"color": "#00838f", "lw": 2.2, "ls": "--", "label": "Conducciones de agua"}))
    for f in gj(SCB / "agua/cuencas_tomas.geojson"):
        cs.append((shape(f["geometry"]), {"color": "#00acc1", "lw": 1.6, "label": "Cuencas de captación de las tomas"}))
    for f in gj(SCB / "agua/tomas.geojson"):
        if f["properties"].get("categoria") in ("toma", "manantial"):
            cs.append((shape(f["geometry"]), {"color": "#00acc1", "marker": "o", "s": 50, "label": "Toma de agua / manantial"}))
    render("san-cristobal", (-89.485, -0.912), 8000, 6000, 32, -100, 5, "San Cristóbal: tomas de agua del acueducto en la parte alta (Cerro Gato, Los Americanos, La Toma)",
           ROOT / "estudios/san-cristobal/figuras/3d_tomas_agua.png", cs, paso=1,
           marcadores=[(lon, lat, nm, "#006064") for lon, lat, nm in tom],
           nota="Ubicaciones de confianza media o alta según fuentes (ver sección de agua potable).")


if __name__ == "__main__":
    quien = sys.argv[1:] or list(VISTAS)
    for n in quien:
        print("→", n); VISTAS[n]()
