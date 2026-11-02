#!/bin/sh
# Genera y publica https://sosgalapagos.org/mapas/ (visor + descargas Shapefile/GeoJSON).
# Requiere: export/galapagos (08_exportar.py) y export/galapagos-completo (08_exportar.py --completo).
# Caddy sirve /srv/sosgalapagos-mapas tal cual (ver app/deploy/sosgalapagos/Caddyfile); no hace falta redeploy.
set -eu
cd "$(dirname "$0")/.."
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
.venv/bin/python -I scripts/10_publicar_web.py
ssh "$SERVIDOR" 'mkdir -p /srv/sosgalapagos-mapas'
rsync -az --delete publicar/mapas/ "$SERVIDOR":/srv/sosgalapagos-mapas/
echo "Publicado: https://sosgalapagos.org/mapas/"
