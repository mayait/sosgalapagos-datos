#!/usr/bin/env bash
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
# Baja los días nuevos de IERSE-WSN y regenera las tablas consolidadas.
# Se puede correr a mano o desde cron/launchd (p. ej., cada día a las 06:00).
set -euo pipefail
cd "$(dirname "$0")"
PY=../geodatos/.venv/bin/python
[ -x "$PY" ] || PY=python3

python3 -I scripts/01_ierse_descargar.py "$@"
"$PY" -I scripts/02_ierse_consolidar.py
