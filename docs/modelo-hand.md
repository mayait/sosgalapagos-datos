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

## Santa Cruz: DEM de 10 m de SIGTIERRAS (desde el 28-nov-2026)

Fuera de la cobertura del DTM de la SGIAR, el relieve de Santa Cruz ya no es el Copernicus sino el **DEM de 10 m de SIGTIERRAS**, que entregó el Instituto de Geografía de la USFQ junto con sus cuencas, subcuencas y drenaje (`geodatos/datos/usfq_geografia/LEEME.md`).

- **Prioridad del relieve**: DTM 1 m SGIAR > SIGTIERRAS 10 m > Copernicus (solo donde no hay ninguno de los dos, ≈ 3 % de la tierra). Lo hace `relieve_sigtierras.py` antes de `relieve_sgiar.py`.
- **Tres mallas empalmadas**: 5 m dentro del DTM, 10 m (1/3 de segundo de arco) en el resto de la cobertura de SIGTIERRAS y 30 m fuera. Cada polígono dice en `metodo` y cada línea en `relieve` con qué malla se calculó.
- **Calidad**: frente a 7 859 puntos acotados del IGM, error absoluto medio de 0,52 m (Copernicus: 2,70 m). Es de terreno, no de superficie. El acuerdo es tan alto que probablemente se hizo en parte con la cartografía del IGM: no es un control independiente.
- **Efecto** (toda la isla, fuera del DTM): la clase alta pasa de 4 671 a 5 889 ha, la media de 6 770 a 4 203 ha y la baja de 8 525 a 6 159 ha. Los cauces de ≥ 0,5 km² que quedan a 30 m o menos de un cauce de la USFQ pasan del 25 % al 61 %. En los poblados casi no cambia, porque ya estaban en el DTM: edificios en alta de 1 295 a 1 314, población en alta o media de 5 392 a 5 394, costa baja de 0 a 3 m de 77 a 72 edificios.
- **Cotas**: SIGTIERRAS queda ≈ 1,1 m bajo el DTM de la SGIAR en la costa y 1,6 a 2,9 m sobre él por encima de 30 m. No mezcles umbrales de un relieve con los de otro.

## Ajuste con lo observado el 21-nov-2026 (Puerto Ayora, el escarpe y Bellavista)

La susceptibilidad publicada en `/mapas/` es la HAND **más** un ajuste calibrado con la inundación del 21-nov. Es un **modelo propio ajustado con reportes sin verificar, no una delimitación oficial**. El ajuste solo **sube** de clase y las demás islas no cambian. Lo único que baja son las **correcciones por conocimiento local** (ver abajo).

- **Puntos de control** (`reportes/eventos/2026-11-21/puntos_control.json`): la altura del agua leída a ojo en fotos y videos se pasa a una profundidad con su rango (al pecho ≈ 1,25 m; llega a la primera planta ≈ 2 m; la cubre ≈ 2,75 m; alcanza la segunda planta ≈ 3 m; calle con corriente ≈ 0,3 m; gravedad 3 o 4 sin altura descrita: 0,5 y 1 m). Cota del agua = cota del DTM de la SGIAR + profundidad.
- **La Cascada**: los 8 puntos con altura dan una cota del agua de 15,7 a 18,1 m (mediana ≈ 17,0 m). Es unos 2 m **por encima** del rebose del DTM (15,04 m): el vaso no se quedó en su rebose, rebosó con carga. Llenarlo hasta 17 m cubre ≈ 34 ha (el vaso hasta el rebose son 5,8 ha) y lo desborda hacia el sur, hacia Matazarnos y la calle Seymour. Es la misma ruta que trazó el coordinador. Error en los puntos: el vaso hasta el rebose subestima ≈ 1,9 m; el ajuste, ≈ 0,7 m de media (0,9 m si se deja fuera el propio punto).
- **Corredor observado** (`flujo_observado.geojson`): se calcula la HAND respecto a las líneas por las que se vio bajar el agua, a 40 m como máximo. Sus clases son las de siempre (≤ 1, ≤ 2,5 y ≤ 5 m). Además se llenan las depresiones cerradas del DTM que toca el agua observada. Un ejemplo: el cruce de Seymour, Petrel y Fragata se llena hasta 8,2 m en el DTM, y los reportes dan 7,7–8,4 m.
- **Otros reportes** (Arrayanes, cementerio, escuelas, La Unión, vía a Bellavista): se rellena alrededor del punto, en un radio que depende de su precisión (15–60 m). Alta queda bajo la cota del agua; media hasta 1 m sobre ella; baja hasta 2,5 m sobre ella.
- **Scripts**: `geodatos/scripts/est_21nov_ajuste.py` escribe `estudios/santa-cruz/datos/ajuste_21nov/`; ahí están las hectáreas por clase antes y después y por zona, en `resumen_ajuste.json`. `10_publicar_web.py` lo suma a la capa al publicar. `est_21nov_contraste.py` escribe `contraste_21nov.json`, que compara lo observado con la HAND antes y después del ajuste y con el modelo 2D.
- **Límites**: las profundidades son estimaciones a ojo y las ubicaciones, aproximadas. Es un modelo de topografía, no de hidráulica: no ve muros, casas ni alcantarillas. El «después» se calibró con esos mismos reportes, así que **no es una validación**. Hace falta medir marcas de agua en campo.

### Trazos de un experto local en El Edén

El 22-nov-2026 un experto local dibujó a mano, sobre una imagen satelital (Airbus, 2024), por dónde corrió el agua el 21-nov en El Edén y Matazarnos:
- desde Isla Santiago y Delfín por Seymour hasta Fragata;
- la bajada por Marchena desde el parque, que él mismo marcó con una pregunta;
- los ramales de Fragata hacia el bosque y hacia el mar.

El dibujo se georreferenció con tres canchas que se ven en la imagen y en OSM, con un error estimado de 3 a 5 m, y se convirtió en líneas: `geodatos/estudios/santa-cruz/datos/flujo_experto_eden.geojson`. `est_21nov_ajuste.py` lo suma a las líneas del corredor observado (paso 3b). **No se publica como capa**: solo calibra la susceptibilidad. Suma unas 2,3 ha en alta, 1,1 en media y 0,7 en baja. Está sin verificar en campo.

### Observaciones de campo del barrio Tomás de Berlanga

El 10-nov-2026 la Comisión de Vías y Encañadas del barrio recorrió sus dos encañadas y levantó con GPS cinco puntos críticos. El informe es del 13-nov y el oficio al COE, del 18-nov. Están en `geodatos/estudios/santa-cruz/datos/observaciones_campo_tomas_de_berlanga.geojson`, sin nombres de propietarios ni de personas afectadas. `est_21nov_ajuste.py` los usa como puntos de control, con el mismo llenado local del paso 4.

- En el punto crítico 3 se inundó cerca de 1 ha, con unos 2 m de agua sin medir. Se toma como 2 m, con un rango de 1 a 2,5 m.
- Los demás puntos se toman como «grave sin nivel», 0,5 m.
- Son desbordes del 30-oct, del 2-nov y de 2016, no del 21-nov. La ficha de la capa lo dice.
- El punto crítico 5, en la vía al hotel Tortuga Bay, no tenía susceptibilidad en la HAND: es un hueco del modelo que el barrio sí ve.
- Es información comunitaria sin verificar en campo por SOS Galápagos.

### Correcciones por conocimiento local

En algunas zonas la coordinación de SOS Galápagos sabe que el agua no llega, aunque el modelo marque una quebrada o el ajuste haya rellenado alrededor de un reporte mal ubicado. Allí **se quita** la susceptibilidad publicada, tanto la HAND como el ajuste.

- **Archivo**: `geodatos/estudios/santa-cruz/datos/correcciones_locales.geojson`, redactado a mano. Cada zona lleva su motivo, su fecha y quién lo afirma. Un punto con `radio_m` es un círculo de ese radio. Los bordes se trazan sobre las vías de OSM.
- **Aplicación**: `10_publicar_web.py` (`susceptibilidad_ajustada`) recorta la capa al publicar. No se modifican la HAND ni el ajuste. Si el archivo falta, falla.
- **22-nov-2026, Tomás de Berlanga**:
  - `k01` (**retirada el 23-nov-2026**): borraba la quebrada entre el camino viejo y la vía al hotel Tortuga Bay. El informe de campo del barrio Tomás de Berlanga (recorrido del 10-nov, informe del 13-nov y oficio al COE del 18-nov) la contradice: sus cinco puntos críticos están sobre esa quebrada, cuatro en susceptibilidad alta. En el lindero norte del punto crítico 3 la encañada inundó cerca de 1 ha, con unos 2 m de agua, y hubo que evacuar viviendas. La vía al hotel Tortuga Bay se desbordó en 2016 y el 2-nov-2026. Antes de quitar una quebrada, hay que contrastarla con lo observado en campo.
  - `k02`: el centro del barrio, alrededor de donde estaba el reporte `r31`. El ajuste rellenaba ahí un círculo de 60 m, pero el punto estaba mal ubicado. La inundación que describe `r31` es la de la encañada en el camino viejo, el punto crítico 1 del informe del barrio. Ahí vuelve el área afectada `c07` y ahí entra como punto de control `btb-pc1`.
- **Límite**: es conocimiento local sin verificar en campo. Tampoco es una delimitación oficial.

## Límites (decirlos siempre que se muestre el mapa)

1. **Fuera de Santa Cruz, el DEM es de superficie (DSM)**: incluye techos y copas de árboles. En la ciudad y el bosque la cota está sesgada; frente al IGM hay un sesgo de −2 a −3 m. No usar cotas absolutas como umbrales normativos.
2. **30 m de resolución** (en Santa Cruz, 10 m con SIGTIERRAS y 5 m en la cobertura del DTM): no ve alcantarillas ni pasos bajo vías; a 30 m tampoco cauces estrechos.
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
