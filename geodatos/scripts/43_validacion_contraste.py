#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Contraste de la susceptibilidad HAND y del modelo 2D de Santa Cruz con lo observado (tabla de contingencia completa).

Lo observado, en tres fuentes independientes del modelo:
  A. Foto aérea del 21-nov-2026, 14:00 (Tui De Roy), rectificada (datos/foto_aerea_21nov/). Dentro de lo fotografiado,
     la zona mojada es «mojado» y el resto, «seco». Se compara en una malla de 5 m.
  B. Reportes ciudadanos del 21-nov (reportes/publicar/2026-11-21/reportes.geojson). Solo son positivos: se da en qué
     clase cae cada uno, por precisión de la ubicación.
  C. Huellas marcadas sobre las ortofotos del GAD del 3 y el 5-nov (42_validacion_muestra.py y
     estudios/santa-cruz/datos/validacion/huellas_marcas.csv). Son huellas del 30-oct y el 2-nov. Las métricas se dan para
     la partición «validacion», sin los «dudoso». Si hay marcas de más de una persona, se da su acuerdo.

Modelos:
  - HAND publicado SIN el ajuste del 21-nov (capas/dem/santa_cruz_susc_inundacion.geojson). Contra el ajuste sería
    circular, porque se calibró con A y B.
  - Modelo 2D del 30-oct, escenario central (estudios/santa-cruz/datos/modelo2d/b_central/calado_max_clases.geojson),
    calado ≥ 0,1 m; solo para C, que es del mismo evento, y dentro del dominio del modelo.

Métricas: POD (detecta lo mojado), FAR (falsas alarmas), CSI, sesgo de área (predicho / observado) y acierto en lo seco.

Salida: estudios/santa-cruz/datos/validacion/contraste.json

Uso, desde geodatos/:
  .venv/bin/python -I scripts/43_validacion_contraste.py
"""
import csv
import json
import pathlib
from collections import Counter

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from shapely import STRtree
from shapely.geometry import shape
from shapely.ops import transform, unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
VAL = ROOT / "estudios/santa-cruz/datos/validacion"
SUSC = ROOT / "capas/dem/santa_cruz_susc_inundacion.geojson"
FOTO = ROOT / "datos/foto_aerea_21nov"
REPORTES = ROOT.parent / "reportes/publicar/2026-11-21/reportes.geojson"
M2D = ROOT / "estudios/santa-cruz/datos/modelo2d/b_central/calado_max_clases.geojson"
UMBRALES = {"alta (HAND ≤ 1 m)": 3, "alta + media (HAND ≤ 2,5 m)": 2, "las tres clases (HAND ≤ 5 m)": 1}
UTM = Transformer.from_crs(4326, 32715, always_xy=True).transform
R = 5


def leer(p, cond=lambda q: True):
    return [(transform(UTM, shape(f["geometry"])), f["properties"]) for f in json.loads(p.read_text())["features"]
            if f.get("geometry") and cond(f["properties"])]


def metricas(a, b, c, d):
    """a acierto, b falsa alarma, c fallo, d seco bien."""
    r = lambda x, y: round(x / y, 3) if y else None
    return {"aciertos": int(a), "falsas_alarmas": int(b), "fallos": int(c), "secos_bien": int(d),
            "POD": r(a, a + c), "FAR": r(b, a + b), "CSI": r(a, a + b + c), "sesgo": r(a + b, a + c), "acierto_seco": r(d, d + b)}


def main():
    susc = leer(SUSC, lambda p: p.get("isla") == "Santa Cruz")
    arbol = STRtree([g for g, _ in susc])
    clase = lambda pt: max([susc[k][1]["nivel"] for k in arbol.query(pt, predicate="intersects")], default=0)
    out = {"nota": "HAND sin el ajuste del 21-nov. Lo observado no se usó para hacer el HAND. Ver el encabezado de 43_validacion_contraste.py.",
           "hand": str(SUSC.relative_to(ROOT))}

    # A. foto del 21-nov: malla de 5 m dentro de lo fotografiado
    with rasterio.open(FOTO / "ortofoto_21nov.tif") as r:
        bd, mk, crs, tr0 = r.bounds, r.dataset_mask(), r.crs, r.transform
    W, H = int((bd.right - bd.left) / R), int((bd.top - bd.bottom) / R)
    tr = from_origin(bd.left, bd.top, R, R)
    vista = np.zeros((H, W), np.uint8)
    reproject(mk, vista, src_transform=tr0, src_crs=crs, dst_transform=tr, dst_crs=crs, resampling=Resampling.min)
    vista = vista > 0
    obs = rasterize([(g, 1) for g, _ in leer(FOTO / "zona_inundada_foto_21nov.geojson")], out_shape=(H, W), transform=tr) > 0
    niv = np.zeros((H, W), np.uint8)
    for n in (1, 2, 3):
        m = rasterize([(g, 1) for g, p in susc if p["nivel"] == n], out_shape=(H, W), transform=tr, fill=0) > 0
        niv[m] = np.maximum(niv[m], n)
    out["A_foto_21nov"] = {"observado": "foto aérea del 21-nov-2026, 14:00 (Tui De Roy), malla de 5 m",
                           "fotografiado_ha": round(vista.sum() * R * R / 1e4, 1), "mojado_ha": round((obs & vista).sum() * R * R / 1e4, 1),
                           "limites": "foto oblicua: no ve lo que tapan techos y árboles; zona suavizada y con áreas marcadas a mano",
                           "por_umbral": {}}
    for nom, u in UMBRALES.items():
        p = niv >= u
        out["A_foto_21nov"]["por_umbral"][nom] = metricas((p & obs & vista).sum(), (p & ~obs & vista).sum(),
                                                          (~p & obs & vista).sum(), (~p & ~obs & vista).sum())

    # B. reportes ciudadanos (solo positivos)
    if REPORTES.exists():
        rep = leer(REPORTES, lambda p: p.get("tipo") in ("inundacion", "desbordamiento", "via_cortada", "personas_atrapadas"))
        precisas = {"exacta", "calle", "cruce"}
        nombres = {3: "alta", 2: "media", 1: "baja", 0: "fuera"}
        todos = Counter(nombres[clase(g.centroid)] for g, _ in rep)
        prec = Counter(nombres[clase(g.centroid)] for g, p in rep if p.get("precision") in precisas)
        out["B_reportes_21nov"] = {"reportes": len(rep), "todos_por_clase": dict(todos),
                                   "precisos": sum(prec.values()), "precisos_por_clase": dict(prec),
                                   "limites": "solo positivos; la mayoría ubicados por barrio o de forma aproximada"}

    # C. huellas sobre las ortofotos del GAD
    muestra = {f["properties"]["id"]: f for f in json.loads((VAL / "huellas_muestra.geojson").read_text())["features"]}
    marcas = list(csv.DictReader(open(VAL / "huellas_marcas.csv", encoding="utf-8")))
    por_quien = {}
    for m in marcas:
        por_quien.setdefault(m["marcado_por"], {})[m["id"]] = m
    principal = next(iter(por_quien))
    m2d = unary_union([g for g, p in leer(M2D) if p.get("calado_min_m", 0) >= 0.1])
    dominio_2d = unary_union([g for g, _ in leer(ROOT / "estudios/la-cascada/datos/cuenca_cascada.geojson")]).buffer(150)
    filas = []
    for i, m in por_quien[principal].items():
        f = muestra[i]; pt = transform(UTM, shape(f["geometry"]))
        filas.append({"id": i, "uso": f["properties"]["uso"], "estado": m["estado"], "confianza": m["confianza"],
                      "nivel": clase(pt), "m2d": m2d.contains(pt), "en_2d": dominio_2d.contains(pt)})
    def tabla(fs, pred):
        a = sum(1 for x in fs if pred(x) and x["estado"] == "mojado"); b = sum(1 for x in fs if pred(x) and x["estado"] == "seco")
        c = sum(1 for x in fs if not pred(x) and x["estado"] == "mojado"); d = sum(1 for x in fs if not pred(x) and x["estado"] == "seco")
        return metricas(a, b, c, d)
    C = {"observado": "huellas del 30-oct y el 2-nov en las ortofotos del GAD del 3 y el 5-nov-2026", "marcado_por": principal,
         "estados": dict(Counter(x["estado"] for x in filas)),
         "estados_por_clase_hand": {str(n): dict(Counter(x["estado"] for x in filas if x["nivel"] == n)) for n in (3, 2, 1, 0)},
         "fraccion_mojado_por_clase_hand": {nombre: (lambda xs: {"vistos": len(xs), "mojado": round(sum(x["estado"] == "mojado" for x in xs) / len(xs), 2) if xs else None})(
             [x for x in filas if x["nivel"] == n and x["estado"] != "dudoso"]) for n, nombre in ((3, "alta"), (2, "media"), (1, "baja"), (0, "fuera"))},
         "ojo_muestra_estratificada": "la muestra tiene el mismo número de puntos por clase HAND, no proporcional al área: POD, FAR, CSI y sesgo "
                                      "por punto no equivalen a los de área. La fracción mojada por clase sí es directa.",
         "limites": "muestra solo cerca de vías y edificios; bajo árboles y techos queda «dudoso»; marcas de una persona hasta que haya revisión"}
    for part in ("validacion", "calibracion", "todas"):
        fs = [x for x in filas if x["estado"] != "dudoso" and (part == "todas" or x["uso"] == part)]
        C[part] = {"puntos": len(fs), "hand": {nom: tabla(fs, lambda x, u=u: x["nivel"] >= u) for nom, u in UMBRALES.items()}}
        f2 = [x for x in fs if x["en_2d"]]
        C[part]["modelo2d_30oct"] = {"puntos": len(f2), **tabla(f2, lambda x: x["m2d"])}
    # acuerdo entre quienes marcaron
    if len(por_quien) > 1:
        otros = [q for q in por_quien if q != principal]
        C["acuerdo"] = {}
        for q in otros:
            com = [i for i in por_quien[q] if i in por_quien[principal]]
            ig = sum(1 for i in com if por_quien[q][i]["estado"] == por_quien[principal][i]["estado"])
            C["acuerdo"][q] = {"puntos": len(com), "iguales": ig, "porcentaje": round(100 * ig / len(com), 1) if com else None}
    out["C_huellas_ortofotos_gad"] = C
    VAL.mkdir(parents=True, exist_ok=True)
    (VAL / "contraste.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
