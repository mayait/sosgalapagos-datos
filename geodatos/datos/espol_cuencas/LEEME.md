# Cuencas hidrográficas de interés de Santa Cruz (ESPOL)

> **Autores:** Maurizio Mulas, Daniel Garcés, Erwin Larreta, Victoria Rosado y Valeria Vaca (ESPOL).
> Cítalos con nombre en todo mapa, descarga o documento que use esta capa.

Son las cuencas de interés con las que trabaja la mesa técnica de SOS Galápagos alrededor de Puerto Ayora. Las entregaron el 28-nov-2026 como `secciones_cuenca.kmz` (KML en EPSG:4326, capa «Seccion_Prueba» de ArcGIS).

## Archivos

| Archivo | Qué es |
|---|---|
| `cuencas_interes_santa_cruz.geojson` | 9 polígonos: secciones alta y baja de las subcuencas SCW01, SCW02 y SCW24, un fragmento de SCW01 y dos microcuencas |
| `resumen.json` | Huella del KMZ (SHA-256) y área de cada polígono |

Lo genera `geodatos/scripts/39_espol_cuencas_interes.py` a partir de `descargas/espol/secciones_cuenca.kmz` (fuera de git). **No se edita a mano.**

| Polígono | Área (km²) |
|---|---|
| SCW01, sección alta / baja (Puerto Ayora) | 7,05 / 11,55 |
| SCW01, fragmento de la sección baja | 0,064 |
| SCW02, sección alta / baja (oeste) | 5,52 / 15,23 |
| SCW24, sección alta / baja (este) | 1,17 / 20,29 |
| Microcuencas | 2,84 y 6,77 |

## Notas

- La **sección** (alta o baja) se asigna por posición: las altas quedan al norte de la franja intermedia (latitud −0,67). El KMZ no la trae.
- La **franja intermedia**, rayada en el mapa original de la ESPOL, no viene en el archivo.
- Se descarta un fragmento de 54 m² de SCW01.
- **Coherencia con las otras cuencas:**
  - SCW01 cae en un 94 a 99 % dentro de la cuenca de Puerto Ayora del modelo de SOS Galápagos y de la cuenca 29 del Instituto de Geografía USFQ.
  - SCW02 cae dentro de la cuenca 10 de la USFQ.
  - En la parte alta, la divisoria de SCW24 con Puerto Ayora no coincide con la de la USFQ: la sección alta de SCW24 queda un 45 % en la cuenca de Puerto Ayora de la USFQ.
