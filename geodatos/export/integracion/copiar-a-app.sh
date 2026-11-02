#!/bin/sh
# Copia el paquete de capas al proyecto principal (no borra nada de lo que ya hay en public/galapagos/).
set -e
G="$(cd "$(dirname "$0")/../.." && pwd)"
# La app ResponseGrid vive en otro repositorio. Ruta configurable con SOSGALAPAGOS_APP.
APP="${SOSGALAPAGOS_APP:-$HOME/dev/RESPONSEGRID_GALAPAGOS/app}/apps/web"
[ -d "$APP" ] || { echo "No encuentro la app en $APP. Define SOSGALAPAGOS_APP=/ruta/a/app" >&2; exit 1; }
mkdir -p "$APP/public/galapagos/capas" "$APP/src/components/organisms/galapagos"
cp -R "$G/export/galapagos/." "$APP/public/galapagos/capas/"
cp "$G/export/integracion/capas-manifiesto.ts" "$APP/src/components/organisms/galapagos/capas-manifiesto.ts"
echo "Copiado a $APP/public/galapagos/capas/ y src/components/organisms/galapagos/"
