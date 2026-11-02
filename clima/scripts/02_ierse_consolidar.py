#!/usr/bin/env python3
"""Consolida los crudos diarios de IERSE-WSN en tablas listas para análisis y simulación.

Entradas: datos/ierse-wsn/crudos/**/*.csv.gz y estaciones.json (de 01_ierse_descargar.py)
Salidas (en datos/ierse-wsn/):
  serie_5min.csv.gz  una fila por estación y registro (≈5 min), variables en columnas
  horario.csv        agregados por hora
  diario.csv         agregados por día, con la cobertura (porcentaje de registros recibidos)
  estaciones.geojson estaciones con coordenadas, fechas y altitud estimada (DEM Copernicus 30 m)

Necesita pandas (y rasterio para la altitud). Uso, desde clima/:
    ../geodatos/.venv/bin/python -I scripts/02_ierse_consolidar.py
"""
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "datos" / "ierse-wsn"
DEM = RAIZ.parent / "geodatos" / "descargas" / "dem_recortes" / "santa_cruz_dem.tif"
REGISTROS_DIA = 288  # las estaciones transmiten cada ~5 min

COLUMNAS = {  # variable del servidor → columna, conversión
    "RAIN": ("lluvia_mm", 1.0),
    "Temperature": ("temp_c", 1.0),
    "Humidity": ("hr_pct", 1.0),
    "Pressure": ("presion_hpa", 0.01),  # el servidor la da en Pa
}


def redondear(df, n):
    num = df.select_dtypes("number").columns
    return df.assign(**{c: df[c].round(n) for c in num})


def leer_crudos():
    archivos = sorted((DIR / "crudos").glob("*/*.csv.gz"))
    df = pd.concat((pd.read_csv(a) for a in archivos), ignore_index=True)
    df["fecha_hora_local"] = pd.to_datetime(df["fecha_hora_local"])
    df = df[df["variable"].isin(COLUMNAS)].drop_duplicates(["fecha_hora_local", "estacion_id", "variable"])
    ancha = df.pivot(index=["estacion_id", "fecha_hora_local"], columns="variable", values="valor")
    ancha = ancha.rename(columns={k: v[0] for k, v in COLUMNAS.items()})
    for k, (col, f) in COLUMNAS.items():
        if col in ancha:
            ancha[col] = ancha[col] * f
    return ancha.reset_index().sort_values(["estacion_id", "fecha_hora_local"])


def agregar(df, frecuencia, etiqueta):
    g = df.groupby(["estacion_id", pd.Grouper(key="fecha_hora_local", freq=frecuencia)])
    out = pd.DataFrame({
        "lluvia_mm": g["lluvia_mm"].sum(min_count=1),
        "temp_c_media": g["temp_c"].mean(),
        "temp_c_min": g["temp_c"].min(),
        "temp_c_max": g["temp_c"].max(),
        "hr_pct_media": g["hr_pct"].mean(),
        "presion_hpa_media": g["presion_hpa"].mean(),
        "registros": g.size(),
    }).reset_index().rename(columns={"fecha_hora_local": etiqueta})
    return out[out["registros"] > 0]


def main():
    est = json.loads((DIR / "estaciones.json").read_text())
    nombres = {k: v.get("node_name") for k, v in est.items()}
    df = leer_crudos()

    redondear(df, 3).to_csv(DIR / "serie_5min.csv.gz", index=False, date_format="%Y-%m-%dT%H:%M:%S",
                       compression={"method": "gzip", "mtime": 0})

    h = agregar(df, "1h", "fecha_hora_local")
    h.insert(1, "estacion", h["estacion_id"].map(nombres))
    redondear(h, 3).to_csv(DIR / "horario.csv", index=False, date_format="%Y-%m-%dT%H:%M")

    d = agregar(df, "1D", "fecha")
    lluvia_max_1h = (h.assign(fecha=h["fecha_hora_local"].dt.floor("D"))
                      .groupby(["estacion_id", "fecha"])["lluvia_mm"].max().rename("lluvia_max_1h_mm"))
    d = d.merge(lluvia_max_1h, on=["estacion_id", "fecha"], how="left")
    d["cobertura_pct"] = (100 * d["registros"] / REGISTROS_DIA).clip(upper=100).round(0)
    d.insert(1, "estacion", d["estacion_id"].map(nombres))
    cols = ["fecha", "estacion_id", "estacion", "lluvia_mm", "lluvia_max_1h_mm", "temp_c_media",
            "temp_c_min", "temp_c_max", "hr_pct_media", "presion_hpa_media", "registros", "cobertura_pct"]
    redondear(d[cols], 2).to_csv(DIR / "diario.csv", index=False, date_format="%Y-%m-%d")

    # Estaciones con altitud estimada desde el DEM (si está disponible localmente)
    alt = {}
    if DEM.exists():
        try:
            import rasterio
            with rasterio.open(DEM) as r:
                for k, v in est.items():
                    val = next(r.sample([(v["node_long"], v["node_lat"])]))[0]
                    alt[k] = None if val == r.nodata else round(float(val))
        except Exception as e:  # noqa: BLE001
            print("Sin altitud del DEM:", e)
    primero = df.groupby("estacion_id")["fecha_hora_local"].agg(["min", "max", "size"])
    feats = []
    for k, v in sorted(est.items()):
        p = primero.loc[k] if k in primero.index else None
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [v["node_long"], v["node_lat"]]},
                      "properties": {"estacion_id": k, "nombre": v.get("node_name"),
                                     "ubicacion": v.get("node_location"),
                                     "altitud_m_dem": alt.get(k),
                                     "desde": None if p is None else p["min"].isoformat(),
                                     "hasta": None if p is None else p["max"].isoformat(),
                                     "registros": None if p is None else int(p["size"]),
                                     "fuente": "IERSE-WSN, Universidad del Azuay"}})
    (DIR / "estaciones.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=1) + "\n")

    print(f"{len(df)} registros, {df['estacion_id'].nunique()} estaciones, "
          f"{df['fecha_hora_local'].min()} → {df['fecha_hora_local'].max()}")
    print(d.groupby("estacion")[["lluvia_mm", "cobertura_pct"]].agg({"lluvia_mm": "sum", "cobertura_pct": "mean"}).round(1))


if __name__ == "__main__":
    main()
