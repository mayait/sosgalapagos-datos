# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Revisa los créditos de lo que se va a publicar en sosgalapagos.org/mapas/ (contrato de créditos v1, sección 6).

Lee publicar/mapas/ (de 10_publicar_web.py), geodatos/creditos.json y los manifiestos fuente. Sale con código 1 si:
  1. una capa no tiene «creditos», o un manifiesto usa un id o una receta que no existe en creditos.json;
  2. falta una cita obligatoria (también heredada) en la «atribucion» de una capa, en su GeoJSON o en el LEEME.txt de su
     descarga, o un zip no trae LEEME.txt y CITATION.cff;
  3. el nombre de una persona sin consentimiento aparece en algún archivo de publicar/mapas/ (también dentro de los zip);
  4. una «fuente» o una «atribucion» dice «no oficial», «estimación» o «experimental» (regla 3 de AGENTS.md: eso va en
     la descripción, si informa, o en el aviso general de la página).

Uso: .venv/bin/python -I scripts/revisar_creditos.py      (lo llama publicar_mapas.sh antes del rsync)
"""
import gzip, importlib.util, json, pathlib, re, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "publicar" / "mapas"
DESC = OUT / "descargas" / "completo"
DATOS = OUT / "datos" / "completo"
REGLA3 = re.compile(r"\bno\b[^.;:]{0,40}\boficial|estimaci[oó]n|experimental", re.I)
TEXTO = {".json", ".geojson", ".txt", ".cff", ".md", ".html", ".csv", ".dbf", ".js"}

errores = []


def error(msg): errores.append(msg)


def publicar_web():
    """Importa 10_publicar_web.py para usar sus constantes y su resolución de créditos (no corre main)."""
    spec = importlib.util.spec_from_file_location("publicar_web", ROOT / "scripts" / "10_publicar_web.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def listas_fuente(pw):
    """(dónde, lista de créditos) de cada capa de los manifiestos fuente y de las constantes de 10_publicar_web.py."""
    out = []
    for g in json.loads((ROOT / "scripts" / "capas.json").read_text())["grupos"]:
        for c in g["capas"]: out.append((f"capas.json «{c['id']}»", c.get("creditos")))
    for isla, ci in json.loads((ROOT / "scripts" / "capas_estudios.json").read_text()).items():
        if isla.startswith("_"): continue
        for c in ci.get("capas", {}).values(): out.append((f"capas_estudios.json «{c['id']}»", c.get("creditos")))
        for c in ci.get("extra", []): out.append((f"capas_estudios.json «{c['id']}»", c.get("creditos")))
    visor = json.loads((ROOT / "scripts" / "visor_mapas.json").read_text())
    for i, c in visor.get("capas", {}).items():
        if "creditos" in c: out.append((f"visor_mapas.json «{i}»", c["creditos"]))
    for fu in visor.get("fusionar", []):
        if "creditos" in fu: out.append((f"visor_mapas.json fusionar «{fu['id']}»", fu["creditos"]))
    for c in [pw.CAPA_DTM, pw.CAPA_ORTOFOTO, pw.CAPA_ZONA_FOTO, pw.CAPA_EDIFICIOS_FOTO, pw.CAPA_ESTIMACION, pw.CAPA_REPORTES,
              pw.CAPA_BUENAS, pw.CAPA_FLUJO] + pw.EXTRA["capas"]:
        out.append((f"10_publicar_web.py «{c['id']}»", c.get("creditos")))
    return out


def textos_publicados():
    """(ruta, texto) de cada archivo de texto de publicar/mapas/, también los de dentro de los zip."""
    for p in sorted(OUT.rglob("*")):
        if not p.is_file(): continue
        if p.suffix in TEXTO:
            yield str(p.relative_to(OUT)), p.read_bytes().decode("utf-8", "replace")
        elif p.suffix == ".gz" and pathlib.Path(p.stem).suffix in TEXTO:      # copias precomprimidas para Caddy
            yield str(p.relative_to(OUT)), gzip.decompress(p.read_bytes()).decode("utf-8", "replace")
        elif p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if pathlib.PurePath(n).suffix in TEXTO:
                        yield f"{p.relative_to(OUT)}:{n}", z.read(n).decode("utf-8", "replace")


def zip_de(c):
    if c.get("archivo"): return DESC / (pathlib.Path(c["archivo"]).stem + ".zip")
    if c.get("raster"): return DESC / f"raster_{c['raster']}.zip"
    if c.get("teselas") == "dtm_sgiar": return DESC / "dtm_sgiar_5m.zip"
    if c.get("teselas"): return DESC / f"{c['teselas']}.zip"


def main():
    if not (OUT / "capas.json").exists(): sys.exit("Falta publicar/mapas/capas.json. Corre antes: .venv/bin/python -I scripts/10_publicar_web.py")
    pw = publicar_web()
    try:
        reg = pw.cargar_creditos()
    except SystemExit as e:
        sys.exit(f"ERROR {e}")
    E = reg["entradas"]

    # 1. Ids y recetas de los manifiestos fuente
    for donde, lista in listas_fuente(pw):
        if lista is None: continue          # las capas que salen por otra vía (fusión, reemplazo) se revisan publicadas
        try: pw.resolver(lista, reg, donde)
        except SystemExit as e: error(str(e))

    # 1 y 2. Capas publicadas: créditos, atribución, GeoJSON y LEEME
    man = json.loads((OUT / "capas.json").read_text())
    n_capas, leemes = 0, {}
    for g in man["grupos"]:
        for c in g["capas"]:
            n_capas += 1
            donde = f"capa «{c['id']}»"
            cr = c.get("creditos")
            if not cr or not all(isinstance(x, dict) and x.get("id") for x in cr):
                error(f"{donde}: no tiene «creditos»"); continue
            ids = [x["id"] for x in cr]
            for i in ids:
                if i not in E: error(f"{donde}: el crédito «{i}» no existe en creditos.json")
            ids = [i for i in ids if i in E]
            for i in ids:
                for j in E[i].get("insumos", []):
                    if not j.startswith("@") and j not in ids: error(f"{donde}: falta «{j}», insumo de «{i}»")
            for k in ("atribucion", "licencia", "fuente"):
                if not c.get(k): error(f"{donde}: le falta «{k}»")
            oblig = [E[i]["cita_corta"] for i in ids if E[i].get("cita_obligatoria")]
            for t in oblig:
                if t not in c.get("atribucion", ""): error(f"{donde}: la atribución no trae la cita obligatoria «{t}»")
            for k in ("fuente", "atribucion"):
                m = REGLA3.search(c.get(k) or "")
                if m: error(f"{donde}: la {k} dice «{m.group(0)}» (regla 3: va en la descripción o en el aviso general)")
            if c.get("archivo"):
                gj = DATOS / c["archivo"]
                if not gj.exists(): error(f"{donde}: no se publica {c['archivo']}")
                else:
                    d = json.loads(gj.read_text())
                    for k in ("creditos", "atribucion", "licencia"):
                        if k not in d: error(f"{c['archivo']}: le falta el miembro «{k}»")
                    for t in oblig:
                        if t not in d.get("atribucion", ""): error(f"{c['archivo']}: la atribución no trae «{t}»")
            z = zip_de(c)
            if z and z.exists():
                if z not in leemes:
                    with zipfile.ZipFile(z) as zz: leemes[z] = zz.read("LEEME.txt").decode() if "LEEME.txt" in zz.namelist() else ""
                for t in oblig:
                    if t not in leemes[z]: error(f"{z.name}: el LEEME.txt no trae la cita obligatoria «{t}» ({donde})")

    # 2. Cada zip trae su LEEME.txt y su CITATION.cff
    for z in sorted(DESC.glob("*.zip")):
        with zipfile.ZipFile(z) as zz:
            nombres = {pathlib.PurePath(n).name for n in zz.namelist()}
        for n in ("LEEME.txt", "CITATION.cff"):
            if n not in nombres: error(f"{z.name}: le falta {n}")

    # /mapas/creditos.json: formato del contrato, sin rutas internas ni datos de consentimiento
    pub = OUT / "creditos.json"
    if not pub.exists(): error("falta publicar/mapas/creditos.json")
    else:
        d = json.loads(pub.read_text())
        for e in d.get("entradas", []):
            for k in ("ficha", "consentimiento", "personas", "institucion", "insumos"):
                if k in e: error(f"creditos.json publicado: «{e['id']}» trae «{k}»")
            src = E.get(e["id"])
            if src is None: error(f"creditos.json publicado: «{e['id']}» no existe en el registro")
            elif e.get("nombre") != pw.nombre_visible(src): error(f"creditos.json publicado: «{e['id']}» no muestra el nombre que toca")

    # 3. Nombres de personas sin consentimiento
    ocultos = sorted({e["nombre"] for e in E.values() if e["tipo"] == "persona" and e.get("nombre") and not pw.con_permiso(e)})
    n_arch = 0
    if ocultos:
        pats = [re.compile(re.escape(n), re.I) for n in ocultos]
        for ruta, txt in textos_publicados():
            n_arch += 1
            for n, p in zip(ocultos, pats):
                if p.search(txt): error(f"{ruta}: nombra a una persona sin consentimiento ({n[:1]}…)")

    for e in errores: print("ERROR", e)
    print(f"revisar_creditos: {n_capas} capas, {len(E)} entradas, {len(ocultos)} nombres protegidos"
          + (f" buscados en {n_arch} archivos" if ocultos else "") + f": {len(errores)} errores")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
