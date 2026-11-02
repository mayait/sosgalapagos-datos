#!/usr/bin/env bash
# Instala o actualiza el recolector y el dashboard de clima en el servidor.
#   ./deploy/publicar.sh               # código + página + timers
#   ./deploy/publicar.sh --historico   # además carga el histórico local de IERSE y el diario del GSC
# Caddy sirve /srv/sosgalapagos-clima en sosgalapagos.org/clima/
# (ver app/deploy/sosgalapagos/Caddyfile y docker-compose.yml).
set -euo pipefail
cd "$(dirname "$0")/.."
SERVIDOR=${SERVIDOR:-root@152.44.45.89}

ssh "$SERVIDOR" 'set -e
  id clima >/dev/null 2>&1 || useradd --system --home /var/lib/sosgalapagos-clima --shell /usr/sbin/nologin clima
  command -v sqlite3 >/dev/null || apt-get install -y -qq sqlite3 >/dev/null
  dpkg -s python3-venv >/dev/null 2>&1 || apt-get install -y -qq python3-venv >/dev/null
  mkdir -p /opt/sosgalapagos-clima /var/lib/sosgalapagos-clima/respaldos /var/lib/sosgalapagos-clima/privado /srv/sosgalapagos-clima/datos
  rm -rf /srv/sosgalapagos-clima/datos/descargas   # nada descargable en la carpeta pública
  chown -R clima:clima /var/lib/sosgalapagos-clima /srv/sosgalapagos-clima'
[ -f privado/fuentes.env ] || { echo "Falta privado/fuentes.env (ver fuentes.env.ejemplo)"; exit 1; }
ssh "$SERVIDOR" 'install -d -m 750 -o root -g clima /etc/sosgalapagos-clima'
scp -q privado/fuentes.env "$SERVIDOR":/etc/sosgalapagos-clima/fuentes.env
ssh "$SERVIDOR" 'chown root:clima /etc/sosgalapagos-clima/fuentes.env; chmod 640 /etc/sosgalapagos-clima/fuentes.env'
rsync -az recolector/*.py recolector/*.json deploy/respaldo.sh deploy/recibir.sh "$SERVIDOR":/opt/sosgalapagos-clima/
# Series diarias de la FCD para la estacionalidad (privadas: fuera de la carpeta pública)
ssh "$SERVIDOR" 'install -d -m 750 -o clima -g clima /var/lib/sosgalapagos-clima/fcd'
rsync -az datos/fcd/*.csv "$SERVIDOR":/var/lib/sosgalapagos-clima/fcd/
rsync -az web/index.html "$SERVIDOR":/srv/sosgalapagos-clima/index.html
rsync -az deploy/*.service deploy/*.timer "$SERVIDOR":/etc/systemd/system/
ssh "$SERVIDOR" 'set -e
  cd /opt/sosgalapagos-clima
  [ -x .venv/bin/python ] || python3 -m venv .venv
  .venv/bin/pip install -q --upgrade websockets
  chown clima:clima /srv/sosgalapagos-clima/index.html
  systemctl daemon-reload
  systemctl enable --now sosgalapagos-clima.timer sosgalapagos-clima-csv.timer'

# Llave del puente IERSE: solo puede ejecutar recibir.sh (sin terminal ni reenvíos)
if [ -f "$HOME/.ssh/id_clima_puente.pub" ]; then
  LLAVE_PUB=$(cat "$HOME/.ssh/id_clima_puente.pub")
  ssh "$SERVIDOR" "set -e; usermod -s /bin/sh clima
    install -d -m 700 -o clima -g clima /var/lib/sosgalapagos-clima/.ssh
    echo 'command=\"/opt/sosgalapagos-clima/recibir.sh\",restrict $LLAVE_PUB' > /var/lib/sosgalapagos-clima/.ssh/authorized_keys
    chown clima:clima /var/lib/sosgalapagos-clima/.ssh/authorized_keys; chmod 600 /var/lib/sosgalapagos-clima/.ssh/authorized_keys"
fi

if [ "${1:-}" = "--historico" ]; then
  rsync -az --delete datos/ierse-wsn/crudos/ "$SERVIDOR":/var/lib/sosgalapagos-clima/importar-ierse/
  rsync -az datos/inamhi/historial/historial_estaciones_pais_*.json "$SERVIDOR":/var/lib/sosgalapagos-clima/importar-inamhi/
  ssh "$SERVIDOR" 'set -e; chown -R clima:clima /var/lib/sosgalapagos-clima
    cd /opt/sosgalapagos-clima
    E="CLIMA_DB=/var/lib/sosgalapagos-clima/clima.db CLIMA_SALIDA=/srv/sosgalapagos-clima/datos"
    runuser -u clima -- env $E .venv/bin/python -I recolector.py --importar-ierse /var/lib/sosgalapagos-clima/importar-ierse
    runuser -u clima -- env $E .venv/bin/python -I recolector.py --importar-gsc-historico
    for f in /var/lib/sosgalapagos-clima/importar-inamhi/*.json; do [ -f "$f" ] && runuser -u clima -- env $E .venv/bin/python -I recolector.py --importar-inamhi "$f"; done
    runuser -u clima -- env $E .venv/bin/python -I recolector.py --solo-exportar --csv'
fi

ssh "$SERVIDOR" 'systemctl start sosgalapagos-clima.service; systemctl --no-pager status sosgalapagos-clima.service | tail -5'
echo "Publicado: sosgalapagos.org/clima/"
