#!/usr/bin/env python3
"""La Cascada (Puerto Ayora) a la resolución del DTM de 1 m de la SGIAR: punto bajo, cota de rebose y vaso.

12_cascada_analisis.py estudia la cuenca y el vaso con el relieve de 30 m. Aquí se repite SOLO la parte topográfica del
vaso con el DTM de 1 m (y 2 y 5 m como sensibilidad), en una ventana alrededor del barrio que llega hasta la bahía:
  - punto bajo del barrio;
  - cota de rebose: nivel al que el agua conectada con el punto bajo encuentra salida al mar (relleno de depresiones por
    reconstrucción morfológica; el mar es la única salida, los bordes de tierra de la ventana son pared);
  - umbral (punto de control) que fija esa cota;
  - vaso hasta el rebose: área, volumen, edificios y población estimada;
  - curva cota–área–volumen desde el punto bajo hasta 1 m sobre el rebose (llenado conectado, sin hidráulica).
Es TOPOGRAFÍA, no un modelo hidráulico: no hay caudal, tiempo ni alcantarillas. El DTM es de terreno: bajo los edificios
la cota está interpolada y los muros no existen, así que el agua «pasa» por donde en la realidad puede haber una pared.

Salidas (estudios/la-cascada/datos/dtm1m/): resumen_dtm.json, vaso_rebose_dtm.geojson, umbral_rebose_dtm.geojson,
curva_cota_volumen_dtm.csv; figura estudios/la-cascada/figuras/vaso_dtm_1m.png.
Uso, desde geodatos/:  .venv/bin/python -I scripts/37_cascada_dtm.py
"""
import csv
import json
import pathlib

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes
from rasterio.windows import from_bounds
from scipy import ndimage
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform as stransform, unary_union
from shapely.strtree import STRtree
from skimage.morphology import reconstruction

ROOT = pathlib.Path(__file__).resolve().parents[1]
VRT = ROOT / "datos/dtm_sgiar/dtm_sgiar_1m.vrt"
MAR = ROOT / "descargas/dem_recortes/santa_cruz_dtm_mar_5m.tif"
OUT = ROOT / "estudios/la-cascada/datos/dtm1m"
FIG = ROOT / "estudios/la-cascada/figuras"
R30 = ROOT / "estudios/la-cascada/datos/resumen.json"
VENTANA_N_M, VENTANA_LADO_M, VENTANA_S_M = 1500, 2200, 2600   # desde el centroide del barrio: norte, este/oeste, sur (hasta la bahía)
RADIO_CURVA_M = 600                                             # la curva sobre el rebose se corta a 600 m del centroide (como 12_cascada_analisis.py)
RESOLUCIONES = (1, 2, 5)                                        # m; la de 1 m es la de referencia
REF = 1
T = Transformer.from_crs(4326, 32715, always_xy=True).transform
TI = Transformer.from_crs(32715, 4326, always_xy=True).transform


def feats(rel, cond=lambda p: True):
    return [(stransform(T, shape(f["geometry"]).buffer(0) if f["geometry"]["type"].endswith("Polygon") else shape(f["geometry"])), f["properties"])
            for f in json.loads((ROOT / rel).read_text())["features"]
            if f["properties"].get("isla", "Santa Cruz") == "Santa Cruz" and cond(f["properties"])]


def r6(g):
    return json.loads(json.dumps(mapping(stransform(TI, g))), parse_float=lambda s: round(float(s), 6))


def leer(bounds, res):
    with rasterio.open(VRT) as d:
        win = from_bounds(*bounds, transform=d.transform)
        h, w = int(round(win.height / res)), int(round(win.width / res))
        z = d.read(1, window=win, out_shape=(h, w), resampling=Resampling.average if res > 1 else Resampling.nearest).astype("float64")
        tr = d.window_transform(win) * d.window_transform(win).scale(win.width / w, win.height / h)
        z[z == d.nodata] = np.nan
    with rasterio.open(MAR) as d:      # máscara de mar de 5 m (relieve_sgiar.py), al vecino más cercano
        xs = tr.c + tr.a * (np.arange(w) + .5); ys = tr.f + tr.e * (np.arange(h) + .5)
        X, Y = np.meshgrid(xs, ys)
        c, r = ~d.transform * (X, Y)
        m = d.read(1).astype(bool)
        r = np.clip(np.floor(r).astype(int), 0, m.shape[0] - 1); c = np.clip(np.floor(c).astype(int), 0, m.shape[1] - 1)
        mar = m[r, c] | ~np.isfinite(z)
    return z, tr, mar


def rellenar(z, mar, conectividad=8):
    """Relleno de depresiones con el mar como única salida (reconstrucción por erosión)."""
    alto = np.nanmax(z) + 100
    zz = np.where(mar, 0.0, z)
    semilla = np.full(zz.shape, alto)
    semilla[mar] = 0.0
    fp = np.ones((3, 3)) if conectividad == 8 else ndimage.generate_binary_structure(2, 1)
    return reconstruction(semilla, zz, method="erosion", footprint=fp), zz


def poligono(m, tr):
    return unary_union([shape(s) for s, _ in shapes(m.astype("uint8"), mask=m, transform=tr)])


def analizar(res, bounds, barrio, conectividad=8, detalle=False):
    z, tr, mar = leer(bounds, res)
    lleno, zz = rellenar(z, mar, conectividad)
    mb = rasterize([(barrio, 1)], out_shape=z.shape, transform=tr, all_touched=True).astype(bool) & ~mar
    r0, c0 = np.argwhere(mb)[np.argmin(np.where(mb, zz, np.inf)[mb])]
    z0, zr = float(zz[r0, c0]), float(lleno[r0, c0])
    prof = lleno - zz
    lab, _ = ndimage.label(prof > 0.001, structure=np.ones((3, 3)) if conectividad == 8 else None)
    vaso = lab == lab[r0, c0] if prof[r0, c0] > 0.001 else np.zeros_like(mb)
    a_cel = res * res
    out = {"resolucion_m": res, "conectividad": conectividad, "cota_punto_bajo_m": round(z0, 2), "cota_rebose_m": round(zr, 2),
           "profundidad_max_m": round(zr - z0, 2), "area_vaso_ha": round(vaso.sum() * a_cel / 1e4, 2),
           "volumen_vaso_m3": int(prof[vaso].sum() * a_cel),
           "punto_bajo_lonlat": [round(v, 5) for v in TI(*(tr * (c0 + .5, r0 + .5)))]}
    if not detalle:
        return out
    # umbral: celda fuera del vaso, vecina de él, con cota ≈ rebose y salida a cotas menores (relleno < rebose)
    anillo = ndimage.binary_dilation(vaso, structure=np.ones((3, 3))) & ~vaso & ~mar
    bajo_fuera = ndimage.binary_dilation((lleno < zr - 0.01) & ~vaso, structure=np.ones((3, 3)))
    cand = anillo & (np.abs(zz - zr) < 0.05)
    cand2 = cand & bajo_fuera
    rr, cc = np.argwhere(cand2 if cand2.any() else cand).T
    k = int(np.argmin(np.hypot(rr - r0, cc - c0)))
    umbral = tr * (cc[k] + .5, rr[k] + .5)
    # curva cota–volumen: llenado conectado con el punto bajo
    curva = []
    cx, cy = barrio.centroid.coords[0]
    X = tr.c + tr.a * (np.arange(z.shape[1]) + .5); Y = tr.f + tr.e * (np.arange(z.shape[0]) + .5)
    ventana = np.hypot(*np.meshgrid(X - cx, Y - cy)) <= RADIO_CURVA_M
    borde_v = ventana & ~ndimage.binary_erosion(ventana)
    for h in np.round(np.arange(np.floor(z0 * 10) / 10 + 0.1, zr + 1.001, 0.1), 2):
        lab_h, _ = ndimage.label((zz <= h) & ~mar & ventana, structure=np.ones((3, 3)))
        m = lab_h == lab_h[r0, c0]
        curva.append([float(h), round(m.sum() * a_cel), int(((h - zz) * m).sum() * a_cel), bool(h > zr), bool((m & borde_v).any())])
    return out, {"vaso": poligono(vaso, tr) if vaso.any() else None, "umbral": Point(umbral), "curva": curva, "z": zz, "tr": tr,
                 "mar": mar, "punto_bajo": Point(tr * (c0 + .5, r0 + .5))}


def main():
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    barrio = unary_union([g for g, _ in feats("capas/final/zonas_pobladas.geojson", lambda p: p.get("nombre") == "La Cascada")] +
                         [g for g, _ in feats("capas/final/barrios.geojson", lambda p: p.get("nombre") == "LA CASCADA")])
    cx, cy = barrio.centroid.coords[0]
    bounds = (cx - VENTANA_LADO_M, cy - VENTANA_S_M, cx + VENTANA_LADO_M, cy + VENTANA_N_M)
    ref, det = analizar(REF, bounds, barrio, detalle=True)
    sens = [analizar(r, bounds, barrio, c) for r in RESOLUCIONES for c in (8, 4) if (r, c) != (REF, 8)]
    # exposición del vaso de referencia
    edif = feats("capas/final/edificios_exposicion.geojson"); t_e = STRtree([g for g, _ in edif])
    manz = feats("capas/final/manzanas_inec.geojson"); t_m = STRtree([g for g, _ in manz])
    expo = {}
    if det["vaso"] is not None:
        v = det["vaso"]
        pob = viv = 0.0
        for i in t_m.query(v, predicate="intersects"):
            gm, pm = manz[i]
            fr = gm.intersection(v).area / gm.area if gm.area else 0
            pob += fr * (pm.get("pob_estimada") or 0); viv += fr * (pm.get("viviendas") or 0)
        expo = {"edificios_intersecan": len(t_e.query(v, predicate="intersects")),
                "edificios_centroide": sum(1 for i in t_e.query(v) if v.contains(edif[i][0].centroid)),
                "poblacion_estimada": round(pob), "viviendas_estimadas": round(viv)}
    r30 = json.loads(R30.read_text()) if R30.exists() else {}
    d30 = r30.get("depresion", {})
    resumen = {
        "fuente": "DTM 1 m SGIAR (Vricon/Maxar), datos/dtm_sgiar/. Cite a la SGIAR.",
        "metodo": "Relleno de depresiones por reconstrucción morfológica (scikit-image) con el mar como única salida; vaso = celdas rellenadas "
                  "conectadas con el punto bajo del barrio. Topografía, no hidráulica.",
        "ventana_utm": [round(v) for v in bounds],
        "referencia": {**ref, "umbral_lonlat": [round(v, 5) for v in TI(det["umbral"].x, det["umbral"].y)], "exposicion": expo},
        "sensibilidad": sens,
        "comparacion_30m": {"relieve_30m": r30.get("parametros", {}).get("dem"), "cota_punto_bajo_m": d30.get("cota_punto_bajo_m"),
                            "cota_rebose_m": d30.get("cota_rebose_m"),
                            "volumen_vaso_m3_4_8_vecinos": d30.get("rango_volumen_m3", {}).get("almacenamiento_cerrado_hasta_rebose")},
        "limitaciones": ["El DTM interpola el terreno bajo los edificios: no hay muros ni casas que frenen o desvíen el agua.",
                         "No hay alcantarillas ni sumideros: el vaso solo se vacía por encima del umbral o por infiltración.",
                         "Imágenes de 2020 a 2024: no recoge rellenos ni obras posteriores.",
                         "Cotas sobre EGM2008; frente a los puntos acotados del IGM el DTM queda ≈1 m más bajo en la zona (ver datos/dtm_sgiar/LEEME.md)."]}
    (OUT / "resumen_dtm.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    fc = lambda fs: {"type": "FeatureCollection", "features": fs}
    if det["vaso"] is not None:
        (OUT / "vaso_rebose_dtm.geojson").write_text(json.dumps(fc([{"type": "Feature", "geometry": r6(det["vaso"]), "properties": {
            "nombre": "Vaso de La Cascada hasta la cota de rebose (DTM 1 m)", "cota_rebose_m": ref["cota_rebose_m"],
            "volumen_m3": ref["volumen_vaso_m3"], "area_ha": ref["area_vaso_ha"], **expo,
            "fuente": "Topografía del DTM 1 m de la SGIAR; llenado estático (modelo propio, no oficial)"}}]), ensure_ascii=False))
    (OUT / "umbral_rebose_dtm.geojson").write_text(json.dumps(fc([
        {"type": "Feature", "geometry": r6(det["umbral"]), "properties": {"nombre": "Umbral que fija la cota de rebose (DTM 1 m)", "cota_m": ref["cota_rebose_m"]}},
        {"type": "Feature", "geometry": r6(det["punto_bajo"]), "properties": {"nombre": "Punto bajo del barrio (DTM 1 m)", "cota_m": ref["cota_punto_bajo_m"]}}]),
        ensure_ascii=False))
    with open(OUT / "curva_cota_volumen_dtm.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(["cota_m", "area_m2", "volumen_m3", "sobre_cota_rebose", "toca_borde_ventana"]); w.writerows(det["curva"])
    figura(det, ref, barrio, d30)
    print(json.dumps(resumen["referencia"], ensure_ascii=False))
    for s in sens: print("  ", s)


def figura(det, ref, barrio, d30):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    z, tr = det["z"], det["tr"]
    cx, cy = barrio.centroid.coords[0]
    x0, x1, y0, y1 = cx - 700, cx + 700, cy - 1300, cy + 500
    c0, r1 = ~tr * (x0, y0); c1, r0 = ~tr * (x1, y1)
    r0, r1, c0, c1 = max(int(r0), 0), int(r1), max(int(c0), 0), int(c1)
    zz = z[r0:r1, c0:c1]; mar = det["mar"][r0:r1, c0:c1]
    ext = [tr.c + tr.a * c0, tr.c + tr.a * c1, tr.f + tr.e * r1, tr.f + tr.e * r0]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 6.6), gridspec_kw={"width_ratios": [1.15, 1]})
    hs = LightSource(azdeg=315, altdeg=40).hillshade(np.where(mar, 0, zz), vert_exag=2, dx=tr.a, dy=-tr.e)
    ax.imshow(np.where(mar, np.nan, hs), extent=ext, cmap="gray", vmin=0, vmax=1)
    ax.imshow(np.where(mar, np.nan, zz), extent=ext, cmap="terrain", vmin=0, vmax=60, alpha=0.35)
    ax.imshow(np.where(mar, 1, np.nan), extent=ext, cmap="Blues", vmin=0, vmax=2, alpha=0.6)
    for g in getattr(barrio, "geoms", [barrio]): ax.plot(*g.exterior.xy, color="#d62728", lw=1.6, label="Barrio La Cascada (OSM ∪ CGREG)")
    if det["vaso"] is not None:
        for g in getattr(det["vaso"], "geoms", [det["vaso"]]):
            ax.fill(*g.exterior.xy, color="#2171b5", alpha=0.55, lw=0, label=f"Vaso hasta el rebose ({str(ref['cota_rebose_m']).replace('.', ',')} m)")
    ax.plot(det["umbral"].x, det["umbral"].y, "^", color="#e65100", mec="k", ms=11, label="Umbral que fija el rebose")
    ax.plot(det["punto_bajo"].x, det["punto_bajo"].y, "v", color="#08306b", mec="w", ms=9, label=f"Punto bajo ({str(ref['cota_punto_bajo_m']).replace('.', ',')} m)")
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_xticks([]); ax.set_yticks([])
    h, l = ax.get_legend_handles_labels(); d = dict(zip(l, h)); ax.legend(d.values(), d.keys(), fontsize=7, loc="lower left", framealpha=0.85)
    ax.set_title("La Cascada con el DTM de 1 m: vaso y umbral de rebose", fontsize=10)
    cv = np.array(det["curva"], dtype=float)
    ax2.plot(cv[:, 0], cv[:, 2] / 1e3, color="#1f78b4", lw=2, label="Volumen bajo la cota (miles de m³)")
    ax2.axvspan(ref["cota_rebose_m"], cv[-1, 0], color="#eee", zorder=0)
    ax2.text(cv[-1, 0] - 0.05, ax2.get_ylim()[1] * 0.08, f"sobre el rebose el agua sale hacia la ciudad:\nvolumen indicativo, dentro de {RADIO_CURVA_M} m", fontsize=6.8, color="#666", ha="right")
    ax2.axvline(ref["cota_rebose_m"], color="#1f78b4", ls="--", lw=1)
    ax2.text(ref["cota_rebose_m"] + 0.05, ax2.get_ylim()[1] * 0.85, f"rebose DTM\n{str(ref['cota_rebose_m']).replace('.', ',')} m", fontsize=7.5, color="#1f78b4")
    if d30.get("cota_rebose_m"):
        ax2.axvline(d30["cota_rebose_m"], color="#999", ls=":", lw=1)
        ax2.text(d30["cota_rebose_m"] + 0.05, ax2.get_ylim()[1] * 0.6, f"rebose 30 m\n{str(d30['cota_rebose_m']).replace('.', ',')} m", fontsize=7, color="#777")
    ax2.set_xlabel("Cota de la lámina (m, EGM2008)"); ax2.set_ylabel("Volumen (miles de m³)"); ax2.grid(alpha=0.25)
    ax2.set_title("Curva cota–volumen (llenado conectado con el punto bajo)", fontsize=10)
    ax2.set_xlim(cv[0, 0], cv[-1, 0])
    fig.text(0.01, 0.01, "Fuente del relieve: DTM 1 m SGIAR (Vricon/Maxar). Llenado estático sin hidráulica ni alcantarillas; el DTM no tiene muros ni edificios. "
             "Modelo propio de SOS Galápagos, preliminar.", fontsize=6.8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG / "vaso_dtm_1m.png", dpi=170); plt.close(fig)


if __name__ == "__main__":
    main()
