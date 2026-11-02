[[SALTO]]

# 5. Cruces de quebradas con vías

> **TOTALMENTE PRELIMINAR.** Es un inventario de gabinete, hecho con un modelo de superficie de 30 m y cartografía abierta, para priorizar inspecciones de campo. **En San Cristóbal no hay lluvia medida del evento**: los caudales corresponden a un escenario de 100 mm.

## 5.1 Método

El método es el mismo que en Santa Cruz (`scripts/16_cruces_quebradas_vias.py`):

- **Vías:** todas las de OSM (557 tramos, 31-oct-2026) y la red vial del IGM 1:25 000 (739 tramos).
- **Cauces:** las quebradas del IGM 1:25 000 y de OSM, y los cauces D8 derivados del DSM GLO-30 con al menos 0,1 km² de área drenada.
- **Deduplicación:** las intersecciones a menos de 40 m se fusionan en un solo cruce. En cada cruce se conserva la vía de mayor jerarquía de OSM.
- **Caudal:** método racional modificado de Témez.
  - El tiempo de concentración se calcula a partir del cauce más largo aguas arriba según el D8.
  - La intensidad I(tc) sale de la curva de intensidad máxima por duración medida el 30-oct en Los Guayabillos (Santa Cruz), escalada a 100 mm. Esto **supone que la tormenta tiene la misma estructura temporal**, un supuesto que no está verificado en San Cristóbal.
  - El coeficiente C es el volumétrico del SCS con CN 60, 70 u 80 (0,19 / 0,33 / 0,51).
- **Prioridad:** puntaje de 0 a 11 con los mismos criterios que en Santa Cruz, que se resumen en la tabla siguiente. Aquí la vía principal es la terciaria de OSM, porque la isla no tiene vías clasificadas como `primary`.

Tabla: Criterios de prioridad de los cruces.

| Criterio | Puntos |
|---|---|
| Área drenada | ≥ 5 km²: 2 · 0,5–5 km²: 1 · < 0,5 km²: 0 |
| Q100 central (CN 70) | ≥ 50 m³/s: 3 · 10–50: 2 · 2–10: 1 · < 2: 0 |
| Tipo de vía | Principal o urbana: 2 · rural: 1 · peatonal: 0 |
| Estructura | Ninguna cartografiada: 1 · puente, alcantarilla o vado: 0 |
| Zona poblada | Dentro: 2 · fuera: 0 |
| **Clase** | **Alta ≥ 7 · media 4–6 · baja ≤ 3** |

**Resultado: 721 intersecciones que quedan en 325 cruces**, con esta prioridad:

- 25 de prioridad alta: 23 en la zona poblada de Puerto Baquerizo Moreno, 1 en Cerro Verde y 1 en la Vía Puerto Baquerizo Moreno–El Progreso, fuera de la zona poblada;
- 147 de prioridad media;
- 153 de prioridad baja.

Hay más cartografía que en Santa Cruz: 123 cruces tocan una quebrada del IGM o de OSM, y **11 cruces tienen una estructura cartografiada**:
- 7 puentes del IGM;
- 2 puentes de OSM (Av. de la Armada Nacional y Av. Jaime Roldós / Vía Perimetral);
- 2 alcantarillas de OSM (en la calle Azogues y en un tramo sin nombre).

## 5.2 Los puntos más prioritarios

Los cruces de un mismo cauce que están juntos se agruparon; el detalle de cada uno está en `datos/cruces.csv`. Se propone una correspondencia con los nombres locales de las encañadas, siguiendo la sección 7, como hipótesis por verificar.

Tabla: Los grupos de cruces más prioritarios de San Cristóbal. Q100 en m³/s (central, CN 70; rango CN 60–80 en el CSV).

| # | Cruce (n.º en el grupo) | Cauce (hipótesis) | Vías | Área (km²) | Q100 | Estructura | Edificios a ≤ 50 m (suma) | Cota* (m) |
|---|---|---|---|---|---|---|---|---|
| 1 | CR-SCR-0001 (4) | Barrio Frío, tramo bajo | Av. de la Armada Nacional, Colón, Av. Alsacio Northia | 10,4–11,0 | 27–28 | 2 puentes IGM y 1 puente OSM; un cruce sin estructura | 65 | 2–14 |
| 2 | CR-SCR-0002 (5) | Barrio Frío, tramo medio / El Manzanillo | Azogues, Av. Jaime Roldós Aguilera / Vía Perimetral | 9,3–9,7 | 25 | 1 alcantarilla y 1 puente OSM; el resto sin estructura | 53 | 16–45 |
| 3 | CR-SCR-0005 (2) | El Manzanillo, tramo alto | Calles sin nombre | 8,4–8,7 | 23–24 | Ninguna | 34 | 60–64 |
| 4 | CR-SCR-0012 (3) | Afluente de El Manzanillo | **Vía Puerto Baquerizo Moreno–El Progreso** | 6,5–6,6 | 18 | Ninguna | 13 | 69–72 |
| 5 | CR-SCR-0013 (4) | Divino Niño | Manuel Agama, Av. Alsacio Northia, Vía Playa de Oro, Av. Jaime Roldós | 1,5 | 5 | Ninguna | 53 | 6–15 |
| 6 | CR-SCR-0015 | Afluente alto | Calle sin nombre | 1,6 | 5 | Ninguna | 10 | 86 |
| 7 | CR-SCR-0018 | Divino Niño, tramo alto | Calle sin nombre | 1,4 | 5 | Ninguna | 9 | 24 |
| 8 | CR-SCR-0019 (2) | Afluente urbano | Calles sin nombre | 1,0 | 3 | Ninguna | 37 | 31–35 |
| 9 | CR-SCR-0021 (2) | Afluente de Barrio Frío | Calles sin nombre | 0,7 | 2 | Ninguna | 7 | 15–18 |
| 10 | CR-SCR-0024 (2) | Escuela Alvear | Av. Alsacio Northia, Av. Jaime Roldós | 0,7 | 2 | Ninguna | 20 | 10 |
| 11 | CR-SCR-0026 (2) | Barrio Frío, desembocadura | Av. Charles Darwin, Av. Quito | 10,6–10,8 | 27 | Puente IGM | 20 | 4–5 |
| 12 | CR-SCR-0028 (5) | El Manzanillo, borde urbano | Vía Perimetral y caminos | 9,0–9,4 | 25 | Un puente IGM; el resto sin estructura | 0 | 46–54 |
| 13 | CR-SCR-0023 | Cerro Verde | Calle sin nombre | 0,7 | 2 | Ninguna | 4 | 211 |
| 14 | CR-SCR-0033 | Ladera sur | Camino rural | 7,1 | 21 | Ninguna | 0 | 92 |
| 15 | CR-SCR-0037 (2) | Cerro Verde | Camino rural | 6,0–6,2 | 16 | Ninguna | 0 | 148–166 |

\* Cota del DSM: ±2–4 m, con un sesgo de unos −2 m frente al IGM; solo es descriptiva.

**Lectura:**

- **La encañada de Barrio Frío (≈10,5–11 km²) es la que más cruces de alto caudal tiene.** Es también la que tiene más estructuras cartografiadas: puentes en Colón, la Av. Alsacio Northia y la Av. Charles Darwin. Hay que verificar la **sección** de esas estructuras frente a un Q100 del orden de 25–40 m³/s.
- **La Vía Puerto Baquerizo Moreno–El Progreso** cruza un afluente de 6,5 km² (Q100 ≈ 18 m³/s) sin estructura cartografiada. Es la conexión con la parte alta.
- **Divino Niño y Escuela Alvear** son cauces pequeños (0,7–1,6 km²; 2–5 m³/s), pero atraviesan zonas muy edificadas: unos 50 edificios a menos de 50 m. Ninguno de sus cruces tiene una estructura cartografiada.
- **El cauce que pasa junto al campus de la USFQ** (0,3 km²; cruces CR-SCR-0218 en la Vía Universidad y CR-SCR-0222) queda en prioridad baja por su tamaño. Se trata en la sección 6.

## 5.3 Limitaciones

Son las mismas que en Santa Cruz:

- el D8 se desplaza en las zonas llanas y edificadas;
- **«ninguna estructura cartografiada» no quiere decir que no haya alcantarilla**;
- los caudales no tienen en cuenta la reducción areal, la laminación ni la infiltración.

A eso se suma que **la lluvia de diseño se trasladó desde Santa Cruz**. Para San Cristóbal hace falta medir la lluvia en la parte alta (El Junco y El Progreso) y en el puerto.

**Archivos:**
- `datos/cruces.geojson` y `datos/cruces.csv`.
- Se generan con `scripts/16_cruces_quebradas_vias.py`.
