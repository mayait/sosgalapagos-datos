#!/bin/sh
# Puente IERSE → servidor. IERSE no responde a la IP del servidor (EE. UU.), así que una
# máquina en Ecuador baja los datos y los envía por SSH con una llave restringida que en el
# servidor solo puede ejecutar recibir.sh. Lo corre launchd cada 5 min (ver LEEME).
set -eu
DIR="$(cd "$(dirname "$0")/.." && pwd)"
ESTADO="$DIR/puente/.ultimo_envio"
export CLIMA_DB="$DIR/puente/puente.db" CLIMA_SALIDA="$DIR/puente/salida" CLIMA_PRIVADO="$DIR/puente/privado"
PY="$DIR/.venv/bin/python"
SERVIDOR=${SERVIDOR:-clima@152.44.45.89}
LLAVE=${LLAVE:-$HOME/.ssh/id_clima_puente}

# Desde el 27-oct-2026 el servidor de IERSE no envía el certificado intermedio (RapidSSL TLS RSA
# CA G1, de DigiCert) y Python rechaza la conexión. Se añade ese intermedio público a las raíces
# del sistema; la verificación sigue activa.
if [ -f "$DIR/puente/ca-intermedios.pem" ]; then
  cat /etc/ssl/cert.pem "$DIR/puente/ca-intermedios.pem" > "$DIR/puente/.ca.pem"
  export SSL_CERT_FILE="$DIR/puente/.ca.pem"
fi
"$PY" -I "$DIR/recolector/recolector.py" --fuentes ierse
# Horas a enviar: desde el último envío correcto (+1 h de margen), entre 2 y 72
ahora=$(date +%s); ult=$(cat "$ESTADO" 2>/dev/null || echo 0)
h=$(( (ahora - ult) / 3600 + 2 )); [ "$h" -gt 72 ] && h=72
"$PY" -I "$DIR/recolector/recolector.py" --emitir ierse --horas "$h" \
  | ssh -i "$LLAVE" -o IdentitiesOnly=yes -o IdentityAgent=none -o BatchMode=yes -o ConnectTimeout=20 "$SERVIDOR"
echo "$ahora" > "$ESTADO"
