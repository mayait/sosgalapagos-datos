#!/bin/sh
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
# Publica un servicio en sosgalapagos.org desde main, con el árbol limpio.
#   servidores/publicar.sh mapas      → datos de /mapas/, que muestra /riesgos/ (geodatos/scripts/publicar_mapas.sh)
#   servidores/publicar.sh clima      → la página de /clima/ (clima/publicar_panel.sh). Los datos los genera la plataforma
#   servidores/publicar.sh descargas  → /descargas/ y la sección «Informes» de la portada (servidores/publicar_descargas.sh)
# Variables: SERVIDOR (por defecto root@152.44.45.89), PERMITIR_RAMA=1 para probar desde otra rama.
set -eu
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
export SERVIDOR
servicio=${1:-}
[ $# -gt 0 ] && shift

uso() { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

rama=$(git -C "$RAIZ" rev-parse --abbrev-ref HEAD)
if [ "$rama" != "main" ] && [ "${PERMITIR_RAMA:-0}" != "1" ]; then
  echo "Solo se publica desde main (estás en «$rama»). Usa PERMITIR_RAMA=1 solo para pruebas." >&2; exit 1
fi
if [ -n "$(git -C "$RAIZ" status --porcelain --untracked-files=no)" ]; then
  echo "Hay cambios sin commit. Haz commit (o descártalos) antes de publicar." >&2; exit 1
fi
commit=$(git -C "$RAIZ" rev-parse --short HEAD)

case "$servicio" in
  mapas)    "$RAIZ/geodatos/scripts/publicar_mapas.sh" "$@";    destino=/srv/sosgalapagos-mapas ;;
  estudios|informes)
    echo "Los informes y los estudios son solo locales desde el 5-nov-2026: no se publican (AGENTS.md, regla 6)." >&2; exit 1 ;;
  clima)    "$RAIZ/clima/publicar_panel.sh" "$@";               destino=/srv/sosgalapagos-clima ;;
  descargas) "$RAIZ/servidores/publicar_descargas.sh" "$@";     destino=/srv/sosgalapagos-descargas ;;
  *) uso ;;
esac

# Deja constancia de qué commit quedó publicado
ssh "$SERVIDOR" "printf '%s %s\n' '$commit' \"\$(date -u +%FT%TZ)\" > $destino/version.txt"
echo "Versión publicada en $servicio: $commit"
