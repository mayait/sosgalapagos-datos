#!/bin/sh
# Sirve el visor en http://127.0.0.1:8765/visor/
cd "$(dirname "$0")/.." && exec python3 -m http.server 8765 --bind 127.0.0.1
