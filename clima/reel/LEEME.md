# Reel del clima

Genera un video vertical por día (1080 × 1920, 10,7 s) con el pronóstico del clima de Galápagos: el mapa de lluvia y viento animado hora a hora, la hora de más lluvia en cada isla, la marea, qué tan fuerte puede llover y cuánta agua ya cayó. Usa los datos públicos de [sosgalapagos.org/clima](https://sosgalapagos.org/clima/).

```bash
python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26 --solo-datos   # baja los datos y los resume
python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26 --prueba       # una imagen por día
python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26                # el reel, en ~/Downloads/sosgalapagos-reel-2026-11-25/
```

Necesita Node 22 o posterior, Google Chrome y ffmpeg. Python, sin paquetes.

**La guía completa está en [`.claude/skills/reel-clima/SKILL.md`](../../.claude/skills/reel-clima/SKILL.md)**: los pasos, cómo escribir la frase de cada día, qué revisar en los cuadros antes de entregar y qué hacer si algo falla. Claude Code la carga sola como skill (`reel-clima`); otros agentes la leen como un documento.

## Archivos

| Archivo | Qué hace |
|---|---|
| `reel.py` | Baja los datos, arma la página de cada día, la manda a grabar y la convierte en video |
| `reel.js` | El mapa: la misma paleta y las mismas partículas de viento del panel de `/clima/`, cuadro a cuadro |
| `reel.css`, `reel-severidad.css`, `reel-porcentajes.css` | La hoja de la pieza, la de la versión por defecto (con el nivel de lluvia por isla) y la de la versión con porcentajes |
| `grabar.mjs` | Graba la página con Chrome sin ventana (protocolo DevTools), sin dependencias |
| `islas.js` | El contorno de las islas. **Generado** por `islas.py` desde `geodatos/capas/igm/islas.geojson` |
| `textos.ejemplo.json` | Ejemplo de la etiqueta y la frase de cada día (`--textos`) |
| `fuentes/` | Zalando Sans Expanded, con su licencia (SIL OFL 1.1, `fuentes/OFL.txt`) |

## Avisos

- El reel **no es un pronóstico oficial** y lo dice en el pie de cada pieza. El oficial es del INAMHI.
- Los videos, los cuadros y los datos bajados no van al repositorio.
- Licencias de lo que se muestra: Open-Meteo con ECMWF (CC BY 4.0), tabla de mareas del INOCAR, UHSLC, IERSE (CC BY-NC-ND 4.0), GSC-USFQ, estaciones particulares publicadas con permiso e IGM. La línea pequeña del pie las nombra.
