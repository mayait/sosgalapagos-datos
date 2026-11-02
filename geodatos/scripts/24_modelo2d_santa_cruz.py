"""Modelo hidrodinámico 2D «rain-on-grid» del evento del 30-oct-2026: cuenca de La Cascada y Puerto Ayora hasta el mar.

Motor: ANUGA 4.1 (volúmenes finitos sobre malla triangular, ecuaciones de aguas someras, algoritmo DE0, OpenMP).
  - Dominio: cuenca completa de Puerto Ayora (D8, 47 km²) ∪ cuenca de La Cascada, con margen de 150 m y una franja de mar.
  - Malla: triángulos de ≤ AREA_GENERAL m² (≈ celdas de 40–60 m) y ≤ AREA_URBANA m² (≈ 20–30 m) en Puerto Ayora, La Cascada
    y Tomás de Berlanga. Cotas del DSM Copernicus GLO-30 (incluye techos y vegetación; ±2–4 m).
  - Lluvia: red IERSE-WSN (Universidad del Azuay), hietograma de 10 min. Crocker excluido. Escenarios: central (Los Guayabillos
    uniforme), bajo (× factor de reducción areal 0,85) y alto (gradiente con la cota entre Los Guayabillos y Santa Rosa).
  - Pérdidas: SCS-CN distribuido por cobertura (Parque 55, agrícola 76, urbano 90 en AMC II), con un factor sobre S calibrado
    para que la escorrentía total de la cuenca de La Cascada iguale la del modelo agregado (CN 76 central; CN 68 en sensibilidad).
    La lluvia de 00:00–12:00 entra en las abstracciones; la simulación empieza a las 12:00. Sin reinfiltración del agua encharcada.
  - Rugosidad de Manning por cobertura (urbano 0,08; agrícola 0,06; natural 0,08; mar 0,03), con sensibilidad ×0,6 y ×1,4.
  - Contorno: mar con nivel fijo NIVEL_MAR (sin dato de marea verificado); resto del contorno reflectivo (pared).

Uso:  .venv/bin/python -I -W ignore scripts/24_modelo2d_santa_cruz.py [escenario] [--horas H]
      escenarios: central (defecto), bajo, alto, manning_bajo, manning_alto, cn68
Salidas: estudios/santa-cruz/datos/modelo2d/<escenario>/ y figuras en estudios/santa-cruz/figuras/
Tiempo de ejecución: ver tiempo_ejecucion_s en resumen_<escenario>.json (Mac Apple Silicon, 10 núcleos).
"""
import csv, json, math, os, pathlib, sys, time, datetime as dt, warnings
warnings.filterwarnings("ignore")
import numpy as np, rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy.interpolate import RegularGridInterpolator
from shapely.geometry import shape, mapping, Point, LineString, Polygon
from shapely.ops import unary_union, transform as stransform
from pyproj import Transformer
import anuga

T0_RELOJ = time.time()
ROOT = pathlib.Path(__file__).resolve().parents[1]


def figuras(esc="central"):
    """Mapas de calado máximo y hora de llegada y animación GIF a partir de las salidas guardadas."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource, BoundaryNorm, ListedColormap
    import imageio.v2 as imageio
    d_ = ROOT / "estudios/santa-cruz/datos/modelo2d" / esc; fg = ROOT / "estudios/santa-cruz/figuras"; fg.mkdir(parents=True, exist_ok=True)
    rs_ = json.loads((d_ / f"resumen_{esc}.json").read_text()); ini = dt.datetime.fromisoformat(rs_.get("inicio", "2026-10-30T12:00"))
    r = rasterio.open(d_ / "calado_max_m.tif"); hmx = r.read(1); gtr = r.transform; H_, W_ = hmx.shape
    ext = [gtr.c, gtr.c + gtr.a * W_, gtr.f + gtr.e * H_, gtr.f]
    src = rasterio.open(ROOT / "descargas/dem_recortes/santa_cruz_dem.tif"); z = np.full((H_, W_), np.nan, "float32")
    reproject(rasterio.band(src, 1), z, src_transform=src.transform, src_crs=src.crs, dst_transform=gtr, dst_crs="EPSG:32715", resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=np.nan)
    fuera = hmx == -9999
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.nan_to_num(z, nan=0), vert_exag=3, dx=30, dy=30); hs[fuera | ~(z > 0.3)] = np.nan
    Tt = Transformer.from_crs(4326, 32715, always_xy=True).transform
    def capas(ax):
        ax.imshow(hs, extent=ext, cmap="gray", vmin=0, vmax=1, alpha=0.55)
        ax.imshow(np.where(fuera | ~(z > 0.3), 1, np.nan), extent=ext, cmap=ListedColormap(["#dbe9f6"]), alpha=1)
        for g, p in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") in ("LA CASCADA", "TOMAS DE BERLANGA")):
            for gg in getattr(g, "geoms", [g]): ax.plot(*gg.exterior.xy, color="#d62728", lw=0.9)
        for nm, (lo_, la_) in {"La Cascada": (-90.3137, -0.7335), "Tomás de Berlanga": (-90.3198, -0.7109), "Bellavista": (-90.3245, -0.6928)}.items():
            x, y = Tt(lo_, la_); ax.plot(x, y, "o", ms=3, color="#d62728"); ax.text(x + 120, y, nm, fontsize=7, color="#7a0000")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    bounds = [0.1, 0.5, 1, 2, 5]; cm = ListedColormap(["#c6dbef", "#6baed6", "#2171b5", "#08306b"])
    fig, ax = plt.subplots(figsize=(6, 9.5)); capas(ax)
    hm = np.where((hmx >= 0.1) & ~fuera, hmx, np.nan)
    im = ax.imshow(np.clip(hm, 0, 4.99), extent=ext, cmap=cm, norm=BoundaryNorm(bounds, cm.N))
    cb = fig.colorbar(im, ax=ax, shrink=0.45, pad=0.01); cb.set_label("Calado máximo (m)"); cb.set_ticklabels(["0,1", "0,5", "1", "2", "5"])
    ax.set_title(f"Calado máximo simulado desde {ini.strftime('%d-%b %H:%M')} (escenario {esc})", fontsize=10)
    fig.text(0.02, 0.01, f"Modelo 2D rain-on-grid ({rs_.get('motor', '')}, celda/malla {rs_.get('celda_m', '')} m) sobre DSM GLO-30 (techos y vegetación; ±2–4 m). Lluvia IERSE-WSN. Preliminar.", fontsize=6.2, color="#555")
    fig.savefig(fg / f"m2d_calado_max_{esc}.png", dpi=170, bbox_inches="tight"); plt.close(fig)
    tl = rasterio.open(d_ / "hora_llegada_h_desde_12h.tif").read(1)
    fig, ax = plt.subplots(figsize=(6, 9.5)); capas(ax)
    tt = np.where((tl >= 0) & (hmx >= 0.3), ini.hour + tl, np.nan)
    v0, v1 = (14, 24) if ini.hour == 12 else (np.nanpercentile(tt, 2), np.nanpercentile(tt, 98))
    im = ax.imshow(tt, extent=ext, cmap="plasma_r", vmin=v0, vmax=v1)
    cb = fig.colorbar(im, ax=ax, shrink=0.45, pad=0.01); cb.set_label(f"Hora de llegada (calado ≥ 0,1 m), {ini.strftime('%d-%b')}, UTC−6")
    tk = list(range(int(np.ceil(v0)), int(v1) + 1, 2)); cb.set_ticks(tk); cb.set_ticklabels([f"{h_ % 24:02d}:00" for h_ in tk])
    ax.set_title(f"Hora de llegada del agua (zonas con calado máximo ≥ 0,3 m; escenario {esc})", fontsize=9.5)
    fig.savefig(fg / f"m2d_hora_llegada_{esc}.png", dpi=170, bbox_inches="tight"); plt.close(fig)
    npz = np.load(d_ / "cuadros_10min.npz"); C = npz["calado"].astype("float32"); hh = npz["horas_desde_12h"]
    imgs = []
    for k in range(len(hh)):
        fig, ax = plt.subplots(figsize=(4.2, 6.6), dpi=90); capas(ax)
        f_ = np.where((C[k] >= 0.1) & ~fuera, C[k], np.nan)
        ax.imshow(np.clip(f_, 0, 4.99), extent=ext, cmap=cm, norm=BoundaryNorm(bounds, cm.N))
        hora = (ini + dt.timedelta(hours=float(hh[k]))).strftime("%d-%b %H:%M")
        ax.set_title(f"{hora} (UTC−6) — calado ≥ 0,1 m", fontsize=9)
        fig.canvas.draw(); imgs.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()); plt.close(fig)
    imageio.mimsave(fg / f"anim_30oct_{esc}.gif", imgs, duration=0.25, loop=0)
    print("figuras:", fg)


if len(sys.argv) > 1 and sys.argv[1] == "figuras":
    import matplotlib
    exec_figs = True
else:
    exec_figs = False
LC = ROOT / "estudios/la-cascada/datos"
ESC = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") and sys.argv[1] != "figuras" else "central"
HORAS_ARG = float(sys.argv[sys.argv.index("--horas") + 1]) if "--horas" in sys.argv else None
MOTOR = sys.argv[sys.argv.index("--motor") + 1] if "--motor" in sys.argv else "anuga"
OUT = ROOT / "estudios/santa-cruz/datos/modelo2d" / (ESC + ("_anuga" if MOTOR == "anuga" else "")); OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "estudios/santa-cruz/figuras"; FIG.mkdir(parents=True, exist_ok=True)
EPSG = 32715; CELDA = 30.0
AREA_GENERAL = 2500.0; AREA_URBANA = 500.0
NIVEL_MAR = 0.75                         # m sobre el cero del DSM (EGM2008); marea no verificada
FONDO_MAR = -3.0
EVENTOS = {"30oct": (dt.datetime(2026, 10, 30, 12, 0), 20.0, "lluvia_ierse_30oct_5min.csv"),          # inicio de la simulación, horas, lluvia
           "03oct": (dt.datetime(2026, 10, 3, 10, 0), 38.0, "lluvia_ierse_validacion_5min.csv"),       # 3 y 4 de octubre (68 + 44 mm en Los Guayabillos)
           "23oct": (dt.datetime(2026, 10, 23, 0, 0), 20.0, "lluvia_ierse_validacion_5min.csv")}       # 97 mm en Santa Rosa; 0 mm en Los Guayabillos
YIELD_S = 60.0; FRAME_S = 600.0
H_LLEGADA = 0.10                         # calado que define la «llegada» del agua
ARF = 0.85; COTA_G, COTA_SR = 178.0, 416.0
CN_II = {"parque": 55, "agricola": 76, "urbano": 90}
# juego (b): pérdida inicial + pérdida constante (IL–CL), aplicada también al agua que escurre (pérdidas de transmisión en el basalto)
IL_MM = {"parque": 20.0, "agricola": 20.0, "urbano": 5.0}
F_MMH = {"parque": 25.0, "agricola": 25.0, "urbano": 5.0}
N_MANNING = {"parque": 0.08, "agricola": 0.06, "urbano": 0.08, "mar": 0.03}
CN_OBJETIVO = 76
_A = dict(perdidas="scs", fn=1.0, cn=76); _B = dict(perdidas="ilcl", fn=1.0, cn=None)
ESCENARIOS = {"central": dict(_A, lluvia="G", evento="30oct"), "bajo": dict(_A, lluvia="ARF", evento="30oct"), "alto": dict(_A, lluvia="grad", evento="30oct"),
              "manning_bajo": dict(_A, lluvia="G", fn=0.6, evento="30oct"), "manning_alto": dict(_A, lluvia="G", fn=1.4, evento="30oct"),
              "cn68": dict(_A, lluvia="G", cn=68, evento="30oct"),
              "a_03oct": dict(_A, lluvia="G", evento="03oct"), "a_23oct": dict(_A, lluvia="grad", evento="23oct"),
              "b_central": dict(_B, lluvia="G", evento="30oct"), "b_alto": dict(_B, lluvia="grad", evento="30oct"), "b_bajo": dict(_B, lluvia="ARF", evento="30oct"),
              "b_03oct": dict(_B, lluvia="G", evento="03oct"), "b_23oct": dict(_B, lluvia="grad", evento="23oct"),
              "b_manning_bajo": dict(_B, lluvia="G", fn=0.6, evento="30oct"), "b_manning_alto": dict(_B, lluvia="G", fn=1.4, evento="30oct")}
CFG = ESCENARIOS[ESC]
INICIO, HORAS, LLUVIA_CSV = EVENTOS[CFG["evento"]]
HORAS = HORAS_ARG or HORAS
T_ANTECEDENTE = INICIO.replace(hour=0, minute=0)
T = Transformer.from_crs(4326, EPSG, always_xy=True).transform
TI = Transformer.from_crs(EPSG, 4326, always_xy=True).transform
PUNTOS = {"La Cascada (punto bajo)": (-90.31452, -0.73401), "La Cascada (centro)": (-90.31369, -0.73350),
          "La Cascada (entrada rama N)": (-90.31291, -0.73265), "Tomás de Berlanga (escuela)": (-90.3198, -0.7109),
          "Tomás de Berlanga (cauce)": (-90.31885, -0.70988), "Bellavista (centro, llegada SC-003)": (-90.324511, -0.692806),
          "Matazarnos (vaso SC-002)": (-90.312636, -0.736178), "Pelican Bay (vaso SC-001)": (-90.309669, -0.742954)}


def feats(rel, cond=lambda p: True):
    return [(stransform(T, shape(f["geometry"]).buffer(0) if f["geometry"]["type"].endswith("Polygon") else shape(f["geometry"])), f["properties"])
            for f in json.loads((ROOT / rel).read_text())["features"] if f["properties"].get("isla", "Santa Cruz") == "Santa Cruz" and cond(f["properties"])]


if exec_figs:
    figuras(sys.argv[2] if len(sys.argv) > 2 else "central"); sys.exit(0)

# ---------------------------------------------------------------- DEM
src = rasterio.open(ROOT / "descargas/dem_recortes/santa_cruz_dem.tif")
tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG}", src.width, src.height, *src.bounds, resolution=CELDA)
dem = np.full((h, w), -9999, "float32")
reproject(rasterio.band(src, 1), dem, src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs=f"EPSG:{EPSG}",
          resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
mar_r = (dem == -9999) | (dem <= 0.3)
demf = np.where(dem == -9999, FONDO_MAR, dem)
xs = tr.c + CELDA * (np.arange(w) + .5); ys = tr.f - CELDA * (np.arange(h) + .5)
interp = RegularGridInterpolator((ys[::-1], xs), demf[::-1], bounds_error=False, fill_value=FONDO_MAR)

# ---------------------------------------------------------------- dominio
pa = max([g for g, p in feats("capas/dem/cuencas_localidad.geojson", lambda p: p.get("destino") == "Puerto Ayora")], key=lambda g: g.area)
pa = max(getattr(pa, "geoms", [pa]), key=lambda g: g.area)
casc_c = unary_union([stransform(T, shape(f["geometry"])) for f in json.loads((LC / "cuenca_cascada.geojson").read_text())["features"]])
tierra = unary_union([pa, casc_c]).buffer(150)
mar_geo = unary_union([shape(s) for s, v in shapes(mar_r.astype("uint8"), mask=mar_r, transform=tr)])
franja_mar = tierra.buffer(400).intersection(mar_geo)
dom = unary_union([tierra, franja_mar]).buffer(30).buffer(-30).simplify(40)
dom = max(getattr(dom, "geoms", [dom]), key=lambda g: g.area)
dom = Polygon(dom.exterior)
X0, Y0 = [math.floor(v / 1000) * 1000 for v in dom.bounds[:2]]
coords = [(x - X0, y - Y0) for x, y in list(dom.exterior.coords)[:-1]]
tags = {"tierra": [], "mar": []}
for i in range(len(coords)):
    a, b = coords[i], coords[(i + 1) % len(coords)]
    zm = float(interp([[(a[1] + b[1]) / 2 + Y0, (a[0] + b[0]) / 2 + X0]])[0])
    tags["mar" if zm <= 0.3 else "tierra"].append(i)
urb = [g for g, p in feats("capas/igm/zona_urbana.geojson") if p.get("nam") == "Puerto Ayora"]
tdb = [g for g, p in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") == "TOMAS DE BERLANGA")]
fino = unary_union(urb + tdb + [casc_c.buffer(-1).intersection(Point(T(-90.3137, -0.7335)).buffer(900))]).intersection(dom.buffer(-60))
interiores = [[[(x - X0, y - Y0) for x, y in list(gp.exterior.coords)[:-1]], AREA_URBANA] for gp in getattr(fino, "geoms", [fino]) if gp.area > 2e4]
if MOTOR == "lisflood":
    # ============================================================ motor inercial local (Bates et al. 2010; LISFLOOD-FP «acc»), numpy
    G_ACC = 9.81; ALFA = 0.7; DX = float(os.environ.get("CELDA_2D", CELDA)); H_MIN = 1e-3
    gx0, gy0, gx1, gy1 = dom.bounds
    Wg = int(math.ceil((gx1 - gx0) / DX)); Hg = int(math.ceil((gy1 - gy0) / DX))
    gtr = rasterio.Affine(DX, 0, gx0, 0, -DX, gy1)
    GX = gx0 + DX * (np.arange(Wg) + .5); GY = gy1 - DX * (np.arange(Hg) + .5)
    MX, MY = np.meshgrid(GX, GY)
    z = interp(np.c_[MY.ravel(), MX.ravel()]).reshape(Hg, Wg).astype("float64")
    act = rasterize([(dom, 1)], out_shape=(Hg, Wg), transform=gtr).astype(bool)
    mar = act & (z <= 0.3); z[mar] = np.minimum(z[mar], FONDO_MAR)
    tierra_ = act & ~mar
    urb_ = [g for g, p in feats("capas/igm/zona_urbana.geojson") if p.get("nam") == "Puerto Ayora"]
    pobl_ = [g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")] + urb_
    agr_ = [g for g, p in feats("export/galapagos/zona_agricola.geojson")]
    r_urb = rasterize([(g, 1) for g in pobl_], out_shape=(Hg, Wg), transform=gtr).astype(bool) & tierra_
    r_agr = rasterize([(g, 1) for g in agr_], out_shape=(Hg, Wg), transform=gtr).astype(bool) & tierra_ & ~r_urb
    cobr = np.full((Hg, Wg), "parque", dtype=object); cobr[r_agr] = "agricola"; cobr[r_urb] = "urbano"; cobr[mar] = "mar"
    nman = np.vectorize(lambda c: N_MANNING[c])(cobr).astype(float) * np.where(mar, 1.0, CFG["fn"])
    DT_B = 600.0
    nb = int(((INICIO - T_ANTECEDENTE).total_seconds() + EVENTOS[CFG["evento"]][1] * 3600) // DT_B) + 1
    serie = {}
    for f in csv.DictReader(open(LC / LLUVIA_CSV)):
        k = int((dt.datetime.fromisoformat(f["fecha_hora_local"]) - T_ANTECEDENTE).total_seconds() // DT_B)
        if 0 <= k < nb: serie.setdefault(f["estacion"], np.zeros(nb))[k] += float(f["lluvia_mm"] or 0)
    G_, SR_ = serie.get("Los Guayabillos", np.zeros(nb)), serie.get("Santa Rosa", np.zeros(nb))
    alfa_r = np.round(np.clip((z - COTA_G) / (COTA_SR - COTA_G), 0, 1) * 4) / 4 if CFG["lluvia"] == "grad" else np.zeros_like(z)

    def lluvia(b):
        if CFG["lluvia"] == "G": return G_
        if CFG["lluvia"] == "ARF": return ARF * G_
        return (1 - b) * G_ + b * SR_

    def scs(Pc, cn, k):
        S = k * (25400 / cn - 254); Ia = 0.2 * S
        return np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0)

    en_casc_r = rasterize([(casc_c, 1)], out_shape=(Hg, Wg), transform=gtr).astype(bool) & tierra_
    K_S = objetivo = None
    if CFG["perdidas"] == "scs":
        objetivo = float(sum(scs(np.cumsum(lluvia(b))[-1], CFG["cn"], 1.0) * (en_casc_r & (alfa_r == b)).sum() for b in np.unique(alfa_r)) / en_casc_r.sum())

        def esc_total(k):
            return sum(scs(np.cumsum(lluvia(b))[-1], CN_II[c_], k) * (en_casc_r & (cobr == c_) & (alfa_r == b)).sum()
                       for c_ in ("parque", "agricola", "urbano") for b in np.unique(alfa_r)) / en_casc_r.sum()
        lo, hi = 0.05, 5.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if esc_total(mid) > objetivo: lo = mid
            else: hi = mid
        K_S = (lo + hi) / 2
        print(f"[{ESC}] calibración: escorrentía objetivo {objetivo:.1f} mm; factor sobre S = {K_S:.3f}", flush=True)
    k0 = int((INICIO - T_ANTECEDENTE).total_seconds() // DT_B)
    nbs = nb - k0 + 1
    TASA = np.zeros((nbs, Hg, Wg), "float32")                      # m/s aplicada en cada bloque de 10 min
    INF = np.zeros((Hg, Wg))                                         # pérdida constante (m/s) sobre el agua presente (juego b)
    for c_ in ("parque", "agricola", "urbano"):
        for b in np.unique(alfa_r):
            m = (cobr == c_) & (alfa_r == b) & tierra_
            if not m.any(): continue
            if CFG["perdidas"] == "scs": dQ = np.diff(scs(np.cumsum(lluvia(b)), CN_II[c_], K_S), prepend=0)
            else: dQ = np.diff(np.maximum(np.cumsum(lluvia(b)) - IL_MM[c_], 0.0), prepend=0)
            e = np.r_[dQ[k0:] / 1000 / DT_B, 0.0][:nbs]
            TASA[:, m] = e[:, None]
        if CFG["perdidas"] == "ilcl": INF[(cobr == c_) & tierra_] = F_MMH[c_] / 1000 / 3600
    h = np.where(mar, NIVEL_MAR - z, 0.0); qx = np.zeros((Hg, Wg + 1)); qy = np.zeros((Hg + 1, Wg))
    wx = act[:, :-1] & act[:, 1:]; wy = act[:-1, :] & act[1:, :]

    def pix(lo_, la_):
        x, y = T(lo_, la_); return int((gy1 - y) // DX), int((x - gx0) // DX)
    pts_r = {nm: pix(*ll) for nm, ll in PUNTOS.items()}
    cruces = [r for r in csv.DictReader(open(ROOT / "estudios/santa-cruz/datos/cruces.csv")) if r["isla"] == "Santa Cruz"] if (ROOT / "estudios/santa-cruz/datos/cruces.csv").exists() else []
    cruces = [r for r in cruces if dom.contains(Point(T(float(r["lon"]), float(r["lat"]))))]
    cruces.sort(key=lambda r: -float(r["area_km2"] or 0)); sel_cr = []
    for r in cruces:
        p_ = Point(T(float(r["lon"]), float(r["lat"])))
        if all(p_.distance(q) > 400 for q, _ in sel_cr): sel_cr.append((p_, r))
        if len(sel_cr) >= 6: break
    for p_, r in sel_cr:
        pts_r[f"Cruce {r['id']} ({r['via_nombre'] or r['via_highway']}, {float(r['area_km2']):.1f} km²)"] = pix(*TI(p_.x, p_.y))
    barrio = unary_union([g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("nombre") == "La Cascada")] +
                         [g for g, p in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") == "LA CASCADA")])
    bx0, by0, bx1, by1 = barrio.bounds
    rs_ = int((gy1 - (by1 + 60)) // DX); cs0 = int((bx0 - 300 - gx0) // DX); cs1 = int((bx1 + 300 - gx0) // DX)
    hmax = np.zeros((Hg, Wg)); vmax = np.zeros((Hg, Wg)); t_lleg = np.full((Hg, Wg), np.nan); t_hmax = np.full((Hg, Wg), np.nan)
    series = {nm: [] for nm in pts_r}; secc = []; frames = []; tf = []
    t = 0.0; t_fin = HORAS * 3600; prox_y = 0.0; vol_mar = 0.0; vol_inf = 0.0; vol_lluvia = 0.0; nstep = 0
    while t < t_fin - 1e-6:
        hw = np.where(tierra_, h, 0.0)
        dt_ = min(ALFA * DX / math.sqrt(G_ACC * max(float(hw.max()), 0.01)), 10.0)
        if prox_y > t: dt_ = min(dt_, prox_y - t)
        eta = z + h
        hf = np.maximum(eta[:, :-1], eta[:, 1:]) - np.maximum(z[:, :-1], z[:, 1:])
        nf = 0.5 * (nman[:, :-1] + nman[:, 1:])
        Sx = (eta[:, 1:] - eta[:, :-1]) / DX
        q = qx[:, 1:-1]
        ok_ = wx & (hf > H_MIN)
        hfs = np.where(ok_, hf, 1.0)
        qn = (q - G_ACC * hfs * dt_ * Sx) / (1 + G_ACC * dt_ * nf ** 2 * np.abs(q) / hfs ** (7 / 3))
        qx[:, 1:-1] = np.where(ok_, qn, 0.0)
        hf = np.maximum(eta[:-1, :], eta[1:, :]) - np.maximum(z[:-1, :], z[1:, :])
        nf = 0.5 * (nman[:-1, :] + nman[1:, :])
        Sy = (eta[1:, :] - eta[:-1, :]) / DX                      # fila creciente = hacia el sur
        q = qy[1:-1, :]
        ok_ = wy & (hf > H_MIN)
        hfs = np.where(ok_, hf, 1.0)
        qn = (q - G_ACC * hfs * dt_ * Sy) / (1 + G_ACC * dt_ * nf ** 2 * np.abs(q) / hfs ** (7 / 3))
        qy[1:-1, :] = np.where(ok_, qn, 0.0)
        out = (np.maximum(qx[:, 1:], 0) + np.maximum(-qx[:, :-1], 0) + np.maximum(qy[1:, :], 0) + np.maximum(-qy[:-1, :], 0)) * dt_ / DX
        fac = np.where(out > h, h / np.maximum(out, 1e-12), 1.0)
        fx = np.where(qx[:, 1:-1] > 0, fac[:, :-1], fac[:, 1:]); qx[:, 1:-1] *= fx
        fy = np.where(qy[1:-1, :] > 0, fac[:-1, :], fac[1:, :]); qy[1:-1, :] *= fy
        dh = (qx[:, :-1] - qx[:, 1:] + qy[:-1, :] - qy[1:, :]) * dt_ / DX
        vol_mar += float(dh[mar].sum()) * DX * DX
        h = h + dh
        kb = min(int(t // DT_B), nbs - 1)
        lluv = TASA[kb] * dt_; h = h + lluv; vol_lluvia += float(lluv[tierra_].sum()) * DX * DX
        if CFG["perdidas"] == "ilcl":
            perd = np.minimum(h, INF * dt_); perd[~tierra_] = 0; vol_inf += float(perd.sum()) * DX * DX; h = h - perd
        h = np.maximum(h, 0.0); h[mar] = NIVEL_MAR - z[mar]; h[~act] = 0.0
        t += dt_; nstep += 1
        if t >= prox_y - 1e-6:
            hl = np.where(tierra_, h, 0.0)
            ux = 0.5 * (np.abs(qx[:, :-1]) + np.abs(qx[:, 1:])); uy = 0.5 * (np.abs(qy[:-1, :]) + np.abs(qy[1:, :]))
            vel = np.where(hl > 0.05, np.hypot(ux, uy) / np.maximum(hl, 0.05), 0.0)
            nuevo = hl > hmax; t_hmax[nuevo] = t; hmax = np.maximum(hmax, hl); vmax = np.maximum(vmax, vel)
            ll = np.isnan(t_lleg) & (hl >= H_LLEGADA); t_lleg[ll] = t
            for nm, (r_, c_) in pts_r.items(): series[nm].append((t, float(hl[r_, c_]), float(z[r_, c_] + hl[r_, c_]), float(vel[r_, c_])))
            q_ent = float(np.clip(qy[rs_ + 1, cs0:cs1], 0, None).sum() * DX)
            secc.append((t, q_ent, vol_mar, vol_lluvia, float(hl.sum() * DX * DX), vol_inf))
            if abs(prox_y % FRAME_S) < 1e-6: frames.append(hl.astype("float16")); tf.append(t)
            if abs(prox_y % 3600) < 1e-6:
                print(f"[{ESC}] {(INICIO + dt.timedelta(seconds=t)).strftime('%d-%b %H:%M')}  vol. tierra {hl.sum() * DX * DX / 1e6:.2f} hm³  "
                      f"h La Cascada {hl[pts_r['La Cascada (punto bajo)']]:.2f} m  Q entrada {q_ent:.0f} m³/s  pasos {nstep}  ({time.time() - T0_RELOJ:.0f} s)", flush=True)
            prox_y += YIELD_S
    T_RUN = time.time() - T0_RELOJ
    reloj = lambda s_: (INICIO + dt.timedelta(seconds=float(s_))).strftime("%Y-%m-%dT%H:%M")
    prof = dict(driver="GTiff", height=Hg, width=Wg, count=1, dtype="float32", crs=f"EPSG:{EPSG}", transform=gtr, nodata=-9999.0, compress="deflate")
    rasters = {"calado_max_m": np.where(act, np.where(mar, 0, hmax), -9999), "velocidad_max_ms": np.where(act, np.where(mar, 0, vmax), -9999),
               "hora_llegada_h_desde_inicio": np.where(tierra_ & ~np.isnan(t_lleg), t_lleg / 3600, -9999),
               "hora_calado_max_h_desde_inicio": np.where(tierra_ & (hmax >= H_LLEGADA), t_hmax / 3600, -9999)}
    for nm, v in rasters.items():
        with rasterio.open(OUT / f"{nm}.tif", "w", **prof) as d:
            d.write(v.astype("float32"), 1); d.update_tags(escenario=ESC, inicio=INICIO.isoformat() + " UTC-6", motor="LISFLOOD-ACC numpy")
    import shutil
    for a_, b_ in (("hora_llegada_h_desde_inicio", "hora_llegada_h_desde_12h"), ("hora_calado_max_h_desde_inicio", "hora_calado_max_h_desde_12h")):
        shutil.copy(OUT / f"{a_}.tif", OUT / f"{b_}.tif")
    hr = np.where(tierra_, hmax, 0.0); fc = []
    for a, b, lab in [(0.1, 0.5, "0,1–0,5 m"), (0.5, 1.0, "0,5–1 m"), (1.0, 2.0, "1–2 m"), (2.0, 99, "> 2 m")]:
        m = (hr >= a) & (hr < b)
        if not m.any(): continue
        g = unary_union([shape(s_) for s_, _ in shapes(m.astype("uint8"), mask=m, transform=gtr)]).simplify(5)
        fc.append({"type": "Feature", "properties": {"clase": lab, "calado_min_m": a, "calado_max_m": b if b < 99 else None, "area_ha": round(g.area / 1e4, 1), "escenario": ESC},
                   "geometry": json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s_: round(float(s_), 6))})
    (OUT / "calado_max_clases.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": fc}, ensure_ascii=False))
    with open(OUT / "series_puntos.csv", "w", newline="") as fh:
        w_ = csv.writer(fh); w_.writerow(["punto", "lon", "lat", "fecha_hora_utc6", "calado_m", "nivel_m", "velocidad_ms"])
        for nm, s_ in series.items():
            r_, c_ = pts_r[nm]; lo_, la_ = TI(GX[c_], GY[r_])
            for tt_, hh, ss, vv in s_: w_.writerow([nm, round(lo_, 6), round(la_, 6), reloj(tt_), round(hh, 3), round(ss, 3), round(vv, 3)])
    S_ = np.array(secc)
    qmar = np.r_[0, np.diff(S_[:, 2]) / np.diff(S_[:, 0])]
    with open(OUT / "caudales_secciones.csv", "w", newline="") as fh:
        w_ = csv.writer(fh); w_.writerow(["fecha_hora_utc6", "q_entrada_la_cascada_m3s", "q_salida_mar_m3s", "lluvia_neta_acum_m3", "volumen_en_tierra_m3", "perdida_constante_acum_m3"])
        for i, (tt_, a, b, c, d_, e_) in enumerate(secc): w_.writerow([reloj(tt_), round(a, 2), round(qmar[i], 2), round(c), round(d_), round(e_)])
    np.savez_compressed(OUT / "cuadros_10min.npz", calado=np.array(frames, dtype="float16"), horas_desde_inicio=np.array(tf) / 3600,
                        horas_desde_12h=np.array(tf) / 3600, transform=np.array(gtr)[:6], epsg=EPSG)
    ser = {nm: np.array(s_) for nm, s_ in series.items()}

    def hito(nm):
        s_ = ser[nm]; i = int(s_[:, 1].argmax())
        return {"calado_max_m": round(float(s_[i, 1]), 2), "nivel_max_m": round(float(s_[i, 2]), 2), "hora_calado_max": reloj(s_[i, 0]),
                "hora_llegada_0.1m": reloj(s_[np.argmax(s_[:, 1] >= H_LLEGADA), 0]) if (s_[:, 1] >= H_LLEGADA).any() else None,
                "velocidad_max_ms": round(float(s_[:, 3].max()), 2)}
    ient = int(S_[:, 1].argmax())
    res = {"escenario": ESC, "config": CFG, "motor": "LISFLOOD-ACC (Bates et al. 2010), numpy", "celdas": int(act.sum()), "celda_m": DX,
           "area_km2": round(act.sum() * DX * DX / 1e6, 2), "nivel_mar_m": NIVEL_MAR, "evento": CFG["evento"], "inicio": INICIO.isoformat(),
           "factor_S_calibrado": round(K_S, 3) if K_S else None, "escorrentia_objetivo_mm": round(objetivo, 1) if objetivo else None,
           "perdidas_ilcl": {"IL_mm": IL_MM, "F_mmh": F_MMH} if CFG["perdidas"] == "ilcl" else None,
           "pasos": nstep, "tiempo_ejecucion_s": round(T_RUN),
           "puntos": {nm: hito(nm) for nm in ser},
           "entrada_la_cascada": {"q_max_m3s": round(float(S_[ient, 1]), 1), "hora_q_max": reloj(S_[ient, 0]), "volumen_m3": int(np.trapezoid(S_[:, 1], S_[:, 0]))},
           "salida_mar": {"q_max_m3s": round(float(qmar.max()), 1), "hora": reloj(S_[int(qmar.argmax()), 0]), "volumen_m3": int(S_[-1, 2])},
           "balance_m3": {"lluvia_neta_aplicada": int(S_[-1, 3]), "perdida_constante": int(S_[-1, 5]), "al_mar": int(S_[-1, 2]), "en_tierra_final": int(S_[-1, 4])},
           "area_inundada_ha": {f_["properties"]["clase"]: f_["properties"]["area_ha"] for f_ in fc}}
    (OUT / f"resumen_{ESC}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("config",)}, ensure_ascii=False, indent=1)[:4000])
    sys.exit(0)
domain = anuga.create_domain_from_regions(coords, boundary_tags=tags, maximum_triangle_area=AREA_GENERAL, interior_regions=interiores,
                                          use_cache=False, verbose=False)
XG = X0 + domain.geo_reference.xllcorner; YG = Y0 + domain.geo_reference.yllcorner     # ANUGA guarda coordenadas relativas a su origen
domain.set_name(f"modelo2d_{ESC}"); domain.set_datadir(str(OUT)); domain.set_store(False)
domain.set_flow_algorithm("DE0")
try:
    import os
    domain.set_multiprocessor_mode(2); domain.set_omp_num_threads(int(os.environ.get("N_HILOS", 8)), verbose=False)
except Exception:
    pass
cx, cy = domain.centroid_coordinates[:, 0] + XG, domain.centroid_coordinates[:, 1] + YG
NT = len(cx); areas = domain.areas
zc = interp(np.c_[cy, cx]).astype(float)
es_mar = zc <= 0.3
zc[es_mar] = np.minimum(zc[es_mar], FONDO_MAR)
domain.set_quantity("elevation", numeric=zc, location="centroids")
domain.set_quantity("stage", numeric=np.where(es_mar, NIVEL_MAR, zc), location="centroids")
print(f"[{ESC}] malla: {NT} triángulos; área {areas.sum() / 1e6:.1f} km²; mar {es_mar.sum()} triángulos", flush=True)

# ---------------------------------------------------------------- coberturas, Manning, CN
pts = [Point(x, y) for x, y in zip(cx, cy)]
def dentro(geoms):
    from shapely.strtree import STRtree
    t_ = STRtree(geoms); out = np.zeros(NT, bool)
    for i, p_ in enumerate(pts):
        if len(t_.query(p_, predicate="within")): out[i] = True
    return out
pobl = [g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")] + urb
agr = [g for g, p in feats("export/galapagos/zona_agricola.geojson")]
es_urb = dentro(pobl); es_agr = dentro(agr) & ~es_urb
cob = np.where(es_mar, "mar", np.where(es_urb, "urbano", np.where(es_agr, "agricola", "parque")))
n_tri = np.array([N_MANNING[c] for c in cob]) * np.where(es_mar, 1.0, CFG["fn"])
domain.set_quantity("friction", numeric=n_tri, location="centroids")

# ---------------------------------------------------------------- lluvia y exceso (SCS-CN distribuido, calibrado)
DT_B = 600.0
nb = int(((INICIO - T_ANTECEDENTE).total_seconds() + EVENTOS[CFG["evento"]][1] * 3600) // DT_B) + 1      # serie completa del evento
serie = {}
for f in csv.DictReader(open(LC / LLUVIA_CSV)):
    k = int((dt.datetime.fromisoformat(f["fecha_hora_local"]) - T_ANTECEDENTE).total_seconds() // DT_B)
    if 0 <= k < nb: serie.setdefault(f["estacion"], np.zeros(nb))[k] += float(f["lluvia_mm"] or 0)
G_, SR_ = serie["Los Guayabillos"], serie["Santa Rosa"]
alfa = np.clip((zc - COTA_G) / (COTA_SR - COTA_G), 0, 1)
BANDAS = np.round(alfa * 4) / 4 if CFG["lluvia"] == "grad" else np.zeros(NT)     # 5 bandas de cota para el gradiente


def lluvia(b):
    if CFG["lluvia"] == "G": return G_
    if CFG["lluvia"] == "ARF": return ARF * G_
    return (1 - b) * G_ + b * SR_


def scs(Pc, cn, k):
    S = k * (25400 / cn - 254); Ia = 0.2 * S
    return np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0)


en_casc = np.array([casc_c.contains(p_) for p_ in pts]) & ~es_mar
k0 = int((INICIO - T_ANTECEDENTE).total_seconds() // DT_B)
ops = []; ops_inf = []; vol_exceso_total = 0.0; K_S = None; objetivo = None
if CFG["perdidas"] == "scs":
    # calibración: escorrentía total en la cuenca de La Cascada = modelo agregado con CN uniforme (mismas lluvias)
    def esc_total(k):
        v = 0.0
        for c_ in ("parque", "agricola", "urbano"):
            for b in np.unique(BANDAS):
                m = en_casc & (cob == c_) & (BANDAS == b)
                if m.any(): v += scs(np.cumsum(lluvia(b))[-1], CN_II[c_], k) * areas[m].sum()
        return v / areas[en_casc].sum()
    objetivo = float(np.sum([scs(np.cumsum(lluvia(b))[-1], CFG["cn"], 1.0) * areas[en_casc & (BANDAS == b)].sum() for b in np.unique(BANDAS)]) / areas[en_casc].sum())
    lo, hi = 0.05, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if esc_total(mid) > objetivo: lo = mid
        else: hi = mid
    K_S = (lo + hi) / 2
    print(f"[{ESC}] calibración: escorrentía objetivo {objetivo:.1f} mm; factor sobre S = {K_S:.3f}", flush=True)
for c_ in ("parque", "agricola", "urbano"):
    for b in np.unique(BANDAS):
        idx = np.flatnonzero((cob == c_) & (BANDAS == b) & ~es_mar)
        if not idx.size: continue
        if CFG["perdidas"] == "scs":
            dQ = np.diff(scs(np.cumsum(lluvia(b)), CN_II[c_], K_S), prepend=0)
        else:                                                                 # lluvia bruta una vez satisfecha la pérdida inicial
            Pc = np.cumsum(lluvia(b)); dQ = np.diff(np.maximum(Pc - IL_MM[c_], 0.0), prepend=0)
        exc = np.r_[dQ[k0:] / 1000 / DT_B, 0.0]                               # m/s desde el inicio de la simulación
        vol_exceso_total += float(exc.sum() * DT_B * areas[idx].sum())
        ops.append(anuga.Rate_operator(domain, rate=(lambda t, e=exc: float(e[min(int(t // DT_B), len(e) - 1)])), indices=idx))
    if CFG["perdidas"] == "ilcl":
        idx = np.flatnonzero((cob == c_) & ~es_mar)
        if idx.size: ops_inf.append(anuga.Rate_operator(domain, rate=-F_MMH[c_] / 1000 / 3600, indices=idx))     # se recorta al agua disponible
# lluvia directa sobre el mar (sin pérdidas) no se añade: el nivel del mar es fijo

# ---------------------------------------------------------------- contorno
domain.set_boundary({"tierra": anuga.Reflective_boundary(domain), "mar": anuga.Dirichlet_boundary([NIVEL_MAR, 0.0, 0.0])})

# ---------------------------------------------------------------- puntos de control y secciones
tri_pts = {}
for nm, (lo_, la_) in PUNTOS.items():
    x, y = T(lo_, la_); tri_pts[nm] = int(np.argmin((cx - x) ** 2 + (cy - y) ** 2))
cruces = [r for r in csv.DictReader(open(ROOT / "estudios/santa-cruz/datos/cruces.csv")) if r["isla"] == "Santa Cruz"] if (ROOT / "estudios/santa-cruz/datos/cruces.csv").exists() else []
cruces = [r for r in cruces if dom.contains(Point(T(float(r["lon"]), float(r["lat"]))))]
cruces.sort(key=lambda r: -float(r["area_km2"] or 0))
sel_cr = []
for r in cruces:
    p_ = Point(T(float(r["lon"]), float(r["lat"])))
    if all(p_.distance(q) > 400 for q, _ in sel_cr): sel_cr.append((p_, r))
    if len(sel_cr) >= 6: break
for p_, r in sel_cr:
    tri_pts[f"Cruce {r['id']} ({r['via_nombre'] or r['via_highway']}, {float(r['area_km2']):.1f} km²)"] = int(np.argmin((cx - p_.x) ** 2 + (cy - p_.y) ** 2))
barrio = unary_union([g for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("nombre") == "La Cascada")] +
                     [g for g, p in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") == "LA CASCADA")])
# sección de entrada a La Cascada: línea E–O 60 m al norte del barrio (cruza las dos ramas antes de entrar)
bx0, by0, bx1, by1 = barrio.bounds
SEC_ENTRADA = [(bx0 - 300 - X0, by1 + 60 - Y0), (bx1 + 300 - X0, by1 + 60 - Y0)]   # ANUGA: coordenadas «absolutas» de su marco (local + su origen)
en_tierra = ~es_mar
vol_tierra_prev = None

# ---------------------------------------------------------------- simulación
hmax = np.zeros(NT); vmax = np.zeros(NT); t_lleg = np.full(NT, np.nan); t_hmax = np.full(NT, np.nan)
series = {nm: [] for nm in tri_pts}; secc = []; frames = []; tiempos_frames = []
st_q = domain.quantities["stage"]; el_q = domain.quantities["elevation"]; xm_q = domain.quantities["xmomentum"]; ym_q = domain.quantities["ymomentum"]
exc_acum = 0.0
for t in domain.evolve(yieldstep=YIELD_S, finaltime=HORAS * 3600):
    hc = np.maximum(st_q.centroid_values - el_q.centroid_values, 0.0)
    vel = np.where(hc > 0.01, np.hypot(xm_q.centroid_values, ym_q.centroid_values) / np.maximum(hc, 0.01), 0.0)
    nuevo = hc > hmax; t_hmax[nuevo] = t; hmax = np.maximum(hmax, hc); vmax = np.maximum(vmax, np.where(hc > 0.05, vel, 0.0))
    ll = np.isnan(t_lleg) & (hc >= H_LLEGADA); t_lleg[ll] = t
    for nm, i in tri_pts.items(): series[nm].append((t, float(hc[i]), float(st_q.centroid_values[i]), float(vel[i])))
    vt = float((hc * areas)[en_tierra].sum())
    q_exc = sum(float(o.rate(t)) * areas[o.indices].sum() for o in ops)
    bfi = float(domain.get_boundary_flux_integral())
    q_mar = (-(bfi - vol_tierra_prev) / YIELD_S) if vol_tierra_prev is not None else 0.0     # flujo saliente por el contorno de mar
    vol_tierra_prev = bfi
    secc.append((t, abs(domain.get_flow_through_cross_section(SEC_ENTRADA)), q_mar, q_exc, vt))
    if abs(t % FRAME_S) < 1e-6:
        frames.append(hc.astype("float16")); tiempos_frames.append(t)
    if abs(t % 3600) < 1e-6:
        print(f"[{ESC}] {(INICIO + dt.timedelta(seconds=t)).strftime('%d-%b %H:%M')}  vol. tierra {vt / 1e6:.2f} hm³  h La Cascada {hc[tri_pts['La Cascada (punto bajo)']]:.2f} m  "
              f"Q entrada {secc[-1][1]:.0f} m³/s  ({time.time() - T0_RELOJ:.0f} s)", flush=True)
T_RUN = time.time() - T0_RELOJ

# ---------------------------------------------------------------- salidas
reloj = lambda s: (INICIO + dt.timedelta(seconds=float(s))).strftime("%Y-%m-%dT%H:%M")
import matplotlib; matplotlib.use("Agg")
from matplotlib.tri import Triangulation
nodes = domain.get_nodes() + np.array([XG, YG]); tris = domain.get_triangles()
tri_ = Triangulation(nodes[:, 0], nodes[:, 1], tris); finder = tri_.get_trifinder()
gx0, gy0, gx1, gy1 = dom.bounds
GX = np.arange(gx0, gx1, CELDA) + CELDA / 2; GY = np.arange(gy1, gy0, -CELDA) - CELDA / 2
MX, MY = np.meshgrid(GX, GY); tid = finder(MX, MY)
gtr = rasterio.Affine(CELDA, 0, gx0, 0, -CELDA, gy1)
def a_raster(v, nodata=-9999.0):
    r = np.where(tid >= 0, v[np.maximum(tid, 0)], nodata).astype("float32"); return r
prof = dict(driver="GTiff", height=MX.shape[0], width=MX.shape[1], count=1, dtype="float32", crs=f"EPSG:{EPSG}", transform=gtr, nodata=-9999.0, compress="deflate")
hmax_land = np.where(es_mar, 0.0, hmax)
rasters = {"calado_max_m": hmax_land, "velocidad_max_ms": np.where(es_mar, 0.0, vmax),
           "hora_llegada_h_desde_12h": np.where(es_mar | np.isnan(t_lleg), -9999, t_lleg / 3600),
           "hora_calado_max_h_desde_12h": np.where(es_mar | (hmax < H_LLEGADA), -9999, t_hmax / 3600)}
for nm, v in rasters.items():
    with rasterio.open(OUT / f"{nm}.tif", "w", **prof) as d:
        d.write(a_raster(v), 1)
        d.update_tags(escenario=ESC, inicio="2026-10-30T12:00 UTC-6", nota="horas desde las 12:00 del 30-oct (UTC-6)" if "hora" in nm else "")
hr = a_raster(hmax_land)
clases = [(0.1, 0.5, "0,1–0,5 m"), (0.5, 1.0, "0,5–1 m"), (1.0, 2.0, "1–2 m"), (2.0, 99, "> 2 m")]
fc = []
for a, b, lab in clases:
    m = (hr >= a) & (hr < b)
    if not m.any(): continue
    g = unary_union([shape(s) for s, _ in shapes(m.astype("uint8"), mask=m, transform=gtr)]).simplify(5)
    fc.append({"type": "Feature", "properties": {"clase": lab, "calado_min_m": a, "calado_max_m": b if b < 99 else None, "area_ha": round(g.area / 1e4, 1), "escenario": ESC},
               "geometry": json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))})
(OUT / "calado_max_clases.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": fc}, ensure_ascii=False))
with open(OUT / "series_puntos.csv", "w", newline="") as fh:
    w_ = csv.writer(fh); w_.writerow(["punto", "lon", "lat", "fecha_hora_utc6", "calado_m", "nivel_m", "velocidad_ms"])
    for nm, s in series.items():
        lo_, la_ = TI(cx[tri_pts[nm]], cy[tri_pts[nm]])
        for t, hh, ss, vv in s: w_.writerow([nm, round(lo_, 6), round(la_, 6), reloj(t), round(hh, 3), round(ss, 3), round(vv, 3)])
with open(OUT / "caudales_secciones.csv", "w", newline="") as fh:
    w_ = csv.writer(fh); w_.writerow(["fecha_hora_utc6", "q_entrada_la_cascada_m3s", "q_salida_mar_m3s", "q_lluvia_aplicada_m3s", "volumen_en_tierra_m3"])
    for t, a, b, c, d_ in secc: w_.writerow([reloj(t), round(a, 2), round(b, 2), round(c, 2), round(d_)])
np.savez_compressed(OUT / "cuadros_10min.npz", calado=np.array([a_raster(np.where(es_mar, 0, f.astype(float)), 0) for f in frames]).astype("float16"),
                    horas_desde_12h=np.array(tiempos_frames) / 3600, transform=np.array(gtr)[:6], epsg=EPSG)
# resumen y validación
ser = {nm: np.array(s) for nm, s in series.items()}
def hito(nm):
    s = ser[nm]; i = int(s[:, 1].argmax())
    return {"calado_max_m": round(float(s[i, 1]), 2), "nivel_max_m": round(float(s[i, 2]), 2), "hora_calado_max": reloj(s[i, 0]),
            "hora_llegada_0.1m": reloj(s[np.argmax(s[:, 1] >= H_LLEGADA), 0]) if (s[:, 1] >= H_LLEGADA).any() else None,
            "velocidad_max_ms": round(float(s[:, 3].max()), 2)}
S_ = np.array(secc)
ient = int(S_[:, 1].argmax())
res = {"escenario": ESC, "config": CFG, "motor": f"ANUGA {anuga.__version__} DE0", "triangulos": NT, "area_km2": round(float(areas.sum()) / 1e6, 2),
       "nivel_mar_m": NIVEL_MAR, "factor_S_calibrado": round(K_S, 3) if K_S else None, "escorrentia_objetivo_mm": round(objetivo, 1) if objetivo else None,
       "perdidas_ilcl": {"IL_mm": IL_MM, "F_mmh": F_MMH} if CFG["perdidas"] == "ilcl" else None, "evento": CFG["evento"], "inicio": INICIO.isoformat(),
       "volumen_exceso_total_m3": int(vol_exceso_total), "tiempo_ejecucion_s": round(T_RUN),
       "puntos": {nm: hito(nm) for nm in ser},
       "entrada_la_cascada": {"q_max_m3s": round(float(S_[ient, 1]), 1), "hora_q_max": reloj(S_[ient, 0]),
                              "volumen_m3": int(np.trapezoid(S_[:, 1], S_[:, 0]))},
       "salida_mar": {"q_max_m3s_balance": round(float(S_[1:, 2].max()), 1), "hora": reloj(S_[1 + int(S_[1:, 2].argmax()), 0]),
                      "volumen_m3": int(np.trapezoid(np.clip(S_[:, 2], 0, None), S_[:, 0]))},
       "volumen_en_tierra_final_m3": int(S_[-1, 4]),
       "area_inundada_ha": {lab: f_["properties"]["area_ha"] for f_ in fc for lab in [f_["properties"]["clase"]]}}
(OUT / f"resumen_{ESC}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != "config"}, ensure_ascii=False, indent=1))
