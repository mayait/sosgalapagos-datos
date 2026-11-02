"""Configura un GeoServer LOCAL (demo) con las capas de Galápagos, vía REST.

- Workspaces «zona» (zona poblada) y «completo» (islas completas), cada uno con un
  almacén «directorio de Shapefiles» que apunta a geoserver-local/datos/<variante>.
- Estilos SLD generados desde el manifiesto capas.json (mismos colores que el mapa web).
- Relieve y pendientes como WorldImage (PNG + .pgw).
- Un grupo de capas «galapagos» por workspace.

Requisitos: GeoServer corriendo en http://127.0.0.1:8085/geoserver con el usuario de
fábrica (solo para pruebas locales) y los Shapefile descomprimidos en geoserver-local/datos/.
Uso: .venv/bin/python -I scripts/11_geoserver_local.py
"""
import base64, json, pathlib, re, urllib.request, urllib.error, importlib.util
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parents[1]
GS = "http://127.0.0.1:8085/geoserver"
AUTH = "Basic " + base64.b64encode(b"admin:geoserver").decode()      # credencial de fábrica, solo local
DATOS = ROOT / "geoserver-local" / "datos"
spec = importlib.util.spec_from_file_location("pub", ROOT / "scripts" / "10_publicar_web.py")
pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
MAN = json.loads((ROOT / "publicar" / "mapas" / "capas.json").read_text())


def req(method, path, body=None, ctype="application/json", ok=(200, 201)):
    data = body.encode() if isinstance(body, str) else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(GS + "/rest" + path, data=data, method=method,
                               headers={"Authorization": AUTH, "Content-Type": ctype, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        if e.code in ok: return e.code, ""
        return e.code, e.read().decode()[:300]


def zoom_a_escala(z): return 559082264.0 / (2 ** z)


# ───────────── SLD desde el manifiesto ─────────────
DEF = {"color": "#3388ff", "weight": 3, "opacity": 1.0, "fillOpacity": 0.2}

def stroke(s):
    if s.get("weight", DEF["weight"]) == 0 or s.get("stroke") is False: return ""
    dash = f'<CssParameter name="stroke-dasharray">{escape(str(s["dashArray"]).replace(",", " "))}</CssParameter>' if s.get("dashArray") else ""
    return (f'<Stroke><CssParameter name="stroke">{s.get("color", DEF["color"])}</CssParameter>'
            f'<CssParameter name="stroke-width">{s.get("weight", DEF["weight"])}</CssParameter>'
            f'<CssParameter name="stroke-opacity">{s.get("opacity", DEF["opacity"])}</CssParameter>'
            f'<CssParameter name="stroke-linecap">round</CssParameter><CssParameter name="stroke-linejoin">round</CssParameter>{dash}</Stroke>')

def simbolos(capa, s):
    t = capa["tipo"]
    if t == "linea":
        return f"<LineSymbolizer>{stroke(s)}</LineSymbolizer>"
    if t == "punto":
        r = s.get("radius", 5)
        return (f'<PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName>'
                f'<Fill><CssParameter name="fill">{s.get("fillColor", s.get("color", DEF["color"]))}</CssParameter></Fill>'
                f'<Stroke><CssParameter name="stroke">#ffffff</CssParameter><CssParameter name="stroke-width">1.3</CssParameter></Stroke>'
                f'</Mark><Size>{2 * r + 2}</Size></Graphic></PointSymbolizer>')
    fc = s.get("fillColor", s.get("color", DEF["color"]))
    if str(fc).startswith("url("):                        # rayado del Parque Nacional
        pt = capa.get("patron", {})
        fondo = (f'<PolygonSymbolizer><Fill><CssParameter name="fill">{pt.get("fondo", "#bbf7d0")}</CssParameter>'
                 f'<CssParameter name="fill-opacity">{pt.get("opacidad_fondo", 0.3)}</CssParameter></Fill></PolygonSymbolizer>')
        rayas = (f'<PolygonSymbolizer><Fill><GraphicFill><Graphic><Mark><WellKnownName>shape://slash</WellKnownName>'
                 f'<Stroke><CssParameter name="stroke">{pt.get("color", "#15803d")}</CssParameter>'
                 f'<CssParameter name="stroke-width">{pt.get("grosor", 1.4)}</CssParameter>'
                 f'<CssParameter name="stroke-opacity">{pt.get("opacidad", 0.55)}</CssParameter></Stroke></Mark>'
                 f'<Size>{pt.get("separacion", 8)}</Size></Graphic></GraphicFill></Fill></PolygonSymbolizer>')
        return fondo + rayas
    return (f'<PolygonSymbolizer><Fill><CssParameter name="fill">{fc}</CssParameter>'
            f'<CssParameter name="fill-opacity">{s.get("fillOpacity", DEF["fillOpacity"])}</CssParameter></Fill>{stroke(s)}</PolygonSymbolizer>')

def literal(v):
    return "true" if v is True else "false" if v is False else escape(str(v))

def sld(nombre, capas, campos):
    """capas: entradas del manifiesto que comparten archivo (p. ej. los 3 grupos de puntos clave)."""
    capa = capas[0]
    f = lambda p: campos.get(p, p[:10])
    maxesc = f"<MaxScaleDenominator>{zoom_a_escala(capa['zoom_min'] - 0.5):.0f}</MaxScaleDenominator>" if capa.get("zoom_min") else ""
    reglas = []
    clas = None
    for c in capas:                                       # une las clasificaciones de las capas que comparten archivo
        if c.get("clasificar"):
            if clas is None: clas = json.loads(json.dumps(c["clasificar"]))
            elif "valores" in c["clasificar"]: clas.setdefault("valores", {}).update(c["clasificar"]["valores"])
    base = capa.get("estilo", {})
    if capa.get("solo_rotulo"):
        pass
    elif clas and clas.get("rangos"):
        prev = None
        for r in clas["rangos"]:
            k = {kk: vv for kk, vv in r.items() if kk not in ("etiqueta", "hasta", "simbolo")}
            cond = f'<ogc:PropertyIsLessThanOrEqualTo><ogc:PropertyName>{f(clas["propiedad"])}</ogc:PropertyName><ogc:Literal>{r["hasta"]}</ogc:Literal></ogc:PropertyIsLessThanOrEqualTo>'
            if prev is not None:
                cond = f'<ogc:And><ogc:PropertyIsGreaterThan><ogc:PropertyName>{f(clas["propiedad"])}</ogc:PropertyName><ogc:Literal>{prev}</ogc:Literal></ogc:PropertyIsGreaterThan>{cond}</ogc:And>'
            reglas.append(f'<Rule><Title>{escape(r.get("etiqueta", ""))}</Title><ogc:Filter>{cond}</ogc:Filter>{maxesc}{simbolos(capa, {**base, **k})}</Rule>')
            prev = r["hasta"]
    elif clas and clas.get("valores"):
        for v, r in clas["valores"].items():
            k = {kk: vv for kk, vv in r.items() if kk not in ("etiqueta", "simbolo")}
            vv = True if v == "true" else False if v == "false" else v
            reglas.append(f'<Rule><Title>{escape(r.get("etiqueta", v))}</Title><ogc:Filter><ogc:PropertyIsEqualTo>'
                          f'<ogc:PropertyName>{f(clas["propiedad"])}</ogc:PropertyName><ogc:Literal>{literal(vv)}</ogc:Literal>'
                          f'</ogc:PropertyIsEqualTo></ogc:Filter>{maxesc}{simbolos(capa, {**base, **k})}</Rule>')
        o = clas.get("otro")
        k = {kk: vv for kk, vv in (o or {}).items() if kk not in ("etiqueta", "simbolo")}
        reglas.append(f'<Rule><Title>{escape((o or {}).get("etiqueta", "Otros"))}</Title><ElseFilter/>{maxesc}{simbolos(capa, {**base, **k})}</Rule>')
    else:
        reglas.append(f'<Rule><Title>{escape(capa["titulo"])}</Title>{maxesc}{simbolos(capa, base)}</Rule>')
    if capa.get("borde"):                                 # contorno blanco bajo las líneas (quebradas)
        reglas.insert(0, f'<Rule><Title>Borde</Title>{maxesc}<LineSymbolizer>{stroke(capa["borde"])}</LineSymbolizer></Rule>')
    rot = capa.get("rotulo")
    if rot:
        esc_rot = zoom_a_escala(max(capa.get("zoom_min", 0), 14) - 0.5)
        place = ('<LabelPlacement><LinePlacement/></LabelPlacement>' if capa["tipo"] == "linea"
                 else '<LabelPlacement><PointPlacement><AnchorPoint><AnchorPointX>0.5</AnchorPointX><AnchorPointY>0.5</AnchorPointY></AnchorPoint></PointPlacement></LabelPlacement>')
        reglas.append(f'<Rule><Title>Rótulos</Title><MaxScaleDenominator>{esc_rot:.0f}</MaxScaleDenominator><TextSymbolizer>'
                      f'<Label><ogc:PropertyName>{f(rot["propiedad"])}</ogc:PropertyName></Label>'
                      f'<Font><CssParameter name="font-family">SansSerif</CssParameter><CssParameter name="font-size">11</CssParameter></Font>'
                      f'{place}<Halo><Radius>1.5</Radius><Fill><CssParameter name="fill">#FFFFFF</CssParameter></Fill></Halo>'
                      f'<Fill><CssParameter name="fill">{"#374151" if capa.get("solo_rotulo") else "#7c2d12"}</CssParameter></Fill>'
                      f'<VendorOption name="followLine">true</VendorOption><VendorOption name="maxDisplacement">40</VendorOption>'
                      f'<VendorOption name="group">yes</VendorOption></TextSymbolizer></Rule>')
    return (f'<?xml version="1.0" encoding="UTF-8"?><StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" '
            f'xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<NamedLayer><Name>{nombre}</Name><UserStyle><Title>{escape(capa["titulo"])}</Title><FeatureTypeStyle>{"".join(reglas)}'
            f'</FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>')


def main():
    st, _ = req("GET", "/about/version")
    assert st == 200, "GeoServer no responde en " + GS
    # Fuera los datos de ejemplo que trae GeoServer
    st, body = req("GET", "/workspaces")
    for w in (json.loads(body).get("workspaces") or {}).get("workspace", []) if st == 200 else []:
        if w["name"] not in ("zona", "completo"):
            req("DELETE", f"/workspaces/{w['name']}?recurse=true")
    req("DELETE", "/layergroups/spearfish"); req("DELETE", "/layergroups/tasmania"); req("DELETE", "/layergroups/tiger-ny")
    por_archivo = {}
    for g in MAN["grupos"]:
        for c in g["capas"]:
            if c.get("archivo"): por_archivo.setdefault(c["archivo"][:-8], []).append(c)
    orden = [c["archivo"][:-8] for g in reversed(MAN["grupos"]) for c in reversed(g["capas"])
             if c.get("archivo") and (c.get("visible") or c["archivo"].startswith("quebradas"))]
    orden = list(dict.fromkeys(orden))
    rango = {"poligono": 0, "linea": 1, "punto": 2}
    orden.sort(key=lambda n: (rango.get(por_archivo[n][0]["tipo"], 0), 0 if n.startswith("parque") else 1))   # áreas abajo, puntos arriba
    for var in ("zona", "completo"):
        d = DATOS / var
        req("DELETE", f"/workspaces/{var}?recurse=true")
        st, b = req("POST", "/workspaces", {"workspace": {"name": var}})
        print(var, "workspace", st, b[:80])
        st, b = req("POST", f"/workspaces/{var}/datastores", {"dataStore": {"name": "capas", "type": "Directory of spatial files (shapefiles)",
                    "connectionParameters": {"entry": [{"@key": "url", "$": "file:" + str(d)}, {"@key": "charset", "$": "UTF-8"},
                                                       {"@key": "fstype", "$": "shape"}, {"@key": "create spatial index", "$": "true"}]}}})
        print(var, "datastore", st, b[:120])
        for shp in sorted(d.glob("*.shp")):
            nombre = shp.stem
            capas = por_archivo.get(nombre) or por_archivo.get(re.sub(r"_(punto|linea|poligono)s$", "", nombre))
            if not capas: continue
            src = ROOT / "publicar" / "mapas" / "datos" / var / f"{capas[0]['archivo']}"
            feats = json.loads(src.read_text())["features"]
            campos = pub.campos_de(feats)[2]
            estilo = f"{var}_{nombre}"
            st, b = req("POST", f"/workspaces/{var}/datastores/capas/featuretypes",
                        {"featureType": {"name": nombre, "nativeName": nombre, "srs": "EPSG:4326", "title": capas[0]["titulo"],
                                         "abstract": (capas[0].get("descripcion", "") + " Fuente: " + capas[0].get("fuente", "")).strip()}})
            if st not in (200, 201): print("  capa", nombre, st, b)
            st, b = req("POST", f"/workspaces/{var}/styles?name={estilo}", sld(estilo, capas, campos), "application/vnd.ogc.sld+xml")
            if st not in (200, 201): print("  estilo", nombre, st, b)
            st, b = req("PUT", f"/layers/{var}:{nombre}", {"layer": {"defaultStyle": {"name": estilo, "workspace": var}}})
            if st != 200: print("  estilo->capa", nombre, st, b)
        # Rásters (PNG + .pgw)
        for png in sorted((d / "raster").glob("*.tif")):          # GeoTIFF convertidos desde los PNG + .pgw
            cs = png.stem
            st, b = req("POST", f"/workspaces/{var}/coveragestores", {"coverageStore": {"name": cs, "type": "GeoTIFF", "enabled": True,
                        "workspace": {"name": var}, "url": "file:" + str(png)}})
            if st in (200, 201):
                st, b = req("POST", f"/workspaces/{var}/coveragestores/{cs}/coverages", {"coverage": {"name": cs, "nativeName": cs.split("_")[-1] if False else png.stem,
                            "srs": "EPSG:4326", "title": cs.replace("_", " ")}})
            if st not in (200, 201): print("  raster", cs, st, b)
        # Grupo de capas con lo que el mapa muestra al abrir
        capas_grupo = [f"{var}:{n}" for n in orden if (d / f"{n}.shp").exists()]
        req("DELETE", f"/workspaces/{var}/layergroups/galapagos")
        st, b = req("POST", f"/workspaces/{var}/layergroups", {"layerGroup": {"name": "galapagos", "title": f"Galápagos — {pub.TITULO_VAR[var]}",
                    "mode": "SINGLE", "publishables": {"published": [{"@type": "layer", "name": n} for n in capas_grupo]}}})
        print(var, "grupo", st, b[:150], capas_grupo)
    print("Listo:", GS + "/web/")


if __name__ == "__main__":
    main()
