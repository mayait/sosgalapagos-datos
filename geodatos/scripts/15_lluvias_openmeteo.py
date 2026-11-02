#!/usr/bin/env python3
"""Descarga de Open-Meteo la lluvia horaria y diaria estimada por varios modelos
(15-oct a 2-nov-2026) en puntos de Santa Cruz y San Cristóbal, en hora de Galápagos.

Se pide directamente con timezone=Pacific/Galapagos (UTC−6), así que los días
naturales y las horas ya están en hora local de Galápagos. Cada valor horario es
la lluvia de la hora que termina en la marca (convención de Open-Meteo).

Uso, desde geodatos/:
    .venv/bin/python -I scripts/15_lluvias_openmeteo.py
Salidas: estudios/{santa-cruz,san-cristobal}/datos/lluvias/crudo/om_<punto>_<modelo>.json
         estudios/{...}/datos/lluvias/modelos_diaria.csv y modelos_horaria.csv
"""
import csv
import json
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "estudios"
MODELOS = ["ecmwf_ifs", "ecmwf_ifs025", "gfs_seamless", "icon_seamless",
           "jma_seamless", "meteofrance_seamless", "ukmo_seamless"]
PUNTOS = {
    "santa-cruz": {
        "los_guayabillos": (-0.6991, -90.3420),
        "santa_rosa_ierse": (-0.6545, -90.4035),
        "cerro_crocker": (-0.6424, -90.3260),
        "militar_baltra": (-0.4900, -90.2808),
        "puerto_ayora": (-0.7350, -90.3140),
        "tomas_de_berlanga": (-0.7109, -90.3198),
    },
    "san-cristobal": {
        "puerto_baquerizo_moreno": (-0.9015, -89.6105),
        "usfq_gsc": (-0.8955, -89.6089),
        "el_progreso": (-0.9071, -89.5569),
        "el_junco": (-0.8940, -89.4800),
    },
}
URL = ("https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}"
       "&past_days=31&forecast_days=1&hourly=precipitation&daily=precipitation_sum"
       "&timezone=Pacific%2FGalapagos&models={m}")


def main():
    for estudio, puntos in PUNTOS.items():
        d = RAIZ / estudio / "datos" / "lluvias"
        (d / "crudo").mkdir(parents=True, exist_ok=True)
        diaria, horaria, celdas = [], [], []
        for p, (la, lo) in puntos.items():
            for m in MODELOS:
                f = d / "crudo" / f"om_{p}_{m}.json"
                if not f.exists():
                    with urllib.request.urlopen(URL.format(la=la, lo=lo, m=m), timeout=90) as r:
                        f.write_bytes(r.read())
                    time.sleep(0.3)
                j = json.loads(f.read_text())
                celdas.append((p, la, lo, m, round(j["latitude"], 4), round(j["longitude"], 4)))
                for t, v in zip(j["daily"]["time"], j["daily"]["precipitation_sum"]):
                    if "2026-10-15" <= t <= "2026-11-01" and v is not None:
                        diaria.append((t, p, m, v))
                for t, v in zip(j["hourly"]["time"], j["hourly"]["precipitation"]):
                    if "2026-10-29T00:00" <= t <= "2026-11-02T00:00" and v is not None:
                        horaria.append((t, p, m, v))
        for nombre, filas, cab in [("modelos_diaria.csv", diaria, ["fecha", "punto", "modelo", "mm"]),
                                   ("modelos_horaria.csv", horaria, ["fecha_hora_local_fin", "punto", "modelo", "mm"]),
                                   ("modelos_celdas.csv", celdas, ["punto", "lat", "lon", "modelo", "lat_celda", "lon_celda"])]:
            with open(d / nombre, "w", newline="") as o:
                w = csv.writer(o)
                w.writerow(cab)
                w.writerows(filas)
        print(estudio, len(diaria), len(horaria))


if __name__ == "__main__":
    main()
