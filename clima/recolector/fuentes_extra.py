"""Fuentes adicionales del recolector: INAMHI, mareógrafos IOC, METAR de los aeropuertos y estaciones
particulares (WeatherLink, Tempest, Ambient Weather y Weather Underground).

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
    # nombre oficial del INAMHI y su código, más la localidad
    "M0191": (-0.745, -90.315, "CHARLES DARWIN 1 (M0191), Puerto Ayora", "Santa Cruz", -0.743056, -90.3025, 6),
    "M0221": (-0.901, -89.611, "SAN CRISTOBAL-GALAPAGOS (M0221), Puerto Baquerizo", "San Cristóbal", -0.904058, -89.614308, 6),
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
# Se usa siempre el mismo radar por estación («ras», con el mismo cero que la serie UHSLC; el «rad» de
# Puerto Ayora tiene otro cero, +4,9 m) y se resta el desfase IOC−UHSLC calculado por
# scripts/05_mareas.py, así que nivel_mar_m queda en el cero UHSLC (comparable con la predicción).
IOC_EST = {"sant": ("Mareógrafo Puerto Ayora", "Santa Cruz", -0.7525, -90.3117),
           "balt": ("Mareógrafo Baltra", "Baltra", -0.4350, -90.2833)}
IOC_SENSORES = ("ras", "rad")  # orden de preferencia


def _ioc_desfases():
    import os
    from pathlib import Path
    f = Path(__file__).resolve().parent / "mareas_prediccion.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text())
    return {cod: (e.get("ioc") or {}) for cod, e in d.get("estaciones", {}).items()}


def fuente_ioc(con):
    api = endpoint("CLIMA_IOC_API")
    fin = dt.datetime.now(UTC)
    desfases = _ioc_desfases()
    filas = []
    for cod, (nom, isla, lat, lon) in IOC_EST.items():
        estacion(con, "ioc", cod, nom, isla, lat, lon, 0, "IOC")
        ult = con.execute("SELECT MAX(ts) FROM obs WHERE fuente='ioc' AND estacion=?", (cod,)).fetchone()[0]
        ini = fin - dt.timedelta(days=3)
        if ult:
            ini = max(ini, dt.datetime.fromisoformat(ult.replace("Z", "+00:00")) - dt.timedelta(minutes=30))
        q = urllib.parse.urlencode({"query": "data", "code": cod, "format": "json",
                                    "timestart": ini.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "timestop": fin.strftime("%Y-%m-%dT%H:%M:%S")})
        datos = http_json(f"{api}?{q}", timeout=120)
        por = {}
        for x in datos:
            if x.get("sensor") in IOC_SENSORES and x.get("slevel") is not None:
                por.setdefault(x["sensor"], []).append(x)
        # el sensor preferido que esté vivo (no congelado) y tenga desfase conocido
        for sen in IOC_SENSORES:
            xs = por.get(sen, [])
            des = (desfases.get(cod) or {}).get(sen)
            if len(xs) > 5 and statistics.pstdev([x["slevel"] for x in xs]) > 0.002 and des:
                off = des["desfase_cm"] / 100
                filas += [(cod, "nivel_mar_m", dt.datetime.fromisoformat(x["stime"]).replace(tzinfo=UTC),
                           round(float(x["slevel"]) - off, 3)) for x in xs]
                break
    return guardar(con, "ioc", filas)


# ---------------------------------------------------------------- Modelo de nivel del mar (Open-Meteo Marine)
# Para los puertos sin mareógrafo (Puerto Baquerizo, Puerto Villamil): marea + nivel modelados, cada hora.
MAR_MODELO = {"baquerizo": ("Puerto Baquerizo Moreno", -0.902, -89.612),
              "villamil": ("Puerto Villamil", -0.962, -90.965)}


def fuente_mar_modelo(con):
    import os
    from pathlib import Path
    destino = Path(os.environ.get("CLIMA_DB", "clima.db")).parent / "mar_modelo.json"
    if destino.exists() and dt.datetime.now(UTC).timestamp() - destino.stat().st_mtime < 3000:
        return 0  # una vez por hora basta
    api = endpoint("CLIMA_OPENMETEO_MARINE_API")
    q = urllib.parse.urlencode({"latitude": ",".join(str(v[1]) for v in MAR_MODELO.values()),
                                "longitude": ",".join(str(v[2]) for v in MAR_MODELO.values()),
                                "minutely_15": "sea_level_height_msl", "hourly": "wave_height",
                                "timezone": "GMT", "past_days": 1, "forecast_days": 3})
    d = http_json(f"{api}?{q}", timeout=60)
    d = d if isinstance(d, list) else [d]
    out = {"generado": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "puertos": {}}
    for (cod, (nom, lat, lon)), p in zip(MAR_MODELO.items(), d):
        m, h = p.get("minutely_15", {}), p.get("hourly", {})
        out["puertos"][cod] = {"nombre": nom, "t": m.get("time", []), "nivel_m": m.get("sea_level_height_msl", []),
                               "ola_t": h.get("time", []), "ola_m": h.get("wave_height", [])}
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(out))
    os.replace(tmp, destino)
    return sum(len(v["t"]) for v in out["puertos"].values())


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


FUENTES_EXTRA = {"inamhi": fuente_inamhi, "ioc": fuente_ioc, "metar": fuente_metar, "mar_modelo": fuente_mar_modelo}

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
        # segundos a :00: las filas con segundos :30 son las horarias del respaldo de Erna
        t = dt.datetime.fromtimestamp(int(t_ult), UTC).replace(second=0)
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
    n = guardar(con, "weatherlink", filas)
    try:
        n += respaldo_erna(con)
    except Exception as e:  # el respaldo nunca tumba la fuente principal
        errores.append(f"respaldo de Erna: {e}")
    if not activas and errores:
        raise RuntimeError("; ".join(errores)[:400])
    return n


# Respaldo de la estación de Erna: la misma consola Davis transmite por CWOP (DW5750) y NOAA MADIS
# la redistribuye. El servicio de CLIMA_RESPALDO_ERNA_API da, sin clave, la última observación con
# la lluvia de la última hora. Si WeatherLink no trae datos de Erna hace más de 30 min, se guarda una
# fila horaria (segundos :30, como el respaldo horario del INAMHI; inundacion.py la cuenta como una
# hora completa), solo para horas que WeatherLink no cubre.
RESPALDO_ERNA = {"cod": "pa_weatherlink", "id": "madis-D5750", "lat": -0.753, "lon": -90.312}


def respaldo_erna(con, ahora=None):
    import os
    if not os.environ.get("CLIMA_RESPALDO_ERNA_API"):
        return 0
    ahora = ahora or dt.datetime.now(UTC)
    cod = RESPALDO_ERNA["cod"]
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    ult = con.execute("SELECT MAX(ts) FROM obs WHERE fuente='weatherlink' AND estacion=? AND variable='lluvia_mm' "
                      "AND substr(ts,18,2)!='30'", (cod,)).fetchone()[0]
    if ult and ahora - dt.datetime.fromisoformat(ult.replace("Z", "+00:00")) < dt.timedelta(minutes=30):
        return 0  # WeatherLink está al día
    d = http_json(f"{endpoint('CLIMA_RESPALDO_ERNA_API')}/{RESPALDO_ERNA['lat']}/{RESPALDO_ERNA['lon']}")
    e = next((x for x in (d if isinstance(d, list) else []) if x.get("id") == RESPALDO_ERNA["id"]), None)
    if not e or e.get("minAgo") is None or e["minAgo"] > 30 or e.get("precip_time") != 1 or e.get("precip") is None:
        return 0
    t = (ahora - dt.timedelta(minutes=int(e["minAgo"]))).replace(second=0, microsecond=0)
    ini = (t - dt.timedelta(hours=1)).replace(second=30)
    # una fila por hora como máximo y nunca encima de datos de WeatherLink
    if con.execute("SELECT 1 FROM obs WHERE fuente='weatherlink' AND estacion=? AND variable='lluvia_mm' "
                   "AND ts>? AND ts<=?", (cod, iso(ini - dt.timedelta(minutes=55)), iso(t))).fetchone():
        return 0
    mm = round(float(e["precip"]), 2)
    filas = [(cod, "lluvia_mm", ini, None if mm > MAX_MM_H else mm)]
    if e.get("temp") is not None:
        filas.append((cod, "temp_c", t, round(float(e["temp"]), 2)))
    if e.get("rh") is not None:
        filas.append((cod, "hr_pct", t, float(e["rh"])))
    print(f"weatherlink: respaldo CWOP de Erna, {mm} mm en la hora hasta {iso(t)}")
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


# ---------------------------------------------------------------- Ambient Weather (AmbientWeather.net)
# Panel público que el dueño comparte con un enlace (sin clave). Variables en privado/fuentes.env:
#   CLIMA_AMBIENT_API         endpoint del panel
#   CLIMA_AMBIENT_ESTACIONES  "clave_del_enlace:codigo[,…]"
# devices?public.slug={clave} da el equipo y su último dato; device-data?macAddress&res=5&start&end
# (ms) da un registro cada 5 min, con historia desde que se instaló. La lluvia llega como acumulado
# del día (dailyrainin, pulgadas, se reinicia a medianoche de Galápagos) y el intervalo se calcula
# por diferencia; temperatura °F, HR %, presión inHg, viento mph. La respuesta trae también la clave
# de subida y la IP de la estación: no se guardan.
AMBIENT_META = {  # código: (nombre, isla, lat, lon, altitud); coordenadas redondeadas a ~100 m
    "evolucion": ("Evolución (Puerto Ayora)", "Santa Cruz", -0.747, -90.315, 10),
    # Paneles públicos en AmbientWeather.net; nombre, ubicación y cita publicados con autorización
    # de Julián (12-nov-2026). Coordenadas y altitud: las que publica cada estación.
    "miconia": ("Miconia (parte alta)", "Santa Cruz", -0.6663, -90.3764, 422),
    "manzanillo_espol": ("El Manzanillo – ESPOL", "Santa Cruz", -0.6965, -90.4020, 169),
    "epmapasc_espol": ("EPMAPASC – ESPOL (Puerto Ayora)", "Santa Cruz", -0.7417, -90.3204, 22),
}
AMBIENT_MAX_EDAD = 3 * 86400  # una estación que no transmite hace más de 3 días no se registra


def _ambient_estaciones():
    import os
    pares = [p.strip().split(":", 1) for p in os.environ.get("CLIMA_AMBIENT_ESTACIONES", "").split(",") if ":" in p]
    if not pares:
        raise RuntimeError("Falta CLIMA_AMBIENT_ESTACIONES en privado/fuentes.env")
    return [(s, c) for s, c in pares if c in AMBIENT_META]


def _ambient_equipo(api, clave):
    d = http_json(f"{api}/devices?{urllib.parse.urlencode({'public.slug': clave})}")
    equipos = d.get("data") or []
    if not equipos or not equipos[0].get("macAddress"):
        raise ValueError("el enlace público no devuelve ningún equipo (¿dejó de compartirse?)")
    return equipos[0]


def _ambient_filas(cod, registros):
    """Registros de 5 min (ordenados) → filas. La lluvia de cada registro es la diferencia con el anterior."""
    filas, ant = [], None
    pulg = lambda r, k: None if r.get(k) is None else float(r[k])  # noqa: E731
    for r in registros:
        t = dt.datetime.fromtimestamp(r["dateutc"] / 1000, UTC)
        b = t - dt.timedelta(minutes=5)  # etiqueta = inicio del intervalo, como el resto de fuentes
        b = b.replace(minute=b.minute - b.minute % 5, second=0, microsecond=0)
        # Diferencia del acumulado anual: el diario se reinicia a medianoche, pero no siempre en el
        # mismo registro (a veces el de las 06:00Z aún trae el total del día anterior). El anual solo
        # se reinicia el 1 de enero; ahí se usa el diario.
        acum = (pulg(r, "yearlyrainin"), pulg(r, "dailyrainin"))
        if ant is not None and None not in acum:
            t0, (anio0, dia0) = ant
            horas = max((t - t0).total_seconds() / 3600, 1 / 60)
            inc = acum[0] - anio0 if acum[0] >= anio0 else (acum[1] - dia0 if acum[1] >= dia0 else acum[1])
            mm = round(inc * 25.4, 2)
            filas.append((cod, "lluvia_mm", b, None if mm > max(10, MAX_MM_H * horas) else mm))
        if None not in acum:
            ant = (t, acum)
        tf = pulg(r, "tempf")
        if tf is not None:
            filas.append((cod, "temp_c", b, round((tf - 32) / 1.8, 2)))
        if pulg(r, "humidity") is not None:
            filas.append((cod, "hr_pct", b, pulg(r, "humidity")))
        if pulg(r, "baromabsin") is not None:
            filas.append((cod, "presion_hpa", b, round(pulg(r, "baromabsin") * 33.8639, 1)))
        if pulg(r, "windspeedmph") is not None:
            filas.append((cod, "viento_ms", b, round(pulg(r, "windspeedmph") * 0.44704, 1)))
    return filas


def _ambient_bajar(con, clave, cod, desde, hasta, pausa=0.0):
    import time
    api = endpoint("CLIMA_AMBIENT_API")
    eq = _ambient_equipo(api, clave)
    ult = (eq.get("lastData") or {}).get("dateutc")
    if not ult or dt.datetime.now(UTC).timestamp() - ult / 1000 > AMBIENT_MAX_EDAD:
        return []  # inactiva: no se registra ni se publica
    nom, isla, lat, lon, alt = AMBIENT_META[cod]
    estacion(con, "ambient", cod, nom, isla, lat, lon, alt, "Ambient Weather")
    registros, t0 = {}, desde
    while t0 < hasta:
        t1 = min(hasta, t0 + dt.timedelta(days=1))
        q = urllib.parse.urlencode({"macAddress": eq["macAddress"], "res": 5,
                                    "start": int(t0.timestamp() * 1000), "end": int(t1.timestamp() * 1000)})
        d = http_json(f"{api}/device-data?{q}", timeout=90)
        datos = d.get("data") if isinstance(d, dict) else None
        if not isinstance(datos, list):
            raise ValueError(f"respuesta inesperada de {cod}: {str(d)[:200]}")
        for r in datos:
            if isinstance(r, dict) and isinstance(r.get("dateutc"), (int, float)):
                registros[int(r["dateutc"])] = r
        t0 = t1
        time.sleep(pausa)
    return _ambient_filas(cod, [registros[k] for k in sorted(registros)])


def fuente_ambient(con):
    ahora = dt.datetime.now(UTC)
    filas = []
    for clave, cod in _ambient_estaciones():
        ult = con.execute("SELECT MAX(ts) FROM obs WHERE fuente='ambient' AND estacion=?", (cod,)).fetchone()[0]
        # desde el último bloque guardado (para rellenar cortes, con el registro anterior para la
        # diferencia de lluvia), como máximo 3 días atrás
        desde = ahora - dt.timedelta(days=3)
        if ult:
            desde = max(desde, dt.datetime.fromisoformat(ult.replace("Z", "+00:00")) - dt.timedelta(minutes=10))
        filas += _ambient_bajar(con, clave, cod, desde, ahora)
    return guardar(con, "ambient", filas)


def ambient_historico(con, desde):
    """Carga puntual de un rango largo (la estación tiene historia desde ago-2024)."""
    n = 0
    for clave, cod in _ambient_estaciones():
        n += guardar(con, "ambient", _ambient_bajar(con, clave, cod, desde, dt.datetime.now(UTC), pausa=0.5))
        con.commit()
    return n


FUENTES_EXTRA["ambient"] = fuente_ambient


# ---------------------------------------------------------------- Weather Underground (estaciones particulares)
# La página pública de cada estación trae el valor actual y la lluvia acumulada del día (se reinicia
# a medianoche de Galápagos), como el mapa de WeatherLink: se guarda el acumulado y la lluvia de cada
# intervalo por diferencia. La «Key» de la estación es la contraseña de subida y no sirve para leer.
# Variables en privado/fuentes.env (no se versionan, como el resto de endpoints):
#   CLIMA_WU_PAGINA       raíz de la página pública de las estaciones (se le añade /{id})
#   CLIMA_WU_ESTACIONES   "id_de_la_estacion:codigo[,…]"
# Casa Marina se publica con su nombre y ubicación exacta: autorizado por Julián el 6-nov-2026.
WU_META = {  # código: (nombre, isla, lat, lon, altitud)
    "casa_marina": ("Puerto Ayora (Casa Marina)", "Santa Cruz", -0.746458, -90.312935, 3),
}
# Conversión a SI según la unidad con que la página muestre cada widget:
# m = métrico (°C, km/h, hPa, mm), e = inglés (°F, mph, inHg, in), h = híbrido (°C, mph, hPa, mm)
WU_UNIDADES = {
    "temp": {"m": lambda x: x, "h": lambda x: x, "e": lambda x: (x - 32) / 1.8},
    "viento": {"m": lambda x: x / 3.6, "h": lambda x: x * 0.44704, "e": lambda x: x * 0.44704},
    "presion": {"m": lambda x: x, "h": lambda x: x, "e": lambda x: x * 33.8639},
    "lluvia": {"m": lambda x: x, "h": lambda x: x, "e": lambda x: x * 25.4},
}


def _wu_estaciones():
    import os
    out = {}
    for par in os.environ.get("CLIMA_WU_ESTACIONES", "").split(","):
        if ":" in par:
            wid, cod = par.strip().split(":", 1)
            if cod in WU_META:
                out[wid] = (cod, *WU_META[cod])
    if not out:
        raise RuntimeError("Falta CLIMA_WU_ESTACIONES en privado/fuentes.env")
    return out


def _wu_widget(html, nombre):
    """Atributos data-* del widget <nombre>-widget-view de la página de la estación."""
    import re
    m = re.search(rf"<{nombre}-widget-view\b([^>]*)>", html)
    return dict(re.findall(r'data-([a-z-]+)="([^"]*)"', m.group(1))) if m else {}


def _wu_leer(html):
    """Lectura actual de la página: {ts, lluvia_dia_mm, temp_c, hr_pct, presion_hpa, viento_ms}."""
    import re
    m = re.search(r'data-obs-time-utc="([A-Z][a-z]{2} [A-Z][a-z]{2} \d{2} \d{4} \d{2}:\d{2}:\d{2} GMT[+-]\d{4})', html)
    if not m:
        return None
    out = {"ts": dt.datetime.strptime(m.group(1), "%a %b %d %Y %H:%M:%S GMT%z").astimezone(UTC)}
    for clave, widget, attr, conv in (("lluvia_dia_mm", "rain", "precip-total", "lluvia"),
                                      ("temp_c", "temp", "temp", "temp"),
                                      ("hr_pct", "humidity", "humidity", None),
                                      ("presion_hpa", "pressure", "pressure", "presion"),
                                      ("viento_ms", "wind", "wind-speed", "viento")):
        w = _wu_widget(html, widget)
        if w.get("status") != "connected":
            continue
        try:
            v = float(w[attr])
        except (KeyError, ValueError):
            continue
        if conv:
            f = WU_UNIDADES[conv].get(w.get("unit"))
            if f is None:
                continue  # unidad desconocida: mejor sin dato que un dato mal convertido
            v = f(v)
        out[clave] = round(v, 2)
    return out


def fuente_wunderground(con):
    import urllib.request
    base = endpoint("CLIMA_WU_PAGINA")
    filas, activas, errores = [], 0, []
    for wid, (cod, nom, isla, lat, lon, alt) in _wu_estaciones().items():
        try:
            req = urllib.request.Request(f"{base}/{wid}", headers={"User-Agent": "Mozilla/5.0 (sosgalapagos-clima)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = _wu_leer(r.read().decode("utf-8", "replace"))
        except Exception as e:  # una estación caída no detiene a las demás
            errores.append(f"{cod}: {e}")
            continue
        if not d or "lluvia_dia_mm" not in d:
            continue  # desconectada o sin pluviómetro
        t = d["ts"]
        if (dt.datetime.now(UTC) - t).total_seconds() > WEATHERLINK_MAX_EDAD:
            continue  # inactiva: no se registra ni se publica
        activas += 1
        estacion(con, "wunderground", cod, nom, isla, lat, lon, alt, "Weather Underground")
        ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        if con.execute("SELECT 1 FROM obs WHERE fuente='wunderground' AND estacion=? AND ts=? LIMIT 1", (cod, ts)).fetchone():
            continue  # sin dato nuevo
        acum = d["lluvia_dia_mm"]
        # incremento respecto de la última lectura del mismo día de Galápagos
        dia0 = t.astimezone(GALAPAGOS).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
        prev = con.execute("SELECT ts, valor FROM obs WHERE fuente='wunderground' AND estacion=? "
                           "AND variable='lluvia_dia_acum_mm' AND ts>=? AND ts<? ORDER BY ts DESC LIMIT 1",
                           (cod, dia0.strftime("%Y-%m-%dT%H:%M:%SZ"), ts)).fetchone()
        filas.append((cod, "lluvia_dia_acum_mm", t, acum))
        if prev is not None:
            horas = max((t - dt.datetime.fromisoformat(prev[0].replace("Z", "+00:00"))).total_seconds() / 3600, 1 / 60)
            inc = round(max(0.0, acum - prev[1]), 2)
            filas.append((cod, "lluvia_mm", t, None if inc > max(10, MAX_MM_H * horas) else inc))
        elif t - dia0 < dt.timedelta(minutes=10):
            filas.append((cod, "lluvia_mm", t, acum))  # primera lectura del día, justo tras el reinicio
        for var in ("temp_c", "hr_pct", "presion_hpa", "viento_ms"):
            if var in d:
                filas.append((cod, var, t, d[var]))
    if not activas and errores:
        raise RuntimeError("; ".join(errores)[:400])
    return guardar(con, "wunderground", filas)


FUENTES_EXTRA["wunderground"] = fuente_wunderground


def fuente_pronostico(con):
    import pronostico
    return pronostico.fuente_pronostico(con)


FUENTES_EXTRA["pronostico"] = fuente_pronostico
