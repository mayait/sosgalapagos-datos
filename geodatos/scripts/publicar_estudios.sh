#!/bin/sh
# Genera y publica https://sosgalapagos.org/estudios/ (estudios preliminares con mapa, 3D y comentarios).
# Caddy sirve /srv/sosgalapagos-estudios tal cual y la API de comentarios en /estudios/api
# (ver app/deploy/sosgalapagos/Caddyfile y comentarios/). No hace falta redeploy para cambiar el contenido.
set -eu
cd "$(dirname "$0")/.."
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
.venv/bin/python -I scripts/19_estudios_web.py
ssh "$SERVIDOR" 'mkdir -p /srv/sosgalapagos-estudios'
rsync -az --delete publicar/estudios/ "$SERVIDOR":/srv/sosgalapagos-estudios/
echo "Publicado: https://sosgalapagos.org/estudios/"
