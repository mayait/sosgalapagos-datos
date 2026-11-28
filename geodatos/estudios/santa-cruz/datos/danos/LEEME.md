# Daños vistos en las ortofotos de dron del GAD de Santa Cruz

Inventario de lo que dejaron las lluvias de octubre y noviembre de 2026 entre Bellavista y La Cascada, marcado a mano sobre las ortofotos de dron del **GAD Municipal de Santa Cruz** (3 al 22-nov-2026, CC BY 4.0).

| Archivo | Qué es | Cómo se hace |
|---|---|---|
| `bloques_recorridos.txt` | Los 220 bloques de 240 m recorridos: tienen foto y edificios del mapa, o una cañada del GAD o un flujo observado a 40 m o menos | `44_danos_observados.py bloques` |
| `danos_bloques.csv` | Los 26 bloques con daño visible | A mano, sobre las hojas de bloques |
| `danos_marcas.csv` | Cada daño: bloque, celda de 80 m (1-9), subcelda de 27 m (a-i), `tipo`, `gravedad` (aparente: alta, media o baja), `descripcion` y `marcado_por` | A mano, sobre las hojas de detalle (`44_danos_observados.py celdas`) |
| `danos_observados.geojson` | Un punto por daño, en el centro de su subcelda (±15 m), con la clase HAND y la distancia al cauce más cercano | `44_danos_observados.py capa` |
| `resumen.json` | Recuentos por tipo, gravedad, clase HAND y distancia al cauce | Ídem |

Las hojas para marcar quedan en `estudios/santa-cruz/figuras/danos/`, solo en local. La cuadrícula tiene un origen fijo (UTM 15S, E 796 000, N 9 917 000): los id de los bloques no cambian.

**Infraestructura (28-nov-2026).** Además del recorrido, se buscaron objetos lineales azules (tuberías de PVC) con un filtro de color y forma a 5–9 cm por píxel, a 30 m o menos de vías y cauces: salieron 23 candidatos. Se revisaron uno por uno con zoom, junto con los cruces de cauces con vías y los puntos de daño junto a carreteras. Casi todos los candidatos eran techos, lonas o mallas; quedaron 12 daños en infraestructura, ubicados con ±3 m (columnas `x_utm` y `y_utm`):
- **Tuberías rotas (2):** tuberías azules de agua arrancadas y arrastradas junto a la Troncal en la Curva Brava, al lado de un poste caído, y restos de tubería entre los escombros de un flujo en Bellavista.
- **Tuberías expuestas (4):** al descubierto sobre el lodo o a lo largo de cárcavas en Bellavista y Tomas de Berlanga. Una es dudosa.
- **Postes caídos o inclinados (2):** en la Curva Brava.
- **Bordes de vía rotos o socavados (4):** Av. Padre Julio Herrera (socavón en el borde), Troncal Insular y la berma de la Curva Brava.

Sirven para avisar a la empresa de agua, a la eléctrica y a obras públicas. **El filtro solo ve tuberías azules a la vista**: no ve las enterradas ni las negras o grises, que se confunden con el suelo. Falta la red de agua potable de Santa Cruz para cruzarla con los cauces.

**Posición.** Las ortofotos del GAD están corridas de 1,4 a 5 m (sobre todo hacia el norte), medido contra el DSM de la SGIAR por la sesión de `45_edificios_ortofotos.py`. `44 capa` y `43` corrigen cada punto con `datos/gad_santa_cruz/registro_ortofotos.json` si existe. Mientras ese archivo no esté en `main`, las posiciones quedan sin corregir (campo `posicion_corregida`).

**Tipos:** `escombros`, `lodo_sedimento`, `erosion` (cárcavas y cauces lavados), `rocas_arrastradas`, `vegetacion_tumbada`, `vivienda_destruida`, `vivienda_danada`, `via_danada`, `muro_caido` y, de infraestructura, `tuberia_rota`, `tuberia_expuesta`, `poste_caido`, `cerca_caida` y `estructura_arrastrada`.

## Primera pasada (28-nov-2026)

- **142 daños** en 26 bloques: 65 de lodo y sedimento, 38 de erosión, 22 de escombros, 14 de vegetación arrasada y 3 de rocas arrastradas. 55 son de gravedad aparente alta.
- **27 a 30 m o menos de un edificio** del mapa, 14 de ellos de gravedad alta.
- **Dónde caen.** El 87 % está a 50 m o menos de un cauce (drenaje derivado o cañada del GAD); la mediana es de 11 m. Pero **54 de 142 (38 %) quedan fuera de toda clase de susceptibilidad HAND**. El daño sigue a los cauces, pero sube por encima de los 5 m de altura sobre el cauce que marca la clase baja. Eso calza con flujos de lodo y escombros con energía, que el HAND, como índice de posición, no representa.
- **Zonas con más daño:** el sur de Bellavista y el camino a Tomas de Berlanga (cárcavas y abanicos de sedimento entre casas), la franja arrasada al este de Mira Mar, la Curva Brava (lodo y escombros en la berma), el flujo de escombros del cauce sobre La Cascada y la cicatriz del escarpe sobre las casas.

## Límites

- **No es una muestra al azar.** Es un recorrido dirigido. Sirve como capa de lo observado y para ver dónde cayó el daño, no para calcular tasas de acierto; para eso está la muestra de `../validacion/`.
- **La fecha del daño no es exacta.** Las ortofotos van del 3 al 22-nov y el daño puede venir del 30-oct, el 2-nov o el 21-nov.
- **Bajo el bosque cerrado y los techos no se ve el suelo.** Faltan daños dentro de las casas y bajo copas.
- **Gravedad aparente**, a ojo sobre la foto. Por confirmar en campo.
- **Algunos daños pueden no ser del evento:** obras, lotes en limpieza o quemas.
- **Pasada de Claude.** Hay que confirmarla con alguien que conozca la zona; quien revise agrega filas con su propio `marcado_por`.
