# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
"""Rutas y utilidades comunes de los reportes de campo.

Todo lo que trae nombres, teléfonos o medios sin revisar vive en `reportes/privado/`,
que git ignora. Lo único que se versiona es lo curado: `eventos/<evento>/reportes.json`.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # reportes/
REPO = RAIZ.parent
PRIVADO = Path(os.environ.get("REPORTES_PRIVADO", RAIZ / "privado"))
EVENTO_POR_DEFECTO = "2026-11-21"
GALAPAGOS = dt.timezone(dt.timedelta(hours=-6))        # Galápagos = UTC−6

TIPOS_CON_ARCHIVO = {"image", "video", "voice", "audio", "document"}


def privado(evento: str) -> Path:
    p = PRIVADO / evento
    p.mkdir(parents=True, exist_ok=True)
    return p


def carpeta_evento(evento: str) -> Path:
    p = RAIZ / "eventos" / evento
    p.mkdir(parents=True, exist_ok=True)
    return p


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def clave_autor(autor: str | None) -> str:
    """Seudónimo estable de quien escribe: sirve para contar fuentes distintas sin guardar quién es."""
    if not autor or autor == "None":
        return "yo"
    return "p" + hashlib.sha256(autor.encode()).hexdigest()[:5]


def hora_local(ts_utc: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts_utc).astimezone(GALAPAGOS)


def leer_mensajes(evento: str) -> list[dict]:
    f = privado(evento) / "mensajes.jsonl"
    if not f.exists():
        return []
    with f.open(encoding="utf-8") as fh:
        return [json.loads(linea) for linea in fh if linea.strip()]


def escribir_mensajes(evento: str, mensajes: list[dict]) -> None:
    f = privado(evento) / "mensajes.jsonl"
    mensajes = sorted(mensajes, key=lambda m: (m["ts"], m["id"]))
    with f.open("w", encoding="utf-8") as fh:
        for m in mensajes:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for trozo in iter(lambda: fh.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


# Un teléfono ecuatoriano o internacional escrito de cualquier forma: no puede salir en nada público.
RE_TELEFONO = re.compile(r"(?:\+?593|\b0)[\s.-]?9(?:[\s.-]?\d){8}\b|\+\d{10,13}\b")
