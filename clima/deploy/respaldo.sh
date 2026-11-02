#!/bin/sh
# Copia diaria de la base del clima (la corre sosgalapagos-clima-csv.service; actúa solo a las 06 UTC).
[ "$(date -u +%H)" = "06" ] || exit 0
D=/var/lib/sosgalapagos-clima
sqlite3 "$D/clima.db" ".backup $D/respaldos/clima-$(date -u +%F).db"
ls -1t "$D"/respaldos/clima-*.db | tail -n +15 | xargs -r rm -f
