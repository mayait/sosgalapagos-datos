[[SALTO]]

# 4c. Floreana: conexión de cañadas para proteger Playa Negra (exploratorio)

> **EXPLORATORIO Y DE CONFIANZA BAJA.** Solo se usa el DSM GLO-30 (30 m; ±2–4 m). En Floreana no hay cartografía del IGM ni de OSM de las cañadas «La Hormiga» y «La Varonesa / Lobería», **así que este análisis no asigna nombres**: describe los cauces del DSM y evalúa si una conexión de ≈500 m tiene sentido topográfico. Se reproduce con `scripts/28_floreana_canadas.py`; los datos están en `datos/floreana/`.

**Qué propone el plan.** El Plan de Acción SC-4-09-2026 de la UGR del GAD San Cristóbal [R] indica que las dos cañadas de Floreana (Hormiga y Varonesa) «deben conectarse con 500 m de excavación para proteger Playa Negra».

**Qué muestra el DSM.** Tres cauces D8 llegan a la costa del poblado.

Tabla: Cauces D8 que llegan al mar cerca de Puerto Velasco Ibarra (área en la desembocadura).

| Cauce | Desembocadura | Área (km²) | Distancia a Playa Negra |
|---|---|---|---|
| Central | **Playa Negra** (−1,2765; −90,4883), frente al poblado | 2,07 | 0 m |
| Norte | (−1,2703; −90,4891) | 1,75 | 690 m al norte |
| Sur | (−1,2825; −90,4902), hacia Playa Prieta / La Lobería | 4,23 | 690 m al sur |

Para proteger Playa Negra hay que desviar el cauce central hacia uno de los otros dos.

Tabla: Mejores conexiones rectas de ≤ 550 m desde el cauce central, con pendiente ≥ 0,5 % y corte ≤ 3 m bajo una rasante recta.

| Hacia | Toma (cota*) | Longitud | Desnivel | Pendiente | Corte máx. | Cuenca desviada |
|---|---|---|---|---|---|---|
| **Norte** | (−1,2782; −90,4770), ≈68–72 m* | 240–270 m | 1,3–5,1 m | 0,5–1,9 % | ≤ 1,1 m | **1,18 km² (57 %)** |
| **Sur** | (−1,2901; −90,4670), ≈199 m* | 120–180 m | ≈1,2 m | 0,7–1,0 % | ≤ 1,6 m | **0,09 km² (4 %)** |

**Lectura**
- **Hacia el norte, la conexión es topográficamente coherente.** Un canal de 250–300 m, a unos 1,3 km de la costa, desviaría algo más de la mitad de la cuenca de Playa Negra con pendiente suficiente y cortes pequeños. Con 500 m hay margen para elegir el trazado. Pero el desnivel (1,3–5 m) es del orden del error del DSM, y el agua iría a parar a la costa 690 m al norte: **hay que verificar qué hay en ese cauce y en su desembocadura**.
- **Hacia el sur (La Lobería), una conexión de 500 m no es coherente.** Solo es posible en la cabecera, donde desviaría el 4 % de la cuenca. Para desviar la mayor parte haría falta un canal más largo o cortes mayores.
- En ambos casos, el 40–45 % inferior de la cuenca y la escorrentía del propio poblado seguirían llegando a Playa Negra.

**Para concluir hace falta:**
- saber cuál de estos cauces es cada cañada del plan. «La Baronesa» aparece en OSM como calle y restaurante del poblado, entre el cauce central y el norte;
- un levantamiento GNSS del trazado propuesto;
- el destino aguas abajo del agua desviada.

Hasta entonces, la conclusión es **condicional**: hacia el norte es plausible; hacia el sur, no con 500 m.
