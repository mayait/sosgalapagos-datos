"""Compara la lluvia de dos inundaciones de La Cascada (30-oct y 21-nov de 2026).

Lee la base del recolector (CLIMA_DB, solo lectura) y escribe en eventos/2026-11-21_inundacion/:
  resumen.json          lluvia máxima en 1, 3, 24 y 72 h por estación al momento de la inundación
  lluvia_5min.csv       serie de 5 min de las estaciones comparadas (UTC)
  niveles.csv           nivel instantáneo de la regla cada 10 min (sin persistencia), para La Cascada
                        antes y después de la calibración del 21-nov y para la parte alta
  f_comparacion.png     lluvia acumulada, intensidad horaria y nivel de la regla en los dos eventos

Uso: CLIMA_DB=ruta/clima.db python -I scripts/08_comparar_eventos.py
Las lluvias son medidas de estaciones (oficiales y particulares); el nivel es la estimación
preliminar de SOS Galápagos, no una alerta oficial.
"""
import datetime as dt
import json
import os
import sqlite3
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI / "recolector"))
import inundacion  # noqa: E402

UTC = dt.timezone.utc
SALIDA = AQUI / "eventos" / "2026-11-21_inundacion"
EVENTOS = {  # hora del desbordamiento reportado (UTC); Galápagos = UTC−6
    "30-oct": ("2026-10-31T03:20:00Z", "30-oct, 21:20 (informe de La Cascada)"),
    "21-nov": ("2026-11-21T11:00:00Z", "21-nov, ~05:00 (reporte de campo)"),
}
ANTES_H, DESPUES_H = 30, 3
ESTACIONES = [  # clave, etiqueta, color, zona
    ("ambient/miconia", "Miconia · 422 m", "#1d4ed8", "alta"),
    ("ierse/n_glps09", "Santa Rosa · 416 m", "#7c3aed", "alta"),
    ("ierse/n_glps05", "Los Guayabillos · 178 m", "#9ca3af", "media"),
    ("ambient/epmapasc_espol", "EPMAPASC · 22 m", "#0f766e", "costa"),
    ("ambient/evolucion", "Evolución · 10 m", "#16a34a", "costa"),
    ("weatherlink/pa_weatherlink", "Erna · 10 m", "#d97706", "costa"),
    ("wunderground/casa_marina", "Casa Marina · 3 m", "#dc2626", "costa"),
    ("tempest/punta_estrada", "Punta Estrada · 8 m", "#be185d", "costa"),
]
NUEVAS = {"ambient/evolucion", "wunderground/casa_marina"}  # añadidas a La Cascada el 21-nov
FRANJAS = {"la-cascada-anterior": "La Cascada\n(regla anterior)", "la-cascada": "La Cascada\n(calibrada 21-nov)",
           "santa-cruz-alta": "Parte alta"}
NIVELES = {"muy alto": "#7f1d1d", "alto": "#dc2626", "medio": "#d97706", "bajo": "#16a34a", None: "#d1d5db"}


def t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def serie(con, clave, t0):
    f, e = clave.split("/")
    a, b = t0 - dt.timedelta(hours=ANTES_H + 72), t0 + dt.timedelta(hours=DESPUES_H)
    filas = con.execute("SELECT ts, valor FROM obs WHERE fuente=? AND estacion=? AND variable='lluvia_mm' "
                        "AND ts>=? AND ts<? AND substr(ts,18,2)!='30' ORDER BY ts",
                        (f, e, a.strftime("%Y-%m-%dT%H:%M:%SZ"), b.strftime("%Y-%m-%dT%H:%M:%SZ"))).fetchall()
    if not filas:
        return None
    s = pd.Series([v or 0.0 for _, v in filas], index=pd.to_datetime([x for x, _ in filas], utc=True))
    return s.groupby(level=0).sum()


def ventana(s, fin, horas):
    """Lluvia y cobertura (fracción de registros de 5 min) en (fin − horas, fin]."""
    x = s[(s.index > fin - pd.Timedelta(hours=horas)) & (s.index <= fin)]
    return float(x.sum()), min(1.0, len(x) / (horas * 12))


def maximo(s, fin, horas, desde):
    """Máximo móvil de `horas` entre desde y fin (pasos de 5 min)."""
    mejor, cuando = 0.0, None
    for u in pd.date_range(desde, fin, freq="5min"):
        v, _ = ventana(s, u, horas)
        if v > mejor:
            mejor, cuando = v, u
    return round(mejor, 1), cuando


def niveles(con, t0):
    """Nivel instantáneo de la regla del sitio (umbrales actuales) cada 10 min, por zona."""
    nombres = {f"{f}/{e}": n for f, e, n in con.execute("SELECT fuente, estacion, nombre FROM estaciones")}
    zonas = {z["id"]: z for z in inundacion.REGLA["zonas"] if z["id"] in ("la-cascada", "santa-cruz-alta")}
    zonas["la-cascada-anterior"] = dict(zonas["la-cascada"],
                                        estaciones=[x for x in zonas["la-cascada"]["estaciones"] if x[0] not in NUEVAS])
    desde = t0 - dt.timedelta(hours=ANTES_H + 72 + 121)
    claves = {c for z in zonas.values() for c, _ in z["estaciones"]}
    series = {c: x for c in claves if (x := inundacion._serie(con, c, desde))[1]}
    out = []
    for k in range(-ANTES_H * 6, DESPUES_H * 6 + 1):
        u = t0 + dt.timedelta(minutes=10 * k)
        fila = {"ts": u.strftime("%Y-%m-%dT%H:%M:%SZ"), "h": k / 6}
        for zid, z in zonas.items():
            nv, R, *_ = inundacion._evaluar(series, z, u, nombres)
            fila[zid] = nv["nivel"] if nv else None
            fila[zid + "_R"] = R
        out.append(fila)
    return out


def main():
    db = os.environ.get("CLIMA_DB")
    if not db:
        sys.exit("Falta CLIMA_DB (ruta a una copia de clima.db)")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    ahora = pd.Timestamp(con.execute("SELECT MAX(ts) FROM obs WHERE variable='lluvia_mm'").fetchone()[0])
    SALIDA.mkdir(parents=True, exist_ok=True)
    resumen = {"nota": "Lluvia medida por estaciones; el nivel es la estimación preliminar de SOS Galápagos, "
                       "no una alerta oficial. Horas en UTC; Galápagos = UTC−6.",
               "eventos": {}, "datos_hasta": ahora.strftime("%Y-%m-%dT%H:%M:%SZ")}
    datos, filas_csv, lv = {}, [], {}
    for ev, (t0s, etiqueta) in EVENTOS.items():
        t0 = t(t0s)
        T0 = pd.Timestamp(t0)
        res = {"desbordamiento": t0s, "etiqueta": etiqueta, "estaciones": {}}
        for clave, nom, _, zona in ESTACIONES:
            s = serie(con, clave, t0)
            danada = inundacion.danada(clave, "lluvia_mm", t0)
            if s is None or ventana(s, T0, 24)[1] < 0.5:
                continue
            datos[(ev, clave)] = s
            for i, v in s[s.index >= T0 - pd.Timedelta(hours=ANTES_H)].items():
                filas_csv.append({"evento": ev, "estacion": clave, "ts": i.strftime("%Y-%m-%dT%H:%M:%SZ"), "lluvia_mm": v})
            r = {"nombre": nom, "zona": zona, "danada": bool(danada)}
            desde = T0 - pd.Timedelta(hours=24)
            for k, h in (("R1h", 1), ("R3h", 3)):
                v, cuando = maximo(s, T0, h, desde)
                r[f"max_{k}"] = v
                r[f"max_{k}_fin"] = cuando.strftime("%Y-%m-%dT%H:%M:%SZ") if cuando is not None else None
            for k, h in (("R24h", 24), ("R72h", 72)):
                v, cob = ventana(s, T0, h)
                r[k] = round(v, 1)
                r[k + "_cobertura"] = round(cob, 2)
            r["P5d_antes"] = round(ventana(s, T0 - pd.Timedelta(hours=24), 120)[0], 1)
            res["estaciones"][clave] = r
        lv[ev] = niveles(con, t0)
        for zid in FRANJAS:
            primero = {}
            for f in lv[ev]:
                if f[zid] and f[zid] not in primero:
                    primero[f[zid]] = round(f["h"], 2)
            res[f"nivel_regla_{zid}"] = {"al_desbordar": next(f[zid] for f in lv[ev] if f["h"] == 0),
                                         "primera_hora_relativa": primero}
        resumen["eventos"][ev] = res
    pd.DataFrame(filas_csv).to_csv(SALIDA / "lluvia_5min.csv", index=False)
    pd.DataFrame([{k: v for k, v in f.items() if not k.endswith("_R")} | {"evento": ev}
                  for ev in lv for f in lv[ev]]).to_csv(SALIDA / "niveles.csv", index=False)
    (SALIDA / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1) + "\n")
    figura(datos, lv, resumen, ahora)


def figura(datos, lv, resumen, ahora):
    fig = plt.figure(figsize=(13, 10.5), constrained_layout=True)
    g = fig.add_gridspec(5, 2, height_ratios=[3.2, 2.0, 0.4, 0.4, 0.4])
    lim = max(float(s[(s.index > pd.Timestamp(t(EVENTOS[ev][0])) - pd.Timedelta(hours=24))].sum())
              for (ev, c), s in datos.items() if not resumen["eventos"][ev]["estaciones"][c]["danada"]) * 1.08
    for j, (ev, (t0s, etiqueta)) in enumerate(EVENTOS.items()):
        T0 = pd.Timestamp(t(t0s))
        ax = fig.add_subplot(g[0, j])
        for clave, nom, color, _ in ESTACIONES:
            s = datos.get((ev, clave))
            if s is None:
                continue
            x = s[(s.index > T0 - pd.Timedelta(hours=24)) & (s.index <= T0 + pd.Timedelta(hours=DESPUES_H))]
            h = (x.index - T0).total_seconds() / 3600
            if resumen["eventos"][ev]["estaciones"][clave]["danada"]:
                ax.plot([], [], color=color, ls=":", label=nom + ": dañada, fuera de escala y del cálculo")
                continue
            ax.plot(h, x.cumsum(), color=color, lw=2, label=nom)
        ax.axvline(0, color="#111", lw=1)
        ax.text(0.2, lim * 0.97, "desbordamiento", va="top", fontsize=9)
        for u in (100, 150):
            ax.axhline(u, color=NIVELES["alto" if u == 100 else "muy alto"], lw=0.8, ls="--")
        ax.text(-23.8, 101, "umbral «alto» en 24 h", fontsize=8, color=NIVELES["alto"])
        ax.text(-23.8, 151, "umbral «muy alto» en 24 h", fontsize=8, color=NIVELES["muy alto"])
        ax.set_xlim(-24, DESPUES_H)
        ax.set_ylim(0, lim)
        ax.set_title(f"{etiqueta}: lluvia acumulada desde 24 h antes", fontsize=11, loc="left")
        ax.set_ylabel("mm")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="upper left", frameon=False)
        if ev == "21-nov" and ahora < T0 + pd.Timedelta(hours=DESPUES_H):
            ax.axvspan((ahora - T0).total_seconds() / 3600, DESPUES_H, color="#f3f4f6", zorder=0)
        # intensidad horaria: estaciones de la parte alta y de la costa
        ax2 = fig.add_subplot(g[1, j], sharex=ax)
        ancho = 0.4
        for k, (zona, color, nombre) in enumerate((("alta", "#1d4ed8", "parte alta (máx. Miconia/Santa Rosa)"),
                                                   ("costa", "#d97706", "costa (máx. Puerto Ayora)"))):
            horas = {}
            for clave, _, _, z in ESTACIONES:
                s = datos.get((ev, clave))
                if s is None or z != zona or resumen["eventos"][ev]["estaciones"][clave]["danada"]:
                    continue
                x = s[(s.index > T0 - pd.Timedelta(hours=24)) & (s.index <= T0 + pd.Timedelta(hours=DESPUES_H))]
                hh = ((x.index - T0).total_seconds() // 3600).astype(int)
                for hora, v in x.groupby(hh).sum().items():
                    horas[hora] = max(horas.get(hora, 0), v)
            ax2.bar([h + 0.5 + (k - 0.5) * ancho for h in horas], list(horas.values()), width=ancho,
                    color=color, label=nombre)
        ax2.axvline(0, color="#111", lw=1)
        ax2.axhline(30, color=NIVELES["alto"], lw=0.8, ls="--")
        ax2.axhline(45, color=NIVELES["muy alto"], lw=0.8, ls="--")
        ax2.set_ylim(0, 75)
        ax2.set_ylabel("mm por hora")
        ax2.grid(alpha=0.25)
        ax2.legend(fontsize=8, loc="upper left", frameon=False)
        for i, zid in enumerate(FRANJAS):
            ax3 = fig.add_subplot(g[2 + i, j], sharex=ax)
            for f in lv[ev]:
                ax3.axvspan(f["h"], f["h"] + 1 / 6, color=NIVELES.get(f[zid], "#d1d5db"), lw=0)
            ax3.axvline(0, color="#111", lw=1)
            ax3.set_yticks([])
            ax3.set_ylabel(FRANJAS[zid], rotation=0, ha="right", va="center", fontsize=9)
            if i == len(FRANJAS) - 1:
                ax3.set_xlabel("horas respecto del desbordamiento")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c, label=n or "sin datos") for n, c in NIVELES.items()], loc="lower center",
               ncol=5, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.06),
               title="nivel que daba la regla del sitio (instantáneo, umbrales actuales)", title_fontsize=9)
    fig.suptitle("Inundaciones de La Cascada: 30-oct vs 21-nov de 2026 · lluvia medida y nivel preliminar "
                 "(estimación de SOS Galápagos, no alerta oficial)", fontsize=12)
    fig.savefig(SALIDA / "f_comparacion.png", dpi=130, bbox_inches="tight")


if __name__ == "__main__":
    main()
