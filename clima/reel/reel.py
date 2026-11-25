#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Reel del clima de Galápagos: un video vertical (1080 × 1920) por día, con el mapa de lluvia y viento
animado hora a hora, la hora de más lluvia en cada isla, la marea y la lluvia ya medida.

    python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26 --solo-datos    # baja los datos y los resume
    python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26 --prueba        # una imagen por día, rápido
    python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26                 # el reel completo

Usa solo los datos públicos de sosgalapagos.org (los mismos del panel de /clima/). Sin dependencias de
Python; para grabar necesita Node 22 o posterior, Google Chrome y ffmpeg. La guía completa, con los pasos
para revisar el resultado, está en .claude/skills/reel-clima/SKILL.md.
"""
import argparse
import base64
import datetime as dt
import html
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SITIO = "https://sosgalapagos.org"
# Datos públicos del sitio (los del panel de /clima/). Cambian de forma sin aviso: si algo falla aquí,
# mira primero si cambió el JSON.
DESCARGAS = {
    "estado.json": "/clima/datos/estado.json",                # pronóstico, estaciones y curva de marea
    "mar.json": "/riesgos/api/clima/mar",                     # pleamares y bajamares de la tabla del INOCAR
    "lluvia-mapa.json": "/riesgos/api/clima/lluvia-mapa.json",  # lluvia y viento de los modelos, cada 3 h
}
GAL = dt.timezone(dt.timedelta(hours=-6))   # Galápagos, UTC−6 todo el año
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
ABREV = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
SLUG = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]      # para los nombres de archivo, sin tildes
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MODELO = "ecmwf_ifs"                                          # el mismo que muestra el panel por defecto

# Una columna por isla. «punto» es el punto de la parte alta en el pronóstico del sitio; «alta» es dónde se
# lee la lluvia del modelo para la tira de horas; «estaciones» son las candidatas para «Ya llovió en 7 días»,
# en orden de preferencia: (fuente, estación, cómo se acredita).
ISLAS = [
    dict(nombre="Santa Cruz", punto="santa-rosa", alta=(-0.655, -90.404),
         estaciones=[("ambient", "miconia", "estaciones particulares"), ("ierse", "n_glps09", "IERSE (CC BY-NC-ND 4.0)")]),
    dict(nombre="San Cristóbal", punto="el-junco", alta=(-0.893, -89.5),
         estaciones=[("gsc", "junco", "GSC-USFQ"), ("gsc", "mirador", "GSC-USFQ")]),
    dict(nombre="Isabela", punto="sierra-negra", alta=(-0.86, -91.03), estaciones=[]),
]
# Con 200 mm o más en 7 días el suelo ya no absorbe: es el umbral de saturación de la regla de inundación
# (clima/recolector/umbrales_inundacion.json, zona alta de Santa Cruz).
SATURADO_MM = 200
CUADROS_POR_DIA = 321      # 15 quietos + 270 de animación + 36 quietos (reel.js), a 30 por segundo: 10,7 s


def fallar(mensaje):
    sys.exit("ERROR: " + mensaje)


def hora_utc(texto):
    return dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))


def nombre_dia(fecha):
    return "%s %d" % (DIAS_SEMANA[fecha.weekday()].capitalize(), fecha.day)


def slug_dia(fecha):
    return "%s%02d" % (SLUG[fecha.weekday()], fecha.day)


def fecha_corta(fecha):
    return "%s %d-%s" % (ABREV[fecha.weekday()], fecha.day, MESES[fecha.month - 1])


def lista(nombres):
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


# ---------------------------------------------------------------- datos

def bajar(carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, ruta in DESCARGAS.items():
        pedido = urllib.request.Request(SITIO + ruta, headers={"User-Agent": "sosgalapagos-reel (python-urllib)"})
        with urllib.request.urlopen(pedido, timeout=120) as r:
            (carpeta / nombre).write_bytes(r.read())


def cargar(carpeta):
    try:
        return {n: json.loads((carpeta / n).read_text(encoding="utf-8")) for n in DESCARGAS}
    except (OSError, ValueError) as e:
        fallar("no se pudieron leer los datos de %s: %s" % (carpeta, e))


class Mapa:
    """Lee lluvia-mapa.json igual que reel.js: bytes en base64, lluvia en 3 h = (b/10)² mm, 255 = sin dato."""

    def __init__(self, lm):
        self.horas = lm["horas"]
        self.g = lm["rejilla"]
        self.modelo = next((m for m in lm["modelos"] if m["id"] == MODELO), None)
        if self.modelo is None or self.modelo.get("disponible") is False:
            fallar("el modelo %s no está disponible en lluvia-mapa.json" % MODELO)
        self._cache = {}

    def inicio(self, fecha):
        """Índice de las 00:00 de Galápagos (06:00Z) de ese día, o None si el mapa no cubre el día entero."""
        try:
            i = self.horas.index(fecha.isoformat() + "T06:00Z")
        except ValueError:
            return None
        return i if i + 8 <= len(self.horas) - 1 else None

    def lluvia(self, i, lat, lon):
        """Lluvia del modelo (mm en las 3 h que terminan en horas[i]) en un punto, con interpolación bilineal."""
        if i not in self._cache:
            self._cache[i] = [0.0 if b == 255 else (b / 10) ** 2 for b in base64.b64decode(self.modelo["lluvia"][i])]
        a, g = self._cache[i], self.g
        x, y = (lon - g["oeste"]) / g["paso"], (g["norte"] - lat) / g["paso"]
        x0, y0 = min(int(x), g["nlon"] - 2), min(int(y), g["nlat"] - 2)
        fx, fy, k = x - x0, y - y0, y0 * g["nlon"] + x0
        return ((a[k] * (1 - fx) + a[k + 1] * fx) * (1 - fy)
                + (a[k + g["nlon"]] * (1 - fx) + a[k + g["nlon"] + 1] * fx) * fy)


def marea(estado, mar):
    """Curva de la marea de Puerto Ayora (predicción del sitio) llevada al nivel de la tabla del INOCAR."""
    m = estado["mareas"]["estaciones"]["sant"]
    extremos = [x for p in mar["puertos"] if p["puerto"] == "santa-cruz" for x in p["mareas"]["extremos"]]
    t0, paso, pred = hora_utc(m["t0"]), m["paso_min"], m["pred_cm"]
    # La predicción va sobre el nivel medio y la tabla del INOCAR sobre la bajamar de sicigia (MLWS):
    # el desfase entre las dos se saca de las pleamares y bajamares que caen dentro de la curva.
    difs = []
    for x in extremos:
        i = (hora_utc(x["ts"]) - t0).total_seconds() / 60 / paso
        if 0 <= i < len(pred) - 1 and pred[int(i)] is not None and pred[int(i) + 1] is not None:
            f = i - int(i)
            difs.append(x["altura_m"] - (pred[int(i)] * (1 - f) + pred[int(i) + 1] * f) / 100)
    if not difs:
        fallar("la curva de marea y la tabla del INOCAR no coinciden en ninguna hora")
    return {"t0": m["t0"], "paso_min": paso, "pred_cm": pred, "desfase_m": round(sum(difs) / len(difs), 3),
            "extremos": extremos, "anomalia_cm": m.get("anomalia_cm"),
            "fin": t0 + dt.timedelta(minutes=paso * (len(pred) - 1)), "inicio": t0}


def lluvia_medida(estado):
    """Lluvia de los últimos 7 días en la estación de la parte alta de cada isla (None si no hay)."""
    generado = hora_utc(estado["generado"])
    por_clave = {(e["fuente"], e["estacion"]): e for e in estado["estaciones"]}
    salida = []
    for isla in ISLAS:
        dato = None
        for fuente, estacion, credito in isla["estaciones"]:
            e = por_clave.get((fuente, estacion))
            if not e or e.get("danada") or not e.get("ultimo") or (e.get("lluvia") or {}).get("7d") is None:
                continue
            if generado - hora_utc(e["ultimo"]) > dt.timedelta(hours=6):   # dejó de transmitir: la suma no vale
                continue
            dato = {"mm": round(e["lluvia"]["7d"]), "estacion": e["nombre"], "credito": credito}
            break
        salida.append(dato)
    return salida


def resumir(dias, datos):
    """Todo lo que el reel muestra, en un diccionario: sirve para escribir las frases y para revisar el video."""
    estado, mapa, mr = datos["estado.json"], Mapa(datos["lluvia-mapa.json"]), marea(datos["estado.json"], datos["mar.json"])
    pron = estado["pronostico"]
    hoy = dt.date.fromisoformat(pron["hoy_local"])
    puntos = {p["id"]: p for z in pron["zonas"].values() for p in z["puntos"]}
    problemas, por_dia = [], []
    for fecha in dias:
        i0 = mapa.inicio(fecha)
        if i0 is None:
            problemas.append("el mapa de lluvia no cubre el %s (va de %s a %s)" % (fecha, mapa.horas[0], mapa.horas[-1]))
            continue
        ini = dt.datetime.combine(fecha, dt.time(6), dt.timezone.utc)
        fin = ini + dt.timedelta(hours=24)
        if not (mr["inicio"] <= ini and fin <= mr["fin"]):
            problemas.append("la curva de marea no cubre el %s (llega hasta %s)" % (fecha, mr["fin"].isoformat()))
        extremos = [x for x in mr["extremos"] if ini <= hora_utc(x["ts"]) <= fin]
        if len(extremos) < 2:
            problemas.append("la tabla del INOCAR no trae las mareas del %s" % fecha)
        islas = []
        for isla in ISLAS:
            bloques = [round(mapa.lluvia(i0 + b + 1, *isla["alta"]), 1) for b in range(8)]
            pico = bloques.index(max(bloques))
            pr = next((d for d in puntos.get(isla["punto"], {}).get("dias", []) if d["fecha"] == fecha.isoformat()), None)
            islas.append({
                "isla": isla["nombre"],
                "modelo_mm_cada_3h": bloques,
                "hora_de_mas_lluvia": "%02d–%02d h" % (pico * 3, pico * 3 + 3) if max(bloques) >= 0.3 else None,
                "prob_20mm": pr and pr["prob"].get("20"),
                "senal": pr and pr.get("nivel"),
            })
        por_dia.append({
            "fecha": fecha.isoformat(), "dia": nombre_dia(fecha), "slug": slug_dia(fecha),
            "es_hoy": fecha == hoy, "pasado": fecha < hoy, "islas": islas,
            "mareas": [{"hora": x["local"].split(" ")[-1], "tipo": x["tipo"], "altura_m": x["altura_m"]} for x in extremos],
        })
        if fecha < hoy:
            problemas.append("el %s ya pasó (hoy es %s en Galápagos)" % (fecha, hoy))
    corrida = mapa.modelo.get("corrida")
    return {
        "emitido_local": pron["generado_local"], "hoy_local": pron["hoy_local"],
        "modelo": mapa.modelo["nombre"], "corrida_modelo_utc": corrida,
        "mapa_generado_utc": datos["lluvia-mapa.json"].get("generado"),
        "lluvia_7d": lluvia_medida(estado), "mar_anomalia_cm": mr["anomalia_cm"],
        "dias": por_dia, "problemas": problemas, "_marea": mr,
    }


def imprimir_resumen(r):
    print("Pronóstico emitido: %s (hora de Galápagos). Modelo del mapa: %s, corrida %s; mapa generado %s."
          % (r["emitido_local"].replace("T", " "), r["modelo"], r["corrida_modelo_utc"], r["mapa_generado_utc"]))
    medida = ["%s %s" % (i["nombre"], ("%d mm (%s)" % (d["mm"], d["estacion"])) if d else "sin estación")
              for i, d in zip(ISLAS, r["lluvia_7d"])]
    print("Ya llovió en 7 días, parte alta: " + "; ".join(medida) + ".")
    if r["mar_anomalia_cm"] is not None:
        print("Nivel del mar: %+.0f cm frente a lo normal (mareógrafo de Puerto Ayora, últimas 6 h)." % r["mar_anomalia_cm"])
    for d in r["dias"]:
        print("\n%s (%s)%s" % (d["dia"], d["fecha"], " · HOY" if d["es_hoy"] else ""))
        for i in d["islas"]:
            prob = "sin pronóstico" if i["prob_20mm"] is None else "prob. de 20 mm o más: %d %% (señal %s)" % (round(i["prob_20mm"] * 100), i["senal"])
            print("  %-14s %s · más lluvia: %s · modelo, mm cada 3 h: %s"
                  % (i["isla"], prob, i["hora_de_mas_lluvia"] or "casi sin lluvia", " ".join("%g" % b for b in i["modelo_mm_cada_3h"])))
        print("  Marea (Puerto Ayora, INOCAR): " + ", ".join("%s %s %.2f m" % (m["hora"], m["tipo"], m["altura_m"]) for m in d["mareas"]))
    print("\nLos mm del modelo sirven para ver cuándo llueve, no cuánto: en las islas se quedan muy cortos.")
    for p in r["problemas"]:
        print("PROBLEMA: " + p)


# ---------------------------------------------------------------- páginas

def textos_por_defecto(d, hoy):
    """Etiqueta y frase si no vienen en --textos. La frase sale de la señal publicada en el panel."""
    fecha = dt.date.fromisoformat(d["fecha"])
    chip = "HOY" if fecha == hoy else "MAÑANA" if fecha == hoy + dt.timedelta(days=1) else "PRONÓSTICO"
    altas = [i["isla"] for i in d["islas"] if i["senal"] == "alta"]
    moderadas = [i["isla"] for i in d["islas"] if i["senal"] == "moderada"]
    if altas:
        frase = "Lluvia fuerte probable en la parte alta de %s." % lista(altas)
    elif moderadas:
        frase = "Puede llover fuerte en la parte alta de %s." % lista(moderadas)
    elif any(i["senal"] for i in d["islas"]):
        frase = "Sin señal de lluvia fuerte en las islas."
    else:
        frase = "Lluvia y viento de los modelos, hora a hora."
    return {"chip": chip, "rojo": False, "frase": frase}


def pagina(d, resumen, textos, porcentajes):
    hoy = dt.date.fromisoformat(resumen["hoy_local"])
    t = dict(textos_por_defecto(d, hoy), **textos.get(d["fecha"], {}))
    emitido = dt.datetime.fromisoformat(resumen["emitido_local"])
    medida = resumen["lluvia_7d"]
    anom = resumen["mar_anomalia_cm"]
    nota_marea = "tabla del INOCAR"
    if anom is not None and abs(anom) >= 10:
        nota_marea += " · %s %d cm más %s" % ("hoy el mar está" if d["es_hoy"] else "el mar viene", round(abs(anom)), "alto" if anom > 0 else "bajo")

    columnas = ""
    for isla, dato, pr in zip(ISLAS, medida, d["islas"]):
        if porcentajes:
            if pr["prob_20mm"] is None:
                fallar("el pronóstico del sitio no trae la probabilidad del %s: quita --porcentajes" % d["fecha"])
            ya = ("Ya llovió <b>%d mm</b><br>en 7 días" % dato["mm"]) if dato else "Sin estaciones:<br>no hay lluvia medida"
            columnas += '<div class="i"><h2>%s</h2><div class="pc">%d<i>%%</i></div><div class="ya">%s</div></div>' % (
                isla["nombre"], int(round(pr["prob_20mm"] * 20) * 5), ya)   # redondeada de 5 en 5
        elif dato:
            columnas += '<div class="i"><h2>%s</h2><div class="pc">%d<i>mm</i></div><div class="ya">en la parte alta</div></div>' % (isla["nombre"], dato["mm"])
        else:
            columnas += '<div class="i"><h2>%s</h2><div class="nd2">sin<br>%s</div></div>' % (isla["nombre"], "dato" if isla["estaciones"] else "estaciones")

    if porcentajes:
        titulo = "PROBABILIDAD DE LLUVIA FUERTE <span>20 mm o más en el día, parte alta</span>"
    else:
        nota = textos.get("nota_lluvia")
        if nota is None:
            nota = "suelo saturado" if any(x and x["mm"] >= SATURADO_MM for x in medida) else ""
        titulo = "YA LLOVIÓ EN 7 DÍAS <span>medido en estaciones%s</span>" % (" · " + html.escape(nota) if nota else "")

    creditos = []
    for x in medida:
        if x and x["credito"] not in creditos:
            creditos.append(x["credito"])
    if porcentajes and "IERSE (CC BY-NC-ND 4.0)" not in creditos:
        creditos.insert(0, "IERSE (CC BY-NC-ND 4.0)")     # el pronóstico se calibró con sus estaciones
    corrida = hora_utc(resumen["corrida_modelo_utc"]) if resumen["corrida_modelo_utc"] else None
    pie = "Emitido el %s, %s%s. Datos: Open-Meteo (CC BY 4.0) con ECMWF%s. Marea: tabla de Puerto Ayora (INOCAR) y UHSLC. Islas: IGM." % (
        fecha_corta(emitido.date()), emitido.strftime("%H:%M"),
        "; modelo del %d-%s, %02d UTC" % (corrida.day, MESES[corrida.month - 1], corrida.hour) if corrida else "",
        "".join(", " + c for c in creditos))

    mr = resumen["_marea"]
    reel = {"dia": d["fecha"], "dias": [x["fecha"] for x in resumen["dias"]], "modelo": MODELO,
            "altas": [{"nombre": i["nombre"], "lat": i["alta"][0], "lon": i["alta"][1]} for i in ISLAS],
            "marea": {k: mr[k] for k in ("t0", "paso_min", "pred_cm", "desfase_m", "extremos")}}
    base = AQUI.as_uri() + "/"
    hojas = '<link rel="stylesheet" href="%sreel.css">' % base
    if porcentajes:
        hojas += '<link rel="stylesheet" href="%sreel-porcentajes.css">' % base
    return """<!doctype html><html lang="es"><meta charset="utf-8"><title>Reel del clima · %(dia)s</title>
<script>window.ERRORES=[];addEventListener("error",e=>window.ERRORES.push(String(e.message||e.type)+" "+(e.filename||(e.target&&(e.target.src||e.target.href))||"")));</script>
%(hojas)s
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<div class="top"><div class="k"><span>sosgalapagos.org/clima</span></div>
<span class="chip%(rojo)s">%(chip)s</span>
<h1>%(dia)s</h1>
<div class="hook">%(frase)s</div></div>
<div id="mapa"><div id="reloj"><b>00:00</b><span>MADRUGADA</span></div>
<div id="ley"><div><span>menos lluvia</span><span>más</span></div><canvas width="230" height="1"></canvas></div>
<div id="cred">Modelo %(modelo)s</div></div>
<div id="tira"><h3>¿A QUÉ HORA LLUEVE MÁS EN CADA ISLA?</h3><div id="barras"></div><div id="cab"></div>
<div id="fr"><span>madrugada</span><span>mañana</span><span>tarde</span><span>noche</span></div></div>
<div id="marea"><h3>MAREA <span>%(nota_marea)s</span></h3><svg width="968" height="100"></svg></div>
<div class="tit">%(titulo)s</div>
<div class="isl">%(columnas)s</div>
<div class="f"><b>No es un pronóstico oficial ni una alerta.</b> Estimación de SOS Galápagos · USFQ con modelos; puede fallar. Oficial: INAMHI. Alertas: SNGR, COE y ECU 911. <b>sosgalapagos.org/clima</b>
<small>%(pie)s</small></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>window.REEL=%(reel)s;</script><script src="datos.js"></script><script src="%(base)sislas.js"></script><script src="%(base)sreel.js"></script>
</html>
""" % dict(dia=html.escape(d["dia"]), hojas=hojas, rojo=" rojo" if t.get("rojo") else "", chip=html.escape(t["chip"]),
           frase=html.escape(t["frase"]), modelo=html.escape(resumen["modelo"]), nota_marea=nota_marea, titulo=titulo,
           columnas=columnas, pie=html.escape(pie), reel=json.dumps(reel, ensure_ascii=False), base=base)


# ---------------------------------------------------------------- grabación

def buscar_chrome():
    candidatos = [os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  "/Applications/Chromium.app/Contents/MacOS/Chromium",
                  shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser")]
    for c in candidatos:
        if c and Path(c).exists():
            return c
    fallar("no encuentro Google Chrome: instálalo o pon su ruta en la variable CHROME")


def requisitos():
    for programa in ("node", "ffmpeg", "ffprobe"):
        if not shutil.which(programa):
            fallar("falta %s (en la Mac: brew install %s)" % (programa, "node" if programa == "node" else "ffmpeg"))
    version = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    if int(version.lstrip("v").split(".")[0]) < 22:
        fallar("hace falta Node 22 o posterior (hay %s)" % version)
    return buscar_chrome()


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def grabar(dias, trabajo, modo, chrome):
    """Graba todos los días a la vez, cada uno en su Chrome. Devuelve la carpeta de cuadros de cada día."""
    procesos = []
    for d in dias:
        cuadros = trabajo / "cuadros" / d["slug"]
        if cuadros.exists():
            shutil.rmtree(cuadros)
        registro = open(trabajo / ("grabacion_%s.txt" % d["slug"]), "w")
        entorno = dict(os.environ, CHROME=chrome, LIMITE=os.environ.get("LIMITE", "120" if modo == "prueba" else "900"))
        p = subprocess.Popen(["node", str(AQUI / "grabar.mjs"), (trabajo / "pagina" / (d["slug"] + ".html")).as_uri(),
                              str(cuadros), str(puerto_libre()), modo], stdout=registro, stderr=subprocess.STDOUT, env=entorno)
        procesos.append((d, p, registro, cuadros))
    carpetas = {}
    for d, p, registro, cuadros in procesos:
        codigo = p.wait()
        registro.close()
        if codigo != 0:
            fallar("la grabación del %s falló (código %d):\n%s" % (d["dia"], codigo, (trabajo / ("grabacion_%s.txt" % d["slug"])).read_text()))
        carpetas[d["slug"]] = cuadros
    return carpetas


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + [str(a) for a in args], capture_output=True, text=True)
    if r.returncode != 0:
        fallar("ffmpeg falló: " + r.stderr.strip()[-800:])


def medir(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                        "stream=width,height,r_frame_rate,nb_read_frames,codec_name,pix_fmt:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    s = j["streams"][0]
    return {"ancho": s["width"], "alto": s["height"], "cuadros": int(s["nb_read_frames"]), "fps": s["r_frame_rate"],
            "codec": s["codec_name"], "pix_fmt": s["pix_fmt"], "segundos": round(float(j["format"]["duration"]), 2)}


def cuadro_de(video, segundo, destino):
    ffmpeg("-ss", "%.2f" % segundo, "-i", video, "-frames:v", "1", "-q:v", "3", destino)


def main():
    ap = argparse.ArgumentParser(description="Reel del clima de Galápagos (un video vertical por día).")
    ap.add_argument("--dias", nargs="+", required=True, metavar="AAAA-MM-DD", help="días del reel, en orden; también «hoy» y «mañana» (hora de Galápagos)")
    ap.add_argument("--salida", type=Path, help="carpeta de los videos e imágenes (por defecto, ~/Downloads/sosgalapagos-reel-<primer día>)")
    ap.add_argument("--textos", type=Path, help="JSON con la etiqueta y la frase de cada día (ver textos.ejemplo.json)")
    ap.add_argument("--porcentajes", action="store_true", help="versión con la probabilidad de lluvia fuerte por isla (por defecto no se muestran)")
    ap.add_argument("--solo-datos", action="store_true", help="baja los datos, imprime el resumen y termina")
    ap.add_argument("--prueba", action="store_true", help="una sola imagen por día, a la hora de más lluvia (para revisar antes de grabar)")
    ap.add_argument("--datos", type=Path, help="usa los datos ya bajados en esta carpeta en vez de pedirlos al sitio")
    ap.add_argument("--trabajo", type=Path, help="carpeta de trabajo (por defecto, una temporal nueva)")
    ap.add_argument("--conservar-cuadros", action="store_true", help="no borra los cuadros sueltos al terminar (pesan ≈ 300 MB por día)")
    a = ap.parse_args()

    hoy = dt.datetime.now(GAL).date()
    palabras = {"hoy": hoy, "mañana": hoy + dt.timedelta(days=1), "manana": hoy + dt.timedelta(days=1)}
    try:
        dias = [palabras.get(x.lower()) or dt.date.fromisoformat(x) for x in a.dias]
    except ValueError as e:
        fallar("día mal escrito (%s): usa AAAA-MM-DD" % e)
    if dias != sorted(set(dias)):
        fallar("los días van en orden y sin repetir")
    textos = {}
    if a.textos:
        try:
            textos = json.loads(a.textos.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            fallar("no se pudo leer %s: %s" % (a.textos, e))
        sobran = [k for k in textos if k != "nota_lluvia" and k not in [d.isoformat() for d in dias]]
        if sobran:
            fallar("--textos trae días que no están en --dias: " + ", ".join(sobran))

    trabajo = (a.trabajo or Path(tempfile.mkdtemp(prefix="reel-clima-"))).resolve()
    (trabajo / "pagina").mkdir(parents=True, exist_ok=True)
    carpeta_datos = (a.datos or trabajo / "datos").resolve()
    if not a.datos:
        bajar(carpeta_datos)
    datos = cargar(carpeta_datos)
    resumen = resumir(dias, datos)
    imprimir_resumen(resumen)
    (trabajo / "resumen.json").write_text(json.dumps({k: v for k, v in resumen.items() if not k.startswith("_")}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nCarpeta de trabajo: %s" % trabajo)
    if resumen["problemas"]:
        fallar("los datos no alcanzan para estos días (ver PROBLEMA arriba)")
    if a.solo_datos:
        return

    chrome = requisitos()
    (trabajo / "pagina" / "datos.js").write_text("window.LM=" + json.dumps(datos["lluvia-mapa.json"], ensure_ascii=False) + ";", encoding="utf-8")
    for d in resumen["dias"]:
        (trabajo / "pagina" / (d["slug"] + ".html")).write_text(pagina(d, resumen, textos, a.porcentajes), encoding="utf-8")

    salida = (a.salida or Path.home() / "Downloads" / ("sosgalapagos-reel-" + dias[0].isoformat())).expanduser().resolve()
    revision = trabajo / "revision"
    revision.mkdir(exist_ok=True)
    escala = "scale=1080:1920:flags=lanczos"

    if a.prueba:
        carpetas = grabar(resumen["dias"], trabajo, "prueba", chrome)
        for d in resumen["dias"]:
            ffmpeg("-i", carpetas[d["slug"]] / "prueba.jpg", "-vf", escala, revision / ("prueba_%s.png" % d["slug"]))
            print("Prueba: %s" % (revision / ("prueba_%s.png" % d["slug"])))
        print("\nMira esas imágenes antes de grabar. Nada se escribió en %s." % salida)
        return

    carpetas = grabar(resumen["dias"], trabajo, "todo", chrome)
    salida.mkdir(parents=True, exist_ok=True)
    videos, fallas = [], []
    for d in resumen["dias"]:
        cuadros, video = carpetas[d["slug"]], salida / (d["slug"] + ".mp4")
        ffmpeg("-framerate", "30", "-i", cuadros / "%04d.jpg", "-vf", escala, "-c:v", "libx264", "-preset", "slow",
               "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", video)
        ffmpeg("-i", cuadros / "poster.jpg", "-vf", escala, salida / (d["slug"] + ".png"))
        videos.append(video)
    completo = salida / ("reel-" + "-".join(SLUG[dt.date.fromisoformat(d["fecha"]).weekday()] for d in resumen["dias"]) + ".mp4")
    (trabajo / "lista.txt").write_text("".join("file '%s'\n" % v for v in videos), encoding="utf-8")
    ffmpeg("-f", "concat", "-safe", "0", "-i", trabajo / "lista.txt", "-c", "copy", completo)

    # Comprobación: medidas de cada video y cuadros sueltos sacados de los videos ya hechos, para mirarlos
    print("\nResultado en %s" % salida)
    for d, video in zip(resumen["dias"], videos):
        m = medir(video)
        bien = (m["ancho"], m["alto"], m["cuadros"], m["fps"]) == (1080, 1920, CUADROS_POR_DIA, "30/1")
        if not bien:
            fallas.append(video.name)
        print("  %-22s %d×%d · %d cuadros · %s s · %s  %s" % (video.name, m["ancho"], m["alto"], m["cuadros"], m["segundos"], m["codec"], "bien" if bien else "REVISAR"))
        print("  %-22s imagen fija" % (d["slug"] + ".png"))
        for nombre, seg in (("1-inicio", 0.2), ("2-medio", m["segundos"] / 2), ("3-fin", m["segundos"] - 0.2)):
            cuadro_de(video, seg, revision / ("%s_%s.jpg" % (d["slug"], nombre)))
    m = medir(completo)
    bien = (m["ancho"], m["alto"], m["cuadros"]) == (1080, 1920, CUADROS_POR_DIA * len(videos))
    if not bien:
        fallas.append(completo.name)
    print("  %-22s %d×%d · %d cuadros · %s s  %s" % (completo.name, m["ancho"], m["alto"], m["cuadros"], m["segundos"], "bien" if bien else "REVISAR"))
    for k in range(len(videos)):   # un cuadro del reel completo dentro de cada día: comprueba el orden de los cortes
        cuadro_de(completo, (k + 0.6) * CUADROS_POR_DIA / 30, revision / ("reel_dia%d.jpg" % (k + 1)))
    if not a.conservar_cuadros:
        shutil.rmtree(trabajo / "cuadros", ignore_errors=True)
    print("\nCuadros para revisar (ábrelos y míralos): %s" % revision)
    for f in sorted(revision.glob("*.jpg")):
        print("  " + f.name)
    if fallas:
        fallar("estos videos no tienen las medidas esperadas: " + ", ".join(fallas))


if __name__ == "__main__":
    main()
