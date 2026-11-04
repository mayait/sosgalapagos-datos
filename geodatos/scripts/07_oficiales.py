"""Integra capas oficiales (SNGR, INEC, CGREG/FCD, Google Open Buildings) en capas/final/,
quitando datos personales, y calcula la exposición de edificios y población."""
import json, pathlib
from shapely.geometry import shape, mapping
from shapely.strtree import STRtree
ROOT = pathlib.Path(__file__).resolve().parents[1]
O = ROOT / "descargas/oficiales"; F = ROOT / "capas/final"
M = 1/111320
def load(p): return json.loads(pathlib.Path(p).read_text())["features"]
def save(name, feats):
    (F / name).write_text(json.dumps({"type":"FeatureCollection","features":feats}, ensure_ascii=False, separators=(",",":")))
    print(f"{name:40s} {len(feats):6d}  {(F/name).stat().st_size/1e6:.1f} MB")
BB = {"Santa Cruz": (-90.56,-0.80,-90.15,-0.42), "San Cristóbal": (-89.66,-0.97,-89.22,-0.66), "Isabela": (-91.67,-1.10,-90.76,0.18)}
def isla(g):
    p = g.representative_point()
    for k,(w,s,e,n) in BB.items():
        if w<=p.x<=e and s<=p.y<=n: return k
def feat(g, **p): return {"type":"Feature","geometry":mapping(g) if not isinstance(g, dict) else g,"properties":p}
def pick(name, keep, rename=None, fuente="", filt=None, simplify=None):
    out = []
    for f in load(O / f"{name}.geojson"):
        if not f.get("geometry"): continue
        g = shape(f["geometry"]); i = isla(g)
        if not i or (filt and not filt(f["properties"])): continue
        if simplify: g = g.simplify(simplify, preserve_topology=True)
        p = {(rename or {}).get(k, k): f["properties"].get(k) for k in keep if f["properties"].get(k) not in (None, "", " ")}
        out.append(feat(g, isla=i, fuente=fuente, **p))
    return out

# --- Amenazas y riesgos oficiales ---
save("tsunami_inundacion_inocar.geojson", pick("sngr_tsunami_area_inundacion_inocar", ["nam","ari"], {"nam":"localidad","ari":"clase"}, "SNGR / INOCAR"))
save("tsunami_rutas_evacuacion.geojson", pick("sngr_rutas_evacuacion", ["tipo","t_de_ruta","localidad"], {"t_de_ruta":"via"}, "SNGR"))
save("tsunami_zonas_seguras.geojson", pick("sngr_zonas_seguras_puntos_encuentro", ["tipo_seña","nombre_ref","localidad","capacidad","luminaria","comentario","observacio"],
     {"tipo_seña":"tipo","nombre_ref":"nombre"}, "SNGR"))
save("tsunami_sirenas.geojson", pick("sngr_sirenas_sat", ["código","referencia","dpa_parroq"], {"código":"codigo","dpa_parroq":"parroquia"}, "SNGR SAT"))
rg = pick("fcd_riesgos_antropicos", ["tipo_riesg"], {"tipo_riesg":"tipo"}, "CGREG (GeoNode FCD)")
for n, loc in [("fcd_riesgo_inundacion_santa_cruz","Puerto Ayora"),("fcd_riesgo_inundacion_isabela","Puerto Villamil")]:
    for f in pick(n, [], fuente="CGREG (GeoNode FCD)"):
        f["properties"].update(tipo="Riesgo de inundación", localidad=loc); rg.append(f)
save("riesgos_cgreg.geojson", rg)
save("quebradas_franja20m_cgreg.geojson", pick("fcd_encanadas_buffer_20m", ["tipo"], fuente="CGREG (GeoNode FCD)", simplify=1*M))
# La descripción libre del SNGR trae nombres de personas afectadas (con y sin «Sr./Sra.»): no se publica.
ev = pick("sngr_eventos_historicos", ["evento","causa","categoria_","año","mes","canton","parroquias","comunidad_","viviendas_","viviendas1","familias_a","heridas","fallecidas"],
          {"categoria_":"categoria","comunidad_":"sector","viviendas_":"viviendas_afectadas","viviendas1":"viviendas_destruidas","familias_a":"familias_afectadas"}, "SNGR")
ev += pick("sngr_eventos_lluvias", ["evento","causa","fechadelevento","canton","parroquia","sector","viviendasafectadas","familiasafectadas","personasafectadasdirectamente"],
           {"fechadelevento":"fecha","viviendasafectadas":"viviendas_afectadas","familiasafectadas":"familias_afectadas","personasafectadasdirectamente":"personas_afectadas"}, "SNGR (época lluviosa 2025)")
save("eventos_historicos.geojson", ev)

# --- Servicios oficiales (sin nombres ni teléfonos personales) ---
save("salud_msp.geojson", pick("sngr_msp_establecimientos_salud_2023", ["uni_nombre__nombre_oficial_","tipología","institución","nivel_atención","estado","uni_direccion","par_descripcion"],
     {"uni_nombre__nombre_oficial_":"nombre","tipología":"tipologia","institución":"institucion","nivel_atención":"nivel","uni_direccion":"direccion","par_descripcion":"parroquia"}, "MSP vía SNGR (2023)"))
save("albergues_sngr.geojson", pick("sngr_albergues_activos_2025", ["nombre_de","tipo_de_se","total_pers","total_fami","espacio_pa","sector_com","parroquia","altitud_m_","nombre_d_1"],
     {"nombre_de":"nombre","tipo_de_se":"tipo","total_pers":"capacidad_personas","total_fami":"capacidad_familias","espacio_pa":"espacio_m2","sector_com":"sector","altitud_m_":"altitud_m","nombre_d_1":"administra"}, "SNGR refugios activos 2025"))
save("educacion_mineduc.geojson", pick("sngr_mineduc_instituciones_educativas_2021", list(load(O/"sngr_mineduc_instituciones_educativas_2021.geojson")[0]["properties"].keys()), fuente="MINEDUC vía SNGR (2021)"))

# --- Población y zonas pobladas oficiales ---
save("barrios.geojson", pick("fcd_barrios", ["nombre_bar","area_ha"], {"nombre_bar":"nombre"}, "CGREG (GeoNode FCD)"))
save("suelo_urbano_rural_cgreg.geojson", pick("fcd_urbano_rural", ["suelo","parroquia","pob_2015"], fuente="CGREG (GeoNode FCD)"))
save("parroquias.geojson", [f for f in pick("sngr_conali_parroquias_2026", ["dpa_despar","dpa_descan","txt","dpa_parroq"],
     {"dpa_despar":"parroquia","dpa_descan":"canton","dpa_parroq":"codigo"}, "CONALI 2026 vía SNGR", simplify=20*M)])
viv = pick("sngr_viviendas_pob_susceptibilidad", ["pob_x_casa","DPA_DESPAR"], {"DPA_DESPAR":"parroquia"}, "SNGR")
man = pick("inec_mgn2026_manzanas", ["man","anio"], {"man":"codigo"}, "INEC MGN 2026")
mt = STRtree([shape(f["geometry"]) for f in man])
for v in viv:
    for i in mt.query(shape(v["geometry"]), predicate="intersects"):
        p = man[i]["properties"]; p["viviendas"] = p.get("viviendas", 0) + 1
        p["pob_estimada"] = round(p.get("pob_estimada", 0) + float(v["properties"].get("pob_x_casa") or 0), 1); break
save("manzanas_inec.geojson", man)
save("sectores_inec.geojson", pick("inec_mgn2026_sectores", ["sec","parroquia"], {"sec":"codigo"}, "INEC MGN 2026"))

# --- Edificios combinados: OSM + Open Buildings (que no se solapen con OSM) ---
osm = load(F / "edificios_exposicion.geojson")
ot = STRtree([shape(f["geometry"]) for f in osm])
ob = []
for f in load(O / "google_open_buildings_v3_galapagos.geojson"):
    p = f["properties"]
    if float(p.get("confidence", 0)) < 0.70: continue
    g = shape(f["geometry"]); i = isla(g)
    if not i or len(ot.query(g, predicate="intersects")): continue
    ob.append(feat(g.simplify(0.5*M), isla=i, fuente="Google Open Buildings v3", area_m2=round(float(p["area_m2"])), confianza=round(float(p["confidence"]),2)))
for f in osm: f["properties"]["fuente"] = "OSM"
edif = osm + ob
susc = load(F / "susceptibilidad_inundacion_zonas_pobladas.geojson"); st = STRtree([shape(f["geometry"]) for f in susc])
costa = load(F / "costa_baja.geojson"); ct = STRtree([shape(f["geometry"]) for f in costa])
ts = load(F / "tsunami_inundacion_inocar.geojson"); tt = STRtree([shape(f["geometry"]) for f in ts])
fr = load(F / "quebradas_franja20m_cgreg.geojson"); ft_ = STRtree([shape(f["geometry"]) for f in fr])
res = {}
def tag(g, p):
    p["susc_inundacion"] = max([susc[i]["properties"]["nivel"] for i in st.query(g, predicate="intersects")], default=0)
    p["cota_costera_m"] = min([costa[i]["properties"]["max_m"] for i in ct.query(g.representative_point(), predicate="intersects")], default=None)
    p["zona_tsunami"] = bool(len(tt.query(g, predicate="intersects")))
    p["franja_quebrada"] = bool(len(ft_.query(g, predicate="intersects")))
for f in edif:
    g = shape(f["geometry"]); p = f["properties"]; tag(g, p)
    r = res.setdefault(p["isla"], {"edificios":0,"susc_alta":0,"susc_media":0,"susc_baja":0,"franja_quebrada_20m":0,"zona_tsunami":0,"costa_0_3m":0})
    r["edificios"] += 1
    if p["susc_inundacion"]: r[{3:"susc_alta",2:"susc_media",1:"susc_baja"}[p["susc_inundacion"]]] += 1
    r["franja_quebrada_20m"] += p["franja_quebrada"]; r["zona_tsunami"] += p["zona_tsunami"]; r["costa_0_3m"] += p["cota_costera_m"] == 3
save("edificios_exposicion.geojson", edif)
# población expuesta (viviendas SNGR)
for v in viv:
    g = shape(v["geometry"]); p = v["properties"]; tag(g, p); pob = float(p.get("pob_x_casa") or 0)
    r = res[v["properties"]["isla"]]
    for k, cond in [("pob_total", True), ("pob_susc_alta_media", p["susc_inundacion"] >= 2), ("pob_franja_quebrada", p["franja_quebrada"]), ("pob_zona_tsunami", p["zona_tsunami"])]:
        r[k] = round(r.get(k, 0) + (pob if cond else 0))
save("viviendas_sngr.geojson", viv)
(F/"resumen_exposicion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False, indent=1))
