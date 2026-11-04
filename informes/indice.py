#!/usr/bin/env python3
"""Genera la página pública https://sosgalapagos.org/estudios/: solo la lista de informes técnicos, con enlaces a sus PDF en el
repositorio de GitHub (rama main). No copia los PDF al servidor: la página enlaza directamente al repositorio.

Lee de cada informes/<carpeta>/informe.tex los campos \\numero{} y \\titulocita{} (o \\title{}), y solo incluye los informes
que tienen informe.pdf. Escribe informes/web/index.html (no versionado). Uso, desde la raíz del repositorio:
    python3 -I informes/indice.py
"""
import html
import re
import subprocess
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "web" / "index.html"
REPO = "https://github.com/mayait/sosgalapagos-datos"
RAMA = "main"


def campo(tex: str, nombre: str) -> str:
    m = re.search(r"\\" + nombre + r"\{((?:[^{}]|\{[^{}]*\})*)\}", tex)
    return m.group(1) if m else ""


def limpiar(s: str) -> str:
    s = s.replace("\\\\", " ").replace("~", " ").replace("--", "–")
    s = re.sub(r"\\enquote\{([^{}]*)\}", r"«\1»", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?\{([^{}]*)\}", r"\2", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def paginas(pdf: Path) -> str:
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=20).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        return f"{m.group(1)} págs." if m else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def informes():
    filas = []
    for tex_path in sorted(AQUI.glob("*/informe.tex")):
        carpeta = tex_path.parent
        pdf = carpeta / "informe.pdf"
        if not pdf.exists():
            continue
        tex = tex_path.read_text(encoding="utf-8")
        numero = limpiar(campo(tex, "numero")) or carpeta.name[:7]
        titulo = limpiar(campo(tex, "titulocita") or campo(tex, "title"))
        ruta = f"informes/{carpeta.name}/informe.pdf"
        filas.append({
            "numero": numero, "titulo": titulo, "paginas": paginas(pdf),
            "ver": f"{REPO}/blob/{RAMA}/{ruta}", "bajar": f"{REPO}/raw/{RAMA}/{ruta}",
        })
    return sorted(filas, key=lambda f: f["numero"])


PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Informes técnicos · SOS Galápagos</title>
<meta name="description" content="Informes técnicos de SOS Galápagos (Universidad San Francisco de Quito) sobre las inundaciones de 2026 en Santa Cruz y San Cristóbal: borradores para discusión en PDF.">
<style>
:root {{ --tinta:#151515; --suave:#5a5a5a; --linea:#d9d9d9; --rojo:#b3121b; --fondo:#ffffff; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--fondo); color:var(--tinta); font:17px/1.55 Charter,"Bitstream Charter",Georgia,serif; }}
main {{ max-width:780px; margin:0 auto; padding:40px 16px 64px; }}
.serie {{ font:600 12px/1.4 system-ui,sans-serif; letter-spacing:.08em; text-transform:uppercase; color:var(--rojo); }}
h1 {{ font-size:30px; line-height:1.2; margin:.3em 0 .4em; }}
p {{ margin:.5em 0; }}
.aviso {{ border-top:1px solid var(--tinta); border-bottom:1px solid var(--tinta); padding:10px 2px; font-size:15px; margin:22px 0 28px; }}
ol {{ list-style:none; padding:0; margin:0; border-top:1px solid var(--linea); }}
li {{ display:grid; grid-template-columns:84px 1fr; gap:4px 16px; padding:14px 0; border-bottom:1px solid var(--linea); }}
.num {{ font:600 14px/1.6 system-ui,sans-serif; color:var(--suave); }}
.tit a {{ color:var(--tinta); text-decoration:none; font-weight:600; }}
.tit a:hover {{ color:var(--rojo); text-decoration:underline; }}
.meta {{ grid-column:2; font:14px/1.4 system-ui,sans-serif; color:var(--suave); }}
.meta a {{ color:var(--suave); }}
footer {{ margin-top:32px; font-size:14px; color:var(--suave); }}
footer a {{ color:var(--suave); }}
@media (max-width:560px) {{ li {{ grid-template-columns:1fr; }} .meta {{ grid-column:1; }} h1 {{ font-size:25px; }} }}
</style>
</head>
<body>
<main>
<div class="serie">SOS Galápagos · Universidad San Francisco de Quito (USFQ)</div>
<h1>Informes técnicos</h1>
<p>Borradores para discusión sobre las inundaciones de octubre de 2026 en Santa Cruz y San Cristóbal (Galápagos): datos, modelos y métodos. Cada enlace abre el PDF en el repositorio público del proyecto.</p>
<div class="aviso"><strong>Modelos propios, no datos oficiales.</strong> Los informes describen estimaciones preliminares preparadas con asistencia de agentes de inteligencia artificial, sin visitas de campo ni revisión profesional externa. No sirven para delimitar zonas, normar ni diseñar obras, y no expresan una posición institucional de la USFQ.</div>
<ol>
{filas}
</ol>
<footer>
<p>Responsable: Julián Maya, Universidad San Francisco de Quito (USFQ) · <a href="mailto:jamaya@usfq.edu.ec">jamaya@usfq.edu.ec</a></p>
<p>© {anio} Universidad San Francisco de Quito (USFQ). Textos, figuras y modelos propios bajo <a href="https://creativecommons.org/licenses/by/4.0/deed.es">CC BY 4.0</a>: toda reutilización debe citar el informe correspondiente (la cita está al pie de la primera página de cada PDF). Los datos de terceros conservan sus licencias (<a href="{repo}/blob/{rama}/LICENCIA-DATOS.md">LICENCIA-DATOS.md</a>).</p>
<p>Fuentes, scripts y datos: <a href="{repo}">github.com/mayait/sosgalapagos-datos</a> · Actualizado: {hoy}</p>
</footer>
</main>
</body>
</html>
"""

FILA = """<li><span class="num">{numero}</span><span class="tit"><a href="{ver}">{titulo}</a></span>
<span class="meta">PDF{sep}{paginas} · <a href="{ver}">ver en el repositorio</a> · <a href="{bajar}">descargar</a></span></li>"""


def main():
    filas = informes()
    if not filas:
        raise SystemExit("No hay informes con PDF en informes/*/informe.pdf")
    cuerpo = "\n".join(FILA.format(numero=html.escape(f["numero"]), titulo=html.escape(f["titulo"]), ver=f["ver"],
                                   bajar=f["bajar"], paginas=html.escape(f["paginas"]), sep=" · " if f["paginas"] else "")
                       for f in filas)
    hoy = date.today()
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(PLANTILLA.format(filas=cuerpo, anio=hoy.year, repo=REPO, rama=RAMA, hoy=hoy.strftime("%d-%m-%Y")),
                      encoding="utf-8")
    print(f"{SALIDA.relative_to(AQUI.parent)}: {len(filas)} informes")


if __name__ == "__main__":
    main()
