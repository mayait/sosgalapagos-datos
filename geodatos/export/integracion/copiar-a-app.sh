#!/bin/sh
# Copia el paquete de capas al proyecto principal (no borra nada de lo que ya hay en public/galapagos/).
set -e
G="$(cd "$(dirname "$0")/../.." && pwd)"
APP="$G/../app/apps/web"
mkdir -p "$APP/public/galapagos/capas" "$APP/src/components/organisms/galapagos"
cp -R "$G/export/galapagos/." "$APP/public/galapagos/capas/"
cp "$G/export/integracion/capas-manifiesto.ts" "$APP/src/components/organisms/galapagos/capas-manifiesto.ts"
echo "Copiado a $APP/public/galapagos/capas/ y src/components/organisms/galapagos/"
