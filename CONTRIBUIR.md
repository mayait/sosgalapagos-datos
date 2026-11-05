# Cómo trabajar en este repositorio (equipos, ramas y agentes)

Aquí trabajan a la vez varias personas y varios agentes de IA (Claude Code y otros), cada uno en su rama. Para que no se pisen, el repositorio separa **qué es de quién**, **qué se edita a mano y qué se regenera**, y **quién publica**.

## 1. Tres tipos de archivo

| Tipo | Ejemplos | Regla |
|---|---|---|
| **Fuente** (se edita a mano) | `geodatos/scripts/*.py`, el manifiesto `geodatos/scripts/capas.json`, `geodatos/capas/operativas/areas_afectadas.geojson`, textos `geodatos/estudios/*/texto/*.md`, `clima/recolector/`, `clima/web/`, documentación | Se cambia en una rama y entra por PR |
| **Crudo externo** (se descarga) | `geodatos/descargas/`, `clima/datos/*/crudos/` | `descargas/` **no** va a git (pesa ~400 MB y trae datos personales). Los crudos de clima sí van a git, **nunca se modifican** y solo se agregan días nuevos |
| **Generado** (lo escribe un script) | `geodatos/capas/{osm,igm,dem,final,raster}/`, `geodatos/export/`, `mapas-galapagos/`, `geodatos/estudios/*/figuras/`, PDF, tablas consolidadas de clima | **Nunca se edita a mano.** Si hay conflicto, se toma la versión de `main` y se vuelve a correr el script |

Cada archivo generado sale de un único script. Si no sabes cuál, búscalo con `grep -rn "nombre_del_archivo" geodatos/scripts clima`.

## 2. Quién es dueño de qué

| Dominio | Carpetas | Comparte con otros dominios |
|---|---|---|
| **Capas base** (geografía) | `geodatos/scripts/01–09`, `geodatos/capas/`, `geodatos/docs/` | `geodatos/scripts/capas.json` (manifiesto) |
| **Publicación de mapas** (servidor) | `geodatos/scripts/10_publicar_web.py`, `visor_mapas.json`, `11_geoserver_local.py`, `publicar_mapas.sh`, `geodatos/web/index.html` | lee `geodatos/export/` |
| **Estudios** | `geodatos/estudios/<estudio>/`, `geodatos/scripts/12–20` y `grd_*.py`, `geodatos/web/estudios.*`, `19_estudios_web.py` | `geodatos/estudios/estudios.json`; lee capas y `clima/datos` |
| **Clima** | `clima/` | sus datos los leen los estudios |
| **Entregable** | `mapas-galapagos/` (lo genera `09_entregable.py`) | — |
| **Servidores** | `servidores/` (índice y publicación) | invoca los scripts de cada dominio |

**Archivos calientes** (los toca casi todo el mundo): `geodatos/scripts/capas.json`, `geodatos/estudios/estudios.json`, y `README.md`. En ellos:
- edita **solo tu bloque** (tu capa, tu estudio, tu fila);
- no reordenes ni reformatees el archivo;
- haz *rebase* sobre `main` justo antes de abrir el PR.

## 3. Qué hay por hacer: issues

Todo lo pendiente está en los [issues del proyecto](https://github.com/mayait/sosgalapagos-datos/issues). Cada uno lleva una etiqueta de prioridad y otra de tipo:
- **P1**: cambia decisiones de esta emergencia. **P2**: mejora mucho el análisis. **P3**: deseable.
- **Tipo**: `datos-faltantes`, `mas-resolucion`, `procesos`, `plataforma` y `gobernanza`.

Antes de empezar, asígnate el issue (o comenta en él) y ponle la etiqueta `en curso`. La rama lleva el número del issue, por ejemplo `datos/12-catastro-santa-cruz`. Si descubres algo nuevo que falta, abre un issue en lugar de anotarlo en un archivo.

## 4. Ramas

```
main                         siempre publicable; solo se despliega desde aquí
├── datos/<capa-o-fuente>     p. ej. datos/catastro-santa-cruz, datos/dtm-dron-puerto-ayora
├── clima/<fuente-o-mejora>   p. ej. clima/inamhi, clima/alertas-lluvia
├── estudio/<nombre>          p. ej. estudio/san-cristobal, estudio/idf-santa-cruz
├── servidor/<servicio>       p. ej. servidor/geoserver-prod (nunca se despliega desde la rama)
└── docs/<tema>
```

- Ramas cortas: un tema por rama y PR en horas o pocos días.
- Un PR **no** incluye regeneraciones masivas ajenas a su tema. Si tu cambio obliga a regenerar `export/` o `mapas-galapagos/`, dilo en el PR. Esa regeneración la hace quien integra, en `main`, después del merge.
- Commits en español, con el estilo `tipo(ámbito): descripción` y estos ámbitos: `geodatos`, `clima`, `estudios`, `servidores`, `docs`. Ejemplo: `feat(clima): fuente INAMHI con historial de 90 días`.
- Autor de los commits: la identidad de git de cada persona. Los agentes que trabajan para Julián usan `Julian Maya <1101119+mayait@users.noreply.github.com>`.

## 5. Trabajar en paralelo con *worktrees* (recomendado para agentes)

Cada tarea va en su propia carpeta, sobre su propia rama, sin tocar la copia principal:

```bash
cd ~/dev/sosgalapagos-datos
git worktree add ../sosgalapagos-datos--estudio-idf -b estudio/idf-santa-cruz
cd ../sosgalapagos-datos--estudio-idf
# Comparte lo pesado con la copia principal, solo para leer:
ln -s ~/dev/sosgalapagos-datos/geodatos/descargas geodatos/descargas
ln -s ~/dev/sosgalapagos-datos/geodatos/.venv     geodatos/.venv
ln -s ~/dev/sosgalapagos-datos/clima/.venv        clima/.venv
```

- `descargas/` compartida se usa **solo para leer**. Para volver a descargar una fuente (scripts 01, 02 y 04), hazlo en la copia principal o en una carpeta propia.
- Al terminar: PR, merge y `git worktree remove ../sosgalapagos-datos--estudio-idf`.
- Si dos agentes van a tocar el mismo archivo caliente, se coordinan antes. Entre sesiones de Claude Code se usa `SendMessage`.

## 6. Recetas

### Añadir una capa nueva
1. Script que la descarga o la calcula. Para el proceso base, usa el siguiente número libre. Para un tema concreto, usa un nombre propio (`grd_*.py`, `est_<estudio>_*.py`). No reutilices un número que ya existe.
2. La salida va a `geodatos/capas/<fuente>/`, en **EPSG:4326** y con propiedades en español `snake_case`.
3. Regístrala en el manifiesto `geodatos/scripts/capas.json` (grupo, estilo, fuente, `visible`).
4. Documenta la fuente, la fecha y la licencia en `geodatos/docs/fuentes-oficiales.md`. Si es un modelo propio, explica el método en `mapas-galapagos/documentacion/02-metodologia.md`.
5. **Datos personales:** quita nombres, teléfonos y cédulas antes de guardar en `capas/`. Lo crudo se queda en `descargas/`.
6. Cierra o abre el issue que corresponda (menciónalo en el PR con `Cierra #N`).

### Actualizar las áreas afectadas (lo más frecuente)
Ver `geodatos/docs/05-como-actualizar.md`, apartado A. Se reemplaza `geodatos/capas/operativas/areas_afectadas.geojson` y se publica.

### Añadir una fuente meteorológica
1. `clima/datos/<fuente>/crudos/`: tal cual llega, con un archivo por día y sin correcciones.
2. Una función `fuente_<nombre>()` en `clima/recolector/recolector.py`, con las horas en UTC.
3. **Los endpoints van solo en `clima/privado/`**, que no se versiona. En el repositorio y en la web se nombra la fuente, pero sin enlaces.
4. Antes de mostrar una fuente nueva en el panel público, hay que preguntar a Julián.

### Añadir o actualizar un estudio
1. Carpeta `geodatos/estudios/<slug>/` con `texto/`, `datos/` y `figuras/`.
2. Entrada en `geodatos/estudios/estudios.json`.
3. Scripts propios. Las figuras y el PDF se generan, no se editan a mano.
4. Todo estudio dice que es **preliminar** y distingue el **dato medido** del **modelo**.

## 7. Publicar

Solo desde `main`, con el árbol limpio y por quien tenga acceso al servidor:

```bash
servidores/publicar.sh mapas      # sosgalapagos.org/mapas/
servidores/publicar.sh clima      # sosgalapagos.org/clima/ (recolector y panel)
```

El script se niega a publicar fuera de `main` o con cambios sin commit. En el servidor deja un `version.txt` con el commit publicado. Detalles en [servidores/README.md](servidores/README.md).

## 8. Antes de abrir un PR

- [ ] Corrí los scripts de mi dominio y funcionan desde cero.
- [ ] No subo `descargas/`, `.venv/`, `privado/`, credenciales ni bases SQLite.
- [ ] No hay datos personales (nombres, teléfonos, cédulas) ni URLs de fuentes de clima.
- [ ] Los generados que subo salen del script, no de ediciones a mano.
- [ ] Actualicé la documentación y enlacé el issue (`Cierra #N`).
- [ ] Se dice «refugio», nunca «albergue».
