#!/bin/sh
# Comando forzado de la llave del puente IERSE (~clima/.ssh/authorized_keys): solo recibe filas por stdin.
# CLIMA_SIN_EXPORTAR=1: el panel lo genera la plataforma (Django); aquí solo se guardan las filas del puente.
export CLIMA_SIN_EXPORTAR=1 CLIMA_DB=/var/lib/sosgalapagos-clima/clima.db CLIMA_SALIDA=/srv/sosgalapagos-clima/datos CLIMA_PRIVADO=/var/lib/sosgalapagos-clima/privado
exec /opt/sosgalapagos-clima/.venv/bin/python -I /opt/sosgalapagos-clima/recolector.py --recibir
