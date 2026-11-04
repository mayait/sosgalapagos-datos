# Cómo se prepara y se publica /estudios

> **Desde el 4-nov-2026, [sosgalapagos.org/estudios](https://sosgalapagos.org/estudios/) (alias `/informes`) publica solo la lista de informes técnicos en PDF** (`informes/`, `servidores/publicar.sh estudios`). El sitio web de estudios que describe este documento (mapa, 3D, comentarios) ya no se publica. Sus textos, datos y figuras siguen aquí y alimentan los informes. El flujo incremental y la revisión automática siguen valiendo para regenerar datos y figuras.

Este documento explica cómo pasa un cambio (datos nuevos, un análisis rehecho o un texto corregido) a [sosgalapagos.org/estudios](https://sosgalapagos.org/estudios/). Responsable: **Julián Maya**.

El sitio se genera aquí, en local, y se sube tal cual al servidor. Nadie edita a mano lo que se publica: todo sale de los textos (`estudios/<isla>/texto/*.md`), de `estudios/estudios.json` y de los datos y figuras que producen los scripts.

## 1. Quién hace qué

| Papel | Quién | Qué hace |
|---|---|---|
| Responsable | Julián Maya | Decide qué se publica y cuándo, aprueba la revisión y ejecuta la publicación (`servidores/publicar.sh estudios`). Abre y cierra los issues de pendientes. |
| Asesor de producción | Agente coordinador (o quien Julián designe) | Corre el flujo incremental, prepara el sitio en local, pasa el checklist, reúne los cambios para la revisión y propone issues nuevos. No publica. |
| Agentes o especialistas temáticos | Hidrología, meteorología, gestión de riesgos, urbanismo | Cambian solo los scripts y textos de su tema. Si cambian una cifra o una conclusión, lo dicen en el commit. |
| Revisor independiente | Un agente o una persona que **no** escribió el cambio | Lee el diff y el sitio generado y da su visto bueno o pide cambios (sección 4). |
| Revisión automática | `scripts/revisar_publicacion.py` | Comprueba lo que se puede comprobar con un programa (sección 3). Si falla, no se publica. |

## 2. Del dato nuevo al sitio: el flujo incremental

Cuando entra un dato nuevo (lluvia en `clima/datos/`, un DEM nuevo, capas nuevas, un issue nuevo), **no se rehace todo a mano**: el flujo incremental rehace solo lo que depende de ese dato y termina regenerando el sitio.

El grafo está en `geodatos/flujo.toml`. Cada paso declara su script, lo que lee y lo que escribe. `scripts/flujo.py` compara el contenido de cada entrada con el de la última corrida (`geodatos/.flujo/`, local y fuera de git) y rehace, en orden, los pasos afectados.

```bash
cd geodatos
.venv/bin/python -I scripts/flujo.py --marcar              # solo la primera vez en esta copia del repositorio
.venv/bin/python -I scripts/flujo.py --seco                # qué se rehace y por qué, sin ejecutar nada
.venv/bin/python -I scripts/flujo.py --seco --cambio ../clima/datos/ierse-wsn/serie_5min.csv.gz   # «¿qué pasa si…?»
.venv/bin/python -I scripts/flujo.py                       # rehace lo afectado (sin pesados ni descargas)
.venv/bin/python -I scripts/flujo.py --red                 # además baja los issues de GitHub y la lluvia de modelos
.venv/bin/python -I scripts/flujo.py --pesados             # además corre el modelo 2D si le toca (minutos)
.venv/bin/python -I scripts/flujo.py --grafo               # el grafo en Mermaid
```

- Los pasos **pesados** (modelo 2D) solo corren con `--pesados` o `--solo <paso>`. El contraste con ANUGA es **manual**: solo con `--forzar modelo2d_santa_cruz_anuga`.
- Si rehaces un paso a mano, márcalo después: `flujo.py --marcar <paso>`.
- Si añades un script, declara en `flujo.toml` sus entradas y salidas, y comprueba con `--seco` dónde queda en el grafo.
- La última etapa del flujo es siempre la revisión automática (`revision`).

Cuando un dato nuevo cambia una cifra que aparece en un texto, la revisión automática falla en «cifras» y dice qué texto quedó desactualizado. **El texto lo corrige el especialista del tema**, no el flujo: una cifra nueva puede cambiar una conclusión.

## 3. Checklist antes de publicar

`publicar_estudios.sh` corre la revisión automática después de generar el sitio y **antes** del `rsync`. Si hay un ERROR, no se publica. También se puede correr sola:

```bash
.venv/bin/python -I scripts/revisar_publicacion.py              # checklist local
.venv/bin/python -I scripts/revisar_publicacion.py --externos   # además, enlaces externos (necesita red)
```

| Qué se comprueba | Cómo | Si falla |
|---|---|---|
| El sitio está al día con sus fuentes | Automático (frescura) | Corre `flujo.py` o `19_estudios_web.py` |
| Enlaces internos, anclas, imágenes, capas del mapa y vista 3D | Automático (enlaces). Externos con `--externos` | Corrige la ruta en el texto o en `estudios.json` |
| Cifras de los textos frente a los datos | Automático para las cifras de `estudios/cifras_clave.json`; **el resto lo revisa el revisor** | El especialista actualiza el texto; si cambió la redacción, actualiza el patrón en `cifras_clave.json` |
| Ni URL ni endpoints de IERSE; ni ids ni endpoints de WeatherLink o Tempest | Automático: busca los valores de `clima/privado/` (sin imprimirlos) en lo publicado y en lo versionado, más patrones genéricos | Quita el valor. Si llegó a un commit, avisa a Julián: hay que limpiar el historial y cambiar la credencial |
| «Refugio», nunca «albergue» | Automático en páginas y textos; aviso en datos descargables | Cambia la palabra (en datos heredados: issue #44) |
| «Preliminar» solo en la etiqueta «Datos preliminares» | Automático | Reescribe la frase |
| Sin recomendaciones en voz de la universidad | Automático para las fórmulas claras («recomendamos», «se recomienda», «la USFQ propone»); **el revisor lee el tono** | Reescribe como riesgo u observación, o atribuye la medida a quien la propone (p. ej., el plan de la UGR) |
| Sin datos personales | Automático: correos, teléfonos, cédulas y campos de contacto en páginas, capas y descargas. Los buzones institucionales (p. ej., `datazone@…`) dan aviso | Quita el dato o depúralo en el script que lo produce |
| Pie «Responsable: Julián Maya» y etiqueta en cada página | Automático | Revisa `19_estudios_web.py` |
| Página de pendientes al día con los issues | Automático (aviso si la caché tiene más de 3 días) | `flujo.py --red` |
| Lo publicado corresponde a un commit | Automático (aviso; error con `--estricto`). `servidores/publicar.sh` exige además `main` y el árbol limpio | Haz commit antes de publicar |
| Modelo ≠ dato oficial; se dice en cada mapa y texto | **Revisor** | Añade la advertencia |
| Figuras legibles, mapa y vista 3D que cargan, comentarios que funcionan | **Revisor**, con el visor local (`scripts/servir.sh`) | — |

## 4. Revisión independiente

La hace alguien que no escribió el cambio. Recibe: el diff (`git diff main…rama -- geodatos/estudios geodatos/scripts`), la salida de `revisar_publicacion.py` y la lista de páginas que cambiaron.

El revisor comprueba, como mínimo:

1. Que cada cifra nueva o cambiada sale de un dato del repositorio, y que el texto y los datos dicen lo mismo.
2. Que las conclusiones no cambian sin que lo diga el commit, y que la confianza declarada (alta, media, baja) sigue siendo coherente.
3. El tono: riesgos y observaciones, no recomendaciones de la universidad; lenguaje llano; «modelo» frente a «dato oficial».
4. Que no hay datos personales en textos, figuras ni descargas.
5. El sitio generado en el navegador (mapa, 3D y una figura por página).

El visto bueno queda en el mensaje del commit con una línea `Revisado-por: <nombre o agente>`. Si pide cambios, se corrigen y se vuelve a revisar.

## 5. Commit y publicación

1. Trabaja en una rama. Mensaje: `tipo(ámbito): descripción` (p. ej., `feat(estudios): …`, `fix(estudios): …`), con la identidad de git de quien trabaja y la línea `Revisado-por:`.
2. Fusiona en `main`.
3. Publica desde `main` y con el árbol limpio (solo Julián o con su autorización):

   ```bash
   servidores/publicar.sh estudios
   ```

   Esto llama a `geodatos/scripts/publicar_estudios.sh`, que: rehace las páginas de pendientes desde la caché, genera el sitio, corre la revisión automática y, solo si pasa, sube `publicar/estudios/` con `rsync`.

## 6. Verificación en producción

Justo después de publicar:

```bash
.venv/bin/python -I scripts/revisar_publicacion.py --produccion   # cada página de producción = la de publicar/estudios
curl -sI https://sosgalapagos.org/estudios/ | head -1
```

`--produccion` descarga cada página y la compara con la local (ignora la baliza que añade Cloudflare). También muestra el `version.txt` que deja `servidores/publicar.sh`. Después, en el navegador: el índice de cada isla, una página con mapa, la vista 3D y un comentario de prueba (bórralo luego).

## 7. Pendientes y preguntas abiertas

Los pendientes viven **solo como issues** de [mayait/sosgalapagos-datos](https://github.com/mayait/sosgalapagos-datos/issues). La página `/estudios/<isla>/pendientes/` se genera a partir de ellos:

- `scripts/22_pendientes.py --actualizar` baja los issues con `gh` a `estudios/pendientes.json` (caché versionada, para generar el sitio sin red). `flujo.py --red` lo hace por ti.
- `scripts/22_pendientes.py` escribe `estudios/pendientes/<isla>.md`. **No se editan a mano.**
- Se agrupan por etiqueta (`datos-faltantes`, `mas-resolucion`, `procesos`, `gobernanza`) y por isla. La isla sale de las etiquetas `santa-cruz` o `san-cristobal` (`todas-las-islas` para las comunes) o, si no las hay, de los topónimos del issue. Los de `plataforma` no se listan: son tareas internas.
- Para añadir un pendiente, abre un issue con título claro, un cuerpo breve (qué falta, quién lo tiene, para qué sirve) y sus etiquetas. Lenguaje llano: son preguntas y vacíos de información, no recomendaciones. La página cambia «preliminar» por «provisional» y «albergue» por «refugio», pero es mejor no usarlas en el issue.
- Cuando un texto nuevo plantea una pregunta abierta («qué falta saber», «por verificar en campo», «no concluyente», «hipótesis»), el asesor de producción propone el issue y Julián lo abre.
