Intro: Quién hizo este estudio y con qué alcance, qué datos usa, cómo se calcularon cuencas, vasos y caudales, cuánto se equivoca el modelo de elevación y cuánta confianza merece cada conclusión. Al final están las descargas y todas las fuentes.

# Quién lo hizo y para qué sirve

Es un reconocimiento de gabinete. **No es un diseño de ingeniería, ni un mapa oficial de amenaza, ni un dictamen profesional.**

- **Quién lo hizo.** El mismo comité de agentes de inteligencia artificial (Claude, de Anthropic) del estudio de Santa Cruz, a pedido de la coordinación de respuesta de USFQ Galápagos:
  - un hidrólogo dedicado a San Cristóbal, que aplica los métodos ya revisados en La Cascada;
  - especialistas en meteorología, gestión del riesgo y planificación urbana.
- **Sin revisión profesional.** No lo han revisado **profesionales habilitados**. Hasta entonces, estas conclusiones no sirven para decidir obras, permisos ni reasentamientos.
- **Sin campo.** **Ningún punto se ha visitado.** Las cifras cambiarán con datos de campo.
- **Sin lluvia medida.** En San Cristóbal **no hay lluvia medida pública** del evento de octubre de 2026. Los caudales son escenarios, no reconstrucciones.

# Datos y convenciones

## Datos

- **Elevación:** modelo de superficie Copernicus GLO-30 (30 m). Incluye techos y vegetación y tiene un error vertical de ±2–4 m.
- **Cartografía:** IGM 1:25 000 y OpenStreetMap (31-oct-2026).
- **Edificios:** OSM y Google Open Buildings.
- **Población:** INEC.
- **Registros y capas de riesgo:** SNGR y CGREG.
- **Lluvia:** estimaciones de modelos (Open-Meteo) y observaciones METAR del aeropuerto.

## Convenciones

- Las horas son de Galápagos (UTC−6).
- Las cotas son del DSM. Las marcadas con * son orientativas (±2–4 m; en Puerto Baquerizo, sesgo local de unos +1,5 m frente al IGM) y no sirven como umbrales.
- Se distingue el tipo de dato: **[M]** medido, **[E]** estimado y **[R]** reportado (por una institución, un medio o un documento).
- Los lugares de acogida temporal se llaman «refugio».

# Cómo se calcularon cuencas, vasos y caudales

Se aplicaron los métodos ya revisados en La Cascada (Santa Cruz):
- **Flujo:** D8 (pysheds) sobre el DSM Copernicus GLO-30 reproyectado a UTM 16S (30 m), con las quebradas del IGM quemadas (−3 m). Como sensibilidad se repitió sin quemarlas.
- **Vasos:** relleno global desde el mar («priority-flood», equivalente al camino de mínimo umbral), sin ventanas de cálculo y, por tanto, sin bordes artificiales. Un vaso es **robusto** si tiene ≥ 1 m de profundidad y persiste (≥ 0,3 m) con el «proxy de suelo» (mínimo 3×3 del DSM). La exposición se cuenta solo por debajo de la cota de rebose.
- **Hidrología:** SCS-CN (Ia = 0,2 S) e hidrograma unitario SCS; tormenta tipo II de 24 h con 50, 100 y 150 mm y CN de 60, 70 y 80; tc por Kirpich, Témez, SCS lag, TR-55 y Manning, del que se da el rango.
- **Trazado junto al campus:** 400 realizaciones con 1–3 m de ruido añadido al DSM (Monte Carlo) y una repetición en la rejilla geográfica original.
- **Modelo 2D:** lluvia sobre la malla con un esquema inercial local; método y escenarios en [Modelo 2D](../modelo-2d/).

El cálculo se reproduce con `scripts/17_san_cristobal_inundacion.py`; las cifras están en `datos/resumen.json`.

## Contraste del DSM con los puntos acotados del IGM

Tabla: DSM menos punto acotado del IGM 1:25 000 (m).

| Ámbito | n | Media | Mediana | Desv. típica | RMSE | P5 a P95 |
|---|---|---|---|---|---|---|
| Isla completa | 2 087 | −2,9 | −2,1 | 6,3 | 6,9 | −11,9 a 3,9 |
| ≤ 5 km de Puerto Baquerizo | 96 | +1,5 | +1,8 | 2,6 | 3,0 | −3,2 a 5,4 |
| Dentro de la zona urbana | 21 | +1,0 | +1,1 | 2,8 | 3,0 | −2,3 a 4,8 |
| ≤ 2 km de El Progreso | 25 | +1,9 | +1,5 | 4,7 | 5,1 | −5,5 a 9,3 |

- En el entorno de Puerto Baquerizo el error es de ≈3 m (RMSE), como en Santa Cruz, pero **el sesgo cambia de signo**: +1,5 m, frente a −2,1 m en Puerto Ayora. **El sesgo de «unos −2 m» que usa el estudio de Santa Cruz no vale aquí: es local.**
- En El Progreso el RMSE sube a 5 m, del orden de la profundidad de sus vasos.
- En la isla completa hay colas largas (P5 = −12 m) por el relieve y la vegetación de la parte alta.

# Incertidumbre y confianza

- **DSM:** ±3 m en torno a la ciudad y ±5 m en El Progreso. En tramos con un 1–3 % de pendiente eso equivale al desnivel de 100 m de recorrido. Por eso las rutas del rellano del campus y de las salidas a Playa Mann son inciertas en decenas a cientos de metros.
- **El DSM no ve** alcantarillas, cauces entubados ni bordillos; en la ciudad el agua sigue las calles.
- **Lluvia:** no hay ninguna medida. Con 100 mm, el caudal pico de la quebrada del campus varía unas 7 veces (2,0–13,7 m³/s) según el CN (60–80) y el método de tc.
- **Campus:** no está cartografiado como polígono. Se aproximó con los edificios universitarios de OSM (0,8 ha).

Tabla: Nivel de confianza de cada conclusión.

| Conclusión | Confianza |
|---|---|
| Área que drena a Puerto Baquerizo (≈11 km²) y peso de la Galápagos (Barrio Frío) | Alta |
| Correspondencia con las encañadas oficiales (Galápagos, Divino Niño) | Alta; Alvear, Playa Mann y La Planada: media; resto: baja |
| Hipótesis: la Galápagos puede desbordar hacia Divino Niño por un tramo con ≈1,2 m* de resalte en una recta de 466 m | Media-baja (consecuencia alta) |
| El Progreso está en la cuenca alta de Barrio Frío | Media-alta |
| En Puerto Baquerizo no hay vasos de almacenamiento relevantes: el problema es el paso del agua | Media |
| Encharcamiento por depresiones en El Progreso | Media-baja |
| Ranking de puntos | Media-baja (pesos convencionales) |
| La quebrada del campus puede entrar en él por la Vía Universidad | Baja-media: plausible, no demostrada |
| Sesgo del DSM de +1,5 m en Puerto Baquerizo | Media |
| Caudales pico | Baja (solo orden de magnitud) |

\* Cota del DSM (±2–4 m), orientativa.

La confianza de los resultados del modelo 2D está en [Modelo 2D](../modelo-2d/), apartado «Confianza». El detalle de cada conclusión está en [Encañadas](../encanadas/), [El Progreso](../el-progreso/), [Campus](../campus/) y [El Plan de Acción de la UGR frente al análisis](../plan-ugr/).

# Descargas

Todas las capas y tablas del estudio, en GeoJSON (WGS84) y CSV (UTF-8). Incluyen cotas del DSM de 30 m (±2–4 m). Las fuentes y licencias están en «Fuentes y referencias», más abajo. Las capas que derivan de OpenStreetMap se distribuyen con licencia ODbL.

[[DESCARGAS]]

# Fuentes y referencias

- UGR del GAD municipal de San Cristóbal, *Plan de Acción SC-4-09-2026 – Fenómeno El Niño – San Cristóbal*. Documento interno facilitado por la coordinación de USFQ Galápagos el 2-nov-2026; citado, no reproducido.
- SNGR, SitRep n.º 01 de Galápagos (31-oct-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SITREP-Nro.-01-Lluvias_Galapagos_29.08.2026-31.10.2026.pdf
- SNGR, SitRep 67 nacional (1-nov-2026): https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SitRep-No-67-Lluvias-29082026-al-01112026-15h00f21.pdf
- USFQ, estudio de las encañadas de Puerto Baquerizo Moreno: https://repositorio.usfq.edu.ec/bitstream/23000/10220/1/138016.pdf
- Ryan, S. J. et al. (2019). Socio-ecological factors associated with dengue risk and *Aedes aegypti* presence in the Galápagos Islands, Ecuador. *Int. J. Environ. Res. Public Health*: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6427784/
- Universidad de Florida, resumen del estudio (incidencia de 2010 en Puerto Baquerizo Moreno): https://epi.ufl.edu/2019/03/13/new-study-explores-galapagos-islands-dengue-risks
- USFQ, *Esferas*: vigilancia de *Aedes aegypti* con trampas Gravid-Aedes en Galápagos: https://revistas.usfq.edu.ec/index.php/esferas/article/download/1988/2312
- LOGIRD: https://procuraduria.utpl.edu.ec/NormativaExterna/LEY%20ORG%C3%81NICA%20PARA%20LA%20GESTI%C3%93N%20INTEGRAL%20DEL%20RIESGO%20DE%20DESASTRES.pdf
- LOREG: https://faolex.fao.org/docs/pdf/ecu166165.pdf
- Bates, P. D., Horritt, M. S. y Fewtrell, T. J. (2010): esquema inercial local usado en el [Modelo 2D](../modelo-2d/).
- Datos: `capas/final/` (eventos SNGR, refugios SNGR 2025, MSP, MINEDUC, OSM, CGREG, INOCAR), DSM Copernicus GLO-30 y resultados del modelo 2D (`datos/modelo2d/`).

Las fuentes de las tomas de agua del acueducto están en [Tomas de agua](../agua/).
