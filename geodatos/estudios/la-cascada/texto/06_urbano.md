[[SALTO]]

# 6. Diagnóstico urbano

## 6.1 Datos y método

El diagnóstico urbano parte del DSM GLO-30 y de un **«proxy de suelo»** construido a partir de él: el mínimo del DSM en una ventana de 3 × 3 celdas (90 m), que reduce el sesgo que introducen los techos. Sobre esa base se usaron:
- las vías de OSM con nombres (31-oct-2026);
- los edificios de OSM y Google Open Buildings v3;
- las manzanas del INEC con su población estimada y las viviendas de la SNGR;
- el suelo urbano del CGREG;
- las quebradas del IGM y de OSM, y la franja de 20 m del CGREG.

Con estas capas se trazaron tres elementos:
- la **línea de flujo D8** del barrio al mar;
- la **ruta de menor coste por la red de calles**, que penaliza cada metro de subida;
- un **llenado tipo «bañera»** conectado al fondo del barrio.

## 6.2 La salida natural del agua no tiene cauce

La quebrada cartografiada pasa a 28 m del borde norte del barrio. Desde allí, OSM la dibuja hacia el este por el pie del escarpe, pero sin llegar al mar (sección 5.3). **Entre el barrio y el mar no hay ningún cauce cartografiado.** Desde allí, la línea de flujo recorre **1 194 m hacia el SSE**, de la cota 12,0 m a la 1,3 m (pendiente media 0,9 %), hasta la ensenada al oeste del muelle de la DPNG. Por el camino **pasa sobre 28 edificaciones**, que ocupan el 24 % de su longitud, y tiene 16 cruces de vías: 11 calles y la Av. Charles Darwin, que cruza tres veces. Los primeros 400 m son prácticamente planos (0,25 % y luego −0,13 %).

Tabla: Perfil del cauce natural urbano por tramos (DSM).

| Tramo (m) | Cota (m) | Pendiente | Lectura |
|---|---|---|---|
| 0–400 | 12,0 → 11,8 | 0,25 % / −0,13 % | Fondo de la depresión, sin pendiente útil |
| 400–600 | 11,5 → 9,6 | 1,0 % | Umbral y comienzo del descenso |
| 600–800 | 9,2 → 5,8 | 1,8 % | El tramo más inclinado |
| 800–1 194 | 5,7 → 1,3 | 1,0–1,2 % | Frente costero y Av. Charles Darwin, bajo la influencia de la marea |

La calle **Marchena**, de 1 040 m, es la única vía continua alineada con este eje y la candidata natural a funcionar como calle-canal. Hoy no puede hacerlo: al salir del barrio sube unos 3 m (una parte puede ser efecto de los techos en el DSM). Además cruza unas 20 calles transversales y su pendiente media es de solo 0,64 %, con tramos en contrapendiente.

**Sobre la línea de flujo hay un umbral** de unos +1,4 m en Isla Santiago – Karl Angermeyer (−90,3121; −0,7372). Retiene el agua que ya desbordó del vaso del barrio (sección 4.4). Con 30 m de resolución no se puede distinguir si es un lomo de lava o un relleno urbano.

Según la prensa (2023, sin fuente oficial), **Santa Cruz no tiene alcantarillado pluvial**, y el drenaje depende de sumideros que infiltran hacia las grietas del basalto. Hay que verificarlo con el GAD.

Tabla: Obstáculos identificados sobre la salida natural (`datos/urbano/tapones.geojson`).

| Tipo | n | Observación |
|---|---|---|
| Umbral sobre la línea de flujo (Isla Santiago – Karl Angermeyer) | 1 | +1,3–1,4 m sobre el fondo local; retiene el agua desbordada |
| Umbral en la cabecera de Marchena | 1 | +3 m; una parte puede ser efecto de los techos en el DSM |
| Cruces de vías | 16 | 11 calles y la Av. Charles Darwin (3 cruces). Se desconocen las rasantes, los bordillos y los pasos bajo la vía |
| Edificaciones sobre la línea de flujo | 28 | Hay muros y cerramientos sin cartografiar |
| Desembocadura | 1 | Tramo plano a 3–4 m de cota, edificado y con influencia de la marea |

![La Cascada: relieve, edificaciones, llenado estático de la depresión a las cotas 13–16 m, salida natural del agua hacia el mar y obstáculos sobre ella. El interceptor hipotético (en morado) se analiza en la sección 5.](figuras/f_mapa_barrio.png)

## 6.3 Exposición

Tabla: Edificaciones y población expuestas. En esta tabla la población del INEC se reparte por área de techo; en la sección 4 se reparte por área de la manzana, lo que explica pequeñas diferencias. Entre paréntesis, la estimación de la SNGR.

| Zona | Área (ha) | Edificios | Población |
|---|---|---|---|
| Polígono del barrio (unión de OSM y CGREG) | 6,1 | 260 | 1 310 (1 309) |
| Área afectada aproximada, radio de 350 m (por validar) | 38,2 | 772 | 3 641 (3 602) |
| **Vaso cerrado, de 12,5 m al rebose (cifra de referencia; sección 4.4)** | 3,7–6,2 | **68–204** | **≈ 400–910** |
| Sensibilidad: zona baja cerrada, DSM ≤ 13,25 m (4 vecinos) | 5,3 | 140 | ≈ 710 |
| Sensibilidad: zona baja cerrada, proxy de suelo ≤ 12,0 m | 15,0 | 374 | ≈ 1 680 |
| Franja de 15 m del cauce natural urbano | 3,6 | 57 | ≈ 150 |
| Franja de 30 m del cauce natural urbano | 7,4 | 130 | ≈ 300 |

- **El cauce urbano no tiene protección normativa.** La franja de protección de quebradas del CGREG («encañadas», 20 m) **no tiene ningún polígono en Puerto Ayora**; el más cercano está a unos 4,7 km.
- **Indicios de crecimiento hacia el escarpe, sin fecha.** Hay 1 201 de 4 854 edificios del suelo urbano de Puerto Ayora (25 %) fuera de la antigua zona urbana del IGM. En el entorno de 500 m de La Cascada son pocos, 43 de 1 524, pero 36 de ellos están **al norte, hacia el pie del escarpe**, por donde entra el agua. Para confirmar si el crecimiento fue hacia allí hacen falta imágenes históricas o el catastro con las fechas de los permisos.

## 6.4 Propuestas urbanas

Las capacidades son de orden de magnitud: fórmula de Manning con n = 0,016 y S = 1 %. **Con la pendiente real de Marchena (0,64 % de media, con contrapendientes) serían un 20 % menores o menos**, y el rebaje de la rasante es parte del diseño. Los costes son indicativos e incluyen un sobrecoste insular del 30–60 %. **No deben usarse para presupuestar sin diseño.**

Tabla: Propuestas urbanas ordenadas por prioridad.

| # | Medida | Plazo | Magnitud y criterio | Coste orientativo | Competencia |
|---|---|---|---|---|---|
| U1 | Moratoria de permisos en la zona baja y la franja de 30 m. Planta baja ≥ cota de rebose **medida con GNSS** + 0,5 m. En el DSM el rebose está en ≈12–13,25 m, pero esa cota no sirve como umbral normativo (sesgo de −2 a −3 m). Prohibición de sótanos y de dormitorios en planta baja. Cerramientos permeables al flujo | Inmediato | Frena el crecimiento de la exposición (68–204 edificios en el vaso; más en la sensibilidad) | Bajo (ordenanza) | GAD municipal |
| U2 | Abrir el corredor de salida. Inmediato: limpieza de sumideros y desembocadura libre. En semanas: badenes y rebaje de bordillos en los cruces. Las aberturas en muros privados requieren estudio | Corto | Elimina los obstáculos locales en eventos frecuentes. **Traslada agua aguas abajo**, a los 57–130 edificios de la franja del cauce | USD 0,1–0,5 M | GAD; la DPNG, para la descarga en la Reserva Marina |
| U3 | Topografía de detalle (dron o LiDAR con GNSS), marcas de agua del evento y catastro de sumideros y pasos bajo las vías | Corto | Condición previa de U4–U8 | USD 50–150 k | GAD y CGREG con la academia |
| U4 | Calle-canal en Marchena (sección en V, bordillos altos) y **colector de cajón** hasta el mar, con rebaje controlado del umbral de 1,4 m | Mediano | La calle lleva ≈ 8–18 m³/s y un cajón de 3 × 2 m, ≈ 28 m³/s: en total 35–45 m³/s con S = 1 % (menos con la pendiente real), **frente a picos de 74–143 m³/s con 100 mm (CN 70) y de 150–230 m³/s en el escenario alto del evento**. No basta sola | USD 4–10 M (1,2 km) | GAD, con financiación del CGREG o del Estado |
| U5 | Ampliar las alcantarillas y los pasos bajo la Av. Charles Darwin y las calles transversales, con descarga dotada de disipador y clapeta antirretorno | Mediano | Se dimensiona con el caudal del corredor y la marea | USD 0,5–2 M | GAD; DPNG y MAATE en la costa |
| U6 | Reasentamiento voluntario de las viviendas más bajas del vaso (las de mayor lámina según las marcas de agua y la topografía GNSS) | Mediano y largo | Del orden de decenas a ≈125 edificios, dentro de los 68–204 del vaso; prioridad para los hogares con personas vulnerables | USD 70–150 k por vivienda | GAD (utilidad pública) y CGREG (suelo y vivienda) |
| U7 | Declarar la franja del cauce natural como **suelo urbano de protección** en el PUGS, sin reconstrucción después de un daño | Largo | 57 edificios en la franja de 15 m y 130 en la de 30 m | Variable | GAD |
| U8 | **Parque inundable o plaza de agua** en la depresión, sobre el suelo liberado (1–2 ha, 1–1,5 m de profundidad) | Largo | 10 000–30 000 m³, **solo si se excava por debajo del terreno actual**. Atenúa los eventos frecuentes y retiene sedimentos; en un evento extremo el vaso se llena igual | USD 1–4 M, más el suelo | GAD |
| U9 | Drenaje sostenible (SUDS): cisternas en los techos, pavimentos permeables y zanjas de infiltración **solo con pretratamiento** y lejos de pozos sépticos | Continuo | 2,5 ha de techos × 50 mm ≈ 1 250 m³: efecto local | Bajo a medio | GAD; CGREG y MAATE para el acuífero |

> **Advertencia sobre la infiltración.** El acuífero basal de Puerto Ayora ya muestra contaminación fecal atribuida a los pozos sépticos y a los vertidos en grietas. Infiltrar escorrentía urbana sin tratar en el basalto fracturado puede agravarla. Es preferible almacenar y reutilizar el agua antes que infiltrarla.

## 6.5 Instrumentos y competencias

- **GAD municipal de Santa Cruz.** Es responsable del PDOT y del PUGS, del uso y la ocupación del suelo, del control de las edificaciones, del alcantarillado pluvial y de la vialidad urbana (COOTAD art. 55; Constitución art. 264). La LOOTUGS le permite clasificar suelo urbano de protección por riesgo y declarar de utilidad pública los predios que se reasienten.
- **CGREG.** El Plan Galápagos es vinculante para el PDOT y el PUGS. Además controla la residencia (LOREG) y aporta suelo, vivienda y financiación para el reasentamiento. Contener el crecimiento demográfico reduce la presión sobre los bordes con riesgo.
- **DPNG.** Autoriza cualquier obra en el Parque Nacional (interceptor, desarenadores) y cualquier descarga en la Reserva Marina. No puede ceder suelo del Parque para reasentar.
- **MAATE.** Ejerce el dominio hídrico público sobre los cauces naturales (Ley de Recursos Hídricos, art. 10) y otorga el licenciamiento ambiental.

**Lo que no se puede saber con estos datos.** Las cotas reales de calles, bordillos y plantas bajas, la existencia y la capacidad de sumideros y pasos bajo las vías, los sótanos y los muros que cortan el flujo, la fecha de la expansión urbana y la lámina real del evento. Con un catastro, la red pluvial levantada y topografía de 0,5 m, las cifras de esta sección podrían cambiar sustancialmente.
