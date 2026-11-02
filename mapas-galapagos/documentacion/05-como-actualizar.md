# Cómo actualizar los mapas

## A. Actualizar las áreas afectadas (lo más frecuente)

La capa operativa es `datos/areas_afectadas.geojson`: polígonos que se dibujan en el grupo «Emergencia en curso».

1. Dibujar o recibir los polígonos. Pueden venir del COE, de la SNGR, de un vuelo de dron, de geojson.io, QGIS o Google My Maps exportado a GeoJSON. Deben estar en **EPSG:4326**.
2. Poner a cada polígono estas propiedades:

   | Propiedad | Valores | Efecto en el mapa |
   |---|---|---|
   | `nombre` | texto | Título de la ficha |
   | `tipo` | `inundacion` · `servicio` · `deslave` · `riesgo` | Color: azul, morado, marrón o rojo |
   | `estado` | `validada` u otro valor (`por_validar`…) | `validada` se dibuja con línea continua; cualquier otro valor, con línea discontinua |
   | `detalle`, `fuente`, `fecha` | texto | Aparecen en la ficha |

3. Reemplazar el archivo en **dos lugares**:
   - `geodatos/capas/operativas/areas_afectadas.geojson`, para que las siguientes regeneraciones lo conserven;
   - el sitio publicado: `app/apps/web/public/capas/galapagos-2026/areas_afectadas.geojson` en la copia local, o donde lo publique ResponseGrid.
4. Recargar el mapa. **No hace falta recompilar.** Los archivos se piden siempre sin caché.

Para **probar** un archivo antes de publicarlo, se puede usar el botón **«+ Cargar capa GeoJSON»** del panel. Solo lo verá quien lo cargue.

## B. Cambiar colores, textos, capas visibles o encuadres

Se edita `geodatos/scripts/capas.json` (el manifiesto) y luego se regenera (ver C). La especificación del formato está en `04-especificacion-capas-json.md`. Ejemplos:
- Encender una capa al abrir el mapa: `"visible": true`.
- Cambiar el color de la susceptibilidad alta: `clasificar.valores["3"].fillColor`.
- Añadir un botón «Ir a»: una entrada nueva en `islas` con `bounds` `[[sur, oeste], [norte, este]]`.

## C. Regenerar todo el paquete

```bash
cd geodatos
# Solo si cambian los datos de origen (≈ 15 min, sobre todo por el paso 02):
.venv/bin/python -I scripts/02_osm_extraer.py descargas/osm/ecuador-latest.osm.pbf
.venv/bin/python -I scripts/04_igm_wfs.py && .venv/bin/python -I scripts/05_igm_limpiar.py
.venv/bin/python -I scripts/03_dem.py
.venv/bin/python -I scripts/06_integrar.py && .venv/bin/python -I scripts/07_oficiales.py
.venv/bin/python -I scripts/07b_cuencas_aportantes.py
# Siempre:
.venv/bin/python -I scripts/08_exportar.py      # recorta, simplifica y genera export/galapagos + capas.json
.venv/bin/python -I scripts/09_entregable.py    # actualiza esta carpeta (datos, visor, catálogo, código y parche)
```

Después hay que copiar `mapas-galapagos/datos/` al lugar donde lo sirve ResponseGrid: `apps/web/public/capas/galapagos-2026/`, o el CDN definido en `NEXT_PUBLIC_CAPAS_BASE_URL`.

## D. Datos nuevos que conviene incorporar en cuanto existan

1. **Delimitación oficial de las zonas inundadas** del 30–31 de octubre (COE, SNGR o dron). Va a `areas_afectadas.geojson` con `estado: validada`.
2. **Catastro municipal** de Santa Cruz, San Cristóbal e Isabela, para tener edificios y predios exactos.
3. **Puntos de encuentro y refugios para inundación**, si el COE los define distintos de los de tsunami.
4. Un **modelo de terreno sin edificios** (DTM) o un levantamiento LiDAR o fotogramétrico de los pueblos. Mejoraría mucho la susceptibilidad.
