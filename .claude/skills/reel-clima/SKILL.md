---
name: reel-clima
description: Genera el reel vertical del clima de Galápagos (un video de 10 segundos por día, con el mapa de lluvia y viento animado, la hora de más lluvia en cada isla, la marea y la lluvia ya medida) con el pronóstico más reciente de sosgalapagos.org. Úsalo cuando pidan un reel, un video, una story o una pieza para redes del pronóstico del clima de ciertos días.
---

# Reel del clima de Galápagos

Todo está en [`clima/reel/`](../../../clima/reel/). Un solo comando, `reel.py`, baja los datos, arma una página por día, la graba cuadro a cuadro con Chrome y la convierte en video.

## Qué sale

Para `--dias 2026-11-25 2026-11-26`, en la carpeta de salida:

| Archivo | Qué es |
|---|---|
| `mie25.mp4`, `jue26.mp4` | Un video por día: 1080 × 1920, 30 cuadros por segundo, 10,7 s, H.264, sin sonido |
| `mie25.png`, `jue26.png` | La imagen fija de cada día, a la hora de más lluvia (sirve de portada o de story) |
| `reel-mie-jue.mp4` | Los días seguidos, en un solo video |

La carpeta de salida es `~/Downloads/sosgalapagos-reel-<primer día>/` si no se indica otra con `--salida`.

Cada pieza tiene, de arriba abajo: la dirección del sitio, una etiqueta («HOY»), el día, una frase, el mapa animado con el reloj, «¿A qué hora llueve más en cada isla?», la marea, «Ya llovió en 7 días» y el aviso de que no es un pronóstico oficial. Es la versión que aprobó Julián el 23-nov-2026: en dos dimensiones, **sin porcentajes**, y la marea se titula solo «MAREA».

## Qué necesita

- `python3` (3.9 o posterior), sin paquetes;
- Node 22 o posterior (usa su WebSocket incorporado);
- Google Chrome (si no está en la ruta habitual, pon la suya en la variable `CHROME`);
- `ffmpeg` y `ffprobe` (`brew install ffmpeg`);
- internet: los datos se piden a sosgalapagos.org y la página carga Leaflet desde cdnjs.

`reel.py` comprueba todo esto y dice qué falta. No necesita claves ni nada de `clima/privado/`.

## Pasos

Corre todo desde la raíz del repositorio. Usa una misma carpeta de trabajo en los cuatro pasos, para que el video salga de los mismos datos que revisaste (tu carpeta temporal de la sesión sirve).

### 1. Baja los datos y léelos

```bash
python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26 --trabajo <carpeta> --solo-datos
```

Imprime de qué hora es el pronóstico, la corrida del modelo, la señal de lluvia fuerte y la hora de más lluvia en cada isla, las mareas y la lluvia medida. Si los datos no cubren un día, lo dice con `PROBLEMA` y se detiene.

- Los días van como `AAAA-MM-DD`; también valen `hoy` y `mañana` (hora de Galápagos, UTC−6).
- **Alcance: hoy, mañana y pasado mañana.** La curva de marea del sitio llega hasta unas 72 horas.
- Baja siempre datos nuevos justo antes de grabar. El mapa del sitio se rehace varias veces al día.

### 2. Escribe la etiqueta y la frase de cada día

Copia [`clima/reel/textos.ejemplo.json`](../../../clima/reel/textos.ejemplo.json) a la carpeta de trabajo y cámbialo. Si no pasas `--textos`, `reel.py` pone una etiqueta («HOY», «MAÑANA» o «PRONÓSTICO») y una frase sacada de la señal del panel. Casi siempre conviene escribirlas.

- **Etiqueta** (`chip`): dos o tres palabras en mayúsculas. «HOY», «MAÑANA», «SIGUE LA LLUVIA», «DÍA PICO». En rojo (`"rojo": true`) solo el día que pide más cuidado, y como mucho uno por reel.
- **Frase** (`frase`): una línea de hasta unos 55 caracteres, en español llano, que diga qué trae el día. Sale del resumen del paso 1, no de la intuición.
- **No pongas** porcentajes, «riesgo alto» ni «alerta» (Julián lo pidió: preocupa más de lo que informa). Tampoco nada que suene a aviso oficial.
- `nota_lluvia` cambia la nota del bloque «Ya llovió en 7 días». Por defecto dice «suelo saturado» cuando alguna estación pasa de 200 mm en 7 días, y nada si no.

### 3. Mira una imagen de prueba

```bash
python3 -I clima/reel/reel.py --dias 2026-11-25 2026-11-26 --trabajo <carpeta> --datos <carpeta>/datos --textos <carpeta>/textos.json --prueba
```

Tarda unos segundos y deja `revision/prueba_<día>.png`. Ábrelas y revísalas con la lista de abajo antes de grabar.

### 4. Graba

El mismo comando sin `--prueba` (y con `--salida` si no va a Descargas). Graba los días a la vez, cada uno en su Chrome sin ventana: alrededor de un minuto para dos o tres días. Al terminar imprime las medidas de cada video (`bien` o `REVISAR`) y deja cuadros sueltos sacados de los videos ya hechos en `<carpeta>/revision/`.

### 5. Revisa los cuadros, siempre

Abre los `.jpg` de `revision/` (tres por día y uno del reel completo por cada día) y comprueba:

- **Día y fecha:** el título dice el día de la semana y el número correctos. `reel_dia1.jpg`, `reel_dia2.jpg`… muestran los días en orden.
- **Reloj:** empieza en 00:00 (madrugada) y termina en 24:00 (noche).
- **Sin porcentajes** en ninguna parte (salvo que hayas pedido `--porcentajes`).
- **Marea:** se titula «MAREA», y sus horas y alturas son las del resumen del paso 1.
- **Lluvia medida:** los milímetros coinciden con el resumen, e Isabela dice «sin estaciones».
- **Textos:** en español, con tildes, sin nada cortado ni montado. La frase cabe en su sitio y no toca el mapa.
- **Pie:** está el aviso «No es un pronóstico oficial ni una alerta», y la línea pequeña dice la fecha y la hora del pronóstico.
- **Mapa:** se ven las tres islas con su contorno, la lluvia en color, las rayas del viento y los puntos rojos de los puertos.

Si algo falla, corrige y vuelve a grabar. No entregues un reel que no miraste.

### 6. Informa

Di dónde quedó cada archivo, de qué fecha y hora es el pronóstico (`Pronóstico emitido` y la corrida del modelo) y lo que no pudiste comprobar. Los cuadros se revisan uno por uno; el video en movimiento no, así que dilo.

## Reglas

- **El reel sale de la página, así que siempre dice que no es oficial.** El aviso del pie no se quita ni se achica (AGENTS.md, regla 3).
- **No se publica nada.** El skill deja archivos en la carpeta de salida. Subirlos a redes o al sitio lo decide Julián.
- **Los videos y los cuadros no van al repositorio.** Tampoco los datos bajados. La carpeta de trabajo va fuera del repositorio.
- **Marca:** USFQ Galápagos «We Want More»: solo rojo, negro y blanco, Zalando Sans Expanded y Helvetica Neue. No añadas colores. Nada de morado en textos, marcos ni fondos. Los colores de la lluvia son los del mapa del sitio, salvo la lluvia extrema, que aquí va en rojo oscuro.
- **No inventes datos.** Si una estación no transmite, el bloque dice «sin dato». Si el sitio no trae un día, no se hace ese día.
- Los milímetros del modelo sirven para ver **cuándo** llueve, no **cuánto**: en las islas se quedan muy cortos. Por eso el reel muestra horas y barras, no milímetros de pronóstico.

## Opciones

| Opción | Para qué |
|---|---|
| `--salida <carpeta>` | Dónde dejar los videos y las imágenes |
| `--textos <archivo>` | Etiqueta y frase de cada día |
| `--porcentajes` | La versión anterior, con la probabilidad de 20 mm o más por isla. Solo si la piden |
| `--datos <carpeta>` | Usa datos ya bajados (`estado.json`, `mar.json`, `lluvia-mapa.json`) |
| `--trabajo <carpeta>` | Carpeta de trabajo. Sin ella, crea una temporal y dice cuál |
| `--conservar-cuadros` | No borra los cuadros sueltos (unos 300 MB por día) |

## De dónde sale cada cosa

| En el reel | Dato | Fuente |
|---|---|---|
| Mapa, puntos rojos y barras por isla | `lluvia-mapa.json`: lluvia y viento cada 3 horas, ECMWF IFS de 9 km | Open-Meteo (CC BY 4.0) |
| Marea | Curva de `estado.json` ajustada a las pleamares y bajamares de `mar.json` | Tabla del INOCAR para Puerto Ayora; UHSLC |
| «El mar viene N cm más alto» | Anomalía del mareógrafo de Puerto Ayora, últimas 6 horas | `estado.json` |
| Ya llovió en 7 días | Estación de la parte alta: Miconia en Santa Cruz y El Junco en San Cristóbal. En Isabela no hay | `estado.json` |
| Contorno de las islas | `clima/reel/islas.js`, generado por `islas.py` | IGM |

Los tres JSON son los del panel público de `/clima/`. Cambian de forma sin aviso: si `reel.py` falla al leerlos, mira primero si cambió su estructura.

## Si algo falla

- **`PROBLEMA: el mapa de lluvia no cubre…` o `la curva de marea no cubre…`**: el día queda fuera del alcance. Quita ese día.
- **`la grabación … falló`**: el mensaje trae el registro de Chrome. «sin Chrome» es que no abrió (revisa `CHROME`); «la página no cargó bien» trae el error de la página, casi siempre que no hay internet para cargar Leaflet.
- **`tiempo agotado`**: la máquina va lenta. Sube el límite con `LIMITE=1800` (segundos) delante del comando.
- **Un video sale `REVISAR`**: no tiene 1080 × 1920 o no tiene 321 cuadros. Graba de nuevo con `--conservar-cuadros` y mira la carpeta `cuadros/`.

## Otras versiones

El 23-nov-2026 se probaron también una versión en tres dimensiones (MapLibre con relieve) y unas primeras hechas con matplotlib. Julián las descartó y no están en el repositorio.
