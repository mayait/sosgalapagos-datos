"""Fuentes adicionales del recolector: INAMHI, mareógrafos IOC y METAR de los aeropuertos.

Los endpoints se leen del entorno o de privado/fuentes.env (CLIMA_INAMHI_API, CLIMA_IOC_API,
CLIMA_METAR_API); no se versionan.
"""
import datetime as dt
import json
import statistics
import urllib.parse

from recolector import CONTINENTE, UTC, endpoint, estacion, guardar, http_json

# ---------------------------------------------------------------- INAMHI (estaciones automáticas)
# tiempo-real-5min/{lat}/{lon}: lluvia de cada 5 min de las últimas ~6 h de la estación más cercana
# (etiqueta = inicio del intervalo, hora continental UTC−5) y la serie de temperatura alineada.
# historial: lluvia y temperatura horarias (etiqueta = inicio de la hora, UTC−5), 90 días.
INAMHI_EST = {  # código: (consulta lat, lon, nombre, isla, lat, lon, altitud)
    "M0191": (-0.745, -90.315, "Puerto Ayora (Charles Darwin)", "Santa Cruz", -0.743056, -90.3025, 6),
    "M0221": (-0.901, -89.611, "Puerto Baquerizo Moreno", "San Cristóbal", -0.904058, -89.614308, 6),
}
HORARIO_SEG = 30  # las filas horarias se guardan a las HH:30:30 para no chocar con las de 5 min


def _hora_ts(fecha, minutos):
    return dt.datetime.fromisoformat(fecha).replace(tzinfo=CONTINENTE) + dt.timedelta(minutes=minutos)


def fuente_inamhi(con):
    api = endpoint("CLIMA_INAMHI_API")
    filas, horas_5min = [], set()
    for cod, (qlat, qlon, nom, isla, lat, lon, alt) in INAMHI_EST.items():
        estacion(con, "inamhi", cod, nom, isla, lat, lon, alt, "INAMHI")
        d = http_json(f"{api}/tiempo-real-5min/{qlat}/{qlon}")
        if not d.get("ok") or "intervalo_minutos" not in d:
            raise ValueError(f"respuesta inesperada para {cod}: {str(d)[:200]}")
        paso, ini = d["intervalo_minutos"], d["inicio"]
        e = next((x for x in d.get("estaciones", []) if x.get("codigo") == cod), None)
        if e:
            for i, v in enumerate(e.get("mm") or []):
                if v is not None:
                    t = _hora_ts(d["fecha"], ini + paso * i)
                    filas.append((cod, "lluvia_mm", t, float(v)))
                    horas_5min.add((cod, t.astimezone(UTC).strftime("%Y-%m-%dT%H")))
        te = next((x for x in (d.get("temperatura") or {}).get("estaciones", []) if x.get("codigo") == cod), None)
        if te:
            for i, v in enumerate(te.get("serie") or []):
                if v is not None:
                    filas.append((cod, "temp_c", _hora_ts(d["fecha"], ini + paso * i), float(v)))
    n = guardar(con, "inamhi", filas)
    # Donde ya hay datos de 5 min, sobran las filas horarias de respaldo
    for cod, h in horas_5min:
        con.execute("DELETE FROM obs WHERE fuente='inamhi' AND estacion=? AND substr(ts,1,13)=? "
                    "AND substr(ts,18,2)=?", (cod, h, f"{HORARIO_SEG:02d}"))
    # Una vez por hora: rellenar con el historial horario las horas sin 5 min (p. ej. tras un corte)
    if dt.datetime.now(UTC).minute < 5:
        n += inamhi_historial(con, dias=2)
    return n


def inamhi_historial(con, dias=2, archivo=None):
    """Carga el historial horario (de la API o de un JSON archivado) solo en horas sin datos de 5 min."""
    if archivo:
        d = json.load(open(archivo))
    else:
        hoy = dt.datetime.now(CONTINENTE).date()
        q = urllib.parse.urlencode({"desde": (hoy - dt.timedelta(days=dias)).isoformat(),
                                    "hasta": hoy.isoformat(), "tipo": "estacion"})
        d = http_json(f"{endpoint('CLIMA_INAMHI_API')}/historial?{q}", timeout=180)
    filas = []
    for f in d.get("filas", []):
        cod = f.get("codigo")
        if cod not in INAMHI_EST:
            continue
        t = dt.datetime.fromisoformat(f["hora"]).replace(tzinfo=CONTINENTE) + dt.timedelta(minutes=30, seconds=HORARIO_SEG)
        h = t.astimezone(UTC).strftime("%Y-%m-%dT%H")
        if con.execute("SELECT 1 FROM obs WHERE fuente='inamhi' AND estacion=? AND variable='lluvia_mm' "
                       "AND substr(ts,1,13)=? AND substr(ts,18,2)='00' LIMIT 1", (cod, h)).fetchone():
            continue
        if f.get("n_lluvia") and f.get("lluvia_mm") is not None:
            filas.append((cod, "lluvia_mm", t, float(f["lluvia_mm"])))
        if f.get("n_temp") and f.get("t_prom") is not None:
            filas.append((cod, "temp_c", t, float(f["t_prom"])))
    for cod, (_, _, nom, isla, lat, lon, alt) in INAMHI_EST.items():
        estacion(con, "inamhi", cod, nom, isla, lat, lon, alt, "INAMHI")
    return guardar(con, "inamhi", filas)


# ---------------------------------------------------------------- Mareógrafos IOC (nivel del mar)
IOC_EST = {"sant": ("Mareógrafo Puerto Ayora", "Santa Cruz", -0.7525, -90.3117),
           "balt": ("Mareógrafo Baltra", "Baltra", -0.4350, -90.2833)}


def fuente_ioc(con):
    api = endpoint("CLIMA_IOC_API")
    fin = dt.datetime.now(UTC)
    ini = fin - dt.timedelta(hours=2)
    filas = []
    for cod, (nom, isla, lat, lon) in IOC_EST.items():
        estacion(con, "ioc", cod, nom, isla, lat, lon, 0, "IOC")
        q = urllib.parse.urlencode({"query": "data", "code": cod, "format": "json",
                                    "timestart": ini.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "timestop": fin.strftime("%Y-%m-%dT%H:%M:%S")})
        datos = http_json(f"{api}?{q}")
        # El sensor de presión está congelado y algún radar también: se usa el radar que varía más
        por = {}
        for x in datos:
            if x.get("sensor") in ("rad", "ras") and x.get("slevel") is not None:
                por.setdefault(x["sensor"], []).append(x)
        vivos = {s: v for s, v in por.items() if len(v) > 5 and statistics.pstdev([x["slevel"] for x in v]) > 0.002}
        if not vivos:
            continue
        s = max(vivos, key=lambda k: statistics.pstdev([x["slevel"] for x in vivos[k]]))
        filas += [(cod, "nivel_mar_m", dt.datetime.fromisoformat(x["stime"]).replace(tzinfo=UTC), float(x["slevel"]))
                  for x in vivos[s]]
    return guardar(con, "ioc", filas)


# ---------------------------------------------------------------- METAR (aeropuertos)
METAR_EST = {"SEGS": ("Aeropuerto Seymour (Baltra)", "Baltra", -0.4539, -90.2658, 51),
             "SEST": ("Aeropuerto San Cristóbal", "San Cristóbal", -0.9100, -89.6170, 18)}


def _codigo_lluvia(wx):
    """0 sin lluvia, 1 llovizna o lluvia débil, 2 moderada, 3 fuerte o tormenta."""
    wx = wx or ""
    if not any(k in wx for k in ("RA", "DZ", "TS", "SH")):
        return 0
    if "+" in wx or "TS" in wx:
        return 3
    if "-" in wx or ("DZ" in wx and "RA" not in wx):
        return 1
    return 2


def fuente_metar(con):
    api = endpoint("CLIMA_METAR_API")
    q = urllib.parse.urlencode({"ids": ",".join(METAR_EST), "format": "json", "hours": 3})
    filas = []
    for m in http_json(f"{api}?{q}"):
        cod = m.get("icaoId")
        if cod not in METAR_EST:
            continue
        t = dt.datetime.fromtimestamp(m["obsTime"], UTC)
        if m.get("temp") is not None:
            filas.append((cod, "temp_c", t, float(m["temp"])))
        if m.get("altim") is not None:
            filas.append((cod, "presion_hpa", t, float(m["altim"])))
        if m.get("wspd") is not None:
            filas.append((cod, "viento_ms", t, round(float(m["wspd"]) * 0.5144, 1)))
        filas.append((cod, "lluvia_codigo", t, _codigo_lluvia(m.get("wxString"))))
    for cod, (nom, isla, lat, lon, alt) in METAR_EST.items():
        estacion(con, "metar", cod, nom, isla, lat, lon, alt, "Aeropuertos (METAR)")
    return guardar(con, "metar", filas)


FUENTES_EXTRA = {"inamhi": fuente_inamhi, "ioc": fuente_ioc, "metar": fuente_metar}

# ---------------------------------------------------------------- WeatherLink (estaciones particulares públicas)
# El mapa público solo da el valor actual y la lluvia acumulada del día (se reinicia a medianoche
# de Galápagos). Se guarda el acumulado tal cual (lluvia_dia_acum_mm) y la lluvia de cada intervalo
# como la diferencia con la consulta anterior del mismo día.
# Estaciones: CLIMA_WEATHERLINK_ESTACIONES (privado/fuentes.env) = "id_publico_del_mapa:codigo[,…]".
# Los identificadores del mapa no se versionan (como el resto de endpoints). La estación de Erna en
# Puerto Ayora se publica con su nombre y ubicación exacta: autorizado por Julián el 2-nov-2026.
WEATHERLINK_META = {  # código: (nombre, isla, lat, lon, altitud)
    "pa_weatherlink": ("Puerto Ayora (Erna)", "Santa Cruz", -0.753368, -90.311995, 10),
    # Sensores «GALAP» de Puerto Baquerizo Moreno: inactivos el 2-nov-2026 (1–3 sin datos; 4 desde
    # ago-2022; 5 desde sep-2024). Entran solos al dashboard cuando vuelvan a transmitir.
    "galap1": ("Puerto Baquerizo (GALAP1)", "San Cristóbal", -0.902, -89.608, 10),
    "galap2": ("Puerto Baquerizo (GALAP2)", "San Cristóbal", -0.902, -89.608, 10),
    "galap3": ("Puerto Baquerizo (GALAP3)", "San Cristóbal", -0.902, -89.608, 10),
    "galap4": ("Puerto Baquerizo (GALAP4)", "San Cristóbal", -0.902, -89.608, 10),
    "galap5": ("Puerto Baquerizo (GALAP5)", "San Cristóbal", -0.902, -89.608, 10),
}
WEATHERLINK_MAX_EDAD = 3 * 86400  # una estación que no transmite hace más de 3 días no se registra


def _weatherlink_estaciones():
    import os
    out = {}
    for par in os.environ.get("CLIMA_WEATHERLINK_ESTACIONES", "").split(","):
        if ":" in par:
            wid, cod = par.strip().split(":", 1)
            if cod in WEATHERLINK_META:
                out[wid] = (cod, *WEATHERLINK_META[cod])
    if not out:
        raise RuntimeError("Falta CLIMA_WEATHERLINK_ESTACIONES en privado/fuentes.env")
    return out
MAX_MM_H = 100  # filtro de saltos: un incremento por encima de esta intensidad se descarta
GALAPAGOS = dt.timezone(dt.timedelta(hours=-6))


def fuente_weatherlink(con):
    api = endpoint("CLIMA_WEATHERLINK_API")
    filas = []
    activas, errores = 0, []
    for wid, (cod, nom, isla, lat, lon, alt) in _weatherlink_estaciones().items():
        try:
            d = http_json(f"{api}/{wid}")
        except Exception as e:  # una estación caída no detiene a las demás
            errores.append(f"{cod}: {e}")
            continue
        t_ult = d.get("lastTimestamp")
        try:
            edad = dt.datetime.now(UTC).timestamp() - int(t_ult)
        except (TypeError, ValueError):
            edad = None
        if edad is None or edad > WEATHERLINK_MAX_EDAD or d.get("dailyRain") in (None, "", "--"):
            continue  # inactiva: no se registra ni se publica
        activas += 1
        estacion(con, "weatherlink", cod, nom, isla, lat, lon, alt, "WeatherLink")
        t = dt.datetime.fromtimestamp(int(t_ult), UTC)
        ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        if con.execute("SELECT 1 FROM obs WHERE fuente='weatherlink' AND estacion=? AND ts=? LIMIT 1", (cod, ts)).fetchone():
            continue  # sin dato nuevo
        num = lambda k: None if d.get(k) in (None, "", "--") else float(d[k])  # noqa: E731
        acum = round(num("dailyRain") * (25.4 if d.get("rainUnit", "in") == "in" else 1), 2)
        # incremento respecto de la última lectura del mismo día de Galápagos
        dia0 = t.astimezone(GALAPAGOS).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
        prev = con.execute("SELECT valor FROM obs WHERE fuente='weatherlink' AND estacion=? AND variable='lluvia_dia_acum_mm' "
                           "AND ts>=? AND ts<? ORDER BY ts DESC LIMIT 1",
                           (cod, dia0.strftime("%Y-%m-%dT%H:%M:%SZ"), ts)).fetchone()
        filas.append((cod, "lluvia_dia_acum_mm", t, acum))
        if prev is not None:
            ult_t = con.execute("SELECT MAX(ts) FROM obs WHERE fuente='weatherlink' AND estacion=? "
                                "AND variable='lluvia_dia_acum_mm' AND ts<?", (cod, ts)).fetchone()[0]
            horas = max((t - dt.datetime.fromisoformat(ult_t.replace("Z", "+00:00"))).total_seconds() / 3600, 1 / 60)
            inc = round(max(0.0, acum - prev[0]), 2)
            # pluviómetro de balancín de 0,01" (0,254 mm); se descartan saltos imposibles (> 100 mm/h y > 10 mm)
            filas.append((cod, "lluvia_mm", t, None if inc > max(10, MAX_MM_H * horas) else inc))
        elif t - dia0 < dt.timedelta(minutes=10):
            filas.append((cod, "lluvia_mm", t, acum))  # primera lectura del día, justo tras el reinicio
        temp = num("temperature")
        if temp is not None:
            filas.append((cod, "temp_c", t, round((temp - 32) / 1.8 if "F" in d.get("temperatureUnit", "F") else temp, 2)))
        if num("humidity") is not None:
            filas.append((cod, "hr_pct", t, num("humidity")))
        if num("barometer") is not None:
            filas.append((cod, "presion_hpa", t, round(num("barometer") * (33.8639 if "in" in d.get("barometerUnit", "in") else 1), 1)))
        if num("windSpeed") is not None:
            filas.append((cod, "viento_ms", t, round(num("windSpeed") * (0.44704 if "mph" in d.get("windSpeedUnit", "mph") else 1), 1)))
    if not activas and errores:
        raise RuntimeError("; ".join(errores)[:400])
    return guardar(con, "weatherlink", filas)


FUENTES_EXTRA["weatherlink"] = fuente_weatherlink


# ---------------------------------------------------------------- Tempest (WeatherFlow)
# API oficial de WeatherFlow con el token personal (solo lectura) que genera el dueño de la estación
# en tempestwx.com → Settings → Data Authorizations. Variables en privado/fuentes.env:
#   CLIMA_TEMPEST_API      endpoint REST
#   CLIMA_TEMPEST_TOKEN    token personal
#   CLIMA_TEMPEST_EQUIPOS  "id_dispositivo:codigo[,…]" (el dispositivo ST de la estación)
# /observations/device/{id}?time_start&time_end devuelve obs_st (1 registro por minuto):
#   [0] época, [2] viento medio m/s, [6] presión de la estación hPa, [7] temperatura °C, [8] HR %,
#   [12] lluvia del minuto mm. Se agregan en bloques de 5 min, como el resto de fuentes.
TEMPEST_META = {  # código: (nombre, isla, lat, lon, altitud)
    "punta_estrada": ("Punta Estrada", "Santa Cruz", -0.7499, -90.31081, 8),
}


def _tempest_equipos():
    import os
    equipos = [p.split(":", 1) for p in os.environ.get("CLIMA_TEMPEST_EQUIPOS", "").split(",") if ":" in p]
    if not equipos:
        raise RuntimeError("Falta CLIMA_TEMPEST_EQUIPOS en privado/fuentes.env")
    return [(d, c) for d, c in equipos if c in TEMPEST_META]


def _tempest_bajar(con, dev, cod, desde, hasta):
    """Baja obs_st entre desde y hasta (en tramos de 1 día) y devuelve filas en bloques de 5 min."""
    api, token = endpoint("CLIMA_TEMPEST_API"), endpoint("CLIMA_TEMPEST_TOKEN")
    nom, isla, lat, lon, alt = TEMPEST_META[cod]
    estacion(con, "tempest", cod, nom, isla, lat, lon, alt, "Tempest")
    bloques, t0 = {}, desde
    while t0 < hasta:
        t1 = min(hasta, t0 + dt.timedelta(days=1))
        q = urllib.parse.urlencode({"token": token, "time_start": int(t0.timestamp()), "time_end": int(t1.timestamp())})
        d = http_json(f"{api}/observations/device/{dev}?{q}", timeout=90)
        obs = d.get("obs") or []
        if not isinstance(obs, list):
            raise ValueError(f"respuesta inesperada de {cod}: {str(d)[:200]}")
        for o in obs:
            if not isinstance(o, list) or len(o) < 13 or o[0] is None:
                continue
            t = dt.datetime.fromtimestamp(int(o[0]), UTC)
            b = t.replace(minute=t.minute - t.minute % 5, second=0)
            g = bloques.setdefault(b, {"lluvia": 0.0, "temp": [], "hr": [], "p": [], "v": []})
            if o[12] is not None:
                g["lluvia"] += float(o[12])
            for k, i in (("v", 2), ("p", 6), ("temp", 7), ("hr", 8)):
                if o[i] is not None:
                    g[k].append(float(o[i]))
        t0 = t1
    ahora = dt.datetime.now(UTC)
    filas = []
    for b, g in bloques.items():
        if b + dt.timedelta(minutes=5) > ahora:
            continue  # bloque en curso: se guarda en la próxima corrida
        filas.append((cod, "lluvia_mm", b, round(g["lluvia"], 2)))
        for k, var in (("temp", "temp_c"), ("hr", "hr_pct"), ("p", "presion_hpa"), ("v", "viento_ms")):
            if g[k]:
                filas.append((cod, var, b, round(sum(g[k]) / len(g[k]), 2)))
    return filas


def fuente_tempest(con):
    ahora = dt.datetime.now(UTC)
    filas = []
    for dev, cod in _tempest_equipos():
        ult = con.execute("SELECT MAX(ts) FROM obs WHERE fuente='tempest' AND estacion=?", (cod,)).fetchone()[0]
        # desde el último bloque guardado (para rellenar cortes), como máximo 3 días atrás
        desde = ahora - dt.timedelta(days=3)
        if ult:
            desde = max(desde, dt.datetime.fromisoformat(ult.replace("Z", "+00:00")) - dt.timedelta(minutes=10))
        filas += _tempest_bajar(con, dev, cod, desde, ahora)
    return guardar(con, "tempest", filas)


def tempest_historico(con, desde):
    """Carga puntual de un rango largo (p. ej. el evento del 30–31 oct)."""
    n = 0
    for dev, cod in _tempest_equipos():
        n += guardar(con, "tempest", _tempest_bajar(con, dev, cod, desde, dt.datetime.now(UTC)))
    con.commit()
    return n


FUENTES_EXTRA["tempest"] = fuente_tempest
