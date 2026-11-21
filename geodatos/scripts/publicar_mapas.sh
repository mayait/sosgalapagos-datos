#!/bin/sh
# Genera y publica los datos de https://sosgalapagos.org/mapas/ (manifiesto, capas y descargas Shapefile/GeoJSON).
# El mapa que los muestra es https://sosgalapagos.org/riesgos/ (repo sosgalapagos-plataforma). El visor que había
# en /mapas/ se retiró el 21-nov-2026 (Archivo/visor-mapas/): por eso index.html no se sube ni se toca.
# Requiere: export/galapagos (08_exportar.py) y export/galapagos-completo (08_exportar.py --completo).
# Caddy sirve /srv/sosgalapagos-mapas tal cual (ver app/deploy/sosgalapagos/Caddyfile); no hace falta redeploy.
set -eu
cd "$(dirname "$0")/.."
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
.venv/bin/python -I scripts/10_publicar_web.py
ssh "$SERVIDOR" 'mkdir -p /srv/sosgalapagos-mapas'
rsync -az --delete --exclude /index.html publicar/mapas/ "$SERVIDOR":/srv/sosgalapagos-mapas/
echo "Publicado: los datos de /mapas/. Se ven en https://sosgalapagos.org/riesgos/"
