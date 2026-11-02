"""Arma la página pública de mapas con descargas (sosgalapagos.org/mapas/).

Toma los dos paquetes exportados por 08_exportar.py:
  export/galapagos/           → «Zona poblada» (recortado al área de interés)
  export/galapagos-completo/  → «Islas completas» (sin recorte, incluye el parque)
y genera en publicar/mapas/:
  index.html                       visor (de web/index.html)
  datos/<variante>/*.geojson       capas que lee el visor (+ .gz precomprimido)
  descargas/<variante>/*.zip       Shapefile por capa (WGS84, UTF-8) con LEEME
  descargas/<variante>/*.geojson   GeoJSON por capa (enlace directo a datos/)
  descargas/<variante>/todo-*.zip  todas las capas juntas
  descargas.json                   índice que usa el visor (rutas y tamaños)

Uso: .venv/bin/python -I scripts/10_publicar_web.py
Publicar: scripts/publicar_mapas.sh
"""
import json, pathlib, shutil, zipfile, gzip, io, datetime
import shapefile                       # pyshp
from PIL import Image
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely import make_valid

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "publicar" / "mapas"
VARIANTES = {"zona": ROOT / "export" / "galapagos", "completo": ROOT / "export" / "galapagos-completo"}
TITULO_VAR = {"zona": "Zona poblada (recortado al área de interés)", "completo": "Islas completas (sin recorte, incluye el Parque Nacional)"}
HOY = datetime.date.today().isoformat()
PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
       'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')
LICENCIA = """Fuentes: IGM 1:25 000, CGREG, Zonificación PNG 2017 (CGREG/FCD), SNGR/INOCAR, MSP, MINEDUC,
INEC MGN 2026, OpenStreetMap (31-oct-2026), Google Open Buildings y Copernicus GLO-30.

- Vías, nombres de calles y parte de los puntos clave: © colaboradores de OpenStreetMap,
  licencia ODbL 1.0 (https://www.openstreetmap.org/copyright). Si redistribuyes estos datos,
  mantén la atribución y la misma licencia.
- Relieve, pendientes, curvas, cauces adicionales, cuencas, costa baja y susceptibilidad:
  contienen datos modificados de Copernicus DEM GLO-30 (© DLR e.V. 2010-2014 y © Airbus 2014-2018,
  proporcionados por la Comisión Europea).
- La susceptibilidad a inundación, la costa baja y los cauces adicionales son un MODELO sobre un
  DSM de 30 m: sirven para priorizar, no son delimitaciones oficiales.
- La población por manzana es una estimación (viviendas SNGR), no el censo.

Preparado por SOS Galápagos (https://sosgalapagos.org) para la respuesta a las inundaciones
de El Niño, oct-nov 2026. Responsable: Human Centric SAS BIC (IA Humana).
"""
# Capas que se publican completas (islas enteras) también en la cobertura «Zona poblada»
SIEMPRE_COMPLETAS = {"quebradas.geojson"}
# Capas que no están en el manifiesto de la app pero se publican aquí
EXTRA = {
    "id": "otras", "titulo": "Otras capas",
    "capas": [
        {"id": "area_interes", "titulo": "Área de interés (recorte de la zona poblada)", "archivo": "area_interes.geojson", "tipo": "poligono",
         "visible": False, "fuente": "Elaboración propia",
         "descripcion": "Zona agrícola y urbana, cuencas que drenan a los poblados, 500 m alrededor de zonas pobladas y 300 m alrededor de vías.",
         "estilo": {"color": "#7c3aed", "weight": 2, "dashArray": "6 4", "fillOpacity": 0.03},
         "popup": {"titulo": "isla", "campos": {"area_km2": "Área (km²)", "criterio": "Criterio"}}},
        {"id": "parque_zonificacion", "titulo": "Zonificación del Parque Nacional", "archivo": "parque_zonificacion.geojson", "tipo": "poligono",
         "visible": False, "fuente": "Zonificación PNG 2017 (CGREG/FCD)",
         "estilo": {"weight": 0.6, "fillOpacity": 0.35},
         "clasificar": {"propiedad": "zona", "valores": {
             "Intangible": {"etiqueta": "Intangible", "color": "#14532d", "fillColor": "#14532d"},
             "Conservación": {"etiqueta": "Conservación", "color": "#15803d", "fillColor": "#22c55e"},
             "Transición": {"etiqueta": "Transición", "color": "#65a30d", "fillColor": "#a3e635"},
             "Aprovechamiento sustentable": {"etiqueta": "Aprovechamiento sustentable", "color": "#ca8a04", "fillColor": "#facc15"},
             "Área especial": {"etiqueta": "Área especial", "color": "#0e7490", "fillColor": "#22d3ee"}},
             "otro": {"etiqueta": "Otra", "color": "#6b7280", "fillColor": "#9ca3af"}},
         "popup": {"titulo": "zona", "campos": {"isla": "Isla", "fuente": "Fuente"}}},
        {"id": "edificios_expuestos", "titulo": "Edificios expuestos", "archivo": "edificios_expuestos.geojson", "tipo": "poligono",
         "visible": False, "zoom_min": 15, "fuente": "OSM + Google Open Buildings",
         "descripcion": "Edificios en susceptibilidad de inundación, zona de tsunami, franja de quebrada o costa de 0 a 3 m.",
         "estilo": {"color": "#9a3412", "weight": 0.8, "fillColor": "#f97316", "fillOpacity": 0.55},
         "popup": {"titulo": "nombre", "titulo_defecto": "Edificio", "campos": {"susc_inundacion": "Susceptibilidad (0-3)",
                   "zona_tsunami": "Zona de tsunami", "franja_quebrada": "Franja de quebrada", "costa_0_3m": "Costa 0-3 m", "fuente": "Fuente"}}},
    ],
}


def tam(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{max(1, round(n / 1e3))} kB"


def tipo_shp(geom_type):
    return {"Point": "punto", "MultiPoint": "punto", "LineString": "linea", "MultiLineString": "linea",
            "Polygon": "poligono", "MultiPolygon": "poligono"}.get(geom_type)


def limpiar(g):
    """Repara geometrías inválidas (autointersecciones, anillos degenerados) para el Shapefile."""
    poligonal = g.geom_type in ("Polygon", "MultiPolygon")
    lineal = g.geom_type in ("LineString", "MultiLineString")
    if lineal:
        ls = [l for l in getattr(g, "geoms", [g]) if len(l.coords) >= 2 and l.length > 0]
        return ls or None
    if poligonal:
        if not g.is_valid: g = make_valid(g)
        ps = []
        for x in getattr(g, "geoms", [g]):
            if x.geom_type == "Polygon" and not x.is_empty: ps.append(x)
            elif x.geom_type == "MultiPolygon": ps += list(x.geoms)
        return ps or None
    return g


def campos_de(feats):
    """Tipos de campo dBASE y nombres de ≤10 caracteres únicos."""
    tipos, largos = {}, {}
    for f in feats:
        for k, v in (f.get("properties") or {}).items():
            if v is None: continue
            t = "L" if isinstance(v, bool) else "N" if isinstance(v, int) else "F" if isinstance(v, float) else "C"
            prev = tipos.get(k)
            tipos[k] = t if prev in (None, t) else ("F" if {prev, t} == {"N", "F"} else "C")
            largos[k] = max(largos.get(k, 1), len(str(v).encode("utf-8")))
    nombres, usados = {}, set()
    for k in tipos:
        base = k[:10]; n = base; i = 1
        while n.upper() in usados:
            suf = str(i); n = base[:10 - len(suf)] + suf; i += 1
        usados.add(n.upper()); nombres[k] = n
    return tipos, largos, nombres


def escribir_shp(feats, base: pathlib.Path):
    """Escribe base.shp/.shx/.dbf/.prj/.cpg. Devuelve las rutas escritas."""
    feats = [f for f in feats if limpiar(shape(f["geometry"])) is not None]   # sin geometrías degeneradas
    tipos, largos, nombres = campos_de(feats)
    st = tipo_shp(feats[0]["geometry"]["type"])
    w = shapefile.Writer(str(base), shapeType={"punto": shapefile.POINT, "linea": shapefile.POLYLINE, "poligono": shapefile.POLYGON}[st],
                         encoding="utf-8")
    if st == "punto" and any(f["geometry"]["type"] == "MultiPoint" for f in feats):
        w.close(); w = shapefile.Writer(str(base), shapeType=shapefile.MULTIPOINT, encoding="utf-8")
    for k, t in tipos.items():
        if t == "C": w.field(nombres[k], "C", size=min(254, largos[k] + 4))
        elif t == "N": w.field(nombres[k], "N", size=18, decimal=0)
        elif t == "F": w.field(nombres[k], "F", size=19, decimal=8)
        else: w.field(nombres[k], "L")
    if not tipos: w.field("id", "N", size=10, decimal=0)
    for i, f in enumerate(feats):
        g = shape(f["geometry"]); gt = g.geom_type; partes = limpiar(g)
        if gt == "Point": w.point(g.x, g.y)
        elif gt == "MultiPoint":
            w.multipoint([(p.x, p.y) for p in g.geoms])
        elif gt in ("LineString", "MultiLineString"):
            w.line([list(l.coords) for l in partes])
        else:
            rings = []
            for p in partes:
                p = orient(p, sign=-1.0)          # shapefile: exterior en sentido horario
                rings.append(list(p.exterior.coords)); rings += [list(r.coords) for r in p.interiors]
            w.poly(rings)
        p = f.get("properties") or {}
        if tipos:
            rec = []
            for k, t in tipos.items():
                v = p.get(k)
                if t == "C": v = "" if v is None else v if isinstance(v, str) else str(v)   # pyshp escribiría «None»
                rec.append(v)
            w.record(*rec)
        else: w.record(i + 1)
    w.close()
    base.with_suffix(".prj").write_text(PRJ)
    base.with_suffix(".cpg").write_text("UTF-8")
    rutas = [base.with_suffix(s) for s in (".shp", ".shx", ".dbf", ".prj", ".cpg")]
    mapa = "\n".join(f"  {nombres[k]:10s} ← {k}" for k in tipos if nombres[k] != k)
    return rutas, mapa


def leeme(capa_titulo, archivo, var, n, extra=""):
    return (f"{capa_titulo}\n{'=' * len(capa_titulo)}\n\nArchivo de origen: {archivo}\nVersión: {TITULO_VAR[var]}\n"
            f"Elementos: {n}\nSistema de coordenadas: WGS 84 (EPSG:4326)\nCodificación de atributos: UTF-8\nGenerado: {HOY}\n"
            f"{extra}\n{LICENCIA}")


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "datos").mkdir(parents=True); (OUT / "descargas").mkdir()
    man = json.loads((VARIANTES["zona"] / "capas.json").read_text())
    man["grupos"].append(EXTRA)
    man["mapas_base"] = [b for b in man.get("mapas_base", []) if b["id"] != "claro"]
    titulos = {}
    for g in man["grupos"]:
        for c in g["capas"]:
            if c.get("archivo"): titulos.setdefault(c["archivo"], c["titulo"] if c["archivo"] != "puntos_clave.geojson" else "Puntos clave (todas las categorías)")
            if c.get("raster"): titulos.setdefault("raster:" + c["raster"], c["titulo"])
    indice = {"generado": HOY, "variantes": {}}
    tmp = ROOT / "publicar" / "_tmp"
    for var, src in VARIANTES.items():
        d_datos = OUT / "datos" / var; d_desc = OUT / "descargas" / var
        d_datos.mkdir(parents=True); d_desc.mkdir(parents=True)
        shutil.copytree(src / "raster", d_datos / "raster")
        info = {"titulo": TITULO_VAR[var], "archivos": {}}
        todo_shp = zipfile.ZipFile(d_desc / f"todo-{var}-shp.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9)
        todo_gj = zipfile.ZipFile(d_desc / f"todo-{var}-geojson.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9)
        for gj in sorted(src.glob("*.geojson")):
            if var == "zona" and gj.name in SIEMPRE_COMPLETAS:
                gj = VARIANTES["completo"] / gj.name          # sin recorte también en «Zona poblada»
            data = json.loads(gj.read_text())
            feats = [f for f in data["features"] if f.get("geometry")]
            shutil.copy(gj, d_datos / gj.name)
            titulo = titulos.get(gj.name, gj.stem.replace("_", " ").capitalize())
            if not feats: continue
            # Shapefile: un .shp por tipo de geometría
            if tmp.exists(): shutil.rmtree(tmp)
            tmp.mkdir(parents=True)
            grupos = {}
            for f in feats: grupos.setdefault(tipo_shp(f["geometry"]["type"]), []).append(f)
            zpath = d_desc / f"{gj.stem}.zip"
            mapas = []
            with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for t, fs in grupos.items():
                    nombre = gj.stem if len(grupos) == 1 else f"{gj.stem}_{t}s"
                    rutas, mapa = escribir_shp(fs, tmp / nombre)
                    if mapa: mapas.append(f"{nombre}:\n{mapa}")
                    for r in rutas:
                        z.write(r, r.name); todo_shp.write(r, f"{var}/{r.name}")
                extra = ("\nNombres de campo acortados (límite de 10 caracteres del formato Shapefile):\n" + "\n".join(mapas) + "\n") if mapas else ""
                if var == "zona" and gj.name in SIEMPRE_COMPLETAS:
                    extra = "\nEsta capa va completa (todas las islas, sin recorte) también en la cobertura «Zona poblada».\n" + extra
                txt = leeme(titulo, gj.name, var, len(feats), extra)
                z.writestr("LEEME.txt", txt)
            todo_gj.write(gj, f"{var}/{gj.name}")
            info["archivos"][gj.name] = {"titulo": titulo, "elementos": len(feats),
                                         "shp": {"url": f"descargas/{var}/{zpath.name}", "tam": tam(zpath.stat().st_size)},
                                         "geojson": {"url": f"datos/{var}/{gj.name}", "tam": tam(gj.stat().st_size)}}
        # Rásters: PNG + archivo de georreferencia (.pgw) + .prj
        lim = json.loads((src / "raster" / "limites.json").read_text())
        for kind in sorted({p.stem.split("_")[-1] for p in (src / "raster").glob("*.png")}):
            zpath = d_desc / f"raster_{kind}.zip"
            with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
                for k, v in lim.items():
                    png = src / "raster" / f"{k}_{kind}.png"
                    if not png.exists(): continue
                    (s, wl), (n, e) = v["bounds"]
                    W, H = Image.open(png).size
                    a, ee = (e - wl) / W, -(n - s) / H
                    pgw = f"{a:.12f}\n0\n0\n{ee:.12f}\n{wl + a / 2:.12f}\n{n + ee / 2:.12f}\n"
                    for zz in (z, todo_shp):
                        pre = "" if zz is z else f"{var}/raster/"
                        zz.write(png, pre + png.name); zz.writestr(pre + png.with_suffix(".pgw").name, pgw); zz.writestr(pre + png.with_suffix(".prj").name, PRJ)
                z.writestr("LEEME.txt", leeme(titulos.get("raster:" + kind, kind), f"raster/*_{kind}.png", var, len(lim),
                                              "\nImagen PNG georreferenciada con archivo de mundo (.pgw). QGIS y ArcGIS la abren directamente.\n"))
            info["archivos"]["raster:" + kind] = {"titulo": titulos.get("raster:" + kind, kind), "shp": {"url": f"descargas/{var}/{zpath.name}",
                                                  "tam": tam(zpath.stat().st_size), "formato": "PNG"}}
        for z in (todo_shp, todo_gj):
            z.writestr(f"{var}/LEEME.txt", leeme(f"Capas de la emergencia — Galápagos ({TITULO_VAR[var]})", "todas", var, "—"))
            z.writestr(f"{var}/capas.json", json.dumps(man, ensure_ascii=False, indent=1))
            z.close()
        info["todo"] = {"shp": {"url": f"descargas/{var}/todo-{var}-shp.zip", "tam": tam((d_desc / f"todo-{var}-shp.zip").stat().st_size)},
                        "geojson": {"url": f"descargas/{var}/todo-{var}-geojson.zip", "tam": tam((d_desc / f"todo-{var}-geojson.zip").stat().st_size)}}
        (d_datos / "resumen_exposicion.json").write_text((src / "resumen_exposicion.json").read_text())
        indice["variantes"][var] = info
    if tmp.exists(): shutil.rmtree(tmp)
    (OUT / "capas.json").write_text(json.dumps(man, ensure_ascii=False, separators=(",", ":")))
    (OUT / "descargas.json").write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")))
    html = (ROOT / "web" / "index.html").read_text().replace("__VERSION__", HOY.replace("-", "") + datetime.datetime.now().strftime("%H%M"))
    (OUT / "index.html").write_text(html)
    # Precompresión para Caddy (file_server precompressed gzip)
    for p in OUT.rglob("*"):
        if p.suffix in (".geojson", ".json", ".html"):
            with gzip.open(p.with_name(p.name + ".gz"), "wb", compresslevel=9) as g: g.write(p.read_bytes())
    tot = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"publicar/mapas: {tot / 1e6:.1f} MB")
    for var, info in indice["variantes"].items():
        print(f"  {var}: {len(info['archivos'])} descargas · todo SHP {info['todo']['shp']['tam']} · todo GeoJSON {info['todo']['geojson']['tam']}")


if __name__ == "__main__":
    main()
