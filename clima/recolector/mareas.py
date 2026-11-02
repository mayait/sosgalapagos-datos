"""Bloque de mareas del dashboard: predicción astronómica (scripts/05_mareas.py), nivel observado por los
mareógrafos IOC y anomalía (observado − predicho), que en 2026 recoge sobre todo la señal de El Niño.

Todas las alturas en cm respecto del nivel medio de referencia 2017–2024 de cada mareógrafo.
"""
import datetime as dt
import json
import os
from pathlib import Path

UTC = dt.timezone.utc
AQUI = Path(__file__).resolve().parent
PRED = AQUI / "mareas_prediccion.json"
VENTANA_H = 72
_cache = {}


def _pred():
    if PRED.exists() and _cache.get("mtime") != PRED.stat().st_mtime:
        _cache.update(mtime=PRED.stat().st_mtime, datos=json.loads(PRED.read_text()))
    return _cache.get("datos")


def calcular(con, ahora=None):
    P = _pred()
    if not P:
        return None
    ahora = ahora or dt.datetime.now(UTC)
    paso = dt.timedelta(minutes=P["paso_min"])
    ini = (ahora - dt.timedelta(hours=VENTANA_H)).replace(second=0, microsecond=0)
    ini -= dt.timedelta(minutes=ini.minute % P["paso_min"])
    fin = ahora + dt.timedelta(hours=VENTANA_H)
    out = {"referencia": "nivel medio 2017–2024 de cada mareógrafo", "metodo": P["metodo"], "estaciones": {}}
    for cod, e in P["estaciones"].items():
        t0 = dt.datetime.fromisoformat(e["t0"].replace("Z", "+00:00"))
        i0 = int((ini - t0) / paso)
        n = int((fin - ini) / paso)
        if i0 < 0 or i0 + n > len(e["h_cm"]):
            continue  # predicción fuera de rango: hay que regenerar scripts/05_mareas.py
        pred = e["h_cm"][i0:i0 + n]
        msl = e["nivel_medio_ref_cm_cero_uhslc"]
        # observado (cero UHSLC, m) → cm sobre el nivel medio, en bloques de 10 min
        obs = [None] * n
        acc = {}
        for ts, v in con.execute("SELECT ts, valor FROM obs WHERE fuente='ioc' AND estacion=? AND variable='nivel_mar_m' "
                                 "AND ts>=? AND valor IS NOT NULL", (cod, ini.strftime("%Y-%m-%dT%H:%M:%SZ"))):
            t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            k = int((t - ini) / paso)
            if 0 <= k < n:
                acc.setdefault(k, []).append(v * 100 - msl)
        for k, vs in acc.items():
            obs[k] = round(sum(vs) / len(vs), 1)
        # anomalía: observado − predicho en las últimas 6 h
        k_ahora = int((ahora - ini) / paso)
        difs = [obs[k] - pred[k] for k in range(max(0, k_ahora - 36), min(n, k_ahora + 1)) if obs[k] is not None]
        mens = e.get("anomalia_mensual_cm", {})
        if len(difs) >= 12:
            anom, fuente_anom = round(sum(difs) / len(difs), 1), "mareógrafo, últimas 6 h"
        elif mens:
            anom, fuente_anom = list(mens.values())[-1], f"media mensual UHSLC {list(mens)[-1]}"
        else:
            anom, fuente_anom = 0.0, "sin datos"
        ext = [x for x in e["extremos"] if ahora - dt.timedelta(hours=12) <= dt.datetime.fromisoformat(x[0].replace("Z", "+00:00")) <= fin]
        prox = [{"t": x[0], "tipo": "pleamar" if x[2] == "P" else "bajamar", "pred_cm": x[1],
                 "esperado_cm": round(x[1] + anom, 1)}
                for x in ext if dt.datetime.fromisoformat(x[0].replace("Z", "+00:00")) >= ahora]
        plea = [x for x in prox if x["tipo"] == "pleamar"]
        out["estaciones"][cod] = {
            "nombre": e["nombre"], "anomalia_cm": anom, "anomalia_fuente": fuente_anom,
            "anomalia_mensual_cm": dict(list(mens.items())[-18:]), "validacion": e["validacion"],
            "t0": ini.strftime("%Y-%m-%dT%H:%M:%SZ"), "paso_min": P["paso_min"], "ahora_i": k_ahora,
            "pred_cm": pred, "obs_cm": obs, "proximos": prox[:8],
            "max_72h": max(plea, key=lambda x: x["esperado_cm"]) if plea else None,
        }
    # modelo para puertos sin mareógrafo
    f = Path(os.environ.get("CLIMA_DB", "clima.db")).parent / "mar_modelo.json"
    if f.exists():
        m = json.loads(f.read_text())
        out["modelo"] = {}
        for cod, p in m.get("puertos", {}).items():
            t, h = p.get("t", []), p.get("nivel_m", [])
            picos = []
            for i in range(1, len(h) - 1):
                if None in (h[i - 1], h[i], h[i + 1]):
                    continue
                tt = dt.datetime.fromisoformat(t[i]).replace(tzinfo=UTC)
                if tt >= ahora and h[i] >= h[i - 1] and h[i] > h[i + 1]:
                    picos.append({"t": tt.strftime("%Y-%m-%dT%H:%M:%SZ"), "nivel_m": h[i]})
            olas = [x for x in p.get("ola_m", []) if x is not None]
            out["modelo"][cod] = {"nombre": p["nombre"], "pleamares": picos[:6],
                                  "ola_max_m": max(olas) if olas else None, "generado": m.get("generado")}
    return out
