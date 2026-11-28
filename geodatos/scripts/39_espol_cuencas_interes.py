# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Cuencas hidrográficas de interés de Santa Cruz (ESPOL), las que usa la mesa técnica de SOS Galápagos.

Autores: Maurizio Mulas, Daniel Garcés, Erwin Larreta, Victoria Rosado y Valeria Vaca (ESPOL).
Entrega: descargas/espol/secciones_cuenca.kmz (KML en EPSG:4326, exportado de ArcGIS como «Seccion_Prueba»).

El archivo trae las secciones alta y baja de tres subcuencas (SCW01, SCW02 y SCW24) y dos microcuencas alrededor de
Puerto Ayora. La franja intermedia que el mapa original de la ESPOL muestra rayada no viene en el archivo.
Se descartan los fragmentos de menos de 100 m² (hay uno de 54 m² en SCW01).

Salida: datos/espol_cuencas/cuencas_interes_santa_cruz.geojson (+ resumen.json). No se edita a mano.
Uso: .venv/bin/python -I scripts/39_espol_cuencas_interes.py
"""
import json, pathlib, re, zipfile, hashlib, datetime
import xml.etree.ElementTree as ET

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
KMZ = ROOT / "descargas/espol/secciones_cuenca.kmz"
OUT = ROOT / "datos/espol_cuencas"
AUTORES = ["Maurizio Mulas", "Daniel Garcés", "Erwin Larreta", "Victoria Rosado", "Valeria Vaca"]
FUENTE = "ESPOL: " + ", ".join(AUTORES[:-1]) + " y " + AUTORES[-1]
K = "{http://www.opengis.net/kml/2.2}"
UTM = Transformer.from_crs(4326, 32715, always_xy=True)
CLASE = {"Sub watersheds": "Subcuenca", "Micro watersheds": "Microcuenca"}
AREA_MIN_M2 = 100
LAT_SECCION_ALTA = -0.67           # las secciones altas quedan al norte de la franja intermedia


def num(s): return float(s.replace(",", ".")) if s else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    kb = KMZ.read_bytes()
    with zipfile.ZipFile(KMZ) as z:
        raiz = ET.fromstring(z.read("doc.kml"))
    feats, descartados = [], 0
    for pm in raiz.iter(K + "Placemark"):
        at = dict(re.findall(r"<td>([^<]+)</td>\s*<td>([^<]*)</td>", pm.find(K + "description").text or ""))
        polys = []
        for pg in pm.iter(K + "Polygon"):
            anillo = lambda e: [tuple(map(float, c.split(",")[:2])) for c in e.text.split()]
            ext = anillo(pg.find(f"{K}outerBoundaryIs//{K}coordinates"))
            huecos = [anillo(h) for h in pg.findall(f"{K}innerBoundaryIs//{K}coordinates")]
            polys.append(Polygon(ext, huecos))
        g = unary_union(polys).buffer(0)
        area = shapely.transform(g, lambda c: np.column_stack(UTM.transform(c[:, 0], c[:, 1]))).area
        if area < AREA_MIN_M2:
            descartados += 1; continue
        clase = CLASE.get(at.get("Classify"), at.get("Classify"))
        nombre = (at.get("Name") or "").strip()
        if clase == "Subcuenca":
            seccion = "alta" if g.bounds[3] > LAT_SECCION_ALTA else "baja"
            titulo = f"{nombre}, sección {seccion}" if area > 1e6 else f"{nombre}, fragmento de la sección {seccion}"
        else:
            seccion = None
            titulo = f"Microcuenca de {area / 1e6:.2f} km²".replace(".", ",")
        feats.append({"type": "Feature", "geometry": mapping(shapely.set_precision(g, 1e-6)),
                      "properties": {"titulo": titulo, "cuenca": nombre or None, "clase": clase, "seccion": seccion,
                                     "area_km2": round(area / 1e6, 3), "perimetro_km": round(num(at.get("P_km")) or 0, 2),
                                     "id_espol": int(at["Id"]) if at.get("Id") else None,
                                     "autores": ", ".join(AUTORES), "fuente": FUENTE}})
    feats.sort(key=lambda f: (f["properties"]["clase"], f["properties"]["cuenca"] or "", -f["properties"]["area_km2"]))
    (OUT / "cuencas_interes_santa_cruz.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")))
    resumen = {"generado": datetime.date.today().isoformat(), "autores": AUTORES, "institucion": "ESPOL",
               "kmz": {"archivo": str(KMZ.relative_to(ROOT)), "sha256": hashlib.sha256(kb).hexdigest()},
               "poligonos": len(feats), "descartados_por_area": descartados,
               "areas_km2": {f["properties"]["titulo"]: f["properties"]["area_km2"] for f in feats}}
    (OUT / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
