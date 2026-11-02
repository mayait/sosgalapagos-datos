"""Genera el sitio estático sosgalapagos.org/estudios/ a partir de los textos y datos de geodatos/estudios/.

Cada estudio es una página larga con:
- aviso de estudio preliminar;
- índice lateral;
- secciones (Markdown) con figuras ampliables;
- mapa interactivo (Leaflet);
- vista 3D interactiva (Plotly, carga diferida);
- línea del tiempo;
- descargas de datos;
- comentarios por sección (API en /estudios/api, ver app/deploy/sosgalapagos/comentarios).

Uso:     .venv/bin/python -I scripts/19_estudios_web.py
Publicar: scripts/publicar_estudios.sh
"""
import csv, datetime, gzip, html, json, pathlib, re, shutil
import markdown
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
EST = ROOT / "estudios"
OUT = ROOT / "publicar" / "estudios"
HOY = datetime.date.today()
VERSION = "0.2 preliminar"

LEAFLET = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">'
           '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>')
PLOTLY = "https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.3/plotly.min.js"

# ---------------------------------------------------------------- configuración de estudios
ESTUDIOS = json.loads((EST / "estudios.json").read_text())


# ---------------------------------------------------------------- utilidades
def slug(t):
    t = re.sub(r"<[^>]+>", "", t).lower()
    t = (t.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ü", "u"))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def copiar_imagen(src: pathlib.Path, dst_dir: pathlib.Path):
    """PNG de figura → WebP (≤1600 px) para la página y PNG original para ampliar/descargar."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".gif":                       # animaciones: tal cual
        shutil.copy2(src, dst_dir / src.name)
        w, h = Image.open(src).size
        return src.name, src.name, (w, h)
    im = Image.open(src).convert("RGB")
    from PIL import ImageChops
    bb = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if bb:
        p = 14; im = im.crop((max(bb[0] - p, 0), max(bb[1] - p, 0), min(bb[2] + p, im.width), min(bb[3] + p, im.height)))
    big = dst_dir / (src.stem + ".png"); im.save(big, optimize=True)
    w = im.copy(); w.thumbnail((1600, 1600)); web = dst_dir / (src.stem + ".webp"); w.save(web, "WEBP", quality=82)
    return web.name, big.name, w.size


def md_a_html(texto, base_dirs, dst_fig, figs, tabs):
    """Convierte el Markdown del proyecto (con «Tabla:», figuras y [[SALTO]]) a HTML."""
    texto = texto.replace("[[SALTO]]", "")
    lineas, out = texto.splitlines(), []
    for ln in lineas:
        m = re.match(r"^Tabla:\s*(.*)", ln.strip())
        if m:
            tabs[0] += 1
            out.append(f'\n<p class="cap cap-tabla"><b>Tabla {tabs[0]}.</b> {html.escape(m.group(1))}</p>\n')
            continue
        m = re.match(r"^!\[(.*)\]\((.*)\)\s*$", ln.strip())
        if m:
            cap, ruta = m.groups()
            src = next((b / ruta for b in base_dirs if (b / ruta).exists()), None)
            if src is None:
                out.append(f'<p class="cap"><i>[Figura pendiente: {html.escape(ruta)}]</i></p>'); continue
            web, big, (w, h) = copiar_imagen(src, dst_fig)
            figs[0] += 1
            cap_html = markdown.markdown(cap).removeprefix("<p>").removesuffix("</p>")
            out.append(f'\n<figure><a href="figuras/{big}" class="ampliar"><img src="figuras/{web}" width="{w}" height="{h}" loading="lazy" '
                       f'alt="{html.escape(re.sub("<[^>]+>", "", cap_html))}"></a><figcaption><b>Figura {figs[0]}.</b> {cap_html}</figcaption></figure>\n')
            continue
        out.append(ln)
    h = markdown.markdown("\n".join(out), extensions=["tables", "sane_lists"], output_format="html5")
    h = re.sub(r"<table>", '<div class="tabla"><table>', h).replace("</table>", "</table></div>")
    h = re.sub(r'(https?://[^\s<"\)]+)(?![^<]*</a>)', r'<a href="\1" rel="noopener" target="_blank">\1</a>', h)
    return h


def secciones(html_txt):
    """Parte el HTML por <h1> y devuelve [(id, título, html)] y el índice de <h2>."""
    partes = re.split(r"(<h1>.*?</h1>)", html_txt)
    secs, cur = [], None
    for p in partes:
        m = re.match(r"<h1>(.*?)</h1>", p)
        if m:
            cur = [slug(m.group(1)), m.group(1), ""]; secs.append(cur)
        elif cur is not None:
            cur[2] += p
        elif p.strip():
            secs.append(["introduccion", "", p]); cur = secs[-1]
    out = []
    for sid, tit, cuerpo in secs:
        subs = []
        def h2(m):
            t = m.group(1); i = f"{sid}--{slug(t)}"; subs.append((i, t)); return f'<h2 id="{i}">{t}</h2>'
        cuerpo = re.sub(r"<h2>(.*?)</h2>", h2, cuerpo)
        out.append((sid, tit, cuerpo, subs))
    return out


def filtrar(feats, filtros):
    for flt in (filtros or []):
        feats = [f for f in feats if str(f["properties"].get(flt["campo"])) in flt["valores"]]
    return feats


def renumerar(texto, n, mapa, titulo=None):
    """Ajusta la numeración de los títulos al orden de la página web y las referencias «sección N.M»."""
    def h(m):
        nivel, num, sub, resto = m.group(1), m.group(2), m.group(3) or "", m.group(4)
        if nivel == "#" and titulo: return f"# {n}. {titulo}" if n else f"# {titulo}"
        if n is None: return f"{nivel} {resto}"
        return f"{nivel} {n}{sub}{'.' if not sub else ''} {resto}"
    texto = re.sub(r"^(#{1,3}) (\d+)((?:\.\d+)*)\.? +(.*)$", h, texto, flags=re.M)
    if titulo and not re.search(r"^# ", texto, flags=re.M): texto = f"# {n}. {titulo}\n" + texto
    if titulo: texto = re.sub(r"^# (?!\d)(.*)$", f"# {n}. {titulo}" if n else f"# {titulo}", texto, count=1, flags=re.M)
    if mapa:
        def ref(m):
            num = m.group(2)
            return m.group(1) + mapa.get(num, num) + (m.group(3) or "")
        texto = re.sub(r"(secci[oó]n(?:es)?\s+|§\s?)(\d+)((?:\.\d+)?)", ref, texto)
    return texto


def dem_json(cfg, dst):
    """Rejilla del DSM (Plotly surface) en JSON compacto: cotas en dm (enteros)."""
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_origin
    from pyproj import Transformer
    v = cfg["vista3d"]
    T = Transformer.from_crs(4326, 32715, always_xy=True)
    cx, cy = T.transform(*v["centro"])
    n = v.get("celdas", 160); dx = v["ancho_m"] / n
    tr = from_origin(cx - v["ancho_m"] / 2, cy + v["alto_m"] / 2, dx, dx)
    ny = int(v["alto_m"] / dx)
    z = np.full((ny, n), np.nan, "float32")
    with rasterio.open(ROOT / v["dem"]) as s:
        reproject(s.read(1).astype("float32"), z, src_transform=s.transform, src_crs=s.crs, src_nodata=-9999,
                  dst_transform=tr, dst_crs="EPSG:32715", dst_nodata=np.nan, resampling=Resampling.bilinear)
    z = np.nan_to_num(z, nan=0).clip(min=0)
    capas = []
    for c in v.get("capas", []):
        p = ROOT / c["archivo"]
        if not p.exists(): continue
        for f in filtrar([f for f in json.loads(p.read_text())["features"] if f.get("geometry")], c.get("filtro"))[: c.get("max", 999)]:
            g = f["geometry"]; geoms = [g["coordinates"]] if g["type"] in ("LineString", "Polygon") else g["coordinates"] if g["type"].startswith("Multi") else [[g["coordinates"]]]
            for coords in geoms:
                ring = coords[0] if g["type"] in ("Polygon", "MultiPolygon") else coords
                if g["type"] == "Point": ring = [g["coordinates"]]
                xs, ys = T.transform([q[0] for q in ring], [q[1] for q in ring])
                cols = np.clip(((np.array(xs) - (cx - v["ancho_m"] / 2)) / dx).astype(int), 0, n - 1)
                rows = np.clip((((cy + v["alto_m"] / 2) - np.array(ys)) / dx).astype(int), 0, ny - 1)
                dentro = (np.array(xs) > cx - v["ancho_m"] / 2) & (np.array(xs) < cx + v["ancho_m"] / 2) & (np.array(ys) > cy - v["alto_m"] / 2) & (np.array(ys) < cy + v["alto_m"] / 2)
                if not dentro.any(): continue
                capas.append({"n": c["nombre"], "c": c["color"], "t": "p" if g["type"] == "Point" else "l",
                              "x": [round(float(a - cx)) for a in np.array(xs)[dentro]], "y": [round(float(b - cy)) for b in np.array(ys)[dentro]],
                              "z": [round(float(z[r, k]) + c.get("off", 4), 1) for r, k in zip(rows[dentro], cols[dentro])]})
    agua = None
    cal = ROOT / v.get("calado", "-")
    if cal.exists():
        h = np.full((ny, n), np.nan, "float32")
        with rasterio.open(cal) as s2:
            reproject(s2.read(1).astype("float32"), h, src_transform=s2.transform, src_crs=s2.crs, src_nodata=s2.nodata,
                      dst_transform=tr, dst_crs="EPSG:32715", dst_nodata=np.nan, resampling=Resampling.max)
        h = np.where(np.nan_to_num(h) >= 0.1, h, np.nan)
        agua = [[None if not np.isfinite(q) else round(float(q), 2) for q in fila] for fila in h]
    d = {"dx": round(dx, 2), "nx": n, "ny": ny, "x0": -v["ancho_m"] / 2, "y0": v["alto_m"] / 2, "agua": agua, "agua_txt": v.get("calado_titulo", "Calado máximo (modelo 2D)"),
         "z": (z * 10).round().astype(int).tolist(), "vexag": v.get("vexag", 4), "capas": capas, "titulo": v.get("titulo", "")}
    (dst / "vista3d.json").write_text(json.dumps(d, separators=(",", ":")))


def linea_tiempo(cfg):
    p = ROOT / cfg.get("linea_tiempo", "-")
    if not p.exists(): return ""
    filas = list(csv.DictReader(open(p, encoding="utf-8")))
    filas.sort(key=lambda r: r.get("fecha_hora_utc6", ""))
    tipos = {"alerta_oficial": "Alerta oficial", "pronostico": "Pronóstico", "lluvia_medida": "Lluvia medida", "hidrologia_modelada": "Hidrología (modelo)",
             "impacto_reportado": "Impacto reportado", "respuesta": "Respuesta", "dato_faltante": "Dato faltante"}
    bot = "".join(f'<button class="filtro activo" data-tipo="{k}"><span class="pt t-{k}"></span>{v}</button>' for k, v in tipos.items())
    items = []
    for r in filas:
        t = r.get("tipo", ""); u = r.get("fuente_url", "").strip()
        fuente = f' <a href="{html.escape(u)}" target="_blank" rel="noopener">fuente</a>' if u.startswith("http") else (f' <span class="muted">{html.escape(u)}</span>' if u else "")
        items.append(f'<li class="ev t-{html.escape(t)}" data-tipo="{html.escape(t)}"><time>{html.escape(r.get("fecha_hora_utc6", "").replace("T", " "))}'
                     f'{" ≈" if r.get("precision") in ("aprox.", "aprox", "día", "dia") else ""}</time>'
                     f'<div><span class="actor">{html.escape(r.get("actor", ""))}</span> {html.escape(r.get("descripcion", ""))}{fuente}'
                     f' <span class="conf conf-{html.escape(r.get("confianza", ""))}">confianza {html.escape(r.get("confianza", "—"))}</span></div></li>')
    return (f'<div class="lt"><div class="lt-filtros">{bot}</div><p class="muted">Hora de Galápagos (UTC−6). ≈ indica hora aproximada o solo fecha.</p>'
            f'<ol class="lt-lista">{"".join(items)}</ol></div>')


def descargas(cfg, dst):
    filas = []
    for d in cfg.get("descargas", []):
        for p in sorted((ROOT / d["dir"]).glob(d.get("patron", "*"))):
            if p.is_dir() or p.stat().st_size > 15e6: continue
            rel = f'datos/{d["prefijo"]}{p.name}'
            (dst / "datos" / d["prefijo"]).mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst / rel)
            filas.append(f'<li><a href="{rel}" download>{html.escape(d["prefijo"] + p.name)}</a> <span class="muted">({p.stat().st_size / 1024:,.0f} kB)</span></li>'.replace(",", " "))
    return f'<ul class="descargas">{"".join(filas)}</ul>' if filas else ""


def mapa_capas(cfg, dst):
    out = []
    for c in cfg.get("mapa", {}).get("capas", []):
        p = ROOT / c["archivo"]
        if not p.exists(): continue
        nombre = slug(c["nombre"]) + ".geojson"
        (dst / "mapa").mkdir(parents=True, exist_ok=True)
        d = json.loads(p.read_text())
        d["features"] = filtrar([f for f in d["features"] if f.get("geometry")], c.get("filtro"))
        txt = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        (dst / "mapa" / nombre).write_text(txt)
        out.append({**{k: v for k, v in c.items() if k not in ("archivo", "filtro")}, "url": f"mapa/{nombre}"})
    return out


# ---------------------------------------------------------------- plantilla
CSS = (ROOT / "web" / "estudios.css").read_text()
JS = (ROOT / "web" / "estudios.js").read_text()


def pagina(sid, cfg):
    dst = OUT / sid
    if dst.exists(): shutil.rmtree(dst)
    (dst / "figuras").mkdir(parents=True)
    figs, tabs, cuerpo = [0], [0], ""
    bases = [ROOT / b for b in cfg.get("bases", [])]
    for t in cfg["textos"]:
        p = ROOT / t["archivo"]
        if not p.exists():
            nombre = t.get("titulo") or pathlib.Path(t["archivo"]).stem.split("_", 1)[-1].replace("_", " ").capitalize()
            cuerpo += f'\n<h1>{t.get("n", "")}{"." if t.get("n") else ""} {html.escape(nombre)}</h1>\n<p class="pendiente">Sección en preparación.</p>\n'
            continue
        txt = renumerar(p.read_text(encoding="utf-8"), t.get("n"), cfg.get("refs_mapas", {}).get(t.get("refs")), t.get("titulo"))
        cuerpo += md_a_html(txt, [p.parent.parent, p.parent] + bases, dst / "figuras", figs, tabs)
    secs = secciones(cuerpo)
    capas = mapa_capas(cfg, dst)
    if cfg.get("vista3d"): dem_json(cfg, dst)
    lt = linea_tiempo(cfg); desc = descargas(cfg, dst)
    especiales = {"[[MAPA]]": '<div id="mapa" class="mapa"></div><p class="muted">Capas preliminares. Cotas del DSM ±2–4 m. Haz clic en un elemento para ver sus atributos.</p>',
                  "[[3D]]": '<div class="v3d"><button id="cargar3d" class="boton">Cargar vista 3D interactiva (≈4 MB)</button><div id="vista3d"></div></div>'
                            '<p class="muted">Arrastra para girar, rueda para acercar. Exageración vertical para que se lea el relieve.</p>',
                  "[[LINEA_TIEMPO]]": lt, "[[DESCARGAS]]": desc}
    toc, html_secs = [], []
    n = 0
    for sec_id, tit, body, subs in secs:
        for k, v in especiales.items():
            body = body.replace(f"<p>{k}</p>", v)
        if tit:
            n += 1 if not tit.lower().startswith(("resumen", "anexo", "fuentes")) else 0
            sub_toc = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in subs)
            toc.append(f'<li><a href="#{sec_id}">{tit}</a>{f"<ul>{sub_toc}</ul>" if sub_toc else ""}</li>')
        html_secs.append(f'<section id="{sec_id}" data-seccion="{sec_id}">{f"<h1>{tit}</h1>" if tit else ""}{body}'
                         f'<div class="com" data-seccion="{sec_id}"></div></section>')
    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(cfg["titulo_corto"])} · Estudio preliminar · SOS Galápagos</title>
<meta name="description" content="{html.escape(cfg["descripcion"])}">
<meta name="robots" content="index,follow"><link rel="icon" href="/favicon.ico">
{LEAFLET}<style>{CSS}</style></head>
<body data-pagina="{sid}">
<div class="preliminar-barra">ESTUDIO PRELIMINAR · NO ES UN DISEÑO DE INGENIERÍA NI UN MAPA OFICIAL DE AMENAZA · v{VERSION} · {HOY.strftime('%d-%m-%Y')}</div>
<header class="cab"><div class="cab-in"><a class="volver" href="/estudios/">← Estudios</a>
<p class="serie">{html.escape(cfg["serie"])}</p><h1 class="titulo">{html.escape(cfg["titulo"])}</h1><p class="sub">{html.escape(cfg["subtitulo"])}</p>
<div class="aviso"><b>Totalmente preliminar.</b> Análisis de reconocimiento hecho en pocos días con datos públicos: un modelo de superficie de 30 m (error vertical ±2–4 m), lluvia medida por una red de estaciones con cortes de transmisión y lluvia estimada por modelos. Lo elaboró un comité de agentes de inteligencia artificial (Claude, de Anthropic) para la coordinación de respuesta de USFQ Galápagos y <b>no lo han revisado profesionales habilitados</b>. Sirve para ordenar preguntas y prioridades, <b>no para decidir obras, permisos ni reasentamientos</b>. Las cifras cambiarán con datos de campo. Tus comentarios ayudan a corregirlo.</div></div></header>
<div class="cuerpo"><nav class="indice" aria-label="Índice"><button class="indice-boton" aria-expanded="false">Índice</button><ol>{"".join(toc)}</ol></nav>
<main>{"".join(html_secs)}
<section id="comentarios-generales" data-seccion="general"><h1>Comentarios generales</h1><p>¿Viviste la inundación, tienes datos (fotos con hora, marcas de agua, lluvia medida) o ves un error? Escríbelo aquí. Los comentarios son públicos.</p><div class="com abierto" data-seccion="general"></div></section>
</main></div>
<footer class="pie"><p>SOS Galápagos · Coordinación de respuesta USFQ Galápagos · Responsable: Julián Maya · <a href="/privacidad">Privacidad</a></p>
<p class="muted">Datos: Copernicus GLO-30, IGM, © colaboradores de OpenStreetMap (ODbL), INEC, SNGR, CGREG, FCD, red IERSE-WSN (Universidad del Azuay), Open-Meteo/ECMWF. Código y datos: geodatos/ en github.com/mayait/sosgalapagos-datos.</p></footer>
<div id="visor" class="visor" hidden><img alt=""><button aria-label="Cerrar">×</button></div>
<script>window.ESTUDIO={json.dumps({"pagina": sid, "capas": capas, "mapa": cfg.get("mapa", {}).get("vista", {}), "plotly": PLOTLY, "v3d": bool(cfg.get("vista3d"))}, ensure_ascii=False)};</script>
<script>{JS}</script></body></html>"""
    (dst / "index.html").write_text(doc, encoding="utf-8")
    print(f"  {sid}: {len(secs)} secciones, {figs[0]} figuras, {tabs[0]} tablas, {len(capas)} capas")


def portada():
    tarjetas = "".join(
        f'<a class="tarjeta" href="{sid}/"><span class="serie">{html.escape(c["serie"])}</span><h2>{html.escape(c["titulo"])}</h2><p>{html.escape(c["descripcion"])}</p><span class="mas">Ver estudio →</span></a>'
        for sid, c in ESTUDIOS.items())
    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estudios preliminares · SOS Galápagos</title><meta name="description" content="Estudios técnicos preliminares sobre las inundaciones de El Niño 2026 en Galápagos.">
<style>{CSS}</style></head><body data-pagina="estudios">
<div class="preliminar-barra">ESTUDIOS PRELIMINARES · EN REVISIÓN · {HOY.strftime('%d-%m-%Y')}</div>
<header class="cab"><div class="cab-in"><a class="volver" href="/">← SOS Galápagos</a><p class="serie">Emergencia El Niño 2026 · Galápagos</p><h1 class="titulo">Estudios técnicos preliminares</h1>
<p class="sub">Análisis topográficos e hidrológicos de reconocimiento sobre las inundaciones de octubre y noviembre de 2026, para ordenar preguntas, datos y prioridades.</p>
<div class="aviso"><b>Todo lo publicado aquí es preliminar.</b> Son análisis rápidos con datos públicos, hechos con asistencia de inteligencia artificial y sin revisión profesional. No sustituyen estudios de ingeniería ni mapas oficiales de amenaza. Cada estudio admite comentarios: si tienes datos o ves errores, escríbelos.</div></div></header>
<main class="portada">{tarjetas}</main>
<footer class="pie"><p>SOS Galápagos · Coordinación de respuesta USFQ Galápagos · Responsable: Julián Maya · <a href="/privacidad">Privacidad</a></p></footer></body></html>"""
    (OUT / "index.html").write_text(doc, encoding="utf-8")


def comprimir():
    for p in OUT.rglob("*"):
        if p.suffix in (".html", ".json", ".geojson", ".csv") and p.stat().st_size > 1024:
            with open(p, "rb") as a, gzip.open(str(p) + ".gz", "wb", 9) as b: b.write(a.read())


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for sid, cfg in ESTUDIOS.items():
        pagina(sid, cfg)
    portada(); comprimir()
    print("Sitio:", OUT)
