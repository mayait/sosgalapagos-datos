# Texto del issue para GitHub

Plantilla: **Propuesta de feature**. Copiar cada bloque en el campo del mismo nombre.

---

**Título**

```
[FEATURE] Capas cartográficas por emergencia (capas.json) — primer caso: inundaciones Galápagos 2026
```

---

**Problema o valor**

```
Durante las inundaciones por El Niño en Galápagos (30–31 oct 2026; barrio La Cascada en Puerto Ayora es
el más afectado) los coordinadores necesitan ver, junto a los puntos de acopio y las necesidades, el
contexto territorial: dónde están las quebradas y zonas inundables, qué cuencas drenan hacia cada
pueblo, dónde está el límite del Parque Nacional y la zona agrícola, qué servicios críticos (salud,
refugios, zonas seguras) caen en zona de riesgo, y la población expuesta.

Hoy el mapa público solo tiene las teselas de OpenStreetMap. No hay forma de añadir capas de contexto
por emergencia sin tocar código.
```

**Propuesta**

```
Capas cartográficas por emergencia, descritas en un manifiesto JSON:

  <NEXT_PUBLIC_CAPAS_BASE_URL | /capas>/<slug>/capas.json

- Si la emergencia no tiene manifiesto → el mapa queda exactamente como hoy (solo OSM).
- Si lo tiene → mapas base del manifiesto + grupos de capas GeoJSON/raster con estilos, clasificación
  por propiedad, leyendas, fichas (popups), botones "Ir a", zoom mínimo por capa, relleno rayado
  (áreas protegidas) y carga local de GeoJSON (solo en el navegador de quien lo carga).
- Las capas de contexto quedan SIEMPRE por debajo de los marcadores de recursos/necesidades.
- Los archivos se descargan solo al activar cada capa (lazy).

Implementación ya hecha y probada (parche adjunto, ~960 líneas, solo apps/web + docs/):
- src/lib/map-layers/manifest.ts (+ .test.ts) — tipos y lógica pura (node --test, 7 tests)
- src/lib/map-layers/leaflet-layers.ts — creación de capas Leaflet (panes, canvas, patrón SVG, raster)
- src/components/organisms/emergency-layers.tsx — organismo: panel, mapas base, zoom
- emergency-map.tsx — sustituye el <TileLayer> fijo por <EmergencyLayers slug={slug} />
- i18n es/en (10 claves map_layers_*), estilos en globals.css
- docs/capas-emergencia.md — especificación del formato
```

**Alcance mínimo**

```
Entra:
- Lectura de capas.json por slug, panel de capas con leyendas, mapas base, "Ir a", zoom_min.
- Publicar el paquete de Galápagos (slug galapagos-2026, 32 archivos, 13 MB).
- Documentación del formato.

Queda fuera (posibles siguientes pasos):
- Gestionar/subir capas desde el panel de administración (hoy se publican como archivos estáticos).
- Guardar capas en la API/DB por emergencia_id.
- Edición colaborativa de "áreas afectadas" desde la plataforma.
```

**Criterios de aceptación**

```
- [ ] /e/galapagos-2026 muestra el panel "Capas" con los grupos del manifiesto y sus leyendas.
- [ ] Una emergencia sin capas.json (p. ej. terremoto-venezuela-2026) se ve igual que hoy.
- [ ] Los marcadores de recursos/necesidades quedan por encima de las capas de contexto.
- [ ] Capas con zoom_min no se dibujan por debajo de ese zoom y el panel lo indica.
- [ ] Gate de CI en verde: web build, web lint, web test (incluye manifest.test.ts).
- [ ] docs/capas-emergencia.md publicado (excepción añadida en .gitignore).
```

**Dependencias o riesgos**

```
- Peso de los datos (13 MB; la capa mayor ~2,3 MB). Opción: servirlos desde un CDN/bucket con
  NEXT_PUBLIC_CAPAS_BASE_URL para no engordar el repo y poder actualizar "áreas afectadas" sin deploy.
- Teselas de terceros en el manifiesto (Esri, OSM, OpenTopoMap): requieren atribución (incluida).
- Licencias de datos: OSM (ODbL), Google Open Buildings (CC BY 4.0), Copernicus DEM, IGM/CGREG/SNGR
  (públicas, con cita). Detalle en el paquete.
- Algunas capas son modeladas (susceptibilidad HAND): se presentan como apoyo a la priorización, no
  como delimitación oficial (se indica en cada capa).
- Sin datos personales (se depuraron nombres/teléfonos de las fuentes oficiales).
- Contacto de datos: coordinación USFQ Galápagos.
```
