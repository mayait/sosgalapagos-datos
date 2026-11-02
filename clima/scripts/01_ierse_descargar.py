#!/usr/bin/env python3
"""Descarga incremental de la red de estaciones IERSE-WSN Galápagos (U. del Azuay).

Fuente: red IERSE-WSN, Galápagos. El endpoint se lee de CLIMA_IERSE_API (entorno o
privado/fuentes.env, no versionado; ver fuentes.env.ejemplo).

Guarda un archivo por día en datos/ierse-wsn/crudos/AAAA-MM/AAAA-MM-DD.csv.gz con
las columnas: fecha_hora_local, estacion_id, variable, valor (tal cual las entrega
el servidor, sin redondeos ni filtros).

Solo usa la biblioteca estándar. Uso:
    python3 -I scripts/01_ierse_descargar.py                  # desde la última fecha guardada hasta hoy
    python3 -I scripts/01_ierse_descargar.py --desde 2026-04-01 --hasta 2026-11-02
    python3 -I scripts/01_ierse_descargar.py --rehacer 2026-10-31   # vuelve a bajar un día cerrado

Un día se marca «cerrado» cuando ya pasaron 2 días desde su fin; los días abiertos
(hoy y ayer) se vuelven a descargar en cada corrida, porque las estaciones
transmiten con retraso.
"""
import argparse
import csv
import datetime as dt
import gzip
import io
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def _api():
    import os
    ruta = Path(__file__).resolve().parent.parent / "privado" / "fuentes.env"
    if "CLIMA_IERSE_API" not in os.environ and ruta.exists():
        for linea in ruta.read_text().splitlines():
            if linea.strip().startswith("CLIMA_IERSE_API="):
                os.environ["CLIMA_IERSE_API"] = linea.split("=", 1)[1].strip().strip('"')
    if not os.environ.get("CLIMA_IERSE_API"):
        sys.exit("Falta CLIMA_IERSE_API (privado/fuentes.env)")
    return os.environ["CLIMA_IERSE_API"]


RED = "ntw003_glps"           # «Red Galápagos»
INICIO_RED = dt.date(2026, 4, 1)  # no hay datos antes de abril de 2026 (verificado el 2-nov-2026)
RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "datos" / "ierse-wsn"
CRUDOS = DIR / "crudos"
ESTADO = DIR / "estado.json"
ESTACIONES = DIR / "estaciones.json"
HILOS = 4                      # servidor universitario: concurrencia baja
GALAPAGOS = dt.timezone(dt.timedelta(hours=-6))


def post(endpoint, cuerpo=None, intentos=4):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    for i in range(intentos):
        try:
            req = urllib.request.Request(
                _api() + endpoint, data=datos, method="POST",
                headers={"Content-Type": "application/json",
                         "User-Agent": "sosgalapagos-clima/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if i == intentos - 1:
                raise
            time.sleep(3 * (i + 1))
            print(f"  reintento {endpoint} {cuerpo}: {e}", file=sys.stderr)


def cargar_json(ruta, defecto):
    return json.loads(ruta.read_text()) if ruta.exists() else defecto


def guardar_json(ruta, obj):
    ruta.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def bajar_dia(fecha, variables, estaciones_conocidas):
    """Devuelve (filas, resumen, estaciones_vistas) de un día."""
    d = fecha.isoformat()
    filas, resumen, vistas = [], {}, {}
    for var in variables:
        nodos = post("/nodes_var_date", {"req_var": var, "req_date": d, "req_netw": RED, "pub_query": "1"})
        for n in nodos:
            vistas[n["node_id"]] = n
            serie = post("/node_data", {"req_var": var, "req_date": d, "req_node": n["node_id"],
                                        "req_netw": RED, "pub_query": "1"})
            for p in serie:
                filas.append((p["timestamp"], n["node_id"], var, p["sensor_value"]))
            resumen.setdefault(var, {})[n["node_id"]] = len(serie)
    filas.sort()
    return filas, resumen, vistas


def escribir_dia(fecha, filas):
    ruta = CRUDOS / fecha.strftime("%Y-%m") / f"{fecha.isoformat()}.csv.gz"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["fecha_hora_local", "estacion_id", "variable", "valor"])
    for t, nodo, var, val in filas:
        w.writerow([t, nodo, var, "" if val is None else repr(float(val))])
    # mtime=0: si los datos no cambian, el archivo queda idéntico (git no ve cambios)
    with open(ruta, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz:
        gz.write(buf.getvalue().encode())
    return ruta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", type=dt.date.fromisoformat)
    ap.add_argument("--hasta", type=dt.date.fromisoformat)
    ap.add_argument("--rehacer", type=dt.date.fromisoformat, nargs="*", default=[])
    ap.add_argument("--todas-las-variables", action="store_true",
                    help="consulta también las variables que la red nunca ha tenido (más lento)")
    args = ap.parse_args()

    hoy = dt.datetime.now(GALAPAGOS).date()
    estado = cargar_json(ESTADO, {"dias": {}})
    estaciones = cargar_json(ESTACIONES, {})

    # Catálogo de variables públicas y estaciones operativas actuales
    sensores = post("/sensors", {"pub_query": "1"})
    variables = [s["sensor_id"] for s in sensores]
    if not args.todas_las_variables:
        # Cada variable vacía cuesta ~3,5 s por día. Se consultan solo las que la red
        # tiene hoy o ha tenido en algún día ya descargado.
        vistas = {v for d in estado["dias"].values() for v in d.get("registros", {})}
        hoy_activas = {v for v in variables if post("/nodes_var_date", {
            "req_var": v, "req_date": hoy.isoformat(), "req_netw": RED, "pub_query": "1"})}
        variables = [v for v in variables if v in vistas | hoy_activas]
    for n in post("/oper_nodes", {"req_netw": RED}):
        estaciones.setdefault(n["node_id"], {}).update(n)

    cerrados = {d for d, v in estado["dias"].items() if v.get("cerrado")}
    desde = args.desde or INICIO_RED
    hasta = args.hasta or hoy
    fechas = [desde + dt.timedelta(days=i) for i in range((hasta - desde).days + 1)]
    fechas = [f for f in fechas if f.isoformat() not in cerrados] + list(args.rehacer)
    fechas = sorted(set(fechas))
    if not fechas:
        print("Nada que descargar: todos los días están cerrados.")
        return
    print(f"Descargando {len(fechas)} días ({fechas[0]} → {fechas[-1]}), variables: {', '.join(variables)}")

    # Para cada día y variable, nodes_var_date dice qué estaciones tienen datos
    # (así aparecen solas las estaciones nuevas o retiradas). En nov-2026 Galápagos
    # solo tiene lluvia, temperatura, humedad y presión; UVI, PM y ruido vuelven vacíos.
    def tarea(f):
        return f, bajar_dia(f, variables, estaciones)

    t0 = time.time()
    with ThreadPoolExecutor(HILOS) as ex:
        for i, (f, (filas, resumen, vistas)) in enumerate(ex.map(tarea, fechas), 1):
            for nid, n in vistas.items():
                e = estaciones.setdefault(nid, {})
                for k in ("node_id", "node_name", "node_location", "node_lat", "node_long"):
                    e[k] = n.get(k, e.get(k))
                e["primer_dia"] = min(e.get("primer_dia", f.isoformat()), f.isoformat())
                e["ultimo_dia"] = max(e.get("ultimo_dia", f.isoformat()), f.isoformat())
            if filas:
                escribir_dia(f, filas)
            estado["dias"][f.isoformat()] = {
                "cerrado": (hoy - f).days >= 2,
                "descargado": dt.datetime.now(GALAPAGOS).isoformat(timespec="seconds"),
                "registros": resumen,
            }
            total = sum(sum(v.values()) for v in resumen.values())
            print(f"[{i}/{len(fechas)}] {f}  {total:6d} registros  ({time.time() - t0:.0f} s)", flush=True)
            if i % 10 == 0:  # guardar el avance por si se corta
                guardar_json(ESTADO, estado)
                guardar_json(ESTACIONES, estaciones)

    guardar_json(ESTADO, estado)
    guardar_json(ESTACIONES, estaciones)
    print("Listo.")


if __name__ == "__main__":
    main()
