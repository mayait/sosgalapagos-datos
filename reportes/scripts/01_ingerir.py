#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
"""Paso 1 · Ingerir la carpeta exportada de WhatsApp.

Lee cada grupo (`<grupo>/mensajes.json` y sus medios) y lo suma a
`reportes/privado/<evento>/`. Es incremental: se puede correr cada vez que la carpeta
se actualiza y solo añade lo nuevo. Cada corrida es un «lote» numerado, para saber
qué falta revisar.

    geodatos/.venv/bin/python -I reportes/scripts/01_ingerir.py "<carpeta de WhatsApp>"

Nada de lo que escribe este paso es público: guarda nombres, teléfonos y medios crudos.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402


def metadatos(crudo: str) -> dict:
    if not crudo or crudo == "None":
        return {}
    try:
        return ast.literal_eval(crudo)
    except (ValueError, SyntaxError):
        return {}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("origen", type=Path, help="carpeta exportada de WhatsApp (una subcarpeta por grupo)")
    ap.add_argument("--evento", default=comun.EVENTO_POR_DEFECTO)
    a = ap.parse_args()

    priv = comun.privado(a.evento)
    medios = priv / "medios"
    previos = {m["id"]: m for m in comun.leer_mensajes(a.evento)}
    lote = 1 + max((m["lote"] for m in previos.values()), default=0)
    por_hash = {m["sha256"]: m["id"] for m in previos.values() if m.get("sha256") and not m.get("duplicado_de")}

    remitentes = {}
    f_rem = a.origen / "remitentes.json"
    if f_rem.exists():
        remitentes = json.loads(f_rem.read_text(encoding="utf-8"))

    nuevos, sin_archivo, archivos_tardios = 0, 0, 0
    for f_msj in sorted(a.origen.glob("*/mensajes.json")):
        grupo = f_msj.parent.name
        gslug = comun.slug(grupo)
        # Los medios se llaman HHMMSS_tipo_<8 primeros del id>[_nombre].ext
        archivos = {}
        for f in f_msj.parent.iterdir():
            partes = f.name.split("_", 3)
            if len(partes) >= 3 and f.name not in ("mensajes.json", "mensajes.txt"):
                archivos[partes[2].split(".")[0][:8]] = f

        for m in json.loads(f_msj.read_text(encoding="utf-8")):
            mid = m["id"]
            previo = previos.get(mid)
            if previo and (previo.get("archivo") or previo["tipo"] not in comun.TIPOS_CON_ARCHIVO):
                continue  # ya está completo
            autor = m.get("author") if m.get("author") not in (None, "None") else None
            lid = (autor or "").split("@")[0]
            ts = dt.datetime.fromtimestamp(int(m["timestamp"]), dt.timezone.utc)
            meta = metadatos(m.get("metadata", ""))
            reg = previo or {
                "id": mid,
                "id8": mid[:8],
                "lote": lote,
                "grupo": grupo,
                "ts": ts.isoformat(),
                "hora": ts.astimezone(comun.GALAPAGOS).strftime("%H:%M:%S"),
                "autor": comun.clave_autor(autor) if m.get("direction") != "outgoing" else "yo",
                "autor_nombre": remitentes.get(lid) or m.get("chatName"),  # PRIVADO
                "tipo": m["type"],
                "texto": m.get("body") or "",
                "cita": ((meta.get("quotedMessage") or {}).get("body") or "")[:200] or None,
                "ubicacion": meta.get("location"),
                "archivo": None,
            }
            if reg["tipo"] in comun.TIPOS_CON_ARCHIVO and not reg.get("archivo"):
                src = archivos.get(mid[:8])
                if src is None:
                    sin_archivo += 1
                else:
                    dst = medios / gslug / src.name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                        shutil.copy2(src, dst)
                    h = comun.sha256(dst)
                    reg["archivo"] = str(dst.relative_to(priv))
                    reg["sha256"] = h
                    reg["duplicado_de"] = por_hash.get(h)
                    por_hash.setdefault(h, mid)
                    if previo:
                        archivos_tardios += 1
                        reg["lote"] = lote  # el medio llegó después: vuelve a quedar pendiente de revisar
            if not previo:
                nuevos += 1
            previos[mid] = reg

    comun.escribir_mensajes(a.evento, list(previos.values()))
    del_lote = [m for m in previos.values() if m["lote"] == lote]
    tipos: dict[str, int] = {}
    for m in del_lote:
        tipos[m["tipo"]] = tipos.get(m["tipo"], 0) + 1
    print(f"Evento {a.evento} · lote {lote}: {nuevos} mensajes nuevos, {archivos_tardios} medios que llegaron tarde.")
    print(f"  Por tipo: {dict(sorted(tipos.items()))}")
    print(f"  Medios aún sin archivo en la carpeta: {sin_archivo} · total acumulado: {len(previos)} mensajes")
    if not del_lote:
        print("  Nada nuevo.")


if __name__ == "__main__":
    main()
