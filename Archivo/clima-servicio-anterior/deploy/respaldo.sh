#!/bin/sh
# Copia diaria de la base del clima (la corre sosgalapagos-clima-csv.service; actúa solo a las 06 UTC).
# La copia se guarda comprimida: la base pesa unos 300 MB y comprimida, la quinta parte.
[ "$(date -u +%H)" = "06" ] || exit 0
D=/var/lib/sosgalapagos-clima
F="$D/respaldos/clima-$(date -u +%F).db"
sqlite3 "$D/clima.db" ".backup $F" && gzip -f "$F"
# Se conservan las 14 más recientes (comprimidas o no).
ls -1t "$D"/respaldos/clima-*.db* | tail -n +15 | xargs -r rm -f
