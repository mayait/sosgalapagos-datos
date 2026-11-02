"""Modelo hidrodinámico 2D «rain-on-grid» preliminar: Puerto Baquerizo Moreno, El Progreso y el campus USFQ / GSC.

Método (documentado también en estudios/san-cristobal/texto/12_modelo2d.md):
  - Ecuaciones de aguas someras simplificadas con el esquema INERCIAL LOCAL de Bates, Horritt y Fewtrell (2010,
    J. Hydrol. 387:33-45): flujo por caras de celda con término de presión + fricción de Manning semiimplícita;
        q(t+dt) = [q(t) − g·hf·dt·∂η/∂x] / [1 + g·dt·n²·|q(t)| / hf^(7/3)],   hf = max(η_i, η_j) − max(z_i, z_j).
    Paso de tiempo adaptativo (CFL): dt = α·Δx / sqrt(g·h_max), α = 0,7, con tope DT_MAX.
    Estabilizadores habituales en ladera empinada: limitador de Froude (|q| ≤ FR_MAX·hf·sqrt(g·hf)) y limitador de
    volumen (una celda no puede ceder en un paso más agua de la que tiene).
  - Lluvia sobre la malla («rain-on-grid»): la lluvia neta de cada celda es la escorrentía SCS-CN (Ia = 0,2 S) calculada
    con la lluvia acumulada y el CN de su cobertura (Parque/natural, agrícola, poblado). Infiltración distribuida.
  - Manning por cobertura (N_CLASE) y en los cauces D8 de ≥ 0,2 km².
  - Terreno: DSM Copernicus GLO-30 (incluye techos y vegetación; ±2–4 m), reproyectado a UTM 16S. Sin red pluvial,
    alcantarillas ni puentes: es un modelo de superficie.
  - Dominio: cuencas D8 que drenan a Puerto Baquerizo Moreno y a El Progreso, más las zonas pobladas y un margen de 150 m.
    Fuera del dominio y en el mar la lámina se anula (contornos absorbentes) y el volumen se contabiliza como salida.
  - Trazador pasivo: el agua de lluvia neta caída en la cuenca de la «quebrada del campus» (aguas arriba del rellano,
    script 17) se marca y se transporta aguas abajo (advección upwind conservativa) para saber si llega al campus.

Escenarios de lluvia (uniforme sobre el dominio):
  (i)  100 mm en 24 h, distribución SCS tipo II.
  (ii) Tormenta MEDIDA el 30-oct-2026 en Los Guayabillos (Santa Cruz, IERSE-WSN, 5 min; 178,8 mm hasta las 21:25,
       cuando la estación dejó de transmitir) TRASLADADA a San Cristóbal («qué pasaría si»). No es lluvia de San Cristóbal.
  (iii) Como (ii) con suelo húmedo (CN AMC III), sensibilidad.
  (iv) Como (ii) con malla de 15 m (DSM remuestreado), sensibilidad de resolución para el campus.

Uso:  .venv/bin/python -I scripts/25_modelo2d_san_cristobal.py [escenario ...]     (desde geodatos/; por defecto, todos)
Salidas: estudios/san-cristobal/datos/modelo2d/
"""
import csv, json, math, pathlib, sys, tempfile, time, datetime as dt_
import numpy as np, rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy import ndimage
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, transform as stransform
from pyproj import Transformer
from pysheds.grid import Grid
from numba import njit

ROOT = pathlib.Path(__file__).resolve().parents[1]
EST = ROOT / "estudios/san-cristobal"
OUT = EST / "datos/modelo2d"
FIG = EST / "figuras"                     # el generador web busca las figuras aquí
DEM_CRUDO = ROOT / "descargas/dem_recortes/san_cristobal_dem.tif"
DEM_QUEMADO = ROOT / "descargas/dem_recortes/san_cristobal_dem_quemado.tif"
HIETO = ROOT / "estudios/santa-cruz/datos/lluvias/hietograma_5min.csv"
HIETO_ALT = ROOT / "estudios/la-cascada/datos/lluvia_ierse_30oct_5min.csv"
CAMPUS_OSM = EST / "datos/insumos/campus_usfq_osm.geojson"
ISLA = "San Cristóbal"
EPSG = 32716

# ---------------------------------------------------------------- parámetros del modelo
G = 9.81
ALFA_CFL = 0.7
DT_MAX = 10.0              # s
H_MIN = 1e-3               # m, lámina mínima para que una cara conduzca
FR_MAX = 1.0               # limitador de Froude en las caras
MARGEN_M = 150             # margen del dominio alrededor de las cuencas
A_CAUCE_KM2 = 0.2          # celdas de cauce (Manning de cauce)
N_CLASE = {"natural": 0.08, "agricola": 0.06, "poblado": 0.04, "cauce": 0.045}
CN_CLASE = {"natural": 60, "agricola": 76, "poblado": 90}      # AMC II, como en el script 17
UMBRALES_LLEGADA = (0.1, 0.3)
CLASES_CALADO = ((0.1, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 99.0))
ETIQUETA_CLASE = {(0.1, 0.5): "0,1–0,5 m", (0.5, 1.0): "0,5–1 m", (1.0, 2.0): "1–2 m", (2.0, 99.0): ">2 m"}   # valores exactos que usa el mapa web
DT_SERIE_S = 300           # series cada 5 min
DT_CUADRO_S = 600          # cuadros cada 10 min
ESCENARIOS = {
    "scs100": dict(nombre="100 mm en 24 h, SCS tipo II", lluvia="scs", P=100.0, dur_h=28.0, amc="II", celda=30.0, inicio="00:00"),
    "guayabillos": dict(nombre="Tormenta medida en Los Guayabillos el 30-oct, trasladada", lluvia="guayabillos", dur_h=26.0, amc="II", celda=30.0),
    "guayabillos_amc3": dict(nombre="Ídem, suelo húmedo (CN AMC III)", lluvia="guayabillos", dur_h=26.0, amc="III", celda=30.0),
    "guayabillos_15m": dict(nombre="Ídem, malla de 15 m", lluvia="guayabillos", dur_h=26.0, amc="II", celda=15.0),
    # pruebas de trazador para la hidrografía del Plan de Acción SC-4-09-2026 (UGR del GAD San Cristóbal): ¿se separa Divino Niño de la
    # Galápagos? ¿recoge Alvear aguas de Divino Niño? Solo se exporta el reparto del agua marcada entre las salidas al mar.
    "traz_galapagos_15m": dict(nombre="Trazador: agua de la Galápagos/Barrio Frío aguas arriba de la ciudad (tormenta trasladada, 15 m)",
                               lluvia="guayabillos", dur_h=26.0, amc="II", celda=15.0, solo_trazador=True,
                               trazador=[(-89.59376, -0.90615), (-89.59188, -0.91157), (-89.59376, -0.90805), (-89.59619, -0.91347),
                                         (-89.59996, -0.91211), (-89.59323, -0.91374)]),
    "traz_divinonino_15m": dict(nombre="Trazador: agua de Divino Niño aguas arriba de la ciudad (tormenta trasladada, 15 m)",
                                lluvia="guayabillos", dur_h=26.0, amc="II", celda=15.0, solo_trazador=True,
                                trazador=[(-89.60345, -0.89963), (-89.60022, -0.90397)]),
    "traz_galapagos_100mm_15m": dict(nombre="Trazador Galápagos con 100 mm SCS II (15 m)", lluvia="scs", P=100.0, dur_h=28.0, amc="II", celda=15.0,
                                     solo_trazador=True, trazador=[(-89.59376, -0.90615), (-89.59188, -0.91157), (-89.59376, -0.90805),
                                                                   (-89.59619, -0.91347), (-89.59996, -0.91211), (-89.59323, -0.91374)]),
}
USFQ_LONLAT = (-89.6089, -0.8955)
PUNTOS = {   # series temporales (lon, lat)
    "campus_GSC": (-89.60865, -0.89548),
    "campus_USFQ": (-89.60888, -0.89549),
    "campus_esquina_NE_via_universidad": (-89.6083, -0.89502),
    "rellano_quebrada_campus": (-89.60695, -0.89556),
    "escuela_alvear": (-89.6080, -0.8975),
    "barrio_frio_registro_2024": (-89.61372, -0.90379),
    "barrio_frio_desembocadura": (-89.61315, -0.90261),
    "divino_nino_salida": (-89.60965, -0.89936),
    "manzanillo_registro_2019": (-89.59940, -0.90846),
    "el_progreso_iess_2021": (-89.55727, -0.90859),
    "el_progreso_escuela_darwin_2024": (-89.55625, -0.90812),
    "el_progreso_vaso_V01": (-89.55766, -0.90373),
    # sectores del Plan de Acción SC-4-09-2026 (UGR del GAD San Cristóbal)
    "hospital_oskar_jandl": (-89.60523, -0.89986),
    "colegio_ignacio_hernandez_via_jaime_roldos": (-89.60401, -0.90199),
    "manzanillo_puente_perimetral": (-89.6058, -0.90835),
    "la_planada_registro_2025": (-89.59404, -0.91131),
    "playa_de_oro": (-89.60951, -0.89986),
}
SALIDAS_MAR = {   # tramos de costa para repartir el agua que sale al mar (radio de asignación SALIDA_RADIO_M)
    "Galápagos / Barrio Frío (playa, Poza de las Garzas)": (-89.61315, -0.90261),
    "Centro: muelles de pasajeros y de pescadores": (-89.61120, -0.90050),
    "Divino Niño (Playa de Oro)": (-89.60965, -0.89936),
    "Playa Mann sur (S03; Alvear según el D8)": (-89.60965, -0.89800),
    "Playa Mann frente al campus": (-89.60930, -0.89514),
    "Norte de Playa Mann (S04)": (-89.61018, -0.89448),
}
SALIDA_RADIO_M = 120
SECCIONES = {   # caudal por sección transversal al cauce D8 (lon, lat del punto de control; semiancho en m)
    "El Manzanillo (entrada, PBM-L01)": ((-89.59376, -0.90615), 90),
    "Barrio Frío (desembocadura, PBM-S01)": ((-89.61315, -0.90261), 90),
    "Divino Niño (salida, PBM-S02)": ((-89.60965, -0.89936), 90),
    "Escuela Alvear (salida, PBM-S03)": ((-89.60965, -0.89800), 90),
    "Quebrada del campus (rellano)": ((-89.60695, -0.89556), 60),
    "El Progreso (quebrada IGM, PRO-L01)": ((-89.55282, -0.90618), 60),
}
VENTANA_CIUDAD = (-89.6175, -0.9145, -89.5900, -0.8905)     # lon0, lat0, lon1, lat1 (mapas y animación)
VENTANA_PROGRESO = (-89.5640, -0.9150, -89.5460, -0.8980)
VENTANA_CAMPUS = (-89.6125, -0.9010, -89.6020, -0.8920)

T = Transformer.from_crs(4326, EPSG, always_xy=True).transform
TI = Transformer.from_crs(EPSG, 4326, always_xy=True).transform
OFF = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)


def feats(rel, cond=lambda p: True):
    out = []
    for f in json.loads((ROOT / rel).read_text())["features"]:
        if f.get("geometry") and f["properties"].get("isla", ISLA) == ISLA and cond(f["properties"]):
            g = shape(f["geometry"]); g = g.buffer(0) if g.geom_type.endswith("Polygon") else g
            out.append((stransform(T, g), f["properties"]))
    return out


def a_utm(src_path, celda, bounds=None):
    src = rasterio.open(src_path)
    if bounds is None:
        tr, w, h = calculate_default_transform(src.crs, f"EPSG:{EPSG}", src.width, src.height, *src.bounds, resolution=celda)
    else:
        x0, y0, x1, y1 = bounds
        w, h = int(round((x1 - x0) / celda)), int(round((y1 - y0) / celda))
        tr = rasterio.Affine(celda, 0, x0, 0, -celda, y1)
    arr = np.full((h, w), -9999, "float32")
    reproject(rasterio.band(src, 1), arr, src_transform=src.transform, src_crs=src.crs, dst_transform=tr,
              dst_crs=f"EPSG:{EPSG}", resampling=Resampling.bilinear, src_nodata=-9999, dst_nodata=-9999)
    return arr, tr


# ---------------------------------------------------------------- núcleo numérico (numba)
@njit(cache=True)
def flujos(z, h, qx, qy, n2, act, dt, dx, g, hmin, frmax):
    H, W = h.shape
    for i in range(H):
        for j in range(1, W):
            a = act[i, j - 1]; b = act[i, j]
            if not (a or b):
                qx[i, j] = 0.0; continue
            z1 = z[i, j - 1]; z2 = z[i, j]; e1 = z1 + h[i, j - 1]; e2 = z2 + h[i, j]
            hf = max(e1, e2) - max(z1, z2)
            if hf <= hmin:
                qx[i, j] = 0.0; continue
            nn = 0.5 * (n2[i, j - 1] + n2[i, j])
            q0 = qx[i, j]
            q = (q0 - g * hf * dt * (e2 - e1) / dx) / (1.0 + g * dt * nn * abs(q0) / hf ** (7.0 / 3.0))
            ql = frmax * hf * math.sqrt(g * hf)
            if q > ql: q = ql
            if q < -ql: q = -ql
            qx[i, j] = q
    for i in range(1, H):
        for j in range(W):
            a = act[i - 1, j]; b = act[i, j]
            if not (a or b):
                qy[i, j] = 0.0; continue
            z1 = z[i - 1, j]; z2 = z[i, j]; e1 = z1 + h[i - 1, j]; e2 = z2 + h[i, j]
            hf = max(e1, e2) - max(z1, z2)
            if hf <= hmin:
                qy[i, j] = 0.0; continue
            nn = 0.5 * (n2[i - 1, j] + n2[i, j])
            q0 = qy[i, j]
            q = (q0 - g * hf * dt * (e2 - e1) / dx) / (1.0 + g * dt * nn * abs(q0) / hf ** (7.0 / 3.0))
            ql = frmax * hf * math.sqrt(g * hf)
            if q > ql: q = ql
            if q < -ql: q = -ql
            qy[i, j] = q


@njit(cache=True)
def continuidad(h, m, qx, qy, act, dt, dx, fac, abs_h, abs_m):
    """Limitador de volumen + actualización de lámina h y del trazador m. Devuelve el volumen absorbido (mar/contorno)."""
    H, W = h.shape
    for i in range(H):
        for j in range(W):
            out = max(qx[i, j + 1], 0.0) + max(-qx[i, j], 0.0) + max(qy[i + 1, j], 0.0) + max(-qy[i, j], 0.0)
            out *= dt / dx
            fac[i, j] = 1.0 if out <= h[i, j] or out == 0.0 else h[i, j] / out
    # aplicar factor del donante a cada cara
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
    absorb = 0.0
    hn = h.copy(); mn = m.copy()
    k = dt / dx
    for i in range(H):
        for j in range(W):
            # flujo de trazador en las 4 caras (concentración del donante)
            c = m[i, j] / h[i, j] if h[i, j] > 1e-9 else 0.0
            dh = 0.0; dm = 0.0
            q = qx[i, j]          # cara oeste: entra si q > 0
            if q > 0:
                cw = m[i, j - 1] / h[i, j - 1] if j > 0 and h[i, j - 1] > 1e-9 else 0.0
                dh += q; dm += q * cw
            else:
                dh += q; dm += q * c
            q = qx[i, j + 1]      # cara este: sale si q > 0
            if q > 0:
                dh -= q; dm -= q * c
            else:
                ce = m[i, j + 1] / h[i, j + 1] if j + 1 < W and h[i, j + 1] > 1e-9 else 0.0
                dh -= q; dm -= q * ce
            q = qy[i, j]          # cara norte: entra si q > 0
            if q > 0:
                cn = m[i - 1, j] / h[i - 1, j] if i > 0 and h[i - 1, j] > 1e-9 else 0.0
                dh += q; dm += q * cn
            else:
                dh += q; dm += q * c
            q = qy[i + 1, j]      # cara sur
            if q > 0:
                dh -= q; dm -= q * c
            else:
                cs = m[i + 1, j] / h[i + 1, j] if i + 1 < H and h[i + 1, j] > 1e-9 else 0.0
                dh -= q; dm -= q * cs
            hv = h[i, j] + k * dh
            mv = m[i, j] + k * dm
            if hv < 0: hv = 0.0
            if mv < 0: mv = 0.0
            if mv > hv: mv = hv
            if act[i, j]:
                hn[i, j] = hv; mn[i, j] = mv
            else:
                absorb += hv * dx * dx
                abs_h[i, j] += hv * dx * dx; abs_m[i, j] += mv * dx * dx
                hn[i, j] = 0.0; mn[i, j] = 0.0
    h[:, :] = hn; m[:, :] = mn
    return absorb


@njit(cache=True)
def maximos(h, qx, qy, t, hmax, vmax, hvmax, tl1, tl2, u1, u2, hmin_v):
    H, W = h.shape
    for i in range(H):
        for j in range(W):
            hh = h[i, j]
            if hh > hmax[i, j]: hmax[i, j] = hh
            if hh > hmin_v:
                ux = 0.5 * (qx[i, j] + qx[i, j + 1]); uy = 0.5 * (qy[i, j] + qy[i + 1, j])
                qq = math.sqrt(ux * ux + uy * uy)
                v = qq / hh
                if v > vmax[i, j]: vmax[i, j] = v
                if qq > hvmax[i, j]: hvmax[i, j] = qq
            if hh >= u1 and tl1[i, j] < 0: tl1[i, j] = t
            if hh >= u2 and tl2[i, j] < 0: tl2[i, j] = t


@njit(cache=True)
def flujo_frontera(qx, qy, mask, h, m, dx, dt):
    """Volumen (y volumen marcado) que entra en la región mask en este paso."""
    H, W = mask.shape
    vin = 0.0; min_ = 0.0
    for i in range(H):
        for j in range(1, W):
            a = mask[i, j - 1]; b = mask[i, j]
            if a == b: continue
            q = qx[i, j]
            if b and q > 0:          # entra en (i, j) desde el oeste
                vin += q * dx * dt; min_ += q * dx * dt * (m[i, j - 1] / h[i, j - 1] if h[i, j - 1] > 1e-9 else 0.0)
            elif a and q < 0:        # entra en (i, j-1) desde el este
                vin += -q * dx * dt; min_ += -q * dx * dt * (m[i, j] / h[i, j] if h[i, j] > 1e-9 else 0.0)
    for i in range(1, H):
        for j in range(W):
            a = mask[i - 1, j]; b = mask[i, j]
            if a == b: continue
            q = qy[i, j]
            if b and q > 0:
                vin += q * dx * dt; min_ += q * dx * dt * (m[i - 1, j] / h[i - 1, j] if h[i - 1, j] > 1e-9 else 0.0)
            elif a and q < 0:
                vin += -q * dx * dt; min_ += -q * dx * dt * (m[i, j] / h[i, j] if h[i, j] > 1e-9 else 0.0)
    return vin, min_


# ---------------------------------------------------------------- lluvia
TII_H = [0, 2, 4, 6, 7, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 11.75, 12, 12.5, 13, 13.5, 14, 16, 20, 24]
TII_F = [0, .022, .048, .080, .098, .120, .133, .147, .163, .181, .204, .235, .283, .357, .663, .735, .772, .799, .820, .880, .952, 1.0]


def curva_lluvia(esc):
    """Devuelve (función t_h -> lluvia acumulada en mm, etiqueta de la hora 0, descripción)."""
    if esc["lluvia"] == "scs":
        P = esc["P"]
        return (lambda t: P * np.interp(t, TII_H, TII_F)), None, {"total_mm": P, "max_1h_mm": round(P * 0.452, 1)}
    f = HIETO if HIETO.exists() else HIETO_ALT
    filas = [r for r in csv.DictReader(open(f, encoding="utf-8")) if r.get("estacion") == "Los Guayabillos"
             and r["fecha_hora_local"].startswith("2026-10-30")]
    t0 = dt_.datetime(2026, 10, 30, 0, 0)
    ts = np.array([(dt_.datetime.fromisoformat(r["fecha_hora_local"]) - t0).total_seconds() / 3600 for r in filas])
    pc = np.cumsum([float(r["lluvia_mm"] or 0) for r in filas])
    o = np.argsort(ts); ts, pc = ts[o], pc[o]
    ts = np.concatenate([[0.0], ts]); pc = np.concatenate([[0.0], pc])
    horas = np.arange(0, 24); ph = np.interp(horas + 1, ts, pc) - np.interp(horas, ts, pc)
    info = {"fuente": str(f.relative_to(ROOT)), "estacion": "Los Guayabillos (IERSE-WSN), Santa Cruz, ≈178 m", "total_mm": round(float(pc[-1]), 1),
            "fin_registro": filas[-1]["fecha_hora_local"], "max_1h_mm": round(float(ph.max()), 1), "hora_max_1h": f"{int(horas[ph.argmax()]):02d}:00–{int(horas[ph.argmax()]) + 1:02d}:00",
            "max_5min_mm": max(float(r["lluvia_mm"] or 0) for r in filas)}
    return (lambda t: np.interp(t, ts, pc)), t0, info


def exceso_scs(P, cn):
    S = 25400.0 / cn - 254.0; Ia = 0.2 * S
    return np.where(P > Ia, (P - Ia) ** 2 / (P - Ia + S), 0.0)


# ---------------------------------------------------------------- preparación del dominio (rejilla base de 30 m)
def preparar_base():
    dem, tr = a_utm(DEM_CRUDO, 30.0)
    demq, _ = a_utm(DEM_QUEMADO, 30.0)
    H, W = dem.shape
    sea = (dem == -9999) | (dem <= 0.5)
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "q.tif"
        with rasterio.open(p, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=f"EPSG:{EPSG}", transform=tr, nodata=-9999) as d:
            d.write(np.where(sea, -9999, demq).astype("float32"), 1)
        g = Grid.from_raster(str(p)); dq = g.read_raster(str(p))
        fdir = g.flowdir(g.resolve_flats(g.fill_depressions(g.fill_pits(dq))), dirmap=DIRMAP)
        F = np.asarray(fdir); A = np.asarray(g.accumulation(fdir, dirmap=DIRMAP)).astype(float) * 900 / 1e6
    A[sea] = 0
    rr, cc = np.indices((H, W))
    nr, nc = rr.copy(), cc.copy()
    for k, (a, b) in OFF.items():
        m = F == k; nr[m] += a; nc[m] += b
    ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W) & np.isin(F, list(OFF)) & ~sea
    nxt = (np.where(ok, nr, rr) * W + np.where(ok, nc, cc)).ravel()
    NN = H * W

    def aguas_arriba(mask):
        tg = np.where(mask.ravel(), np.arange(NN), -1); jj = nxt.copy()
        for _ in range(int(np.ceil(np.log2(NN))) + 1):
            un = tg == -1; tg[un] = tg[jj[un]]; jj = jj[jj]
        return (tg >= 0).reshape(H, W) & ~sea

    zp = feats("capas/final/zonas_pobladas.geojson"); manz = feats("capas/final/manzanas_inec.geojson")
    pbm = [g for g, p in zp if p.get("nombre") == "Puerto Baquerizo Moreno"]
    pbm += [g for g, p in zp if p.get("tipo") == "Huella edificada" and TI(*g.centroid.coords[0])[0] < -89.59]
    pbm += [g for g, p in manz if p["codigo"].startswith("200150")]
    prog_pt = Point(T(-89.5547, -0.9091))
    hue = [g for g, p in zp if p.get("tipo") == "Huella edificada"]
    prog = [min(hue, key=lambda g: g.distance(prog_pt))] + [g for g, p in manz if p["codigo"].startswith("200151")]
    zonas = {"Puerto Baquerizo Moreno": unary_union(pbm).buffer(0), "El Progreso": unary_union(prog).buffer(0)}
    zm = {k: rasterize([(v, 1)], out_shape=(H, W), transform=tr, all_touched=True).astype(bool) & ~sea for k, v in zonas.items()}
    up = aguas_arriba(zm["Puerto Baquerizo Moreno"] | zm["El Progreso"]) | zm["Puerto Baquerizo Moreno"] | zm["El Progreso"]
    # cuenca de la quebrada del campus aguas arriba del rellano (punto de control 1 del script 17) → trazador
    c_, r_ = ~tr * T(-89.60695, -0.89556); r1 = np.zeros((H, W), bool); r1[int(r_), int(c_)] = True
    cuenca_campus = aguas_arriba(r1) | r1
    dom = ndimage.binary_dilation(up, iterations=int(MARGEN_M / 30)) & ~sea
    rows, cols = np.where(ndimage.binary_dilation(dom, iterations=3))
    x0, y1 = tr * (cols.min(), rows.min()); x1, y0 = tr * (cols.max() + 1, rows.max() + 1)
    def aguas_arriba_de(puntos):
        m = np.zeros((H, W), bool)
        for lo, la in puntos:
            c_, r_ = ~tr * T(lo, la); m[int(r_), int(c_)] = True
        return aguas_arriba(m) | m
    return dict(tr=tr, dem=dem, A=A, F=F, sea=sea, dom=dom, cuenca_campus=cuenca_campus, zonas=zonas, aguas_arriba_de=aguas_arriba_de,
                bounds=(x0, y0, x1, y1), area_aportante_km2=float(up.sum() * 900 / 1e6))


def remuestrear_mascara(mask, tr_src, tr_dst, shape_dst):
    out = np.zeros(shape_dst, "uint8")
    reproject(mask.astype("uint8"), out, src_transform=tr_src, src_crs=f"EPSG:{EPSG}", dst_transform=tr_dst, dst_crs=f"EPSG:{EPSG}",
              resampling=Resampling.nearest)
    return out.astype(bool)


def guardar_tif(nombre, arr, tr, nodata=-9999.0):
    with rasterio.open(OUT / nombre, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype="float32",
                       crs=f"EPSG:{EPSG}", transform=tr, nodata=nodata, compress="deflate") as d:
        d.write(arr.astype("float32"), 1)


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


# ---------------------------------------------------------------- simulación de un escenario
def simular(clave, esc, base):
    celda = esc["celda"]
    dem, tr = a_utm(DEM_CRUDO, celda, base["bounds"])
    H, W = dem.shape
    sea = (dem == -9999) | (dem <= 0.5)
    dom = remuestrear_mascara(base["dom"], base["tr"], tr, (H, W)) & ~sea
    traz = remuestrear_mascara(base["cuenca_campus"] if "trazador" not in esc else base["aguas_arriba_de"](esc["trazador"]), base["tr"], tr, (H, W)) & dom
    Ac = np.zeros((H, W)); reproject(base["A"], Ac, src_transform=base["tr"], src_crs=f"EPSG:{EPSG}", dst_transform=tr, dst_crs=f"EPSG:{EPSG}", resampling=Resampling.max)
    cauce = (Ac >= A_CAUCE_KM2) & dom
    # coberturas
    pob = rasterize([(g, 1) for g, p in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("tipo") != "OSM farmyard")]
                    + [(g, 1) for g, p in feats("capas/final/manzanas_inec.geojson")], out_shape=(H, W), transform=tr).astype(bool)
    agr = rasterize([(g, 1) for g, _ in feats("export/galapagos/zona_agricola.geojson")], out_shape=(H, W), transform=tr).astype(bool)
    clase = np.where(pob, 2, np.where(agr, 1, 0))                 # 0 natural, 1 agrícola, 2 poblado
    n = np.choose(clase, [N_CLASE["natural"], N_CLASE["agricola"], N_CLASE["poblado"]]).astype(float)
    n[cauce & ~pob] = N_CLASE["cauce"]
    n2 = n ** 2
    cn_ii = np.array([CN_CLASE["natural"], CN_CLASE["agricola"], CN_CLASE["poblado"]], float)
    cn = cn_ii if esc["amc"] == "II" else 23 * cn_ii / (10 + 0.13 * cn_ii)
    fP, t0, info_ll = curva_lluvia(esc)
    z = np.where(sea, 0.0, dem).astype(np.float64)
    h = np.zeros((H, W)); m = np.zeros((H, W))
    qx = np.zeros((H, W + 1)); qy = np.zeros((H + 1, W)); fac = np.ones((H, W))
    hmax = np.zeros((H, W)); vmax = np.zeros((H, W)); hvmax = np.zeros((H, W))
    tl1 = -np.ones((H, W)); tl2 = -np.ones((H, W))
    mmax = np.zeros((H, W)); abs_h = np.zeros((H, W)); abs_m = np.zeros((H, W))                      # lámina máxima de agua marcada (de la quebrada del campus), muestreada cada 5 min
    act = dom.copy()
    # campus
    ux, uy = T(*USFQ_LONLAT); upt = Point(ux, uy)
    campus_osm = [stransform(T, shape(f["geometry"])) for f in json.loads(CAMPUS_OSM.read_text())["features"]]
    edif = feats("capas/final/edificios_exposicion.geojson")
    univ = [g for g, p in edif if p.get("tipo") == "university" and g.distance(upt) < 150]
    campus = unary_union(campus_osm + univ).convex_hull.buffer(15)
    cmask = rasterize([(campus, 1)], out_shape=(H, W), transform=tr, all_touched=True).astype(bool) & dom
    # puntos y secciones
    def rc(lon, lat):
        c, r = ~tr * T(lon, lat); return int(r), int(c)
    pts = {k: rc(*v) for k, v in PUNTOS.items()}
    secs = {}
    rb, cb = np.indices(base["F"].shape)
    for nm, ((lo, la), semi) in SECCIONES.items():
        cB, rB = ~base["tr"] * T(lo, la); rB, cB = int(rB), int(cB)
        d = OFF.get(int(base["F"][rB, cB]), (0, 1))                       # dirección D8 (fila, columna)
        nv = np.array([d[1], d[0]], float); nv /= np.hypot(*nv)            # normal (este, sur)
        pv = np.array([-nv[1], nv[0]])                                     # perpendicular
        x, y = T(lo, la); celdas = []
        for s_ in np.arange(-semi, semi + 1e-6, celda / 2):
            xs, ys = x + pv[0] * s_, y - pv[1] * s_                        # sur = −y
            c, r = ~tr * (xs, ys); celdas.append((int(r), int(c)))
        celdas = sorted(set(celdas))
        secs[nm] = (np.array(celdas), nv, (2 * semi + celda) / len(celdas))
    t_fin = esc["dur_h"] * 3600
    nser = int(t_fin // DT_SERIE_S) + 1
    serie = {k: np.zeros((nser, 2)) for k in pts}
    serie_q = {k: np.zeros(nser) for k in secs}
    serie_campus = np.zeros((nser, 4))       # vol. entrado acumulado, vol. marcado entrado acumulado, h máx en campus, lluvia acumulada
    cuadros, t_cuadros = [], []
    vin_c = vmk_c = 0.0
    vol_lluvia = vol_abs = vol_traz = 0.0
    t = 0.0; k_ser = 0; k_cua = 0; pasos = 0
    Pprev = 0.0; Qprev = np.zeros(3)
    area = celda * celda
    t_inicio = time.time()
    while t < t_fin - 1e-6:
        hm = float(h[act].max()) if act.any() else 0.0
        dt = min(DT_MAX, ALFA_CFL * celda / math.sqrt(G * max(hm, 0.01)))
        dt = min(dt, t_fin - t, (k_ser * DT_SERIE_S - t) if k_ser * DT_SERIE_S > t else DT_MAX)
        if dt <= 0: dt = 1e-3
        # lluvia neta SCS por clase
        P = float(fP((t + dt) / 3600)); Qc = exceso_scs(P, cn)
        dq = (Qc - Qprev) / 1000.0; Qprev = Qc
        add = np.where(act, dq[clase], 0.0)
        h += add; m += np.where(traz, add, 0.0)
        vol_lluvia += float(add.sum() * area); vol_traz += float((add * traz).sum() * area)
        flujos(z, h, qx, qy, n2, act, dt, celda, G, H_MIN, FR_MAX)
        vol_abs += continuidad(h, m, qx, qy, act, dt, celda, fac, abs_h, abs_m)
        a_, b_ = flujo_frontera(qx, qy, cmask, h, m, celda, dt); vin_c += a_; vmk_c += b_
        t += dt; pasos += 1
        maximos(h, qx, qy, t, hmax, vmax, hvmax, tl1, tl2, UMBRALES_LLEGADA[0], UMBRALES_LLEGADA[1], 0.05)
        if t >= k_ser * DT_SERIE_S - 1e-6 and k_ser < nser:
            ucx = 0.5 * (qx[:, :-1] + qx[:, 1:]); ucy = 0.5 * (qy[:-1, :] + qy[1:, :])
            for kk, (r, c) in pts.items():
                hh = h[r, c]; serie[kk][k_ser] = (hh, math.hypot(ucx[r, c], ucy[r, c]) / hh if hh > 0.05 else 0.0)
            for kk, (cl, nv, w) in secs.items():
                serie_q[kk][k_ser] = float(np.sum(ucx[cl[:, 0], cl[:, 1]] * nv[0] + ucy[cl[:, 0], cl[:, 1]] * nv[1]) * w)
            serie_campus[k_ser] = (vin_c, vmk_c, float(h[cmask].max()) if cmask.any() else 0.0, P)
            np.maximum(mmax, m, out=mmax)
            k_ser += 1
        if t >= k_cua * DT_CUADRO_S - 1e-6:
            cuadros.append(h.astype("float16")); t_cuadros.append(t); k_cua += 1
    vol_alm = float(h[act].sum() * area)
    dur = time.time() - t_inicio
    balance = {"lluvia_neta_m3": round(vol_lluvia), "salida_mar_y_contornos_m3": round(vol_abs), "almacenado_final_m3": round(vol_alm),
               "error_relativo": round((vol_lluvia - vol_abs - vol_alm) / max(vol_lluvia, 1), 5)}
    print(f"  {clave}: {pasos} pasos, {dur:.0f} s; balance {balance}")
    return dict(H=H, W=W, tr=tr, dem=dem, dom=dom, hmax=hmax, vmax=vmax, hvmax=hvmax, tl1=tl1, tl2=tl2, serie=serie, serie_q=serie_q,
                serie_campus=serie_campus, cuadros=cuadros, t_cuadros=t_cuadros, t0=t0, info_ll=info_ll, balance=balance, cmask=cmask,
                campus=campus, traz=traz, mmax=mmax, abs_h=abs_h, abs_m=abs_m, sea=sea, vol_traz=vol_traz, pasos=pasos, seg=dur, pts=pts, clase=clase, nser=nser, h_final=h.copy(), m_final=m.copy())


# ---------------------------------------------------------------- salidas
def hora_txt(t0, t_s):
    if t0 is None: return f"{t_s / 3600:.2f} h"
    return (t0 + dt_.timedelta(seconds=float(t_s))).strftime("%d-%b %H:%M")


def salidas_al_mar(res):
    """Reparte el volumen absorbido por el mar (total y marcado) entre los tramos de SALIDAS_MAR."""
    tr = res["tr"]; ab_h, ab_m = res["abs_h"], res["abs_m"]
    rs, cs = np.where(res["sea"] & (ab_h > 0))
    xy = np.array([tr * (c + .5, r + .5) for r, c in zip(rs, cs)]) if len(rs) else np.zeros((0, 2))
    cen = {k: np.array(T(*v)) for k, v in SALIDAS_MAR.items()}
    out = {k: [0.0, 0.0] for k in list(SALIDAS_MAR) + ["resto de la costa"]}
    for (x, y), r, c in zip(xy, rs, cs):
        d = {k: math.hypot(x - v[0], y - v[1]) for k, v in cen.items()}
        k = min(d, key=d.get)
        k = k if d[k] <= SALIDA_RADIO_M else "resto de la costa"
        out[k][0] += ab_h[r, c]; out[k][1] += ab_m[r, c]
    bordes = (~res["sea"]) & (ab_h > 0)
    out["bordes del dominio (tierra)"] = [float(ab_h[bordes].sum()), float(ab_m[bordes].sum())]
    tot_m = sum(v[1] for v in out.values()) + float(res["m_final"][res["dom"]].sum() * tr.a ** 2)
    return {k: {"vol_m3": round(v[0]), "vol_trazador_m3": round(v[1]), "fraccion_del_trazador": round(v[1] / tot_m, 3) if tot_m else None}
            for k, v in out.items()}, round(float(res["m_final"][res["dom"]].sum() * tr.a ** 2)), round(tot_m)


def exportar(clave, esc, res, R, base_zonas):
    tr, dom = res["tr"], res["dom"]
    sal, traz_alm, traz_tot = salidas_al_mar(res)
    if esc.get("solo_trazador"):
        guardar_tif(f"{clave}_agua_marcada_max.tif", np.where(dom & (res["mmax"] > 0.001), res["mmax"], -9999), tr)
        R["escenarios"][clave] = {"descripcion": esc["nombre"], "celda_m": esc["celda"], "trazador_puntos": esc["trazador"],
                                 "vol_lluvia_neta_marcada_m3": round(res["vol_traz"]), "salidas_al_mar": sal,
                                 "trazador_almacenado_al_final_m3": traz_alm, "balance_masa": res["balance"]}
        print("   salidas:", {k: (v["vol_m3"], v["vol_trazador_m3"], v["fraccion_del_trazador"]) for k, v in sal.items()})
        return
    hmax = np.where(dom, res["hmax"], -9999); vmax = np.where(dom & (res["hmax"] > 0.05), res["vmax"], -9999)
    tl = np.where(dom & (res["tl2"] >= 0), res["tl2"] / 3600, -9999); tl1 = np.where(dom & (res["tl1"] >= 0), res["tl1"] / 3600, -9999)
    guardar_tif(f"{clave}_calado_max.tif", hmax, tr); guardar_tif(f"{clave}_velocidad_max.tif", vmax, tr)
    guardar_tif(f"{clave}_hora_llegada_0.3m.tif", tl, tr); guardar_tif(f"{clave}_hora_llegada_0.1m.tif", tl1, tr)
    guardar_tif(f"{clave}_agua_quebrada_campus_max.tif", np.where(dom & (res["mmax"] > 0.001), res["mmax"], -9999), tr)
    guardar_tif(f"{clave}_hv_max.tif", np.where(dom & (res["hmax"] > 0.05), res["hvmax"], -9999), tr)
    # clases de calado → GeoJSON (con exposición)
    edif = feats("capas/final/edificios_exposicion.geojson")
    from shapely.strtree import STRtree
    te = STRtree([g for g, _ in edif])
    fs, resumen_cl = [], {}
    for lo, hi in CLASES_CALADO:
        msk = dom & (res["hmax"] >= lo) & (res["hmax"] < hi)
        if not msk.any(): continue
        geoms = [shape(s) for s, _ in shapes(msk.astype("uint8"), mask=msk, transform=tr)]
        u = unary_union(geoms)
        ne = len(te.query(u, predicate="intersects"))
        etiqueta = ETIQUETA_CLASE[(lo, hi)]
        resumen_cl[etiqueta] = {"area_ha": round(msk.sum() * tr.a ** 2 / 1e4, 1), "edificios_que_tocan": ne}
        for gg in getattr(u, "geoms", [u]):
            fs.append({"type": "Feature", "properties": {"clase": etiqueta, "calado_min_m": lo, "calado_max_m": hi if hi < 99 else None,
                                                         "escenario": esc["nombre"]}, "geometry": r6(gg.simplify(tr.a * 0.3))})
    (OUT / f"{clave}_calado_max_clases.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": fs}, ensure_ascii=False))
    # edificios por zona según el calado máximo en la celda de su centroide (el DSM incluye techos: es un indicador, no un conteo exacto)
    expo_zonas = {}
    for zn, zg in base_zonas.items():
        cnt = {f">={u}m": 0 for u in (0.1, 0.3, 0.5, 1.0)}; tot = 0
        for g, _ in edif:
            if not zg.contains(g.centroid): continue
            tot += 1
            c, r = ~tr * g.centroid.coords[0]; r, c = int(r), int(c)
            if 0 <= r < res["H"] and 0 <= c < res["W"]:
                for u in (0.1, 0.3, 0.5, 1.0):
                    if res["hmax"][r, c] >= u: cnt[f">={u}m"] += 1
        expo_zonas[zn] = {"edificios_en_zona": tot, "edificios_con_calado_max": cnt}
    # series
    t_ser = np.arange(res["nser"]) * DT_SERIE_S
    cab = ["tiempo_h", "hora"] + [f"{k}_h_m" for k in res["serie"]] + [f"{k}_v_ms" for k in res["serie"]] + \
          [f"Q_{k}_m3s" for k in res["serie_q"]] + ["campus_vol_entrado_m3", "campus_vol_entrado_quebrada_m3", "campus_h_max_m", "lluvia_acum_mm"]
    with open(OUT / f"{clave}_series.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cab)
        for i, tt in enumerate(t_ser):
            w.writerow([round(tt / 3600, 4), hora_txt(res["t0"], tt)] + [round(float(v[i, 0]), 3) for v in res["serie"].values()] +
                       [round(float(v[i, 1]), 2) for v in res["serie"].values()] + [round(float(v[i]), 2) for v in res["serie_q"].values()] +
                       [round(float(x), 1) for x in res["serie_campus"][i, :2]] + [round(float(res["serie_campus"][i, 2]), 3), round(float(res["serie_campus"][i, 3]), 1)])
    # cuadros para animación (recorte de la ventana de la ciudad), en cm uint16
    x0, y0 = T(*VENTANA_CIUDAD[:2]); x1, y1 = T(*VENTANA_CIUDAD[2:])
    c0, r1 = ~tr * (x0, y0); c1, r0 = ~tr * (x1, y1)
    r0, r1, c0, c1 = max(int(r0), 0), min(int(r1) + 1, res["H"]), max(int(c0), 0), min(int(c1) + 1, res["W"])
    np.savez_compressed(OUT / f"{clave}_cuadros_ciudad.npz", calado_cm=np.array([np.clip(cq[r0:r1, c0:c1].astype(float) * 100, 0, 65000).astype("uint16") for cq in res["cuadros"]]),
                        t_s=np.array(res["t_cuadros"]), transform=np.array(list(tr * rasterio.Affine.translation(c0, r0))[:6]), epsg=EPSG)
    # resumen
    pk = {}
    for k, v in res["serie"].items():
        i = int(v[:, 0].argmax()); pk[k] = {"h_max_m": round(float(v[:, 0].max()), 2), "hora_h_max": hora_txt(res["t0"], t_ser[i]), "v_max_ms": round(float(v[:, 1].max()), 2),
                                            "h_max_3x3_celdas_m": round(float(res["hmax"][max(res["pts"][k][0] - 1, 0):res["pts"][k][0] + 2, max(res["pts"][k][1] - 1, 0):res["pts"][k][1] + 2].max()), 2)}
    qk = {k: {"Q_max_m3s": round(float(v.max()), 1), "hora": hora_txt(res["t0"], t_ser[int(v.argmax())])} for k, v in res["serie_q"].items()}
    cm = res["cmask"]
    sc = res["serie_campus"]
    campus = {"celdas": int(cm.sum()), "h_max_m": round(float(res["hmax"][cm].max()), 2), "v_max_ms": round(float(res["vmax"][cm].max()), 2),
              "hv_max_m2s": round(float(res["hvmax"][cm].max()), 2),
              "hora_h_max": hora_txt(res["t0"], t_ser[int(sc[:, 2].argmax())]),
              "vol_entrado_m3": round(float(sc[-1, 0])), "vol_entrado_de_la_quebrada_m3": round(float(sc[-1, 1])),
              "fraccion_del_agua_de_la_quebrada_que_entra": round(float(sc[-1, 1]) / max(res["vol_traz"], 1), 3),
              "vol_lluvia_neta_quebrada_m3": round(res["vol_traz"]),
              "caudal_max_entrante_m3s": round(float(np.max(np.diff(sc[:, 0])) / DT_SERIE_S), 2),
              "caudal_max_entrante_quebrada_m3s": round(float(np.max(np.diff(sc[:, 1])) / DT_SERIE_S), 2),
              "lamina_max_agua_quebrada_en_campus_m": round(float(res["mmax"][cm].max()), 3),
              "celdas_campus_con_agua_quebrada_>1cm": int((res["mmax"][cm] > 0.01).sum())}
    # el trazador alrededor del campus: concentración máxima no se guarda; se informa el volumen
    R["escenarios"][clave] = {"descripcion": esc["nombre"], "celda_m": esc["celda"], "amc": esc["amc"], "lluvia": res["info_ll"], "duracion_simulada_h": esc["dur_h"],
                             "pasos": res["pasos"], "tiempo_calculo_s": round(res["seg"]), "balance_masa": res["balance"],
                             "clases_calado": resumen_cl, "exposicion_por_zona": expo_zonas, "salidas_al_mar": sal, "puntos": pk, "secciones": qk, "campus": campus,
                             "celdas_dominio": int(dom.sum()), "area_dominio_km2": round(float(dom.sum() * tr.a ** 2 / 1e6), 2)}
    print("   campus:", campus)
    print("   secciones:", qk)


# ---------------------------------------------------------------- figuras
def figuras(clave, res, R):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm, LightSource
    FIG.mkdir(parents=True, exist_ok=True)
    tr = res["tr"]; dem = np.where(res["dem"] <= 0.5, np.nan, res["dem"])
    ls = LightSource(azdeg=315, altdeg=45)
    cmap = ListedColormap(["#c6dbef", "#6baed6", "#2171b5", "#08306b"]); norm = BoundaryNorm([0.1, 0.5, 1, 2, 99], 4)

    def ventana(v):
        x0, y0 = T(*v[:2]); x1, y1 = T(*v[2:])
        c0, r1 = ~tr * (x0, y0); c1, r0 = ~tr * (x1, y1)
        return max(int(r0), 0), min(int(r1) + 1, res["H"]), max(int(c0), 0), min(int(c1) + 1, res["W"])

    edif = feats("capas/final/edificios_exposicion.geojson")
    for nm, v in (("ciudad", VENTANA_CIUDAD), ("progreso", VENTANA_PROGRESO), ("campus", VENTANA_CAMPUS)):
        r0, r1, c0, c1 = ventana(v)
        ext = [tr.c + c0 * tr.a, tr.c + c1 * tr.a, tr.f + r1 * tr.e, tr.f + r0 * tr.e]
        fig, ax = plt.subplots(figsize=(10, 9))
        sub = dem[r0:r1, c0:c1]
        ax.imshow(ls.hillshade(np.nan_to_num(sub, nan=0), vert_exag=2, dx=tr.a, dy=tr.a), cmap="gray", extent=ext, alpha=0.9)
        hm = np.where(res["dom"][r0:r1, c0:c1] & (res["hmax"][r0:r1, c0:c1] >= 0.1), res["hmax"][r0:r1, c0:c1], np.nan)
        im = ax.imshow(hm, cmap=cmap, norm=norm, extent=ext, alpha=0.85)
        bx = (ext[0], ext[2], ext[1], ext[3])
        for g, _ in edif:
            if bx[0] < g.centroid.x < bx[2] and bx[1] < g.centroid.y < bx[3] and g.geom_type == "Polygon":
                ax.plot(*g.exterior.xy, color="#444", lw=0.3)
        if nm in ("ciudad", "campus"):
            mm = res["mmax"][r0:r1, c0:c1]
            ax.contour(np.linspace(ext[0], ext[1], mm.shape[1]), np.linspace(ext[3], ext[2], mm.shape[0]), mm, levels=[0.02],
                       colors="#9467bd", linewidths=1.2)
            ax.plot([], [], color="#9467bd", label="agua de la quebrada del campus ≥ 2 cm (trazador)")
            ax.legend(loc="lower left", fontsize=8)
            ax.plot(*res["campus"].exterior.xy, color="#e6550d", lw=2)
            ax.annotate("Campus USFQ / GSC", res["campus"].centroid.coords[0], xytext=(-150, 40), textcoords="offset points", color="#e6550d", fontsize=9,
                        arrowprops=dict(arrowstyle="-", color="#e6550d"))
        for k, (r, c) in res["pts"].items():
            x, y = tr * (c + .5, r + .5)
            if bx[0] < x < bx[2] and bx[1] < y < bx[3]:
                ax.plot(x, y, "o", ms=3, color="#d62728")
        cb = fig.colorbar(im, ax=ax, shrink=0.6, ticks=[0.3, 0.75, 1.5, 3]); cb.ax.set_yticklabels(["0,1–0,5", "0,5–1", "1–2", "> 2"]); cb.set_label("Calado máximo (m)")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{R['escenarios'][clave]['descripcion']} — calado máximo (DSM 30 m, preliminar)", fontsize=10)
        fig.savefig(FIG / f"f_modelo2d_{clave}_{nm}.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    # animación GIF (ciudad)
    from PIL import Image
    r0, r1, c0, c1 = ventana(VENTANA_CIUDAD)
    sub = dem[r0:r1, c0:c1]
    hs = ls.hillshade(np.nan_to_num(sub, nan=0), vert_exag=2, dx=tr.a, dy=tr.a)
    base_rgb = (np.stack([hs] * 3, -1) * 200 + 30).astype(np.uint8)
    base_rgb[np.isnan(sub)] = (200, 220, 235)
    cols = np.array([[198, 219, 239], [107, 174, 214], [33, 113, 181], [8, 48, 107]], np.uint8)
    camp = rasterize([(res["campus"].exterior.buffer(tr.a * 0.3), 1)], out_shape=res["dom"].shape, transform=tr)[r0:r1, c0:c1].astype(bool)
    frames = []
    for cq, tt in zip(res["cuadros"], res["t_cuadros"]):
        hh = cq[r0:r1, c0:c1].astype(float)
        img = base_rgb.copy()
        k = np.digitize(hh, [0.1, 0.5, 1, 2]) - 1
        msk = (hh >= 0.1) & res["dom"][r0:r1, c0:c1]
        img[msk] = (0.25 * img[msk] + 0.75 * cols[k[msk]]).astype(np.uint8)
        img[camp] = (230, 85, 13)
        esc_px = 3 if tr.a >= 30 else 2
        im = Image.fromarray(img).resize((img.shape[1] * esc_px, img.shape[0] * esc_px), Image.NEAREST)
        from PIL import ImageDraw
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 330, 22], fill=(255, 255, 255))
        d.text((5, 5), f"{hora_txt(res['t0'], tt)}  calado >= 0,1 m  (preliminar)", fill=(0, 0, 0))
        frames.append(im)
    # recortar a las horas con agua
    activos = [i for i, cq in enumerate(res["cuadros"]) if float(cq[r0:r1, c0:c1].max()) >= 0.1]
    if activos:
        i0, i1 = max(activos[0] - 2, 0), min(activos[-1] + 3, len(frames))
        frames = frames[i0:i1]
    frames[0].save(FIG / f"anim_modelo2d_{clave}.gif", save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)
    print("   figuras:", FIG / f"f_modelo2d_{clave}_ciudad.png", FIG / f"anim_modelo2d_{clave}.gif")


# ---------------------------------------------------------------- principal
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    sel = sys.argv[1:] or list(ESCENARIOS)
    base = preparar_base()
    print("Dominio base:", base["bounds"], "área aportante", round(base["area_aportante_km2"], 2), "km²")
    fr = OUT / "resumen_modelo2d.json"
    R = json.loads(fr.read_text()) if fr.exists() else {}
    R.update({"metodo": {"esquema": "inercial local (Bates et al., 2010), numpy + numba", "cfl_alfa": ALFA_CFL, "dt_max_s": DT_MAX, "h_min_m": H_MIN,
                         "froude_max": FR_MAX, "manning": N_CLASE, "cn_amc_ii": CN_CLASE, "infiltracion": "SCS-CN distribuida por celda (Ia = 0,2 S)",
                         "terreno": "DSM Copernicus GLO-30 sin quemar (UTM 16S, bilineal)", "contornos": "mar y bordes del dominio absorbentes",
                         "trazador": "lluvia neta de la cuenca de la quebrada del campus aguas arriba del rellano (0,28 km²)",
                         "sin_representar": "red pluvial, alcantarillas, puentes, muros, cauces menores de 30 m, sedimentos"},
              "dominio": {"bounds_utm": base["bounds"], "area_aportante_km2": round(base["area_aportante_km2"], 2)}})
    R.setdefault("escenarios", {})
    for clave in sel:
        esc = ESCENARIOS[clave]
        print("Escenario", clave, "—", esc["nombre"])
        res = simular(clave, esc, base)
        exportar(clave, esc, res, R, base["zonas"])
        if clave in ("scs100", "guayabillos", "guayabillos_15m"):
            figuras(clave, res, R)
        fr.write_text(json.dumps(R, ensure_ascii=False, indent=1))
    print("Listo:", OUT)
