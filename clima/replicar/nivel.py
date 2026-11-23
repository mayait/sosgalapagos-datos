#!/usr/bin/env python3
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
"""Reproduce el nivel de lluvia peligrosa de sosgalapagos.org/clima con los datos públicos.

Solo usa la biblioteca estándar de Python (3.9 o más). Lee el ZIP público con todo
(clima_galapagos_todo.zip): las mediciones de `mediciones/` y la regla de `regla/`. Si no se le
da un ZIP, lo baja una vez a ~/.cache/sosgalapagos/ y lo reutiliza.

Es la misma regla que corre la plataforma (mayait/sosgalapagos-plataforma, clima/nivel.py):
  1. Para cada estación de la zona: lluvia en 1, 3, 24 y 72 h hasta su ÚLTIMO dato (no hasta el
     reloj), y su cobertura (registros recibidos / esperados, un registro cada 5 min).
  2. Válida si: no está marcada como dañada, su último dato tiene ≤ 30 min, cubre ≥ 80 % de las
     ventanas de 1 y 3 h, y no marca 0 mm en 3 h mientras otra válida marca ≥ 10 mm.
  3. R_v = máximo entre las válidas de (peso × lluvia en la ventana v).
  4. Humedad previa: P5d = lluvia de los 5 días que terminan 24 h antes. Si P5d > 53 mm, los
     umbrales de 1, 3 y 24 h se multiplican por 0,8 (no los de 72 h).
  5. Nivel instantáneo: el primero (de «muy alto» a «medio») con ALGUNA ventana ≥ su umbral; si
     ninguna, «bajo». Sin estaciones válidas: sin nivel.
  6. Nivel mostrado: el más alto de los instantáneos de las últimas 8 h (persistencia).
  7. Los niveles puestos a mano por reportes de campo (estimaciones/nivel_manual.csv) solo suben.

Lo único que no se puede reproducir sin la base es el «silencio en alerta» (si todas las
estaciones callan con el nivel en «alto» o más, sube a «muy alto»): depende de si el recolector
consultó bien la fuente, y eso no está en el ZIP. Con --silencio se aplica suponiendo que sí.

Es un modelo propio y preliminar, NO un dato ni una alerta oficial.

Ejemplos:
  python3 -I nivel.py --zona la-cascada --desde 2026-10-30T12:00Z --hasta 2026-11-01T12:00Z
  python3 -I nivel.py --desde 2026-11-20T12:00Z --hasta 2026-11-22T00:00Z --salida niveles.csv
  python3 -I nivel.py --comparar            # contra los niveles que publicó la página
  python3 -I nivel.py --verificar           # comprueba los dos desbordamientos de La Cascada
"""
import argparse
import bisect
import csv
import datetime as dt
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://sosgalapagos.org/clima/datos/descargas/clima_galapagos_todo.zip"
UTC = dt.timezone.utc
VENTANAS = (("R1h", 1), ("R3h", 3), ("R24h", 24), ("R72h", 72))
PASO_MIN = 5          # una medición cada 5 min en todas las fuentes de lluvia
FRESCURA_MAX_MIN = 30
HORARIAS = ("inamhi", "weatherlink")  # sus filas con segundos :30 son respaldos de 1 h (= 12 registros)

# Lo que se sabe de cada desbordamiento de La Cascada (para --verificar). Horas en UTC.
EVENTOS = {
    "2026-10-30": {"zona": "la-cascada", "impacto": "2026-10-31T03:20:00Z", "desde": "2026-10-30T12:00:00Z"},
    "2026-11-21": {"zona": "la-cascada", "impacto": "2026-11-21T11:00:00Z", "desde": "2026-11-20T12:00:00Z"},
}


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fecha(texto):
    texto = texto.strip().replace("Z", "+00:00")
    t = dt.datetime.fromisoformat(texto if len(texto) > 10 else texto + "T00:00:00+00:00")
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t.astimezone(UTC)


def abrir_zip(ruta):
    if ruta:
        return zipfile.ZipFile(ruta)
    cache = Path.home() / ".cache" / "sosgalapagos" / "clima_galapagos_todo.zip"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        print(f"Bajando {URL} …", file=sys.stderr)
        with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "sosgalapagos-replicar"}), timeout=120) as r:
            cache.write_bytes(r.read())
    return zipfile.ZipFile(cache)


def leer_csv(z, nombre):
    with z.open(nombre) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))


class Datos:
    """La regla, los daños y las series de lluvia de las estaciones de las zonas, entre dos fechas."""

    def __init__(self, z, desde, hasta):
        self.regla = json.loads(z.read("regla/umbrales_inundacion.json"))
        claves = {c for zona in self.regla["zonas"] for c, _ in zona["estaciones"]}
        self.danos = {}
        for d in leer_csv(z, "regla/estaciones_danadas.csv"):
            if d["variable"] == "lluvia_mm":
                self.danos.setdefault(f"{d['fuente']}/{d['estacion']}", []).append(
                    (fecha(d["desde_utc"]), fecha(d["hasta_utc"]) if d["hasta_utc"] else None))
        # Hace falta historia antes de «desde»: 72 h de ventana + 8 h de persistencia + 6 días de P5d.
        inicio = desde - dt.timedelta(hours=72 + 8 + 24 + 120 + 1)
        crudo = {}
        meses = sorted(n for n in z.namelist() if n.startswith("mediciones/") and n.endswith(".csv"))
        for nombre in meses:
            mes = nombre[-11:-4]  # AAAA-MM
            if mes < inicio.strftime("%Y-%m") or mes > hasta.strftime("%Y-%m"):
                continue
            for f in leer_csv(z, nombre):
                if f["variable"] != "lluvia_mm":
                    continue
                clave = f"{f['fuente']}/{f['estacion']}"
                if clave not in claves:
                    continue
                t = fecha(f["ts_utc"])
                if inicio <= t <= hasta:
                    crudo.setdefault(clave, []).append((t, float(f["valor"] or 0)))
        self.series = {}
        for clave, filas in crudo.items():
            filas.sort()
            fuente = clave.split("/")[0]
            ts, cs, cn = [], [0.0], [0]
            for t, v in filas:
                ts.append(t.timestamp())
                cs.append(cs[-1] + v)
                cn.append(cn[-1] + (12 if fuente in HORARIAS and t.second == 30 else 1))
            self.series[clave] = (ts, cs, cn)
        self.manual = [dict(m, desde=fecha(m["desde_utc"]), hasta=fecha(m["hasta_utc"]))
                       for m in leer_csv(z, "estimaciones/nivel_manual.csv")] if "estimaciones/nivel_manual.csv" in z.namelist() else []

    def danada(self, clave, t):
        return any(a <= t and (b is None or t < b) for a, b in self.danos.get(clave, []))


def ventana(serie, fin, horas):
    ts, cs, cn = serie
    a = bisect.bisect_right(ts, (fin - dt.timedelta(hours=horas)).timestamp())
    b = bisect.bisect_right(ts, fin.timestamp())
    return cs[b] - cs[a], min(1.0, (cn[b] - cn[a]) / (horas * 60 / PASO_MIN))


def evaluar(D, zona, t):
    """Nivel instantáneo en t: (nivel o None, R, P5d, factor, estaciones válidas, callada)."""
    regla = D.regla
    cand, edad = {}, {}
    for clave, peso in zona["estaciones"]:
        if D.danada(clave, t) or clave not in D.series:
            continue
        s = D.series[clave]
        i = bisect.bisect_right(s[0], t.timestamp()) - 1
        if i < 0:
            continue
        ult = dt.datetime.fromtimestamp(s[0][i], UTC)
        edad[clave] = (t - ult).total_seconds() / 60
        cand[clave] = (peso, {k: ventana(s, ult, h) for k, h in VENTANAS}, ventana(s, ult - dt.timedelta(hours=24), 120))
    cortas = regla.get("cobertura_ventanas", ["R1h", "R3h", "R24h"])
    cob_min = regla["cobertura_minima"]
    validas = {c: x for c, x in cand.items()
               if edad[c] <= regla.get("frescura_max_min", FRESCURA_MAX_MIN) and min(x[1][k][1] for k in cortas) >= cob_min}
    callada = bool(cand) and all(e > regla.get("silencio_min", 60) for e in edad.values())
    r3 = {c: x[1]["R3h"][0] for c, x in validas.items()}
    for c in list(validas):
        if r3[c] == 0 and any(o >= regla["excluir_cero_si_otra_mm_3h"] for k, o in r3.items() if k != c):
            validas.pop(c)
    if not validas:
        return None, {}, None, 1.0, [], callada
    R = {k: round(max(p * v[k][0] for p, v, _ in validas.values()), 1) for k, _ in VENTANAS}
    p5 = [p * x[0] for p, _, x in validas.values() if x[1] >= cob_min]
    P5d = round(max(p5), 1) if p5 else None
    ha = regla["humedad_antecedente"]
    factor = ha["humedo"]["factor"] if P5d is not None and P5d > ha["humedo"]["min"] else (
        ha["seco"]["factor"] if P5d is not None and P5d < ha["seco"]["max"] else ha["normal"]["factor"])
    if zona.get("ajuste_humedad") is False:
        factor = 1.0
    nivel = regla["niveles"][-1]["nivel"]
    for nv in regla["niveles"][:-1]:
        umbrales = (zona.get("umbrales") or {}).get(nv["nivel"], nv.get("si_alguno", {}))
        if any(R.get(k) is not None and R[k] >= u * (1.0 if k == "R72h" else factor) for k, u in umbrales.items()):
            nivel = nv["nivel"]
            break
    return nivel, R, P5d, factor, sorted(validas), callada


def calcular(D, zonas, desde, hasta, silencio=False, manual=True):
    """Filas cada 5 min, con el nivel instantáneo y el mostrado (persistencia, silencio, manual)."""
    regla = D.regla
    orden = [n["nivel"] for n in regla["niveles"]]
    pers = regla["persistencia_horas"]
    sil = regla.get("silencio_en_alerta")
    alerta = orden[:orden.index(sil["desde_nivel"]) + 1] if sil else []
    P = pers * 60 // PASO_MIN
    t0 = desde - dt.timedelta(hours=pers)
    t0 = t0.replace(minute=t0.minute - t0.minute % PASO_MIN, second=0, microsecond=0)
    n = int((hasta - t0).total_seconds() // (PASO_MIN * 60)) + 1
    muestras = [t0 + dt.timedelta(minutes=PASO_MIN * k) for k in range(n)]
    filas = []
    for zona in regla["zonas"]:
        if zonas and zona["id"] not in zonas:
            continue
        inst = []
        for i, t in enumerate(muestras):
            nivel, R, P5d, factor, validas, callada = evaluar(D, zona, t)
            inst.append(nivel)
            if t < desde:
                continue
            recientes = [x for x in inst[max(0, i - P):i] if x]
            if nivel is None:
                if silencio and sil and callada and any(x in alerta for x in recientes):
                    mostrado = sil["nivel"]
                else:
                    mostrado = min(recientes, key=orden.index) if recientes else None
            else:
                mostrado = min(recientes + [nivel], key=orden.index)
            m = next((m for m in D.manual if m["zona"] == zona["id"] and m["desde"] <= t < m["hasta"]), None) if manual else None
            if m and m["nivel"] in orden and (mostrado is None or orden.index(m["nivel"]) < orden.index(mostrado)):
                mostrado = m["nivel"]
            filas.append({"ts_utc": iso(t), "zona": zona["id"], "instantaneo": nivel or "", "nivel": mostrado or "sin datos",
                          **{k: R.get(k, "") for k, _ in VENTANAS}, "P5d": "" if P5d is None else P5d, "factor": factor,
                          "manual": "sí" if m and mostrado == m["nivel"] else "", "estaciones": " ".join(validas)})
    return filas


def cambios(filas):
    """Solo las filas en que cambia el nivel mostrado de una zona."""
    ultimo, salida = {}, []
    for f in filas:
        if ultimo.get(f["zona"]) != f["nivel"]:
            salida.append(f)
            ultimo[f["zona"]] = f["nivel"]
    return salida


def comparar(z, filas):
    """Coincidencia con estimaciones/nivel_zona.csv (lo que publicó la página cada 5 min)."""
    mias = {(f["zona"], f["ts_utc"][:15]): f for f in filas}  # misma zona y mismo bloque de 10 min
    total = igual_inst = igual_niv = 0
    for p in leer_csv(z, "estimaciones/nivel_zona.csv"):
        f = mias.get((p["zona"], p["calculado_utc"][:15]))
        if not f:
            continue
        total += 1
        igual_inst += (p["instantaneo"] or "") == f["instantaneo"]
        igual_niv += p["nivel"] == f["nivel"]
    return total, igual_inst, igual_niv


def verificar(z):
    """Primera hora en que la regla llega a cada nivel antes de cada desbordamiento conocido."""
    ok = True
    for nombre, ev in EVENTOS.items():
        impacto = fecha(ev["impacto"])
        D = Datos(z, fecha(ev["desde"]), impacto)
        filas = calcular(D, {ev["zona"]}, fecha(ev["desde"]), impacto, manual=False)
        primero = {}
        for f in filas:
            primero.setdefault(f["nivel"], f["ts_utc"])
        ma = primero.get("muy alto")
        antes = (impacto - fecha(ma)).total_seconds() / 3600 if ma else None
        print(f"{nombre} {ev['zona']}: desbordamiento {ev['impacto']} · medio {primero.get('medio', '—')} · "
              f"alto {primero.get('alto', '—')} · muy alto {ma or '—'}" + (f" ({antes:.1f} h antes)" if ma else ""))
        ok &= ma is not None and antes > 0
    print("OK: la regla llega a «muy alto» antes de los dos desbordamientos." if ok else "FALLA: revise la regla o los datos.")
    return ok


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--zip", help=f"ruta del ZIP (si no, baja {URL})")
    a.add_argument("--zona", action="append", help="la-cascada, santa-cruz-alta, san-cristobal o isabela (se puede repetir)")
    a.add_argument("--desde", help="inicio en UTC, p. ej. 2026-11-20T12:00Z (por omisión, 48 h antes de --hasta)")
    a.add_argument("--hasta", help="fin en UTC (por omisión, el último dato del ZIP)")
    a.add_argument("--salida", help="escribe aquí todas las filas (CSV, cada 5 min)")
    a.add_argument("--silencio", action="store_true", help="aplica el «silencio en alerta» suponiendo que la recolección funcionó")
    a.add_argument("--sin-manual", action="store_true", help="no aplica los niveles puestos a mano por reportes de campo")
    a.add_argument("--comparar", action="store_true", help="compara con los niveles publicados (estimaciones/nivel_zona.csv)")
    a.add_argument("--verificar", action="store_true", help="comprueba los desbordamientos de La Cascada del 30-oct y el 21-nov")
    o = a.parse_args()
    z = abrir_zip(o.zip)
    if o.verificar:
        sys.exit(0 if verificar(z) else 1)
    if o.hasta:
        hasta = fecha(o.hasta)
    else:
        ultimo = max(n for n in z.namelist() if n.startswith("mediciones/"))
        hasta = max(fecha(f["ts_utc"]) for f in leer_csv(z, ultimo))
    desde = fecha(o.desde) if o.desde else hasta - dt.timedelta(hours=48)
    if o.comparar and not o.desde:
        publicados = [fecha(p["calculado_utc"]) for p in leer_csv(z, "estimaciones/nivel_zona.csv")]
        desde = max(desde, min(publicados)) if publicados else desde
    D = Datos(z, desde, hasta)
    filas = calcular(D, set(o.zona or []), desde, hasta, silencio=o.silencio, manual=not o.sin_manual)
    if o.salida:
        with open(o.salida, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)
        print(f"{len(filas)} filas en {o.salida}", file=sys.stderr)
    print("ts_utc               zona             nivel      instantáneo  R1h    R3h    R24h   R72h   P5d    factor")
    for f in cambios(filas):
        print(f"{f['ts_utc']} {f['zona']:16s} {f['nivel']:10s} {f['instantaneo'] or '—':12s} "
              + " ".join(f"{str(f[k]):6s}" for k in ("R1h", "R3h", "R24h", "R72h", "P5d")) + f" {f['factor']}" + (" (reporte de campo)" if f["manual"] else ""))
    if o.comparar:
        total, ii, nn = comparar(z, filas)
        if total:
            print(f"\nContra lo publicado: {total} pasadas · nivel instantáneo igual en {ii / total:.1%} · nivel mostrado igual en {nn / total:.1%}")
        else:
            print("\nNo hay pasadas publicadas en ese intervalo.")


if __name__ == "__main__":
    main()
