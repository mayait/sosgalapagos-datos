[[SALTO]]

# 5. ¿Es posible desviar las quebradas?

## 5.1 Planteamiento

Desviar las quebradas consiste en **interceptar la escorrentía antes de que llegue al barrio** y conducirla **por gravedad** hasta el mar por una ruta que no atraviese zonas pobladas. Se buscaron corredores con estas condiciones: pendiente de rasante ≥ 0,5 %, corte ≤ 3 m (o 6 m), terraplén ≤ 1 m y un margen de 30 m respecto de las zonas pobladas. Las tomas se probaron en cotas de 20 a 120 m, en ambas ramas y hacia el este, el oeste y el frente urbano. De 24 combinaciones de toma y corte salieron 34 trazados con salida al mar.

**Resultado general.** Con tomas a 20–30 m no existe salida al mar sin cruzar zonas pobladas. A partir de unos 40 m (30 m si se admiten cortes de hasta 6 m) aparece un corredor hacia el este. Hacia el oeste solo hay salida desde 80 m o más.

## 5.2 Evaluación por criterios

Tabla: Viabilidad del desvío por criterios.

| Criterio | Este (toma en la rama 2 a ≈40 m) | Oeste (mejor variante) |
|---|---|---|
| C1. Continuidad por gravedad (≥ 0,5 %, corte ≤ 3 m) | Sí: 3,5 km, corte máximo de 2,9 m (medio de 0,9 m). Llega al mar en −90,2992; −0,7435 | Solo con tomas a ≥ 80 m: 10,5 km (rama 1, a 120 m) o 6,0 km (rama 2, a 80 m) |
| C2. Área captada (≥ 90 %) | 41,9 km² (99 %) | 35,4 km² (84 %) o 11,3 km² (27 %) |
| C3. Sin zonas pobladas ni vías | 0 vías; el edificio más cercano está a 143 m | Cruza la Av. Padre Julio Herrera; edificios a 50–62 m |
| C4. Margen frente al error del DSM | **No se cumple**: en los primeros 2,5 km el terreno baja de 41,6 a 28,9 m (≈ 0,5 %, con contrapendientes), dentro del error de ±2 m. Además, el trazado se calculó como una rasante. Como canal real de 2,5–3 m de profundidad, iría **en terraplén en 3,1–3,5 km de sus 3,5 km**: más de 2 m de altura en 1,8–2,2 km y hasta 3,5–4 m como máximo, sobre el borde del escarpe y encima del barrio. Ese terraplén supone un riesgo de rotura. La alternativa sería excavar de media 3,1–3,6 m (máximo 5,4–5,9 m) en basalto | Pendiente mayor, pero longitud triple |
| C5. Capacidad hidráulica | Para 100 mm y CN 70, un canal de 8–16 m de base con 2,5 m de calado; ≈17–25 m de base para 150–230 m³/s (evento modelado con ECMWF de 9 km). La excavación real es el corte sobre la rasante más el calado y el resguardo | Igual o mayor, en 10 km |
| C6. Marco legal y ambiental | 100 % en el Parque Nacional (1,8 km en zona de Transición y 1,7 km en Aprovechamiento sustentable). Desemboca en la Reserva Marina, cerca de la Estación Charles Darwin / DPNG | 100 % en el Parque Nacional |
| **Valoración** | **No descartable, pero no demostrado.** Depende de C4 y C6 | **No viable**: capta poco o exige más de 10 km de obra |

![Perfil del interceptor hipotético hacia el este: terreno según el DSM, rasante con pendiente ≥ 0,5 % (sin calado) y corte sobre la rasante.](figuras/f_perfil_interceptor.png)

![Vista 3D de la cuenca aportante (exageración vertical ≈3,5×), con el barrio y el interceptor hipotético hacia el este, sobre el borde del escarpe (≈40 m).](figuras/f3d_cuenca.png)

## 5.3 ¿Existe ya un cauce hacia el este?

OSM dibuja un cauce intermitente de 4,1 km al pie del escarpe que pasa junto al borde norte del barrio y sigue hacia el ESE. Se verificó con detalle porque, si fuera real, **recuperarlo** sería preferible a abrir un canal nuevo. Los hallazgos son cuatro:
- **Fuente.** El cauce es **solo de OSM** (vía 737164765, `waterway=stream`, `intermittent=yes`), sin nombre ni fuente. El IGM 1:25 000 no cartografía ningún cauce en ese lugar.
- **Perfil.** Es coherente en los primeros 480 m. Después, el mínimo de una franja de ±90 m **sube en cuatro umbrales**, a 18,8, 17,8, 21,2 y 33,0 m. El extremo oriental está a unos 40 m de cota y a 370–410 m de la costa: **el trazado no llega al mar**. Para recorrerlo entero, el agua tendría que subir hasta unos 37 m, frente a los 12,95 m del rebose del barrio.
- **Posición.** El trazado está dibujado, en mediana, 4,6 m ladera arriba del fondo, siempre del lado del escarpe.
- **Causa de los umbrales.** No hay vías ni edificios cerca. La vegetación podría explicar parte de los dos primeros umbrales, pero no el ascenso del último kilómetro, que un punto acotado del IGM de 47 m confirma como relieve real.

![Perfil a lo largo del cauce dibujado en OSM hacia el este. Si el umbral acumulado supera la cota de rebose del barrio (≈13 m), el agua no puede seguir ese trazado sin excavación.](figuras/f_perfil_cauce_este.png)

**Valoración.** Tal como está dibujado, el cauce de OSM no es hidráulicamente coherente con el relieve más allá de 1 km al este del barrio. Si existió un drenaje histórico hacia el este, el candidato coherente es el **fondo de la fosa tectónica**, 100–300 m al sur del trazado de OSM, por donde va la rama este del rebose (sección 4.5). Ese fondo está hoy urbanizado en un 76 %. En ese caso, «recuperar el cauce» significaría abrir un **corredor urbano** con afectación de predios, no reabrir un canal en el Parque.

La confianza en esta hipótesis es **baja**. Para confirmarla o descartarla se necesitan:
- el historial de edición de OSM;
- fotografías aéreas históricas del IGM;
- un vuelo de dron de 2 km² al pie del escarpe;
- una inspección de campo que busque lecho, depósitos o marcas de flujo;
- testimonios de los vecinos más antiguos.

## 5.4 Respuesta a la pregunta

> **Topográficamente, desviar las quebradas hacia el este no es descartable, pero no está demostrado. No es una medida de emergencia y no resuelve el problema por sí solo.**
>
> - **El corredor.** Un interceptor a unos 40 m, justo sobre el escarpe, captaría el 99 % de la cuenca y bajaría 3,5 km por gravedad hasta el mar sin cruzar vías ni viviendas. Pero en sus primeros 2,5 km la pendiente es del mismo orden que el error del modelo de elevación. Solo un levantamiento con dron o LiDAR puede confirmar si existe.
> - **El encaje legal y ambiental.** La obra iría íntegramente dentro del Parque Nacional y desembocaría en la Reserva Marina, cerca de la Estación Charles Darwin. Requeriría autorización de la DPNG, licencia ambiental del MAATE y un estudio de impacto, además de un canal de 8–16 m de base excavado en basalto. Como canal real tendría que ir excavado de media más de 3 m en basalto o en terraplén alto sobre el escarpe. Es una obra de años, no de semanas.
> - **Lo que el desvío no resuelve.** No actúa sobre la escorrentía local (0,6 km²) ni sobre la falta de salida urbana. Tampoco están resueltos el cruce de la rama 1 ni la disipación de energía en el último kilómetro, donde el canal baja unos 29 m hasta el mar. Además, su eficacia está limitada por la lluvia de diseño, que hoy se desconoce.
> - **Hacia el oeste no es viable.**
>
> El desvío debe tratarse como **una alternativa más** dentro de un estudio de alternativas, que se compara con la mejora de la salida urbana, la laminación y la relocalización (sección 8).
