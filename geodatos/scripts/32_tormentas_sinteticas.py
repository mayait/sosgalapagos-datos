"""Biblioteca de tormentas sintéticas: cientos de lluvias plausibles sobre Santa Cruz y San Cristóbal, cada una pasada por el
modelo 2D, para saber QUÉ MARCA CADA PLUVIÓMETRO cuando algo se inunda abajo y derivar de ahí umbrales de alerta (#26, #30).

La idea es la de los gemelos digitales de crecidas (p. ej. PGTEC, UPV 2026: TETIS + HIDRIS): mover, agrandar o achicar
tormentas y ver qué pasa. Aquí, con herramientas propias y abiertas:

  1. Generador de tormentas (paramétrico, reproducible con semilla):
       - forma en el espacio: «celda» convectiva gaussiana (radio 1,5–6 km, puede desplazarse), «orográfica» (crece con la
         cota) o «uniforme»; el 65 % de las celdas se centra en la parte alta («tormenta en la montaña»);
       - forma en el tiempo: beta con la moda entre el 20 y el 80 % de la duración (1–24 h);
       - lámina puntual máxima D ≤ 90·d^0,42 mm (d en h): 90 mm en 1 h … 340 mm en 24 h, del orden del 30-oct-2026
         (61–66 mm/h, 117–131 mm en 3 h, 179–238 mm en el día), que es un evento de decenas de años;
       - humedad antecedente P5d (0–100 mm) y pérdida constante F inciertas (se muestrean, no se fijan).
  2. Motor 2D: el esquema inercial local de los scripts 24 (Santa Cruz) y 25 (San Cristóbal), portado a numba en una sola
     función (`avanzar`). Santa Cruz: θ = 0,8 (de Almeida et al. 2012), mar a nivel fijo, contorno de tierra cerrado.
     San Cristóbal: limitador de Froude 1, mar y bordes absorbentes. Celda de 30 m sobre el DSM GLO-30.
  3. Pérdidas: juego (b) del script 24 (pérdida inicial + pérdida constante sobre el agua presente), que reproduce el 30-oct
     y deja seco el 3-oct en La Cascada. La pérdida inicial baja con P5d: IL = IL0·clip(1,4 − P5d/60; 0,2; 1,4).
  4. Lo que mira cada pluviómetro: la lluvia del campo sintético en su posición (sin error de medida).

Todo es MODELO PROPIO, no dato oficial. Sirve para comparar reglas de alerta y ubicar pluviómetros, no para delimitar.

Uso (desde geodatos/):
  .venv/bin/python -I scripts/32_tormentas_sinteticas.py validar santa-cruz        motor nuevo frente a b_central (script 24)
  .venv/bin/python -I scripts/32_tormentas_sinteticas.py validar san-cristobal     motor nuevo frente a «guayabillos» (script 25)
  .venv/bin/python -I scripts/32_tormentas_sinteticas.py correr <isla> [--n 500] [--procesos 8]
  .venv/bin/python -I scripts/32_tormentas_sinteticas.py analizar <isla>
Las figuras y animaciones están en 33_tormentas_figuras.py.
Salidas: estudios/tormentas/datos/<isla>/ (catálogo, resultados por punto, umbrales propuestos) y estudios/tormentas/cache/
(corridas individuales y rasters; no se versiona).
"""
import csv, json, math, os, pathlib, sys, time, datetime as dt, warnings, importlib.util
warnings.filterwarnings("ignore")
import numpy as np, rasterio
from numba import njit

ROOT = pathlib.Path(__file__).resolve().parents[1]
EST = ROOT / "estudios/tormentas"
CACHE = EST / "cache"
SEMILLA = {"santa-cruz": 20261030, "san-cristobal": 20261031}
DT_B = 300.0                     # bloque de lluvia y de series: 5 min
H_IMPACTO = 0.30                 # calado que se considera «inundación» en un punto clave
MIN_AVISO_S = 900                # una alerta sirve si llega al menos 15 min antes que el agua
VENTANAS_H = (1, 3, 6, 24)

# ---------------------------------------------------------------- estaciones (lat, lon, cota m), de clima/recolector
ESTACIONES = {
    "santa-cruz": {
        "Cerro Crocker": (-0.6424, -90.3260, 861), "Santa Rosa": (-0.6545, -90.4035, 416),
        "Los Guayabillos": (-0.6991, -90.3420, 178), "INAMHI Puerto Ayora": (-0.743056, -90.3025, 6),
        "Erna (Puerto Ayora)": (-0.753368, -90.311995, 10), "Punta Estrada": (-0.7499, -90.31081, 8)},
    "san-cristobal": {
        "El Junco": (-0.896537, -89.481624, 548), "Cerro Alto": (-0.887049, -89.530986, 517),
        "El Mirador": (-0.886248, -89.539587, 387), "Merceditas": (-0.889712, -89.442020, 100),
        "INAMHI Puerto Baquerizo": (-0.904058, -89.614308, 6)},
}
# zonas de alerta: punto clave del modelo y estaciones con peso (la de La Cascada es la de umbrales_inundacion.json v0.2).
# El calado se lee en la celda de 30 m del punto, como en los scripts 24 y 25 (La Cascada está calibrada así con el testimonio
# de ≈2 m). Se guarda también el máximo a menos de ≈45 m («serie9»), pero no se usa: incluye depresiones y el estuario, que
# guardan agua con cualquier lluvia. La Planada (registro 2025) no entra: el modelo no la inunda con ninguna de las 500 tormentas.
ZONAS = {
    "santa-cruz": {
        "La Cascada": dict(punto="La Cascada (centro)", v02=[("Los Guayabillos", 1.0), ("Santa Rosa", 0.75), ("INAMHI Puerto Ayora", 1.0), ("Erna (Puerto Ayora)", 1.0)]),
        "Tomás de Berlanga": dict(punto="Tomás de Berlanga (cauce)", v02=[("Los Guayabillos", 1.0), ("Santa Rosa", 0.75), ("INAMHI Puerto Ayora", 1.0), ("Erna (Puerto Ayora)", 1.0)]),
        "Bellavista": dict(punto="Bellavista (centro, llegada SC-003)", v02=[("Los Guayabillos", 1.0), ("Santa Rosa", 1.0), ("Cerro Crocker", 1.0)]),
    },
    "san-cristobal": {
        "Barrio Frío (desembocadura)": dict(punto="barrio_frio_desembocadura", v02=[("El Junco", 1.0), ("Cerro Alto", 1.0), ("El Mirador", 1.0), ("Merceditas", 1.0), ("INAMHI Puerto Baquerizo", 1.0)]),
        "El Manzanillo": dict(punto="manzanillo_registro_2019", v02=[("El Junco", 1.0), ("Cerro Alto", 1.0), ("El Mirador", 1.0), ("Merceditas", 1.0), ("INAMHI Puerto Baquerizo", 1.0)]),
        "El Progreso": dict(punto="el_progreso_escuela_darwin_2024", v02=[("El Junco", 1.0), ("Cerro Alto", 1.0), ("El Mirador", 1.0), ("Merceditas", 1.0), ("INAMHI Puerto Baquerizo", 1.0)]),
    },
}
EPSG = {"santa-cruz": 32715, "san-cristobal": 32716}
DEM = {"santa-cruz": ROOT / "descargas/dem_recortes/santa_cruz_dem.tif", "san-cristobal": ROOT / "descargas/dem_recortes/san_cristobal_dem.tif"}
# parámetros del motor y de las pérdidas por isla (clases: 0 natural/parque, 1 agrícola, 2 urbano)
MOTOR = {"santa-cruz": dict(theta=0.8, frmax=1e9, pared=True), "san-cristobal": dict(theta=1.0, frmax=1.0, pared=False)}
IL0 = (20.0, 20.0, 5.0)          # mm, pérdida inicial con P5d «normal» (script 24, juego b)
F_URB = 5.0                      # mm/h en zona urbana
RANGO_F = {"santa-cruz": (15.0, 35.0), "san-cristobal": (5.0, 35.0)}    # mm/h; Santa Cruz: barrido F10–F35 del script 24


def cargar_modulo(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, ROOT / "scripts" / archivo)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# ================================================================ motor numérico
@njit(cache=__name__ == "__main__")       # la caché de numba guarda el nombre del módulo: solo al correr el script directamente
def avanzar(z, h, qx, qy, nman, act, fijo, hfijo, tierra, rate, inf, t, t_end, dx, theta, frmax, pared,
            hmax, tl1, tl3, qxo, qyo, fac):
    """Avanza el esquema inercial local (Bates et al. 2010) de t a t_end. rate: lluvia neta (m/s); inf: pérdida constante (m/s)."""
    g = 9.81
    H, W = h.shape
    vol_out = 0.0
    n = 0
    while t < t_end - 1e-9:
        hm = 0.0
        for i in range(H):
            for j in range(W):
                if tierra[i, j] and h[i, j] > hm:
                    hm = h[i, j]
        if hm < 0.01:
            hm = 0.01
        dt = 0.7 * dx / math.sqrt(g * hm)
        if dt > 10.0:
            dt = 10.0
        if dt > t_end - t:
            dt = t_end - t
        qxo[:, :] = qx
        qyo[:, :] = qy
        for i in range(H):
            for j in range(1, W):
                a = act[i, j - 1]; b = act[i, j]
                ok = (a and b) if pared else (a or b)
                if not ok:
                    qx[i, j] = 0.0; continue
                z1 = z[i, j - 1]; z2 = z[i, j]; e1 = z1 + h[i, j - 1]; e2 = z2 + h[i, j]
                hf = max(e1, e2) - max(z1, z2)
                if hf <= 1e-3:
                    qx[i, j] = 0.0; continue
                q0 = qxo[i, j]
                if theta < 1.0:
                    ql = qxo[i, j - 1] if j - 1 >= 1 else 0.0
                    qr = qxo[i, j + 1] if j + 1 <= W - 1 else 0.0
                    q0 = theta * q0 + (1.0 - theta) * 0.5 * (ql + qr)
                nf = 0.5 * (nman[i, j - 1] + nman[i, j])
                q = (q0 - g * hf * dt * (e2 - e1) / dx) / (1.0 + g * dt * nf * nf * abs(q0) / hf ** (7.0 / 3.0))
                ql_ = frmax * hf * math.sqrt(g * hf)
                if q > ql_: q = ql_
                if q < -ql_: q = -ql_
                qx[i, j] = q
        for i in range(1, H):
            for j in range(W):
                a = act[i - 1, j]; b = act[i, j]
                ok = (a and b) if pared else (a or b)
                if not ok:
                    qy[i, j] = 0.0; continue
                z1 = z[i - 1, j]; z2 = z[i, j]; e1 = z1 + h[i - 1, j]; e2 = z2 + h[i, j]
                hf = max(e1, e2) - max(z1, z2)
                if hf <= 1e-3:
                    qy[i, j] = 0.0; continue
                q0 = qyo[i, j]
                if theta < 1.0:
                    ql = qyo[i - 1, j] if i - 1 >= 1 else 0.0
                    qr = qyo[i + 1, j] if i + 1 <= H - 1 else 0.0
                    q0 = theta * q0 + (1.0 - theta) * 0.5 * (ql + qr)
                nf = 0.5 * (nman[i - 1, j] + nman[i, j])
                q = (q0 - g * hf * dt * (e2 - e1) / dx) / (1.0 + g * dt * nf * nf * abs(q0) / hf ** (7.0 / 3.0))
                ql_ = frmax * hf * math.sqrt(g * hf)
                if q > ql_: q = ql_
                if q < -ql_: q = -ql_
                qy[i, j] = q
        # limitador de volumen: una celda no cede más agua de la que tiene
        for i in range(H):
            for j in range(W):
                o = max(qx[i, j + 1], 0.0) + max(-qx[i, j], 0.0) + max(qy[i + 1, j], 0.0) + max(-qy[i, j], 0.0)
                o *= dt / dx
                fac[i, j] = 1.0 if (o <= h[i, j] or o == 0.0) else h[i, j] / o
        for i in range(H):
            for j in range(1, W):
                q = qx[i, j]
                if q > 0: qx[i, j] = q * fac[i, j - 1]
                elif q < 0: qx[i, j] = q * fac[i, j]
        for i in range(1, H):
            for j in range(W):
                q = qy[i, j]
                if q > 0: qy[i, j] = q * fac[i - 1, j]
                elif q < 0: qy[i, j] = q * fac[i, j]
        k = dt / dx
        for i in range(H):
            for j in range(W):
                hv = h[i, j] + k * (qx[i, j] - qx[i, j + 1] + qy[i, j] - qy[i + 1, j])
                if fijo[i, j]:
                    vol_out += (hv - hfijo[i, j]) * dx * dx
                    hv = hfijo[i, j]
                elif not act[i, j]:
                    vol_out += hv * dx * dx
                    hv = 0.0
                elif tierra[i, j]:
                    hv += rate[i, j] * dt
                    p = inf[i, j] * dt
                    hv = hv - p if hv > p else 0.0
                if hv < 0.0:
                    hv = 0.0
                h[i, j] = hv
        t += dt
        n += 1
        for i in range(H):
            for j in range(W):
                if tierra[i, j]:
                    hh = h[i, j]
                    if hh > hmax[i, j]: hmax[i, j] = hh
                    if hh >= 0.1 and tl1[i, j] < 0: tl1[i, j] = t
                    if hh >= 0.3 and tl3[i, j] < 0: tl3[i, j] = t
    return t, vol_out, n


# ================================================================ dominios
def dominio_santa_cruz():
    """Dominio del script 24 (cuenca de Puerto Ayora ∪ cuenca de La Cascada + 150 m + franja de mar), malla de 30 m."""
    from rasterio.features import rasterize, shapes
    from rasterio.warp import reproject, Resampling, calculate_default_transform
    from scipy.interpolate import RegularGridInterpolator
    from shapely.geometry import shape, Point, Polygon
    from shapely.ops import unary_union, transform as stransform
    from pyproj import Transformer
    E = EPSG["santa-cruz"]; CEL = 30.0; NIVEL_MAR = 0.75; FONDO = -3.0
    T = Transformer.from_crs(4326, E, always_xy=True).transform
    LC = ROOT / "estudios/la-cascada/datos"

    def feats(rel, cond=lambda p: True):
        return [(stransform(T, shape(f["geometry"]).buffer(0) if f["geometry"]["type"].endswith("Polygon") else shape(f["geometry"])), f["properties"])
                for f in json.loads((ROOT / rel).read_text())["features"] if f["properties"].get("isla", "Santa Cruz") == "Santa Cruz" and cond(f["properties"])]
    src = rasterio.open(DEM["santa-cruz"])
    tr, w, h = calculate_default_transform(src.crs, f"EPSG:{E}", src.width, src.height, *src.bounds, resolution=CEL)
    dem = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), dem, src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs=f"EPSG:{E}",
              resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    mar_r = (dem == -9999) | (dem <= 0.3); demf = np.where(dem == -9999, FONDO, dem)
    xs = tr.c + CEL * (np.arange(w) + .5); ys = tr.f - CEL * (np.arange(h) + .5)
    interp = RegularGridInterpolator((ys[::-1], xs), demf[::-1], bounds_error=False, fill_value=FONDO)
    pa = max([g for g, p in feats("capas/dem/cuencas_localidad.geojson", lambda p: p.get("destino") == "Puerto Ayora")], key=lambda g: g.area)
    pa = max(getattr(pa, "geoms", [pa]), key=lambda g: g.area)
    casc = unary_union([stransform(T, shape(f["geometry"])) for f in json.loads((LC / "cuenca_cascada.geojson").read_text())["features"]])
    tierra_g = unary_union([pa, casc]).buffer(150)
    mar_geo = unary_union([shape(s) for s, v in shapes(mar_r.astype("uint8"), mask=mar_r, transform=tr)])
    dom = unary_union([tierra_g, tierra_g.buffer(400).intersection(mar_geo)]).buffer(30).buffer(-30).simplify(40)
    dom = Polygon(max(getattr(dom, "geoms", [dom]), key=lambda g: g.area).exterior)
    gx0, gy0, gx1, gy1 = dom.bounds
    Wg = int(math.ceil((gx1 - gx0) / CEL)); Hg = int(math.ceil((gy1 - gy0) / CEL))
    gtr = rasterio.Affine(CEL, 0, gx0, 0, -CEL, gy1)
    GX = gx0 + CEL * (np.arange(Wg) + .5); GY = gy1 - CEL * (np.arange(Hg) + .5)
    MX, MY = np.meshgrid(GX, GY)
    z = interp(np.c_[MY.ravel(), MX.ravel()]).reshape(Hg, Wg).astype("float64")
    act = rasterize([(dom, 1)], out_shape=(Hg, Wg), transform=gtr).astype(bool)
    mar = act & (z <= 0.3); z[mar] = np.minimum(z[mar], FONDO)
    tierra = act & ~mar
    urb = [g for g, p in feats("capas/igm/zona_urbana.geojson") if p.get("nam") == "Puerto Ayora"]
    pobl = [g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")] + urb
    agr = [g for g, p in feats("export/galapagos/zona_agricola.geojson")]
    r_urb = rasterize([(g, 1) for g in pobl], out_shape=(Hg, Wg), transform=gtr).astype(bool) & tierra
    r_agr = rasterize([(g, 1) for g in agr], out_shape=(Hg, Wg), transform=gtr).astype(bool) & tierra & ~r_urb
    clase = np.zeros((Hg, Wg), "int8"); clase[r_agr] = 1; clase[r_urb] = 2
    nman = np.where(mar, 0.03, np.choose(clase, [0.08, 0.06, 0.08])).astype("float64")
    hfijo = np.where(mar, NIVEL_MAR - z, 0.0)
    m24 = cargar_modulo_fuente_puntos_24()
    pts = dict(m24)
    cr = [r for r in csv.DictReader(open(ROOT / "estudios/santa-cruz/datos/cruces.csv")) if r["isla"] == "Santa Cruz"]
    cr = [r for r in cr if dom.contains(Point(T(float(r["lon"]), float(r["lat"]))))]
    cr.sort(key=lambda r: -float(r["area_km2"] or 0)); sel = []
    for r in cr:
        p_ = Point(T(float(r["lon"]), float(r["lat"])))
        if all(p_.distance(q) > 400 for q, _ in sel): sel.append((p_, r))
        if len(sel) >= 6: break
    for p_, r in sel:
        pts[f"Cruce {r['id']} ({r['via_nombre'] or r['via_highway']}, {float(r['area_km2']):.1f} km²)"] = (float(r["lon"]), float(r["lat"]))
    return dict(z=z, act=act, fijo=mar, hfijo=hfijo, tierra=tierra, clase=clase, nman=nman, tr=gtr, epsg=E, celda=CEL, puntos=pts)


def cargar_modulo_fuente_puntos_24():
    """Lee el diccionario PUNTOS del script 24 sin ejecutarlo (el script no es importable)."""
    import ast
    src = (ROOT / "scripts/24_modelo2d_santa_cruz.py").read_text()
    for nodo in ast.parse(src).body:
        if isinstance(nodo, ast.Assign) and any(getattr(t, "id", "") == "PUNTOS" for t in nodo.targets):
            return ast.literal_eval(nodo.value)
    raise RuntimeError("PUNTOS no encontrado en el script 24")


def dominio_san_cristobal():
    """Dominio del script 25 (cuencas D8 de Puerto Baquerizo Moreno y El Progreso + 150 m), malla de 30 m."""
    from rasterio.features import rasterize
    m25 = cargar_modulo("m25", "25_modelo2d_san_cristobal.py")
    base = m25.preparar_base()
    dem, tr = m25.a_utm(m25.DEM_CRUDO, 30.0, base["bounds"])
    H, W = dem.shape
    sea = (dem == -9999) | (dem <= 0.5)
    dom = m25.remuestrear_mascara(base["dom"], base["tr"], tr, (H, W)) & ~sea
    Ac = np.zeros((H, W))
    from rasterio.warp import reproject, Resampling
    reproject(base["A"], Ac, src_transform=base["tr"], src_crs=f"EPSG:{m25.EPSG}", dst_transform=tr, dst_crs=f"EPSG:{m25.EPSG}", resampling=Resampling.max)
    cauce = (Ac >= m25.A_CAUCE_KM2) & dom
    pob = rasterize([(g, 1) for g, p in m25.feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")]
                    + [(g, 1) for g, p in m25.feats("capas/final/manzanas_inec.geojson")], out_shape=(H, W), transform=tr).astype(bool)
    agr = rasterize([(g, 1) for g, _ in m25.feats("export/galapagos/zona_agricola.geojson")], out_shape=(H, W), transform=tr).astype(bool)
    clase = np.where(pob, 2, np.where(agr, 1, 0)).astype("int8")
    N = m25.N_CLASE
    nman = np.choose(clase, [N["natural"], N["agricola"], N["poblado"]]).astype(float)
    nman[cauce & ~pob] = N["cauce"]
    z = np.where(sea, 0.0, dem).astype("float64")
    return dict(z=z, act=dom.copy(), fijo=np.zeros((H, W), bool), hfijo=np.zeros((H, W)), tierra=dom.copy(), clase=clase, nman=nman,
                tr=tr, epsg=m25.EPSG, celda=30.0, puntos={k: v for k, v in m25.PUNTOS.items()})


def dominio(isla):
    """Dominio en caché (npz); se rehace si no existe."""
    f = CACHE / isla / "dominio.npz"
    if f.exists():
        d = dict(np.load(f, allow_pickle=True)); d = {k: (v.item() if v.dtype == object and v.shape == () else v) for k, v in d.items()}
        d["tr"] = rasterio.Affine(*d["tr"][:6]); return d
    d = dominio_santa_cruz() if isla == "santa-cruz" else dominio_san_cristobal()
    from pyproj import Transformer
    T = Transformer.from_crs(4326, d["epsg"], always_xy=True).transform
    H, W = d["z"].shape; tr = d["tr"]
    # puntos: celda + vecindario 3×3 (90 m) para leer el calado sin depender de una sola celda de 30 m
    pr = {}
    for nm, (lo, la) in d["puntos"].items():
        c, r = ~tr * T(lo, la); pr[nm] = (int(r), int(c), lo, la)
    d["puntos_rc"] = pr
    st = {}
    for nm, (la, lo, cota) in ESTACIONES[isla].items():
        x, y = T(lo, la); st[nm] = (x, y, cota, lo, la)
    d["estaciones_xy"] = st
    # cotas de un área amplia (dominio + 6 km) a 150 m para el campo de lluvia orográfico y los centros de tormenta
    d.update(rejilla_amplia(isla, d))
    f.parent.mkdir(parents=True, exist_ok=True)
    g = dict(d); g["tr"] = np.array(tr)[:6]
    np.savez_compressed(f, **{k: (np.array(v, dtype=object) if isinstance(v, dict) else v) for k, v in g.items()})
    return dominio(isla)


def rejilla_amplia(isla, d):
    from rasterio.warp import reproject, Resampling
    tr = d["tr"]; H, W = d["z"].shape
    x0, y1 = tr.c, tr.f; x1, y0 = x0 + W * tr.a, y1 + H * tr.e
    xs_st = [v[0] for v in d["estaciones_xy"].values()]; ys_st = [v[1] for v in d["estaciones_xy"].values()]
    M = 6000
    bx0, bx1 = min(x0, min(xs_st)) - M, max(x1, max(xs_st)) + M
    by0, by1 = min(y0, min(ys_st)) - M, max(y1, max(ys_st)) + M
    C = 150.0
    w = int((bx1 - bx0) // C); h = int((by1 - by0) // C)
    atr = rasterio.Affine(C, 0, bx0, 0, -C, by1)
    za = np.full((h, w), -9999, "float32")
    src = rasterio.open(DEM[isla])
    reproject(rasterio.band(src, 1), za, src_transform=src.transform, src_crs=src.crs, dst_transform=atr, dst_crs=f"EPSG:{d['epsg']}",
              resampling=Resampling.average, src_nodata=-9999, dst_nodata=-9999)
    return dict(amplia_z=za, amplia_tr=np.array(atr)[:6])


# ================================================================ generador de tormentas
def envolvente(d_h):
    return 90.0 * d_h ** 0.42


def generar_catalogo(isla, n, d):
    """Parámetros de n tormentas (hipercubo latino en lo continuo) → lista de dicts."""
    from scipy.stats import qmc
    rng = np.random.default_rng(SEMILLA[isla])
    U = qmc.LatinHypercube(d=7, seed=SEMILLA[isla]).random(n)
    atr = rasterio.Affine(*d["amplia_tr"]); za = d["amplia_z"]
    rr, cc = np.where(za > 150); alto = np.c_[atr.c + atr.a * (cc + .5), atr.f + atr.e * (rr + .5)]
    tr = d["tr"]; H, W = d["z"].shape
    rr2, cc2 = np.where(za > -9999)
    box = (atr.c, atr.f + atr.e * za.shape[0], atr.c + atr.a * za.shape[1], atr.f)
    # «montaña»: celdas altas a menos de 4 km del dominio
    dx0, dy1 = tr.c, tr.f; dx1, dy0 = dx0 + W * tr.a, dy1 + H * tr.e
    cerca = (alto[:, 0] > dx0 - 4000) & (alto[:, 0] < dx1 + 4000) & (alto[:, 1] > dy0 - 4000) & (alto[:, 1] < dy1 + 4000)
    alto = alto[cerca]
    cat = []
    for i in range(n):
        u = U[i]
        dur = float(np.exp(np.log(1.0) + u[0] * (np.log(24.0) - np.log(1.0))))
        dur = round(dur * 12) / 12                                            # múltiplo de 5 min
        D = float(envolvente(dur) * (0.12 + 0.88 * u[1]))
        r = 0.2 + 0.6 * u[2]; kappa = 2.0 + 12.0 * u[3]
        p5d = 100.0 * u[4]
        F = RANGO_F[isla][0] + (RANGO_F[isla][1] - RANGO_F[isla][0]) * u[5]
        x = rng.random()
        tipo = "celda" if x < 0.55 else ("orografica" if x < 0.80 else "uniforme")
        p = dict(id=i, tipo=tipo, dur_h=dur, D_mm=round(D, 1), pico=round(r, 3), kappa=round(kappa, 2), P5d_mm=round(p5d, 1), F_mmh=round(F, 1))
        if tipo == "celda":
            if rng.random() < 0.65:
                cx, cy = alto[rng.integers(len(alto))]; p["centro"] = "montaña"
            else:
                cx = dx0 - 3000 + rng.random() * (dx1 - dx0 + 6000); cy = dy0 - 3000 + rng.random() * (dy1 - dy0 + 6000); p["centro"] = "cualquiera"
            p.update(cx=round(float(cx)), cy=round(float(cy)), sigma_m=round(1500 + 4500 * float(rng.random())), fondo=round(0.05 + 0.35 * float(rng.random()), 3),
                     vel_ms=round(float(rng.random() ** 2 * 4.0), 2), dir_grados=round(float(rng.random() * 360)))
        elif tipo == "orografica":
            p.update(razon_costa=round(0.3 + 0.9 * float(rng.random()), 3), cota_tope_m=round(300 + 400 * float(rng.random())))
        cat.append(p)
    return cat


def pesos_tiempo(p, nb):
    """Fracción de la lámina en cada bloque de 5 min (beta con moda en «pico»)."""
    from scipy.stats import beta
    s = p["kappa"]; a = 1 + p["pico"] * (s - 2); b = 1 + (1 - p["pico"]) * (s - 2)
    nb_ll = max(int(round(p["dur_h"] * 3600 / DT_B)), 1)
    edges = np.linspace(0, 1, nb_ll + 1)
    w = np.diff(beta.cdf(edges, a, b))
    out = np.zeros(nb); out[:nb_ll] = w / w.sum()
    return out


def factor_espacial(p, x, y, cota, t_s):
    """Fracción de la lámina D que cae en (x, y) en el instante t_s (1 en el núcleo)."""
    if p["tipo"] == "uniforme":
        return np.ones_like(np.asarray(x, float))
    if p["tipo"] == "orografica":
        g = p["razon_costa"]; f = g + (1 - g) * np.clip(np.asarray(cota, float) / p["cota_tope_m"], 0, 1)
        return f / max(g, 1.0)
    tp = p["pico"] * p["dur_h"] * 3600
    ang = math.radians(p["dir_grados"]); s = p["vel_ms"] * (t_s - tp)
    cx = p["cx"] + s * math.sin(ang); cy = p["cy"] + s * math.cos(ang)
    r2 = (np.asarray(x, float) - cx) ** 2 + (np.asarray(y, float) - cy) ** 2
    return p["fondo"] + (1 - p["fondo"]) * np.exp(-r2 / (2 * p["sigma_m"] ** 2))


def lluvia_puntos(p, xs, ys, cotas, nb):
    """Lluvia (mm) por bloque de 5 min en una lista de puntos → matriz (nb, npuntos)."""
    w = pesos_tiempo(p, nb); out = np.zeros((nb, len(xs)))
    for k in np.flatnonzero(w):
        out[k] = p["D_mm"] * w[k] * factor_espacial(p, xs, ys, cotas, (k + 0.5) * DT_B)
    return out


# ================================================================ una corrida
def correr_tormenta(p, d, guardar_cuadros=False, lluvia_fija=None, t_total_h=None, il=None, F=None, P0=None, cn=None):
    """Simula una tormenta. lluvia_fija: serie (mm por bloque de 5 min) uniforme sobre el dominio (validación con lluvia medida)."""
    z, act, fijo, hfijo, tierra, nman, clase = d["z"], d["act"], d["fijo"], d["hfijo"], d["tierra"], d["nman"], d["clase"]
    H, W = z.shape; tr = d["tr"]; dx = float(d["celda"])
    mot = MOTOR[d["isla"]]
    if lluvia_fija is not None:
        nb = len(lluvia_fija)
    else:
        nb = int(round(((t_total_h or (max(p["dur_h"] + 6.0, 8.0))) * 3600) / DT_B))
    if il is None:
        fac_il = float(np.clip(1.4 - p["P5d_mm"] / 60.0, 0.2, 1.4)); il = tuple(v * fac_il if i < 2 else v for i, v in enumerate(IL0))
    if F is None:
        F = p["F_mmh"] if p else 0.0
    ILc = np.choose(clase, il).astype(float)
    inf = np.where(tierra, np.where(clase == 2, F_URB, F) / 1000 / 3600, 0.0)
    if cn is not None:                                               # SCS-CN por clase (solo para validar contra el script 25)
        S_ = np.choose(clase, [25400.0 / c - 254.0 for c in cn]).astype(float); inf = np.zeros((H, W))
        def Q_(P): return np.where(P > 0.2 * S_, (P - 0.2 * S_) ** 2 / (P + 0.8 * S_), 0.0)
    GX = tr.c + dx * (np.arange(W) + .5); GY = tr.f + tr.e * (np.arange(H) + .5)
    MX, MY = np.meshgrid(GX, GY)
    w = pesos_tiempo(p, nb) if lluvia_fija is None else None
    zc = np.where(tierra, z, 0.0)
    h = np.where(fijo, hfijo, 0.0).astype("float64")
    qx = np.zeros((H, W + 1)); qy = np.zeros((H + 1, W)); qxo = qx.copy(); qyo = qy.copy(); fac = np.ones((H, W))
    hmax = np.zeros((H, W)); tl1 = -np.ones((H, W)); tl3 = -np.ones((H, W))
    Pc = np.zeros((H, W)) if P0 is None else np.full((H, W), float(P0))
    pts = {nm: v for nm, v in d["puntos_rc"].items() if 1 <= v[0] < H - 1 and 1 <= v[1] < W - 1}
    serie = np.zeros((nb, len(pts)), "float32"); serie9 = serie.copy(); nms = list(pts)
    cuadros = []; lluvia_cuadros = []
    t = 0.0; vol_out = 0.0; vol_ll = 0.0; pasos = 0; t0 = time.time()
    acum10 = np.zeros((H, W))
    for k in range(nb):
        if lluvia_fija is not None:
            ll = np.full((H, W), float(lluvia_fija[k]))
        elif w[k] > 0:
            ll = p["D_mm"] * w[k] * factor_espacial(p, MX, MY, zc, (k + 0.5) * DT_B)
        else:
            ll = None
        if ll is not None:
            Pn = Pc + ll
            exc = (Q_(Pn) - Q_(Pc)) if cn is not None else (np.maximum(Pn - ILc, 0) - np.maximum(Pc - ILc, 0)); Pc = Pn
            rate = np.where(tierra, exc / 1000 / DT_B, 0.0)
            vol_ll += float(exc[tierra].sum()) * dx * dx / 1000
            acum10 += ll
        else:
            rate = np.zeros((H, W))
        t, vo, n_ = avanzar(z, h, qx, qy, nman, act, fijo, hfijo, tierra, rate, inf, t, (k + 1) * DT_B, dx,
                            mot["theta"], mot["frmax"], mot["pared"], hmax, tl1, tl3, qxo, qyo, fac)
        vol_out += vo; pasos += n_
        for j, nm in enumerate(nms):
            r, c = pts[nm][:2]
            serie[k, j] = h[r, c] if tierra[r, c] else 0.0
            serie9[k, j] = float(np.max(np.where(tierra[r - 1:r + 2, c - 1:c + 2], h[r - 1:r + 2, c - 1:c + 2], 0.0)))
        if guardar_cuadros and (k + 1) % 2 == 0:
            cuadros.append(np.where(tierra, h, 0).astype("float16")); lluvia_cuadros.append(acum10.astype("float16")); acum10 = np.zeros((H, W))
    hpt = {nm: float(serie[:, j].max()) for j, nm in enumerate(nms)}
    res = dict(hmax=np.where(tierra, hmax, 0).astype("float16"), tl3=np.where(tl3 >= 0, tl3 / 60, 65535).astype("uint16"),
               serie=serie, serie9=serie9, puntos=nms, hmax_puntos=hpt, hmax_puntos9={nm: float(serie9[:, j].max()) for j, nm in enumerate(nms)}, pasos=pasos, seg=round(time.time() - t0, 1), nb=nb,
               balance=dict(lluvia_neta_m3=round(vol_ll), salida_m3=round(vol_out), almacenado_m3=round(float(h[tierra].sum()) * dx * dx)))
    if guardar_cuadros:
        res["cuadros"] = np.array(cuadros); res["lluvia_cuadros"] = np.array(lluvia_cuadros)
    return res


# ================================================================ validación frente a los scripts 24 y 25
def validar(isla):
    d = dominio(isla); d["isla"] = isla
    if isla == "santa-cruz":
        # b_central: lluvia de Los Guayabillos uniforme, IL 20 mm (urbano 5), F 25 mm/h (urbano 5), desde las 12:00 del 30-oct, 20 h
        t0 = dt.datetime(2026, 10, 30, 0, 0); ini = dt.datetime(2026, 10, 30, 12, 0)
        nb_tot = int(32 * 3600 / DT_B); serie = np.zeros(nb_tot)
        for r in csv.DictReader(open(ROOT / "estudios/la-cascada/datos/lluvia_ierse_30oct_5min.csv")):
            if r["estacion"] != "Los Guayabillos": continue
            k = int((dt.datetime.fromisoformat(r["fecha_hora_local"]) - t0).total_seconds() // DT_B)
            if 0 <= k < nb_tot: serie[k] += float(r["lluvia_mm"] or 0)
        k0 = int((ini - t0).total_seconds() // DT_B)
        P0 = float(serie[:k0].sum())
        res = correr_tormenta(None, d, lluvia_fija=serie[k0:k0 + int(20 * 3600 / DT_B)], il=IL0, F=25.0, P0=P0)
        ref = json.loads((ROOT / "estudios/santa-cruz/datos/modelo2d/b_central/resumen_b_central.json").read_text())["puntos"]
        out = {}
        j = res["puntos"].index("La Cascada (centro)")
        s = res["serie"][:, j]; kk = np.argmax(s >= 0.1) if (s >= 0.1).any() else None
        for nm in ("La Cascada (centro)", "Tomás de Berlanga (cauce)", "Bellavista (centro, llegada SC-003)", "Matazarnos (vaso SC-002)"):
            out[nm] = dict(nuevo_celda=round(res["hmax_puntos"][nm], 2), nuevo_max_3x3=round(res["hmax_puntos9"][nm], 2), script24_celda=ref[nm]["calado_max_m"])
        out["La Cascada (centro)"]["llegada_0.1m_nuevo"] = (ini + dt.timedelta(seconds=(int(kk) + 1) * DT_B)).strftime("%H:%M") if kk is not None else None
        out["La Cascada (centro)"]["llegada_0.1m_script24"] = ref["La Cascada (centro)"]["hora_llegada_0.1m"][11:]
        out["La Cascada (centro)"]["hora_max_nuevo"] = (ini + dt.timedelta(seconds=(int(np.argmax(s)) + 1) * DT_B)).strftime("%H:%M")
        out["La Cascada (centro)"]["hora_max_script24"] = ref["La Cascada (centro)"]["hora_calado_max"][11:]
    else:
        # «guayabillos» del script 25 (SCS-CN AMC II, 30 m): mismo método de pérdidas para comparar el motor
        m25 = cargar_modulo("m25", "25_modelo2d_san_cristobal.py")
        fP, t0, info = m25.curva_lluvia(m25.ESCENARIOS["guayabillos"])
        nb = int(26 * 3600 / DT_B); tt = np.arange(nb + 1) * DT_B / 3600
        serie = np.diff(fP(tt))
        res = correr_tormenta(None, d, lluvia_fija=serie, il=IL0, cn=(m25.CN_CLASE["natural"], m25.CN_CLASE["agricola"], m25.CN_CLASE["poblado"]))
        filas = list(csv.DictReader(open(ROOT / "estudios/san-cristobal/datos/modelo2d/guayabillos_series.csv")))
        ref = {nm: max(float(r.get(f"{nm}_h_m") or 0) for r in filas) for nm in res["puntos"]}
        out = {nm: dict(nuevo_celda=round(res["hmax_puntos"][nm], 2), nuevo_max_3x3=round(res["hmax_puntos9"][nm], 2), script25_celda=round(ref[nm], 2)) for nm in res["puntos"]}
    out["_corrida"] = dict(segundos=res["seg"], pasos=res["pasos"], balance=res["balance"])
    (EST / "datos" / isla).mkdir(parents=True, exist_ok=True)
    (EST / "datos" / isla / "validacion_motor.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


# ================================================================ lote en paralelo
_D = None


def _ini(isla):
    global _D
    _D = dominio(isla); _D["isla"] = isla


def _una(p):
    f = CACHE / _D["isla"] / "corridas" / f"t{p['id']:04d}.npz"
    if f.exists(): return p["id"], None
    r = correr_tormenta(p, _D)
    np.savez_compressed(f, hmax=r["hmax"], tl3=r["tl3"], serie=r["serie"], serie9=r["serie9"], puntos=np.array(r["puntos"]), seg=r["seg"], pasos=r["pasos"],
                        balance=json.dumps(r["balance"]))
    return p["id"], r["seg"]


def correr(isla, n, procesos):
    from multiprocessing import Pool
    d = dominio(isla); d["isla"] = isla
    (CACHE / isla / "corridas").mkdir(parents=True, exist_ok=True)
    cat = generar_catalogo(isla, n, d)
    (EST / "datos" / isla).mkdir(parents=True, exist_ok=True)
    claves = sorted({k for p in cat for k in p})
    with open(EST / "datos" / isla / "catalogo_tormentas.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "tipo", "centro", "dur_h", "D_mm", "pico", "kappa", "P5d_mm", "F_mmh", "cx", "cy", "sigma_m", "fondo", "vel_ms", "dir_grados", "razon_costa", "cota_tope_m"])
        w.writeheader(); [w.writerow(p) for p in cat]
    print(f"{isla}: {len(cat)} tormentas; dominio {d['z'].shape}, {int(d['tierra'].sum())} celdas de tierra", flush=True)
    _ini(isla); _una(cat[0])                                        # compila numba una vez antes de repartir
    t0 = time.time(); hechas = 0
    with Pool(procesos, initializer=_ini, initargs=(isla,)) as pool:
        for i, s in pool.imap_unordered(_una, cat[1:], chunksize=2):
            hechas += 1
            if hechas % 25 == 0:
                print(f"  {hechas + 1}/{len(cat)}  ({time.time() - t0:.0f} s)", flush=True)
    print(f"listo en {time.time() - t0:.0f} s", flush=True)


# ================================================================ análisis
def leer_catalogo(isla):
    out = []
    for r in csv.DictReader(open(EST / "datos" / isla / "catalogo_tormentas.csv")):
        p = {k: (v if k in ("tipo", "centro") else (float(v) if v not in ("", None) else None)) for k, v in r.items()}
        p["id"] = int(p["id"]); out.append(p)
    return out


def ventanas(serie_mm):
    """serie (nb, n) en mm por 5 min → dict ventana → acumulado móvil (nb, n)."""
    c = np.cumsum(np.r_[np.zeros((1, serie_mm.shape[1])), serie_mm], axis=0)
    out = {}
    for v in VENTANAS_H:
        k = int(v * 3600 / DT_B); out[v] = c[1:] - c[np.maximum(np.arange(1, len(c)) - k, 0)]
    return out


def analizar(isla):
    d = dominio(isla); cat = leer_catalogo(isla)
    st = d["estaciones_xy"]; nm_st = list(st)
    xs = np.array([st[k][0] for k in nm_st]); ys = np.array([st[k][1] for k in nm_st]); cz = np.array([st[k][2] for k in nm_st])
    filas = []; HM = []; TL = []; ids = []
    for p in cat:
        f = CACHE / isla / "corridas" / f"t{p['id']:04d}.npz"
        if not f.exists(): continue
        r = np.load(f, allow_pickle=True)
        serie = r["serie"]; pts = list(r["puntos"]); nb = serie.shape[0]
        ll = lluvia_puntos(p, xs, ys, cz, nb); V = ventanas(ll)
        fila = dict(id=p["id"], tipo=p["tipo"], centro=p.get("centro") or "", dur_h=p["dur_h"], D_mm=p["D_mm"], P5d_mm=p["P5d_mm"], F_mmh=p["F_mmh"], seg=float(r["seg"]))
        for j, s in enumerate(nm_st):
            fila[f"{s}|total"] = round(float(ll[:, j].sum()), 1)
            for v in VENTANAS_H: fila[f"{s}|R{v}h"] = round(float(V[v][:, j].max()), 1)
        for zn, zc in ZONAS[isla].items():
            j = pts.index(zc["punto"]); s = serie[:, j]
            fila[f"{zn}|hmax"] = round(float(s.max()), 3)
            fila[f"{zn}|t_llegada_min"] = int((np.argmax(s >= H_IMPACTO) + 1) * DT_B / 60) if (s >= H_IMPACTO).any() else None
        filas.append(fila); ids.append(p["id"]); HM.append(r["hmax"]); TL.append(r["tl3"])
    print(f"{isla}: {len(filas)} corridas leídas", flush=True)
    od = EST / "datos" / isla
    with open(od / "resultados_tormentas.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); [w.writerow(f) for f in filas]
    HM = np.array(HM, dtype="float32"); TL = np.array(TL)
    np.savez_compressed(CACHE / isla / "pila_hmax.npz", hmax=HM.astype("float16"), tl3=TL, ids=np.array(ids))
    # mapa de frecuencia de inundación (≥ 0,3 m) en el conjunto sintético
    frec = (HM >= H_IMPACTO).mean(axis=0)
    prof = dict(driver="GTiff", height=frec.shape[0], width=frec.shape[1], count=1, dtype="float32", crs=f"EPSG:{d['epsg']}",
                transform=d["tr"], nodata=-1, compress="deflate")
    with rasterio.open(od / "frecuencia_inundacion.tif", "w", **prof) as f_:
        f_.write(np.where(d["tierra"], frec, -1).astype("float32"), 1)
    resumen = dict(isla=isla, n_tormentas=len(filas), estaciones=nm_st, ventanas_h=list(VENTANAS_H), h_impacto_m=H_IMPACTO,
                   segundos_por_corrida_mediana=float(np.median([f["seg"] for f in filas])), zonas={})
    reglas = {}
    for zn, zc in ZONAS[isla].items():
        reglas[zn] = umbrales_zona(isla, zn, zc, filas, cat, d, nm_st, xs, ys, cz)
        resumen["zonas"][zn] = reglas[zn]["resumen"]
    (od / "umbrales_propuestos.json").write_text(json.dumps({k: v["regla"] for k, v in reglas.items()}, ensure_ascii=False, indent=1))
    (od / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(json.dumps(resumen, ensure_ascii=False, indent=1)[:6000])


def premax_por_tormenta(isla, zn, zc, cat, nm_st, xs, ys, cz, est_sel, pesos):
    """Para cada tormenta: R1h, R3h, R24h de la zona (máximo ponderado entre sus estaciones) hasta 15 min antes de la llegada
    del agua (si se inunda) o en toda la corrida (si no), la llegada y el instante en que cada ventana cruza un umbral."""
    out = []
    for p in cat:
        f = CACHE / isla / "corridas" / f"t{p['id']:04d}.npz"
        if not f.exists(): continue
        r = np.load(f, allow_pickle=True); serie = r["serie"]; pts = list(r["puntos"]); nb = serie.shape[0]
        idx = [nm_st.index(s) for s in est_sel]
        ll = lluvia_puntos(p, xs[idx], ys[idx], cz[idx], nb) * np.array(pesos)[None, :]
        V = ventanas(ll); Rz = {v: V[v].max(axis=1) for v in (1, 3, 24)}
        s = serie[:, pts.index(zc["punto"])]
        imp = bool((s >= H_IMPACTO).any())
        k_arr = int(np.argmax(s >= H_IMPACTO)) if imp else nb - 1
        k_lim = k_arr - int(MIN_AVISO_S / DT_B) if imp else nb - 1
        pm = [float(Rz[v][:max(k_lim, 0) + 1].max()) if k_lim >= 0 else 0.0 for v in (1, 3, 24)]
        out.append(dict(id=p["id"], imp=imp, k_arr=k_arr, pm=pm, Rz=Rz, P5d=p["P5d_mm"], hmax=float(s.max())))
    return out


def evaluar(T_, pm, imp, wet, k_wet):
    """T_: (m, 3) umbrales; pm: (n, 3); devuelve POD y POFD de cada combinación (regla «basta superar uno»)."""
    esc = np.where(wet, k_wet, 1.0)[:, None]
    trig = np.zeros((T_.shape[0], pm.shape[0]), bool)
    for v in range(3):
        trig |= pm[None, :, v] >= T_[:, None, v] * esc[None, :, 0]
    pod = (trig & imp[None, :]).sum(1) / max(imp.sum(), 1)
    pofd = (trig & ~imp[None, :]).sum(1) / max((~imp).sum(), 1)
    return pod, pofd


def umbrales_zona(isla, zn, zc, filas, cat, d, nm_st, xs, ys, cz):
    est = [s for s, _ in zc["v02"]]; pes = [w for _, w in zc["v02"]]
    D_ = premax_por_tormenta(isla, zn, zc, cat, nm_st, xs, ys, cz, est, pes)
    pm = np.array([x["pm"] for x in D_]); imp = np.array([x["imp"] for x in D_]); P5 = np.array([x["P5d"] for x in D_])
    wet = P5 > 53
    g1 = np.arange(5, 101, 2.5); g3 = np.arange(10, 201, 5); g24 = np.arange(20, 351, 10)
    TT = np.array(np.meshgrid(g1, g3, g24, indexing="ij")).reshape(3, -1).T
    res = {}
    # regla v0.2 tal cual (umbrales y factor 0,8 con suelo húmedo)
    V02 = {"medio": (15, 30, 50), "alto": (30, 60, 100), "muy alto": (45, 90, 150)}
    ev02 = {}
    for nv, th in V02.items():
        pod, pofd = evaluar(np.array([th], float), pm, imp, wet, 0.8)
        ev02[nv] = dict(umbrales=dict(zip(("R1h", "R3h", "R24h"), th)), POD=round(float(pod[0]), 3), POFD=round(float(pofd[0]), 3),
                        anticipacion_mediana_min=anticipacion(D_, np.array(th, float), 0.8))
    # búsqueda: primero el factor de suelo húmedo con la regla «alto» óptima; luego cada nivel
    mejor = None
    for kw in (1.0, 0.9, 0.8, 0.7, 0.6):
        pod, pofd = evaluar(TT, pm, imp, wet, kw); pss = pod - pofd; i = int(np.argmax(pss))
        if mejor is None or pss[i] > mejor[0] + 0.005: mejor = (float(pss[i]), kw, i)
    kw = mejor[1]
    pod, pofd = evaluar(TT, pm, imp, wet, kw); pss = pod - pofd
    sel = {}
    i_alto = int(np.argmax(pss)); sel["alto"] = i_alto
    ok = np.where(pod >= 0.95)[0]; sel["medio"] = int(ok[np.argmin(pofd[ok])]) if len(ok) else int(np.argmax(pod))
    ok = np.where(pofd <= 0.05)[0]; sel["muy alto"] = int(ok[np.argmax(pod[ok])]) if len(ok) else int(np.argmin(pofd))
    th = {nv: TT[i].copy() for nv, i in sel.items()}
    th["medio"] = np.minimum(th["medio"], th["alto"]); th["muy alto"] = np.maximum(th["muy alto"], th["alto"])
    prop = {}
    for nv in ("medio", "alto", "muy alto"):
        p1, p2 = evaluar(th[nv][None, :], pm, imp, wet, kw)
        prop[nv] = dict(umbrales=dict(zip(("R1h", "R3h", "R24h"), [float(x) for x in th[nv]])), POD=round(float(p1[0]), 3), POFD=round(float(p2[0]), 3),
                        anticipacion_mediana_min=anticipacion(D_, th[nv], kw))
    # incertidumbre del umbral «alto»: remuestreo
    rng = np.random.default_rng(7); boots = []
    sub = TT[::3]
    for _ in range(150):
        ii = rng.integers(0, len(imp), len(imp))
        a, b = evaluar(sub, pm[ii], imp[ii], wet[ii], kw); boots.append(sub[int(np.argmax(a - b))])
    boots = np.array(boots)
    rango = {k: [float(np.percentile(boots[:, i], 10)), float(np.percentile(boots[:, i], 90))] for i, k in enumerate(("R1h", "R3h", "R24h"))}
    # ¿qué estación sola predice mejor? (AUC del R3h previo a la llegada)
    auc_est = {}
    for s in nm_st:
        D1 = premax_por_tormenta(isla, zn, zc, cat, nm_st, xs, ys, cz, [s], [1.0])
        auc_est[s] = round(auc(np.array([x["pm"][1] for x in D1]), np.array([x["imp"] for x in D1])), 3)
    out_pm = [dict(id=x["id"], inunda=x["imp"], hmax=round(x["hmax"], 3), R1h=round(x["pm"][0], 1), R3h=round(x["pm"][1], 1), R24h=round(x["pm"][2], 1),
                   P5d=x["P5d"], llegada_min=int((x["k_arr"] + 1) * DT_B / 60) if x["imp"] else None) for x in D_]
    od = EST / "datos" / isla
    with open(od / f"previo_llegada_{slug(zn)}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_pm[0])); w.writeheader(); [w.writerow(r) for r in out_pm]
    resumen = dict(punto=zc["punto"], estaciones=dict(zip(est, pes)), n=int(len(imp)), inundan=int(imp.sum()),
                   regla_v02=ev02, propuesta=prop, factor_suelo_humedo=kw, rango_alto_p10_p90=rango, auc_R3h_por_estacion=auc_est)
    regla = dict(zona=zn, isla=isla, estaciones=[[s, w] for s, w in zip(est, pes)], niveles={nv: prop[nv]["umbrales"] for nv in prop},
                 factor_suelo_humedo=dict(P5d_min_mm=53, factor=kw),
                 nota="Propuesta derivada de tormentas sintéticas y el modelo 2D propio (no oficial). Validar con inundaciones históricas antes de usar.")
    return dict(resumen=resumen, regla=regla)


def anticipacion(D_, th, kw):
    """Mediana de minutos entre el primer cruce de la regla y la llegada del agua (solo tormentas que inundan y que la regla avisa)."""
    out = []
    for x in D_:
        if not x["imp"]: continue
        f = kw if x["P5d"] > 53 else 1.0
        cr = np.zeros(len(x["Rz"][1]), bool)
        for v, t_ in zip((1, 3, 24), th): cr |= x["Rz"][v] >= t_ * f
        if cr.any():
            k = int(np.argmax(cr))
            if k <= x["k_arr"]: out.append((x["k_arr"] - k) * DT_B / 60)
    return round(float(np.median(out)), 0) if out else None


def auc(score, y):
    y = np.asarray(y, bool)
    if y.all() or (~y).all(): return float("nan")
    from scipy.stats import rankdata
    r = rankdata(score); n1 = y.sum(); n0 = (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c if c.isalnum() else "_" for c in s).strip("_").replace("__", "_")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    cmd, isla = a[0], a[1]
    if cmd == "validar": validar(isla)
    elif cmd == "correr":
        n = int(a[a.index("--n") + 1]) if "--n" in a else 500
        pr = int(a[a.index("--procesos") + 1]) if "--procesos" in a else 8
        correr(isla, n, pr)
    elif cmd == "analizar": analizar(isla)
    else: print(__doc__)
