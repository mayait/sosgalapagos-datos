#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Paso 2 · Preparar los medios para revisarlos rápido.

De cada medio nuevo (no duplicado) saca, dentro de `reportes/privado/<evento>/`:

- `fotogramas/<id8>_<n>.jpg`: tres fotogramas de cada video (al 15, 50 y 85 %);
- `laminas/`: láminas de contacto con fotos y fotogramas rotulados con su id, para verlos de un vistazo;
- `transcripciones/<id8>.txt`: lo que se dice en cada audio y en cada video (whisper.cpp).

Es incremental: lo que ya existe no se rehace.

    geodatos/.venv/bin/python -I reportes/scripts/02_medios.py [--sin-transcribir]

La transcripción necesita `whisper-cli` y un modelo ggml: variable WHISPER_MODELO.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402

CELDA = (560, 420)
COLS = 3
FILAS = {"fotos": 2, "videos": 4}   # cada video ocupa una fila con sus tres fotogramas


def duracion(ruta: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def fotogramas(m: dict, priv: Path) -> list[Path]:
    dst = priv / "fotogramas"
    dst.mkdir(exist_ok=True)
    salida = [dst / f"{m['id8']}_{n}.jpg" for n in (1, 2, 3)]
    if all(f.exists() for f in salida):
        return salida
    src = priv / m["archivo"]
    d = duracion(src)
    for f, frac in zip(salida, (0.15, 0.5, 0.85)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * frac:.2f}", "-i", str(src), "-frames:v", "1",
                        "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", str(f)], capture_output=True)
    return [f for f in salida if f.exists()]


def fuente(tam: int):
    for ruta in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def lamina(celdas: list[tuple[Path, str]], destino: Path, filas: int) -> None:
    """Una rejilla de imágenes con su rótulo (id · hora · grupo) encima de cada una."""
    alto_rot = 30
    hoja = Image.new("RGB", (COLS * CELDA[0], filas * (CELDA[1] + alto_rot)), "white")
    dib = ImageDraw.Draw(hoja)
    f = fuente(20)
    for i, (ruta, rotulo) in enumerate(celdas):
        if not rotulo:
            continue  # hueco: un video del que no salieron los tres fotogramas
        x, y = (i % COLS) * CELDA[0], (i // COLS) * (CELDA[1] + alto_rot)
        try:
            im = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
            im.thumbnail((CELDA[0] - 6, CELDA[1] - 6))
            hoja.paste(im, (x + (CELDA[0] - im.width) // 2, y + alto_rot + (CELDA[1] - im.height) // 2))
        except OSError:
            rotulo += " (ilegible)"
        dib.text((x + 6, y + 4), rotulo, fill="black", font=f)
    hoja.save(destino, quality=82)


def transcribir(m: dict, priv: Path, modelo: str) -> None:
    dst = priv / "transcripciones"
    dst.mkdir(exist_ok=True)
    salida = dst / f"{m['id8']}.txt"
    if salida.exists():
        return
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(priv / m["archivo"]), "-vn", "-ar", "16000",
                            "-ac", "1", str(wav)], capture_output=True)
        if r.returncode != 0 or not wav.exists() or wav.stat().st_size < 20_000:  # sin audio o < 0,6 s
            salida.write_text("", encoding="utf-8")
            return
        r = subprocess.run(["whisper-cli", "-m", modelo, "-l", "es", "-nt", "-np", "-f", str(wav)],
                           capture_output=True, text=True)
        if r.returncode != 0 and not r.stdout.strip():
            raise SystemExit(f"whisper-cli falló con {m['id8']}: revisa WHISPER_MODELO.\n{r.stderr[-400:]}")
        salida.write_text(" ".join(r.stdout.split()), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--evento", default=comun.EVENTO_POR_DEFECTO)
    ap.add_argument("--sin-transcribir", action="store_true")
    a = ap.parse_args()

    priv = comun.privado(a.evento)
    mensajes = [m for m in comun.leer_mensajes(a.evento) if m.get("archivo") and not m.get("duplicado_de")]
    fotos = [m for m in mensajes if m["tipo"] == "image"]
    videos = [m for m in mensajes if m["tipo"] == "video"]
    audios = [m for m in mensajes if m["tipo"] in ("voice", "audio")]

    with ThreadPoolExecutor(6) as ex:
        cuadros = dict(zip((m["id8"] for m in videos), ex.map(lambda m: fotogramas(m, priv), videos)))
    print(f"Fotogramas: {sum(len(v) for v in cuadros.values())} de {len(videos)} videos")

    # Láminas: una serie por lote, para que cada actualización traiga solo láminas nuevas.
    dlam = priv / "laminas"
    dlam.mkdir(exist_ok=True)
    hechas = 0
    for lote in sorted({m["lote"] for m in mensajes}):
        celdas_f = [(priv / m["archivo"], f"{m['id8']} {m['hora'][:5]} {m['grupo'][:22]}") for m in fotos if m["lote"] == lote]
        celdas_v = []
        for m in videos:
            if m["lote"] == lote:
                cs = cuadros.get(m["id8"], [])
                for n, c in enumerate(cs, 1):
                    celdas_v.append((c, f"{m['id8']}·{n} {m['hora'][:5]} {m['grupo'][:20]}"))
                celdas_v += [(Path("/nonexistent"), "")] * (COLS - len(cs))  # cada video ocupa una fila
        for prefijo, celdas in (("fotos", celdas_f), ("videos", celdas_v)):
            por_hoja = COLS * FILAS[prefijo]
            for i in range(0, len(celdas), por_hoja):
                destino = dlam / f"lote{lote:02d}_{prefijo}_{i // por_hoja + 1:03d}.jpg"
                if not destino.exists():
                    lamina(celdas[i:i + por_hoja], destino, FILAS[prefijo])
                    hechas += 1
    print(f"Láminas nuevas: {hechas} en {dlam}")

    if a.sin_transcribir:
        return
    modelo = os.environ.get("WHISPER_MODELO", "")
    if not shutil.which("whisper-cli") or not os.path.exists(modelo):
        print("Sin transcripción: falta whisper-cli o WHISPER_MODELO no apunta a un modelo ggml.")
        return
    pendientes = [m for m in audios + videos if not (priv / "transcripciones" / f"{m['id8']}.txt").exists()]
    print(f"Transcribiendo {len(pendientes)} audios y videos…", flush=True)
    for i, m in enumerate(pendientes, 1):
        transcribir(m, priv, modelo)
        if i % 20 == 0:
            print(f"  {i}/{len(pendientes)}", flush=True)
    print("Transcripción terminada.")


if __name__ == "__main__":
    main()
