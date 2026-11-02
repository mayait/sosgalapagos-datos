"""Copia la lluvia medida por la red IERSE-WSN (Universidad del Azuay) desde clima/datos/ a los datos de los estudios.

Hasta ahora estas copias se hacían a mano. Con este paso, el flujo incremental (scripts/flujo.py) detecta cuando llega
lluvia nueva a clima/datos/ierse-wsn/ y rehace solo lo que depende de ella.

Solo LEE ../clima/datos/ierse-wsn/ (no ejecuta los scripts de clima/):
  serie_5min.csv.gz    → estudios/la-cascada/datos/lluvia_ierse_30oct_5min.csv       (30 y 31-oct)
                       → estudios/la-cascada/datos/lluvia_ierse_validacion_5min.csv  (2–4 y 22–24-oct: días sin inundación reportada)
  diario.csv           → estudios/la-cascada/datos/lluvia_ierse_diaria.csv           (copia íntegra)
  estaciones.geojson   → estudios/la-cascada/datos/estaciones_ierse.geojson          (desde/hasta/registros del 30–31-oct)

Formato idéntico al de las copias manuales del 2-nov-2026 (comprobado byte a byte). Un archivo solo se reescribe si su
contenido cambia, para no disparar en cascada el resto del flujo.

Uso (desde geodatos/):  .venv/bin/python -I scripts/21_lluvia_ierse_estudios.py [--salida DIR] [--comprobar]
  --salida DIR   escribe en DIR en lugar de estudios/la-cascada/datos (para pruebas)
  --comprobar    no escribe; sale con código 1 si alguna copia está desactualizada
"""
import csv, gzip, io, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
IERSE = ROOT.parent / "clima/datos/ierse-wsn"
OUT = ROOT / "estudios/la-cascada/datos"
DIAS_EVENTO = {"2026-10-30", "2026-10-31"}
DIAS_VALIDACION = {"2026-10-02", "2026-10-03", "2026-10-04", "2026-10-22", "2026-10-23", "2026-10-24"}


def serie(filas, nombres, dias):
    sel = sorted((r for r in filas if r["fecha_hora_local"][:10] in dias), key=lambda r: (r["estacion_id"], r["fecha_hora_local"]))
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(("estacion_id", "estacion", "fecha_hora_local", "lluvia_mm"))
    for r in sel:
        w.writerow((r["estacion_id"], nombres[r["estacion_id"]], r["fecha_hora_local"], r["lluvia_mm"]))
    return b.getvalue(), sel


def estaciones(sel):
    g = json.loads((IERSE / "estaciones.geojson").read_text())
    for f in g["features"]:
        p = f["properties"]
        r = [x for x in sel if x["estacion_id"] == p["estacion_id"]]
        if r:
            p["desde"], p["hasta"], p["registros"] = r[0]["fecha_hora_local"], r[-1]["fecha_hora_local"], len(r)
    return json.dumps(g, ensure_ascii=False, indent=1) + "\n"


def main():
    salida = pathlib.Path(sys.argv[sys.argv.index("--salida") + 1]) if "--salida" in sys.argv else OUT
    comprobar = "--comprobar" in sys.argv
    nombres = {k: v["node_name"] for k, v in json.loads((IERSE / "estaciones.json").read_text()).items()}
    with gzip.open(IERSE / "serie_5min.csv.gz", "rt", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    ev, sel_ev = serie(filas, nombres, DIAS_EVENTO)
    va, _ = serie(filas, nombres, DIAS_VALIDACION)
    copias = {"lluvia_ierse_30oct_5min.csv": ev, "lluvia_ierse_validacion_5min.csv": va,
              "lluvia_ierse_diaria.csv": (IERSE / "diario.csv").read_text(encoding="utf-8"),
              "estaciones_ierse.geojson": estaciones(sel_ev)}
    salida.mkdir(parents=True, exist_ok=True)
    cambios = 0
    for nombre, txt in copias.items():
        p = salida / nombre
        igual = p.exists() and p.read_text(encoding="utf-8") == txt
        print(f"  {nombre}: {'sin cambios' if igual else ('DESACTUALIZADA' if comprobar else 'actualizada')}")
        if not igual:
            cambios += 1
            if not comprobar:
                p.write_text(txt, encoding="utf-8")
    if comprobar and cambios:
        sys.exit(1)


if __name__ == "__main__":
    main()
