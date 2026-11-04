"""Pronóstico de lluvia por zona (modelos globales; NO es un dato oficial ni una alerta).

Qué se publica y por qué (evaluación en clima/pronostico/fase0/, con 2024–2026):
- Los modelos globales se quedan muy cortos en milímetros en las islas, pero sí «suben» los días en
  que llueve fuerte. Por eso la señal no usa sus milímetros. Usa el **consenso**: el percentil de cada
  modelo dentro de su propia climatología en ese punto (pronostico_calibracion.json), promediado entre
  los modelos. Una curva logística ajustada con la lluvia medida convierte el consenso en la
  probabilidad de que alguna estación de la zona supere 10, 20 o 50 mm en el día.
- Los conjuntos (ensembles) se guardan para calibrarlos más adelante y se usan solo para repartir la
  lluvia en bloques de 6 h de las próximas 72 h (cuándo se concentra), no para la probabilidad.

Cada hora, fuente_pronostico() baja los deterministas (una petición) y las corridas nuevas de los
conjuntos, guarda lo crudo en CLIMA_PRONOSTICO_DIR/archivo/ y deja un resumen en ultimo/.
exportar() arma el JSON público. Endpoints en privado/fuentes.env (CLIMA_OPENMETEO_FORECAST_API y
CLIMA_OPENMETEO_ENSEMBLE_API).
"""
import bisect
import datetime as dt
import gzip
import json
import math
import os
import urllib.parse
from pathlib import Path

from recolector import DB, UTC, endpoint, escribir, http_json

AQUI = Path(__file__).resolve().parent
DIR = Path(os.environ.get("CLIMA_PRONOSTICO_DIR", DB.parent / "pronostico"))
ZONAS = json.loads((AQUI / "zonas_geo.json").read_text())["zonas"]
REGLAS = json.loads((AQUI / "pronostico_reglas.json").read_text())
CAL = json.loads((AQUI / "pronostico_calibracion.json").read_text())
GALAPAGOS = dt.timezone(dt.timedelta(hours=-6))
DIAS = 5  # hoy y 4 días más (la señal se evaluó hasta 5 días de anticipación)

# Deterministas: id en la API de pronóstico → (nombre, id de metadatos para la hora de corrida)
DETERMINISTAS = {
    "ecmwf_ifs025": ("ECMWF IFS 0,25°", "ecmwf_ifs025"),
    "ecmwf_aifs025_single": ("ECMWF AIFS (IA)", "ecmwf_aifs025_single"),
    "gfs_seamless": ("NOAA GFS", "ncep_gfs013"),
    "icon_seamless": ("DWD ICON", "dwd_icon"),
    "ukmo_seamless": ("UK Met Office", "ukmo_global_deterministic_10km"),
    "meteofrance_seamless": ("Météo-France ARPEGE", "meteofrance_arpege_world025"),
    "gem_seamless": ("Canadá GEM", "cmc_gem_gdps"),
    "ecmwf_ifs": ("ECMWF IFS 9 km", "ecmwf_ifs"),  # no entra en el consenso: se muestra hora a hora
}
DETALLE = "ecmwf_ifs"
# Conjuntos: id en la API de conjuntos, id de metadatos, nombre, miembros
CONJUNTOS = [
    ("ecmwf_ifs025", "ecmwf_ifs025_ensemble", "ECMWF IFS ENS", 51),
    ("ecmwf_aifs025", "ecmwf_aifs025_ensemble", "ECMWF AIFS ENS (IA)", 51),
    ("gfs025", "ncep_gefs025", "NOAA GEFS", 31),
    ("icon_global", "dwd_icon_eps", "DWD ICON-EPS", 40),
    ("ukmo_global_ensemble_20km", "ukmo_global_ensemble_20km", "UK Met Office MOGREPS-G", 18),
]


def _puntos():
    return [(z, p) for z, zona in ZONAS.items() for p in zona["puntos"]]


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%MZ")


def _de_iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _hora_local(iso_utc):
    return _de_iso(iso_utc).astimezone(GALAPAGOS).strftime("%Y-%m-%dT%H:%M")


def _meta(api, meta_id, ahora):
    """(inicio de la corrida, disponible desde, fiable). Algunos metadatos de Open-Meteo quedan viejos
    (ICON-EPS, GEM): entonces la hora de corrida no se conoce."""
    u = urllib.parse.urlsplit(api)
    try:
        m = http_json(f"{u.scheme}://{u.netloc}/data/{meta_id}/static/meta.json", timeout=30)
        ini = dt.datetime.fromtimestamp(m["last_run_initialisation_time"], UTC)
        disp = dt.datetime.fromtimestamp(m["last_run_availability_time"], UTC)
    except Exception:
        return None, None, False
    if (ahora - ini).total_seconds() > 36 * 3600:
        return None, None, False
    return ini, disp, True


def _pedir(api, modelos, extra=None):
    pts = _puntos()
    q = {"latitude": ",".join(str(p["lat"]) for _, p in pts), "longitude": ",".join(str(p["lon"]) for _, p in pts),
         "hourly": "precipitation", "models": ",".join(modelos), "timezone": "GMT", "past_days": 1, "forecast_days": DIAS + 1}
    q.update(extra or {})
    d = http_json(f"{api}?{urllib.parse.urlencode(q)}", timeout=120)
    return d if isinstance(d, list) else [d]


def _claves_locales(t_iso):
    """La lluvia de Open-Meteo es la suma de la hora que TERMINA en t; cuenta para el día y el bloque
    de 6 h (hora de Galápagos) en que EMPIEZA esa hora."""
    loc = (dt.datetime.fromisoformat(t_iso).replace(tzinfo=UTC) - dt.timedelta(hours=1)).astimezone(GALAPAGOS)
    return loc.strftime("%Y-%m-%d"), f"{loc:%Y-%m-%d}T{loc.hour // 6 * 6:02d}"


def _sumar(horas, valores_por_hora, horas_dia=24, horas_bloque=6):
    """valores_por_hora: lista (por hora) de listas (por serie). Devuelve totales por día y por bloque,
    solo si están completos y sin huecos."""
    dias, bloques = {}, {}
    for t, fila in zip(horas, valores_por_hora):
        d, b = _claves_locales(t)
        for destino, clave in ((dias, d), (bloques, b)):
            acc = destino.setdefault(clave, {"n": 0, "v": [0.0] * len(fila), "nulos": False})
            acc["n"] += 1
            if any(x is None for x in fila):
                acc["nulos"] = True
            else:
                acc["v"] = [a + x for a, x in zip(acc["v"], fila)]
    ok = lambda a, h: a["n"] >= h and not a["nulos"]  # noqa: E731
    return ({k: [round(x, 2) for x in a["v"]] for k, a in sorted(dias.items()) if ok(a, horas_dia)},
            {k: [round(x, 2) for x in a["v"]] for k, a in sorted(bloques.items()) if ok(a, horas_bloque)})


def _estado():
    try:
        return json.loads((DIR / "estado.json").read_text())
    except (OSError, ValueError):
        return {}


def _archivar(nombre, ini, datos):
    arch = DIR / "archivo" / ini.strftime("%Y-%m") / f"{ini:%Y%m%dT%H}_{nombre}.json.gz"
    if not arch.exists():
        arch.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(arch, "wt") as fh:
            json.dump(datos, fh)


def fuente_pronostico(con):
    """Baja los pronósticos. Devuelve el número de modelos con corrida nueva."""
    estado = _estado()
    ahora = dt.datetime.now(UTC)
    if estado.get("_revisado") and (ahora - _de_iso(estado["_revisado"])).total_seconds() < 3300:
        return 0  # una vez por hora basta
    nuevos, errores = 0, []

    # 1) Deterministas: una sola petición con todos los modelos.
    api = endpoint("CLIMA_OPENMETEO_FORECAST_API")
    corridas = {}
    for m, (_, meta_id) in DETERMINISTAS.items():
        ini, disp, fiable = _meta(api, meta_id, ahora)
        corridas[m] = {"corrida_utc": _iso(ini) if fiable else None, "disponible_utc": _iso(disp) if fiable else None}
    try:
        resp = _pedir(api, list(DETERMINISTAS))
        puntos = {}
        for (z, p), r in zip(_puntos(), resp):
            h = r.get("hourly", {})
            pm = {}
            for m in DETERMINISTAS:
                serie = h.get(f"precipitation_{m}") or (h.get("precipitation") if len(DETERMINISTAS) == 1 else None)
                if not serie:
                    continue
                dias, _ = _sumar(h["time"], [[x] for x in serie])
                pm[m] = {"dias": {k: v[0] for k, v in dias.items()}}
                if m == DETALLE:
                    pm[m]["horario"] = {"t": h["time"], "mm": serie}
            puntos[p["id"]] = {"zona": z, "modelos": pm}
        cambio = any(corridas[m]["corrida_utc"] != estado.get("deterministas", {}).get(m, {}).get("corrida_utc")
                     for m in DETERMINISTAS)
        if cambio or not (DIR / "ultimo" / "deterministas.json").exists():
            _archivar("deterministas", ahora.replace(minute=0, second=0, microsecond=0), resp)
            nuevos += sum(corridas[m]["corrida_utc"] != estado.get("deterministas", {}).get(m, {}).get("corrida_utc")
                          for m in DETERMINISTAS)
        escribir(DIR / "ultimo" / "deterministas.json", {"recibido_utc": _iso(ahora), "corridas": corridas, "puntos": puntos})
        estado["deterministas"] = {m: {**c, "recibido_utc": _iso(ahora)} for m, c in corridas.items()}
    except Exception as e:
        errores.append(f"deterministas: {type(e).__name__}: {e}"[:200])

    # 2) Conjuntos: solo si hay corrida nueva (o cada 6 h si la hora de corrida no se conoce).
    api = endpoint("CLIMA_OPENMETEO_ENSEMBLE_API")
    for modelo, meta_id, nombre, miembros in CONJUNTOS:
        try:
            ini, disp, fiable = _meta(api, meta_id, ahora)
            previo = estado.get(modelo, {})
            if fiable and previo.get("corrida_utc") == _iso(ini):
                continue
            if not fiable:
                rec = previo.get("recibido_utc")
                if rec and (ahora - _de_iso(rec)).total_seconds() < 6 * 3600:
                    continue
            resp = _pedir(api, [modelo])
            _archivar(modelo, ini if fiable else ahora.replace(minute=0, second=0, microsecond=0), resp)
            puntos = {}
            for (z, p), r in zip(_puntos(), resp):
                h = r.get("hourly", {})
                claves = sorted((k for k in h if k.startswith("precipitation")), key=lambda k: (k != "precipitation", k))
                dias, bloques = _sumar(h.get("time", []), list(zip(*[h[k] for k in claves])) if claves else [])
                puntos[p["id"]] = {"zona": z, "dias": dias, "bloques6h": bloques}
            resumen = {"modelo": modelo, "nombre": nombre, "miembros": miembros,
                       "corrida_utc": _iso(ini) if fiable else None, "disponible_utc": _iso(disp) if fiable else None,
                       "recibido_utc": _iso(ahora), "puntos": puntos}
            escribir(DIR / "ultimo" / f"{modelo}.json", resumen)
            estado[modelo] = {k: resumen[k] for k in ("corrida_utc", "disponible_utc", "recibido_utc")}
            nuevos += 1
        except Exception as e:  # un modelo caído no detiene a los demás
            errores.append(f"{modelo}: {type(e).__name__}: {e}"[:200])
    estado["_revisado"] = ahora.isoformat()
    estado["_errores"] = errores
    escribir(DIR / "estado.json", estado)
    if errores and len(errores) == 1 + len(CONJUNTOS):
        raise RuntimeError("; ".join(errores))
    return nuevos


# ---------------------------------------------------------------- señal calibrada

def percentil(clim, x):
    """Percentil (rango medio, como en la evaluación) de x en la lista de cuantiles clim."""
    i, j = bisect.bisect_left(clim, x), bisect.bisect_right(clim, x)
    return ((i + j) / 2) / len(clim)


def _cercano(objetivo, disponibles):
    """Clave disponible más cercana a la anticipación objetivo (en empate, la mayor)."""
    return str(min((int(k) for k in disponibles), key=lambda k: (abs(k - objetivo), -k)))


def senal(punto_id, modelos_dia, fecha, dias_adelante):
    """modelos_dia: {modelo: mm del día}. Devuelve consenso, probabilidades calibradas y nivel.

    En el archivo con que se calibró, «anticipación 1» (previous_day1) usa corridas listas hasta la
    madrugada del mismo día: corresponde a «hoy». Por eso el día k usa la anticipación k+1."""
    ant = dias_adelante + 1
    clim = (CAL.get("climatologia") or {}).get(punto_id, {})
    pcts = {}
    for m in CAL["modelos_consenso"]:
        x, c = modelos_dia.get(m), clim.get(m)
        if x is None or not c:
            continue
        pcts[m] = percentil(c[_cercano(ant, c)], x)
    if len(pcts) < REGLAS["modelos_minimos"]:
        return None
    cons = sum(pcts.values()) / len(pcts)
    gp = CAL["grupo_punto"].get(punto_id, {})
    temp = "lluviosa" if int(fecha[5:7]) in CAL["temporada_lluviosa_meses"] else "garua"
    por_grupo = CAL["calibracion"].get(gp.get("grupo"), {}).get(temp, {})
    plazo = _cercano(ant, por_grupo) if por_grupo else None
    curvas = por_grupo.get(plazo, {}) if plazo else {}
    uP = str(REGLAS["umbral_principal"])
    prob, estado = {}, {}
    for u, c in curvas.items():
        estado[u] = c.get("estado", "sin_datos")
        if estado[u] == "ok":
            prob[u] = round(1 / (1 + math.exp(-(c["a"] + c["b"] * cons))), 3)
        elif estado[u] == "sin_eventos":
            prob[u] = 0.0  # en esta época no se midió ningún día así
        else:
            prob[u] = None  # sin habilidad demostrada o pocos datos: no se publica una cifra
    c20 = curvas.get(uP, {})
    p20 = prob.get(uP)
    # El nivel se decide con la cifra que se publica (redondeada a 5 %), para que no se contradigan.
    p20r = None if p20 is None else round(p20 * 20) / 20
    nivel = "no_evaluable" if p20r is None else next(n["id"] for n in REGLAS["niveles"] if p20r >= n.get("desde", 2) - 1e-9)
    return {"consenso": round(cons, 3), "n_modelos": len(pcts), "prob": prob, "nivel": nivel,
            "estado_20": estado.get(uP, "sin_datos"), "frec_normal_20": c20.get("frec_base"),
            "temporada": temp, "anticipacion_calibracion": plazo, "calibrado": gp.get("calibrado", False),
            "grupo": gp.get("grupo"), "prestada_de": c20.get("prestada_de"),
            "percentiles": {m: round(v, 2) for m, v in pcts.items()}}


def _leer(nombre):
    try:
        return json.loads((DIR / "ultimo" / f"{nombre}.json").read_text())
    except (OSError, ValueError):
        return None


def _pct(xs, q):
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    i = int(k)
    return xs[i] + (xs[min(i + 1, len(xs) - 1)] - xs[i]) * (k - i)


def exportar(ahora=None):
    ahora = ahora or dt.datetime.now(UTC)
    loc = ahora.astimezone(GALAPAGOS)
    hoy = loc.strftime("%Y-%m-%d")
    bloque_actual = f"{hoy}T{loc.hour // 6 * 6:02d}"
    edad_max = REGLAS["edad_maxima_horas"] * 3600
    det = _leer("deterministas")
    det_ok = det and (ahora - _de_iso(det["recibido_utc"])).total_seconds() < edad_max
    viejos = {m for m, c in ((det or {}).get("corridas") or {}).items()  # corrida conocida y demasiado vieja
              if c.get("corrida_utc") and (ahora - _de_iso(c["corrida_utc"])).total_seconds() >= edad_max}
    conj = {}
    for modelo, *_ in CONJUNTOS:
        r = _leer(modelo)
        ref = r and (r.get("corrida_utc") or r.get("recibido_utc"))
        if ref and (ahora - _de_iso(ref)).total_seconds() < edad_max:
            conj[modelo] = r

    zonas = {}
    for z, zona in ZONAS.items():
        puntos = []
        for p in zona["puntos"]:
            dias = []
            pd_ = (det or {}).get("puntos", {}).get(p["id"], {}).get("modelos", {}) if det_ok else {}
            pd_ = {m: v for m, v in pd_.items() if m not in viejos}
            for k in range(DIAS):
                if k == 0 and loc.hour >= 18:
                    continue  # «hoy» casi terminado: lo que queda está en los bloques de 6 h
                fecha = (loc + dt.timedelta(days=k)).strftime("%Y-%m-%d")
                mm = {m: v["dias"].get(fecha) for m, v in pd_.items() if v["dias"].get(fecha) is not None}
                s = senal(p["id"], mm, fecha, k)
                if s:
                    dias.append({"fecha": fecha, **s,
                                 "mm_modelos_mediana": round(_pct([mm[m] for m in s["percentiles"]], .5), 1)})
            # Bloques de 6 h (próximas 72 h): mediana y p90 de los miembros, promediadas entre conjuntos.
            bloques = []
            claves = sorted({b for r in conj.values() for b in r["puntos"].get(p["id"], {}).get("bloques6h", {})})
            for b in claves:
                if b < bloque_actual:
                    continue
                vals = [r["puntos"][p["id"]]["bloques6h"][b] for r in conj.values() if b in r["puntos"].get(p["id"], {}).get("bloques6h", {})]
                if len(vals) < 2:
                    continue
                bloques.append({"inicio": b + ":00", "n_conjuntos": len(vals),
                                "mediana": round(sum(_pct(v, .5) for v in vals) / len(vals), 1),
                                "p90": round(sum(_pct(v, .9) for v in vals) / len(vals), 1)})
                if len(bloques) >= 12:
                    break
            detalle = None
            h = pd_.get(DETALLE, {}).get("horario")
            if h:
                corte = ahora.strftime("%Y-%m-%dT%H:%M")
                serie = [(_hora_local(t + "Z"), v) for t, v in zip(h["t"], h["mm"]) if v is not None and t > corte][:72]
                detalle = {"modelo": DETERMINISTAS[DETALLE][0], "hora_local_fin": [x[0] for x in serie], "mm": [round(x[1], 1) for x in serie]}
            puntos.append({"id": p["id"], "nombre": p["nombre"], "tipo": p["tipo"], "dias": dias,
                           "bloques6h": bloques, "detalle": detalle})
        zonas[z] = {"nombre": zona["nombre"], "puntos": puntos}

    modelos = []
    for m, (nombre, _) in DETERMINISTAS.items():
        c = (det or {}).get("corridas", {}).get(m, {})
        modelos.append({"id": m, "nombre": nombre, "tipo": "determinista", "miembros": 1, "en_consenso": m in CAL["modelos_consenso"],
                        "corrida_utc": c.get("corrida_utc"), "corrida_local": c.get("corrida_utc") and _hora_local(c["corrida_utc"]),
                        "disponible_local": c.get("disponible_utc") and _hora_local(c["disponible_utc"]),
                        "recibido_local": det and _hora_local(det["recibido_utc"]), "vigente": bool(det_ok) and m not in viejos})
    for modelo, _, nombre, miembros in CONJUNTOS:
        r = _leer(modelo) or {}
        modelos.append({"id": modelo, "nombre": nombre, "tipo": "conjunto", "miembros": miembros, "en_consenso": False,
                        "corrida_utc": r.get("corrida_utc"), "corrida_local": r.get("corrida_utc") and _hora_local(r["corrida_utc"]),
                        "disponible_local": r.get("disponible_utc") and _hora_local(r["disponible_utc"]),
                        "recibido_local": r.get("recibido_utc") and _hora_local(r["recibido_utc"]), "vigente": modelo in conj})
    return {"generado": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"), "generado_local": loc.strftime("%Y-%m-%dT%H:%M"),
            "hoy_local": hoy, "modelos": modelos, "zonas": zonas,
            "reglas": {k: REGLAS[k] for k in ("version", "umbral_principal", "dias_fiables", "niveles", "grupos",
                                              "aviso", "explicacion_horas", "evaluacion")}}
