"""Tomas de agua del acueducto de San Cristóbal: ubicación con fuentes, conducciones y diagnóstico de exposición.

PRELIMINAR. Ninguna ubicación se ha verificado en campo. Cada punto registra sus fuentes y una confianza en la
ubicación (alta / media / baja) con este criterio:
  alta   el objeto está cartografiado como tal (IGM, OSM o capa FCD/CGREG) y otra fuente independiente lo confirma
         a ≤ 350 m;
  media  el punto se infiere de una sola fuente cartográfica (p. ej., el inicio de la tubería IGM) o de una coordenada
         administrativa (registro SNGR) coherente con la toponimia;
  baja   solo hay toponimia o descripción textual.

Fuentes locales (descargas/):
  IGM 1:25 000 WFS (descargas/igm/wfs/): acueducto, manantial, tanque, estanque, nombres_sititos, texto_descriptivo_p
  FCD/CGREG GeoNode: descargas/oficiales/fcd_captacion_agua.geojson
  SNGR eventos históricos: descargas/oficiales/sngr_eventos_historicos.geojson (registro 2023, toma Los Americanos)
  OSM (Overpass, 2-nov-2026): planta de tratamiento El Progreso (way 1548803171) y tanques de Las Palmeras
  (ways 760656469–72); se transcriben aquí sus coordenadas.
Fuentes web (texto): CGREG 2015, estudio de preinversión del recurso hídrico (caudales); USFQ/GSC «Agua para
Galápagos» (Cerro Gato → planta Las Palmeras; La Toma → planta El Progreso); SNGR SITREP 01 y 03 de 2023.

Salidas: estudios/san-cristobal/datos/agua/{tomas.geojson, conducciones.geojson, fuentes_agua.csv, diagnostico.json}
Uso:  .venv/bin/python -I scripts/16c_agua_san_cristobal.py [--solo-tomas]
"""
import csv, json, pathlib, sys
import numpy as np, rasterio
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, transform as stransform
from shapely.strtree import STRtree
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "estudios/san-cristobal/datos/agua"
T = Transformer.from_crs(4326, 32716, always_xy=True).transform
TI = Transformer.from_crs(32716, 4326, always_xy=True).transform
DEM = rasterio.open(ROOT / "descargas/dem_recortes/san_cristobal_dem.tif")
def cota(lon, lat): return round(float(list(DEM.sample([(lon, lat)]))[0][0]))

URL = {
    "CGREG2015": "https://www.gobiernogalapagos.gob.ec/wp-content/uploads/downloads/2015/07/LINK-3.1Proyecto-H%C3%ADdrico-Planificaci%C3%B3n_-VS8.pdf",
    "USFQ": "https://revistas.usfq.edu.ec/index.php/esferas/article/download/2026/2344?inline=1",
    "SITREP01": "https://www.gestionderiesgos.gob.ec/wp-content/uploads/2023/06/SITREP_Nr.-01_Epoca_Lluviosa_01012023_-Galapagos-.-..pdf",
    "SITREP03": "https://www.gestionderiesgos.gob.ec/wp-content/uploads/2023/09/SITREP_Nr.-03_Epoca_Lluviosa_01012023_a_31082023-1.pdf",
    "GC2024": "https://www.galapagos.org/newsroom/remarkable-benefits-of-reviving-a-critical-water-source/",
}

# Cada registro: id, nombre, categoría, lon, lat, tipo, operador, abastece, caudal, confianza, aproximada, fuentes, notas
TOMAS = [
    dict(id="AG-01", nombre="Cerro Gato", categoria="toma", lon=-89.4787, lat=-0.9200,
         tipo="captación de manantial / cañada (tipo exacto no documentado)", operador="GAD Municipal de San Cristóbal",
         abastece="Planta Las Palmeras → Puerto Baquerizo Moreno (USFQ); según el CGREG 2015, fuente de la planta municipal",
         caudal_ls="27 (CGREG 2015)", confianza="media", aproximada=True,
         fuentes="IGM acueducto «Proyecto de agua Cerro Gato» (inicio de la línea, 16,7 km hasta Las Palmeras); IGM tanque de agua a 10 m; IGM topónimo «Cerro Gato» a 0,4–0,7 km; CGREG2015; USFQ; GC2024",
         notas="Punto = inicio de la conducción IGM y tanque IGM. La USFQ da 164 m de cota; el DSM da ≈267 m en este punto: no se ha resuelto la discrepancia."),
    dict(id="AG-02", nombre="Los Americanos (toma / represa)", categoria="toma", lon=-89.48728, lat=-0.91339,
         tipo="represa pequeña sobre cañada alimentada por manantial", operador="GAD Municipal de San Cristóbal",
         abastece="Sistema de agua potable de Puerto Baquerizo Moreno (SITREP 2023: 112 familias afectadas por el corte)",
         caudal_ls="19 (CGREG 2015)", confianza="media", aproximada=True,
         fuentes="SNGR eventos históricos 2023 (coordenada del registro del aluvión, comunidad «El Junco – Finca Las Carmelitas»); SITREP01; SITREP03; CGREG2015",
         notas="Coordenada administrativa de un registro de evento, no un levantamiento. Está a 370 m del topónimo IGM «Cerro Gato», a 1,2 km del punto AG-01 y a ≈170 m de la quebrada IGM más cercana; el D8 no muestra cauce en el punto, por lo que la represa puede estar a decenas o centenas de metros. No hay conducción cartografiada desde aquí."),
    dict(id="AG-03", nombre="La Toma (El Progreso)", categoria="toma", lon=-89.50639, lat=-0.91162,
         tipo="captación con reservorio (IGM «Reservorio»; zanjas perennes IGM)", operador="GAD Municipal de San Cristóbal (por confirmar)",
         abastece="Planta de tratamiento El Progreso (USFQ) → El Progreso y, según la USFQ, también Puerto Baquerizo Moreno",
         caudal_ls="no documentado", confianza="alta", aproximada=False,
         fuentes="FCD/CGREG captación (punto); IGM estanque «Reservorio» a 250 m; IGM topónimo «LA TOMA» a 330 m; IGM acueducto «Proyección Agua Potable Pampas Mías» termina a 150 m; USFQ",
         notas="La USFQ da 150 m de cota; el DSM da ≈500 m. Discrepancia no resuelta."),
    dict(id="AG-04", nombre="El Chino (manantial)", categoria="toma", lon=-89.4571, lat=-0.9019,
         tipo="manantial", operador="no documentado", abastece="Red rural (conducción IGM enterrada hacia el sureste, 3,3 km); destino no documentado",
         caudal_ls="20 (CGREG 2015)", confianza="media", aproximada=False,
         fuentes="IGM manantial (sin nombre); IGM acueducto enterrado «funcionando» que nace en el manantial; topónimo IGM «EL CHINO» a 0,9 km; FCD captación sin nombre a 275 m; CGREG2015 (El Chino 20 l/s)",
         notas="La asignación del nombre «El Chino» es por proximidad."),
    dict(id="AG-05", nombre="El Chino (poza FCD)", categoria="reservorio", lon=-89.46266, lat=-0.89869,
         tipo="poza de almacenamiento superficial", operador="no documentado", abastece="no documentado", caudal_ls="—",
         confianza="alta", aproximada=False, fuentes="FCD/CGREG captación «EL CHINO» (POZA ALMACENAMIENTO SUPERFICIAL)", notas=""),
    dict(id="AG-06", nombre="J Chico", categoria="reservorio", lon=-89.47007, lat=-0.88992,
         tipo="poza de almacenamiento superficial / reservorio", operador="no documentado", abastece="no documentado", caudal_ls="—",
         confianza="alta", aproximada=False, fuentes="FCD/CGREG captación «J CHICO»; IGM estanque «Reservorio» en el mismo punto", notas=""),
    dict(id="AG-07", nombre="La Piscina", categoria="reservorio", lon=-89.49446, lat=-0.90581,
         tipo="poza de almacenamiento superficial", operador="no documentado", abastece="no documentado", caudal_ls="—",
         confianza="alta", aproximada=False, fuentes="FCD/CGREG captación «LA PISCINA»", notas=""),
    dict(id="AG-08", nombre="Vertiente Las Goteras", categoria="manantial", lon=-89.4771, lat=-0.8842,
         tipo="manantial", operador="no documentado", abastece="no documentado", caudal_ls="no documentado (CGREG 2015 la cita sin caudal)",
         confianza="alta", aproximada=False, fuentes="IGM manantial «Vertiente Las Goteras»; CGREG2015", notas="No consta que sea toma del acueducto público."),
    dict(id="AG-09", nombre="Captación FCD sin nombre (oeste de La Toma)", categoria="toma", lon=-89.51953, lat=-0.91846,
         tipo="captación (FCD)", operador="no documentado", abastece="no documentado", caudal_ls="—", confianza="media", aproximada=False,
         fuentes="FCD/CGREG captación (sin nombre)", notas="Podría corresponder a El Plátano/Platanal, La Policía, La Honda o Chuquimarca: no hay fuente que lo confirme."),
    dict(id="AG-10", nombre="Captación FCD sin nombre (noroeste de El Progreso)", categoria="toma", lon=-89.53797, lat=-0.89193,
         tipo="captación (FCD)", operador="no documentado", abastece="no documentado", caudal_ls="—", confianza="media", aproximada=False,
         fuentes="FCD/CGREG captación (sin nombre)", notas="Ídem."),
    dict(id="AG-11", nombre="Captación FCD sin nombre (El Chino sur)", categoria="toma", lon=-89.45469, lat=-0.90246,
         tipo="captación (FCD)", operador="no documentado", abastece="no documentado", caudal_ls="—", confianza="media", aproximada=False,
         fuentes="FCD/CGREG captación (sin nombre), a 275 m del manantial IGM AG-04", notas="Probablemente el mismo sistema que AG-04."),
    # instalaciones aguas abajo (no son tomas)
    dict(id="AG-P1", nombre="Planta de tratamiento El Progreso", categoria="planta", lon=-89.5576, lat=-0.9063,
         tipo="planta potabilizadora", operador="GAD Municipal de San Cristóbal", abastece="El Progreso y Puerto Baquerizo Moreno (USFQ)",
         caudal_ls="—", confianza="alta", aproximada=False, fuentes="IGM tanques «Planta de agua potable»; OSM man_made=water_works (way 1548803171); USFQ", notas=""),
    dict(id="AG-P2", nombre="Planta / tanques Las Palmeras", categoria="planta", lon=-89.5951, lat=-0.9094,
         tipo="planta potabilizadora y tanques", operador="GAD Municipal de San Cristóbal", abastece="Puerto Baquerizo Moreno",
         caudal_ls="—", confianza="alta", aproximada=False, fuentes="IGM tanques de agua (4); OSM man_made=storage_tank (4); fin de la línea IGM «Proyecto de agua Cerro Gato»; topónimo IGM «Las Palmeras» a 250 m; USFQ", notas=""),
    dict(id="AG-T1", nombre="Tanque Cerro Patricia", categoria="tanque", lon=-89.6037, lat=-0.9055,
         tipo="tanque de distribución", operador="GAD Municipal (por confirmar)", abastece="Puerto Baquerizo Moreno (red baja)",
         caudal_ls="—", confianza="media", aproximada=False, fuentes="IGM tanques de agua (2); topónimo IGM «Cerro Patricia»; inicio de una línea IGM de 1,5 km hacia el puerto", notas="Una fuente secundaria cita un «Cerro Patricio» como destino del agua de Cerro Gato."),
    dict(id="AG-T2", nombre="Tanques de Cerro Verde", categoria="tanque", lon=-89.4371, lat=-0.8852,
         tipo="tanques de agua", operador="no documentado", abastece="Cerro Verde (por confirmar)", caudal_ls="—", confianza="alta", aproximada=False,
         fuentes="IGM tanques de agua (2); fin de una línea IGM enterrada de 9,7 km", notas=""),
]

def tomas():
    OUT.mkdir(parents=True, exist_ok=True)
    feats = []
    for t in TOMAS:
        p = dict(t); p["cota_dsm_m"] = cota(t["lon"], t["lat"])
        p["fuentes_url"] = "; ".join(u for k, u in URL.items() if k in t["fuentes"])
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [t["lon"], t["lat"]]}, "properties": {k: v for k, v in p.items() if k not in ("lon", "lat")}})
    (OUT / "tomas.geojson").write_text(json.dumps({"type": "FeatureCollection", "metadata": {
        "titulo": "Tomas y fuentes del acueducto de San Cristóbal (PRELIMINAR, sin verificación de campo)",
        "confianza": __doc__.split("Fuentes locales")[0].split("PRELIMINAR.")[1].strip(),
        "cota": "Cota del DSM Copernicus GLO-30: ±2–4 m; sesgo local frente al IGM ≈ +1,5 m (Puerto Baquerizo) a +1,9 m (El Progreso), sección 4.5; descriptiva"}, "features": feats}, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "fuentes_agua.csv", "w", newline="", encoding="utf-8") as fh:
        cols = ["id", "nombre", "categoria", "lon", "lat", "cota_dsm_m", "tipo", "operador", "abastece", "caudal_ls", "confianza", "aproximada", "fuentes", "fuentes_url", "notas"]
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for f in feats:
            p = f["properties"]; w.writerow({**{k: p.get(k) for k in cols}, "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1]})
    print("tomas.geojson:", len(feats), "puntos")

# ================================================================ conducciones y diagnóstico
def cargar(rel, cond=lambda p: True, isla="San Cristóbal"):
    out = []
    for f in json.loads((ROOT / rel).read_text())["features"]:
        if not f.get("geometry"): continue
        pi = str(f["properties"].get("isla", ""))
        if isla and isla.upper().replace("Ó", "O") not in pi.upper().replace("Ó", "O"): continue
        if cond(f["properties"]): out.append((shape(f["geometry"]), f["properties"]))
    return out

def diagnostico():
    import importlib.util
    spec = importlib.util.spec_from_file_location("c16", ROOT / "scripts/16_cruces_quebradas_vias.py")
    c16 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c16)
    hd = c16.hidro("san_cristobal")
    def area(lon, lat):
        m = c16.muestra(hd, lon, lat); return round(m["A"], 2) if m else None
    def area_100m(lon, lat):   # máximo de la acumulación D8 a ≤ 3 celdas (≈ 95 m): la toma suele estar junto al cauce, no sobre la celda
        c, r = ~hd["tr"] * (lon, lat); r, c = int(r), int(c)
        w = hd["A"][r - 3:r + 4, c - 3:c + 4] * c16.CELL_KM2
        return round(float(w.max()), 2)
    tomas_ = {t["id"]: (Point(T(t["lon"], t["lat"])), t) for t in TOMAS}
    # --- conducciones IGM
    lines = []
    for g, p in cargar("descargas/igm/wfs/acueducto.geojson", isla="CRIST"):
        gu = stransform(T, g)
        a, b = Point(gu.coords[0]), Point(gu.coords[-1])
        def cerca(pt):
            k = min(tomas_, key=lambda k: tomas_[k][0].distance(pt)); d = tomas_[k][0].distance(pt)
            return f"{k} {tomas_[k][1]['nombre']} ({d:.0f} m)" if d < 400 else "—"
        lines.append(dict(g=gu, nombre=p.get("nam") or "(sin nombre)", estado_igm=p.get("exs_desc"), ubicacion_igm=p.get("loc_desc"),
                          largo_m=round(gu.length), extremo_inicial=cerca(a), extremo_final=cerca(b),
                          cota_ini_m=cota(*TI(*gu.coords[0])), cota_fin_m=cota(*TI(*gu.coords[-1])), fuente="IGM 1:25 000, capa acueducto"))
    # --- cruces con cauces y vías
    cauces = [(stransform(T, g), p.get("nombre") or "", p.get("fuente")) for g, p in cargar("capas/final/quebradas.geojson")]
    cauces += [(stransform(T, g), "", "D8 GLO-30") for g, p in cargar("capas/final/drenaje_derivado.geojson") ]
    tq = STRtree([g for g, _, _ in cauces])
    vias = [(stransform(T, g), p) for g, p in cargar("capas/osm/vias.geojson")]
    tv = STRtree([g for g, _ in vias])
    riesgos = [(stransform(T, g), p["tipo"]) for g, p in cargar("capas/final/riesgos_cgreg.geojson")]
    franja = unary_union([stransform(T, g) for g, p in cargar("capas/final/quebradas_franja20m_cgreg.geojson")])
    cruces_out = []
    for L in lines:
        pts = []
        for k in tq.query(L["g"], predicate="intersects"):
            x = L["g"].intersection(cauces[k][0])
            for q in ([x] if x.geom_type == "Point" else [y for y in getattr(x, "geoms", []) if y.geom_type == "Point"]):
                pts.append((q, cauces[k][1], cauces[k][2]))
        # dedup 40 m
        keep = []
        for q, n, f in sorted(pts, key=lambda t: t[2] != "D8 GLO-30"):
            if all(q.distance(o[0]) > 40 for o in keep): keep.append((q, n, f))
        cr = []
        for q, n, f in keep:
            lon, lat = TI(q.x, q.y); A = area(lon, lat)
            cr.append(dict(lon=round(lon, 5), lat=round(lat, 5), area_km2=A, cauce=n or f, cota_dsm_m=cota(lon, lat)))
        cr.sort(key=lambda d: -(d["area_km2"] or 0))
        nv = sum(1 for k in tv.query(L["g"], predicate="intersects"))
        L["cruces_cauce"] = len(cr); L["cruces_cauce_ge_0_5km2"] = sum(1 for d in cr if (d["area_km2"] or 0) >= 0.5)
        L["cruce_mayor_km2"] = cr[0]["area_km2"] if cr else 0
        L["cruces_via_osm"] = nv
        L["en_riesgo_cgreg"] = "; ".join(f"{t}: {round(L['g'].intersection(g).length)} m" for g, t in riesgos if L["g"].intersects(g)) or "ninguno"
        L["en_franja_quebrada_m"] = round(L["g"].intersection(franja).length)
        for d in cr: cruces_out.append(dict(conduccion=L["nombre"], extremo_inicial=L["extremo_inicial"], **d))
    feats = [{"type": "Feature", "geometry": mapping(stransform(TI, L["g"])), "properties": {k: v for k, v in L.items() if k != "g"}} for L in lines]
    # tramos desconocidos (sin geometría)
    for nm, nota in [("Los Americanos (AG-02) → planta o red", "No hay conducción cartografiada en IGM ni OSM desde la represa de Los Americanos."),
                     ("Planta El Progreso (AG-P1) → Puerto Baquerizo Moreno", "La USFQ indica que la planta abastece también al puerto; la conducción no está cartografiada."),
                     ("Cerro Gato (AG-01) → Las Palmeras, conducción en servicio", "La línea IGM de 16,7 km figura «EN CONSTRUCCIÓN»; no se sabe si es la conducción actual ni su estado en 2026.")]:
        feats.append({"type": "Feature", "geometry": None, "properties": {"nombre": nm, "estado_cartografico": "desconocida", "nota": nota}})
    (OUT / "conducciones.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "cruces_conducciones.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["conduccion", "extremo_inicial", "lon", "lat", "area_km2", "cauce", "cota_dsm_m"]); w.writeheader(); [w.writerow(r) for r in cruces_out]
    # --- tomas: área drenada, pendiente, distancia a vía, riesgos CGREG
    Z = DEM.read(1).astype(float)
    diag_t = []
    for k, (pt, t) in tomas_.items():
        lon, lat = t["lon"], t["lat"]
        r, c = DEM.index(lon, lat); w = Z[r - 2:r + 3, c - 2:c + 3]
        gy, gx = np.gradient(w, 30.9); pend = float(np.nanmean(np.hypot(gx, gy)) * 100)
        dv = min(((g.distance(pt), p) for g, p in vias), key=lambda x: x[0])
        rz = [f"{tt} ({g.distance(pt):.0f} m)" for g, tt in riesgos if g.distance(pt) < 500]
        dq = min(g.distance(pt) for g, n, f in cauces if f != "D8 GLO-30") if cauces else None
        diag_t.append(dict(id=k, nombre=t["nombre"], categoria=t["categoria"], area_drenada_d8_km2=area(lon, lat), area_d8_max_100m_km2=area_100m(lon, lat), pendiente_25ha_pct=round(pend),
                           via_mas_cercana_m=round(dv[0]), via_tipo=dv[1].get("highway"), via_nombre=dv[1].get("name") or "",
                           riesgos_cgreg_500m="; ".join(rz) or "ninguno", dist_quebrada_igm_osm_m=round(dq) if dq is not None else None,
                           en_franja_cgreg=bool(franja.contains(pt))))
    json.dump(dict(conducciones=[{k: v for k, v in L.items() if k != "g"} for L in lines], tomas=diag_t, cruces=cruces_out),
              open(OUT / "diagnostico.json", "w"), ensure_ascii=False, indent=1)
    for L in lines: print({k: v for k, v in L.items() if k != "g"})
    for d in diag_t: print(d)

if __name__ == "__main__":
    tomas()
    if "--solo-tomas" not in sys.argv:
        diagnostico()
