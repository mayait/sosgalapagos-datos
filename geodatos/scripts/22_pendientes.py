"""Página «Pendientes y preguntas abiertas» de cada isla, generada SOLO a partir de los issues de GitHub.

Los pendientes viven únicamente como issues de mayait/sosgalapagos-datos. Este script no mantiene ninguna lista a mano:
  1. --actualizar  baja los issues con `gh issue list --json` y los guarda en estudios/pendientes.json (caché versionada,
                   para que el sitio se genere sin red). Guarda título, estado, etiquetas, cuerpo, fechas y el NÚMERO de
                   comentarios (no su texto ni los autores).
  2. siempre       escribe estudios/pendientes/<isla>.md (una página por isla, que 19_estudios_web.py publica en
                   /estudios/<isla>/pendientes/), agrupada por tipo de pendiente (etiqueta) y por isla.

La isla de cada issue sale de sus etiquetas «santa-cruz» / «san-cristobal» («todas-las-islas» = comunes) o, si no las tiene,
de los topónimos de su título y su cuerpo; si no nombra ninguna isla, va en «comunes a las islas».
Los issues de «plataforma» (servidores, scripts) no se listan: son tareas internas, no vacíos de información; la página
enlaza a ellos en GitHub.

Uso (desde geodatos/):  .venv/bin/python -I scripts/22_pendientes.py [--actualizar]
No edites estudios/pendientes/*.md a mano: cambia el issue en GitHub y vuelve a correr este script (o scripts/flujo.py --red).
"""
import datetime, json, pathlib, re, subprocess, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = "mayait/sosgalapagos-datos"
URL_REPO = f"https://github.com/{REPO}"
CACHE = ROOT / "estudios/pendientes.json"
OUT = ROOT / "estudios/pendientes"
ESTUDIOS = json.loads((ROOT / "estudios/estudios.json").read_text())

ISLAS = {
    "santa-cruz": ("Santa Cruz", ["santa cruz", "puerto ayora", "la cascada", "bellavista", "aguacatal", "tomas de berlanga",
                                  "cerro crocker", "guayabillos", "santa rosa", "m0191", "escarpe", "baltra", "matazarnos"]),
    "san-cristobal": ("San Cristóbal", ["san cristobal", "baquerizo", "el progreso", "ugr", "manzanillo", "divino nino",
                                        "barrio frio", "floreana", "galapagos science center", "gsc", "playa mann"]),
}
GRUPOS = [
    ("datos-faltantes", "Datos que faltan", "Datos que no tenemos: hay que pedirlos a quien los tiene o levantarlos en campo."),
    ("mas-resolucion", "Datos con poco detalle", "Datos que existen, pero con un detalle que no alcanza para responder bien."),
    ("procesos", "Análisis y modelos por hacer", "Análisis que darán respuestas más firmes cuando lleguen los datos."),
    ("gobernanza", "Acuerdos y gestión de los datos", "Acuerdos, permisos y reglas para que los datos lleguen, se compartan y se mantengan."),
]
EXCLUIDAS = {"plataforma"}                       # tareas internas: solo se enlazan
PRIORIDAD = {"P1": "prioridad 1", "P2": "prioridad 2", "P3": "prioridad 3"}
# Lenguaje de la página (las reglas del sitio no admiten estas palabras fuera de la etiqueta «Datos preliminares»).
SUSTITUCIONES = [(r"\bpreliminares\b", "provisionales"), (r"\bpreliminar\b", "provisional"),
                 (r"\bPreliminares\b", "Provisionales"), (r"\bPreliminar\b", "Provisional"),
                 (r"\balbergues\b", "refugios"), (r"\balbergue\b", "refugio")]


def llano(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def actualizar():
    campos = "number,title,body,labels,state,url,createdAt,updatedAt,closedAt,comments"
    r = subprocess.run(["gh", "issue", "list", "-R", REPO, "--state", "all", "--limit", "1000", "--json", campos],
                       capture_output=True, text=True, check=True)
    issues = []
    for i in sorted(json.loads(r.stdout), key=lambda x: x["number"]):
        issues.append({"numero": i["number"], "titulo": i["title"], "estado": i["state"].lower(), "url": i["url"],
                       "etiquetas": sorted(l["name"] for l in i["labels"]), "cuerpo": i.get("body") or "",
                       "comentarios": len(i.get("comments") or []), "creado": i["createdAt"], "actualizado": i["updatedAt"],
                       "cerrado": i.get("closedAt") or None})
    previo = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    datos = {"_nota": f"Caché de los issues de {REPO} para el sitio /estudios (la escribe scripts/22_pendientes.py --actualizar). "
                      "No editar a mano: los pendientes se cambian en GitHub.",
             "repo": REPO, "descargado": previo.get("descargado"), "issues": issues}
    if previo.get("issues") != issues:                # la fecha solo cambia si cambian los issues (no dispara el flujo en vano)
        datos["descargado"] = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        CACHE.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  {CACHE.relative_to(ROOT)}: {len(issues)} issues (actualizada)")
    else:
        print(f"  {CACHE.relative_to(ROOT)}: {len(issues)} issues (sin cambios)")


def islas_de(issue):
    por_etiqueta = [k for k in ISLAS if k in issue["etiquetas"]]      # etiquetas «santa-cruz» / «san-cristobal», si existen
    if por_etiqueta or "todas-las-islas" in issue["etiquetas"]:
        return por_etiqueta
    t = llano(issue["titulo"] + " " + issue["cuerpo"])
    return [k for k, (_, claves) in ISLAS.items() if any(re.search(r"\b" + re.escape(c) + r"\b", t) for c in claves)]


def limpiar(txt):
    for a, b in SUSTITUCIONES:
        txt = re.sub(a, b, txt)
    return txt


def resumen(issue):
    """Cuerpo del issue en una o varias líneas cortas (sin la línea de prioridad ni la de migración)."""
    lineas = []
    tit = llano(re.sub(r"[*_`]", "", issue["titulo"]))[:30]
    for ln in issue["cuerpo"].replace("\r", "").split("\n"):
        s = ln.strip()
        if not s or s.startswith(("_Migrado", "**Prioridad:**", "<!--")) or re.match(r"^#{1,6}\s", s) or s.startswith("!["):
            continue
        m = re.match(r"^\*\*(Dato|Proceso|Tarea):\*\*\s*(.*)", s)
        if m and llano(re.sub(r"[*_`]", "", m.group(2))).startswith(tit[:20]):
            continue                                   # repite el título
        s = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "· ", s)   # listas del cuerpo → renglones (no anidar listas)
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"\]\((?!https?://|#|mailto:)(?:\./)?([^)\s]+)\)", lambda k: f"]({URL_REPO}/blob/main/{k.group(1)})", s)  # rutas del repo
        s = re.sub(r"(?<![\w/\[])#(\d+)\b", lambda k: f"[#{k.group(1)}]({URL_REPO}/issues/{k.group(1)})", s)
        lineas.append(s)
    txt = "  \n    ".join(lineas)
    if len(txt) > 900:
        txt = txt[:900].rsplit(" ", 1)[0] + " …"
    return limpiar(txt)


def item(issue):
    eti = issue["etiquetas"]
    meta = [f"#{issue['numero']}"] + [PRIORIDAD[p] for p in ("P1", "P2", "P3") if p in eti]
    if "en curso" in eti:
        meta.append("en curso")
    if issue["comentarios"]:
        meta.append(f"{issue['comentarios']} comentario{'s' if issue['comentarios'] > 1 else ''}")
    titulo = limpiar(issue["titulo"]).replace("[", "(").replace("]", ")")
    cuerpo = resumen(issue)
    return f"- **[{titulo}]({issue['url']})** ({' · '.join(meta)})" + (f"  \n    {cuerpo}" if cuerpo else "")


def orden(issue):
    eti = issue["etiquetas"]
    return (next((n for n, p in enumerate(("P1", "P2", "P3")) if p in eti), 3), issue["numero"])


def pagina(sid, datos):
    nombre = ISLAS[sid][0]
    abiertos = [i for i in datos["issues"] if i["estado"] == "open" and not EXCLUIDAS & set(i["etiquetas"])]
    propios = lambda i: sid in islas_de(i)
    comunes = lambda i: not islas_de(i)
    de_isla = [i for i in abiertos if propios(i) or comunes(i)]
    fecha = (datos.get("descargado") or "")[:10]
    md = [f"Intro: Lo que todavía no se sabe sobre las inundaciones en {nombre}: datos que faltan, datos con poco detalle y análisis "
          f"por hacer. Cada punto es un issue público en GitHub; si tienes información, compártela.",
          "", "# Cómo aportar", "",
          f"Esta página reúne los pendientes abiertos del proyecto que tocan a {nombre}: **{sum(map(propios, abiertos))} propios de la isla** "
          f"y **{sum(map(comunes, abiertos))} comunes a las islas**. Se arma sola a partir de los "
          f"[issues de GitHub]({URL_REPO}/issues) (última descarga: {fecha or 'sin fecha'}) y se ordena por prioridad: "
          "la prioridad 1 cambia decisiones de esta emergencia; la 2 mejora mucho el análisis; la 3 es deseable.", "",
          "Si tienes un dato que ayude (fotos o videos con fecha, hora y lugar, marcas de agua, lluvia medida, planos de obras, "
          "registros de daños), escríbelo en los comentarios de la sección que corresponda o en el issue de GitHub. "
          "Los comentarios son públicos: no pongas nombres, teléfonos ni datos de otras personas.", ""]
    for etiqueta, titulo, desc in GRUPOS:
        g = sorted((i for i in de_isla if etiqueta in i["etiquetas"]), key=orden)
        if not g:
            continue
        md += [f"# {titulo}", "", desc, ""]
        for sub, filtro in ((f"En {nombre}", propios), ("Comunes a las islas", comunes)):
            gg = [i for i in g if filtro(i)]
            if gg:
                md += [f"## {sub}", ""] + [item(i) for i in gg] + [""]
    sin_grupo = sorted((i for i in de_isla if not {e for e, _, _ in GRUPOS} & set(i["etiquetas"])), key=orden)
    if sin_grupo:
        md += ["# Otros pendientes", ""] + [item(i) for i in sin_grupo] + [""]
    cerrados = sorted((i for i in datos["issues"] if i["estado"] == "closed" and not EXCLUIDAS & set(i["etiquetas"])
                       and (propios(i) or comunes(i))), key=lambda i: i.get("cerrado") or "", reverse=True)
    if cerrados:
        md += ["# Resueltos", "", "Pendientes que ya se cerraron. El issue explica qué se hizo.", ""] + [item(i) for i in cerrados] + [""]
    n_plat = sum(1 for i in datos["issues"] if i["estado"] == "open" and "plataforma" in i["etiquetas"])
    md += ["# Tareas de la plataforma", "",
           f"Hay además {n_plat} tareas abiertas sobre los servidores, los mapas y los scripts. No son vacíos de información, "
           f"así que no se listan aquí: están en GitHub con la etiqueta [plataforma]({URL_REPO}/issues?q=is%3Aopen+label%3Aplataforma).", "",
           "<!-- Generado por scripts/22_pendientes.py a partir de estudios/pendientes.json. No editar a mano. -->", ""]
    return "\n".join(md)


def main():
    if "--actualizar" in sys.argv:
        actualizar()
    if not CACHE.exists():
        sys.exit(f"Falta {CACHE.relative_to(ROOT)}: corre «22_pendientes.py --actualizar» (necesita gh con sesión iniciada).")
    datos = json.loads(CACHE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for sid in ESTUDIOS:
        if sid not in ISLAS:
            continue
        p = OUT / f"{sid}.md"
        txt = pagina(sid, datos)
        if not p.exists() or p.read_text(encoding="utf-8") != txt:
            p.write_text(txt, encoding="utf-8")
            print(f"  {p.relative_to(ROOT)}: actualizada")
        else:
            print(f"  {p.relative_to(ROOT)}: sin cambios")


if __name__ == "__main__":
    main()
