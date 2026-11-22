#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
"""Paso 3 · Publicar los reportes curados como capa de mapa con fotos.

Lee `eventos/<evento>/reportes.json` (curado a mano), lo valida y produce:

- `eventos/<evento>/reportes.geojson` (GENERADO, versionado): solo reportes con coordenadas;
- `publicar/<evento>/` (ignorado por git; es lo que se sirve): `index.html`, `evento.json`,
  `reportes.geojson`, `fotos/` (máx. 1280 px) y `mini/` (máx. 360 px), todas sin EXIF.

Nunca copia mensajes ni nombres: la validación rechaza teléfonos y nombres de quienes escriben.

    geodatos/.venv/bin/python -I reportes/scripts/03_publicar.py [--evento 2026-11-21]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402

TIPOS = {"inundacion", "desbordamiento", "personas_atrapadas", "via_cortada", "rescate", "refugio", "necesidad"}
PRECISIONES = {"exacta", "calle", "cruce", "barrio", "aproximada", "por_confirmar", "sin_ubicar"}
ESTADOS = {"varias_fuentes", "sin_verificar", "oficial"}
LAT = (-1.6, 0.8)
LON = (-92.1, -89.1)
FUENTE = "Reporte ciudadano por WhatsApp, sin verificar"
FUENTE_OFICIAL = "Aviso oficial reenviado"
GRANDE, MINI = 1280, 360
PROPS = ["id", "hora", "hora_fin", "lugar", "barrio", "tipo", "gravedad", "estado", "n_fuentes", "precision",
         "titulo", "descripcion"]


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


def nombres_autores(mensajes: list[dict]) -> set[str]:
    out = set()
    for m in mensajes:
        n = re.sub(r"\(.*?\)", " ", m.get("autor_nombre") or "")
        n = norm(re.sub(r"[+\d]", " ", n))
        if len(n.split()) >= 2 and len(n) >= 8:
            out.add(n)
    return out


def ruta_origen(medio: dict, msgs: dict, priv: Path) -> Path | None:
    if medio.get("fotograma"):
        return priv / "fotogramas" / f"{medio['id']}_{medio['fotograma']}.jpg"
    m = msgs.get(medio["id"])
    if not m or m.get("tipo") != "image" or not m.get("archivo"):
        return None
    return priv / m["archivo"]


def nombre_foto(medio: dict) -> str:
    return f"{medio['id']}_{medio['fotograma']}.jpg" if medio.get("fotograma") else f"{medio['id']}.jpg"


def validar(datos: dict, mensajes: list[dict], priv: Path) -> list[str]:
    err: list[str] = []
    msgs = {m["id8"]: m for m in mensajes if m.get("id8") and m.get("tipo") == "image"}
    autores = nombres_autores(mensajes)
    ids = Counter(r.get("id") for r in datos["reportes"])
    textos_globales = [("titulo", datos.get("titulo", "")), ("nota", datos.get("nota", ""))]
    textos_globales += [(f"avisos[{i}]", f"{a.get('fuente', '')} {a.get('texto', '')}")
                        for i, a in enumerate(datos.get("avisos", []))]
    for r in datos["reportes"]:
        rid = r.get("id")
        if ids[rid] > 1:
            err.append(f"{rid}: id repetido")
        if r.get("tipo") not in TIPOS:
            err.append(f"{rid}: tipo desconocido {r.get('tipo')!r}")
        if r.get("precision") not in PRECISIONES:
            err.append(f"{rid}: precisión desconocida {r.get('precision')!r}")
        if r.get("estado") not in ESTADOS:
            err.append(f"{rid}: estado desconocido {r.get('estado')!r}")
        g = r.get("gravedad")
        if g is not None and g not in (1, 2, 3, 4):
            err.append(f"{rid}: gravedad fuera de 1–4 ({g!r})")
        if r.get("precision") != "sin_ubicar":
            lat, lon = r.get("lat"), r.get("lon")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                err.append(f"{rid}: faltan coordenadas")
            elif not (LAT[0] <= lat <= LAT[1] and LON[0] <= lon <= LON[1]):
                err.append(f"{rid}: coordenadas fuera de Galápagos ({lat}, {lon})")
        for medio in r.get("medios", []):
            o = ruta_origen(medio, msgs, priv)
            if o is None or not o.exists():
                err.append(f"{rid}: medio {medio.get('id')} no existe ({'fotograma ' + str(medio['fotograma']) if medio.get('fotograma') else 'foto'})")
        textos = [(f"{rid}.{k}", r.get(k) or "") for k in ("titulo", "descripcion", "lugar", "barrio")]
        textos += [(f"{rid}.pie", m.get("pie") or "") for m in r.get("medios", [])]
        textos_globales_r = textos
        for campo, t in textos_globales_r:
            _revisar_texto(campo, t, autores, err)
    for campo, t in textos_globales:
        _revisar_texto(campo, t, autores, err)
    return err


def _revisar_texto(campo: str, t: str, autores: set[str], err: list[str]) -> None:
    if comun.RE_TELEFONO.search(t):
        err.append(f"{campo}: contiene un teléfono")
    n = norm(t)
    for a in autores:
        if a in n:
            err.append(f"{campo}: contiene el nombre de quien escribe ({a.split()[0]} …)")


def hacer_foto(origen: Path, destino: Path, lado: int) -> bool:
    if destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime:
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(origen) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((lado, lado), Image.LANCZOS)
        limpia = Image.new("RGB", im.size)
        limpia.paste(im)
        limpia.save(destino, "JPEG", quality=80, optimize=True)   # sin exif=: no lleva metadatos
    return True


def props(r: dict, fotos: list[dict]) -> dict:
    p = {k: r.get(k) for k in PROPS}
    p["fuente"] = FUENTE_OFICIAL if r.get("estado") == "oficial" else FUENTE
    p["fotos"] = fotos
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--evento", default=comun.EVENTO_POR_DEFECTO)
    ev = ap.parse_args().evento
    carpeta = comun.carpeta_evento(ev)
    fuente = carpeta / "reportes.json"
    if not fuente.exists():
        print(f"No existe {fuente}", file=sys.stderr)
        return 1
    datos = json.loads(fuente.read_text(encoding="utf-8"))
    priv = comun.privado(ev)
    mensajes = comun.leer_mensajes(ev)
    err = validar(datos, mensajes, priv)
    if err:
        print(f"{len(err)} error(es) de validación:", file=sys.stderr)
        for e in err:
            print(f"  - {e}", file=sys.stderr)
        return 1
    msgs = {m["id8"]: m for m in mensajes if m.get("id8") and m.get("tipo") == "image"}

    pub = comun.RAIZ / "publicar" / ev
    (pub / "fotos").mkdir(parents=True, exist_ok=True)
    (pub / "mini").mkdir(parents=True, exist_ok=True)
    usadas: set[str] = set()
    nuevas = 0
    features, sin_ubicar = [], []
    for r in datos["reportes"]:
        fotos = []
        for medio in r.get("medios", []):
            n = nombre_foto(medio)
            o = ruta_origen(medio, msgs, priv)
            usadas.add(n)
            nuevas += hacer_foto(o, pub / "fotos" / n, GRANDE)
            hacer_foto(o, pub / "mini" / n, MINI)
            fotos.append({"archivo": f"fotos/{n}", "mini": f"mini/{n}", "hora": medio.get("hora"), "pie": medio.get("pie")})
        p = props(r, fotos)
        if r["precision"] == "sin_ubicar":
            sin_ubicar.append(p)
        else:
            features.append({"type": "Feature", "properties": p,
                             "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]}})
    for sub in ("fotos", "mini"):
        for f in (pub / sub).iterdir():
            if f.name not in usadas:
                f.unlink()

    gj = json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n"
    (carpeta / "reportes.geojson").write_text(gj, encoding="utf-8")
    (pub / "reportes.geojson").write_text(gj, encoding="utf-8")
    evento = {"titulo": datos.get("titulo"), "nota": datos.get("nota"), "corte": datos.get("corte"),
              "gravedad": datos.get("gravedad"), "avisos": datos.get("avisos", []), "sin_ubicar": sin_ubicar}
    (pub / "evento.json").write_text(json.dumps(evento, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    web = comun.RAIZ / "web" / "index.html"
    if web.exists():
        shutil.copyfile(web, pub / "index.html")
    else:
        print("Aviso: falta reportes/web/index.html", file=sys.stderr)

    graves = Counter(f["properties"]["gravedad"] for f in features)
    print(f"Evento {ev}: {len(features)} reportes con ubicación, {len(sin_ubicar)} por ubicar")
    print("  por gravedad: " + ", ".join(f"{k if k else 'sin dato'}: {v}" for k, v in sorted(graves.items(), key=lambda x: (x[0] is None, x[0]))))
    print(f"  fotos: {len(usadas)} ({nuevas} nuevas o actualizadas)")
    print(f"  salida: {pub}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
