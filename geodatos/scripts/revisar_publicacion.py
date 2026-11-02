"""Checklist automático antes de publicar sosgalapagos.org/estudios/ (ver estudios/PUBLICAR.md).

Revisa el sitio ya generado (publicar/estudios, de 19_estudios_web.py) y las fuentes versionadas. Sale con código 1 si
algo no pasa (ERROR); los AVISOS no detienen la publicación, pero hay que leerlos.

  1. frescura     el sitio es más nuevo que sus fuentes (textos, estudios.json, figuras, pendientes)
  2. enlaces      enlaces internos, anclas, imágenes, capas del mapa y vista 3D sin roturas; sin «Figura pendiente» ni
                  «Página en preparación»
  3. secretos     ni URL ni endpoints de IERSE, GSC, INAMHI, WeatherLink o Tempest, ni sus ids o tokens (se leen de
                  clima/privado/ para buscarlos; nunca se imprimen)
  4. palabras     «albergue» (se dice «refugio»); «preliminar» fuera de la etiqueta «Datos preliminares»
  5. voz          recomendaciones en voz de la universidad («recomendamos», «la USFQ propone»…)
  6. personales   correos, teléfonos, cédulas y campos de contacto en páginas y descargas
  7. pie          «Responsable: Julián Maya» y la etiqueta en cada página
  8. cifras       las cifras clave de los textos coinciden con los datos (estudios/cifras_clave.json)
  9. pendientes   la caché de issues y las páginas de pendientes están al día entre sí
 10. git          cambios sin commit en lo que se publica (aviso; error con --estricto)

Uso (desde geodatos/):
  .venv/bin/python -I scripts/revisar_publicacion.py              checklist local (lo llama publicar_estudios.sh antes del rsync)
  .venv/bin/python -I scripts/revisar_publicacion.py --externos   además prueba los enlaces externos (red)
  .venv/bin/python -I scripts/revisar_publicacion.py --produccion compara producción con publicar/estudios (después de publicar)
"""
import argparse, csv, hashlib, html as H, importlib.util, json, os, pathlib, re, subprocess, sys, unicodedata, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "publicar" / "estudios"
EST = ROOT / "estudios"
PRIVADO = ROOT.parent / "clima" / "privado"
PROD = "https://sosgalapagos.org"
TEXTO = {".html", ".json", ".geojson", ".csv", ".js", ".css", ".txt", ".md", ".py", ".sh", ".toml"}
SENSIBLES = ("IERSE", "GSC", "INAMHI", "WEATHERLINK", "TEMPEST")
FUERA_ESTUDIOS_OK = ("/", "/privacidad", "/favicon.ico", "/mapas/", "/clima/")

errores, avisos = [], []


def err(c, m): errores.append((c, m))
def aviso(c, m): avisos.append((c, m))
def rel(p): return os.path.relpath(p, ROOT)


def paginas():
    return sorted(OUT.rglob("index.html"))


def url_de(p):
    """Ruta pública de una página: publicar/estudios/a/b/index.html → /estudios/a/b/."""
    r = p.parent.relative_to(OUT).as_posix()
    return "/estudios/" + ("" if r == "." else r + "/")


def visible(doc):
    """Texto que ve el lector: título, descripción y cuerpo sin scripts, estilos ni comentarios."""
    t = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", " ", doc, flags=re.S)
    meta = " ".join(re.findall(r'<meta name="description" content="([^"]*)"', doc))
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", H.unescape(meta + " " + t))


def contexto(t, m, ancho=60):
    return "…" + t[max(m.start() - ancho, 0):m.end() + ancho].strip() + "…"


# ------------------------------------------------------------------ 1. frescura
def frescura():
    idx = OUT / "index.html"
    if not idx.exists():
        err("frescura", "no existe publicar/estudios: corre scripts/19_estudios_web.py (o scripts/flujo.py)"); return False
    t = idx.stat().st_mtime
    fuentes = [EST / "estudios.json", *EST.glob("*/texto/*.md"), *EST.glob("pendientes/*.md"), *EST.glob("*/figuras/*"),
               ROOT / "web/estudios.css", ROOT / "web/estudios.js", ROOT / "scripts/19_estudios_web.py"]
    nuevas = [rel(f) for f in fuentes if f.exists() and f.stat().st_mtime > t]
    if nuevas:
        err("frescura", f"el sitio es más viejo que {len(nuevas)} fuente(s) ({', '.join(nuevas[:3])}…): regenera con scripts/flujo.py")
    return True


# ------------------------------------------------------------------ 2. enlaces
def ids_de(p, cache={}):
    if p not in cache:
        cache[p] = set(re.findall(r'\bid="([^"]+)"', p.read_text(encoding="utf-8"))) if p.suffix == ".html" else set()
    return cache[p]


def destino(base_url, enlace):
    u = urllib.parse.urljoin(base_url, enlace)
    pu = urllib.parse.urlparse(u)
    ruta = urllib.parse.unquote(pu.path)
    return ruta, pu.fragment


def enlaces(externos_ok):
    externos = set()
    n = 0
    for p in paginas():
        doc = p.read_text(encoding="utf-8")
        base = url_de(p)
        refs = re.findall(r'(?:href|src)="([^"]+)"', doc)
        m = re.search(r"window\.ESTUDIO=(\{.*?\});</script>", doc)
        if m:
            cfg = json.loads(m.group(1))
            refs += [c["url"] for c in cfg.get("capas", [])]
            if cfg.get("v3d"):
                refs.append("vista3d.json")
        for r in refs:
            n += 1
            r = H.unescape(r)
            if r.startswith(("mailto:", "data:", "javascript:")):
                continue
            if r.startswith(("http://", "https://")):
                if not r.startswith(PROD + "/estudios/"):
                    externos.add(r); continue
                r = r[len(PROD):]
            if r.startswith("#"):
                if r[1:] and r[1:] not in ids_de(p):
                    err("enlaces", f"{rel(p)}: ancla inexistente {r}")
                continue
            ruta, frag = destino(base, r)
            if not ruta.startswith("/estudios/"):
                if not any(ruta == x or (x.endswith("/") and x != "/" and ruta.startswith(x)) for x in FUERA_ESTUDIOS_OK):
                    aviso("enlaces", f"{rel(p)}: enlace fuera de /estudios que no se puede comprobar en local: {r}")
                continue
            if ruta.startswith("/estudios/api"):
                continue
            f = OUT / ruta[len("/estudios/"):]
            if ruta.endswith("/"):
                f = f / "index.html"
            if not f.exists():
                err("enlaces", f"{rel(p)}: enlace roto {r}")
            elif frag and frag not in ids_de(f):
                err("enlaces", f"{rel(p)}: ancla inexistente {r}")
        if "[Figura pendiente:" in doc:
            err("enlaces", f"{rel(p)}: hay figuras que faltan («Figura pendiente»)")
        if "Página en preparación" in doc:
            err("enlaces", f"{rel(p)}: un texto de estudios.json no existe («Página en preparación»)")
    print(f"  enlaces: {n} referencias en {len(paginas())} páginas; {len(externos)} externas")
    if externos_ok:
        for u in sorted(externos):
            try:
                rq = urllib.request.Request(u, method="GET", headers={"User-Agent": "sosgalapagos-revision/1.0"})
                with urllib.request.urlopen(rq, timeout=20) as r:
                    if r.status >= 400:
                        aviso("enlaces", f"externo {r.status}: {u}")
            except Exception as e:
                aviso("enlaces", f"externo no responde ({type(e).__name__}): {u}")


# ------------------------------------------------------------------ 3. secretos
def secretos():
    """[(nombre, valor, sensible, solo_numero)] leídos de clima/privado (si existe en esta máquina)."""
    out = []
    env = PRIVADO / "fuentes.env"
    if env.exists():
        for ln in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)", ln)
            if not m or not m.group(2).strip():
                continue
            k, v = m.group(1), m.group(2).strip().strip("'\"")
            sens = any(s in k for s in SENSIBLES)
            if v.startswith("http"):
                pu = urllib.parse.urlparse(v)
                out.append((k, v.rstrip("/"), sens, False))
                if pu.hostname and not pu.hostname.endswith(("open-meteo.com",)):
                    out.append((k + " (servidor)", pu.hostname, sens, False))
            elif re.match(r"(wss?|ftp)://", v):
                out.append((k, v.rstrip("/"), sens, False))
                out.append((k + " (servidor)", urllib.parse.urlparse(v).hostname, sens, False))
            else:
                for parte in re.split(r"[,; ]+", v):
                    for x in re.split(r"[:|=]", parte):
                        if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", x) or len(x) >= 20:
                            out.append((k, x, sens, False))
                        elif x.isdigit() and len(x) >= 5:
                            out.append((k, x, sens, True))
    tok = PRIVADO / "token_investigadores.txt"
    if tok.exists() and tok.read_text().strip():
        out.append(("token_investigadores", tok.read_text().strip(), True, False))
    return out


GENERICO = re.compile(r"(?:https?|wss?)://[^\s\"'<>)]*(?:ierse|uazuay|weatherlink|weatherflow|tempestwx)[^\s\"'<>)]*", re.I)


def buscar_secretos():
    sec = secretos()
    if not sec:
        aviso("secretos", "no se encontró clima/privado/fuentes.env: solo se buscan patrones genéricos (IERSE, WeatherLink, Tempest)")
    publicados = [p for p in OUT.rglob("*") if p.is_file() and p.suffix in TEXTO]
    fuentes = ([p for p in EST.rglob("*") if p.is_file() and p.suffix in TEXTO]
               + [p for p in (ROOT / "scripts").glob("*") if p.suffix in TEXTO] + list((ROOT / "web").glob("*")) + [ROOT / "flujo.toml"])
    for grupo, archivos in (("publicado", publicados), ("versionado", fuentes)):
        for p in archivos:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except (IsADirectoryError, FileNotFoundError):
                continue
            for m in GENERICO.finditer(t):
                err("secretos", f"{rel(p)}: URL de una fuente meteorológica ({m.group(0)[:12]}…)")
            for k, v, sens, num in sec:
                hay = re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d.])", t) if num else (v in t)
                if hay:
                    msg = f"{rel(p)}: contiene el valor de {k} de clima/privado/"
                    (err if (grupo == "publicado" or sens) else aviso)("secretos", msg)


# ------------------------------------------------------------------ 4–7. palabras, voz, datos personales, pie
VOZ = [r"\b(recomendamos|sugerimos|proponemos|aconsejamos|exhortamos|instamos)\b", r"\bse recomienda\b",
       r"\b(USFQ|[Uu]niversidad|Galapagos Science Center)\b[^.]{0,30}\b(recomienda|propone|sugiere|aconseja|exige|insta)\b",
       r"\brecomendaci[oó]n(es)? (de la USFQ|de la universidad|del estudio|de este estudio)\b", r"\bnuestras? recomendaci"]
BUZONES_INSTITUCIONALES = {"datazone", "info", "informacion", "contacto", "datos", "comunicacion", "secretaria", "prensa"}
CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TELEFONO = re.compile(r"(?<![\d.,/-])(?:\+?593[\s-]?|0)(?:9\d{8}|5[\s-]?2\d{6})(?![\d.,])")
CEDULA = re.compile(r"(?<![\d.,/-])(?:0[1-9]|1\d|2[0-4]|30)\d{8}(?![\d.,])")
CLAVE_PERSONAL = re.compile(r"(tel[eé]fono|celular|c[eé]dula|correo|e-?mail|whatsapp|contacto|propietari|representante|nombre_(afectad|persona|jefe))", re.I)


def cedula_valida(c):
    d = [int(x) for x in c]
    if d[2] > 5:
        return False
    s = sum((x * 2 - 9 if x * 2 > 9 else x * 2) if i % 2 == 0 else x for i, x in enumerate(d[:9]))
    return (10 - s % 10) % 10 == d[9]


def revisar_paginas():
    for p in paginas():
        doc = p.read_text(encoding="utf-8")
        sin_etq = re.sub(r'<p class="etiqueta">Datos preliminares · [^<]*</p>', " ", doc)
        t = visible(sin_etq)
        for m in re.finditer(r"albergue", t, re.I):
            err("palabras", f"{rel(p)}: «albergue» (se dice «refugio»): {contexto(t, m)}")
        for m in re.finditer(r"preliminar", t, re.I):
            err("palabras", f"{rel(p)}: «preliminar» fuera de la etiqueta: {contexto(t, m)}")
        for rx in VOZ:
            for m in re.finditer(rx, t, re.I):
                err("voz", f"{rel(p)}: recomendación en voz de la universidad: {contexto(t, m)}")
        for m in CORREO.finditer(t):
            institucional = m.group(0).split("@")[0].lower() in BUZONES_INSTITUCIONALES
            (aviso if institucional else err)("personales", f"{rel(p)}: correo electrónico visible"
                                              f"{' (buzón institucional)' if institucional else ''}: {contexto(t, m, 30)}")
        for m in TELEFONO.finditer(t):
            err("personales", f"{rel(p)}: posible teléfono: {contexto(t, m, 30)}")
        for m in CEDULA.finditer(t):
            if cedula_valida(m.group(0)):
                err("personales", f"{rel(p)}: posible cédula: {contexto(t, m, 30)}")
        if "Responsable: Julián Maya" not in doc:
            err("pie", f"{rel(p)}: falta «Responsable: Julián Maya» en el pie")
        if 'class="etiqueta">Datos preliminares' not in doc:
            aviso("pie", f"{rel(p)}: falta la etiqueta «Datos preliminares»")
    # fuentes de texto (para que no vuelva a entrar en la próxima generación)
    for p in [EST / "estudios.json", *EST.glob("*/texto/*.md"), *EST.glob("pendientes/*.md")]:
        t = p.read_text(encoding="utf-8")
        for m in re.finditer(r"albergue", t, re.I):
            err("palabras", f"{rel(p)}: «albergue» (se dice «refugio»): {contexto(t, m, 40)}")
    # descargas y capas del mapa: campos y valores personales
    for p in list(OUT.rglob("*.geojson")) + list(OUT.rglob("*.csv")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if p.suffix == ".csv":
            claves = set(next(csv.reader([t.split("\n", 1)[0]]), []))
        else:
            try:
                claves = {k for f in json.loads(t).get("features", []) for k in (f.get("properties") or {})}
            except Exception:
                claves = set()
        malas = sorted(k for k in claves if CLAVE_PERSONAL.search(k))
        if malas:
            err("personales", f"{rel(p)}: campos con datos de contacto: {', '.join(malas)}")
        for m in CORREO.finditer(t):
            err("personales", f"{rel(p)}: correo electrónico: {m.group(0)[:3]}…")
            break
        for m in TELEFONO.finditer(t):
            aviso("personales", f"{rel(p)}: número con forma de teléfono (revisar): {contexto(t, m, 25)}")
            break
        if re.search(r"albergue", t, re.I):
            aviso("palabras", f"{rel(p)}: la palabra «albergue» aparece en los datos descargables (issue #44)")


# ------------------------------------------------------------------ 8. cifras
NUM = r"(?<![\d,.])(\d{1,3}(?:[   ]\d{3})+(?:,\d+)?|\d+(?:,\d+)?)"


def valor_dato(d):
    if "json" in d:
        x = json.loads((ROOT / d["json"]).read_text())
        for k in d["clave"].split("."):
            x = x[k]
        return float(x)
    if "geojson" in d:
        fs = json.loads((ROOT / d["geojson"]).read_text())["features"]
        if "filtro" in d:
            fs = [f for f in fs if str(f["properties"].get(d["filtro"]["campo"])) in d["filtro"]["valores"]]
        if "excluir" in d:
            fs = [f for f in fs if str(f["properties"].get(d["excluir"]["campo"])) not in d["excluir"]["valores"]]
        return float(len(fs))
    if "csv" in d:
        for r in csv.DictReader(open(ROOT / d["csv"], encoding="utf-8")):
            if all(r.get(k) == v for k, v in d["fila"].items()):
                return float(r[d["columna"]])
        raise KeyError(f"fila {d['fila']} no está en {d['csv']}")
    raise ValueError("tipo de dato desconocido")


def leer_texto(ref):
    if ref.startswith("estudios.json:"):
        sid, campo = ref.split(":", 1)[1].split(".", 1)
        return json.loads((EST / "estudios.json").read_text())[sid][campo]
    return (ROOT / ref).read_text(encoding="utf-8")


def cifras():
    conf = EST / "cifras_clave.json"
    if not conf.exists():
        aviso("cifras", "no hay estudios/cifras_clave.json"); return
    ok = 0
    for c in json.loads(conf.read_text())["cifras"]:
        try:
            v = round(valor_dato(c["dato"]), c.get("decimales", 0))
        except Exception as e:
            err("cifras", f"{c['id']}: no se pudo leer el dato ({type(e).__name__}: {e})"); continue
        rx = re.compile(c["patron"].replace("{n}", NUM))
        for ref in c["textos"]:
            t = leer_texto(ref)
            ms = list(rx.finditer(t))
            if not ms:
                aviso("cifras", f"{c['id']}: el patrón ya no aparece en {ref} (¿se reescribió el texto? actualiza cifras_clave.json)"); continue
            for m in ms:
                num = next(g for g in m.groups() if g)
                n = float(re.sub(r"[   ]", "", num).replace(",", "."))
                if abs(n - v) > 10 ** -(c.get("decimales", 0)) / 2 + 1e-9:
                    fmt = f"{v:,.{c.get('decimales', 0)}f}".replace(",", " ").replace(".", ",")
                    err("cifras", f"{c['id']} ({c['descripcion']}): {ref} dice {num}, los datos dan {fmt}")
                else:
                    ok += 1
    print(f"  cifras: {ok} coincidencias comprobadas")


# ------------------------------------------------------------------ 9. pendientes
def pendientes():
    cache = EST / "pendientes.json"
    if not cache.exists():
        err("pendientes", "falta estudios/pendientes.json: corre scripts/22_pendientes.py --actualizar"); return
    import datetime
    d = json.loads(cache.read_text())
    if d.get("descargado"):
        dias = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(d["descargado"])).days
        if dias > 3:
            aviso("pendientes", f"la caché de issues tiene {dias} días: «flujo.py --red» o «22_pendientes.py --actualizar»")
    spec = importlib.util.spec_from_file_location("pendientes22", ROOT / "scripts/22_pendientes.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for sid in json.loads((EST / "estudios.json").read_text()):
        if sid in mod.ISLAS:
            p = EST / "pendientes" / f"{sid}.md"
            if not p.exists() or p.read_text(encoding="utf-8") != mod.pagina(sid, d):
                err("pendientes", f"{rel(p)} no corresponde a la caché de issues: corre scripts/22_pendientes.py")


# ------------------------------------------------------------------ 10. git
def git(estricto):
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "estudios", "scripts/19_estudios_web.py", "web", "flujo.toml"],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    except Exception:
        return
    cambios = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if cambios:
        (err if estricto else aviso)("git", f"{len(cambios)} archivo(s) de lo que se publica sin commit (p. ej. {cambios[0][3:]}): "
                                     "lo publicado debe corresponder a un commit")


# ------------------------------------------------------------------ producción
def produccion():
    """Compara cada página de publicar/estudios con la que sirve producción."""
    iguales, distintas, fallos = 0, [], []
    for p in paginas():
        url = PROD + url_de(p)
        try:
            rq = urllib.request.Request(url, headers={"User-Agent": "sosgalapagos-revision/1.0", "Accept-Encoding": "identity"})
            with urllib.request.urlopen(rq, timeout=30) as r:
                cuerpo = r.read()
        except Exception as e:
            fallos.append(f"{url} ({e})"); continue
        cuerpo = re.sub(rb"<script[^>]*cloudflareinsights[^>]*>\s*</script>\s*(?=</body>)", b"", cuerpo)   # baliza que inyecta Cloudflare
        if hashlib.sha256(cuerpo).digest() == hashlib.sha256(p.read_bytes()).digest():
            iguales += 1
        else:
            distintas.append(url)
    try:
        with urllib.request.urlopen(f"{PROD}/estudios/version.txt", timeout=20) as r:
            print("  versión publicada:", r.read().decode(errors="replace").strip().replace("\n", " · "))
    except Exception:
        pass
    print(f"  producción: {iguales} páginas iguales a publicar/estudios, {len(distintas)} distintas, {len(fallos)} sin respuesta")
    for u in distintas[:20]:
        print("   distinta:", u)
    for u in fallos[:20]:
        print("   sin respuesta:", u)
    return 1 if (distintas or fallos) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--externos", action="store_true", help="prueba también los enlaces externos (red)")
    ap.add_argument("--estricto", action="store_true", help="los cambios sin commit cuentan como error")
    ap.add_argument("--produccion", action="store_true", help="compara producción con publicar/estudios y termina")
    a = ap.parse_args()
    if a.produccion:
        sys.exit(produccion())
    print("Revisión de publicar/estudios")
    if frescura():
        enlaces(a.externos)
        revisar_paginas()
    buscar_secretos()
    cifras()
    pendientes()
    git(a.estricto)
    for nivel, lista in (("AVISO", avisos), ("ERROR", errores)):
        por = {}
        for c, m in lista:
            por.setdefault(c, []).append(m)
        for c, ms in por.items():
            for m in ms[:15]:
                print(f"  {nivel} [{c}] {m}")
            if len(ms) > 15:
                print(f"  {nivel} [{c}] … y {len(ms) - 15} más")
    print(f"\n{len(errores)} error(es), {len(avisos)} aviso(s).", "NO PUBLICAR." if errores else "Se puede publicar.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
