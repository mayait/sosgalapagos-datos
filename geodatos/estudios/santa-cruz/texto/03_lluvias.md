[[SALTO]]

# 3. Lluvias del 15 de octubre al 2 de noviembre de 2026

En esta sección se distinguen tres tipos de información que no deben mezclarse:
- **[M] medido**: pluviómetros, METAR y temperatura del mar;
- **[E] estimado**: modelos numéricos y reanálisis;
- **[R] reportado**: informes oficiales y prensa.

Todas las horas están en **hora de Galápagos (UTC−6)** y todas las fuentes se consultaron el 2 de noviembre de 2026. Los datos y los scripts están en `datos/lluvias/` y en `scripts/15_lluvias_openmeteo.py` y `scripts/16_lluvias_ierse_evento.py`.

> **Lo esencial [M].** El 30 de octubre, la red IERSE-WSN (Universidad del Azuay) midió:
> - **178,8 mm en Los Guayabillos** (parte media, ≈178 m*);
> - **237,6 mm en Santa Rosa** (oeste, ≈416 m*).
>
> Casi todo cayó entre las 14:00 y las 21:25. Los máximos fueron de **61–66 mm en una hora de reloj** (20–21 h), **64–73 mm en 60 minutos móviles** y **138–139 mm en 3 horas**.
>
> Las dos estaciones dejaron de transmitir a las 21:22–21:25, en plena lluvia intensa, así que **los totales son mínimos**.
>
> Para la parte media es la mayor lluvia de octubre o noviembre en más de 30 años de registros cercanos: triplica el récord anterior.
>
> El modelo ECMWF de 9 km situó el máximo **unas 9 horas tarde**, con **la mitad de la intensidad horaria** y apenas un 10 % de la lluvia en la ventana en que realmente llovió. Los demás modelos se quedaron entre 4 y 85 veces por debajo, según la ventana de tiempo.

*\* Cotas del DSM Copernicus GLO-30: error de ±2–4 m y sesgo de unos −2 m frente al IGM. Son orientativas y no deben usarse como umbral.*

## 3.1 Fuentes de lluvia disponibles

Tabla: Fuentes de lluvia medida en Santa Cruz y su estado al 2 de noviembre de 2026.

| Fuente | Estaciones en Santa Cruz | Periodo | ¿Cubre el evento? |
|---|---|---|---|
| Red IERSE-WSN (U. del Azuay, con FCD, DPNG y MAG). API pública, cada 5 min | Los Guayabillos, Santa Rosa, Cerro Crocker, Militar (Baltra) | Desde abr–may de 2026 | **Sí**, con cortes (véase 3.2) |
| FCD, estación Charles Darwin, Puerto Ayora (diaria, manual) | Puerto Ayora, 2 m | 1965 a 3-jun-2026 | **No.** El archivo del dataZone se actualizó el 29-oct, pero sus datos siguen terminando el 3-jun-2026 |
| FCD / INAMHI, Bellavista (diaria) | Bellavista, 223 m | 1987 a 2019 (publicado) | No; sirve de climatología |
| INAMHI (M0191 Puerto Ayora y otras) | — | Sin portal público operativo (HTTP 500) | No disponible |
| Proyecto DARWIN (U. de Marburgo): estaciones automáticas y radar | Santa Rosa, Cerro Crocker, Puerto Ayora, Minas Rojas, Militar | Últimos datos publicados entre oct-2025 y may-2026; acceso con registro y acuerdo de uso | No publicado aún |
| METAR del aeropuerto de Baltra (SEGS) | Baltra | Continuo | Solo dice **si** llueve, no cuánto |

## 3.2 Lluvia medida del evento [M]

Tabla: Resumen por estación (red IERSE-WSN). Cobertura = registros recibidos sobre 288 posibles al día.

| Estación (cota*) | 30-oct (mm) | De ello, 14:00–21:25 | Máx. 5 min | Máx. 1 h de reloj | Máx. 60 min móvil | Máx. 3 h móvil | Cobertura 30-oct / 31-oct | Último registro del 30-oct |
|---|---|---|---|---|---|---|---|---|
| **Los Guayabillos** (≈178 m) | **≥178,8** | 158,0 | 6,4 | **61,0** (20–21 h) | **63,8** | **137,6** | 89 % / 22 % | 21:25, con 4,6 mm en esos 5 min |
| **Santa Rosa** (≈416 m) | **≥237,6** | 210,6 | 9,4 | **66,4** (20–21 h) | **73,0** | **139,2** | 88 % / 21 % | 21:22, con 3,2 mm en esos 5 min |
| Cerro Crocker (≈861 m) | 5,0 (dato dudoso, 3.5) | 2,4 | 0,4 | 0,8 | 1,2 | 1,4 | 79 % / 80 % | Siguió transmitiendo |
| Militar, Baltra (≈14 m) | 2,0 | 1,4 | 0,2 | 0,8 | 0,8 | 0,8 | 100 % / 100 % | Siguió transmitiendo |

**Cortes de transmisión** (`datos/lluvias/cortes_transmision.csv`):
- **Los Guayabillos y Santa Rosa** dejaron de transmitir a la vez (21:25 y 21:22 del 30-oct) y volvieron a la vez (18:45 y 18:42 del 31-oct): unas **21,3 horas sin datos**.
  - Cuando se cortaron, llovía a 38–55 mm/h.
  - La lluvia de ese tramo **no se midió**. No queda acumulada en ningún registro posterior: el primer registro tras el regreso marca 0,0 mm.
  - La simultaneidad apunta a una causa común (energía o comunicaciones), sin verificar.
- **Cerro Crocker** tiene un hueco **todas las noches**, de ≈01:00 a 05:30. Eso explica su cobertura del 79–81 %; no es un efecto del evento.
- **Militar** transmitió sin cortes.

**Intensidades.** El máximo en 5 minutos de Santa Rosa (9,4 mm) equivale a unos 113 mm/h; el de Los Guayabillos (6,4 mm), a unos 77 mm/h. Los pluviómetros de balancín **subestiman** la lluvia por encima de unos 50 mm/h, así que las intensidades reales pudieron ser mayores.

**Comparación con la hidrología.** Los 64 mm en 60 minutos de Los Guayabillos superan el rango de 30–50 mm/h que se usó como escala en el primer análisis de La Cascada. La cuenca tiene un tiempo de concentración de unos 86 min.

Tabla: Lluvia horaria medida el 30-oct (mm). La hora indica el inicio del intervalo. La hora de 21:00 solo cubre unos 25 minutos.

| Hora | 06 | 07 | 08 | 09 | 10 | 13 | 14 | **15** | 16 | 17 | **18** | **19** | **20** | 21* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Los Guayabillos | 4,4 | 0,8 | 6,4 | 2,4 | 0,6 | 1,8 | 1,2 | 7,8 | 5,2 | 1,0 | **35,0** | 21,2 | **61,0** | 25,6* |
| Santa Rosa | 1,2 | 2,0 | 10,6 | 6,0 | 3,6 | 2,2 | 16,4 | **43,2** | 8,8 | 2,4 | 8,8 | **43,0** | **66,4** | 21,6* |

**Cronología medida.** La lluvia tuvo tres fases:
1. **Mañana (06–11 h):** lluvia moderada, de 15 a 23 mm.
2. **Primer pulso (14:00–16:30):** concentrado en Santa Rosa, con unos 68 mm.
3. **Segundo pulso (18:00–21:25):** unos 140 mm en las dos estaciones. Cortó la medición antes de terminar.

La cronología detallada y su relación con los hechos reportados está en la sección 2. El hietograma a 5 minutos está en `datos/lluvias/hietograma_5min.csv`, y el horario en `hietograma_1h.csv`. En este último, la columna `completa` marca las horas con 11 o más registros.

![Lluvia horaria medida (red IERSE-WSN) y estimada por ECMWF 9 km del 30-oct 12:00 al 2-nov 13:00, hora de Galápagos. En gris, el corte de transmisión de Los Guayabillos y Santa Rosa.](figuras/f_lluvia_medida.png)

## 3.3 Antes y después del evento [M]

Tabla: Lluvia diaria medida (mm) del 15-oct al 2-nov. Cobertura superior al 90 % salvo donde se indica.

| Estación | 15–22 oct | **23 oct** | 24–29 oct | **30 oct** | 31 oct | 1 nov | 2 nov (hasta 13 h) | Octubre completo |
|---|---|---|---|---|---|---|---|---|
| Los Guayabillos | 6,0 | 0,0 | 12,4 | **≥178,8** | 0,0 (22 %) | 0,0 | 0,0 | **≥340,4** |
| Santa Rosa | 72,2 | **97,2** | 26,2 | **≥237,6** | 13,4 (21 %) | **34,0** | **42,8** | **≥520,6** |
| Cerro Crocker | 0,2 (sin datos 18–22 oct) | 2,6 | 0,8 | 5,0 | 3,6 | 2,2 | 1,8 | 17,6 |
| Militar (Baltra) | 0,0 | 0,0 | 0,2 | 2,0 | 0,8 | 0,0 | 0,2 | 3,2 |

**Humedad antecedente.**
- **Octubre fue un mes húmedo:** Los Guayabillos midió ≥340 mm y Santa Rosa ≥521 mm.
  - Los Guayabillos tuvo 68,2 mm el 3-oct y 43,8 mm el 4-oct.
  - **Santa Rosa tuvo 97,2 mm el 23-oct**, con 28 mm en una hora, y unos 196 mm entre el 15 y el 29.
- **Los 5 días previos (25–29 oct) fueron casi secos:** 12,4 mm en Los Guayabillos y 10,2 mm en Santa Rosa.
- El suelo no estaba saturado al empezar el 30-oct. Sí debió de estarlo antes del segundo pulso: a las 18:00 ya habían caído unos 36 mm en Los Guayabillos y unos 98 mm en Santa Rosa, contando desde la madrugada.

**El 30-oct en la serie completa de la red (23-abr a 2-nov-2026).** El 30-oct es, de lejos, el mayor día de la serie en las dos estaciones fiables:
- en total diario, multiplica por 2,4–2,6 el segundo mayor día;
- en intensidad horaria, multiplica por 2,4–4,8 el segundo mayor valor.

La serie es corta (6 meses) y no incluye ninguna estación cálida completa.

Tabla: Mayores días de la serie IERSE-WSN por estación (mm; `datos/lluvias/mayores_dias_por_estacion.csv`).

| Estación | 1.º | 2.º | 3.º | 4.º | Máx. 1 h fuera del 30-oct |
|---|---|---|---|---|---|
| Los Guayabillos | **178,8 (30-oct; 61,0 en 1 h)** | 68,2 (3-oct) | 46,0 (12-sep) | 43,8 (4-oct) | 12,8 (12-sep) |
| Santa Rosa | **237,6 (30-oct; 66,4 en 1 h)** | 97,2 (23-oct; 28,2 en 1 h) | 65,2 (14-jun) | 54,4 (12-sep) | 28,2 (23-oct) |
| Cerro Crocker | 62,2 (14-jun; 23,2 en 1 h) | 35,4 (4-jun) | 27,2 (1-jul) | 24,6 (9-jun) | — (5,0 el 30-oct) |
| Militar (Baltra) | 21,8 (7-may; en 1 h, cobertura 58 %) | 2,0 (30-oct) | 1,2 (10-jun) | 1,0 (27-abr) | — |

![Lluvia diaria medida por la red IERSE-WSN del 23-abr al 2-nov-2026, con el 30-oct en negro. Cerro Crocker deja de registrar lluvias apreciables desde el 11 de agosto (línea de puntos).](figuras/f_lluvia_diaria_serie.png)
- **Las estaciones siguieron registrando después del evento.**
  - Santa Rosa: 34 mm el 1-nov (16–20 h, con 14,8 mm entre las 19 y las 20 h) y 42,8 mm el 2-nov hasta las 13:10. **La lluvia continúa en la parte alta oeste.**
  - Los Guayabillos: **0,0 mm** desde que volvió a transmitir (31-oct 18:45) hasta el 2-nov 13:10, con una cobertura del 100 % el 1-nov. En ese tiempo hubo 90 mm en Santa Rosa (13,4, 34,0 y 42,8 mm).
    - Hay razones para dudar del sensor: el pluviómetro se cortó en plena tormenta y su registro cambió tras el regreso (marcas exactas cada 5 minutos, que sugieren un reinicio). Además, pudo recibir hojas o barro.
    - Hay también razones para no darlo por dañado: antes del evento ya hubo días con lluvia en Santa Rosa y nada en Los Guayabillos (23-oct: 97,2 frente a 0,0), y la correlación diaria entre ambas es baja (r = 0,37, abril–octubre sin el evento).
    - **Puede estar obstruido o dañado, pero los datos no permiten afirmarlo. Hay que verificarlo en campo.**
- **Baltra.** El METAR del aeropuerto (SEGS) reporta **lluvia fuerte (+RA, visibilidad de 3 000 m) entre las 11:35 y las 13:00 del 30-oct**. La estación Militar, a unos 4 km, marcó 0,0 mm en esas horas y solo 27,8 mm desde abril. La lluvia pudo ser muy local, pero el dato de Militar debe tomarse con cautela.

## 3.4 ¿Qué tan mal lo hicieron los modelos?

Tabla: Lluvia medida frente a estimada en la celda de cada estación (mm). Modelos de Open-Meteo pedidos directamente en hora de Galápagos.

| Fuente | 30-oct, 14–22 h | Día 30-oct | Día 31-oct | 30 + 31 oct | Máx. 1 h (hora de inicio) |
|---|---|---|---|---|---|
| **Medido, Los Guayabillos** | **158,0** | **≥178,8** | ≥0 (22 % de cobertura) | **≥178,8** | **61,0 (30-oct, 20 h)** |
| ECMWF 9 km, celda de Los Guayabillos | 17,1 | 39,8 | 129,8 | 169,6 | 32,5 (31-oct, 05 h) |
| **Medido, Santa Rosa** | **210,6** | **≥237,6** | ≥13,4 (21 %) | **≥251,0** | **66,4 (30-oct, 20 h)** |
| ECMWF 9 km, celda de Santa Rosa | 15,0 | 33,1 | 153,1 | 186,2 | 38,0 (31-oct, 05 h) |
| Otros 6 modelos (ECMWF 0,25°, GFS, ICON, JMA, Météo-France, UKMO), mismas celdas | 1,1–7,2 | 2,8–15,6 | 0,2–30,5 | 3,0–41,8 | 0,9–4,6 |

**Hora.** ECMWF de 9 km situó el máximo entre las 05 y las 06 h del 31-oct, **unas 9 horas después** del máximo medido. En la ventana en que realmente llovió (14–22 h del 30-oct) estimó entre el 7 y el 11 % de lo medido. Ningún modelo reprodujo los dos pulsos de la tarde y la noche.

**Cantidad.**
- En 48 horas, ECMWF de 9 km (170–186 mm) queda **por debajo** del mínimo medido en Santa Rosa (≥251) y cerca del de Los Guayabillos (≥179).
- **No puede comprobarse si llovió en la madrugada del 31**, que es cuando ECMWF pone su máximo, porque las dos estaciones estaban cortadas.
- Hay indicios débiles de que no llovió mucho en esas horas: Militar no registró lluvia y Cerro Crocker estaba en su hueco nocturno.
- La prensa habla de lluvia «hasta las 06:00» y de «15 horas» de lluvia, sin indicar el huso [R].
- **Conclusión:** la afirmación previa de que «ECMWF sobrestima la lámina» **no se sostiene**. Lo medido iguala o supera a ECMWF en 24–48 h.

**Intensidad.** ECMWF de 9 km dio la mitad de la intensidad horaria medida. Los demás modelos la subestimaron entre 13 y 74 veces.

**Antes del evento.** Del 15 al 29 de octubre, ECMWF de 9 km dio unos 63 mm en ambas celdas, frente a 196 mm medidos en Santa Rosa y 18 mm en Los Guayabillos. El modelo **no resuelve el contraste oeste–centro** de la parte alta.

> **Implicación.** Para Santa Cruz, los modelos de pronóstico que se pueden consultar en abierto no sirven como estimación cuantitativa de la lluvia de un evento convectivo, ni como aviso. Ni siquiera sirve el mejor de ellos. La medición en tiempo casi real sí detectó la tormenta (sección 2).

## 3.5 Cerro Crocker: ¿5 mm reales o fallo del sensor?

El sensor **transmite y bascula**: registra pasos de 0,2 mm casi todas las horas. Pero su serie desde abril indica un **cambio de comportamiento a partir del 11 de agosto de 2026**.

Tabla: Cerro Crocker frente a Santa Rosa y Los Guayabillos por periodos (mm; `datos/lluvias/verificacion_cerro_crocker.csv`).

| Periodo | Crocker, total | Santa Rosa, total | Los Guayabillos, total | Crocker, máx. 1 h | Santa Rosa, máx. 1 h |
|---|---|---|---|---|---|
| 23-abr a 31-may | 34,2 | 189,2 | 97,8 | 2,6 | 16,4 |
| Junio | **296,6** | 290,6 | 190,4 | **23,2** | 13,2 |
| Julio | 141,4 | 162,0 | 103,4 | 3,8 | 9,4 |
| 1 a 10 de agosto | 29,2 | 40,8 | 31,8 | 3,0 | 2,4 |
| 11 a 31 de agosto | **4,0** | 77,4 | 27,6 | 1,2 | 4,8 |
| 1-sep a 29-oct | **17,8** | 458,0 | 301,6 | **0,8** | 28,2 |

**Antes del 11 de agosto**
- En 33 días con 5 mm o más en Santa Rosa, Crocker registró al menos 1 mm en 32.
- En esos días sumó 404 mm, frente a 475 mm en Santa Rosa (85 %).
- Es lo esperable en una cumbre de barlovento con garúa. En junio Crocker fue la estación más lluviosa, con 62,2 mm el 14 de junio.

**Desde el 11 de agosto**
- Solo 6 de 20 días comparables tuvieron al menos 1 mm en Crocker.
- Sumó 16 mm, frente a 404 mm en Santa Rosa (4 %).
- **No volvió a superar 1,2 mm en una hora.** El 23-oct, con 97 mm en Santa Rosa, Crocker registró 2,6 mm.

**Humedad y pauta diaria** (`datos/lluvias/cerro_crocker_mensual.csv`):
- **Humedad.** Desde julio, la humedad relativa de Crocker marca 100 % en el 100 % de las horas. La cumbre está casi siempre dentro de la nube, en condiciones de garúa. Con ese régimen, un pluviómetro que funciona recoge llovizna con frecuencia:
  - en junio y julio, Crocker registró lluvia en 250 y 185 horas;
  - en agosto, septiembre y octubre, con la misma humedad y con más lluvia en el resto de la isla, solo en 66, 29 y 62 horas.
  - Una humedad permanentemente en 100 % también puede indicar un sensor saturado, así que este dato confirma la nube pero no la lluvia.
- **Pauta diaria.** Antes del 11 de agosto, las horas con lluvia seguían el ciclo típico de la garúa: más frecuentes de noche y de madrugada (32–46 casos por hora del día entre las 21 y las 07 h, sin datos entre las 01 y las 05 h por el hueco nocturno de transmisión) y menos por la tarde (14–22 entre las 13 y las 18 h). Desde el 11 de agosto quedan pocos casos (3–10 por hora del día), repartidos sin pauta clara. Eso cuadra con un goteo residual más que con lluvia real.

**Durante el evento**, Crocker siguió marcando 0,2–0,8 mm/h de forma regular, igual que en días secos posteriores (2,2 y 1,8 mm el 1 y el 2-nov). Al mismo tiempo, su temperatura bajó unos 2 °C entre las 13 y las 15 h, a la vez que el primer pulso de Santa Rosa. Eso es compatible con la cercanía de la convección.

> **Conclusión.** El patrón (tope de ≈1 mm/h y goteo regular) es el típico de un **embudo parcialmente obstruido** (hojas, musgo, insectos o sedimento) desde mediados de agosto. **Los 5 mm de Cerro Crocker no son una medida fiable** y no permiten concluir que la cumbre quedara seca. Por tanto, la idea de una «tormenta de cotas medias» **no está demostrada**: puede ser cierta, pero no se apoya en este dato. Hace falta inspeccionar el pluviómetro en campo.

## 3.6 Comparación con la climatología medida [M]

Climatología de la FCD (serie diaria): Bellavista, a 223 m y a ≈1,7 km de Los Guayabillos, con datos de 1987 a 2019; Puerto Ayora, con datos de 1965 a 2026.

Tabla: Lluvia del evento frente a los registros históricos (mm).

| Indicador | Bellavista (FCD) | Puerto Ayora (FCD) | Evento 2026 |
|---|---|---|---|
| Media de octubre (1991–2019/2020) | 63,7 | 10,9 | Octubre de 2026: **≥340,4** en Los Guayabillos (5,3 veces la media de Bellavista) y ≥520,6 en Santa Rosa |
| Octubre más lluvioso (1991–2019/2020) | 143,2 | 29,6 | — |
| Máximo diario de octubre o noviembre | **59,5** (16-nov-1997) | 104,3 (2-oct-2023) | **178,8** (Los Guayabillos) y **237,6** (Santa Rosa), mínimos |
| Máximos diarios de cualquier mes | 490,0, 280,0 y 202,0 (marzo de 2008)†; 164,1 (12-mar-2005); 130,0 (29-abr-1998) | 312,0 (31-mar-2022); 215,0 (22-feb-2024); 186,3 (30-abr-1997) | — |

*† La FCD advierte que los datos publicados de Bellavista fueron «ajustados» por los digitalizadores. El episodio de marzo de 2008 (770 mm en 3 días) debe verificarse con la serie original.*

**¿Es un récord?**
- **Para octubre y noviembre, sí, con mucho margen.** En la parte media (Los Guayabillos y Bellavista) el día triplica el récord de 32 años, y el mes quintuplica la media de octubre.
- **Para cualquier época del año, no necesariamente.**
  - 178,8 mm ocuparía el 4.º lugar de la serie de Bellavista, y el 1.º si se excluye el episodio dudoso de 2008.
  - 237,6 mm ocuparía el 3.º lugar.
- **Santa Rosa** no tiene una serie histórica larga en ese punto, así que no se puede hablar de récord local.
- **La intensidad horaria** (61–66 mm/h) no puede compararse: no hay series horarias históricas públicas en Santa Cruz.
- Que un evento así ocurra a finales de octubre, en plena estación de garúa, es coherente con El Niño en curso.
  - El mar alrededor de Santa Cruz estuvo durante octubre entre 26,7 y 28,2 °C, con una anomalía de +4,7 a +5,9 °C (NOAA OISST).
  - La región Niño 1+2 marcó +5,4 °C (NOAA CPC, semana del 28-oct).
  - El ERFEN declaró El Niño el 28 de agosto. Los detalles están en el estudio de La Cascada (sección 3.3).

## 3.7 Periodo de retorno: solo como orden de magnitud

Se ajustaron distribuciones de Gumbel y GEV a los **máximos diarios anuales de Bellavista**: 31 años completos, de 1988 a 2018.

Tabla: Periodo de retorno indicativo de la lluvia diaria en Bellavista (régimen anual).

| Lluvia diaria | Gumbel | GEV (ξ ≈ 0,20) | Años con excedencia en la serie |
|---|---|---|---|
| 179 mm (Los Guayabillos) | ≈23 años | ≈16 años | 1 de 31 |
| 238 mm (Santa Rosa) | ≈110 años | ≈40 años | 1 de 31 |

> **Estos valores no son de diseño**, por varias razones:
> - la serie es corta e incluye años El Niño y años normales (una población mixta);
> - los valores medidos son mínimos y cayeron en unas 7 horas, no en 24;
> - Santa Rosa está en otro lugar y a otra cota que Bellavista;
> - el día pluviométrico de la FCD (lectura manual) no coincide con el día natural.
>
> Lo único sólido es el orden de magnitud: **decenas de años en régimen anual**. Para octubre o noviembre es un valor **sin precedentes** en los registros disponibles. Para la intensidad horaria **no hay base para estimar un periodo de retorno**, porque no existen curvas IDF publicadas en Santa Cruz.

## 3.8 Afectación reportada [R]

La SNGR atribuye el evento a «fuertes precipitaciones registradas durante la tarde y noche del 30/10/2026», lo que **coincide con lo medido**.

Cuerpos de agua con nivel en ascenso el 30-oct, según el SitRep n.º 01 de Galápagos:
- la cañada El Aguacatal, Guayabillos y El Occidente, en Bellavista;
- el Parque Artesanal y El Bosque, en Puerto Ayora.

La prensa cita además Santa Rosa, Miramar, Divino Niño, La Cascada, La Unión y el sector Tomás de Berlanga (El Universo, 31-oct).

Las cifras de afectación están en la sección 2 y en el estudio de La Cascada (sección 3.4):
- 1 fallecido en la cañada El Aguacatal;
- 3 120 personas afectadas en la provincia según el SitRep 67, con una incoherencia interna sobre el número de familias;
- 165 personas en refugios al 31-oct.

## 3.9 Limitaciones y datos que hay que pedir

**Limitaciones**
- Solo dos pluviómetros fiables midieron el evento, y ninguno en Puerto Ayora, El Aguacatal ni el sector Tomás de Berlanga.
- Las dos estaciones se cortaron antes del final de la lluvia.
- Los pluviómetros de balancín subestiman las intensidades altas.
- El sensor de Cerro Crocker parece obstruido, y Militar es dudoso.
- La climatología horaria no existe en abierto.

> **Recomendación: revisar en campo Cerro Crocker y Los Guayabillos cuanto antes.**
> - **Cerro Crocker:** probable obstrucción del embudo desde el 11 de agosto.
> - **Los Guayabillos:** 0,0 mm durante 42 h con lluvia en Santa Rosa, justo después de la tormenta.
>
> En cada uno hay que:
> - limpiar el embudo y el filtro;
> - comprobar que el balancín bascula libremente;
> - hacer una prueba de calibración con un volumen conocido;
> - fotografiar el estado antes de intervenir y anotar la hora.
>
> Hasta entonces, **ninguna de las dos estaciones debe usarse** como medida de la lluvia posterior a sus fechas de fallo.

**Datos que hay que pedir**
1. **IERSE (U. del Azuay):**
   - ¿Guardan las estaciones los registros en memoria local durante los cortes? Si es así, se podría **recuperar la lluvia del 30-oct desde las 21:25 hasta el 31-oct a las 18:45**.
   - La revisión en campo de Cerro Crocker y Los Guayabillos descrita arriba, y la causa del corte simultáneo.
2. **FCD:** lectura diaria de la estación Charles Darwin del 15-oct al 2-nov (datazone@fcdarwin.org.ec).
3. **INAMHI:** datos de M0191 (Puerto Ayora), Bellavista y Baltra, y las curvas IDF si existen.
4. **Proyecto DARWIN (U. de Marburgo, contacto: N. Turini):** datos de sus estaciones automáticas de Santa Rosa, Cerro Crocker, Puerto Ayora y Minas Rojas para octubre y noviembre de 2026. Son series de 10 min con lluvia, y de radar (MRR) en Cerro Crocker.
5. **GPM IMERG** (cuenta gratuita de NASA Earthdata), para la distribución espacial.
6. **Pluviómetros privados** (fincas, hoteles y escuelas de Bellavista y Santa Rosa), y las marcas de agua del evento.
