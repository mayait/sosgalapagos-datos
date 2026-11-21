# Visor de `/mapas` (retirado el 21-nov-2026)

`index.html` era el visor Leaflet de `sosgalapagos.org/mapas/`. Se retiró el 21-nov-2026 por decisión de Julián: el mapa único del sitio es **[sosgalapagos.org/riesgos](https://sosgalapagos.org/riesgos/)**, del repositorio [`mayait/sosgalapagos-plataforma`](https://github.com/mayait/sosgalapagos-plataforma). Quien entra a `/mapas/` llega a `/riesgos/` (redirección en el Caddy del sitio).

No se borró: queda aquí por si hace falta consultarlo.

## Qué sigue vivo

Solo se retiró la página. **`/mapas/` sigue siendo la publicación de datos** y `/riesgos/` lee de ahí:

| Dirección | Qué es |
|---|---|
| `/mapas/capas.json` | Manifiesto de grupos, capas, estilos, mapas base y buscador (`geodatos/scripts/visor_mapas.json`) |
| `/mapas/descargas.json` | Índice de descargas |
| `/mapas/version.txt` | Versión de cada publicación |
| `/mapas/datos/…` | Capas en GeoJSON, imágenes de relieve y fotos de los reportes |
| `/mapas/descargas/…` | Shapefile y GeoJSON en zip |
| `/mapas/teselas/…` | Teselas del DTM |

Se publican igual que antes: `servidores/publicar.sh mapas`.

## Qué pasó con cada función del visor

| Función | Dónde está ahora |
|---|---|
| Capas, leyendas, mapas base, descargas | `/riesgos/` (panel «Capas») y `/riesgos/descargas/` |
| Buscador de calles, barrios, lugares y coordenadas | `/riesgos/` (la lupa junto a «Capas») |
| «Mis puntos» | `/riesgos/`. Usa la misma clave del navegador, así que lo guardado se conserva |
| Enlaces a un lugar (`#ptoayora`, `#lat,lon,zoom`) | Iguales en `/riesgos/`; la redirección conserva lo que va tras `#` |
| Punto de análisis, imagen con leyenda y modo captura | No se llevaron: quien necesite ese análisis descarga las capas |
| Tabla de exposición por isla | Pendiente: irá como PDF en las descargas de la portada |

## Si hubiera que volver a servirlo

1. Copiar `index.html` a `geodatos/web/` y restaurar en `10_publicar_web.py` las dos líneas que lo escribían en `publicar/mapas/` (reemplazando `__VERSION__`).
2. Quitar del `Caddyfile` del sitio (`mayait/sosgalapagos`) las líneas `@visor` y `redir @visor /riesgos/ 302` del bloque de `/mapas`.
