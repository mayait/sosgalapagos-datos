#!/bin/sh
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
# Publica el panel de /clima/ (clima/web/index.html). Solo la página: los datos los genera la
# plataforma (repo sosgalapagos-plataforma, app clima). Guarda copia de la página anterior.
# Lo llama servidores/publicar.sh clima.
set -eu
AQUI="$(cd "$(dirname "$0")" && pwd)"
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
scp -q "$AQUI/web/index.html" "$SERVIDOR":/tmp/clima-index.nuevo.html
ssh "$SERVIDOR" 'mkdir -p /root/respaldo-clima-panel && cp /srv/sosgalapagos-clima/index.html "/root/respaldo-clima-panel/index-$(date -u +%Y%m%dT%H%M%SZ).html" && install -m 644 /tmp/clima-index.nuevo.html /srv/sosgalapagos-clima/index.html && rm -f /tmp/clima-index.nuevo.html'
echo "Panel de /clima/ publicado."
