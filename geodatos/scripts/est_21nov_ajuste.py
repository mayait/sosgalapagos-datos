"""Ajuste de la susceptibilidad a inundación de Puerto Ayora con lo observado el 21-nov-2026 (DTM 1 m de la SGIAR).

Modelo propio, topográfico (no hidráulico), calibrado con reportes de vecinos SIN VERIFICAR. No es una delimitación oficial.

Entradas
  reportes/eventos/2026-11-21/puntos_control.json   profundidad estimada a ojo en fotos y videos (tabla de equivalencias)
  reportes/eventos/2026-11-21/reportes.geojson      ubicación y precisión de cada reporte
  reportes/eventos/2026-11-21/flujo_observado.geojson   trazo del coordinador (Seymour → Fragata → Pelican Bay)
  datos/dtm_sgiar/dtm_sgiar_1m.vrt (promediado a 2 m) y descargas/dem_recortes/santa_cruz_dtm_mar_5m.tif (mar)
  export/galapagos-completo/susceptibilidad_inundacion.geojson   susceptibilidad HAND publicada (no se modifica)

Método (todo con cotas del DTM de la SGIAR; nunca se mezclan con umbrales del Copernicus)
  1. Cota del espejo en cada punto de control = cota del terreno (mediana a 10 m) + profundidad estimada.
  2. La Cascada: cota del espejo observada = mediana de los puntos del vaso con altura descrita. Se llena el vaso a esa cota
     (celdas conectadas con el punto bajo; fuera del vaso de rebose solo las que quedan por encima del umbral, para no
     «inundar» la ciudad aguas abajo, donde el agua corre en vez de empozarse). Alta = bajo el espejo; media ≤ 1 m sobre él;
     baja ≤ 2,5 m (a ≤ 100 m), por la incertidumbre del espejo.
  3. Corredor observado: HAND respecto a las líneas de flujo observadas (altura de cada celda sobre el punto más cercano de
     la línea, a ≤ 40 m), con las clases del HAND publicado: alta ≤ 1 m, media ≤ 2,5 m, baja ≤ 5 m. Las depresiones
     cerradas del DTM (≥ 50 m²) que toca el agua observada se llenan (alta).
  3b. Trazos de un experto local en El Edén y Matazarnos (estudios/santa-cruz/datos/flujo_experto_eden.geojson), dibujados
     sobre imagen satelital y georreferenciados: se suman a las líneas de flujo del paso 3. No se publican como capa.
  4. Resto de puntos de control (Matazarnos, Arrayanes, cementerio, El Edén, Bellavista…): llenado local en un radio que
     depende de la precisión del reporte: alta ≤ espejo, media ≤ espejo + 1 m, baja ≤ espejo + 2,5 m.
  4b. Observaciones de campo del barrio Tomás de Berlanga (estudios/santa-cruz/datos/observaciones_campo_tomas_de_berlanga.geojson,
     informe comunitario del 13-nov-2026 sobre los desbordes del 30-oct, el 2-nov y 2016): mismo llenado local que el paso 4.
     No son del 21-nov; la ficha de la capa lo dice.
  5. Solo se SUBE de clase: lo que ya era alta, media o baja en el HAND se conserva.
     (Lo que baja son las correcciones por conocimiento local: estudios/santa-cruz/datos/correcciones_locales.geojson,
     que 10_publicar_web.py recorta al publicar. Ver docs/modelo-hand.md.)

Salidas (estudios/santa-cruz/datos/ajuste_21nov/)
  susceptibilidad_ajuste_21nov.geojson   solo lo que se añade a cada clase (acumuladas, como la capa publicada);
                                         10_publicar_web.py lo suma a la susceptibilidad publicada en /mapas/
  vaso_21nov.geojson                     La Cascada llena hasta la cota observada, por profundidad
  puntos_control_21nov.geojson           puntos de control con profundidad observada y modelada
  resumen_ajuste.json                    cotas, errores, hectáreas por clase antes y después, por zona

    .venv/bin/python -I scripts/est_21nov_ajuste.py
"""
import importlib.util
import json
import pathlib
import warnings

import numpy as np
from rasterio.features import rasterize, shapes
from scipy import ndimage
from shapely.geometry import Point, box, mapping, shape
from shapely.ops import transform as stransform, unary_union

warnings.filterwarnings("ignore", category=DeprecationWarning)
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
EV = REPO / "reportes" / "eventos" / "2026-11-21"
OUT = ROOT / "estudios" / "santa-cruz" / "datos" / "ajuste_21nov"
SUSC = ROOT / "export" / "galapagos-completo" / "susceptibilidad_inundacion.geojson"
RESUMEN_DTM = ROOT / "estudios" / "la-cascada" / "datos" / "dtm1m" / "resumen_dtm.json"
FLUJO_EXPERTO = ROOT / "estudios" / "santa-cruz" / "datos" / "flujo_experto_eden.geojson"
CAMPO_BTB = ROOT / "estudios" / "santa-cruz" / "datos" / "observaciones_campo_tomas_de_berlanga.geojson"
_spec = importlib.util.spec_from_file_location("cascada_dtm", ROOT / "scripts" / "37_cascada_dtm.py")
cd = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cd)   # leer(), rellenar(), T, TI (mismo DTM y máscara de mar)

RES = 2                                              # m (en el vaso, 1 m y 2 m dan la misma cota de rebose: resumen_dtm.json)
LONLAT = (-90.3460, -0.7465, -90.2995, -0.6890)      # Puerto Ayora, escarpe y Bellavista (dentro del DTM)
ESPEJO_SIN_NIVEL = ("grave_sin_nivel", "muy_grave_sin_nivel")
NOMBRE = {3: "Alta", 2: "Media", 1: "Baja"}
FUENTE = ("Ajuste con lo observado el 21-nov-2026 (reportes sin verificar) y con el informe de campo del barrio Tomás de "
          "Berlanga (13-nov-2026) sobre el DTM 1 m: SGIAR (Vricon/Maxar). Modelo propio, no es una delimitación oficial.")
DESC = {3: "Ajuste 21-nov: bajo el agua observada o ≤ 1 m sobre el flujo observado",
        2: "Ajuste 21-nov: ≤ 1 m sobre el agua observada o ≤ 2,5 m sobre el flujo observado",
        1: "Ajuste 21-nov: ≤ 2,5 m sobre el agua observada o ≤ 5 m sobre el flujo observado"}


def r6(g):
    return json.loads(json.dumps(mapping(stransform(cd.TI, g))), parse_float=lambda s: round(float(s), 6))


def fc(feats):
    return {"type": "FeatureCollection", "features": feats}


def poligono(m, tr, min_m2=100):
    gs = [shape(s) for s, _ in shapes(m.astype("uint8"), mask=m, transform=tr)]
    g = unary_union(gs).buffer(0)
    partes = [p for p in getattr(g, "geoms", [g]) if p.area >= min_m2]
    return unary_union(partes).simplify(1.0) if partes else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x0, y0 = cd.T(*LONLAT[:2]); x1, y1 = cd.T(*LONLAT[2:])
    z, tr, mar = cd.leer((x0, y0, x1, y1), RES)
    lleno, zz = cd.rellenar(z, mar)
    tierra = ~mar & np.isfinite(z)
    H, W = zz.shape
    X = tr.c + tr.a * (np.arange(W) + .5); Y = tr.f + tr.e * (np.arange(H) + .5)

    def rc(lon, lat):
        x, y = cd.T(lon, lat); c, r = ~tr * (x, y); return int(r), int(c)

    def disco(lon, lat, rad):
        r, c = rc(lon, lat); k = int(np.ceil(rad / RES))
        rr, cc = np.ogrid[-k:k + 1, -k:k + 1]
        m = np.zeros_like(tierra); sl = (slice(max(r - k, 0), r + k + 1), slice(max(c - k, 0), c + k + 1))
        m[sl] = ((rr ** 2 + cc ** 2) * RES ** 2 <= rad ** 2)[: m[sl].shape[0], : m[sl].shape[1]]
        return m & tierra

    # ------------------------------------------------------------ 1. puntos de control
    pc = json.loads((EV / "puntos_control.json").read_text())
    eq, radio = pc["equivalencias_m"], pc["radio_por_precision_m"]
    rep = {f["properties"]["id"]: f for f in json.loads((EV / "reportes.geojson").read_text())["features"]}
    pts = []

    def control(p, lon, lat, lugar, gravedad, precision):
        e = eq[p["lectura"]]
        zs = zz[disco(lon, lat, 10)]
        zr = zz[disco(lon, lat, radio[precision])]
        zt = float(np.median(zs))
        pts.append({**p, "lonlat": [lon, lat], "lugar": lugar, "gravedad": gravedad,
                    "precision": precision, "radio_m": radio[precision],
                    "cota_terreno_m": round(zt, 2), "cota_terreno_p10_p90_m": [round(float(np.percentile(zr, q)), 2) for q in (10, 90)],
                    "prof_obs_m": e["central"], "prof_obs_rango_m": [e["min"], e["max"]], "espejo_m": round(zt + e["central"], 2),
                    "espejo_rango_m": [round(zt + e["min"], 2), round(zt + e["max"], 2)], "con_altura": p["lectura"] not in ESPEJO_SIN_NIVEL})

    for p in pc["puntos"]:
        f = rep[p["reporte"]]; lon, lat = f["geometry"]["coordinates"]
        control(p, lon, lat, f["properties"]["lugar"], f["properties"]["gravedad"], f["properties"]["precision"])
    # Observaciones de campo del barrio Tomás de Berlanga (30-oct, 2-nov y 2016, no del 21-nov): se llenan igual que el paso 4
    for f in json.loads(CAMPO_BTB.read_text())["features"]:
        q = f["properties"]
        if not q.get("lectura"): continue
        lon, lat = f["geometry"]["coordinates"]
        control({"reporte": q["id"], "zona": "fuera", "hora": None, "lectura": q["lectura"],
                 "base": f"Informe de campo del barrio Tomás de Berlanga ({q['fechas']}): {q['lugar']}"},
                lon, lat, q["lugar"], None, q["precision"])

    # ------------------------------------------------------------ 2. La Cascada: vaso a la cota observada
    ref = json.loads(RESUMEN_DTM.read_text())["referencia"]
    r0, c0 = rc(*ref["punto_bajo_lonlat"])
    r0, c0 = np.unravel_index(np.argmin(np.where(disco(*ref["punto_bajo_lonlat"], 20), zz, np.inf)), zz.shape)
    rebose = float(lleno[r0, c0])
    lab, _ = ndimage.label((lleno - zz) > 0.001, structure=np.ones((3, 3)))
    vaso = lab == lab[r0, c0]
    casc = [p for p in pts if p["zona"] == "cascada" and p["con_altura"]]
    esp = np.array([p["espejo_m"] for p in casc])
    h = float(np.median(esp))
    cerca = np.hypot(*np.meshgrid(X - X[c0], Y - Y[r0])) <= 700

    def llenar(nivel):
        lab_h, _ = ndimage.label((zz <= nivel) & tierra & cerca & (vaso | (zz >= rebose)), structure=np.ones((3, 3)))
        return lab_h == lab_h[r0, c0]
    pond = llenar(h)
    salidas = ndimage.binary_dilation(pond, np.ones((3, 3))) & ~pond & ~vaso & tierra & (zz < rebose)
    ls, ns = ndimage.label(salidas, structure=np.ones((3, 3)))
    sal = []
    for k in range(1, ns + 1):
        rr, cc = np.nonzero(ls == k)
        if len(rr) * RES >= 4:
            sal.append({"lonlat": [round(v, 5) for v in cd.TI(*(tr * (cc.mean() + .5, rr.mean() + .5)))], "ancho_aprox_m": int(len(rr) * RES)})
    sal.sort(key=lambda s: -s["ancho_aprox_m"])
    prof_pond = np.where(pond, h - zz, 0)

    def prof_mod(p, nivel, masc):
        m = disco(*p["lonlat"], 10)
        return round(float(np.median(np.where(masc[m], nivel - zz[m], 0).clip(0))), 2)
    for p in pts:
        if p["zona"] != "cascada": continue
        p["prof_mod_rebose_m"] = prof_mod(p, rebose, vaso)
        p["prof_mod_ajuste_m"] = prof_mod(p, h, pond)
        otros = [q["espejo_m"] for q in casc if q is not p]
        p["prof_mod_ajuste_sin_este_m"] = prof_mod(p, float(np.median(otros)), llenar(float(np.median(otros)))) if p["con_altura"] else None

    # ------------------------------------------------------------ 3. corredor observado (HAND sobre las líneas observadas)
    flujo = json.loads((EV / "flujo_observado.geojson").read_text())["features"]
    T = lambda g: stransform(cd.T, g)
    lineas = [T(shape(f["geometry"])) for f in flujo if f["properties"]["tipo"] in ("flujo", "salida")]
    # Trazos del experto local en El Edén (no se publican como capa; solo calibran el corredor)
    lineas += [T(shape(f["geometry"])) for f in json.loads(FLUJO_EXPERTO.read_text())["features"]]
    remolinos = [T(shape(f["geometry"])) for f in flujo if f["properties"]["tipo"] == "remolino"]
    ml = rasterize([(g, 1) for g in lineas] + [(g.exterior, 1) for g in remolinos], out_shape=zz.shape, transform=tr, all_touched=True).astype(bool) & tierra
    zlin = np.where(ml, ndimage.minimum_filter(np.where(tierra, zz, np.inf), size=3), np.nan)
    dist, (ir, ic) = ndimage.distance_transform_edt(~ml, return_indices=True)
    hand_obs = zz - zlin[ir, ic]
    corredor = np.zeros(zz.shape, np.int8)
    d_ok = (dist * RES <= 40) & tierra
    for n, u in ((1, 5.0), (2, 2.5), (3, 1.0)):
        corredor[d_ok & (hand_obs <= u)] = n
    mrem = rasterize([(g, 1) for g in remolinos], out_shape=zz.shape, transform=tr).astype(bool)
    corredor[mrem & tierra & (corredor < 3) & (hand_obs <= 1.0)] = 3
    # depresiones cerradas tocadas por el agua observada
    toca = ml | mrem
    for p in pts:
        if p["zona"] != "cascada": toca |= disco(*p["lonlat"], p["radio_m"])
    ld, _ = ndimage.label(((lleno - zz) > 0.05) & tierra & ~vaso, structure=np.ones((3, 3)))
    ids = np.unique(ld[toca & (ld > 0)])
    area = ndimage.sum(np.ones_like(ld), ld, ids) * RES * RES
    depres = np.isin(ld, ids[area >= 50])

    # ------------------------------------------------------------ 4. llenado local en los demás puntos de control
    capas = {"vaso": np.zeros(zz.shape, np.int8)}
    m100 = ndimage.distance_transform_edt(~pond) * RES <= 100
    capas["vaso"][m100 & tierra & (zz <= h + 2.5)] = 1
    capas["vaso"][m100 & tierra & (zz <= h + 1.0)] = 2
    capas["vaso"][pond] = 3
    capas["corredor"] = corredor
    capas["depresiones"] = np.where(depres, 3, 0).astype(np.int8)
    for p in pts:
        if p["zona"] == "cascada": continue
        m = disco(*p["lonlat"], p["radio_m"]); a = np.zeros(zz.shape, np.int8)
        for n, extra in ((1, 2.5), (2, 1.0), (3, 0.0)):
            a[m & (zz <= p["espejo_m"] + extra)] = n
        capas[p["reporte"]] = a
        p["cota_relleno_dtm_m"] = round(float(np.median(lleno[disco(*p["lonlat"], 10)])), 2)   # depresión cerrada del DTM, si la hay

    ajuste = np.max(np.stack(list(capas.values())), axis=0)

    # ------------------------------------------------------------ 5. comparar con la susceptibilidad publicada y sumar
    win = box(*LONLAT)
    orig = {n: [] for n in (1, 2, 3)}
    for f in json.loads(SUSC.read_text())["features"]:
        if f["properties"].get("isla") != "Santa Cruz" or not f.get("geometry"): continue
        g = shape(f["geometry"])
        if g.intersects(win):
            for n in range(1, int(f["properties"]["nivel"]) + 1): orig[n].append(g)
    orig_u = {n: T(unary_union(v).intersection(win).buffer(0)) for n, v in orig.items()}
    win_u = T(win)
    feats, ha, por_zona = [], {}, {}
    for n in (3, 2, 1):
        adj = poligono(ajuste >= n, tr)
        nuevo = adj.difference(orig_u[n]).buffer(0) if adj else None
        partes = [p for p in getattr(nuevo, "geoms", [nuevo]) if p is not None and not p.is_empty and p.area >= 100] if nuevo else []
        nuevo = unary_union(partes) if partes else None
        if nuevo:
            feats.append({"type": "Feature", "geometry": r6(nuevo), "properties": {
                "isla": "Santa Cruz", "nivel": n, "susceptibilidad": NOMBRE[n], "descripcion": DESC[n], "fuente": FUENTE,
                "metodo": "ajuste_21nov_dtm_sgiar"}})
        antes = orig_u[n].intersection(win_u).area / 1e4
        despues = unary_union([orig_u[n]] + ([nuevo] if nuevo else [])).intersection(win_u).area / 1e4
        ha[NOMBRE[n]] = {"antes_ha": round(antes, 2), "despues_ha": round(despues, 2), "anadido_ha": round(despues - antes, 2)}
        for k, a in capas.items():
            g = poligono(a >= n, tr)
            add = g.difference(orig_u[n]).area / 1e4 if g else 0
            if add >= 0.01: por_zona.setdefault(k, {})[NOMBRE[n]] = round(add, 2)
    (OUT / "susceptibilidad_ajuste_21nov.geojson").write_text(json.dumps(fc(feats), ensure_ascii=False) + "\n")

    # vaso a la cota observada, por profundidad
    vf = []
    for lo, hi, et in ((0, 0.5, "0–0,5 m"), (0.5, 1, "0,5–1 m"), (1, 2, "1–2 m"), (2, 3, "2–3 m"), (3, 99, "> 3 m")):
        g = poligono(pond & (prof_pond > lo) & (prof_pond <= hi), tr, min_m2=20)
        if g: vf.append({"type": "Feature", "geometry": r6(g), "properties": {"clase": et, "prof_min_m": lo, "cota_espejo_m": round(h, 2),
                         "area_ha": round(g.area / 1e4, 2), "fuente": FUENTE}})
    (OUT / "vaso_21nov.geojson").write_text(json.dumps(fc(vf), ensure_ascii=False) + "\n")
    pf = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": p["lonlat"]}, "properties": {
        "reporte": p["reporte"], "lugar": p["lugar"], "hora": p["hora"], "lectura": eq[p["lectura"]]["texto"], "base": p["base"],
        "prof_obs_m": p["prof_obs_m"], "prof_obs_txt": f"{p['prof_obs_rango_m'][0]}–{p['prof_obs_rango_m'][1]} m".replace(".", ","),
        "cota_terreno_m": p["cota_terreno_m"], "espejo_m": p["espejo_m"], "prof_mod_rebose_m": p.get("prof_mod_rebose_m"),
        "prof_mod_ajuste_m": p.get("prof_mod_ajuste_m"), "cota_relleno_dtm_m": p.get("cota_relleno_dtm_m"), "zona": p["zona"]}} for p in pts]
    (OUT / "puntos_control_21nov.geojson").write_text(json.dumps(fc(pf), ensure_ascii=False) + "\n")

    def err(campo):
        e = [p[campo] - p["prof_obs_m"] for p in casc if p.get(campo) is not None]
        return {"n": len(e), "sesgo_m": round(float(np.mean(e)), 2), "error_medio_abs_m": round(float(np.mean(np.abs(e))), 2)}
    perfil = {}
    for f in flujo:
        if f["properties"]["tipo"] not in ("flujo", "salida"): continue
        g = T(shape(f["geometry"])); zs = []
        for d in np.arange(0, g.length, 10):
            q = g.interpolate(d); c, r = ~tr * (q.x, q.y)
            zs.append(float(np.nanmin(zz[int(r) - 2:int(r) + 3, int(c) - 2:int(c) + 3])))
        perfil[f["properties"]["id"]] = {"cota_ini_m": round(zs[0], 1), "cota_fin_m": round(zs[-1], 1),
                                         "subidas_m": round(float(np.clip(np.diff(zs), 0, None).sum()), 1)}
    resumen = {
        "fuente": FUENTE, "relieve": "DTM 1 m: SGIAR (Vricon/Maxar), promediado a 2 m",
        "la_cascada": {
            "cota_punto_bajo_m": round(float(zz[r0, c0]), 2), "cota_rebose_dtm_m": round(rebose, 2),
            "cota_espejo_observada_m": round(h, 2), "espejo_puntos_m": sorted(esp.round(2).tolist()),
            "espejo_rango_intercuartil_m": [round(float(np.percentile(esp, 25)), 2), round(float(np.percentile(esp, 75)), 2)],
            "sobre_rebose_m": round(h - rebose, 2), "prof_max_m": round(float(prof_pond.max()), 2),
            "area_ha": round(pond.sum() * RES * RES / 1e4, 2), "area_vaso_rebose_ha": round(vaso.sum() * RES * RES / 1e4, 2),
            "volumen_m3": int(prof_pond.sum() * RES * RES),
            "salidas_por_debajo_del_espejo": sal[:6],
            "error_rebose": err("prof_mod_rebose_m"), "error_ajuste": err("prof_mod_ajuste_m"),
            "error_ajuste_sin_el_punto": err("prof_mod_ajuste_sin_este_m")},
        "perfil_dtm_flujo_observado": perfil,
        "hectareas_por_clase_ventana": ha, "hectareas_anadidas_por_zona": por_zona,
        "ventana_lonlat": LONLAT, "puntos_control": pts,
        "limitaciones": ["Profundidades estimadas a ojo en fotos y videos; ubicaciones aproximadas (radio según precisión).",
                         "Topografía, no hidráulica: no simula caudales, tiempos ni alcantarillas; el DTM no ve muros ni casas.",
                         "Los reportes y el trazo del flujo no se han verificado en campo."]}
    (OUT / "resumen_ajuste.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in resumen["la_cascada"].items()}, ensure_ascii=False))
    print(json.dumps(perfil), json.dumps(ha, ensure_ascii=False), json.dumps(por_zona, ensure_ascii=False))
    for p in pts: print(p["reporte"], p["zona"], p["cota_terreno_m"], p["prof_obs_m"], p["espejo_m"], p.get("prof_mod_rebose_m"), p.get("prof_mod_ajuste_m"), p.get("prof_mod_ajuste_sin_este_m"), p.get("cota_relleno_dtm_m"))


if __name__ == "__main__":
    main()
