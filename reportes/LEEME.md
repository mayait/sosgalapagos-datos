# Reportes de campo

Convierte lo que la gente reporta por WhatsApp durante una emergencia en una capa de mapa con fotos: dónde pasa, qué tan grave es y a qué hora.

**Son reportes ciudadanos sin verificar. No son datos oficiales.** Esa frase va siempre en el mapa y en cualquier texto que los use.

## Qué hay

| Ruta | Tipo | Qué es |
|---|---|---|
| `scripts/01_ingerir.py` | fuente | Suma la carpeta exportada de WhatsApp a `privado/`. Incremental: cada corrida es un «lote» |
| `scripts/02_medios.py` | fuente | Fotogramas de los videos, láminas de contacto y transcripciones (whisper.cpp) |
| `scripts/03_publicar.py` | fuente | Valida lo curado y genera la capa, las fotos públicas y el visor |
| `scripts/04_areas.py` | fuente | Genera la capa de áreas afectadas (`geodatos/capas/operativas/areas_afectadas.geojson`) desde `areas.json`, los reportes, los barrios y las vías. Hace la misma validación de teléfonos y nombres |
| `scripts/05_flujo.py` | fuente | Genera `eventos/<fecha>/flujo_observado.geojson` («Por dónde bajó el agua», con flechas) desde `flujo_observado.json` y las calles de OSM. `10_publicar_web.py` la suma al grupo «Emergencia en curso» |
| `scripts/06_buenas.py` | fuente | Valida `buenas_noticias.json` y genera la capa de buenas noticias y ayuda (un corazón por acción), con sus fotos en `publicar/<fecha>/buenas/` |
| `eventos/<fecha>/buenas_noticias.json` | **fuente, curada** | Buenas noticias y ayuda: entregas de comida, cocinas comunitarias, donaciones, rescates de voluntarios, vías rehabilitadas. Cada una dice quién la hace (`autor`) y si está anunciada, en curso o realizada (`estado_accion`). Las `sin_ubicar` no van al mapa |
| `eventos/<fecha>/buenas_noticias.geojson` | generado | La capa de buenas noticias. No se edita a mano |
| `eventos/<fecha>/reportes.json` | **fuente, curada** | Un reporte por lugar: hora, coordenadas, tipo, gravedad, texto y fotos elegidas |
| `eventos/<fecha>/areas.json` | **fuente, curada** | Zonas del evento: inundadas, corredores y encañadas (`riesgo`), evacuación del COE y cortes de servicio. Cada una dice su geometría base (barrio, franja sobre calles de OSM o círculo alrededor de un reporte), los reportes que la sustentan y el detalle con horas |
| `eventos/<fecha>/flujo_observado.json` | **fuente, curada** | Trazo del coordinador: por dónde bajó el agua (tramos sobre calles de OSM o vértices libres, en el sentido del agua) |
| `eventos/<fecha>/puntos_control.json` | **fuente, curada** | Profundidad del agua leída en fotos y videos (tabla de equivalencias). Calibra la susceptibilidad ajustada (`geodatos/scripts/est_21nov_ajuste.py`, ver `docs/modelo-hand.md`) |
| `eventos/<fecha>/reportes.geojson` | generado | La capa. No se edita a mano |
| `web/index.html` | fuente | Visor (Leaflet) |
| `privado/` | **no va a git** | Mensajes con nombres y teléfonos, medios crudos, láminas, transcripciones |
| `publicar/` | no va a git | Lo que se sube al servidor: visor, capa y fotos sin metadatos |

## Cómo se actualiza (cada vez que llega información nueva)

```bash
PY=geodatos/.venv/bin/python
$PY -I reportes/scripts/01_ingerir.py "<carpeta de WhatsApp>"   # dice cuántos mensajes nuevos trae el lote
WHISPER_MODELO=<modelo ggml> $PY -I reportes/scripts/02_medios.py
# revisar el lote nuevo y editar eventos/<fecha>/reportes.json (ver abajo)
$PY -I reportes/scripts/03_publicar.py
# si los reportes nuevos cambian una zona, editar eventos/<fecha>/areas.json y regenerar las áreas afectadas:
$PY -I reportes/scripts/04_areas.py                             # escribe geodatos/capas/operativas/areas_afectadas.geojson
# buenas noticias y ayuda (capa aparte, con corazón): editar eventos/<fecha>/buenas_noticias.json y generar
$PY -I reportes/scripts/06_buenas.py
python3 -m http.server -d reportes/publicar/<fecha> 8765        # verlo en local
# Sumarlos al visor público /mapas/ (capa «Reportes ciudadanos del 21-nov (sin verificar)», grupo «Emergencia en curso»):
$PY -I geodatos/scripts/10_publicar_web.py                      # copia la capa y las fotos a geodatos/publicar/mapas/
python3 -m http.server -d geodatos/publicar/mapas 8766          # verlo en local
```

`10_publicar_web.py` falla si falta `reportes/publicar/<fecha>/` (corre antes `03_publicar.py` y `06_buenas.py`) y solo lee de ahí, nunca de `privado/`. El estilo de la capa y su ficha están en `geodatos/scripts/visor_mapas.json`; la ficha con fotos es genérica (`popup.fotos` en `geodatos/web/index.html`).

`04_areas.py` no publica nada por sí mismo: la capa llega a `geodatos/export/galapagos/` con `geodatos/scripts/08_exportar.py` (la copia tal cual) y de ahí a `mapas-galapagos/datos/` con `09_entregable.py`. Todas las zonas salen con `estado: por_validar` (línea discontinua). La geometría de `areas.json` se escribe así (se puede anidar): `{"barrio": "LA CASCADA"}`, `{"via": "Seymour", "buffer_m": 12}`, `{"reporte": "r10", "buffer_m": 60}`, `{"punto": [lat, lon], "buffer_m": 60}`, `{"cruce": ["Seymour", "Petrel"], "buffer_m": 50}`, `{"al_norte_de": lat}`, `{"union": […]}`, `{"interseccion": […]}` y `{"menos": [a, b]}`. Regla: el polígono entero de un barrio solo cuando los reportes hablan del barrio entero; si no, franja sobre las calles nombradas o círculo alrededor del punto. Las zonas `riesgo` y `evacuacion` dicen en `detalle` cuándo la ubicación es aproximada.

En un *worktree*, `reportes/privado` es un enlace a la carpeta de la copia principal, igual que `geodatos/descargas`.

El WhatsApp de trabajo se exporta en la subcarpeta `Trabajo/` de la carpeta de WhatsApp, con su propio `remitentes.json`: `01_ingerir.py` solo mira un nivel, así que se ingiere en una segunda corrida (otro lote) con una carpeta que tenga solo los chats con reportes, sin los grupos ajenos a la emergencia. Los videos que llegan como documento (`.mov`) no pasan por `02_medios.py`: sus fotogramas se sacan a mano en `privado/<fecha>/fotogramas/<id8>_<n>.jpg`.

### Revisar un lote gastando poco

La revisión es el único paso que necesita criterio. Para que cueste poco:

1. Solo se mira el lote nuevo: mensajes con `lote == N` en `privado/<fecha>/mensajes.jsonl` y láminas `lote0N_*.jpg`.
2. Lo hace un agente Sonnet (es trabajo simple: describir y transcribir). Recibe el texto del lote, las transcripciones y las láminas, y devuelve por cada mensaje útil: id, lugar que nombra, qué muestra y si suma a un reporte que ya existe.
3. Quien coordina solo decide los cambios en `reportes.json`. No vuelve a mirar los medios, salvo los dudosos.

## Reglas de lo que se publica

- **Nada de nombres, teléfonos ni voces.** `03_publicar.py` se niega a generar si un texto trae un teléfono o el nombre de alguien de los grupos.
- **De los videos solo se publica un fotograma**, no el video: el audio trae voces y nombres.
- No se publican fotos donde se reconozca a una persona en primer plano, ni menores, ni capturas de pantalla de chats.
- No se publica la casa exacta de quien pide rescate: el punto va a la calle o al cruce.
- Las fotos públicas salen sin EXIF y a 1280 px.
- Cada reporte dice su `precision`: `exacta`, `cruce`, `calle`, `barrio`, `aproximada`, `por_confirmar` o `sin_ubicar`. Los `sin_ubicar` no van al mapa: salen en la lista «Por ubicar».
- `estado`: `sin_verificar` (una sola fuente), `varias_fuentes` u `oficial` (aviso de una institución reenviado).

## Buenas noticias y ayuda

Van en una capa propia del grupo «Emergencia en curso» («Buenas noticias y ayuda del 21-nov»), con un corazón rosa. No son reportes de riesgo: no llevan gravedad.

- **`autor` es obligatorio** y es una organización, institución, empresa o colectivo («Fundación Torraja», «COE cantonal», «vecinos de El Bosque»). Nunca el nombre de una persona particular. Si no se sabe: «Autor sin identificar», y se anota en `pendiente` qué falta.
- `06_buenas.py` hace la misma validación de teléfonos y nombres que `03_publicar.py`. Si el nombre de una organización coincide con el de un contacto de los grupos, se declara en la lista `organizaciones` del JSON; la comprobación no se quita.
- `estado_accion`: `anunciado` (se ofreció o se avisó, sin confirmar), `en_curso` o `realizado`. El texto dice siempre qué está confirmado y qué no.
- `mensajes` guarda de qué mensaje sale cada una (solo el identificador), para completar autores después.
- Las fotos siguen las mismas reglas de arriba. El marcador (`pinCorazon`) está en `geodatos/web/index.html` y la capa en `geodatos/scripts/visor_mapas.json` (`marcador: corazon`).

## Gravedad

| | |
|---|---|
| 1 | Leve: agua en la calle, se puede pasar |
| 2 | Moderada: calle inundada o agua empozada |
| 3 | Grave: el agua entra a las casas o corta una vía |
| 4 | Muy grave: agua hasta la primera planta, personas atrapadas o rescates |

## Pendiente

- Publicar el visor propio de `reportes/publicar/` en `sosgalapagos.org`: falta la ruta en el Caddy (repositorio `sosgalapagos`) y el paso en `servidores/publicar.sh`. No se despliega sin que Julián lo pida.
- Desplegar `/mapas/` con la capa nueva: lo hace Julián con `servidores/publicar.sh mapas` desde `main`.
