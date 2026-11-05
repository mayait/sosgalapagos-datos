# El modelo HAND: cómo se calcula la susceptibilidad a inundación por quebradas

> **Resumen.** No existe un mapa oficial de amenaza por inundación pluvial para Galápagos (las capas nacionales de la SNGR y el INEC no tienen entidades en las islas). Para tener algo con qué priorizar, calculamos un índice topográfico propio, **HAND**, sobre el relieve de 30 m. Sirve para **priorizar**, no para **delimitar**: no es una simulación hidráulica ni tiene período de retorno.

## Qué es HAND

**HAND** (*Height Above Nearest Drainage*, Rennó et al. 2008; Nobre et al. 2011) asigna a cada celda del terreno su **altura sobre el cauce al que drena**. Se sigue el camino del agua cuesta abajo (dirección de flujo D8) hasta tocar un cauce y se resta la cota de ese punto del cauce a la cota de la celda.

- Una casa a **0,5 m** sobre su quebrada tiene HAND = 0,5 m: con poco que suba el agua, se moja.
- Una casa en una loma a **12 m** sobre su quebrada tiene HAND = 12 m: es muy improbable que la quebrada la alcance.

Es un índice de **posición en el relieve**. No dice cuánta agua viene ni con qué frecuencia; dice dónde se acumularía primero si una quebrada se desborda.

## Paso a paso (lo que hace `geodatos/scripts/03_dem.py`)

```
DSM Copernicus GLO-30 (30 m)
   │
   ├─ 1. Quemado de cauces: baja 3 m el DEM sobre las quebradas IGM 1:25 000
   │     (para que el flujo siga los cauces reales y no salte entre valles)
   ├─ 2. Relleno de pozos y depresiones, resolución de zonas planas (pysheds)
   ├─ 3. Dirección de flujo D8 y acumulación (área drenada por celda)
   ├─ 4. Red de referencia = celdas con ≥ 0,5 km² drenados
   │                       + quebradas IGM con ≥ 0,05 km² drenados
   ├─ 5. HAND = cota (DEM SIN quemar) − cota del cauce al que drena cada celda
   ├─ 6. Clases:  Alta ≤ 1 m · Media ≤ 2,5 m · Baja ≤ 5 m
   ├─ 7. Solo hasta 300 m del cauce (evita marcar mesetas planas lejanas)
   └─ 8. Suavizado: mediana 3×3 → polígonos ≥ 2 500 m²
          │
          └─ 08_exportar.py: recorta al área de interés, cierre/apertura de 12 m,
             publica las clases ACUMULADAS (Baja ⊃ Media ⊃ Alta)
```

| Parámetro | Valor | Dónde se cambia |
|---|---|---|
| Profundidad del quemado | 3 m | `03_dem.py`, `zb[igm_rio & land] -= 3.0` |
| Umbral de cauce de referencia | 0,5 km² (0,05 km² sobre quebradas IGM) | `03_dem.py`, variable `major` |
| Clases | ≤ 1 / ≤ 2,5 / ≤ 5 m | `03_dem.py`, `clsH` |
| Distancia máxima al cauce | 300 m | `03_dem.py`, `dist > 300` |
| Área mínima de polígono | 2 500 m² (1 500 m² tras el recorte) | `03_dem.py` y `08_exportar.py` |

Librerías: `pysheds` (necesita `numpy < 2.4`), `rasterio`, `scipy`, `shapely`.

## Dónde se usa

| Producto | Uso del HAND |
|---|---|
| Capa **«Susceptibilidad a inundación por quebradas»** (`export/galapagos/susceptibilidad_inundacion.geojson`) | Directamente, en tres clases |
| **Exposición** (`07_oficiales.py` → `resumen_exposicion.json`) | Cada edificio y vivienda recibe `susc_inundacion` 0–3 y se suman edificios y población en clase alta o media |
| **Puntos clave** | Cada punto lleva `en_susc_alta_media` |
| **Estudios** (`grd_riesgo_islas.py`) | Atributo `susceptibilidad_hand` en los puntos y tramos analizados |

El estudio de **La Cascada** no se apoya en HAND: allí el barrio es un **vaso cerrado** y se analizó con el DEM directamente (cota de rebose, volumen y área drenada; `12_cascada_analisis.py` a 30 m y `37_cascada_dtm.py` con el DTM de 1 m).

## Cómo se validó

- La clase alta coincide con el polígono oficial **«Riesgo de inundación – Puerto Ayora»** del CGREG.
- El polígono de **flujos de lodo por El Niño** del CGREG cae sobre la quebrada encima de **La Cascada**, el barrio más afectado el 30–31-oct-2026.
- **Falta** compararlo con la delimitación real de lo inundado y con marcas de agua (ver los [issues](https://github.com/mayait/sosgalapagos-datos/issues)).

## Santa Cruz: DTM de 1 m de la SGIAR

Desde noviembre de 2026, en **Puerto Ayora, el escarpe y Bellavista** el relieve es el **DTM de 1 m de la SGIAR** (Subsecretaría de Gestión de la Información y Análisis de Riesgo; producto Vricon/Maxar; `geodatos/datos/dtm_sgiar/`). Cambia dos cosas:

- **Relieve de 30 m fusionado** (`relieve_sgiar.py`): dentro de la cobertura del DTM, el relieve de 30 m de Santa Cruz es el DTM promediado; fuera, el Copernicus. En una franja de 300 m se pasa de uno a otro. Todo lo que lee `descargas/dem_recortes/santa_cruz_dem.tif` (cuencas, La Cascada, modelo 2D, cruces, tormentas sintéticas) usa ya este relieve.
- **HAND de 5 m**: dentro de la cobertura (menos la franja de transición), HAND, drenaje, costa baja y curvas se recalculan con el mismo método en una malla de 1/6 de segundo de arco (≈ 5 m), con 2,2 km de margen para que cuente el agua que entra por los bordes. Se empalman con las capas de 30 m. Cada polígono dice en `metodo` con qué relieve se calculó.

Efecto en la exposición de Santa Cruz (`resumen_exposicion.json`): los edificios en susceptibilidad alta pasan de 926 a 1 295 y la población en alta o media de 3 965 a 5 392. En la costa baja de 0 a 3 m quedan 77 edificios (antes, 162).

Frente a los puntos acotados del IGM, el DTM queda en mediana 1,0 m más bajo y el Copernicus 1,8 m más bajo; por encima de 100 m de altura el DTM se acerca al IGM 1,3 a 2 m más que el Copernicus. El DTM es de terreno, pero **no ve alcantarillas ni muros**, y las imágenes son de 2020–2024.

## Límites (decirlos siempre que se muestre el mapa)

1. **Fuera del DTM de la SGIAR, el DEM es de superficie (DSM)**: incluye techos y copas de árboles. En la ciudad y el bosque la cota está sesgada; frente al IGM hay un sesgo de −2 a −3 m. No usar cotas absolutas como umbrales normativos.
2. **30 m de resolución** (5 m en la cobertura del DTM): no ve alcantarillas ni pasos bajo vías; a 30 m tampoco cauces estrechos.
3. **Terreno muy plano** (Puerto Villamil): HAND marca casi todo como susceptible.
4. **No hay caudal ni período de retorno**: es posición topográfica, no simulación.
5. **Vasos cerrados** (como La Cascada): el relleno de depresiones del paso 2 los «borra»; hay que analizarlos aparte.

## Cómo mejorarlo

1. ~~Recalcular con un **DTM ≤ 1 m** en los poblados~~. Hecho en Santa Cruz con el DTM de la SGIAR (ver «Santa Cruz: DTM de 1 m de la SGIAR»). Falta en San Cristóbal e Isabela.
2. Ajustar las clases con **marcas de agua** y la delimitación oficial del evento.
3. Pasar de susceptibilidad a **amenaza** con un modelo hidrológico (HEC-HMS) e hidráulico 2D (HEC-RAS, ANUGA o SFINCS) por período de retorno.

## Referencias

- Rennó, C. D. et al. (2008). HAND, a new terrain descriptor using SRTM-DEM. *Remote Sensing of Environment*, 112(9), 3469–3481.
- Nobre, A. D. et al. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology*, 404(1–2), 13–29.
- Metodología completa de todas las capas: [`mapas-galapagos/documentacion/02-metodologia.md`](../mapas-galapagos/documentacion/02-metodologia.md).
