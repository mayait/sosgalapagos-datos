# Guía técnica: capas cartográficas por emergencia

Dirigida a los desarrolladores de ResponseGrid. La especificación completa del formato está en `codigo/docs/capas-emergencia.md`; es el mismo archivo que el parche añade en `docs/`.

## 1. Qué hace

`EmergencyMap` recibe `slug`. En lugar del `<TileLayer>` fijo de OSM, ahora pinta `<EmergencyLayers slug={slug} />`, que funciona así:

1. Pide `<NEXT_PUBLIC_CAPAS_BASE_URL ?? '/capas'>/<slug>/capas.json` (sin caché).
2. **Si no existe** (404 o error), renderiza el mismo `<TileLayer>` de OSM que había antes. Las demás emergencias no cambian.
3. **Si existe**, hace cuatro cosas:
   - crea los panes `rg-capas-*`, con z-index de 350 a 590, todos por debajo del `markerPane` (600);
   - pinta el mapa base que el manifiesto marca por defecto;
   - pinta las capas con `visible: true`, en el orden del manifiesto;
   - muestra un panel «Capas» (arriba a la derecha) con «Ir a», el selector de mapa base, los interruptores por grupo, las leyendas, el aviso de `zoom_min` y «+ Cargar capa GeoJSON».
4. Cada GeoJSON se descarga **la primera vez que se activa** su capa y queda en caché en memoria. Los polígonos y las líneas usan el renderer canvas. Las áreas protegidas usan un renderer SVG con un `<pattern>` de rayas.

## 2. Archivos del parche

Base: `main` @ `d83c2e5` (`chore(deploy): desplegar la API en srv07…`).

| Archivo | Cambio |
|---|---|
| `apps/web/src/lib/map-layers/manifest.ts` | **Nuevo.** Tipos del manifiesto y funciones puras: `classFor`, `styleFor`, `legendFor`, `popupHtml` (escapa el HTML), `resolveUrl`, `defaultVisibility`, `isDrawable`. Importa Leaflet solo como tipo. |
| `apps/web/src/lib/map-layers/manifest.test.ts` | **Nuevo.** 7 tests con `node --test`. |
| `apps/web/src/lib/map-layers/leaflet-layers.ts` | **Nuevo.** `capasBaseUrl`, `loadManifest`, `prepareMap` (panes y renderers) y `createLayer` (GeoJSON, raster, patrón y marcadores con símbolo). |
| `apps/web/src/components/organisms/emergency-layers.tsx` | **Nuevo.** Organismo cliente: manifiesto, mapa base, sincronización de capas, zoom y panel. |
| `apps/web/src/components/organisms/emergency-map.tsx` | `TileLayer` → `<EmergencyLayers slug={slug} />`, y se quita el import de `TileLayer`. |
| `apps/web/src/i18n/messages/{es,en}.ts` | 10 claves `ui.map_layers_*`. |
| `apps/web/src/app/globals.css` | Clases `rg-capas-multiply`, `rg-capas-rotulo` y `rg-capas-lejos`. |
| `docs/capas-emergencia.md` | **Nuevo.** Especificación del formato. |
| `.gitignore` | Excepción `!/docs/capas-emergencia.md`. Hace falta porque `/docs/*` está ignorado. |

No toca la API, la base de datos ni el cliente tipado, así que **no hacen falta migraciones ni `gen:api`**.

## 3. Aplicar y probar

```bash
git checkout main && git fetch origin && git merge --ff-only origin/main
git checkout -b feature/NN-capas-por-emergencia
git apply --3way capas-por-emergencia.patch

# datos de Galápagos (si se sirven desde el repo)
mkdir -p apps/web/public/capas/galapagos-2026
cp -R <paquete>/mapas-galapagos/datos/. apps/web/public/capas/galapagos-2026/

# gate web
pnpm install --frozen-lockfile
pnpm --filter @reliefhub/api-client build && pnpm --filter web build
pnpm --filter web lint
pnpm --filter web test
```

**Prueba manual** con `next start`, porque el mapa es `dynamic(ssr:false)`:

- `/e/galapagos-2026`:
  - aparece el panel «Capas» con 8 grupos;
  - el Parque Nacional se ve rayado en verde;
  - al hacer clic en una quebrada se abre su ficha;
  - las curvas, con `zoom_min` 14, solo se dibujan de cerca, y el panel avisa de ello mientras tanto;
  - «Ir a → San Cristóbal» encuadra la isla;
  - los marcadores de recursos quedan por encima de todo.
- `/e/terremoto-venezuela-2026`: el mapa se ve igual que antes (solo OSM) y en la consola de red aparece un 404 de `capas.json`.

## 4. Publicar los datos

| Opción | Cómo | Ventajas e inconvenientes |
|---|---|---|
| **A. En el repo** | `apps/web/public/capas/galapagos-2026/` (32 archivos, 13 MB) | Lo más simple. Pero cualquier cambio de datos exige un PR y un deploy, y el repositorio crece 13 MB. |
| **B. CDN o bucket** | Subir `datos/` a `https://<cdn>/capas/galapagos-2026/` y definir `NEXT_PUBLIC_CAPAS_BASE_URL=https://<cdn>/capas` en Vercel | Recomendada en emergencia: las **áreas afectadas** se actualizan sin desplegar. Necesita CORS `GET` abierto y `Cache-Control` corto para `areas_afectadas.geojson` y `capas.json`. |

`NEXT_PUBLIC_*` se fija en el build. Después de cambiar la variable hay que volver a desplegar la web.

## 5. Datos de Galápagos

- **32 archivos:** 23 GeoJSON, `capas.json`, `resumen_exposicion.json` y `raster/` (6 PNG más `limites.json`). Hay dos GeoJSON (`edificios_expuestos` y `parque_zonificacion`) que se publican pero no están activados en el manifiesto; se pueden añadir como capas cuando se quiera.
- **Formato:** EPSG:4326 con coordenadas a 5 decimales.
- **Peso:** la capa más pesada es `susceptibilidad_inundacion.geojson` (2,3 MB).
- **Privacidad:** no hay datos personales.
- **Catálogo:** `../documentacion/01-catalogo-de-capas.md`.
- **Origen:** los datos los regenera la coordinación de USFQ Galápagos con scripts reproducibles (`geodatos/scripts/01`–`09`). ResponseGrid solo tiene que **servir** los archivos.

## 6. Decisiones de diseño

- **Manifiesto estático y no API:** no hay migraciones ni endpoints, sirve hoy y desacopla la preparación de los datos (GIS) de la plataforma. Más adelante se puede servir el mismo JSON desde la API por `emergency_id`, sin cambiar el componente: basta con apuntar `capasBaseUrl` a otra ruta.
- **Lógica pura separada de Leaflet:** se puede probar con `node --test` sin DOM, como `supply-lines.ts`.
- **Estilos como `PathOptions` de Leaflet:** no hay un lenguaje de estilos propio, y quien prepara los datos ve directamente qué opción cambia.
- **Seguridad:** todo texto de los datos que llega al HTML (popups, tooltips y marcadores) pasa por `escapeHtml`. El manifiesto se considera contenido de confianza, publicado por el equipo, pero aun así se escapan también los colores y los ids del patrón.

## 7. Posibles siguientes pasos

1. Subir y gestionar capas desde el panel de administración de la emergencia (almacenamiento en `files`).
2. Endpoint `GET /emergencies/:id/layers` que devuelva el manifiesto (para versionado y auditoría).
3. Editar las áreas afectadas desde la plataforma, con validación por coordinadores (estado `validada`).
4. Leyenda plegable o pantalla completa del mapa para móviles.
