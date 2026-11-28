#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Edificios de la zona afectada del 21-nov redibujados sobre las ortofotos de dron del GAD de Santa Cruz.

Por qué: las huellas de OpenStreetMap y Google Open Buildings que usaba la capa `edificios_foto_21nov` son cajas
aproximadas, con errores locales de 1 a 4 m; faltan edificios y sobran otros. Las ortofotos del GAD (2 a 5 cm,
3 y 5-nov-2026) dejan ver cada techo.

Pasos (cada uno lee lo que dejó el anterior):

  registro  Las ortofotos del GAD vienen de Pix4D sin puntos de control y están corridas de 2 a 6 m. Se calzan contra
            el DSM de 1 m de la SGIAR (Vricon/Maxar) por correlación de bordes en bloques de 100 m y se ajusta una
            transformación afín por ortofoto. Salida: datos/gad_santa_cruz/registro_ortofotos.json (versionado).
  mosaico   Mosaico RGB corregido a 10 cm de la zona afectada (+60 m), con la ortofoto más fina donde hay dos, y la
            altura sobre el terreno (DSM − DTM de la SGIAR) en la misma rejilla. Salida local (descargas/, fuera de git).
  sam       Techos candidatos con SAM 2.1 (segmentación automática + puntos semilla en las huellas viejas y en los
            bultos del DSM), en mosaicos de 80 m con 20 m de solape. Necesita torch y ultralytics, que no están en
            requirements.txt (ver «Uso»). Salida local.
  capa      Elige techos (altura sobre el terreno, sin vegetación, forma compacta, sin solapes), conserva la huella
            vieja donde no hay foto o SAM no ve un techo y calcula los atributos. Reemplaza
            datos/foto_aerea_21nov/edificios_afectados_foto_21nov.geojson y escribe resumen_edificios_ortofotos.json.

Créditos: ortofotos del GAD Municipal de Santa Cruz (CC BY 4.0); DSM y DTM 1 m: SGIAR (Vricon/Maxar); huellas de
respaldo: OpenStreetMap (ODbL) y Google Open Buildings (CC BY 4.0); gravedad: zona de la foto aérea del 21-nov
(Foto: Tui De Roy).

Uso, desde geodatos/:
  .venv/bin/python -I scripts/45_edificios_ortofotos.py registro
  .venv/bin/python -I scripts/45_edificios_ortofotos.py mosaico
  uv run --python 3.12 --with torch --with ultralytics==8.4.220 --with rasterio --with shapely --with scipy \
      --with pyproj python -I scripts/45_edificios_ortofotos.py sam
  .venv/bin/python -I scripts/45_edificios_ortofotos.py capa
"""
import glob
import json
import pathlib
import sys

import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.windows import from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, mapping, shape
from shapely.ops import transform, unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORTOS = ROOT / "descargas/gad_santa_cruz/ortofotos"
SGIAR = ROOT / "descargas/sgiar"                    # el ZIP del pedido 7032308101286995205 (fuera de git)
LOCAL = ROOT / "descargas/gad_santa_cruz/derivados"  # intermedios pesados, fuera de git
FOTO = ROOT / "datos/foto_aerea_21nov"
REGISTRO = ROOT / "datos/gad_santa_cruz/registro_ortofotos.json"
UTM = Transformer.from_crs(4326, 32715, always_xy=True).transform
GEO = Transformer.from_crs(32715, 4326, always_xy=True).transform
R_REG = 0.5        # m por píxel para el registro
BLOQUE_M = 100     # lado de los bloques de correlación
BUSCA_M = 12       # desplazamiento máximo que se busca


def a_utm(g):
    return transform(UTM, g)


# ---------------------------------------------------------------- DSM y DTM de la SGIAR
def sgiar_tifs(tipo):
    """Extrae del ZIP de la SGIAR los GeoTIFF del DSM o del DTM (solo la primera vez)."""
    dst = SGIAR / "dsm"
    tifs = sorted(dst.glob(f"*_{tipo}.tif"))
    if tifs:
        return tifs
    import zipfile
    zips = sorted(SGIAR.glob("*.zip"))
    if not zips:
        raise SystemExit(f"Falta el ZIP de la SGIAR en {SGIAR.relative_to(ROOT)}")
    dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zips[0]) as z:
        for n in z.namelist():
            if f"/vricon_raster_1m/{tipo}/data/" in n and n.endswith(".tif"):
                (dst / pathlib.Path(n).name).write_bytes(z.read(n))
    return sorted(dst.glob(f"*_{tipo}.tif"))


def altura_sobre_terreno(bounds, res):
    """DSM − DTM de la SGIAR (m) en la rejilla `bounds` a `res` m. NaN donde no hay dato."""
    out = []
    for tipo in ("dsm", "dtm"):
        fs = [rasterio.open(p) for p in sgiar_tifs(tipo)]
        a, _ = merge(fs, bounds=bounds, res=res, resampling=Resampling.bilinear, nodata=np.nan)
        for f in fs:
            f.close()
        out.append(a[0].astype(np.float32))
    return out[0] - out[1]


# ---------------------------------------------------------------- registro
def bordes(a):
    a = ndi.gaussian_filter(np.nan_to_num(a.astype(np.float32)), 1.0)
    return np.hypot(ndi.sobel(a, 0), ndi.sobel(a, 1))


def correlacion(ref, mov, m, rmax):
    """Desplazamiento (filas, columnas, subpíxel) que hay que aplicar a `mov` para calzar con `ref`, y su correlación."""
    ref = np.where(m, ref, 0.0); mov = np.where(m, mov, 0.0)
    ref = (ref - ref[m].mean()) * m; mov = (mov - mov[m].mean()) * m
    c = np.fft.fftshift(np.fft.irfft2(np.fft.rfft2(ref) * np.conj(np.fft.rfft2(mov)), s=ref.shape))
    cy, cx = np.array(c.shape) // 2
    w = c[cy - rmax:cy + rmax + 1, cx - rmax:cx + rmax + 1]
    iy, ix = np.unravel_index(np.argmax(w), w.shape)
    if not (0 < iy < w.shape[0] - 1 and 0 < ix < w.shape[1] - 1):
        return None
    def sub(a, b, c_):
        d = a - 2 * b + c_
        return 0.0 if d == 0 else 0.5 * (a - c_) / d
    fy = iy + sub(w[iy - 1, ix], w[iy, ix], w[iy + 1, ix]); fx = ix + sub(w[iy, ix - 1], w[iy, ix], w[iy, ix + 1])
    r = w[iy, ix] / (np.sqrt((ref ** 2).sum() * (mov ** 2).sum()) + 1e-9)
    return fy - rmax, fx - rmax, float(r)


def registrar(p):
    """Ajusta, para una ortofoto, la afín que lleva sus coordenadas a las del DSM de la SGIAR."""
    with rasterio.open(p) as src:
        b = src.bounds
        b = (np.floor(b.left), np.floor(b.bottom), np.ceil(b.right), np.ceil(b.top))
        W, H = int((b[2] - b[0]) / R_REG), int((b[3] - b[1]) / R_REG)
        o = src.read([1, 2, 3, 4], window=from_bounds(*b, src.transform), out_shape=(4, H, W),
                     resampling=Resampling.average, boundless=True, fill_value=0)
    nd = altura_sobre_terreno(b, R_REG)[:H, :W]
    g_o = bordes(o[:3].astype(np.float32).mean(0)); g_n = bordes(np.clip(nd, 0, 10))
    val = (o[3] > 0) & np.isfinite(nd)
    BS, rmax = int(BLOQUE_M / R_REG), int(BUSCA_M / R_REG)
    pts = []
    for i in range(0, H - BS + 1, BS // 2):
        for j in range(0, W - BS + 1, BS // 2):
            m = val[i:i + BS, j:j + BS]
            if m.mean() < 0.7:
                continue
            alto = nd[i:i + BS, j:j + BS][m]
            if (alto > 2.5).mean() < 0.06:          # sin edificios ni árboles: no hay bordes que calzar
                continue
            res = correlacion(g_n[i:i + BS, j:j + BS], g_o[i:i + BS, j:j + BS], m, rmax)
            if res is None or res[2] < 0.12:
                continue
            dy, dx, r = res
            x = b[0] + (j + BS / 2) * R_REG; y = b[3] - (i + BS / 2) * R_REG
            pts.append((x, y, dx * R_REG, -dy * R_REG, r))   # desplazamiento en metros: +x este, +y norte
    if len(pts) < 6:
        return {"bloques": len(pts), "nota": "pocos bloques con edificios o árboles: sin corrección"}
    P = np.array(pts)
    x0, y0 = P[:, 0].mean(), P[:, 1].mean()
    ok = np.ones(len(P), bool)
    for _ in range(5):                               # mínimos cuadrados pesados, quitando los bloques que no calzan
        A = np.c_[np.ones(ok.sum()), P[ok, 0] - x0, P[ok, 1] - y0]; w = P[ok, 4]
        cx = np.linalg.lstsq(A * w[:, None], P[ok, 2] * w, rcond=None)[0]
        cy = np.linalg.lstsq(A * w[:, None], P[ok, 3] * w, rcond=None)[0]
        A_all = np.c_[np.ones(len(P)), P[:, 0] - x0, P[:, 1] - y0]
        res = np.hypot(P[:, 2] - A_all @ cx, P[:, 3] - A_all @ cy)
        nuevo = res < max(1.0, 2.5 * np.median(res[ok]))
        if (nuevo == ok).all():
            break
        ok = nuevo
    # X' = X + cx0 + cx1 (X − x0) + cx2 (Y − y0); igual para Y
    a, bb, c = 1 + cx[1], cx[2], cx[0] - cx[1] * x0 - cx[2] * y0
    d, e, f = cy[1], 1 + cy[2], cy[0] - cy[1] * x0 - cy[2] * y0
    centro = (float(cx[0]), float(cy[0]))
    return {"bloques": int(len(P)), "bloques_usados": int(ok.sum()),
            "desplazamiento_en_el_centro_m": [round(centro[0], 2), round(centro[1], 2)],
            "desplazamiento_min_max_m": [[round(float(v), 2) for v in (P[ok, 2].min(), P[ok, 2].max())],
                                         [round(float(v), 2) for v in (P[ok, 3].min(), P[ok, 3].max())]],
            "residuo_mediano_m": round(float(np.median(res[ok])), 2),
            "afin": [a, bb, c, d, e, f],
            "nota": "X' = a·X + b·Y + c ; Y' = d·X + e·Y + f (UTM 15S). Coordenadas de la ortofoto → las del DSM de la SGIAR."}


def paso_registro():
    sal = {"descripcion": "Corrección de posición de las ortofotos de dron del GAD de Santa Cruz (Pix4D, sin puntos de "
                          "control) contra el DSM de 1 m de la SGIAR (Vricon/Maxar), por correlación de bordes en bloques "
                          f"de {BLOQUE_M} m a {R_REG} m por píxel. La afín se aplica a la georreferencia de cada ortofoto.",
           "referencia": "DSM 1 m: SGIAR (Vricon/Maxar)", "crs": "EPSG:32715", "ortofotos": {}}
    for p in sorted(ORTOS.glob("orto_*.tif")):
        r = registrar(p)
        sal["ortofotos"][p.name] = r
        print(p.name, {k: v for k, v in r.items() if k not in ("afin", "nota")}, flush=True)
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(json.dumps(sal, ensure_ascii=False, indent=1))
    print("→", REGISTRO.relative_to(ROOT))


def transform_corregido(nombre, t):
    """Georreferencia corregida de una ortofoto (`t`: su Affine original)."""
    reg = json.loads(REGISTRO.read_text())["ortofotos"].get(nombre, {})
    if "afin" not in reg:
        return t
    a, b, c, d, e, f = reg["afin"]
    return Affine(a, b, c, d, e, f) * t


# ---------------------------------------------------------------- mosaico
R_MOS = 0.10                                   # m por píxel del mosaico
ORDEN = ["orto_barrio-la-cascada_2026-11-03.tif",   # 2 cm: va primero donde hay dos ortofotos
         "orto_curva-brava_la-cascada_2026-11-05.tif"]
MOSAICO = LOCAL / "mosaico_zona_21nov_10cm.tif"
ALTURA = LOCAL / "altura_sgiar_zona_21nov_50cm.tif"


def zona_21nov():
    return unary_union([a_utm(shape(f["geometry"])) for f in
                        json.loads((FOTO / "zona_inundada_foto_21nov.geojson").read_text())["features"]]).buffer(0)


def limites_mosaico():
    x0, y0, x1, y1 = zona_21nov().buffer(60).bounds
    return (np.floor(x0 / 10) * 10, np.floor(y0 / 10) * 10, np.ceil(x1 / 10) * 10, np.ceil(y1 / 10) * 10)


def paso_mosaico():
    from rasterio.warp import reproject
    B = limites_mosaico()
    W, H = int(round((B[2] - B[0]) / R_MOS)), int(round((B[3] - B[1]) / R_MOS))
    T = Affine(R_MOS, 0, B[0], 0, -R_MOS, B[3])
    out = np.zeros((4, H, W), np.uint8)
    fuente = np.zeros((H, W), np.uint8)
    for k, nombre in enumerate(ORDEN, 1):
        with rasterio.open(ORTOS / nombre) as src:
            tc = transform_corregido(nombre, src.transform)
            # ventana de la ortofoto (en su georreferencia original) que cubre el mosaico, con 15 m de margen
            inv = ~tc
            cs, rs = zip(*[inv * (x, y) for x in (B[0] - 15, B[2] + 15) for y in (B[1] - 15, B[3] + 15)])
            c0, c1 = max(0, int(min(cs))), min(src.width, int(max(cs)) + 1)
            r0, r1 = max(0, int(min(rs))), min(src.height, int(max(rs)) + 1)
            if c1 <= c0 or r1 <= r0:
                continue
            f = max(1, int(R_MOS / src.res[0]))           # se lee ya reducido, desde las vistas generales del COG
            w_, h_ = (c1 - c0) // f, (r1 - r0) // f
            a = src.read([1, 2, 3, 4], window=rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0), out_shape=(4, h_, w_),
                         resampling=Resampling.average)
            ts = tc * Affine.translation(c0, r0) * Affine.scale((c1 - c0) / w_, (r1 - r0) / h_)
        tmp = np.zeros((4, H, W), np.uint8)
        for i in range(4):
            reproject(a[i], tmp[i], src_transform=ts, src_crs="EPSG:32715", dst_transform=T, dst_crs="EPSG:32715",
                      resampling=Resampling.bilinear)
        nuevo = (tmp[3] > 250) & (out[3] == 0)
        out[:, nuevo] = tmp[:, nuevo]; fuente[nuevo] = k
        print(nombre, "aporta", round(nuevo.sum() * R_MOS ** 2 / 1e4, 1), "ha", flush=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    perfil = dict(driver="GTiff", width=W, height=H, crs="EPSG:32715", transform=T, tiled=True, blockxsize=512,
                  blockysize=512, compress="deflate", predictor=2)
    with rasterio.open(MOSAICO, "w", count=5, dtype="uint8", **perfil) as d:
        d.write(out, [1, 2, 3, 4]); d.write(fuente, 5)
        d.descriptions = ("rojo", "verde", "azul", "valido", "ortofoto (1 = La Cascada 3-nov, 2 = Curva Brava 5-nov)")
    B2 = (B[0], B[1], B[2], B[3]); R2 = 0.5
    nd = altura_sobre_terreno(B2, R2)
    perfil.update(width=nd.shape[1], height=nd.shape[0], transform=Affine(R2, 0, B[0], 0, -R2, B[3]), predictor=3)
    with rasterio.open(ALTURA, "w", count=1, dtype="float32", nodata=np.nan, **perfil) as d:
        d.write(nd, 1)
    print("→", MOSAICO.relative_to(ROOT), "y", ALTURA.relative_to(ROOT))


# ---------------------------------------------------------------- SAM
LADO_M, PASO_M = 80, 60                      # mosaicos de 80 m que se solapan 20 m
CANDIDATOS = LOCAL / "techos_candidatos_sam.geojson"


def huellas_mapa():
    """Huellas de OSM y Google Open Buildings de Santa Cruz (UTM), con su fuente."""
    out = []
    for f in json.loads((ROOT / "capas/final/edificios_exposicion.geojson").read_text())["features"]:
        p = f["properties"]
        if p.get("isla") == "Santa Cruz" and f.get("geometry"):
            g = a_utm(shape(f["geometry"])).buffer(0)
            if not g.is_empty:
                out.append((g, p.get("fuente") or "", p.get("osm_id")))
    return out


def semillas_altura(nd, t_nd, caja):
    """Centros de los bultos de más de 2,5 m (edificios o árboles) del DSM dentro de `caja` (UTM)."""
    from rasterio.features import shapes as rshapes
    inv = ~t_nd
    c0, r0 = inv * (caja[0], caja[3]); c1, r1 = inv * (caja[2], caja[1])
    c0, r0, c1, r1 = int(c0), int(r0), int(np.ceil(c1)), int(np.ceil(r1))
    sub = nd[r0:r1, c0:c1]
    m = np.nan_to_num(sub) > 2.5
    m = ndi.binary_opening(m, iterations=1)
    lb, n = ndi.label(m)
    pts = []
    for i, sl in enumerate(ndi.find_objects(lb), 1):
        area = (lb[sl] == i).sum() * t_nd.a ** 2
        if area < 15:
            continue
        cy, cx = ndi.center_of_mass(lb == i)
        pts.append(t_nd * (c0 + cx + 0.5, r0 + cy + 0.5))
    return pts


def paso_sam():
    import torch
    from rasterio.features import shapes as rshapes
    from shapely import STRtree
    from shapely.geometry import Point
    from ultralytics import SAM
    pesos = LOCAL / "sam2.1_l.pt"
    modelo = SAM(str(pesos) if pesos.exists() else "sam2.1_l.pt")
    dev = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    zona = zona_21nov().buffer(25)
    hue = huellas_mapa(); arbol = STRtree([g for g, _, _ in hue])
    with rasterio.open(ALTURA) as s:
        nd = s.read(1); t_nd = s.transform
    feats = []
    with rasterio.open(MOSAICO) as src:
        B = src.bounds
        xs = np.arange(B.left, B.right - LADO_M + PASO_M, PASO_M); ys = np.arange(B.top, B.bottom + LADO_M - PASO_M, -PASO_M)
        cajas = [(x, y - LADO_M, x + LADO_M, y) for y in ys for x in xs if box(x, y - LADO_M, x + LADO_M, y).intersects(zona)]
        print(len(cajas), "mosaicos", flush=True)
        for k, cj in enumerate(cajas):
            win = from_bounds(*cj, src.transform)
            a = src.read([1, 2, 3, 4], window=win, boundless=True, fill_value=0)
            if (a[3] > 0).mean() < 0.15:
                continue
            tt = src.window_transform(win); n = a.shape[1]
            img = np.ascontiguousarray(np.moveaxis(a[:3], 0, -1)[:, :, ::-1])   # BGR, como espera ultralytics
            inv = ~tt
            # semillas: un punto dentro de cada huella del mapa y de cada bulto del DSM
            sem = [g.representative_point().coords[0] for i in arbol.query(box(*cj)) for g in [hue[i][0]]
                   if box(*cj).buffer(-3).contains(g.representative_point())]
            sem += [p for p in semillas_altura(nd, t_nd, cj) if box(*cj).buffer(-3).contains(Point(p))]
            px = [[float(c), float(r)] for c, r in (inv * p for p in sem)]
            corridas = [("auto", dict())]
            if px:
                corridas.append(("semilla", dict(points=px, labels=[1] * len(px))))
            for origen, kw in corridas:
                try:
                    r = modelo(img, device=dev, verbose=False, imgsz=1024, **kw)[0]
                except Exception as e:                          # noqa: BLE001 — un mosaico que falla no detiene el resto
                    print("falla", k, origen, e, flush=True)
                    continue
                if r.masks is None:
                    continue
                mm = r.masks.data.cpu().numpy().astype(np.uint8)
                conf = r.boxes.conf.cpu().numpy() if r.boxes is not None and r.boxes.conf is not None else np.ones(len(mm))
                for m, cf in zip(mm, conf):
                    if m.shape != (n, n):
                        continue
                    ys_, xs_ = np.nonzero(m)
                    if len(xs_) < 400:                          # < 4 m²
                        continue
                    borde = xs_.min() <= 2 or ys_.min() <= 2 or xs_.max() >= n - 3 or ys_.max() >= n - 3
                    gs = [shape(s_) for s_, v in rshapes(m, mask=m.astype(bool), transform=tt) if v == 1]
                    g = max(gs, key=lambda q: q.area).buffer(0)
                    feats.append({"type": "Feature", "properties": {"origen": origen, "mosaico": k, "conf": round(float(cf), 3),
                                                                     "toca_borde": bool(borde)},
                                  "geometry": mapping(g.simplify(0.05))})
            print(k + 1, "/", len(cajas), len(feats), flush=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    CANDIDATOS.write_text(json.dumps({"type": "FeatureCollection", "crs_utm": "EPSG:32715", "features": feats}))
    print("→", CANDIDATOS.relative_to(ROOT), len(feats), "candidatos")


# ---------------------------------------------------------------- capa
# Un candidato de SAM es un techo si:
AREA_MIN, AREA_MAX = 6, 1500        # m²
VEG_MAX = 0.30                      # fracción de píxeles verdes (exceso de verde)
RECT_MIN, SOLIDEZ_MIN = 0.65, 0.85  # área / rectángulo mínimo girado; área / envolvente convexa
ALARGADO_MAX = 7                    # lado largo / lado corto del rectángulo mínimo
ALTO_MIN = 2.0                      # m sobre el terreno (percentil 75 del DSM − DTM), o
ALTO_MIN_CON_HUELLA = 1.0           # si además cae sobre una huella del mapa (casas nuevas o bajas que el DSM suaviza), o
CLARO_MIN, SAT_MAX = 175, 0.15      # si es un techo claro (zinc, fibrocemento) bien formado: brillo medio y saturación
                                    # (en una muestra de 48 candidatos bajos: 17 de 18 aceptados eran techos)
PIEZA_MIN = 20                      # m²: una pieza menor pegada a otro techo es un anexo del mismo edificio
UNION_RECT_MIN = 0.88               # dos aguas del mismo tejado: juntas forman casi un rectángulo
EDIFICIO_MIN = 10                   # m²: lo aislado y más chico (tanques, carros) no cuenta
SOLAPE_MAX = 0.20                   # dos techos aceptados no comparten más del 20 % del menor
CUBIERTA_MIN = 0.30                 # una huella del mapa está «vista» si los techos nuevos cubren el 30 % de ella
GRAVEDAD = {1: "Leve", 2: "Moderada", 3: "Grave", 4: "Muy grave"}
SALIDA = FOTO / "edificios_afectados_foto_21nov.geojson"
RESUMEN = FOTO / "resumen_edificios_ortofotos.json"


def medir(g, mos, t_mos, nd, t_nd):
    """Fracción válida y verde (mosaico) y percentiles de la altura sobre el terreno (DSM) dentro de `g`."""
    from rasterio.features import geometry_mask
    out = {}
    for nombre, arr, t in (("mos", mos, t_mos), ("nd", nd, t_nd)):
        inv = ~t
        x0, y0, x1, y1 = g.bounds
        c0, r0 = inv * (x0, y1); c1, r1 = inv * (x1, y0)
        c0, r0 = max(0, int(c0)), max(0, int(r0)); c1, r1 = int(np.ceil(c1)) + 1, int(np.ceil(r1)) + 1
        sub = arr[..., r0:r1, c0:c1]
        if sub.size == 0:
            return None
        m = ~geometry_mask([g], out_shape=sub.shape[-2:], transform=t * Affine.translation(c0, r0), all_touched=False)
        if m.sum() == 0:
            m = ~geometry_mask([g], out_shape=sub.shape[-2:], transform=t * Affine.translation(c0, r0), all_touched=True)
        if nombre == "mos":
            r_, v_, b_, ok = (sub[i][m].astype(np.float32) for i in range(4))
            out["valido"] = float((ok > 0).mean())
            exg = (2 * v_ - r_ - b_) / (r_ + v_ + b_ + 1)
            out["verde"] = float(((exg > 0.06) & (ok > 0)).mean())
            mx = np.maximum(np.maximum(r_, v_), b_); mn = np.minimum(np.minimum(r_, v_), b_)
            out["brillo"] = float(mx.mean()); out["saturacion"] = float(((mx - mn) / (mx + 1)).mean())
        else:
            h = sub[m]; h = h[np.isfinite(h)]
            out["alto_p75"] = float(np.percentile(h, 75)) if len(h) else float("nan")
            out["alto_med"] = float(np.median(h)) if len(h) else float("nan")
    return out


def forma(g):
    r = g.minimum_rotated_rectangle
    xy = np.asarray(r.exterior.coords)[:4]
    lados = sorted(np.hypot(*(xy[1:] - xy[:-1]).T)) if len(xy) == 4 else [1, 1, 1]
    return {"rect": g.area / max(r.area, 1e-6), "solidez": g.area / max(g.convex_hull.area, 1e-6),
            "alargado": lados[-1] / max(lados[0], 0.1)}


def juntar(piezas):
    """Junta las piezas de techo de un mismo edificio: anexos chicos pegados y las dos aguas de un tejado."""
    from shapely import STRtree
    P = [dict(a) for a in piezas]
    vivo = [True] * len(P)
    cambio = True
    while cambio:
        cambio = False
        idx = [i for i in range(len(P)) if vivo[i]]
        arbol = STRtree([P[i]["g"] for i in idx])
        pares = []
        for k, i in enumerate(idx):
            gi = P[i]["g"]
            for kk in arbol.query(gi.buffer(0.6)):
                j = idx[kk]
                if j <= i:
                    continue
                gj = P[j]["g"]
                comun = gi.buffer(0.4).intersection(gj.buffer(0.4)).area / 0.8      # largo del borde compartido (m)
                if comun < 1.5:
                    continue
                u = unary_union([gi.buffer(0.3, join_style=2), gj.buffer(0.3, join_style=2)]).buffer(-0.3, join_style=2)
                if u.geom_type != "Polygon":
                    continue
                chica = min(gi.area, gj.area)
                if chica < PIEZA_MIN:
                    pares.append((2.0, i, j, u))
                else:
                    fu = forma(u)
                    lado = np.sqrt(chica)
                    if fu["rect"] >= UNION_RECT_MIN and fu["solidez"] >= 0.93 and comun >= 0.8 * lado and u.area <= 600:
                        pares.append((fu["rect"], i, j, u))
        usados = set()
        for _, i, j, u in sorted(pares, key=lambda t: -t[0]):
            if i in usados or j in usados:
                continue
            usados |= {i, j}
            P[i] = {**P[i], "g": u, "area": u.area, "alto_p75": max(P[i]["alto_p75"], P[j]["alto_p75"])}
            vivo[j] = False
            cambio = True
    # lo que al juntar quedó con forma irregular suele ser tierra, escombros o árboles pegados a un techo
    return [P[i] for i in range(len(P)) if vivo[i] and P[i]["g"].area >= EDIFICIO_MIN
            and forma(P[i]["g"])["rect"] >= 0.6 and forma(P[i]["g"])["solidez"] >= 0.8]


def paso_capa():
    from shapely import STRtree
    from shapely.geometry.polygon import orient
    zona_pol = [(a_utm(shape(f["geometry"])).buffer(0), int(f["properties"]["gravedad"])) for f in
                json.loads((FOTO / "zona_inundada_foto_21nov.geojson").read_text())["features"]]
    zona = unary_union([g for g, _ in zona_pol])
    with rasterio.open(MOSAICO) as s:
        mos = s.read([1, 2, 3, 4]); t_mos = s.transform; fuente_orto = s.read(5)
    with rasterio.open(ALTURA) as s:
        nd = s.read(1); t_nd = s.transform
    hue = huellas_mapa(); arbol_h = STRtree([g for g, _, _ in hue])
    cand = []
    for f in json.loads(CANDIDATOS.read_text())["features"]:
        p = f["properties"]
        if p["toca_borde"]:
            continue
        g = shape(f["geometry"]).buffer(0)
        if g.geom_type != "Polygon":
            g = max(getattr(g, "geoms", [g]), key=lambda q: q.area)
        g = g.buffer(0.15, join_style=2).buffer(-0.15, join_style=2)      # quita dientes de un píxel
        if not (AREA_MIN <= g.area <= AREA_MAX) or not zona.buffer(15).intersects(g):
            continue
        fm = forma(g)
        if fm["rect"] < RECT_MIN or fm["solidez"] < SOLIDEZ_MIN or fm["alargado"] > ALARGADO_MAX:
            continue
        me = medir(g, mos, t_mos, nd, t_nd)
        if me is None or me["valido"] < 0.9 or me["verde"] > VEG_MAX:
            continue
        sobre_huella = max([hue[i][0].intersection(g).area / g.area for i in arbol_h.query(g)] or [0])
        alto = me["alto_p75"]
        claro = (me["brillo"] >= CLARO_MIN and me["saturacion"] <= SAT_MAX and fm["rect"] >= 0.8 and fm["solidez"] >= 0.9
                 and me["verde"] <= 0.15 and 15 <= g.area <= 400)
        if not (alto >= ALTO_MIN or (sobre_huella >= 0.5 and alto >= ALTO_MIN_CON_HUELLA) or claro):
            continue
        cand.append({"g": g, "area": g.area, "origen": p["origen"], "conf": p["conf"], **fm, **me, "sobre_huella": sobre_huella})
    print(len(cand), "candidatos que parecen techo", flush=True)
    # sin solapes: primero los grandes y bien formados
    cand.sort(key=lambda c: -c["area"] * c["rect"] * c["solidez"])
    acept, arbol_a = [], None
    for c in cand:
        g = c["g"]
        if any(a["g"].intersection(g).area > SOLAPE_MAX * min(a["area"], c["area"]) for a in acept if a["g"].intersects(g)):
            continue
        acept.append(c)
    print(len(acept), "techos sin solape", flush=True)
    acept = juntar(acept)
    print(len(acept), "edificios después de juntar anexos y aguas", flush=True)
    techos = unary_union([a["g"] for a in acept])
    techos_margen = techos.buffer(0.3)
    # huellas del mapa que la foto no confirma
    sin_orto, no_vistas, guardadas = [], [], []
    for g, fte, oid in hue:
        c = g.centroid
        if not zona.contains(c):
            continue
        if g.intersection(techos).area >= CUBIERTA_MIN * g.area:
            continue
        me = medir(g, mos, t_mos, nd, t_nd)
        if me is None or me["valido"] < 0.5:
            sin_orto.append((g, fte))
        elif me["verde"] < 0.5 and me["alto_p75"] >= ALTO_MIN:
            # algo alto que SAM no recortó: se conserva la huella vieja, sin la parte que ya cubre un techo nuevo
            resto = g.difference(techos_margen)
            resto = max(getattr(resto, "geoms", [resto]), key=lambda q: q.area) if not resto.is_empty else resto
            if not resto.is_empty and resto.area >= 15 and forma(resto)["solidez"] >= 0.8:
                guardadas.append((resto.buffer(0), fte))
            else:
                no_vistas.append((g, fte, me))
        else:
            no_vistas.append((g, fte, me))
    # tamaños y promedios de la muestra (los mismos de la estimación publicada)
    est = json.loads((FOTO / "resumen_estimacion.json").read_text())
    tab = est["por_tamano"]; TH = est["personas_por_hogar"]
    nm = {k: tab[k]["muestra"] for k in "PMG"}; N = sum(nm.values())
    feats_g = [(a["g"], "Ortofoto de dron del GAD de Santa Cruz", a) for a in acept if zona.contains(a["g"].centroid)]
    feats_g += [(g, f"{fte or 'Mapa'} (sin ortofoto)", None) for g, fte in sin_orto]
    feats_g += [(g, f"{fte or 'Mapa'} (la foto no lo recorta)", None) for g, fte in guardadas]
    areas = sorted(g.area for g, _, _ in feats_g)
    U1 = areas[int(len(areas) * nm["P"] / N)]; U2 = areas[int(len(areas) * (nm["P"] + nm["M"]) / N)]
    tam = lambda a: "P" if a < U1 else ("M" if a < U2 else "G")
    # Familias y personas: el total publicado (estimación por muestreo de resumen_estimacion.json) se reparte entre los
    # edificios según el promedio de su tamaño. Hay más edificios que huellas viejas (la ortofoto separa anexos y casas
    # que el mapa juntaba), así que el promedio por tamaño se escala para que la capa siga sumando el mismo total.
    escala = est["viviendas"] / sum(tab[tam(g.area)]["viviendas_por_edificio"] for g, _, _ in feats_g)
    inv_m = ~t_mos
    ef = []
    for g, fte, a in feats_g:
        c = g.centroid
        grav = max([k for z_, k in zona_pol if z_.contains(c)] or [1])
        if a is not None:
            col, fil = inv_m * (c.x, c.y)
            k_orto = int(fuente_orto[int(fil), int(col)]) if 0 <= int(fil) < fuente_orto.shape[0] and 0 <= int(col) < fuente_orto.shape[1] else 0
            fte = {1: "Ortofoto de dron del GAD de Santa Cruz, 3-nov-2026", 2: "Ortofoto de dron del GAD de Santa Cruz, 5-nov-2026"}.get(k_orto, fte)
            alto = a["alto_p75"]
        else:
            me = medir(g, mos, t_mos, nd, t_nd)
            alto = me["alto_p75"] if me else float("nan")
        t_ = tam(g.area)
        alto_ok = np.isfinite(alto) and alto >= 2.2
        ef.append({"type": "Feature", "properties": {
            "gravedad": grav, "gravedad_txt": GRAVEDAD[grav], "tamano": {"P": "pequeño", "M": "mediano", "G": "grande"}[t_],
            "area_m2": round(g.area), "huella": fte,
            "altura_m": round(float(min(alto, 15)), 1) if alto_ok else round(tab[t_]["pisos_medios"] * 3, 1),
            "altura_medida": bool(alto_ok),
            "pisos_est": tab[t_]["pisos_medios"], "viviendas_est": round(tab[t_]["viviendas_por_edificio"] * escala, 2),
            "personas_est": round(tab[t_]["viviendas_por_edificio"] * escala * TH, 1), "fecha": "2026-11-21",
            "fuente": ("Huella: ortofoto de dron del GAD de Santa Cruz corregida con el DSM de la SGIAR; donde no hay foto, "
                       "OpenStreetMap o Google Open Buildings. Altura: DSM − DTM 1 m de la SGIAR (Vricon/Maxar, 2020-2024). "
                       "Pisos, familias y personas: promedio de su tamaño en una muestra sobre la foto aérea (Foto: Tui De Roy).")},
            "geometry": mapping(transform(lambda X, Y: tuple(np.round(GEO(X, Y), 7)), orient(g.simplify(0.2), 1.0)))})
    SALIDA.write_text(json.dumps({"type": "FeatureCollection", "name": "edificios_afectados_foto_21nov",
                                  "nota": ("Edificios dentro de la zona afectada del 21-nov-2026 en Puerto Ayora, redibujados sobre las "
                                           "ortofotos de dron del GAD de Santa Cruz (3 y 5-nov-2026) y calzados con el DSM de la SGIAR. "
                                           "La altura sale del DSM − DTM de la SGIAR (imágenes de 2020 a 2024). Pisos, familias y personas "
                                           "NO están medidos edificio por edificio: son el promedio de su tamaño en una muestra sobre la "
                                           "foto aérea (Foto: Tui De Roy); sirven para sumar. Estimación propia de SOS Galápagos; no es un "
                                           "dato oficial ni un censo de daños."),
                                  "features": ef}, ensure_ascii=False, separators=(",", ":")))
    cuenta = lambda pred: sum(1 for f in ef if pred(f["properties"]))
    res = {"edificios": len(ef),
           "de_la_ortofoto": cuenta(lambda p: p["huella"].startswith("Ortofoto")),
           "huella_vieja_sin_ortofoto": len(sin_orto), "huella_vieja_que_sam_no_recorta": len(guardadas),
           "huellas_viejas_sin_techo_en_la_foto": len(no_vistas),
           "huellas_viejas_en_la_zona": sum(1 for g, _, _ in hue if zona.contains(g.centroid)),
           "umbral_area_m2": {"pequeno_menor_que": round(U1), "grande_desde": round(U2)},
           "por_gravedad": {GRAVEDAD[k]: cuenta(lambda p, k=k: p["gravedad"] == k) for k in GRAVEDAD},
           "altura_medida": cuenta(lambda p: p["altura_medida"]),
           "escala_familias": round(escala, 3),
           "suma_familias": round(sum(f["properties"]["viviendas_est"] for f in ef)),
           "suma_personas": round(sum(f["properties"]["personas_est"] for f in ef)),
           "area_techada_m2": round(sum(f["properties"]["area_m2"] for f in ef)),
           "registro": {k: v.get("desplazamiento_en_el_centro_m") for k, v in json.loads(REGISTRO.read_text())["ortofotos"].items() if k in ORDEN}}
    RESUMEN.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / "huellas_sin_techo_en_la_foto.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"fuente": fte, **{k: round(v, 2) for k, v in me.items()}},
         "geometry": mapping(transform(GEO, g))} for g, fte, me in no_vistas]}, ensure_ascii=False))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    pasos = {"registro": paso_registro, "mosaico": paso_mosaico, "sam": paso_sam, "capa": paso_capa}
    if len(sys.argv) != 2 or sys.argv[1] not in pasos:
        raise SystemExit(__doc__)
    pasos[sys.argv[1]]()
