"""Arma la carpeta final `mapas-galapagos/` (junto a geodatos/) a partir de export/ y de la app:
datos listos, visor, capturas, código y parche para ResponseGrid, y el catálogo de capas generado.

Los documentos escritos a mano (00-LEEME.md, documentacion/02-05, para-responsegrid/*.md) no se tocan.
Uso: .venv/bin/python -I scripts/09_entregable.py   (después de 08)
"""
import json, os, pathlib, shutil, collections, datetime

G = pathlib.Path(__file__).resolve().parents[1]
ROOT = G.parent
# La app ResponseGrid vive en otro repositorio. Ruta configurable con SOSGALAPAGOS_APP.
APP = pathlib.Path(os.environ.get("SOSGALAPAGOS_APP", pathlib.Path.home() / "dev/RESPONSEGRID_GALAPAGOS/app")).expanduser()
if not (APP / "apps/web").is_dir():
    raise SystemExit(f"No encuentro la app ResponseGrid en {APP}. Define SOSGALAPAGOS_APP=/ruta/a/app")
E = ROOT / "mapas-galapagos"
SRC = G / "export" / "galapagos"

def fresh(d: pathlib.Path):
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)

for sub in ["documentacion", "para-responsegrid"]: (E / sub).mkdir(parents=True, exist_ok=True)

# 1) datos
fresh(E / "datos")
for p in SRC.rglob("*"):
    if p.is_file() and p.name != "_conteos.json":
        dst = E / "datos" / p.relative_to(SRC); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dst)

# 2) visor (lee ../datos/)
fresh(E / "visor")
html = (G / "visor/index.html").read_text().replace("const BASE_URL = '../export/galapagos/';", "const BASE_URL = '../datos/';")
assert "'../datos/'" in html
(E / "visor/index.html").write_text(html)
(E / "ver-mapa.sh").write_text('#!/bin/sh\n# Abre el visor en http://127.0.0.1:8765/visor/ (Ctrl+C para cerrar)\ncd "$(dirname "$0")"\n'
                               '( sleep 1; open "http://127.0.0.1:8765/visor/" 2>/dev/null || xdg-open "http://127.0.0.1:8765/visor/" ) &\n'
                               'exec python3 -m http.server 8765 --bind 127.0.0.1\n')
(E / "ver-mapa.sh").chmod(0o755)

# 3) capturas
fresh(E / "capturas")
for p in sorted((G / "docs/capturas").glob("*.jpg")): shutil.copy2(p, E / "capturas" / p.name)

# 4) código y parche para ResponseGrid
C = E / "para-responsegrid" / "codigo"; fresh(C)
FILES = ["apps/web/src/lib/map-layers/manifest.ts", "apps/web/src/lib/map-layers/manifest.test.ts",
         "apps/web/src/lib/map-layers/leaflet-layers.ts", "apps/web/src/components/organisms/emergency-layers.tsx",
         "docs/capas-emergencia.md"]
for f in FILES:
    dst = C / f; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(APP / f, dst)
shutil.copy2(G / "export/integracion/capas-por-emergencia.patch", E / "para-responsegrid/capas-por-emergencia.patch")
shutil.copy2(APP / "docs/capas-emergencia.md", E / "documentacion/04-especificacion-capas-json.md")

# 5) catálogo de capas (generado del manifiesto y de los archivos)
man = json.loads((SRC / "capas.json").read_text())
L = [f"# Catálogo de capas\n\n_Generado automáticamente el {datetime.date.today().isoformat()} a partir de `datos/capas.json` "
     "(script `geodatos/scripts/09_entregable.py`). No editar a mano._\n",
     "Las capas están en `datos/`. Todas usan GeoJSON EPSG:4326 con coordenadas a 5 decimales (≈ 1 m). Las que dicen «modelo» son "
     "cálculos propios sobre el DEM Copernicus GLO-30. Las demás vienen de fuentes oficiales o de OpenStreetMap. Ver `02-metodologia.md` y `03-fuentes-y-licencias.md`.\n"]
tot = 0
L.append("| Grupo | Capa | Archivo | Tipo | Elementos | Tamaño | Visible al abrir |\n|---|---|---|---|---:|---:|:---:|")
rows, det = [], []
for g in man["grupos"]:
    for c in g["capas"]:
        if c.get("archivo"):
            p = SRC / c["archivo"]; size = p.stat().st_size; tot += size
            feats = json.loads(p.read_text())["features"]
            if c.get("filtro"): feats = [f for f in feats if f["properties"].get(c["filtro"]["propiedad"]) in c["filtro"]["en"]]
            n = len(feats); arch = f"`{c['archivo']}`"; tam = f"{size / 1e6:.2f} MB" if size > 1e5 else f"{size / 1e3:.0f} kB"
        else:
            feats, n, arch, tam = [], "—", f"`raster/*_{c.get('raster')}.png`", "—"
        rows.append(f"| {g['titulo']} | {c['titulo']} | {arch} | {c['tipo']} | {n} | {tam} | {'sí' if c.get('visible') else ''} |")
        d = [f"### {c['titulo']}\n", f"- **Grupo:** {g['titulo']} · **id:** `{c['id']}` · **tipo:** {c['tipo']}"
             + (f" · **zoom mínimo:** {c['zoom_min']}" if c.get("zoom_min") else "")]
        if c.get("fuente"): d.append(f"- **Fuente:** {c['fuente']}")
        if c.get("descripcion"): d.append(f"- **Qué es:** {c['descripcion']}")
        if c.get("filtro"): d.append(f"- **Filtro:** `{c['filtro']['propiedad']}` ∈ {', '.join(c['filtro']['en'])}")
        cl = c.get("clasificar")
        if cl:
            items = cl.get("rangos") or list(cl.get("valores", {}).values()) + ([cl["otro"]] if cl.get("otro") else [])
            d.append(f"- **Clasificación por `{cl['propiedad']}`:** " + "; ".join(i.get("etiqueta", "") for i in items))
        if feats:
            keys = collections.OrderedDict()
            for f in feats[:3000]:
                for k, v in f["properties"].items():
                    if v not in (None, "") and k not in keys: keys[k] = v
            d.append("- **Campos:** " + ", ".join(f"`{k}` (ej.: {str(v)[:40]})" for k, v in keys.items()))
        det.append("\n".join(d) + "\n")
L += rows
L.append(f"\n**Total del paquete:** {sum(p.stat().st_size for p in SRC.rglob('*') if p.is_file()) / 1e6:.1f} MB "
         f"(GeoJSON {tot / 1e6:.1f} MB; resto: raster y JSON).\n")
L.append("## Detalle por capa\n")
L += det
usados = {c.get("archivo") for g in man["grupos"] for c in g["capas"]}
extra = sorted(p.name for p in SRC.glob("*.geojson") if p.name not in usados and p.name != "area_interes.geojson")
L.append("## Otros archivos\n\n" + "".join(f"- `{x}`: se publica, pero no está activada en el manifiesto (se puede añadir como capa).\n" for x in extra) + "- `capas.json`: manifiesto (grupos, estilos, leyendas y encuadres). Especificación en `04-especificacion-capas-json.md`.\n"
         "- `resumen_exposicion.json`: edificios y población expuestos por isla.\n- `raster/limites.json`: encuadre de cada PNG.\n"
         "- `area_interes.geojson`: área de interés (zona agrícola y urbana completas, cuencas que drenan a poblados y márgenes de 500 m alrededor de las zonas pobladas y de 300 m alrededor de las vías).\n")
(E / "documentacion/01-catalogo-de-capas.md").write_text("\n".join(L))
print("Entregable listo en", E)
for p in sorted(E.rglob("*")):
    if p.is_file() and "datos" not in p.parts and "codigo" not in p.parts: print("  ", p.relative_to(E))
