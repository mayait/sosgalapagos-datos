#!/bin/sh
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
# Sirve el visor en http://127.0.0.1:8765/visor/
cd "$(dirname "$0")/.." && exec python3 -m http.server 8765 --bind 127.0.0.1
