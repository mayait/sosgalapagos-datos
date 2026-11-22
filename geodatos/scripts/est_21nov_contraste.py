# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
"""Contraste de los modelos con lo observado el 21-nov-2026 en Santa Cruz.

Cruza lo observado (áreas inundadas y corredores de areas_afectadas.geojson, reportes de gravedad 3–4 y el flujo observado
del coordinador) con:
  - la susceptibilidad HAND publicada (export/galapagos-completo/susceptibilidad_inundacion.geojson) ANTES del ajuste;
  - la misma susceptibilidad DESPUÉS de sumarle el ajuste del 21-nov (est_21nov_ajuste.py);
  - el modelo 2D del 30-oct (estudios/santa-cruz/datos/modelo2d/b_central/calado_max_clases.geojson).

Escribe estudios/santa-cruz/datos/contraste_21nov.json: fracción de lo observado en susceptibilidad alta / media / baja /
fuera (área, longitud o número de reportes) y en agua del modelo 2D, en total y por zona.

Límite: lo observado son trazos aproximados a partir de reportes sin verificar; el «después» está calibrado con esos
mismos reportes (no es una validación independiente).

    .venv/bin/python -I scripts/est_21nov_contraste.py
"""
import json
import pathlib
import warnings

from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.ops import transform as stransform, unary_union

warnings.filterwarnings("ignore", category=DeprecationWarning)
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
EV = REPO / "reportes" / "eventos" / "2026-11-21"
SUSC = ROOT / "export" / "galapagos-completo" / "susceptibilidad_inundacion.geojson"
AJUSTE = ROOT / "estudios" / "santa-cruz" / "datos" / "ajuste_21nov" / "susceptibilidad_ajuste_21nov.geojson"
M2D = ROOT / "estudios" / "santa-cruz" / "datos" / "modelo2d" / "b_central" / "calado_max_clases.geojson"
AREAS = ROOT / "capas" / "operativas" / "areas_afectadas.geojson"
OUT = ROOT / "estudios" / "santa-cruz" / "datos" / "contraste_21nov.json"
T = Transformer.from_crs(4326, 32715, always_xy=True).transform
U = lambda g: stransform(T, g)
CLASES = ("alta", "media", "baja", "fuera")
ZONAS = {  # zona → ids de lo observado (áreas, flujo, reportes)
    "La Cascada (vaso)": ["a01", "r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r30"],
    "Rebose de La Cascada hacia el sur (Scalesia, escuelas, La Unión)": ["a02", "a03", "r10", "r11", "r12", "r28"],
    "Matazarnos (Seymour y Marchena)": ["a04", "r14"],
    "Los Arrayanes": ["a05", "r15"],
    "El Edén: bajada por Seymour y cruce con Fragata": ["a06", "c01", "f01", "f02", "f03", "r16", "r17", "r18"],
    "Salida al mar: Pelican Bay y cementerio": ["a07", "f04", "r19", "r33"],
    "Parte alta y vía a Bellavista (encañadas)": ["c02", "c03", "c04", "c05", "c06", "c07", "c09", "r21", "r22", "r23", "r24", "r25", "r31", "r32"],
    "Los Guayabillos": ["a08", "r38"],
}


def coberturas(feats, win):
    cov = {n: [] for n in (1, 2, 3)}
    for f in feats:
        if f["properties"].get("isla") not in (None, "Santa Cruz") or not f.get("geometry"): continue
        g = shape(f["geometry"])
        if g.intersects(win):
            for n in range(1, int(f["properties"]["nivel"]) + 1): cov[n].append(g)
    return {n: U(unary_union(v).intersection(win).buffer(0)) for n, v in cov.items()}


def reparto(g, cov):
    """Medida (área, longitud o 1 por punto) de g en cada clase máxima."""
    med = (lambda x: x.area) if g.geom_type.endswith("Polygon") else (lambda x: x.length) if "Line" in g.geom_type else (lambda x: 0 if x.is_empty else 1)
    a3 = g.intersection(cov[3]); a2 = g.intersection(cov[2]).difference(cov[3]); a1 = g.intersection(cov[1]).difference(cov[2])
    tot = med(g) or 1
    out = dict(zip(CLASES[:3], (med(a3), med(a2), med(a1))))
    out["fuera"] = max(tot - sum(out.values()), 0)
    return out, tot


def pct(d, tot):
    return {k: round(100 * v / tot, 1) for k, v in d.items()}


def main():
    areas = {f["properties"]["id"]: f for f in json.loads(AREAS.read_text())["features"] if f["properties"]["tipo"] in ("inundacion", "riesgo")}
    reps = {f["properties"]["id"]: f for f in json.loads((EV / "reportes.geojson").read_text())["features"]
            if (f["properties"].get("gravedad") or 0) >= 3 and f.get("geometry")}
    flujo = {f["properties"]["id"]: f for f in json.loads((EV / "flujo_observado.geojson").read_text())["features"] if f["properties"]["tipo"] != "flecha"}
    obs = {**{k: ("area", v) for k, v in areas.items()}, **{k: ("reporte", v) for k, v in reps.items()}, **{k: ("flujo", v) for k, v in flujo.items()}}
    win = box(*unary_union([shape(v["geometry"]) for _, v in obs.values()]).buffer(0.01).bounds)
    base = json.loads(SUSC.read_text())["features"]
    cov = {"antes": coberturas(base, win), "despues": coberturas(base + json.loads(AJUSTE.read_text())["features"], win)}
    m2d = json.loads(M2D.read_text())["features"]
    agua2d = {"≥ 0,1 m": U(unary_union([shape(f["geometry"]) for f in m2d])),
              "≥ 0,5 m": U(unary_union([shape(f["geometry"]) for f in m2d if f["properties"]["calado_min_m"] >= 0.5]))}
    dominio2d = agua2d["≥ 0,1 m"].convex_hull

    def medir(ids):
        out = {}
        for tipo in ("area", "flujo_linea", "reporte"):
            gs = []
            for i in ids:
                if i not in obs: continue
                t, f = obs[i]; g = U(shape(f["geometry"]))
                if t == "flujo": t = "area" if g.geom_type.endswith("Polygon") else "flujo_linea"
                if t == tipo: gs.append(g)
            if not gs: continue
            r = {}
            for k, c in cov.items():
                acc = dict.fromkeys(CLASES, 0.0); tot = 0
                for g in gs:
                    d, t = reparto(g, c); tot += t
                    for kk in CLASES: acc[kk] += d[kk]
                r[k] = pct(acc, tot)
            for et, a in agua2d.items():
                if tipo == "reporte":
                    r[f"modelo2d_{et}"] = round(100 * sum(a.distance(g) <= 25 for g in gs) / len(gs), 1)
                else:
                    tot = sum((g.area if tipo == "area" else g.length) for g in gs)
                    r[f"modelo2d_{et}"] = round(100 * sum(((g.intersection(a).area) if tipo == "area" else g.intersection(a).length) for g in gs) / tot, 1)
            r["dentro_dominio_2d_pct"] = round(100 * sum(dominio2d.intersects(g) for g in gs) / len(gs), 1)
            r["n"] = len(gs)
            r["magnitud"] = round(sum(g.area for g in gs) / 1e4, 2) if tipo == "area" else round(sum(g.length for g in gs)) if tipo == "flujo_linea" else len(gs)
            r["unidad"] = {"area": "ha", "flujo_linea": "m", "reporte": "reportes (en el punto; 2D: a ≤ 25 m)"}[tipo]
            out[tipo] = r
        return out

    todo_pa = [i for i in obs if not (i.startswith("c0") and i != "c01") and i not in ("a08", "r21", "r22", "r23", "r24", "r25", "r31", "r32", "r38")]
    res = {"nota": "Porcentaje de lo observado en cada clase de susceptibilidad (clase máxima en ese lugar). «antes» = HAND publicado; "
                   "«despues» = HAND + ajuste del 21-nov (calibrado con estos mismos reportes: no es una validación independiente). "
                   "modelo2d = % en agua del modelo 2D del 30-oct (lluvia de otro evento). Lo observado son trazos aproximados de reportes sin verificar.",
           "puerto_ayora": medir(todo_pa), "todo_santa_cruz": medir(list(obs)),
           "por_zona": {z: medir(ids) for z, ids in ZONAS.items()},
           "por_elemento": {}}
    for i in sorted(obs):
        t, f = obs[i]; g = U(shape(f["geometry"]))
        e = {"tipo": t, "nombre": f["properties"].get("nombre") or f["properties"].get("lugar")}
        for k, c in cov.items():
            d, tot = reparto(g, c); e[k] = pct(d, tot) if t != "reporte" else next((kk for kk in CLASES if d[kk]), "fuera")
        e["modelo2d_≥0,1m"] = round(100 * g.intersection(agua2d["≥ 0,1 m"]).area / g.area, 1) if g.geom_type.endswith("Polygon") else \
            round(100 * g.intersection(agua2d["≥ 0,1 m"]).length / g.length, 1) if "Line" in g.geom_type else bool(agua2d["≥ 0,1 m"].distance(g) <= 25)
        res["por_elemento"][i] = e
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    for k in ("puerto_ayora",):
        print(k, json.dumps(res[k], ensure_ascii=False))
    for z, v in res["por_zona"].items():
        print("·", z, {t: (r["antes"], r["despues"], r["modelo2d_≥ 0,1 m"]) for t, r in v.items()})


if __name__ == "__main__":
    main()
