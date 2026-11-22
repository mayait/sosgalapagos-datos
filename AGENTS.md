# Instrucciones para agentes (Claude Code, Codex y otros)

Lee primero [README.md](README.md) (qué hay) y [CONTRIBUIR.md](CONTRIBUIR.md) (cómo se trabaja). Este archivo resume las reglas que **no** se pueden romper.

## Reglas duras

1. **Repositorio público.** Nunca subas:
   - `geodatos/descargas/` (trae nombres y teléfonos de fuentes oficiales);
   - `.venv/`, `clima/privado/`, bases SQLite (`*.db`) ni credenciales;
   - **URLs o endpoints de las fuentes meteorológicas**. Solo se nombran: «IERSE», «USFQ GSC», «INAMHI». Los endpoints viven en `clima/privado/`.
2. **Datos personales:** las capas oficiales (SNGR, MSP) traen nombres y teléfonos. Se depuran en el script, por ejemplo en `07_oficiales.py`. Nunca publiques nombres de personas afectadas.
3. **Modelo ≠ dato oficial.** La susceptibilidad HAND, las cuencas, la costa baja y las lluvias de modelos son estimaciones propias. Dilo siempre en mapas, textos y fichas.
4. **No edites archivos generados a mano.** Corre el script que los produce (ver CONTRIBUIR §1).
5. **No despliegues** a `sosgalapagos.org` si no te lo piden, y solo desde `main` (`servidores/publicar.sh`).
6. **Informes y textos de estudios son solo locales.** `informes/` y `geodatos/estudios/*/{texto,figuras}/` (y sus PDF) están en `.gitignore`: no se suben al repositorio ni se publican en la web. Los datos de los estudios sí se versionan. **Única excepción (desde el 21-nov-2026):** los mapas e informes en PDF que Julián pida publicar uno por uno van a la sección de descargas de la portada con `servidores/publicar.sh descargas`. Siguen fuera de git y nunca se publica uno que él no haya pedido.
7. **Trabaja en tu rama** (mejor en un *worktree*) y no toques el dominio de otra sesión sin coordinarlo. Entre sesiones de Claude Code: `ListAgents` y `SendMessage`.

8. **Licencia (desde el 22-nov-2026).** El código tiene todos los derechos reservados ([`LICENSE`](LICENSE)); lo propio que no es código va bajo CC BY-NC-ND 4.0 y lo de terceros conserva su licencia ([`LICENCIA-DATOS.md`](LICENCIA-DATOS.md)). Cada archivo de código propio (`.py`, `.sh`, páginas) empieza con el aviso de autoría de dos líneas (USFQ · SOS Galápagos · Julián Maya): ponlo en los archivos nuevos y no lo quites. Donde se muestre o se descargue un dato de terceros, se nombra su licencia.

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
| Tocar el clima | El que corre en vivo: repo `sosgalapagos-plataforma`, app `clima/`. Aquí: el panel (`clima/web/`) y los análisis (`clima/LEEME.md`) |
| Tocar el pronóstico de lluvia | `clima/pronostico/LEEME.md` (evaluación en `fase0/informe.md`) |

## Árbol de repositorios de SOS Galápagos

**Estás en:** `sosgalapagos-datos`. Los datos, el clima y los modelos. La plataforma vive en otro repositorio.

<!-- arbol-repos:inicio -->
> **Este bloque es idéntico en los seis repositorios** (en su `AGENTS.md`). Si cambias algo, cámbialo en los seis. Última revisión: 2026-11-21 (el mapa único es `/riesgos/`; el visor de `/mapas` se retiró).

SOS Galápagos no es un solo repositorio, son seis. No hay organización de GitHub: todos están en la cuenta `mayait`. En la Mac de Julián cada uno se clona en `~/dev/<nombre>`.

| Repositorio | Visibilidad | Qué contiene | Qué publica |
|---|---|---|---|
| [`sosgalapagos`](https://github.com/mayait/sosgalapagos) | público | La plataforma de coordinación: web y API. Es un fork de `GlobalEmergency/ResponseGrid`. También guarda el Caddy y el Docker Compose de **todo** el servidor (`deploy/sosgalapagos/`). | `sosgalapagos.org/` y `/backend` |
| [`sosgalapagos-datos`](https://github.com/mayait/sosgalapagos-datos) | público | Geodatos, clima, estudios de riesgo y modelos. Su carpeta `servidores/` es el índice de qué corre dónde. | Los datos de `/mapas/…` (capas y descargas, sin visor) y `/clima/` |
| [`sosgalapagos-plataforma`](https://github.com/mayait/sosgalapagos-plataforma) | público | El mapa de riesgos: reportes ciudadanos con vencimiento sobre las capas de riesgo, buscador, descargas e informe. Django + PostGIS, Apache 2.0. Es el único mapa del sitio desde el 21-nov-2026. | `/riesgos/` |
| [`sosgalapagos-bot`](https://github.com/mayait/sosgalapagos-bot) | **privado** | Asistente de WhatsApp: lee grupos, clasifica mensajes y crea pedidos en la plataforma. | Nada en la web; es un servicio systemd aparte (ver su `LEEME.md`) |
| [`RESPONSEGRID_GALAPAGOS`](https://github.com/mayait/RESPONSEGRID_GALAPAGOS) | público | Carpeta de trabajo local: arranque en la Mac y datos semilla. Clona `sosgalapagos` dentro de `app/`, que git ignora. Conserva la historia de geodatos hasta el 2-nov-2026. | Nada |
| [`estudiantes-riesgo-nino`](https://github.com/mayait/estudiantes-riesgo-nino) | **privado** | Viviendas de estudiantes de USFQ Galápagos cruzadas con el riesgo de inundación. Tiene datos personales. | `/usfq/`, con contraseña |

```
                         sosgalapagos.org (un solo servidor, detrás de Cloudflare)
                                          │
              Caddy + Docker Compose: sosgalapagos → deploy/sosgalapagos/
        ┌──────────────┬──────────────────┬──────────────────┬───────────────────────┐
        │ /  /backend  │ /riesgos/        │ /mapas/… /clima/ │ /usfq/ (contraseña)   │
        ▼              ▼                  ▼                  ▼                       │
   sosgalapagos   sosgalapagos-      sosgalapagos-datos   estudiantes-riesgo-nino    │
   (portada y     plataforma         (datos y modelos)    (privado)                  │
    coordinación) (mapa de riesgos)       │                    ▲                     │
        ▲              ▲  lee capas.json, │ capas y descargas  │ capas de geodatos   │
        │              └──────────────────┴────────────────────┘                     │
        │ API pública                                                                │
   sosgalapagos-bot (privado, servicio aparte) ◄─────────────────────────────────────┘

   /mapas/ ya no tiene visor: la página redirige a /riesgos/. Sus datos se siguen sirviendo.
   RESPONSEGRID_GALAPAGOS/app/  =  otro clon local de sosgalapagos
```

### Cómo dependen unos de otros

1. **Las rutas del servidor se definen en `sosgalapagos`.** El `Caddyfile` y el `docker-compose.yml` de `deploy/sosgalapagos/` sirven la plataforma, pasan `/riesgos/` al contenedor de `sosgalapagos-plataforma` (Compose aparte, en la misma red) y montan las carpetas que publican los demás: `/srv/sosgalapagos-mapas` y `/srv/sosgalapagos-clima` (de `sosgalapagos-datos`) y `/srv/sosgalapagos-privado` (de `estudiantes-riesgo-nino`). Una ruta nueva se añade allí y se despliega con `deploy/sosgalapagos/deploy.sh`, aunque el contenido venga de otro repositorio.
2. **Las capas del mapa de la plataforma se generan en `sosgalapagos-datos`** (`geodatos/export/`) y se sirven desde `sosgalapagos` (`apps/web/public/capas/galapagos-2026/`), dentro de la imagen web. Para que un cambio de capa llegue a la plataforma hay que copiarla y desplegar la app. La carpeta `geodatos/` de `sosgalapagos` no recibe cambios desde el 1-nov-2026: el proceso vivo está en `sosgalapagos-datos`.
3. **El bot habla con la plataforma solo por su API pública** (`https://sosgalapagos.org/backend`, cliente en `src/responsegrid.ts`). No toca la base de datos ni el código. Si cambias un endpoint o un DTO de la API en `sosgalapagos`, revisa ese cliente.
4. **`estudiantes-riesgo-nino` lee las capas de `sosgalapagos-datos`.** Su ruta por defecto apunta a la ubicación antigua, que ya no existe: se corre con `GEODATOS=~/dev/sosgalapagos-datos/geodatos`.
5. **`RESPONSEGRID_GALAPAGOS/app/` es un clon de `sosgalapagos`**, no una carpeta del repositorio que lo contiene. Lo que se hace commit allí va a `sosgalapagos`. Como hay dos clones locales del mismo repositorio (`~/dev/sosgalapagos` y `~/dev/RESPONSEGRID_GALAPAGOS/app`), haz `git pull` antes de trabajar en cualquiera.
6. **El mapa de `/riesgos/` lee lo que `sosgalapagos-datos` publica bajo `/mapas/`**: el manifiesto (`capas.json`), las capas, las teselas, `descargas.json` y `version.txt`. Una capa nueva se añade en `sosgalapagos-datos` y aparece sola en `/riesgos/`. **Nunca se da de baja la carpeta de `/mapas/`**: solo se retiró su página, que redirige a `/riesgos/`.

### Dónde va cada cambio

| Quiero cambiar… | Repositorio |
|---|---|
| La web, la API, la portada, formularios o la marca | `sosgalapagos` |
| Una ruta, un contenedor o el Caddy del servidor | `sosgalapagos` → `deploy/sosgalapagos/` |
| El mapa de riesgos: reportes, buscador, panel de capas, informe, página de descargas | `sosgalapagos-plataforma` |
| Una capa, un estudio, un modelo, el orden y los colores de las capas | `sosgalapagos-datos` → `geodatos/` |
| El panel de `/clima/`, el recolector, el pronóstico | `sosgalapagos-datos` → `clima/` |
| Qué servicio corre dónde y cómo se publica | `sosgalapagos-datos` → `servidores/README.md` |
| Cómo lee, responde o modera el asistente de WhatsApp | `sosgalapagos-bot` |
| El arranque local o los datos semilla | `RESPONSEGRID_GALAPAGOS` → `galapagos/` |
| El mapa o el informe de estudiantes en riesgo | `estudiantes-riesgo-nino` |

### Reglas que cruzan repositorios

- **No se copia código de `sosgalapagos` (AGPL-3.0) a `sosgalapagos-plataforma`** (todos los derechos reservados desde el 22-nov-2026; antes, Apache 2.0).
- **Nada de un repositorio privado pasa a uno público.** Ni los datos personales de `estudiantes-riesgo-nino` ni la lógica de detección de estafas del bot (`src/analista.ts`).
- **Cada repositorio tiene sus propias reglas de commit y de ramas.** Léelas en su `AGENTS.md` o `LEEME.md` antes de hacer commit. Dos que cambian: en `sosgalapagos` los commits van como «IA Humana» y sin `Co-Authored-By`; en `sosgalapagos-datos` y en `sosgalapagos-plataforma` se trabaja en una rama con pull request, también sin `Co-Authored-By`.
- **Desplegar es un paso aparte y manual.** Subir a `main` no publica nada en `sosgalapagos.org`. No despliegues si no te lo piden.
<!-- arbol-repos:fin -->
