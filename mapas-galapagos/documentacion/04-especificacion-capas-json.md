# Capas cartográficas por emergencia (`capas.json`)

Cada emergencia puede tener, además de los puntos de acopio y las necesidades, **capas cartográficas de contexto**: zonas inundables, quebradas, límites de áreas protegidas, vías, población, servicios críticos, etc. Las capas se describen en un **manifiesto** (`capas.json`) que el mapa público (`/e/<slug>`) lee al cargarse.

- Si la emergencia **no** tiene manifiesto, el mapa no cambia: solo muestra OpenStreetMap.
- Si lo tiene, el mapa pinta los mapas base y las capas declaradas, y muestra un panel **«Capas»** con interruptores, leyendas, botones «Ir a» y carga local de GeoJSON.

## Dónde se publica

```
<NEXT_PUBLIC_CAPAS_BASE_URL | /capas>/<slug>/capas.json
<NEXT_PUBLIC_CAPAS_BASE_URL | /capas>/<slug>/<archivos .geojson, raster/…>
```

- Por defecto se sirve desde `apps/web/public/capas/<slug>/`.
- Para no meter datos pesados en el repositorio se puede usar `NEXT_PUBLIC_CAPAS_BASE_URL`, que apunta a un CDN o bucket con la misma estructura y CORS abierto.
- Los archivos se descargan **solo cuando una capa se activa**.

## Código

| Archivo | Rol |
|---|---|
| `apps/web/src/lib/map-layers/manifest.ts` | Tipos del manifiesto y lógica pura: clase, estilo, leyenda, popup y visibilidad. Se prueba con `node --test`. |
| `apps/web/src/lib/map-layers/manifest.test.ts` | Tests unitarios. |
| `apps/web/src/lib/map-layers/leaflet-layers.ts` | Crea las capas de Leaflet: panes, renderer canvas, relleno rayado SVG y raster. |
| `apps/web/src/components/organisms/emergency-layers.tsx` | Organismo React: carga el manifiesto, gestiona los mapas base, el panel y el zoom mínimo. |
| `apps/web/src/components/organisms/emergency-map.tsx` | Sustituye su `<TileLayer>` fijo por `<EmergencyLayers slug={slug} />`. |

Apilado de los panes de Leaflet, de abajo arriba:

| Pane | Contenido | z-index |
|---|---|---|
| `rg-capas-fondo` | Raster | 350 |
| `rg-capas-patron` | Áreas rayadas | 390 |
| `rg-capas-areas` | Polígonos | 410 |
| `rg-capas-lineas` | Líneas | 430 |
| `rg-capas-puntos` | Puntos de contexto | 590 |
| `markerPane` | Marcadores de la plataforma | 600 |

Así los recursos y necesidades de ResponseGrid quedan **siempre por encima** de las capas de contexto.

## Formato

```jsonc
{
  "version": 2,
  "titulo": "Capas de la emergencia — Galápagos",     // título del panel
  "generado": "2026-11-01",
  "mapas_base": [                                       // opcional; sin él se usa OSM
    { "id": "claro", "titulo": "Claro", "url": "https://…/{z}/{y}/{x}", "atribucion": "Esri…",
      "maxZoom": 19, "maxNativeZoom": 16, "defecto": true }
  ],
  "islas": {                                            // opcional: botones «Ir a»
    "Puerto Ayora": { "bounds": [[-0.762, -90.330], [-0.722, -90.298]] }
  },
  "grupos": [
    { "id": "inundacion", "titulo": "Zonas inundables", "capas": [ /* capas */ ] }
  ]
}
```

### Capa

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Único en el manifiesto. |
| `titulo` | string | Texto del interruptor. |
| `tipo` | `poligono` \| `linea` \| `punto` \| `raster` | Decide el pane y la forma de la leyenda. |
| `archivo` | string | GeoJSON (EPSG:4326). Relativo al manifiesto, o absoluto (`/…`, `https://…`). |
| `raster` | string | Solo `raster`: dibuja `raster/<región>_<raster>.png` con los límites de `raster/limites.json` (`{"<región>": {"bounds": [[s,w],[n,e]]}}`). |
| `opacidad` | número | Solo `raster`. |
| `visible` | bool | Encendida al cargar. |
| `zoom_min` | número | No se dibuja por debajo de ese zoom; el panel avisa «Acércate…». |
| `fuente`, `descripcion` | string | Se muestran bajo el título. |
| `elementos` | número | Informativo. |
| `estilo` | Leaflet `PathOptions` (+ `radius`) | Estilo base. |
| `borde` | `PathOptions` | Línea de contorno dibujada debajo (por ejemplo, el borde blanco de un río). |
| `filtro` | `{ "propiedad", "en": [...] }` | Dibuja solo los elementos cuya propiedad está en la lista. Permite varias capas sobre un mismo archivo. |
| `clasificar` | ver abajo | Estilo según una propiedad; alimenta la leyenda. |
| `estilo_si` | `[{ "propiedad", "igual_a" \| "distinto_de", "estilo", "etiqueta"? }]` | Reglas que se aplican encima. Por ejemplo, línea discontinua si `estado ≠ validada`. |
| `rotulo` | `{ "propiedad", "permanente"?, "sufijo"? }` | Etiqueta al pasar el ratón; si es `permanente`, visible desde zoom 15. |
| `popup` | `{ "titulo", "titulo_defecto"?, "sufijo_titulo"?, "campos": { "prop": "Etiqueta" } }` | Ficha al hacer clic. Todo el texto se escapa. |
| `leyenda` | `[[color, texto], …]` | Leyenda explícita (sustituye a la derivada). |
| `patron` | `{ "id", "color", "separacion"?, "grosor"?, "fondo"?, "opacidad_fondo"?, "opacidad"? }` | Relleno rayado SVG. La capa usa `"fillColor": "url(#<id>)"`. |

### `clasificar`

```jsonc
// por valor (se compara como texto); "otro" es el valor por defecto
"clasificar": { "propiedad": "nivel", "valores": {
  "3": { "etiqueta": "Alta", "color": "#173f8a", "fillColor": "#1d4a9e" } }, "otro": { … } }

// por rangos numéricos ("hasta" inclusive, en orden)
"clasificar": { "propiedad": "poblacion_estimada", "rangos": [
  { "hasta": 10, "etiqueta": "1–10 hab.", "fillColor": "#fde68a" }, … ] }
```

Cada clase es un `PathOptions` con `etiqueta` (en la leyenda) y, en las capas de puntos, `simbolo` opcional: una letra dentro de un marcador circular, por ejemplo `+` para salud.

En las capas de puntos, si un elemento tiene `en_susc_alta_media: true`, el marcador lleva un **anillo azul**: es un servicio que puede quedar afectado por la inundación.

## Buenas prácticas para preparar datos

- GeoJSON en **EPSG:4326** con coordenadas a 5 decimales (≈ 1 m). Simplificar las geometrías y quitar propiedades que no se muestran.
- Recortar al área de interés y **no publicar datos personales**: nombres de afectados, teléfonos de responsables, etc.
- Indicar `fuente` en cada capa y distinguir en `descripcion` lo **oficial** de lo **modelado**.
- Las capas pesadas, como edificios o curvas, deben llevar `zoom_min`.
- Como referencia: el paquete de Galápagos tiene 32 archivos y pesa 13 MB. Cada capa pesa como mucho 2,3 MB.
