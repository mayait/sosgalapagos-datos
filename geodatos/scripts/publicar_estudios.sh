#!/bin/sh
# Genera y publica https://sosgalapagos.org/estudios/ (estudios preliminares con mapa, 3D y comentarios).
# Caddy sirve /srv/sosgalapagos-estudios tal cual y la API de comentarios en /estudios/api
# (ver app/deploy/sosgalapagos/Caddyfile y comentarios/). No hace falta redeploy para cambiar el contenido.
# Antes del rsync corre el checklist automático (scripts/revisar_publicacion.py): si algo no pasa, NO se publica.
# Proceso completo: geodatos/estudios/PUBLICAR.md
set -eu
# OBSOLETO desde el 4-nov-2026: /estudios/ publica solo la lista de informes técnicos en PDF (informes/publicar.sh).
# El sitio web de estudios (mapa, 3D, comentarios) ya no se publica; sus textos y datos siguen en el repositorio.
echo "Obsoleto: usa servidores/publicar.sh estudios (informes/publicar.sh)." >&2
exit 1
cd "$(dirname "$0")/.."
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
.venv/bin/python -I scripts/22_pendientes.py
.venv/bin/python -I scripts/19_estudios_web.py
if ! .venv/bin/python -I scripts/revisar_publicacion.py; then
  echo "La revisión encontró errores: no se publica. Corrígelos y vuelve a intentarlo (ver estudios/PUBLICAR.md)." >&2
  exit 1
fi
ssh "$SERVIDOR" 'mkdir -p /srv/sosgalapagos-estudios'
rsync -az --delete publicar/estudios/ "$SERVIDOR":/srv/sosgalapagos-estudios/
echo "Publicado: https://sosgalapagos.org/estudios/"
echo "Comprueba producción: .venv/bin/python -I scripts/revisar_publicacion.py --produccion"
