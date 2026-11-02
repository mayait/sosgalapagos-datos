"""Geolocalización de los lugares y medidas del Plan de Acción SC-4-09-2026 (UGR del GAD San Cristóbal).

Fuente del listado: «Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal» (documento interno facilitado por la
coordinación de USFQ Galápagos el 2-nov-2026; no se reproduce).

Cada lugar se ubica SOLO con fuentes cartográficas o registros existentes; si no hay ninguna, va a no_localizados.csv.
Confianza de la ubicación:
  alta   el objeto está cartografiado con ese nombre (OSM, IGM, MSP/MINEDUC, INEC, FCD) y, si hay otra fuente, concuerda;
  media  una sola fuente con el nombre, o un punto que representa a un barrio/sector extenso, o fuentes que discrepan;
  baja   ubicación inferida del texto del plan + cartografía (p. ej., «punto final de la cañada Galápagos» = desembocadura
         del cauce D8), o topónimo ambiguo.
Coordenadas OSM transcritas de una consulta Overpass del 2-nov-2026 (ids citados) o de capas/osm/.

Salidas: estudios/san-cristobal/datos/ugr/{lugares_plan.geojson, no_localizados.csv, medidas_plan.geojson}
Uso:  .venv/bin/python -I scripts/16d_plan_ugr_sancristobal.py
"""
import csv, json, pathlib
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, linemerge, transform as stransform, substring
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "estudios/san-cristobal/datos/ugr"
PLAN = "Plan de Acción SC-4-09-2026, UGR del GAD San Cristóbal"
MAX, NOR = "máxima", "normal"

# nombre, tipo, isla, prioridad, afectación (resumen del plan), lon, lat, fuente, confianza, nota
L = [
 # --- Puerto Baquerizo Moreno: hitos
 ("Bahía Naufragio", "bahía", "San Cristóbal", NOR, "Desembocadura de las cañadas Galápagos (Barrio Frío) y Escuela Alvear", -89.61355, -0.89877, "OSM natural=bay «Wreck Bay» (n249407971); IGM texto «Bahía Naufragio»", "alta", ""),
 ("Playa y Poza de las Garzas (Barrio Frío)", "playa", "San Cristóbal", MAX, "Desbordamiento y rompimiento de la playa; punto final de la cañada Galápagos; riesgo para embarcaciones varadas", -89.61292, -0.90319, "Inferido: desembocadura al mar del cauce D8 de Barrio Frío (estudios/san-cristobal/datos/urbano/cauces_urbanos.geojson, PBM-02), que el plan identifica como punto final de la cañada Galápagos", "baja", "No hay topónimo «Garzas» en OSM ni en el IGM."),
 ("Playa de Oro", "playa", "San Cristóbal", MAX, "Desembocadura de la cañada Divino Niño tapada con lodo y piedras", -89.60951, -0.89986, "OSM natural=beach «Playa de Oro» (w303563274); OSM vía peatonal «Vía Playa de Oro»", "alta", ""),
 ("Playa Mann", "playa", "San Cristóbal", MAX, "Rejillas y alcantarillado pluvial taponados, vía adoquinada dañada, desbordamiento en la playa", -89.60936, -0.89559, "OSM natural=beach «Playa Mann» (w62331834); IGM texto «Playa Mann»", "alta", ""),
 ("Pasarela del muelle de pescadores", "infraestructura", "San Cristóbal", NOR, "Por aquí desemboca la cañada de la Escuela Alejandro Alvear", -89.60965, -0.89990, "IGM muelle_l (muelle largo, sin nombre) más próximo a la salida del cauce Escuela Alvear", "baja", "El IGM y OSM no nombran un muelle de pescadores; el IGM tiene un «Centro de acopio de pescadores» en -89,6060; -0,8986."),
 ("Hospital Oskar Jandl", "salud", "San Cristóbal", MAX, "Muro de contención fracturado en 240 m; calle de emergencia obstruida; acceso cortado por el agua de la vía perimetral", -89.60523, -0.89986, "OSM amenity=hospital «Hospital Oskar Jandl» (n3077654455) y 3 edificios hospital", "media", "El registro del MSP lo sitúa 1,3 km al suroeste (-89,6153; -0,9051). El plan lo asocia al barrio Divino Niño y al Colegio Ignacio Hernández, lo que favorece la ubicación de OSM."),
 ("Colegio Ignacio Hernández", "educación", "San Cristóbal", MAX, "El agua drena por la vía perimetral e impide el acceso al hospital", -89.60401, -0.90199, "OSM amenity=school (n14151166571); IGM edificio_a «Colegio Técnico Ignacio Hernández»; MINEDUC (-89,6045; -0,9018)", "alta", ""),
 ("Mina de Cerro Quemado", "mina", "San Cristóbal", NOR, "Desembocadura de la cañada Cerro Quemado / Don García", -89.61238, -0.91412, "OSM man_made=mineshaft «Mina Cerro Quemado» (w144837057); IGM texto «Cerro Quemado» a 230 m", "alta", ""),
 ("Cerro Mundo", "cerro (PNG)", "San Cristóbal", NOR, "Paso de la cañada Galápagos", -89.56667, -0.88333, "OSM natural=peak «Cerro Mundo» (n249411912); IGM texto (-89,5749; -0,8871)", "alta", "El INEC tiene además una localidad «Cerro Mundo» en -89,5705; -0,9053."),
 ("Centro de Gestión de Residuos Sólidos (CGRS)", "infraestructura", "San Cristóbal", NOR, "Cañada de 2,2 km con más de 20 ramificaciones", -89.57818, -0.91417, "OSM landuse=landfill «Centro de Gestión de Residuos Sólidos» (w1549052785); IGM edificio_a «Proyecto de gestión de residuos sólidos urbanos»", "alta", ""),
 # --- barrios / sectores
 ("Barrio Frío", "barrio", "San Cristóbal", MAX, "Desbordamiento de la cañada Galápagos en la playa", -89.61372, -0.90379, "Coordenada del registro SNGR «Barrio Frío» (22-feb-2024)", "media", "Punto representativo; no hay polígono de barrio."),
 ("Barrio Manzanillo", "barrio", "San Cristóbal", MAX, "Desborde en abril de 2026 a 100 m del puente; destrucción de viviendas, calles, agua potable, alcantarillado y postes; requiere zanja de 1 040 m", -89.5997, -0.9106, "IGM poblado «Manzanillo»; registro SNGR «El Manzanillo» (2023) a 340 m", "media", "Punto representativo."),
 ("Ciudadela El Gran Maestro (Manzanillo)", "barrio", "San Cristóbal", MAX, "Incluida en el área afectada de Manzanillo", -89.599397, -0.908457, "Coordenada del registro SNGR de abril de 2019 «Barrio Manzanillo y Ciudadela El Maestro»", "baja", "Una sola coordenada para dos sectores."),
 ("Puente de Manzanillo (Vía Perimetral)", "puente", "San Cristóbal", MAX, "Referencia del desborde de abril de 2026 («a 100 m del puente»)", -89.6058, -0.90819, "OSM bridge=yes en la Av. Jaime Roldós / Vía Perimetral (w802657332), sobre el cauce de El Manzanillo (cruce CR-SCR-0011)", "baja", "Se supone que «el puente» del plan es este; no está confirmado."),
 ("Barrio Divino Niño", "barrio", "San Cristóbal", MAX, "Sectores Playa de Oro, Hospital y Colegio Ignacio Hernández afectados", -89.6046, -0.9009, "IGM edificio_p «Iglesia Divino Niño» como referencia del barrio", "media", "Punto representativo."),
 ("Barrio Palmeras", "barrio", "San Cristóbal", MAX, "Sector Los Arrayanes / La Picada: daños en calles y viviendas; la cañada cruza el centro del barrio", -89.5932, -0.9114, "IGM poblado «Las Palmeras»; INEC localidad «Las Palmeras» (-89,5887; -0,9066)", "media", ""),
 ("Barrio Playa Mann", "barrio", "San Cristóbal", MAX, "Rejillas y alcantarillado taponados; vía adoquinada dañada", -89.6085, -0.89667, "Inmediato a la playa (OSM); punto de «Casa Playa Mann» (n10229613402) como referencia", "media", "Punto representativo."),
 ("Sector La Planada", "barrio", "San Cristóbal", MAX, "El sector más afectado en 2025–2026: 5 familias evacuadas en abril de 2025; nuevo desborde en abril de 2026", -89.594043, -0.911313, "Coordenada del registro SNGR «La Planada» (8-abr-2025)", "media", ""),
 ("Los Arroyos", "poblado", "San Cristóbal", NOR, "Paso de la cañada Galápagos", -89.5031, -0.9298, "IGM poblado «Los Arroyos / Los Tres Palos»", "baja", "El plan sitúa Los Arroyos aguas abajo de La Planada; el poblado IGM está 9 km al este, en la parte alta. Puede ser otro lugar homónimo."),
 ("Av. Jaime Roldós Aguilera / Vía Perimetral", "vía", "San Cristóbal", MAX, "El agua de la cañada Divino Niño drena por la vía e impide el acceso al hospital; la cañada Cerro Quemado la bordea", None, None, "OSM highway=tertiary «Avenida Jaime Roldós Aguilera / Vía Perimetral» (varias vías unidas)", "alta", "Geometría lineal."),
 # --- El Progreso
 ("El Progreso (zona urbana)", "poblado", "San Cristóbal", NOR, "43 viviendas y 124 personas expuestas directamente; inundación por cunetas y bordillos en los sectores bajos", None, None, "CGREG suelo urbano El Progreso (polígono)", "alta", "Geometría poligonal."),
 ("Cerro Verde (recinto)", "recinto", "San Cristóbal", NOR, "Cañadas del recinto", -89.44263, -0.90209, "OSM place=hamlet (n3077654557); IGM poblado; INEC localidad", "alta", ""),
 ("El Chino (recinto)", "recinto", "San Cristóbal", NOR, "Cañadas del recinto", -89.45909, -0.91437, "INEC localidad «El Chino»; IGM topónimo (-89,4658; -0,9019)", "media", ""),
 ("Las Goteras (recinto)", "recinto", "San Cristóbal", NOR, "Cañadas del recinto", -89.44372, -0.87737, "INEC localidad «Las Goteras»", "media", "El manantial IGM «Vertiente Las Goteras» está 3,4 km al oeste (-89,4771; -0,8842)."),
 ("Cerro Gato (recinto)", "recinto", "San Cristóbal", NOR, "Cañadas del recinto", -89.4843, -0.9148, "IGM topónimo «Cerro Gato»; INEC localidades «Cerro Gato» (-89,4694; -0,9204) y (-89,4893; -0,9268)", "media", ""),
 ("Viveros del PNG", "infraestructura", "San Cristóbal", NOR, "Cañadas de los viveros", -89.5535, -0.9197, "IGM edificio_p «Vivero El Progreso»", "baja", "No consta que sea el vivero del PNG."),
 ("Galapaguera Cerro Colorado (Centro de Crianza David Rodríguez)", "infraestructura PNG", "San Cristóbal", NOR, "Cañadas de la galapaguera", -89.43679, -0.91365, "OSM leisure=nature_reserve «Galapaguera de Cerro Colorado» (n3077654257); IGM topónimo (-89,4411; -0,9205)", "alta", ""),
 # --- Floreana
 ("Puerto Velasco Ibarra (todo el poblado)", "poblado", "Floreana", NOR, "Todo el poblado en riesgo; conectar las cañadas Hormiga y Varonesa con 500 m de excavación para proteger Playa Negra", None, None, "IGM zona_urbana «Puerto Velasco Ibarra» (polígono); OSM place (n249596983)", "alta", "Geometría poligonal."),
 ("Playa Negra (Floreana)", "playa", "Floreana", NOR, "A proteger con la conexión de las cañadas", -90.48847, -1.27649, "OSM natural=beach «Playa Negra» (r2045693); IGM «Fondeadero Playa Negra»", "alta", ""),
 ("Dispensario médico (Floreana)", "salud", "Floreana", NOR, "Lugar estratégico en riesgo", -90.48574, -1.27520, "OSM building=hospital «Dispensario Médico» (w155185461)", "alta", ""),
 ("Empresa eléctrica (Floreana)", "energía", "Floreana", NOR, "Lugar estratégico en riesgo", -90.48705, -1.27634, "OSM power=generator «Perla Solar» (w98735385)", "media", "Es la central de generación; las oficinas de la empresa pueden estar en otro edificio."),
]
NO = [
 ("Talleres del Consejo de Gobierno (CGREG)", "San Cristóbal", "Punto donde la cañada Divino Niño se separa de la Galápagos", "No figura en OSM, IGM ni en capas oficiales."),
 ("Estación Terrena", "San Cristóbal", "La cañada Cerro Quemado bordea la vía perimetral en este sector", "No figura en OSM ni IGM."),
 ("Sector El Manantial (Manzanillo)", "San Cristóbal", "Ramificaciones desde La Planada", "Sin topónimo; solo se sabe que está en Manzanillo."),
 ("Barrio San Francisco", "San Cristóbal", "Afectado por las cañadas Galápagos y Cerro Quemado", "Solo hay un hotel homónimo en OSM; no sirve como referencia del barrio."),
 ("Barrio Fragata", "San Cristóbal", "Afectado por las cañadas Galápagos y Cerro Quemado", "Solo hay comercios homónimos en OSM."),
 ("Sector Los Arrayanes (Barrio Palmeras)", "San Cristóbal", "La cañada cruza el centro del barrio", "Sin topónimo; se usa el punto del barrio Palmeras."),
 ("La Picada / Bar La Picada", "San Cristóbal", "Limpieza de 240 m urbanos y 170 m en el PNG; 7 meses sin servicios básicos", "No figura en OSM ni IGM."),
 ("Patio de contenedores", "San Cristóbal", "Nacimiento de la cañada de Playa Mann", "No figura en OSM ni IGM."),
 ("Parque Artesanal (San Cristóbal)", "San Cristóbal", "Cañada del Parque Artesanal", "No figura en OSM ni IGM."),
 ("La Lobería (Floreana)", "Floreana", "Cañada La Varonesa / Lobería", "Las «Loberías» de OSM e IGM están en San Cristóbal; no hay una en Floreana."),
 ("Cañada perimetral La Hormiga (Floreana)", "Floreana", "A conectar con La Varonesa", "No figura en OSM ni IGM."),
 ("Cañada La Varonesa (Floreana)", "Floreana", "A conectar con La Hormiga", "No figura en OSM ni IGM («Casa de la Baronesa» de OSM está en la costa norte, 6 km al noreste)."),
 ("Desalinizadora (Floreana)", "Floreana", "Lugar estratégico en riesgo", "No figura en OSM ni IGM."),
 ("Bodega parroquial, ABG y oficinas del PNG (Floreana)", "Floreana", "Lugares estratégicos en riesgo", "No figuran en OSM ni IGM."),
]

def cargar(rel, cond):
    return [(shape(f["geometry"]), f["properties"]) for f in json.loads((ROOT / rel).read_text())["features"] if f.get("geometry") and cond(f["properties"])]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    feats = []
    for nombre, tipo, isla, pr, af, lon, lat, fu, cf, nota in L:
        if lon is not None:
            geom = {"type": "Point", "coordinates": [lon, lat]}
        elif "Perimetral" in nombre:
            ls = [g for g, p in cargar("capas/osm/vias.geojson", lambda p: "Roldós" in (p.get("name") or "") or "Roldos" in (p.get("name") or ""))]
            geom = mapping(linemerge(unary_union(ls)))
        elif nombre.startswith("El Progreso"):
            geom = mapping(unary_union([g for g, p in cargar("capas/final/suelo_urbano_rural_cgreg.geojson", lambda p: p.get("parroquia") == "El Progreso" and p.get("suelo") == "Suelo urbano")]))
        else:
            geom = mapping(unary_union([g for g, p in cargar("descargas/igm/wfs/zona_urbana.geojson", lambda p: p.get("nam") == "Puerto Velasco Ibarra")]))
        feats.append({"type": "Feature", "geometry": geom, "properties": dict(nombre=nombre, tipo=tipo, isla=isla, prioridad_ugr=pr,
                      afectacion_reportada=af, fuente_ubicacion=fu, confianza=cf, nota=nota, fuente_listado=PLAN)})
    (OUT / "lugares_plan.geojson").write_text(json.dumps({"type": "FeatureCollection", "metadata": {
        "titulo": "Lugares del Plan de Acción SC-4-09-2026 (UGR GAD San Cristóbal) — ubicación PRELIMINAR", "criterio_confianza": __doc__.split("Confianza de la ubicación:")[1].split("Coordenadas OSM")[0].strip()},
        "features": feats}, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "no_localizados.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["nombre", "isla", "afectacion_o_rol_en_el_plan", "estado", "motivo"])
        for n, i, a, m in NO: w.writerow([n, i, a, "no localizado", m])
    print("lugares", len(feats), "no localizados", len(NO))

if __name__ == "__main__":
    main()
