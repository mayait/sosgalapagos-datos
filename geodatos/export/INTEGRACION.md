# Pasar las capas al mapa de ResponseGrid

## Qué contiene `export/`

| Ruta | Contenido |
|---|---|
| `galapagos/capas.json` | Manifiesto: grupos, capas, estilos (Leaflet `PathOptions`), clasificación por propiedad, leyendas, popups, rótulos, zoom mínimo y encuadres por isla. |
| `galapagos/*.geojson` | 17 capas en EPSG:4326 con coordenadas redondeadas a 5 decimales (≈ 1 m). Están recortadas al área de interés, excepto la de tsunami (INOCAR) y la de cuencas aportantes, que se dejan completas. |
| `galapagos/area_interes.geojson` | Zona agrícola y urbana completas (zonificación PNG 2017 y CGREG), las **cuencas completas que drenan a los poblados**, 500 m alrededor de las zonas pobladas y 300 m alrededor de las vías. |
| `galapagos/parque_nacional.geojson`, `limite_parque.geojson`, `zona_agricola.geojson`, `parque_zonificacion.geojson` | Parque Nacional (rayado verde), su límite con la zona colonizada, la zona agrícola y la zonificación interna del parque. |
| `galapagos/cuencas_localidad.geojson`, `cuencas_aportantes.geojson` | La cuenca completa de cada localidad (todo lo que drena hacia ella, aunque atraviese otros poblados) y las subcuencas por punto de entrada. |
| `galapagos/raster/` | Relieve sombreado (la isla completa) y pendientes (solo el área de interés), con sus límites en `limites.json`. |
| `galapagos/resumen_exposicion.json` | Edificios y población expuestos por isla. |
| `integracion/capas-manifiesto.ts` | Motor tipado que lee el manifiesto y crea las capas: `prepararMapa`, `crearCapa`, `rendererPatron`, `leyendaDe`, `popupDe`. Pasa `tsc --strict`. |
| `integracion/copiar-a-app.sh` | Copia el paquete a `app/apps/web/public/galapagos/capas/` y el motor a `src/components/organisms/galapagos/`. |

El paquete pesa unos 12 MB. Cada capa se descarga solo cuando se activa.

## Pasos

1. Ejecutar `./export/integracion/copiar-a-app.sh`.
2. En `galapagos-map-layers.tsx`:
   - leer `/galapagos/capas/capas.json`;
   - llamar a `prepararMapa(map, '/galapagos/capas/')`;
   - las capas con `patron` (el parque) usan `rendererPatron`; `crearCapa` lo hace solo;
   - por cada capa con `visible: true`, crear su capa con `crearCapa(capa, ctx)` y añadirla al mapa en el orden del manifiesto.
3. Reemplazar `L.control.layers` por un panel que agrupe por `manifiesto.grupos` y pinte `leyendaDe(capa)`. El visor (`geodatos/visor/index.html`) sirve de referencia: tiene interruptores, leyenda en línea y aviso de zoom mínimo.
4. Respetar `zoom_min`: quitar la capa del mapa por debajo de ese zoom (edificios y curvas a 14–15).
5. Añadir `CSS_CAPAS` a `globals.css`.
6. Los botones de isla salen de `manifiesto.islas` y usan `map.fitBounds(bounds)`.
7. Retirar `drenajes-osm.geojson` y `vias-osm.geojson`, que quedan reemplazados por `quebradas`, `drenaje_adicional` y `vias`. **Mantener `areas-afectadas.geojson`**: es la capa operativa de la emergencia (áreas validadas por el COE).

## Cómo actualizar

Para regenerar el paquete:

```bash
cd geodatos && .venv/bin/python -I scripts/08_exportar.py
```

Los estilos se cambian en `scripts/capas.json`, no en `export/`. Después de cambiarlos, hay que volver a ejecutar `08` y el script de copia.

## Avisos

- La susceptibilidad, la costa baja, los cauces adicionales y las cuencas son un **modelo** sobre un DSM de 30 m. Hay que presentarlos como apoyo a la priorización, no como delimitación oficial.
- `puntos_clave` marca con `en_susc_alta_media` y `en_zona_tsunami` los servicios que pueden quedar afectados. El visor les dibuja un anillo azul.
- Se quitaron nombres y teléfonos personales (albergues y eventos de la SNGR). No copiar `descargas/oficiales/` al proyecto principal.
