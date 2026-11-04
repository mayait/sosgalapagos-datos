#!/bin/sh
# Publica https://sosgalapagos.org/estudios/: solo la lista de informes técnicos con enlaces a sus PDF en GitHub (rama main).
# Reemplaza el antiguo sitio web de estudios (mapa, 3D, comentarios): rsync --delete borra en el servidor todo lo que
# no sea la página nueva. Se llama desde servidores/publicar.sh estudios (solo desde main y con el árbol limpio).
# Los PDF deben estar compilados y en main antes de publicar (informes/compilar.sh todos).
set -eu
cd "$(dirname "$0")"
SERVIDOR=${SERVIDOR:-root@152.44.45.89}
python3 -I indice.py
ssh "$SERVIDOR" 'mkdir -p /srv/sosgalapagos-estudios'
rsync -az --delete web/ "$SERVIDOR":/srv/sosgalapagos-estudios/
echo "Publicado: https://sosgalapagos.org/estudios/ (y /informes redirige ahí)"
