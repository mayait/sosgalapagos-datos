"""Figuras y cifras del Informe técnico 2026-10 (infraestructura abierta de datos).

Uso (desde la raíz del repositorio):
    geodatos/.venv/bin/python -I informes/2026-10-infraestructura/figuras.py

Solo lee: el grafo declarado en geodatos/flujo.toml (con las funciones de geodatos/scripts/flujo.py, sin ejecutar
ningún paso ni tocar geodatos/.flujo/) y el inventario de crudos de clima/datos/. No usa red.

Salidas (en figuras/):
  flujo_grafo.png   grafo de pasos del flujo incremental (reducción transitiva), por niveles
  crudos.png        archivos diarios de crudos IERSE por mes y cobertura diaria de la red
  resumen.json      cifras citadas en el informe (pasos, aristas, alcance de cambios típicos, crudos)
"""
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "geodatos/scripts"))
import flujo  # noqa: E402

OUT = AQUI / "figuras"
OUT.mkdir(exist_ok=True)

COL = {"normal": "#e5e7eb", "pesado": "#fca5a5", "red": "#bfdbfe", "siempre": "#bbf7d0", "manual": "#fde68a"}


def tipo(p):
    return "manual" if p.manual else "pesado" if p.pesado else "red" if p.red else "siempre" if p.siempre else "normal"


def grafo():
    pasos = flujo.cargar()
    G = nx.DiGraph()
    for n, p in pasos.items():
        G.add_node(n, tipo=tipo(p))
        for d in p.deps:
            G.add_edge(d, n)
    return pasos, G


def alcance(pasos, G, rutas):
    """Pasos que se rehacen si cambia RUTA: los que la leen y todo lo que depende de ellos."""
    out = {}
    for r in rutas:
        directos = {n for n, p in pasos.items() if any(flujo.casa(r, pat) or r in flujo.resolver(pat) for pat in p.entradas + p.codigo)}
        todos = set(directos)
        for n in directos:
            todos |= nx.descendants(G, n)
        out[r] = dict(directos=sorted(directos), total=len(todos),
                      pesados=sorted(n for n in todos if pasos[n].pesado))
    return out


def fig_grafo(G):
    R = nx.transitive_reduction(G)
    R.add_nodes_from(G.nodes(data=True))
    # niveles «lo más tarde posible»: cada paso queda justo antes del primero que lo usa
    largo = {}
    for n in nx.topological_sort(G):
        largo[n] = max([largo[d] + 1 for d in G.predecessors(n)], default=0)
    total = max(largo.values())
    nivel = {}
    for n in reversed(list(nx.topological_sort(G))):
        nivel[n] = min([nivel[s] - 1 for s in G.successors(n)], default=total)
    capas = {}
    for n in sorted(G):
        capas.setdefault(nivel[n], []).append(n)
    orden = {n: i for k in capas for i, n in enumerate(capas[k])}
    ks = sorted(capas)
    for it in range(12):  # barridos de baricentro hacia la derecha y hacia la izquierda
        secuencia = ks[1:] if it % 2 == 0 else ks[-2::-1]
        for k in secuencia:
            vecinos = (lambda n: list(R.predecessors(n))) if it % 2 == 0 else (lambda n: list(R.successors(n)))
            capas[k].sort(key=lambda n: (sum(orden[v] for v in vecinos(n)) / len(vecinos(n))) if vecinos(n) else orden[n])
            for i, n in enumerate(capas[k]):
                orden[n] = i
    altura = max(len(v) for v in capas.values())
    pos = {}
    for k, v in capas.items():
        off = (altura - len(v)) / 2
        for i, n in enumerate(v):
            pos[n] = (k * 2.6, -(i + off) * 0.78)
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.set_xlim(min(x for x, _ in pos.values()) - 1.3, max(x for x, _ in pos.values()) + 1.3)
    ax.set_ylim(min(y for _, y in pos.values()) - 0.5, 0.5)
    ax.axis("off")
    caja = {}
    for n, (x, y) in pos.items():
        et = n.replace("_", " ")
        if len(et) > 15:  # etiquetas largas en dos líneas
            corte = et.rfind(" ", 0, len(et) // 2 + 4)
            et = et[:corte] + "\n" + et[corte + 1:]
        caja[n] = ax.text(x, y, et, ha="center", multialignment="center", va="center", fontsize=6.6, zorder=3,
                          bbox=dict(boxstyle="round,pad=0.25", fc=COL[G.nodes[n]["tipo"]], ec="#374151", lw=0.5))
    for a, b in R.edges():
        ax.annotate("", xy=(0, 0.5), xycoords=caja[b], xytext=(1, 0.5), textcoords=caja[a], zorder=1,
                    arrowprops=dict(arrowstyle="-|>", lw=0.55, color="#6b7280", shrinkA=1, shrinkB=1, mutation_scale=6,
                                    connectionstyle="arc3,rad=0.06"))
    hs = [plt.Rectangle((0, 0), 1, 1, fc=COL[k], ec="#374151", lw=0.5) for k in ("normal", "pesado", "red", "manual", "siempre")]
    ax.legend(hs, ["paso normal", "pesado (modelo 2D, tormentas)", "baja datos de internet", "manual", "control (corre siempre)"],
              loc="upper center", fontsize=7, frameon=False, ncol=5, bbox_to_anchor=(0.5, 0.02))
    fig.savefig(OUT / "flujo_grafo.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return R, total + 1


def crudos():
    base = RAIZ / "clima/datos/ierse-wsn/crudos"
    fs = sorted(base.glob("*/*.csv.gz"))
    por_mes = Counter(f.parent.name for f in fs)
    d = pd.read_csv(RAIZ / "clima/datos/ierse-wsn/diario.csv", parse_dates=["fecha"])
    return fs, por_mes, d


def fig_crudos(d):
    piv = d.pivot_table(index="fecha", columns="estacion", values="cobertura_pct")
    fig, ax = plt.subplots(figsize=(9.2, 2.9))
    cols = {"Los Guayabillos": "#1d4ed8", "Santa Rosa": "#7c3aed", "Cerro Crocker": "#0f766e", "Militar": "#b45309"}
    for e in piv.columns:
        ax.plot(piv.index, piv[e].rolling(7, min_periods=1).mean(), lw=1.3, color=cols.get(e, "0.4"), label=e)
    ax.axvline(pd.Timestamp("2026-10-30"), color="#7f1d1d", lw=0.8, ls="--")
    ax.text(pd.Timestamp("2026-10-29"), 8, "30-oct", color="#7f1d1d", fontsize=8, ha="right")
    ax.set_ylabel("cobertura diaria (%)\nmedia móvil de 7 días")
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.25)
    ax.legend(ncol=4, fontsize=7.5, frameon=False, loc="lower center")
    fig.savefig(OUT / "crudos.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    pasos, G = grafo()
    R, niveles = fig_grafo(G)
    cambios = ["../clima/datos/ierse-wsn/serie_5min.csv.gz", "descargas/dem_recortes/santa_cruz_dem.tif",
               "estudios/santa-cruz/texto/07_riesgos.md", "estudios/pendientes.json", "../clima/datos/fcd/climate_bellavista.csv"]
    fs, por_mes, d = crudos()
    fig_crudos(d)
    cob = d.groupby("estacion").cobertura_pct.agg(["mean", "count"]).round(1)
    res = dict(
        nota="Generado por informes/2026-10-infraestructura/figuras.py desde geodatos/flujo.toml y clima/datos/ (solo lectura).",
        pasos=len(pasos), aristas=G.number_of_edges(), aristas_reduccion_transitiva=R.number_of_edges(), niveles=niveles,
        tipos=dict(Counter(G.nodes[n]["tipo"] for n in G)),
        pesados=sorted(n for n, p in pasos.items() if p.pesado), red=sorted(n for n, p in pasos.items() if p.red),
        scripts_distintos=len({p.script for p in pasos.values() if p.script}),
        max_predecesores=max(G.in_degree(n) for n in G), nodo_max_predecesores=max(G, key=G.in_degree),
        alcance=alcance(pasos, G, cambios),
        crudos_ierse=dict(archivos=len(fs), por_mes=dict(sorted(por_mes.items())),
                          primero=fs[0].name if fs else None, ultimo=fs[-1].name if fs else None,
                          megabytes=round(sum(f.stat().st_size for f in fs) / 1e6, 2)),
        cobertura_media_pct=cob["mean"].to_dict(), dias_por_estacion=cob["count"].astype(int).to_dict(),
    )
    (OUT / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
