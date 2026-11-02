#!/bin/sh
# Comando forzado de la llave del puente IERSE (~clima/.ssh/authorized_keys): solo recibe filas por stdin.
export CLIMA_DB=/var/lib/sosgalapagos-clima/clima.db CLIMA_SALIDA=/srv/sosgalapagos-clima/datos CLIMA_PRIVADO=/var/lib/sosgalapagos-clima/privado
exec /opt/sosgalapagos-clima/.venv/bin/python -I /opt/sosgalapagos-clima/recolector.py --recibir
