[[SALTO]]

# 3. Lluvias del 15 de octubre al 1 de noviembre de 2026

En esta sección se distinguen tres tipos de información que no deben mezclarse: **[M] medido** (pluviómetros, temperatura del mar), **[E] estimado** (modelos numéricos y reanálisis) y **[R] reportado** (informes oficiales y prensa). Todas las fuentes se consultaron el 2 de noviembre de 2026.

> **No existe ningún dato medido de lluvia del evento que sea público.** La estación de la Fundación Charles Darwin (FCD) en Puerto Ayora, con 61 años de serie, publica datos solo hasta el 3 de junio de 2026. La serie de Bellavista termina en 2019. El portal de estaciones del INAMHI no respondió (HTTP 500). Todas las cifras de lluvia de 2026 de este informe son **estimaciones de modelo**.

## 3.1 Estimación del evento

La mejor estimación disponible es la del modelo ECMWF IFS HRES, con una malla de unos 9 km, obtenida a través de Open-Meteo: es la concatenación de los primeros plazos de sus corridas. Los modelos con mallas de unos 10 km o más no resuelven bien la isla y, para el mismo día, dan entre 0,2 y 26 mm (tabla siguiente).

Tabla: Lluvia estimada por fuente (mm). El 31-oct se da en día natural de Galápagos (UTC−6), recalculado a partir de los datos horarios. El total se da en UTC−5, como se descargó, lo que cambia poco el resultado. Las celdas de la malla están en `datos/lluvias/celdas_modelos.csv`.

| Fuente (malla) | 28–30 oct | **31 oct (UTC−6)** | 1 nov | Total 15-oct–1-nov | Máx. 1 h | Máx. 6 h |
|---|---|---|---|---|---|---|
| ECMWF IFS 9 km, celda costera (3,5 km al E del pueblo) | 20,5 | **81,1** | 27,7 | **≈187** | 23,2 | 64,7 |
| ECMWF IFS 9 km, celda de la parte alta (NO de Bellavista) | 51,1 | **129,8** | 26,5 | **≈259** | 32,5 | 110,4 |
| Météo-France seamless | — | 26,2 | — | 63,7 | 3,1 | 13,1 |
| ECMWF IFS 0,25° | — | 24,3 | — | 50,3 | 4,3 | 15,3 |
| UKMO seamless (Puerto Ayora) | — | 22,4 | — | 53,5 | 2,2 | 8,8 |
| NOAA GFS seamless (Puerto Ayora) | — | 13,5 | — | 62,5 | 1,9 | 8,6 |
| DWD ICON seamless | — | 8,7 | — | 26,7 | 1,2 | 5,0 |
| JMA seamless | — | 4,2 | — | 23,3 | 1,0 | 6,0 |
| ERA5 (reanálisis 0,25°) | — | — | — | 16,5* | — | — |

*\*Solo del 15 al 26 de octubre, por la latencia del reanálisis. Los modelos de malla gruesa ponen celdas distintas en Puerto Ayora y en la parte alta; el rango completo del 31-oct es de 0,2 a 26 mm. ERA5-Land no tiene datos sobre la isla. GPM IMERG requiere una cuenta de NASA Earthdata, que no se tenía.*

Según ECMWF de 9 km, el núcleo del evento ocurrió **entre la medianoche y las 06:00 del 31 de octubre (hora de Galápagos, UTC−6)** y su intensidad creció hasta un máximo **hacia las 05:00–06:00**: 23 mm/h en la costa y 33 mm/h en la parte alta (véase el hietograma más abajo). Antes, entre las 11:00 y la medianoche del 30 de octubre, la parte alta ya había acumulado unos 30 mm, lo que probablemente humedeció el suelo. El 1 de noviembre hubo un nuevo pulso de unos 20 mm entre las 06:00 y las 10:00.

**La cronología modelada no coincide del todo con la reportada.** La prensa sitúa la lluvia entre las 22:00 del 30 y las 06:00 del 31, sin indicar el huso horario (probablemente la hora continental). La SNGR habla de «fuertes precipitaciones registradas durante la tarde y noche del 30/10/2026», y el cantón declaró la emergencia ese mismo día 30. ECMWF, en cambio, sitúa el máximo en la madrugada del 31. Esta discrepancia horaria es otra razón para no tomar el modelo como medida.

> **ECMWF de 9 km es un valor alto aislado.** Para el mismo día, los demás modelos dan entre 0,2 y 26 mm, de 3 a más de 10 veces menos. Ningún modelo está validado en la isla. Por eso la lluvia del evento es la variable más incierta de todo el análisis: va de menos de 1 a unos 130 mm según la fuente. La sección 4 trabaja con los dos extremos.

![Lluvia diaria estimada por modelos en la costa y la parte alta (izquierda) y climatología mensual medida en las estaciones de la FCD (Puerto Ayora 1991–2020, Bellavista 1991–2019) (derecha). Días en UTC−5. Las barras corresponden a ECMWF IFS de 9 km; las líneas verticales, al rango de otros seis modelos y ERA5.](figuras/f_lluvias.png)

![Hietograma horario e intensidad acumulada estimados por ECMWF IFS (9 km) del 30-oct 12:00 al 1-nov 12:00, en las celdas costera y de la parte alta.](figuras/f_lluvia_horaria.png)

## 3.2 Comparación con la climatología medida [M]

Octubre y noviembre pertenecen a la estación fría o de garúa. La media 1991–2020 de la estación Charles Darwin es de **10,9 mm en octubre** y 14,5 mm en noviembre. En Bellavista, de 63,7 y 75,9 mm.

El día más lluvioso de octubre o noviembre registrado en Puerto Ayora desde 1965 fue de **104,3 mm** (2 de octubre de 2023, durante El Niño 2023). En Bellavista, de **59,5 mm** (16 de noviembre de 1997).

Si la estimación del modelo fuera correcta, el 31 de octubre de 2026 habría llovido en la costa unas **7,4 veces la media de todo octubre**. En la parte alta habría caído más del doble del máximo diario de octubre o noviembre registrado en Bellavista.

Tabla: Lluvia en Puerto Ayora (estación Charles Darwin) durante los Niños de referencia (mm) [M].

| Mes | Oct | Nov | Dic | Ene | Feb | Mar | Abr | May | Jun | Total oct–jun |
|---|---|---|---|---|---|---|---|---|---|---|
| 1982–83 | 8,9 | 34,7 | 508,6 | 315,9 | 91,9 | 298,9 | 434,2 | 660,2 | 635,5 | **2 988,8** |
| 1997–98 | 7,9 | 146,9 | 317,5 | 396,6 | 320,1 | 244,0 | 448,4 | 245,4 | — | **2 180,5** |

En ambos Niños fuertes, **octubre fue seco** y la lluvia extrema empezó en noviembre o diciembre y duró hasta mayo o junio. El ERFEN señala la semejanza oceánica de 2026 con 1997–98. Por analogía, que no es un pronóstico, el evento del 30–31 de octubre **podría ser un adelanto de la temporada y no su pico**. Además, la advertencia n.º 85 del INAMHI (1 al 4 de noviembre) ya preveía «eventos muy fuertes en gran parte de las islas». Esto pesa al ordenar las medidas en el tiempo.

## 3.3 Contexto oceánico [M]

- **Temperatura del mar.** Durante octubre, al sur de Santa Cruz, estuvo entre 26,7 y 28,2 °C, con una anomalía de **+4,7 a +5,9 °C** (NOAA OISST v2.1). En la semana del 28 de octubre, la región Niño 1+2 marcó +5,4 °C y la Niño 3.4, +3,4 °C (NOAA CPC).
- **Declaraciones oficiales.**
  - El ERFEN declaró El Niño el 28 de agosto de 2026. La SNGR declaró la alerta roja nacional el 29 de agosto y la naranja para Santa Cruz desde el 20 de julio (Resolución SNGR-193-2026).
  - La NOAA da un **83 % de probabilidad** de un evento «histórico» (RONI ≥ +2,5 °C) entre octubre y diciembre.
- **Advertencias del INAMHI.** La advertencia n.º 84 (29-oct a 1-nov) preveía «eventos leves en el archipiélago y de puntual alta intensidad en Isla Isabela». La alerta roja de corto plazo (n.º 59, vigente desde el 31-oct a las 15:00, en hora probablemente continental) se emitió **después** del evento.

## 3.4 Afectación reportada [R]

- **SNGR, SitRep n.º 01 de Galápagos (corte: 31 de octubre a las 15:30).** Describe el «desbordamiento de varias cañadas». Registra 1 fallecido (en Bellavista), 175 personas afectadas y 165 en refugios. Unas 700 personas salieron por sus propios medios a casas de familias acogientes. Hubo daños en la UPC y en el edificio de la DINAF del **sector La Cascada** y en el Centro de Salud Santa Cruz.
- **SNGR, SitRep 67 nacional (1 de noviembre).** Da 3 120 personas y 780 familias afectadas en la provincia, pero en el texto dice «60 familias»: es una incoherencia interna del propio informe.
- **Prensa.** Un testigo habló de agua «hasta dos metros» junto a la quebrada de La Cascada, y otros de agua «sobre la cintura» en La Unión. La alcaldía habló de unas «2 000 personas» o «2 000 familias» afectadas, con la unidad ambigua según el medio.

> **Corrección de datos de partida.** Las cifras de «3 m de agua» y «800 familias en La Cascada» con las que se inició este análisis **no tienen una fuente verificable**. El «800» podría venir de las 780 familias de la provincia o de los 800 kits enviados por la SNGR. En este informe la lámina del evento se toma como «1,5–2 m, por validar», y la población expuesta se estima con los datos del INEC (sección 6).

## 3.5 Limitaciones y cómo cerrarlas

Los modelos y satélites **subestiman la lluvia convectiva y orográfica en islas pequeñas**. Incluso el modelo de 9 km suaviza un relieve de 0 a 860 m. Tampoco se ha validado aquí y es una única realización determinista.

Para cerrar estas brechas:
1. pedir a la FCD (datazone@fcdarwin.org.ec) y al INAMHI la lluvia diaria y horaria del 15 de octubre al 2 de noviembre;
2. descargar GPM IMERG Early/Late de 30 min con una cuenta gratuita de NASA Earthdata;
3. recoger los registros de pluviómetros de vecinos, fincas y hoteles de Bellavista y Santa Rosa;
4. levantar las marcas de agua (sección 9).
