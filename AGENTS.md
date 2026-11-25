# Instrucciones para agentes (Claude Code, Codex y otros)

Lee primero [README.md](README.md) (qué hay) y [CONTRIBUIR.md](CONTRIBUIR.md) (cómo se trabaja). Este archivo resume las reglas que **no** se pueden romper.

## Reglas duras

1. **Repositorio público.** Nunca subas:
   - `geodatos/descargas/` (trae nombres y teléfonos de fuentes oficiales);
   - `.venv/`, `clima/privado/`, bases SQLite (`*.db`) ni credenciales;
   - **URLs o endpoints de las fuentes meteorológicas**. Solo se nombran: «IERSE», «USFQ GSC», «INAMHI». Los endpoints viven en `clima/privado/`.
2. **Datos personales:** las capas oficiales (SNGR, MSP) traen nombres y teléfonos. Se depuran en el script, por ejemplo en `07_oficiales.py`. Nunca publiques nombres de personas afectadas.
3. **Modelo ≠ dato oficial, dicho una vez.** La susceptibilidad HAND, las cuencas, la costa baja y las lluvias de modelos son estimaciones propias, nunca datos oficiales.
   - **En la web** lo dice **un solo aviso general por página**: el del menú del sitio. Los boletines oficiales van en su propia sección («Boletines oficiales»). No se ponen sellos ni frases de «no oficial», «estimación» o «experimental» en cada tarjeta (decisión de Julián, 23-nov-2026).
   - **En las tarjetas** solo van las advertencias que **informan**: cuánto subestima un modelo, qué no ve el satélite, cuándo puede fallar un pronóstico, «para navegar, Capitanía de Puerto».
   - **Lo que sale de la página** sí lo dice siempre: fichas, PDF, capas descargables y mensajes que se comparten por WhatsApp.
4. **No edites archivos generados a mano.** Corre el script que los produce (ver CONTRIBUIR §1).
5. **No despliegues** a `sosgalapagos.org` si no te lo piden, y solo desde `main` (`servidores/publicar.sh`).
6. **Informes y textos de estudios son solo locales.** `informes/` y `geodatos/estudios/*/{texto,figuras}/` (y sus PDF) están en `.gitignore`: no se suben al repositorio ni se publican en la web. Los datos de los estudios sí se versionan. **Única excepción (desde el 21-nov-2026):** los mapas e informes en PDF que Julián pida publicar uno por uno van a la sección de descargas de la portada con `servidores/publicar.sh descargas`. Siguen fuera de git y nunca se publica uno que él no haya pedido.
7. **Trabaja en tu rama** (mejor en un *worktree*) y no toques el dominio de otra sesión sin coordinarlo. Entre sesiones de Claude Code: `ListAgents` y `SendMessage`.

8. **Licencia (desde el 23-nov-2026).** El código va bajo Apache 2.0 ([`LICENSE`](LICENSE) y [`NOTICE`](NOTICE)); lo propio que no es código va bajo CC BY 4.0 y lo de terceros conserva su licencia, que prevalece ([`LICENCIA-DATOS.md`](LICENCIA-DATOS.md)). Crédito: «SOS Galápagos · Universidad San Francisco de Quito (USFQ) · Julián Maya <jamaya@usfq.edu.ec>». Del 22 al 23-nov-2026 rigieron derechos reservados y CC BY-NC-ND 4.0. Cada archivo de código propio (`.py`, `.sh`, páginas) empieza con el aviso de autoría de dos líneas (USFQ · SOS Galápagos · Julián Maya): ponlo en los archivos nuevos y no lo quites. Donde se muestre o se descargue un dato de terceros, se nombra su licencia.

## Convenciones

- Idioma: español claro. En SOS Galápagos se dice **«refugio»**, nunca «albergue».
- Commits: `tipo(ámbito): descripción`, sin líneas `Co-Authored-By`. Usa la identidad de git de quien trabaja; los agentes de Julián usan `Julian Maya <1101119+mayait@users.noreply.github.com>`.
- Python: `geodatos/.venv/bin/python -I scripts/…` (`-I` aísla el intérprete). Dependencias en `geodatos/requirements.txt`. `pysheds` necesita `numpy < 2.4`.
- Coordenadas: EPSG:4326. Horas: se guardan en UTC. Galápagos está en UTC−6. INAMHI y GSC usan la hora continental (UTC−5), aunque marquen «Z». IERSE usa UTC−6. Open-Meteo devuelve UTC−5 si se pide `America/Guayaquil`.
- En la Mac no hay Docker: los contenedores se corren con `container` (Apple).
- El DSM Copernicus tiene un sesgo de −2 a −3 m frente al IGM. No uses sus cotas absolutas como umbrales.
- En Santa Cruz (Puerto Ayora, escarpe y Bellavista) el relieve es el **DTM de 1 m de la SGIAR** fusionado con el Copernicus (`relieve_sgiar.py`, `03_dem.py`). Cita siempre «DTM 1 m: SGIAR (Vricon/Maxar)». Sus cotas quedan ≈ 1–3 m sobre las del Copernicus (≈ 3 m en La Cascada): nunca mezcles umbrales de un relieve con el otro.

## Mapa rápido

| Quiero… | Voy a… |
|---|---|
| Entender una capa | `mapas-galapagos/documentacion/01-catalogo-de-capas.md` y `02-metodologia.md` |
| Saber de dónde sale un dato | `geodatos/docs/fuentes-oficiales.md` |
| Entender el modelo HAND | `docs/modelo-hand.md` |
| Ver qué falta | [Issues del proyecto](https://github.com/mayait/sosgalapagos-datos/issues) (etiquetas P1–P3 y por tipo) |
| Publicar o tocar un servidor | `servidores/README.md` |
| Rehacer los estudios tras un dato nuevo | `geodatos/flujo.toml` + `geodatos/scripts/flujo.py --seco` |
| Bajar los datos del clima o reproducir sus cálculos | `clima/PARA-AGENTES.md` (ZIP con todo, formato, trampas) y `clima/replicar/nivel.py` (sin dependencias) |
| Tocar el clima | El que corre en vivo: repo `sosgalapagos-plataforma`, app `clima/`. Aquí: el panel (`clima/web/`) y los análisis (`clima/LEEME.md`) |
| Tocar el pronóstico de lluvia | `clima/pronostico/LEEME.md` (evaluación en `fase0/informe.md`) |
| Hacer un reel o un video del pronóstico del clima | Skill `reel-clima`: [`.claude/skills/reel-clima/SKILL.md`](.claude/skills/reel-clima/SKILL.md) (los scripts están en `clima/reel/`) |

## Árbol de repositorios de SOS Galápagos

**Estás en:** `sosgalapagos-datos`. Los datos, el clima y los modelos. La plataforma vive en otro repositorio.

<!-- arbol-repos:inicio -->
> **Este bloque es idéntico en los repositorios activos** (en su `AGENTS.md`). Si cambias algo, cámbialo en todos. Última revisión: 2026-11-24 (ResponseGrid retirado: la portada «/» y el Caddy pasan a `sosgalapagos-plataforma`; `mayait/sosgalapagos` queda archivado. Apache 2.0 y CC BY 4.0 en `sosgalapagos-datos` y `sosgalapagos-plataforma`; el mapa único es `/riesgos/`; todo el clima corre en `sosgalapagos-plataforma`).

SOS Galápagos son varios repositorios, todos en la cuenta `mayait` de GitHub (no hay organización). En la Mac de Julián cada uno se clona en `~/dev/<nombre>`.

| Repositorio | Visibilidad | Qué contiene | Qué publica |
|---|---|---|---|
| [`sosgalapagos-plataforma`](https://github.com/mayait/sosgalapagos-plataforma) | público | **El sitio**: la portada, el mapa de riesgos (reportes ciudadanos con vencimiento sobre las capas de riesgo, buscador, descargas, línea del tiempo), la privacidad y todo el clima (un solo stack desde el 22-nov-2026). Django + PostGIS. También guarda el **Caddy** del servidor (`despliegue/sitio/`). Código Apache 2.0; datos propios CC BY 4.0. | `sosgalapagos.org/`, `/riesgos/`, `/privacidad` |
| [`sosgalapagos-datos`](https://github.com/mayait/sosgalapagos-datos) | público | Geodatos, estudios de riesgo, modelos y el panel de `/clima/`. Su carpeta `servidores/` es el índice de qué corre dónde. Código Apache 2.0; datos propios CC BY 4.0. | Los datos de `/mapas/…` (capas y descargas, sin visor), `/estudios/`, `/descargas/` y la página de `/clima/` |
| [`estudiantes-riesgo-nino`](https://github.com/mayait/estudiantes-riesgo-nino) | **privado** | Viviendas de estudiantes de USFQ Galápagos cruzadas con el riesgo de inundación. Tiene datos personales. | `/usfq/`, con contraseña |
| [`sosgalapagos-bot`](https://github.com/mayait/sosgalapagos-bot) | **privado** | Asistente de WhatsApp de la etapa anterior: creaba pedidos en la API de ResponseGrid, que ya no existe. No corre. El WhatsApp vivo está en la plataforma (`entradas/`). | Nada |
| [`sosgalapagos`](https://github.com/mayait/sosgalapagos) | público, **archivado** | El fork de ResponseGrid (AGPL-3.0): la antigua plataforma de coordinación. Retirado el 24-nov-2026; sus contenedores están detenidos y su base, respaldada. | Nada (`/backend` responde 410) |
| [`RESPONSEGRID_GALAPAGOS`](https://github.com/mayait/RESPONSEGRID_GALAPAGOS) | público | Carpeta de trabajo local de la etapa anterior. Conserva la historia de geodatos hasta el 2-nov-2026. | Nada |

```
                    sosgalapagos.org (un solo servidor, detrás de Cloudflare)
                                     │
        Caddy: sosgalapagos-plataforma → despliegue/sitio/ (proyecto Compose «sosgalapagos»)
     ┌─────────────────────────────┬───────────────────────────────┬──────────────────────┐
     │ /  /riesgos/  /privacidad   │ /mapas/… /clima/ /estudios/   │ /usfq/ (contraseña)  │
     ▼                             │ /descargas/                   ▼                      │
 sosgalapagos-plataforma           ▼                         estudiantes-riesgo-nino     │
 (portada, mapa, clima)      sosgalapagos-datos              (privado)                   │
     ▲  lee capas.json,      (datos y modelos)                    ▲                      │
     └───────────────────────────┴────────────────────────────────┘ capas de geodatos   │
```

### Cómo dependen unos de otros

1. **Las rutas del servidor se definen en `sosgalapagos-plataforma`** (`despliegue/sitio/Caddyfile`). Caddy pasa «/», `/riesgos/` y `/privacidad` a la plataforma, y sirve las carpetas que publican los demás: `/srv/sosgalapagos-mapas`, `/srv/sosgalapagos-clima`, `/srv/sosgalapagos-estudios` y `/srv/sosgalapagos-descargas` (de `sosgalapagos-datos`) y `/srv/sosgalapagos-privado` (de `estudiantes-riesgo-nino`). Una ruta nueva se añade allí y se despliega con `despliegue/sitio/desplegar.sh`. **Nunca** con `--remove-orphans`: los contenedores de ResponseGrid quedan detenidos, no borrados.
2. **El mapa de `/riesgos/` lee lo que `sosgalapagos-datos` publica bajo `/mapas/`**: el manifiesto (`capas.json`), las capas, las teselas, `descargas.json` y `version.txt`. Una capa nueva se añade en `sosgalapagos-datos` y aparece sola en `/riesgos/`. **Nunca se da de baja la carpeta de `/mapas/`**: solo se retiró su página, que redirige a `/riesgos/`.
3. **`estudiantes-riesgo-nino` lee las capas de `sosgalapagos-datos`.** Se corre con `GEODATOS=~/dev/sosgalapagos-datos/geodatos`.
4. **El panel de `/clima/` es una página de `sosgalapagos-datos`**, pero sus datos, su código JS y sus APIs los sirve la plataforma (`/riesgos/api/clima/…`, `/riesgos/estaticos/mapa/…`).

### Dónde va cada cambio

| Quiero cambiar… | Repositorio |
|---|---|
| La portada, la privacidad, el menú del sitio o la marca | `sosgalapagos-plataforma` |
| El mapa de riesgos: reportes, buscador, panel de capas, línea del tiempo, página de descargas | `sosgalapagos-plataforma` |
| Una ruta o el Caddy del servidor | `sosgalapagos-plataforma` → `despliegue/sitio/` |
| Las fuentes de clima, el nivel de lluvia, el pronóstico, las mareas, el satélite | `sosgalapagos-plataforma` → `clima/` |
| Una capa, un estudio, un modelo, el orden y los colores de las capas | `sosgalapagos-datos` → `geodatos/` |
| La página del panel de `/clima/` | `sosgalapagos-datos` → `clima/web/` |
| Qué servicio corre dónde y cómo se publica | `sosgalapagos-datos` → `servidores/README.md` |
| El mapa o el informe de estudiantes en riesgo | `estudiantes-riesgo-nino` |

### Reglas que cruzan repositorios

- **No se copia código de `sosgalapagos` (AGPL-3.0, archivado) a ningún otro repositorio.** La AGPL obligaría a publicar el otro bajo AGPL.
- **Nada de un repositorio privado pasa a uno público.** Ni los datos personales de `estudiantes-riesgo-nino` ni la lógica de detección de estafas del bot (`src/analista.ts`).
- **Licencias.**
  - `sosgalapagos-datos` y `sosgalapagos-plataforma`: desde el 23-nov-2026, el código va bajo Apache 2.0 (con `NOTICE`) y lo propio que no es código, bajo CC BY 4.0, con crédito a «SOS Galápagos · Universidad San Francisco de Quito (USFQ) · Julián Maya <jamaya@usfq.edu.ec>». Cada archivo de código lleva su aviso de autoría. Del 22 al 23-nov-2026 tuvieron derechos reservados y CC BY-NC-ND 4.0.
  - Los datos de terceros conservan la licencia de su fuente.
  - `sosgalapagos` sigue siendo AGPL-3.0 y está archivado.
- **En `sosgalapagos-datos` y `sosgalapagos-plataforma` se trabaja en una rama con pull request**, sin `Co-Authored-By`.
- **Desplegar es un paso aparte y manual.** Subir a `main` no publica nada en `sosgalapagos.org`. No despliegues si no te lo piden, y avisa a las otras sesiones antes.
<!-- arbol-repos:fin -->
