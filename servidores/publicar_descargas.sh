#!/bin/sh
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
# Publica los informes y mapas descargables de la portada: https://sosgalapagos.org/#informes
#
# Los PDF NO están en este repositorio (AGENTS.md, regla 6). Viven en una carpeta local, junto a
# `indice.json`, que es la lista que lee la portada:
#
#   ~/dev/sosgalapagos-informes/publicar/
#     indice.json                 {"informes": [{archivo, portada, titulo, resumen, fecha, paginas, formato, tamano}]}
#     <nombre>.pdf  <nombre>.jpg  el PDF y su miniatura
#
# Para añadir un informe: copia el PDF y la miniatura a esa carpeta, añádelo a `indice.json` y corre
# `servidores/publicar.sh descargas`. No hace falta desplegar la web: la portada lee el índice al vuelo.
# Caddy sirve la carpeta en /descargas/ (repo sosgalapagos: deploy/sosgalapagos/Caddyfile).
#
# Variables: ORIGEN (carpeta local), SERVIDOR.
set -eu
ORIGEN=${ORIGEN:-$HOME/dev/sosgalapagos-informes/publicar}
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
DESTINO=/srv/sosgalapagos-descargas

[ -f "$ORIGEN/indice.json" ] || { echo "No existe $ORIGEN/indice.json" >&2; exit 1; }

# El índice debe ser válido y cada archivo que nombra debe existir, con un nombre simple.
python3 - "$ORIGEN" <<'PY'
import json, re, sys
from pathlib import Path
d = Path(sys.argv[1]); lista = json.loads((d / "indice.json").read_text())["informes"]
ok = True
for i in lista:
    for clave, patron in (("archivo", r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.pdf$"), ("portada", r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.(jpg|png)$")):
        n = i.get(clave)
        if clave == "portada" and not n: continue
        if not n or not re.match(patron, n): print(f"Nombre no válido en «{clave}»: {n!r}", file=sys.stderr); ok = False
        elif not (d / n).is_file(): print(f"Falta el archivo {n}", file=sys.stderr); ok = False
    for clave in ("titulo", "fecha"):
        if not i.get(clave): print(f"Falta «{clave}» en {i.get('archivo')}", file=sys.stderr); ok = False
print(f"{len(lista)} informes en el índice")
sys.exit(0 if ok else 1)
PY

ssh "$SERVIDOR" "mkdir -p $DESTINO"
# Solo el índice, los PDF y las miniaturas. Lo que ya no está en la carpeta local se borra del servidor.
rsync -az --delete --include='indice.json' --include='*.pdf' --include='*.jpg' --include='*.png' --exclude='*' "$ORIGEN"/ "$SERVIDOR":$DESTINO/
ssh "$SERVIDOR" "chmod -R a+rX $DESTINO"
echo "Publicado: https://sosgalapagos.org/#informes"
