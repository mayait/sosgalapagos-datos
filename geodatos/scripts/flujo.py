"""Flujo incremental de los estudios: rehace solo lo que depende de los datos que cambiaron.

El grafo está en geodatos/flujo.toml: cada paso declara su script, sus entradas y sus salidas. Un paso depende de otro
si lee un archivo que el otro escribe. El flujo compara el contenido (hash) de cada entrada con el de la última corrida
correcta del paso (geodatos/.flujo/estado.json, local y fuera de git) y rehace, en orden, solo los pasos afectados.

Uso (desde geodatos/):
  .venv/bin/python -I scripts/flujo.py --seco               lista qué se rehace y por qué, sin ejecutar nada
  .venv/bin/python -I scripts/flujo.py                      rehace lo afectado; salta pesados (modelo 2D), red y manuales
  .venv/bin/python -I scripts/flujo.py --pesados            incluye los pasos pesados afectados
  .venv/bin/python -I scripts/flujo.py --red                incluye los pasos que bajan datos (issues de GitHub, Open-Meteo)
  .venv/bin/python -I scripts/flujo.py --cambio RUTA [...]  trata RUTA como cambiada (p. ej. un DEM o una lluvia nueva)
  .venv/bin/python -I scripts/flujo.py --hasta sitio        solo los pasos que llevan a «sitio»
  .venv/bin/python -I scripts/flujo.py --solo cruces,sitio  solo esos pasos (corren aunque sean pesados, si hace falta)
  .venv/bin/python -I scripts/flujo.py --forzar PASO        rehace PASO aunque esté al día (y lo que dependa de él)
  .venv/bin/python -I scripts/flujo.py --marcar [PASO ...]  da por buenas las salidas actuales sin ejecutar nada
  .venv/bin/python -I scripts/flujo.py --lista | --grafo    pasos y dependencias (texto o Mermaid)

Primera vez en una copia del repositorio: «--marcar» (las salidas versionadas ya están al día) y después «--seco».
Si rehaces un paso a mano, vuelve a marcarlo: «--marcar PASO».
"""
import argparse, datetime, glob, hashlib, json, os, pathlib, re, subprocess, sys, time, tomllib, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONF = ROOT / "flujo.toml"
DIR = ROOT / ".flujo"
ESTADO = DIR / "estado.json"
CACHE = DIR / "hashes.json"
PY = ".venv/bin/python -I"
COMODIN = set("*?[")


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ------------------------------------------------------------------ configuración
class Paso:
    def __init__(self, nombre, d, grupos):
        self.nombre = nombre
        self.script = d.get("script")
        self.cmd = d.get("cmd") or [f"{{py}} scripts/{self.script}"]
        self.pesado, self.red, self.manual, self.siempre = (bool(d.get(k)) for k in ("pesado", "red", "manual", "siempre"))
        self.nota = d.get("nota", "")
        exp = lambda lst: [nfc(x) for p in lst for x in (grupos[p[1:]] if p.startswith("@") else [p])]
        self.entradas = exp(d.get("entradas", []))
        self.codigo = [f"scripts/{c}" for c in ([self.script] if self.script else []) + d.get("codigo", [])]
        self.salidas = exp(d.get("salidas", []))
        self.deps = []

    def firma(self):
        txt = json.dumps([self.cmd, self.entradas, self.codigo, self.salidas], ensure_ascii=False)
        return hashlib.blake2b(txt.encode(), digest_size=8).hexdigest()


def cargar():
    c = tomllib.loads(CONF.read_text(encoding="utf-8"))
    grupos = {k: v for k, v in c.get("grupos", {}).items()}
    pasos = {n: Paso(n, d, grupos) for n, d in c["pasos"].items()}
    for p in pasos.values():
        for q in pasos.values():
            if q is not p and solapan(p.entradas + p.codigo, q.salidas):
                p.deps.append(q.nombre)
    return pasos


# ------------------------------------------------------------------ archivos y hashes
_glob_cache = {}


def resolver(patron):
    """Archivos (rutas relativas a geodatos/, NFC) que casan con un patrón."""
    if patron not in _glob_cache:
        fs = glob.glob(str(ROOT / patron), recursive=True)
        _glob_cache[patron] = sorted(nfc(os.path.relpath(f, ROOT)) for f in fs if os.path.isfile(f))
    return _glob_cache[patron]


_rx_cache = {}


def casa(ruta, patron):
    """¿La ruta casa con el patrón? «*» y «?» no cruzan «/»; «**» sí (como glob)."""
    if patron not in _rx_cache:
        rx, i = "", 0
        while i < len(patron):
            c = patron[i]
            if patron.startswith("**/", i):
                rx += "(?:.*/)?"; i += 3; continue
            if patron.startswith("**", i):
                rx += ".*"; i += 2; continue
            rx += "[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c)
            i += 1
        _rx_cache[patron] = re.compile(rx + r"\Z")
    return bool(_rx_cache[patron].match(ruta))


def solapan(entradas, salidas):
    for e in entradas:
        fe = set(resolver(e))
        for s in salidas:
            if fe & set(resolver(s)):
                return True
            if not COMODIN & set(s) and casa(s, e):
                return True
            if not COMODIN & set(e) and casa(e, s):
                return True
    return False


class Hashes:
    def __init__(self):
        try:
            self.c = json.loads(CACHE.read_text())
        except Exception:
            self.c = {}

    def __call__(self, rel):
        p = ROOT / rel
        st = p.stat()
        clave = f"{st.st_size}:{st.st_mtime_ns}"
        e = self.c.get(rel)
        if e and e[0] == clave:
            return e[1]
        h = hashlib.blake2b(digest_size=12)
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        self.c[rel] = [clave, h.hexdigest()]
        return self.c[rel][1]

    def guardar(self):
        DIR.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(self.c, ensure_ascii=False, separators=(",", ":")))


def leer_estado():
    try:
        return json.loads(ESTADO.read_text())
    except Exception:
        return {}


def guardar_estado(est):
    DIR.mkdir(exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1, sort_keys=True))


def huella(paso, H):
    return {f: H(f) for pat in paso.entradas + paso.codigo for f in resolver(pat)}


# ------------------------------------------------------------------ orden y motivos
def orden(pasos):
    pend = {n: set(p.deps) for n, p in pasos.items()}
    out = []
    while pend:
        listos = [n for n in pasos if n in pend and not pend[n]]
        if not listos:
            sys.exit("El grafo tiene un ciclo entre: " + ", ".join(sorted(pend)))
        for n in listos:
            out.append(n); del pend[n]
            for v in pend.values():
                v.discard(n)
    return out


def motivos(paso, est, H, cambios):
    """Por qué hay que rehacer el paso ([] si está al día). También devuelve las entradas que faltan."""
    m, faltan = [], []
    for pat in paso.entradas + paso.codigo:
        if not resolver(pat):
            faltan.append(pat)
    if cambios:
        hit = [c for c in cambios if any(casa(c, pat) or c in resolver(pat) for pat in paso.entradas + paso.codigo)]
        m += [f"cambio indicado: {c}" for c in hit]
    for pat in paso.salidas:
        if not resolver(pat):
            m.append(f"falta la salida {pat}")
    if paso.red:
        m.append("baja datos de internet")
    e = est.get(paso.nombre)
    if not e:
        m.append("sin corrida registrada (usa --marcar si las salidas ya están al día)")
        return m, faltan
    if e.get("firma") != paso.firma():
        m.append("cambió la definición del paso en flujo.toml")
    ahora, antes = huella(paso, H), e.get("entradas", {})
    nuevos = [f for f in ahora if f not in antes]
    idos = [f for f in antes if f not in ahora]
    distintos = [f for f in ahora if f in antes and ahora[f] != antes[f]]
    for etiqueta, lista in (("cambió", distintos), ("nuevo", nuevos), ("ya no está", idos)):
        if lista:
            m.append(f"{etiqueta}: {', '.join(lista[:3])}{f' y {len(lista) - 3} más' if len(lista) > 3 else ''}")
    return m, faltan


def permitido(paso, a):
    if paso.nombre in a.forzar:
        return True, ""
    if paso.manual:
        return False, "manual (solo con --forzar)"
    if paso.red and not a.red:
        return False, "baja datos (usa --red)"
    if paso.pesado and not (a.pesados or paso.nombre in a.solo):
        return False, "pesado (usa --pesados o --solo)"
    return True, ""


def seleccion(pasos, a):
    sel = list(pasos)
    if a.hasta:
        incl, pila = set(), [a.hasta]
        while pila:
            n = pila.pop()
            if n not in incl:
                incl.add(n); pila += pasos[n].deps
        sel = [n for n in sel if n in incl]
    if a.solo:
        sel = [n for n in sel if n in a.solo]
    return sel


# ------------------------------------------------------------------ acciones
def plan(pasos, a, est, H):
    """Modo seco: propaga los cambios por el grafo sin ejecutar nada."""
    rehace, filas = set(), []
    sel = seleccion(pasos, a)
    for n in orden(pasos):
        if n not in sel:
            continue
        p = pasos[n]
        m, faltan = motivos(p, est, H, a.cambio)
        if n in a.forzar:
            m.insert(0, "forzado")
        m += [f"depende de «{d}», que se rehace" for d in p.deps if d in rehace]
        if p.siempre:
            filas.append(("SIEMPRE", n, p.nota or "se ejecuta en cada corrida")); continue
        if not m:
            filas.append(("al día", n, "")); continue
        ok, porque = permitido(p, a)
        if faltan and not any(d in rehace for d in p.deps):
            filas.append(("BLOQUEADO", n, "faltan entradas: " + ", ".join(faltan[:3]))); continue
        if ok:
            rehace.add(n); filas.append(("REHACER", n, "; ".join(m[:4])))
        else:
            filas.append(("pendiente", n, f"{porque}: " + "; ".join(m[:3])))
    ancho = max(len(f[1]) for f in filas) if filas else 10
    for e, n, txt in filas:
        print(f"  {e:<10} {n:<{ancho}}  {txt}")
    print(f"\n{len(rehace)} paso(s) a rehacer" + (" (los pasos «pendiente» no se ejecutan sin la opción indicada)" if any(f[0] == "pendiente" for f in filas) else ""))
    return rehace


def ejecutar(pasos, a, est, H):
    DIR.mkdir(exist_ok=True); (DIR / "logs").mkdir(exist_ok=True)
    sel, corridos, saltados = seleccion(pasos, a), [], []
    for n in orden(pasos):
        if n not in sel:
            continue
        p = pasos[n]
        _glob_cache.clear()                         # los pasos anteriores pudieron crear archivos
        m, faltan = motivos(p, est, H, a.cambio)
        if n in a.forzar:
            m.insert(0, "forzado")
        if not m and not p.siempre:
            continue
        ok, porque = permitido(p, a)
        if not ok:
            saltados.append((n, porque)); print(f"  -- {n}: se salta ({porque})"); continue
        if faltan:
            print(f"  !! {n}: faltan entradas: {', '.join(faltan)}"); sys.exit(1)
        print(f"  >> {n}: {'control (corre siempre)' if p.siempre else '; '.join(m[:3])}", flush=True)
        log = DIR / "logs" / f"{n}.log"
        t0 = time.time()
        with open(log, "w") as fh:
            for c in p.cmd:
                c = c.replace("{py}", PY)
                fh.write(f"$ {c}\n"); fh.flush()
                r = subprocess.run(c, shell=True, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env={**os.environ, "MPLBACKEND": "Agg"})
                if r.returncode:
                    break
        if r.returncode:
            print(f"  !! {n} falló (código {r.returncode}). Últimas líneas de {log.relative_to(ROOT)}:")
            print("     " + "\n     ".join(log.read_text(errors="replace").splitlines()[-15:]))
            H.guardar(); guardar_estado(est); sys.exit(r.returncode)
        _glob_cache.clear()
        est[n] = {"firma": p.firma(), "entradas": huella(p, H), "fecha": datetime.datetime.now().isoformat(timespec="seconds"),
                  "segundos": round(time.time() - t0, 1)}
        guardar_estado(est); H.guardar()
        corridos.append(n)
        print(f"     listo en {time.time() - t0:.1f} s")
    print(f"\nRehechos: {', '.join(corridos) or 'ninguno'}" + (f". Saltados: {', '.join(s for s, _ in saltados)}" if saltados else ""))


def marcar(pasos, nombres, est, H):
    for n in (nombres or list(pasos)):
        p = pasos[n]
        if p.red or p.siempre:
            continue
        sin = [s for s in p.salidas if not resolver(s)]
        if sin:
            print(f"  {n}: NO se marca, faltan salidas: {', '.join(sin[:3])}"); continue
        est[n] = {"firma": p.firma(), "entradas": huella(p, H), "fecha": datetime.datetime.now().isoformat(timespec="seconds"), "marcado": True}
        print(f"  {n}: marcado al día")
    guardar_estado(est); H.guardar()


def grafo(pasos):
    print("```mermaid\nflowchart LR")
    for n, p in pasos.items():
        forma = f'{n}[["{n}"]]' if p.pesado else (f'{n}(("{n}"))' if p.red else f'{n}["{n}"]')
        print(f"  {forma}")
        for d in p.deps:
            print(f"  {d} --> {n}")
    print("```")


def main():
    ap = argparse.ArgumentParser(description="Flujo incremental de los estudios (ver flujo.toml).")
    ap.add_argument("--seco", action="store_true", help="solo lista lo que se rehace")
    ap.add_argument("--pesados", action="store_true")
    ap.add_argument("--red", action="store_true")
    ap.add_argument("--cambio", nargs="+", default=[], metavar="RUTA", help="rutas (relativas a geodatos/) que se tratan como cambiadas")
    ap.add_argument("--hasta")
    ap.add_argument("--solo", default="")
    ap.add_argument("--forzar", default="")
    ap.add_argument("--marcar", nargs="*", metavar="PASO")
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--grafo", action="store_true")
    a = ap.parse_args()
    a.solo = {s for s in a.solo.split(",") if s}
    a.forzar = {s for s in a.forzar.split(",") if s}
    a.cambio = [nfc(os.path.relpath(os.path.abspath(c), ROOT)) if os.path.isabs(c) else nfc(c) for c in a.cambio]
    pasos = cargar()
    for n in list(a.solo) + list(a.forzar) + ([a.hasta] if a.hasta else []) + (a.marcar or []):
        if n not in pasos:
            sys.exit(f"Paso desconocido: {n}. Pasos: {', '.join(pasos)}")
    if a.grafo:
        return grafo(pasos)
    if a.lista:
        for n in orden(pasos):
            p = pasos[n]
            flags = ",".join(k for k in ("pesado", "red", "manual", "siempre") if getattr(p, k))
            print(f"  {n:<34} {('[' + flags + ']') if flags else '':<16} ← {', '.join(p.deps) or '—'}")
        return
    est, H = leer_estado(), Hashes()
    if a.marcar is not None:
        return marcar(pasos, a.marcar, est, H)
    if a.seco:
        plan(pasos, a, est, H); H.guardar(); return
    ejecutar(pasos, a, est, H)


if __name__ == "__main__":
    main()
