# Resumen ejecutivo

**Pregunta.** ¿Es posible desviar las quebradas que bajan hacia el barrio La Cascada (Puerto Ayora, Santa Cruz)? ¿Cuál es el problema de fondo y qué se puede hacer, también desde lo urbano?

**Cómo se respondió.** Con un análisis topográfico e hidrológico de reconocimiento que usa estas fuentes:
- el modelo de superficie Copernicus GLO-30, de 30 m;
- la cartografía del IGM 1:25 000;
- OSM, INEC, SNGR y CGREG;
- la lluvia estimada por modelos meteorológicos.

El análisis lo hizo un comité de agentes de IA especializados en hidrología, meteorología, gestión del riesgo y planificación urbana, con revisión cruzada y una revisión científica independiente. Todo el cálculo es reproducible.

## Hallazgos principales

1. **El problema es sobre todo la forma del terreno.**
   - La Cascada recibe el agua de **42 km²**, casi toda la cuenca de Puerto Ayora. El agua entra por dos quebradas que bajan el escarpe por el norte y el noroeste.
   - El barrio ocupa un **vaso cerrado al pie de escarpes**. El fondo está a ≈10,5 m y el agua rebosa entre 12,0 y 12,95 m (cota del DSM; sin precisión GNSS).
   - El vaso almacena solo **42 000–62 000 m³**. Con el método SCS-CN y sin pérdidas en los cauces, **bastan unos 25–50 mm de lluvia sobre suelo húmedo para llenarlo**. Una lluvia de 100 mm genera de 13 a 50 veces su volumen.
   - Por eso la altura del agua en el barrio depende de **cuánta agua puede salir**, no de cuánta cabe.
2. **El agua no tiene por dónde salir.**
   - La quebrada cartografiada pasa a 28 m del borde norte del barrio. **Entre el barrio y el mar no hay ningún cauce cartografiado.**
   - La salida natural recorre 1,2 km hasta el mar con ≈1 % de pendiente. Pasa sobre 28 edificaciones y tiene 16 cruces de vías.
   - Según la prensa (2023, por verificar), Santa Cruz no tiene alcantarillado pluvial.
   - La franja de protección de quebradas del CGREG no tiene ningún polígono en Puerto Ayora.
3. **La lluvia del evento solo se conoce por modelos.**
   - No hay medición pública del 30–31 de octubre.
   - El modelo de mayor resolución (ECMWF, 9 km) estima **≈81 mm en la costa y ≈130 mm en la parte alta** el 31 de octubre, con el máximo hacia las 05:00–06:00 (hora de Galápagos). Los demás modelos dan entre **0,2 y 26 mm**.
   - La SNGR sitúa las lluvias fuertes antes, en la tarde y la noche del 30.
   - La media de octubre en Puerto Ayora es de 10,9 mm.
   - En los Niños de 1982–83 y 1997–98, la lluvia fuerte empezó en noviembre o diciembre y duró hasta junio. Por analogía, que no es un pronóstico, este evento podría ser un adelanto de la temporada.
4. **La lámina observada es compatible con el análisis, pero no lo valida.**
   - El único testimonio con fuente habla de agua «hasta dos metros», es decir, una cota de ≈12,5–13 m: el vaso lleno hasta su rebose.
   - Hasta esa cota, dentro del vaso, quedan **68–204 edificios y unas 400–910 personas** (llenado estático del DSM).
   - Las cifras de «3 m» y «800 familias» que circularon **no tienen fuente verificable**.
5. **Desviar las quebradas hacia el este no es descartable, pero no está demostrado.**
   - Según el DSM de 30 m, un interceptor a ≈40 m sobre el borde del escarpe captaría el 99 % de la cuenca y bajaría por gravedad 3,5 km hasta el mar sin cruzar viviendas.
   - Pero en sus primeros 2,5 km la pendiente es del orden del error del modelo (±2 m).
   - Como canal real, de 2,5–3 m de profundidad, iría **en terraplén de hasta 3,5–4 m durante más de 2 km sobre el escarpe**, justo encima del barrio, o exigiría excavar de media 3–3,6 m en basalto.
   - Estaría **íntegramente en el Parque Nacional** y desembocaría en la Reserva Marina.
   - **Hacia el oeste no es viable.**
   - El cauce que OSM dibuja hacia el este no llega al mar: para seguirlo, el agua tendría que subir hasta ≈37 m.
6. **No es posible avisar con mucha antelación.**
   - Una crecida generada en Bellavista tarda 1–2,5 h en llegar al barrio, y desde el borde del escarpe, minutos.
   - El aviso debe basarse en la **lluvia medida en la parte alta**, no en el nivel del agua.

> **Conclusión.** La medida que más reduce el riesgo a corto plazo no es el desvío. Lo que más lo reduce es **dar salida al agua a través de la ciudad, dejar de aumentar la exposición en la zona baja y medir la lluvia**. El desvío al este debe estudiarse como una alternativa entre otras, con topografía de detalle y un modelo 2D, junto con la DPNG y el MAATE. Ninguna obra sustituye al sistema de alerta ni a la regulación del suelo.

## Recomendaciones prioritarias

Tabla: Recomendaciones por horizonte temporal.

| Horizonte | Acción | Responsable principal |
|---|---|---|
| **Días** | Levantar con GNSS las marcas de agua y los daños por vivienda antes de que se borren. Medir con GNSS la cota real del rebose | GAD, con la academia y la sociedad civil |
| **Días** | Limpiar los sumideros y liberar la desembocadura. Designar refugios fuera de las depresiones: el Coliseo no sirve para esta amenaza | GAD, COE cantonal |
| **Días** | Pedir la lluvia medida a la FCD y al INAMHI. Descargar GPM IMERG | Academia |
| **Semanas** | Moratoria de permisos en la zona baja y en la franja de 30 m del cauce natural. Prohibir sótanos. Fijar los umbrales de cota respecto al rebose medido con GNSS, no con el DSM | GAD municipal |
| **Semanas** | Instalar tres pluviómetros telemétricos (cabecera, Bellavista y Puerto Ayora) con umbrales provisionales, y hacer un simulacro | SNGR, INAMHI, GAD, FCD |
| **Semanas** | Volar con dron o LiDAR 5–10 km² del escarpe, el barrio y el corredor este | GAD, CGREG |
| **Meses** | Modelo hidrológico calibrado (HEC-HMS) y modelo 2D que compare las alternativas | GAD, CGREG, academia |
| **Meses** | Diseñar la calle-canal y el colector de Marchena. Elaborar el mapa oficial de amenaza | GAD, SNGR |
| **Años** | Según lo que concluya el estudio: interceptor al este (con la DPNG y el MAATE), parque inundable y reasentamiento voluntario de las viviendas más bajas | GAD, CGREG, DPNG, MAATE |
