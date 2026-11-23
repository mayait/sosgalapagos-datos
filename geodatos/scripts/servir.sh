#!/bin/sh
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
# Sirve el visor en http://127.0.0.1:8765/visor/
cd "$(dirname "$0")/.." && exec python3 -m http.server 8765 --bind 127.0.0.1
