# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Cuencas, subcuencas y drenaje de Santa Cruz del Instituto de Geografía de la USFQ, y su DEM de 10 m (SIGTIERRAS).

Entrega del 24-nov-2026 (descargas/usfq_geografia/GALAPAGOS-SCRUZ.zip): análisis en SAGA GIS sobre el DEM de 10 m de
SIGTIERRAS, exportado desde ArcGIS Pro. Proyección WGS 84 / UTM 15 S (EPSG:32715).

Hace dos cosas:
  1. Pasa las tres capas a EPSG:4326 con propiedades en español → datos/usfq_geografia/*.geojson (se versionan).
     El drenaje trae la magnitud de Shreve (campo «Order»: un tramo suma los de aguas arriba); aquí se calcula además
     el orden de Strahler con la topología de los tramos.
  2. Deja el DEM listo para 03_dem.py → descargas/usfq_geografia/santa_cruz_sigtierras_10m.tif (sin dato = −9999,
     cotas redondeadas al cm). No va a git hasta confirmar su licencia de redistribución.

Uso: .venv/bin/python -I scripts/38_usfq_cuencas_sigtierras.py
"""
import json, pathlib, zipfile, io, hashlib, datetime
from collections import defaultdict

import numpy as np
import rasterio
import shapefile                       # pyshp
from pyproj import Transformer
from shapely.geometry import shape, mapping, LineString
import shapely

ROOT = pathlib.Path(__file__).resolve().parents[1]
ZIP = ROOT / "descargas/usfq_geografia/GALAPAGOS-SCRUZ.zip"
OUT = ROOT / "datos/usfq_geografia"
DEM_OUT = ROOT / "descargas/usfq_geografia/santa_cruz_sigtierras_10m.tif"
CRS_ORIGEN = "EPSG:32715"              # lo indicó la autora; los .prj dicen lo mismo
FUENTE = "Instituto de Geografía USFQ, María Belén Zapata (SAGA GIS sobre DEM 10 m SIGTIERRAS)"
SIMP_POLI_M = 8.0                      # los bordes vienen en escalera de 10 m
SIMP_LINEA_M = 3.0
JERARQUIA = {1: "Orden 1 (cabecera)", 2: "Orden 2", 3: "Orden 3", 4: "Orden 4 (cauce principal)"}

T = Transformer.from_crs(CRS_ORIGEN, "EPSG:4326", always_xy=True)
def a_4326(g):
    """UTM 15 S → EPSG:4326, con 6 decimales (≈ 0,1 m)."""
    return shapely.transform(g, lambda c: np.round(np.column_stack(T.transform(c[:, 0], c[:, 1])), 6))
def r(v, n=2): return None if v is None else round(float(v), n)


def leer(z, nombre):
    """Lee un shapefile del zip (pyshp desde memoria)."""
    base = f"GALAPAGOS-SCRUZ/{nombre}"
    prj = z.read(base + ".prj").decode()
    if "UTM_Zone_15S" not in prj: raise SystemExit(f"{nombre}: proyección inesperada: {prj[:80]}")
    return shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), shx=io.BytesIO(z.read(base + ".shx")),
                            dbf=io.BytesIO(z.read(base + ".dbf")), encoding="utf-8")


def cuencas(rd, nivel):
    feats = []
    for s, rec in zip(rd.shapes(), rd.records()):
        p = rec.as_dict()
        g = shape(s.__geo_interface__).buffer(0).simplify(SIMP_POLI_M, preserve_topology=True)
        lon, lat = T.transform(p["Outlet_X"], p["Outlet_Y"])
        props = {"nivel": nivel, "id": int(p["ID"]),
                 "cuenca_principal": int(p["Main_Basin"]) if nivel == "subcuenca" else int(p["ID"]),
                 "area_km2": r(p["Area"] / 1e6, 3), "perimetro_km": r(p["Perimeter"] / 1e3),
                 "cota_media_m": r(p["Mean_Eleva"], 1), "desnivel_m": r(p["Elevation"], 1),
                 "longitud_flujo_max_km": r(p["Maximum_Fl"] / 1e3), "longitud_flujo_media_km": r(p["Mean_Flow"] / 1e3),
                 "tiempo_concentracion_h": r(p["Concentrat"]), "forma": p["Basin_Type"],
                 "coef_orografico": r(p["Orographic"]), "coef_masividad": r(p["Massivity"]),
                 "desembocadura": [round(lon, 6), round(lat, 6)], "fuente": FUENTE}
        feats.append({"type": "Feature", "geometry": mapping(a_4326(g)), "properties": props})
    return feats


def drenaje(rd):
    """Tramos con magnitud de Shreve (de SAGA) y orden de Strahler (calculado aquí con la topología)."""
    tramos = [(s.points, int(rec["Order_"])) for s, rec in zip(rd.shapes(), rd.records())]
    k = lambda p: (round(p[0], 1), round(p[1], 1))
    inicio = defaultdict(list)
    for i, (pts, _) in enumerate(tramos): inicio[k(pts[0])].append(i)
    abajo = {i: inicio.get(k(pts[-1]), []) for i, (pts, _) in enumerate(tramos)}
    arriba = defaultdict(list)
    for i, js in abajo.items():
        for j in js: arriba[j].append(i)
    strahler = {}
    def orden(i, pila=()):
        if i in strahler: return strahler[i]
        if i in pila: return 1                       # ciclo (no debería haber)
        ups = [orden(u, pila + (i,)) for u in arriba[i]]
        if not ups: o = 1
        else:
            m = max(ups); o = m + 1 if ups.count(m) >= 2 else m
        strahler[i] = o; return o
    import sys; sys.setrecursionlimit(20000)
    feats, incoherentes = [], 0
    for i, (pts, shreve) in enumerate(tramos):
        ups = [tramos[u][1] for u in arriba[i]]
        if ups and sum(ups) != shreve: incoherentes += 1
        g = LineString(pts)
        largo = g.length
        g = g.simplify(SIMP_LINEA_M)
        feats.append({"type": "Feature", "geometry": mapping(a_4326(g)),
                      "properties": {"jerarquia": JERARQUIA.get(orden(i), f"Orden {orden(i)}"),
                                     "orden_strahler": orden(i), "magnitud_shreve": shreve,
                                     "longitud_m": round(largo), "fuente": FUENTE}})
    return feats, incoherentes


def dem(z):
    with rasterio.MemoryFile(z.read("GALAPAGOS-SCRUZ/santa_cruz.tif")) as mf, mf.open() as d:
        a = d.read(1); prof = d.profile
        if d.crs.to_epsg() != 32715: raise SystemExit(f"DEM: CRS inesperado {d.crs}")
    malo = ~np.isfinite(a) | (a > 1e30)
    a = np.round(a, 2).astype("float32"); a[malo] = -9999
    prof.update(nodata=-9999, compress="deflate", predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256)
    with rasterio.open(DEM_OUT, "w", **prof) as d: d.write(a, 1)
    v = a[~malo]
    return {"archivo": str(DEM_OUT.relative_to(ROOT)), "celdas": [int(a.shape[1]), int(a.shape[0])], "celda_m": 10,
            "area_km2": round(float((~malo).sum()) * 100 / 1e6, 1), "cota_min_m": r(v.min()), "cota_max_m": r(v.max())}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    zb = ZIP.read_bytes()
    with zipfile.ZipFile(ZIP) as z:
        cu = cuencas(leer(z, "BASIN-SCRUZ"), "cuenca")
        sc = cuencas(leer(z, "SUB-BASIN-SCRUZ"), "subcuenca")
        dr, inc = drenaje(leer(z, "STREAM-SCRUZ"))
        info_dem = dem(z)
    for nombre, feats in (("cuencas_santa_cruz", cu), ("subcuencas_santa_cruz", sc), ("drenaje_santa_cruz", dr)):
        (OUT / f"{nombre}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                                                           ensure_ascii=False, separators=(",", ":")))
        print(f"   {nombre}: {len(feats)}")
    ordenes = defaultdict(int)
    for f in dr: ordenes[f["properties"]["orden_strahler"]] += 1
    resumen = {"generado": datetime.date.today().isoformat(), "entrega": "2026-11-24",
               "zip": {"archivo": str(ZIP.relative_to(ROOT)), "sha256": hashlib.sha256(zb).hexdigest()},
               "crs_origen": CRS_ORIGEN, "fuente": FUENTE,
               "cuencas": {"n": len(cu), "area_total_km2": round(sum(f["properties"]["area_km2"] for f in cu), 1),
                           "mayor_km2": max(f["properties"]["area_km2"] for f in cu)},
               "subcuencas": {"n": len(sc), "mediana_km2": float(np.median([f["properties"]["area_km2"] for f in sc]))},
               "drenaje": {"tramos": len(dr), "longitud_km": round(sum(f["properties"]["longitud_m"] for f in dr) / 1e3, 1),
                           "tramos_por_orden_strahler": dict(sorted(ordenes.items())),
                           "confluencias_donde_shreve_no_suma": inc},
               "dem": info_dem}
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
