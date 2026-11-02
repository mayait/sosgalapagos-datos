# Modelo hidrodinámico 2D del 30 de octubre

> **Resultado preliminar en revisión.** Esta es la primera corrida, con el escenario central y una malla de 30 m. Están en curso la validación con días de lluvia sin inundación reportada, la sensibilidad a la rugosidad y a la lluvia, y un segundo juego de parámetros de infiltración. El texto completo sustituirá a este resumen.

**Qué es.** Es un modelo de inundación **bidimensional distribuido** («rain-on-grid»): la lluvia medida cae sobre cada celda del terreno, una parte se infiltra y el resto escurre siguiendo las ecuaciones de aguas someras simplificadas (esquema inercial local de Bates et al., 2010, el de LISFLOOD-FP). Abarca 52 km² y unas 58 000 celdas, desde la parte alta hasta el mar, incluidos Tomás de Berlanga y Puerto Ayora. La lluvia es la medida en Los Guayabillos (179 mm), con infiltración SCS-CN distribuida y el mar a +0,75 m. Como contraste se está corriendo también ANUGA (volúmenes finitos).

**Primeros resultados (escenario central):**
- **La Cascada.**
  - El agua llega al punto más bajo (0,1 m) hacia las **15:36** y al centro del barrio hacia las **20:37**.
  - El nivel máximo, de 15,3 m de cota en el DSM, se alcanza hacia las **22:08**. Eso supone ≈2,4 m de agua en el centro del barrio, compatible con el testimonio de «hasta dos metros», y hasta 4,6 m en el punto más bajo.
  - Caudal de entrada al barrio: **≈358 m³/s hacia las 21:57**, con 3,2 hm³ de volumen.
- **Hacia el mar.** La salida alcanza ≈417 m³/s hacia las 22:23. El vaso de Matazarnos llega a ≈3,9 m y el cruce de la Av. Charles Darwin a ≈2 m.
- **Tomás de Berlanga.** El cauce lleva ≈0,5 m desde las 18:57. La escuela queda seca con esta resolución.
- **Bellavista centro:** ≈0,7 m.

![Calado máximo del modelo 2D el 30 de octubre (escenario central, malla de 30 m).](figuras/m2d_calado_max_central.png)

![Hora de llegada del agua (calado ≥ 0,1 m) según el modelo 2D.](figuras/m2d_hora_llegada_central.png)

![Animación de la inundación del 30 de octubre según el modelo 2D (cada 10 minutos).](figuras/anim_30oct_central.gif)
