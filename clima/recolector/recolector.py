#!/usr/bin/env python3
"""Recolector meteorológico de Galápagos: corre cada 5 minutos (systemd timer).

Baja las mediciones más recientes de cada fuente, las guarda en SQLite (horas en UTC)
y escribe los JSON que lee el dashboard (sosgalapagos.org/clima).

    python3 recolector.py                 # una corrida: todas las fuentes + exportación
    python3 recolector.py --fuentes ierse # solo algunas fuentes
    python3 recolector.py --solo-exportar # regenera los JSON sin descargar
    python3 recolector.py --importar-ierse ../datos/ierse-wsn/crudos   # carga el histórico local
    python3 recolector.py --importar-gsc-historico                     # lluvia diaria GSC desde 2015

Variables normalizadas (columna `variable`):
    lluvia_mm      lluvia caída en el intervalo que termina en ts (5 min en IERSE y GSC)
    lluvia_dia_mm  lluvia del día (histórico diario del GSC; ts = 00:00 hora local en UTC)
    temp_c, hr_pct, presion_hpa, rad_wm2, viento_ms, viento_dir_deg, rafaga_ms,
    nivel_mar_m, vis_km

Dependencias: biblioteca estándar + `websockets` (solo para GSC).
Rutas configurables por entorno: CLIMA_DB, CLIMA_SALIDA, CLIMA_PRIVADO.
Los endpoints de las fuentes NO están en el código: se leen de variables de entorno
(CLIMA_IERSE_API, CLIMA_GSC_WS, CLIMA_GSC_ORIGEN) o del archivo no versionado
privado/fuentes.env (ver fuentes.env.ejemplo). En el servidor: /etc/sosgalapagos-clima/fuentes.env.
"""
import argparse
import asyncio
import csv
import datetime as dt
import gzip
import json
import io
import os
import re
import shutil
import sqlite3
import sys
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:  # con python -I la carpeta del script no está en sys.path
    sys.path.insert(0, str(AQUI))
import danadas  # noqa: E402  (estaciones marcadas como dañadas a mano)


def _cargar_fuentes_env():
    """Lee KEY=VALOR de privado/fuentes.env (o CLIMA_FUENTES_ENV) sin pisar el entorno."""
    ruta = Path(os.environ.get("CLIMA_FUENTES_ENV", AQUI.parent / "privado" / "fuentes.env"))
    if ruta.exists():
        for linea in ruta.read_text().splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_cargar_fuentes_env()


def endpoint(nombre):
    v = os.environ.get(nombre)
    if not v:
        raise RuntimeError(f"Falta {nombre}: defínelo en privado/fuentes.env (ver fuentes.env.ejemplo)")
    return v

DB = Path(os.environ.get("CLIMA_DB", AQUI / "clima.db"))
SALIDA = Path(os.environ.get("CLIMA_SALIDA", AQUI / "salida"))
UA = "sosgalapagos-clima/1.0"
UTC = dt.timezone.utc
GALAPAGOS = dt.timezone(dt.timedelta(hours=-6))
CONTINENTE = dt.timezone(dt.timedelta(hours=-5))

# ---------------------------------------------------------------- base de datos

ESQUEMA = """
CREATE TABLE IF NOT EXISTS obs (
  fuente TEXT NOT NULL, estacion TEXT NOT NULL, variable TEXT NOT NULL,
  ts TEXT NOT NULL,            -- ISO 8601 UTC, 'YYYY-MM-DDTHH:MM:SSZ'
  valor REAL,
  PRIMARY KEY (fuente, estacion, variable, ts)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS obs_ts ON obs(ts);
CREATE TABLE IF NOT EXISTS estaciones (
  fuente TEXT NOT NULL, estacion TEXT NOT NULL, nombre TEXT, isla TEXT,
  lat REAL, lon REAL, altitud_m REAL, operador TEXT, url TEXT, meta TEXT,
  PRIMARY KEY (fuente, estacion)
);
CREATE TABLE IF NOT EXISTS corridas (
  ts TEXT NOT NULL, fuente TEXT NOT NULL, ok INTEGER, registros INTEGER,
  segundos REAL, error TEXT
);
"""


def conectar():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(ESQUEMA)
    return con


def guardar(con, fuente, filas):
    """filas: iterable de (estacion, variable, ts_datetime_aware, valor)."""
    datos = [(fuente, e, v, t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), x) for e, v, t, x in filas]
    con.executemany("INSERT OR REPLACE INTO obs VALUES (?,?,?,?,?)", datos)
    return len(datos)


def estacion(con, fuente, est, nombre, isla, lat, lon, alt=None, operador=None, url=None, **meta):
    con.execute("INSERT OR REPLACE INTO estaciones VALUES (?,?,?,?,?,?,?,?,?,?)",
                (fuente, est, nombre, isla, lat, lon, alt, operador, url, json.dumps(meta, ensure_ascii=False)))


def http_json(url, cuerpo=None, intentos=3, timeout=60):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, data=datos, method="POST" if datos else "GET",
                                         headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(2 * (i + 1))


# ---------------------------------------------------------------- IERSE-WSN (U. del Azuay)

IERSE_RED = "ntw003_glps"
IERSE_VARS = {"RAIN": ("lluvia_mm", 1.0), "Temperature": ("temp_c", 1.0),
              "Humidity": ("hr_pct", 1.0), "Pressure": ("presion_hpa", 0.01)}
IERSE_ALT = {"n_glps01": 861, "n_glps05": 178, "n_glps06": 14, "n_glps09": 416}  # DEM Copernicus 30 m


def ierse_ts(s):  # '2026-10-31T00:02:11.000', hora de Galápagos (verificado contra la hora actual)
    return dt.datetime.fromisoformat(s[:19]).replace(tzinfo=GALAPAGOS)


def fuente_ierse(con):
    api = endpoint("CLIMA_IERSE_API")
    nodos = http_json(api + "/oper_nodes", {"req_netw": IERSE_RED})
    for n in nodos:
        estacion(con, "ierse", n["node_id"], n["node_name"], "Santa Cruz", n["node_lat"], n["node_long"],
                 IERSE_ALT.get(n["node_id"]), "IERSE-WSN")
    ahora = dt.datetime.now(GALAPAGOS)
    # Desde el día del último dato guardado (máx. 3 días atrás), para rellenar después de un corte
    ult = con.execute("SELECT MAX(ts) FROM obs WHERE fuente='ierse'").fetchone()[0]
    desde = ahora.date() - dt.timedelta(days=3)
    if ult:
        desde = max(desde, dt.datetime.fromisoformat(ult.replace("Z", "+00:00")).astimezone(GALAPAGOS).date())
    if ahora.hour < 2:
        desde = min(desde, ahora.date() - dt.timedelta(days=1))
    dias = [desde + dt.timedelta(days=i) for i in range((ahora.date() - desde).days + 1)]
    filas = []
    for d in dias:
        for var, (nombre, f) in IERSE_VARS.items():
            for n in nodos:
                serie = http_json(api + "/node_data", {"req_var": var, "req_date": d.isoformat(),
                                  "req_node": n["node_id"], "req_netw": IERSE_RED, "pub_query": "1"})
                filas += [(n["node_id"], nombre, ierse_ts(p["timestamp"]),
                           None if p["sensor_value"] is None else p["sensor_value"] * f) for p in serie]
    return guardar(con, "ierse", filas)


def importar_ierse(con, carpeta):
    n = 0
    for a in sorted(Path(carpeta).glob("*/*.csv.gz")):
        with gzip.open(a, "rt") as f:
            filas = [(r["estacion_id"], IERSE_VARS[r["variable"]][0], ierse_ts(r["fecha_hora_local"]),
                      float(r["valor"]) * IERSE_VARS[r["variable"]][1] if r["valor"] else None)
                     for r in csv.DictReader(f) if r["variable"] in IERSE_VARS]
        n += guardar(con, "ierse", filas)
    con.commit()
    print(f"IERSE: {n} registros importados")


# ---------------------------------------------------------------- GSC · USFQ (San Cristóbal)
# App Shiny: no hay API. Se abre una sesión por websocket, como un navegador, y se leen
# los gráficos plotly de «Previous 24 hours / 5 minute increments» para cada variable.

GSC_VARS = {"Rain_Tot": "lluvia_mm", "Air_Temp": "temp_c", "SR": "rad_wm2", "RH": "hr_pct"}
GSC_EST = {  # id: (nombre, lat, lon, altitud) — del mapa de la app
    # también son estaciones del INAMHI: se muestran los dos nombres (GSC · nombre y código del INAMHI)
    "merceditas": ("Merceditas · USFQ - SAN CRISTOBAL EN LAS MERCEDITAS (M5300)", -0.889712, -89.442020, 100),
    "junco": ("El Junco · USFQ - SAN CRISTOBAL EN EL JUNCO (M5301)", -0.896537, -89.481624, 548),
    "cerro_alto": ("Cerro Alto · USFQ - SAN CRISTOBAL EN CERRO ALTO (M5302)", -0.887049, -89.530986, 517),
    "mirador": ("El Mirador · USFQ - SAN CRISTOBAL EN EL MIRADOR (M5303)", -0.886248, -89.539587, 387),
    "gsc": ("GSC (Puerto Baquerizo Moreno)", -0.895653, -89.608702, 20),
}


def gsc_id(nombre):
    k = nombre.lower().replace(" ", "_").replace("el_", "")
    return {"cerro_alto": "cerro_alto", "junco": "junco", "mirador": "mirador",
            "merceditas": "merceditas", "gsc": "gsc"}.get(k, k)


def gsc_ts(s):  # '2026-11-01T14:05:00Z': la «Z» es falsa; es hora continental UTC−5 (verificado)
    return dt.datetime.fromisoformat(s[:19]).replace(tzinfo=CONTINENTE)


def gsc_init(extra=None):
    from urllib.parse import urlparse
    host = urlparse(endpoint("CLIMA_GSC_ORIGEN")).hostname
    d = {"variable_selection_xh": "Rain_Tot", "Variable_selection_xd": "Rain_Tot", "var_hist": "Precip",
         "time_hist": "diario", "ldas_var": "streamflow", "tabset1": "tab-4532-2",
         ".clientdata_pixelratio": 1, ".clientdata_url_protocol": "https:",
         ".clientdata_url_hostname": host, ".clientdata_url_port": "",
         ".clientdata_url_pathname": "/", ".clientdata_url_search": "", ".clientdata_url_hash_initial": "",
         ".clientdata_url_hash": "", ".clientdata_singletons": "", ".clientdata_allowDataUriScheme": True}
    for o in ("Time_series_xh", "Time_series_xd", "ts_hist", "mymap"):
        d[f".clientdata_output_{o}_width"] = 1000
        d[f".clientdata_output_{o}_height"] = 400
        d[f".clientdata_output_{o}_hidden"] = o != "Time_series_xh"
    d.update(extra or {})
    return d


async def gsc_sesion(pasos, espera=45):
    """pasos: lista de (datos_update | None, salida_esperada). Devuelve {salida: valor} por paso."""
    import websockets
    res = []
    async with websockets.connect(endpoint("CLIMA_GSC_WS"), origin=endpoint("CLIMA_GSC_ORIGEN"), max_size=2**28,
                                  open_timeout=30, user_agent_header=UA) as ws:
        for i, (datos, salida) in enumerate(pasos):
            await ws.send(json.dumps({"method": "init" if i == 0 else "update", "data": datos}))
            fin = time.time() + espera
            while True:
                j = json.loads(await asyncio.wait_for(ws.recv(), timeout=max(1, fin - time.time())))
                if salida in (j.get("values") or {}):
                    res.append(j["values"][salida])
                    break
    return res


def gsc_series(widget):
    for d in widget["x"]["data"]:
        for t in d.get("data", []):
            if t.get("x"):
                yield gsc_id(t.get("name", "")), t["x"], t["y"]


def fuente_gsc(con):
    for k, (nom, lat, lon, alt) in GSC_EST.items():
        estacion(con, "gsc", k, nom, "San Cristóbal", lat, lon, alt, "GSC-USFQ")
    vars_ = list(GSC_VARS)
    pasos = [(gsc_init({"variable_selection_xh": vars_[0]}), "Time_series_xh")]
    pasos += [({"variable_selection_xh": v}, "Time_series_xh") for v in vars_[1:]]
    widgets = asyncio.run(gsc_sesion(pasos))
    filas = []
    for v, w in zip(vars_, widgets):
        for est, xs, ys in gsc_series(w):
            filas += [(est, GSC_VARS[v], gsc_ts(x), y) for x, y in zip(xs, ys) if y is not None]
    return guardar(con, "gsc", filas)


def importar_gsc_historico(con):
    """Lluvia diaria desde 2015 (pestaña «Historical records»)."""
    pasos = [(gsc_init({"tabset1": "tab-4532-3", "filter_hist": ["2015-01-01", dt.date.today().isoformat()],
                        ".clientdata_output_ts_hist_hidden": False, ".clientdata_output_Time_series_xh_hidden": True}),
              "ts_hist")]
    w = asyncio.run(gsc_sesion(pasos, espera=120))[0]
    filas = []
    for est, xs, ys in gsc_series(w):
        filas += [(est, "lluvia_dia_mm", dt.datetime.fromisoformat(x[:10]).replace(tzinfo=CONTINENTE), y)
                  for x, y in zip(xs, ys) if y is not None]
    n = guardar(con, "gsc", filas)
    con.commit()
    print(f"GSC histórico: {n} días-estación")


# ---------------------------------------------------------------- registro de fuentes

FUENTES = {"ierse": fuente_ierse, "gsc": fuente_gsc}
if __name__ == "__main__":  # fuentes adicionales (INAMHI, IOC, METAR); importan este módulo como «recolector»
    sys.modules.setdefault("recolector", sys.modules["__main__"])
    from fuentes_extra import FUENTES_EXTRA  # noqa: E402
    FUENTES.update(FUENTES_EXTRA)


def correr(con, nombres):
    for nombre in nombres:
        t0 = time.time()
        try:
            n = FUENTES[nombre](con)
            con.execute("INSERT INTO corridas VALUES (?,?,?,?,?,?)",
                        (ahora_utc(), nombre, 1, n, round(time.time() - t0, 1), None))
            print(f"{nombre}: {n} registros ({time.time() - t0:.1f} s)")
        except Exception as e:  # una fuente caída no detiene a las demás
            con.execute("INSERT INTO corridas VALUES (?,?,?,?,?,?)",
                        (ahora_utc(), nombre, 0, 0, round(time.time() - t0, 1), f"{type(e).__name__}: {e}"[:500]))
            print(f"{nombre}: ERROR {e}", file=sys.stderr)
            traceback.print_exc()
        con.commit()


def ahora_utc():
    return dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- exportación para el dashboard
# Lo público (CLIMA_SALIDA) son los JSON agregados que usa la página, sin URLs de las fuentes, y
# desde el 12-nov-2026 las descargas de datos crudos de estaciones (SALIDA/descargas, cada hora).
# Copia completa (con modelos y satélite) en CLIMA_PRIVADO/csv, que no se publica.

PRIVADO = Path(os.environ.get("CLIMA_PRIVADO", AQUI / "privado"))
OPERADOR = {"ierse": "IERSE-WSN", "gsc": "GSC-USFQ", "inamhi": "INAMHI", "ioc": "IOC", "metar": "Aeropuertos (METAR)",
            "weatherlink": "WeatherLink", "tempest": "Tempest", "ambient": "Ambient Weather", "wunderground": "Weather Underground", "mar_modelo": "Modelo de nivel del mar",
            "pronostico": "Pronóstico (modelos)"}
EVENTOS = [  # momentos de referencia para comparar (horas UTC)
    {"id": "inundacion-2026-10-30", "nombre": "Inundación La Cascada (30–31 oct 2026)",
     "desde": "2026-10-30T06:00:00Z", "hasta": "2026-11-01T06:00:00Z"},
]
# Red DARWIN-Rain (Philipps-Universität Marburg, con la Fundación Charles Darwin y la Universidad de
# Cuenca): estaciones automáticas con pluviómetro, sin transmisión en tiempo real (los datos se suben
# con semanas de retraso y su descarga requiere un acuerdo). Se publican nombre, ubicación y cita
# (autorizado por Julián el 12-nov-2026) para que se sepa que existen; no hay serie. «hasta» es el
# último dato publicado que vimos en sus metadatos (12-nov-2026). Cerro Crocker, Santa Rosa y
# Militar no se repiten: son los mismos sitios que transmiten en vivo por IERSE-WSN.
DARWIN_RAIN = [  # (código, nombre, isla, lat, lon, altitud, hasta, nota)
    ("puerto_baquerizo", "Puerto Baquerizo Moreno (DARWIN)", "San Cristóbal", -0.9031, -89.612, 25, "2026-10-29", None),
    ("galapaguera", "La Galapaguera", "San Cristóbal", -0.914, -89.437, 165, "2026-10-10", None),
    ("el_junco", "El Junco (DARWIN)", "San Cristóbal", -0.8938, -89.480, 684, "2026-05-25", None),
    ("sierra_negra", "Sierra Negra", "Isabela", -0.8484, -91.131, 1145, "2026-10-28", None),
    ("cueva_sucre", "Cueva de Sucre", "Isabela", -0.8431, -91.028, 382, "2026-10-19", None),
    ("puerto_villamil", "Puerto Villamil (El Chapín)", "Isabela", -0.9462, -90.974, 22, "2026-01-14", None),
    ("wittmer", "Wittmer (Puerto Velasco Ibarra)", "Floreana", -1.2757, -90.4875, None, "2026-10-01",
     "ubicación aproximada: la red no publica coordenadas"),
    ("minas_rojas", "Minas Rojas", "Santa Cruz", -0.6186, -90.367, 619, "2026-05-20", None),
    ("puerto_ayora_fcd", "Puerto Ayora (FCD)", "Santa Cruz", -0.7438, -90.302, 4, "2026-01-12", None),
]


PUBLICOS = {"estado.json", "horario.json", "diario.json", "pronostico.json", "satelite.json"}


def escribir(ruta, obj):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    os.replace(tmp, ruta)


def exportar(con):
    ahora = dt.datetime.now(UTC)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    hace = lambda **k: iso(ahora - dt.timedelta(**k))  # noqa: E731

    ests = [dict(zip(("fuente", "estacion", "nombre", "isla", "lat", "lon", "altitud_m"), r))
            for r in con.execute("SELECT fuente, estacion, nombre, isla, lat, lon, altitud_m "
                                 "FROM estaciones ORDER BY isla, altitud_m DESC")]
    for e in ests:
        k = (e["fuente"], e["estacion"])
        e["operador"] = OPERADOR.get(e["fuente"], e["fuente"])
        e["ultimo"] = con.execute("SELECT MAX(ts) FROM obs WHERE fuente=? AND estacion=? "
                                  "AND variable!='lluvia_dia_mm'", k).fetchone()[0]
        e["actual"] = {v: (round(x, 2) if x is not None else None) for v, x in con.execute(
            "SELECT variable, valor FROM obs o WHERE fuente=? AND estacion=? AND variable!='lluvia_dia_mm' AND ts=("
            " SELECT MAX(ts) FROM obs WHERE fuente=o.fuente AND estacion=o.estacion AND variable=o.variable"
            " AND ts>=?) GROUP BY variable", (*k, hace(hours=3)))}
        e["lluvia"] = {}
        marca = danadas.publica(f"{e['fuente']}/{e['estacion']}")
        if marca:  # estación dañada: no se publica su lluvia (los crudos siguen en la base)
            e["danada"] = marca
            for v in marca["variables"]:
                e["actual"].pop(v, None)
            if "lluvia_mm" in marca["variables"]:
                e["lluvia"] = {k: None for k in ("1h", "3h", "6h", "24h", "72h", "7d")}
                continue
        for etiqueta, horas in (("1h", 1), ("3h", 3), ("6h", 6), ("24h", 24), ("72h", 72), ("7d", 168)):
            s = con.execute("SELECT SUM(valor), COUNT(*) FROM obs WHERE fuente=? AND estacion=? "
                            "AND variable='lluvia_mm' AND ts>?", (*k, hace(hours=horas))).fetchone()
            e["lluvia"][etiqueta] = None if not s[1] else round(s[0], 1)
    ests += [{"fuente": "darwin", "estacion": c, "nombre": n, "isla": i, "lat": la, "lon": lo, "altitud_m": a,
              "operador": "DARWIN-Rain", "ultimo": None, "actual": {}, "lluvia": {}, "en_vivo": False,
              "datos_hasta": h, **({"nota": nota} if nota else {})}
             for c, n, i, la, lo, a, h, nota in DARWIN_RAIN]
    corr = {f: dict(zip(("ts", "ok", "registros", "segundos"), r)) for f, *r in con.execute(
        "SELECT fuente, ts, ok, registros, segundos FROM corridas c WHERE ts=("
        "SELECT MAX(ts) FROM corridas WHERE fuente=c.fuente)")}
    corr = {OPERADOR.get(f, f): v for f, v in corr.items()}
    try:
        import inundacion
        riesgo = inundacion.calcular(con, ahora)
    except Exception as e:  # el nivel de inundación nunca debe tumbar la exportación
        traceback.print_exc()
        riesgo = {"error": str(e)[:200]}
    try:
        import mareas
        marea = mareas.calcular(con, ahora)
    except Exception as e:
        traceback.print_exc()
        marea = {"error": str(e)[:200]}
    try:  # pronóstico de modelos (lo baja fuente_pronostico; aquí solo se resume)
        import pronostico
        pron = pronostico.exportar(ahora)
        escribir(SALIDA / "pronostico.json", pron)
    except Exception as e:
        traceback.print_exc()
        pron = {"error": str(e)[:200]}
    try:  # satélite GOES-19: lo escribe satelite/colector.py (otro proceso y otro timer)
        sat = json.loads((SALIDA / "satelite.json").read_text())
    except (OSError, ValueError):
        sat = None
    # El pronóstico y el satélite van también dentro de estado.json: Caddy solo deja pasar
    # estado/horario/diario (Caddyfile del repo mayait/sosgalapagos).
    escribir(SALIDA / "estado.json", {"generado": iso(ahora), "estaciones": ests, "fuentes": corr,
                                      "eventos": EVENTOS, "inundacion": riesgo, "mareas": marea, "pronostico": pron,
                                      "satelite": sat})

    # Historia horaria completa en un eje común (horas UTC): lluvia (suma) y temperatura (media).
    # null = sin registros en esa hora (corte de transmisión o fuera del período de la estación).
    ini = con.execute("SELECT MIN(ts) FROM obs WHERE variable IN ('lluvia_mm','temp_c') AND fuente IN ('ierse','gsc')").fetchone()[0]
    hor = {}
    horas_n = 0
    if ini:
        h0 = dt.datetime.fromisoformat(ini[:13] + ":00:00+00:00")
        horas_n = int((ahora - h0).total_seconds() // 3600) + 1
        for f, e, v, h, x in con.execute(
                "SELECT fuente, estacion, variable, substr(ts,1,13), "
                "CASE WHEN variable='lluvia_mm' THEN SUM(valor) ELSE AVG(valor) END "
                "FROM obs WHERE variable IN ('lluvia_mm','temp_c','nivel_mar_m') GROUP BY 1,2,3,4"):
            i = int((dt.datetime.fromisoformat(h + ":00:00+00:00") - h0).total_seconds() // 3600)
            if 0 <= i < horas_n:
                s = hor.setdefault(f"{f}/{e}", {}).setdefault(v, [None] * horas_n)
                if danadas.danada(f"{f}/{e}", v, dt.datetime.fromisoformat(h + ":59:59+00:00")):
                    continue  # hora con datos de una estación dañada: queda en null
                s[i] = None if x is None else round(x, 1)
    escribir(SALIDA / "horario.json", {"generado": iso(ahora), "inicio": ini[:13] + ":00:00Z" if ini else None,
                                       "horas": horas_n, "series": hor})

    # Lluvia diaria (día de Galápagos, UTC−6): suma de los registros si la estación
    # transmitió al menos 20 h ese día; si no, el diario histórico de la fuente (GSC desde 2015).
    dia = {}
    for f, e, d, ll, hs in con.execute(
            "SELECT fuente, estacion, date(ts, '-6 hours') d, SUM(valor), COUNT(DISTINCT substr(ts,1,13)) "
            "FROM obs WHERE variable='lluvia_mm' GROUP BY 1,2,3"):
        dia.setdefault(f"{f}/{e}", {})[d] = (round(ll, 1), hs)
    for f, e, d, ll in con.execute("SELECT fuente, estacion, date(ts, '-5 hours'), valor FROM obs "
                                   "WHERE variable='lluvia_dia_mm'"):
        s = dia.setdefault(f"{f}/{e}", {})
        if d not in s or s[d][1] < 20:
            s[d] = (round(ll, 1), 24)
    for k, s in dia.items():  # estaciones dañadas: sin lluvia diaria desde el día en que empezó la falla
        x = danadas.danada(k, "lluvia_mm")
        if x:
            d0 = (x["desde_dt"] - dt.timedelta(hours=6)).date().isoformat()
            for d in [d for d in s if d >= d0]:
                s[d] = (None, 0)
    diario = {}
    for k, s in dia.items():
        fechas = sorted(s)
        d0 = dt.date.fromisoformat(fechas[0])
        n = (dt.date.fromisoformat(fechas[-1]) - d0).days + 1
        ll = [None] * n
        cob = [0] * n
        for d, (x, hs) in s.items():
            i = (dt.date.fromisoformat(d) - d0).days
            ll[i], cob[i] = x, min(hs, 24)
        diario[k] = {"inicio": fechas[0], "lluvia": ll, "horas": cob}
    try:
        import estacionalidad
        estac = estacionalidad.calcular(con)
    except Exception as e:
        traceback.print_exc()
        estac = {"error": str(e)[:200]}
    escribir(SALIDA / "diario.json", {"generado": iso(ahora), "diario": diario, "estacionalidad": estac})

    for viejo in SALIDA.iterdir():  # nada más que lo público queda en la carpeta servida
        if viejo.is_file() and viejo.name not in PUBLICOS:
            viejo.unlink()


LEEME_DESCARGA = """Datos meteorológicos de Galápagos recopilados por SOS Galápagos
Actualizado: {generado} (se regenera cada hora)
https://sosgalapagos.org/clima/

DATOS CRUDOS: cada valor está tal como llegó de su fuente, sin control de calidad ni
correcciones. Al usarlos, cite a cada operador (abajo) y respete su licencia. La regla de
nivel de inundación de la página filtra estaciones; estos archivos no.
{danadas}
CÓMO CITAR
- IERSE-WSN (Santa Cruz). Licencia CC BY-NC-ND 4.0 (atribución, no comercial, sin
  obras derivadas): Orellana-Samaniego, M.L., Cabrera-Lituma, A., Omar, D., Célleri, R.,
  Bendix, J., y Ballari, D. 2023. Proyecto DARWIN. Versión 2023.1. IERSE, Universidad del
  Azuay. <http://opengeodata.uazuay.edu.ec/EstudioDarwin/>, fecha de acceso.
- GSC-USFQ (San Cristóbal): Universidad San Francisco de Quito; Galapagos Science Center.
  (2026). Weather Data - GSC. Recuperado el <fecha> de https://weathergsc.usfq.edu.ec/
- INAMHI, IOC (mareógrafos), METAR de los aeropuertos: citar al operador.
- Estaciones particulares (WeatherLink, Tempest, Ambient Weather, Weather Underground):
  datos de sus dueños, publicados con su panel público; citar la estación y la plataforma.

ARCHIVOS
clima_galapagos_AAAA-MM.zip      todas las observaciones de estaciones del mes (un CSV dentro)
    ts_utc     hora en UTC (Galápagos = UTC-6)
    fuente     ierse | gsc | inamhi | ioc | metar | weatherlink | tempest | ambient | wunderground
    estacion   identificador (ver estaciones.csv)
    variable   lluvia_mm (lluvia del intervalo de ~5 min que empieza o termina en ts; 1 h en
               las filas con segundos :30: respaldo horario del INAMHI y de Erna),
               lluvia_dia_acum_mm (acumulado del día que da la estación), temp_c, hr_pct,
               presion_hpa, rad_wm2, viento_ms, nivel_mar_m, lluvia_codigo (METAR: 0 nada,
               1 débil, 2 moderada, 3 fuerte o tormenta)
    valor      tal como llega de la fuente
historico_lluvia_diaria.csv      lluvia diaria del GSC desde 2015 (fecha local)
estaciones.csv                   nombre, isla, coordenadas, altitud y operador
indice.json                      lista de archivos con tamaño y fecha

Cuidado: durante los cortes de transmisión la lluvia no se mide (no queda en cero ni se
acumula después). Ver la cobertura antes de sumar.
"""


def exportar_csv(con, meses=2):
    """Archivo PRIVADO (no se publica): un CSV.gz por mes con todas las observaciones."""
    hoy = dt.date.today().replace(day=1)
    destino = PRIVADO / "csv"
    destino.mkdir(parents=True, exist_ok=True)
    for (mes,) in con.execute("SELECT DISTINCT substr(ts,1,7) FROM obs WHERE variable!='lluvia_dia_mm'").fetchall():
        ruta = destino / f"clima_galapagos_{mes}.csv.gz"
        if ruta.exists() and mes < (hoy - dt.timedelta(days=31 * meses)).strftime("%Y-%m"):
            continue
        tmp = ruta.with_suffix(".tmp")
        with gzip.open(tmp, "wt", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts_utc", "fuente", "estacion", "variable", "valor"])
            w.writerows(con.execute("SELECT ts, fuente, estacion, variable, valor FROM obs WHERE substr(ts,1,7)=? "
                                    "AND variable!='lluvia_dia_mm' ORDER BY ts, fuente, estacion, variable", (mes,)))
        os.replace(tmp, ruta)
    with open(destino / "historico_lluvia_diaria.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha_local", "fuente", "estacion", "lluvia_mm"])
        w.writerows(con.execute("SELECT date(ts, '-5 hours'), fuente, estacion, valor FROM obs "
                                "WHERE variable='lluvia_dia_mm' ORDER BY 1, 2, 3"))
    with open(destino / "estaciones.csv", "w", newline="") as f:
        w = csv.writer(f)
        cur = con.execute("SELECT fuente, estacion, nombre, isla, lat, lon, altitud_m, operador FROM estaciones "
                          "ORDER BY fuente, estacion")
        w.writerow([c[0] for c in cur.description])
        w.writerows(cur)
    exportar_descargas(con)


FUENTES_ESTACION = ("ierse", "gsc", "inamhi", "ioc", "metar", "weatherlink", "tempest", "ambient", "wunderground")


def exportar_descargas(con, meses=2):
    """Descargas PÚBLICAS de datos crudos (desde el 12-nov-2026): SALIDA/descargas/, que Caddy sirve
    en /clima/datos/descargas/. Solo observaciones de estaciones (no modelos ni satélite)."""
    hoy = dt.date.today().replace(day=1)
    destino = SALIDA / "descargas"
    destino.mkdir(parents=True, exist_ok=True)
    marcas = ",".join("?" * len(FUENTES_ESTACION))
    for (mes,) in con.execute(f"SELECT DISTINCT substr(ts,1,7) FROM obs WHERE fuente IN ({marcas}) "
                              "AND variable!='lluvia_dia_mm'", FUENTES_ESTACION).fetchall():
        # ZIP con un CSV dentro: se abre con doble clic en Windows, macOS y Linux (el .gz no siempre)
        ruta = destino / f"clima_galapagos_{mes}.zip"
        if ruta.exists() and mes < (hoy - dt.timedelta(days=31 * meses)).strftime("%Y-%m"):
            continue
        tmp = ruta.with_name(f".{ruta.name}.{os.getpid()}.tmp")
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z, \
                z.open(f"clima_galapagos_{mes}.csv", "w") as crudo, \
                io.TextIOWrapper(crudo, encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts_utc", "fuente", "estacion", "variable", "valor"])
            w.writerows(con.execute(f"SELECT ts, fuente, estacion, variable, valor FROM obs WHERE substr(ts,1,7)=? "
                                    f"AND fuente IN ({marcas}) AND variable!='lluvia_dia_mm' "
                                    "ORDER BY ts, fuente, estacion, variable", (mes, *FUENTES_ESTACION)))
        os.replace(tmp, ruta)
    for nombre in ("historico_lluvia_diaria.csv", "estaciones.csv"):
        shutil.copyfile(PRIVADO / "csv" / nombre, destino / nombre)
    marcadas = [f"- {k}: {x.get('motivo', 'dañada')} (desde {x['desde']}; variables: {', '.join(x['variables'])})."
                for k, x in danadas.DANADAS.items()]
    aviso = ("\nESTACIONES MARCADAS COMO DAÑADAS (sus datos siguen aquí, pero la página no los usa):\n"
             + "\n".join(marcadas) + "\n") if marcadas else ""
    texto = LEEME_DESCARGA.format(generado=ahora_utc(), danadas=aviso)
    (PRIVADO / "LEEME.txt").write_text(texto)
    (destino / "LEEME.txt").write_text(texto)
    for viejo in destino.glob("*.csv.gz"):  # formato anterior (hasta el 12-nov-2026)
        viejo.unlink()
    archivos = sorted(p for p in destino.iterdir() if p.is_file() and not p.name.startswith(".")
                      and p.suffix in (".zip", ".csv", ".txt"))
    escribir(destino / "indice.json", {"generado": ahora_utc(), "archivos": [
        {"archivo": p.name, "bytes": p.stat().st_size,
         "actualizado": dt.datetime.fromtimestamp(p.stat().st_mtime, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
        for p in archivos]})


# ---------------------------------------------------------------- puente (fuentes que el servidor no alcanza)
# IERSE bloquea las IP del servidor (EE. UU.). Una máquina en Ecuador corre la fuente y manda
# las filas al servidor:  recolector.py --emitir ierse | ssh servidor recolector.py --recibir

def emitir(con, fuente, horas):
    corte = (dt.datetime.now(UTC) - dt.timedelta(hours=horas)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = sys.stdout
    for r in con.execute("SELECT * FROM estaciones WHERE fuente=?", (fuente,)):
        out.write(json.dumps(["E", *r], ensure_ascii=False) + "\n")
    for r in con.execute("SELECT * FROM corridas WHERE fuente=? AND ts>=? ", (fuente, corte)):
        out.write(json.dumps(["C", *r], ensure_ascii=False) + "\n")
    for r in con.execute("SELECT * FROM obs WHERE fuente=? AND ts>=?", (fuente, corte)):
        out.write(json.dumps(["O", *r], ensure_ascii=False) + "\n")


# El puente (llave restringida desde la Mac) solo trae IERSE. Todo lo demás se
# rechaza: si la llave se filtra, no se puede falsear la lluvia de otras fuentes
# ni meter HTML en los nombres que publica estado.json.
PUENTE = {"ierse"}
_ID = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
_TS = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def _texto(x, n=120):
    return x is None or (isinstance(x, str) and len(x) <= n and not any(c in x for c in "<>`"))


def _num(x):
    return x is None or (isinstance(x, (int, float)) and not isinstance(x, bool))


def _fila_valida(t, r):
    if t == "E" and len(r) == 10:
        return (r[0] in PUENTE and isinstance(r[1], str) and _ID.match(r[1]) and _texto(r[2]) and _texto(r[3])
                and all(_num(v) for v in r[4:7]) and _texto(r[7]) and r[8] is None
                and (r[9] is None or (isinstance(r[9], str) and len(r[9]) <= 2000)))
    if t == "C" and len(r) == 6:
        return (isinstance(r[0], str) and _TS.match(r[0]) and r[1] in PUENTE and _num(r[2]) and _num(r[3])
                and _num(r[4]) and (r[5] is None or (isinstance(r[5], str) and len(r[5]) <= 500)))
    if t == "O" and len(r) == 5:
        return (r[0] in PUENTE and isinstance(r[1], str) and _ID.match(r[1]) and isinstance(r[2], str) and _ID.match(r[2])
                and isinstance(r[3], str) and _TS.match(r[3]) and _num(r[4]))
    return False


def recibir(con):
    n = rechazadas = 0
    for i, linea in enumerate(sys.stdin):
        if i >= 200_000:
            rechazadas += 1
            break
        try:
            t, *r = json.loads(linea)
        except (ValueError, TypeError):
            rechazadas += 1
            continue
        if not _fila_valida(t, r):
            rechazadas += 1
            continue
        if t == "E":
            con.execute("INSERT OR REPLACE INTO estaciones VALUES (?,?,?,?,?,?,?,?,?,?)", r)
        elif t == "C":
            if not con.execute("SELECT 1 FROM corridas WHERE ts=? AND fuente=?", r[:2]).fetchone():
                con.execute("INSERT INTO corridas VALUES (?,?,?,?,?,?)", r)
        else:
            con.execute("INSERT OR REPLACE INTO obs VALUES (?,?,?,?,?)", r)
            n += 1
    con.commit()
    print(f"recibidos {n} registros" + (f", {rechazadas} filas rechazadas" if rechazadas else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuentes", nargs="*", help="por defecto, CLIMA_FUENTES o todas")
    ap.add_argument("--solo-exportar", action="store_true")
    ap.add_argument("--csv", action="store_true", help="regenera también el archivo CSV privado")
    ap.add_argument("--importar-ierse")
    ap.add_argument("--importar-gsc-historico", action="store_true")
    ap.add_argument("--importar-inamhi", metavar="JSON", help="historial horario archivado del INAMHI")
    ap.add_argument("--tempest-desde", metavar="AAAA-MM-DD", help="carga histórica de Tempest desde esa fecha (UTC)")
    ap.add_argument("--ambient-desde", metavar="AAAA-MM-DD", help="carga histórica de Ambient Weather desde esa fecha (UTC)")
    ap.add_argument("--emitir", metavar="FUENTE")
    ap.add_argument("--horas", type=int, default=6)
    ap.add_argument("--recibir", action="store_true")
    a = ap.parse_args()
    con = conectar()
    if a.emitir:
        return emitir(con, a.emitir, a.horas)
    if a.recibir:
        recibir(con)
        return exportar(con)
    if a.importar_ierse:
        importar_ierse(con, a.importar_ierse)
    if a.importar_gsc_historico:
        importar_gsc_historico(con)
    if a.importar_inamhi:
        from fuentes_extra import inamhi_historial
        print(f"INAMHI: {inamhi_historial(con, archivo=a.importar_inamhi)} registros importados")
        con.commit()
    if a.tempest_desde:
        from fuentes_extra import tempest_historico
        desde = dt.datetime.fromisoformat(a.tempest_desde).replace(tzinfo=UTC)
        print(f"Tempest: {tempest_historico(con, desde)} registros importados")
    if a.ambient_desde:
        from fuentes_extra import ambient_historico
        desde = dt.datetime.fromisoformat(a.ambient_desde).replace(tzinfo=UTC)
        print(f"Ambient Weather: {ambient_historico(con, desde)} registros importados")
    if not (a.solo_exportar or a.importar_ierse or a.importar_gsc_historico or a.importar_inamhi or a.tempest_desde
            or a.ambient_desde):
        env = [x for x in os.environ.get("CLIMA_FUENTES", "").split(",") if x]
        correr(con, a.fuentes or env or list(FUENTES))
    exportar(con)
    if a.csv:
        exportar_csv(con)


if __name__ == "__main__":
    main()
