#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Paso 6 · Publicar las buenas noticias y la ayuda como capa de mapa (un corazón por acción).

Lee `eventos/<evento>/buenas_noticias.json` (curado a mano), lo valida y produce:

- `eventos/<evento>/buenas_noticias.geojson` (GENERADO, versionado): solo las que tienen coordenadas;
- `publicar/<evento>/buenas/` (ignorado por git): `buenas_noticias.geojson`, `sin_ubicar.json`, `fotos/` y `mini/`, sin EXIF.

Cada buena noticia dice quién la hace (`autor`): una organización, institución, empresa o colectivo. Nunca una
persona particular: la validación rechaza teléfonos y nombres de quienes escriben en los grupos. Si el nombre de una
organización coincide con el de un contacto, se declara en la lista `organizaciones` del JSON; la comprobación no se quita.
`estado_accion` distingue lo anunciado de lo que ya se hizo. No llevan gravedad: no son reportes de riesgo.

    geodatos/.venv/bin/python -I reportes/scripts/06_buenas.py [--evento 2026-11-21]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402

_spec = importlib.util.spec_from_file_location("publicar03", Path(__file__).resolve().parent / "03_publicar.py")
p03 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p03)

ESTADOS_ACCION = {"anunciado", "en_curso", "realizado"}
FUENTE = "Mensajes de vecinos y organizaciones por WhatsApp, sin verificar"
PROPS = ["id", "hora", "hora_fin", "lugar", "barrio", "autor", "estado_accion", "precision", "titulo", "descripcion"]


def revisar_texto(campo: str, t: str, autores: set[str], permitidas: list[str], err: list[str]) -> None:
    if comun.RE_TELEFONO.search(t):
        err.append(f"{campo}: contiene un teléfono")
    n = p03.norm(t)
    for org in permitidas:          # una organización declarada no cuenta como nombre de persona
        n = n.replace(org, " ")
    for a in autores:
        if a in n:
            err.append(f"{campo}: contiene el nombre de quien escribe ({a.split()[0]} …)")


def validar(datos: dict, mensajes: list[dict], priv: Path) -> list[str]:
    err: list[str] = []
    msgs = {m["id8"]: m for m in mensajes if m.get("id8") and m.get("tipo") == "image"}
    autores = p03.nombres_autores(mensajes)
    permitidas = sorted((p03.norm(o) for o in datos.get("organizaciones", [])), key=len, reverse=True)
    ids = Counter(b.get("id") for b in datos["buenas"])
    for b in datos["buenas"]:
        bid = b.get("id")
        if ids[bid] > 1:
            err.append(f"{bid}: id repetido")
        if b.get("precision") not in p03.PRECISIONES:
            err.append(f"{bid}: precisión desconocida {b.get('precision')!r}")
        if b.get("estado_accion") not in ESTADOS_ACCION:
            err.append(f"{bid}: estado_accion desconocido {b.get('estado_accion')!r}")
        if not (b.get("autor") or "").strip():
            err.append(f"{bid}: falta el autor (si no se sabe: «Autor sin identificar»)")
        if "gravedad" in b:
            err.append(f"{bid}: una buena noticia no lleva gravedad")
        if b.get("precision") != "sin_ubicar":
            lat, lon = b.get("lat"), b.get("lon")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                err.append(f"{bid}: faltan coordenadas")
            elif not (p03.LAT[0] <= lat <= p03.LAT[1] and p03.LON[0] <= lon <= p03.LON[1]):
                err.append(f"{bid}: coordenadas fuera de Galápagos ({lat}, {lon})")
        for medio in b.get("medios", []):
            o = p03.ruta_origen(medio, msgs, priv)
            if o is None or not o.exists():
                err.append(f"{bid}: medio {medio.get('id')} no existe")
        textos = [(f"{bid}.{k}", b.get(k) or "") for k in ("titulo", "descripcion", "lugar", "barrio", "autor")]
        textos += [(f"{bid}.pie", m.get("pie") or "") for m in b.get("medios", [])]
        for campo, t in textos:
            revisar_texto(campo, t, autores, permitidas, err)
    for campo in ("titulo", "nota"):
        revisar_texto(campo, datos.get(campo, ""), autores, permitidas, err)
    return err


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--evento", default=comun.EVENTO_POR_DEFECTO)
    ev = ap.parse_args().evento
    carpeta = comun.carpeta_evento(ev)
    fuente = carpeta / "buenas_noticias.json"
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

    pub = comun.RAIZ / "publicar" / ev / "buenas"
    (pub / "fotos").mkdir(parents=True, exist_ok=True)
    (pub / "mini").mkdir(parents=True, exist_ok=True)
    usadas: set[str] = set()
    features, sin_ubicar = [], []
    for b in datos["buenas"]:
        fotos = []
        for medio in b.get("medios", []):
            n = p03.nombre_foto(medio)
            o = p03.ruta_origen(medio, msgs, priv)
            usadas.add(n)
            p03.hacer_foto(o, pub / "fotos" / n, p03.GRANDE)
            p03.hacer_foto(o, pub / "mini" / n, p03.MINI)
            fotos.append({"archivo": f"fotos/{n}", "mini": f"mini/{n}", "hora": medio.get("hora"), "pie": medio.get("pie")})
        p = {k: b.get(k) for k in PROPS}
        p["tipo"] = "buena_noticia"
        p["fuente"] = FUENTE
        p["fotos"] = fotos
        if b["precision"] == "sin_ubicar":
            sin_ubicar.append(p)
        else:
            features.append({"type": "Feature", "properties": p,
                             "geometry": {"type": "Point", "coordinates": [b["lon"], b["lat"]]}})
    for sub in ("fotos", "mini"):
        for f in (pub / sub).iterdir():
            if f.name not in usadas:
                f.unlink()

    gj = json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=1) + "\n"
    (carpeta / "buenas_noticias.geojson").write_text(gj, encoding="utf-8")
    (pub / "buenas_noticias.geojson").write_text(gj, encoding="utf-8")
    (pub / "sin_ubicar.json").write_text(json.dumps(sin_ubicar, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    est = Counter(f["properties"]["estado_accion"] for f in features)
    print(f"Evento {ev}: {len(features)} buenas noticias con ubicación, {len(sin_ubicar)} sin ubicar")
    print("  por estado: " + ", ".join(f"{k}: {v}" for k, v in sorted(est.items())))
    print(f"  fotos: {len(usadas)} · salida: {pub}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
