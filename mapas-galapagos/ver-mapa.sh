#!/bin/sh
# Abre el visor en http://127.0.0.1:8765/visor/ (Ctrl+C para cerrar)
cd "$(dirname "$0")"
( sleep 1; open "http://127.0.0.1:8765/visor/" 2>/dev/null || xdg-open "http://127.0.0.1:8765/visor/" ) &
exec python3 -m http.server 8765 --bind 127.0.0.1
