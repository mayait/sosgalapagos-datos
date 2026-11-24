# Servidores: qué corre dónde y cómo se publica

Esta carpeta es el **índice de la parte de servidor**. El código de cada servicio vive junto a sus datos, en `geodatos/` o en `clima/`, para que los scripts sigan funcionando con rutas relativas. Aquí está el mapa completo y el único comando para publicar: [`publicar.sh`](publicar.sh).

> **Datos vs. servidor, en una línea:** los **datos** se descargan, se procesan y se guardan en git (`geodatos/`, `clima/datos/`, `mapas-galapagos/`). Los **servidores** toman esos archivos ya generados y los sirven en `sosgalapagos.org`, o recogen datos nuevos cada 5 minutos (el clima).

## Mapa

```
                       Cloudflare (DNS + proxy)
                                │
                     sosgalapagos.org  ·  152.44.45.89 (Debian 13)
  ┌─────────────────────────────┴──────────────────────────────────────────┐
  │  Compose «sosgalapagos» (repo sosgalapagos-plataforma → despliegue/sitio/) │
  │   caddy ─┬─ / /riesgos/ /privacidad → plataforma:8000                    │
  │          ├─ /backend/*   → 410 (ResponseGrid retirado el 24-nov-2026)    │
  │          ├─ /mapas/…     → /srv/sosgalapagos-mapas     (datos; la página redirige a /riesgos/) │
  │          ├─ /estudios/   → /srv/sosgalapagos-estudios  (estático)       │
  │          ├─ /descargas/  → /srv/sosgalapagos-descargas (PDF de la portada) │
  │          ├─ /estudios/api/* → contenedor «comentarios» (volumen comentariosdata) │
  │          └─ /clima/      → /srv/sosgalapagos-clima     (solo index + 3 JSON) │
  │                                                                          │
  │  Compose «sosgalapagos-plataforma»: postgis, plataforma, trabajador,     │
  │   reloj y satelite. Ahí corre TODO el clima (fuentes, nivel, pronóstico, │
  │   mareas, satélite) y escribe /srv/sosgalapagos-clima/datos              │
  │  Host (systemd): solo respaldo diario y monitor de recursos              │
  └──────────────────────────────────────────────────────────────────────────┘
            ▲ https, con una llave (POST /riesgos/api/clima/relevo/ierse)
            │
  Una máquina en Ecuador: relevo de IERSE cada 5 min (IERSE solo responde
  desde Ecuador). Programa mínimo: despliegue/relevo/ de la plataforma
```

## Servicios

| Servicio | URL | Qué es | Código fuente (este repo) | En el servidor | Publicar |
|---|---|---|---|---|---|
| **Datos del mapa** | `/mapas/…` | **Sin visor desde el 21-nov-2026**: `/mapas/` redirige a `/riesgos/`. Aquí se publican el manifiesto (`capas.json`), las capas, las teselas y las descargas en Shapefile y GeoJSON (islas completas). **No dar de baja esta carpeta: `/riesgos/` lee todo de aquí** | `geodatos/scripts/10_publicar_web.py`, `geodatos/scripts/visor_mapas.json` (orden, colores, capas encendidas y buscador), `geodatos/scripts/publicar_mapas.sh`. El visor anterior está en `Archivo/visor-mapas/` | `/srv/sosgalapagos-mapas`, montado en Caddy como `/srv/mapas` (solo lectura) | `servidores/publicar.sh mapas` |
| **Mapa de riesgos** | `/riesgos/` | El mapa único del sitio: reportes ciudadanos, capas, buscador, descargas e informe | repo `mayait/sosgalapagos-plataforma` | código en `/opt/sosgalapagos-plataforma`, Compose aparte `sosgalapagos-plataforma` | `despliegue/produccion/desplegar.sh` de ese repo |
| **Estudios / Informes** | `/estudios/` (alias `/informes`) | **Retirado el 5-nov-2026**: los informes y los textos de los estudios son solo locales. La ruta redirige a la portada | — | `/srv/sosgalapagos-estudios` (solo una redirección; la copia anterior quedó en `/root/respaldo-estudios-2026-11-05/`) | no se publica |
| **Informes descargables** | `/descargas/` y la sección «Informes y mapas para descargar» de la portada | Mapas e informes en PDF que Julián decide publicar (desde el 21-nov-2026). Los archivos no están en git: viven en `~/dev/sosgalapagos-informes/publicar/` con su `indice.json` | `servidores/publicar_descargas.sh` | `/srv/sosgalapagos-descargas`, montado en Caddy (sirve solo `.pdf`, `.jpg` y `.png`) y en la web (lee `indice.json`) | `servidores/publicar.sh descargas` |
| **Portada** | `/`, `/privacidad` | La portada (Ahora, boletines oficiales, ayuda) y la privacidad del sitio. **Desde el 24-nov-2026 en la plataforma**; el fork de ResponseGrid (`mayait/sosgalapagos`) está archivado y sus contenedores detenidos, sin borrar (respaldo en `/root/respaldo-responsegrid/`) | repo `mayait/sosgalapagos-plataforma`, app `portada/` | Compose `sosgalapagos-plataforma` | `despliegue/produccion/desplegar.sh` de ese repo |
| **Comentarios** | `/estudios/api/*` | API de comentarios del antiguo sitio de estudios (sin uso desde el 4-nov-2026; el contenedor y el volumen se conservan) | repo `mayait/sosgalapagos-plataforma`: `despliegue/sitio/comentarios/servidor.py` | contenedor `comentarios`, volumen `comentariosdata` | `despliegue/sitio/desplegar.sh` de la plataforma |
| **Clima en vivo** | `/clima/` | Panel con el nivel de lluvia peligrosa, lluvia, pronóstico, mareas, oleaje, satélite y lo oficial (INAMHI, INOCAR). **Desde el 22-nov-2026 todo corre en la plataforma, en un solo stack y sobre PostgreSQL** | Panel: `clima/web/index.html` (este repo). Todo lo demás: repo `mayait/sosgalapagos-plataforma`, app `clima/` (`docs/plan-clima.md`) | Datos en PostgreSQL (contenedor `postgis`); JSON del panel y descargas en `/srv/sosgalapagos-clima/datos`. **Sin uso, sin borrar:** `/var/lib/sosgalapagos-clima/clima.db`, `/opt/sosgalapagos-clima/` y los timers `sosgalapagos-clima*.timer` (detenidos y deshabilitados) | Panel: `servidores/publicar.sh clima`. Lo demás: `despliegue/produccion/desplegar.sh` de la plataforma |
| **Relevo de IERSE** | — | IERSE solo responde desde Ecuador: una máquina allá pide lo que la plataforma le indica y devuelve las respuestas. Sin base ni SSH | repo `mayait/sosgalapagos-plataforma`: `despliegue/relevo/` | puerta `/riesgos/api/clima/relevo/ierse`, con la llave `CLIMA_RELEVO_LLAVE` | `sh despliegue/relevo/instalar.sh` en la máquina de Ecuador. El puente anterior está en `Archivo/clima-servicio-anterior/` |
| **GeoServer (demo)** | `http://127.0.0.1:8085/geoserver` | WMS/WFS **local** para probar en QGIS. No está en producción | `geodatos/scripts/11_geoserver_local.py` | — | — |
| **Visor local** | `http://127.0.0.1:8765/visor/` | Revisar capas antes de publicar | `geodatos/scripts/servir.sh`, `mapas-galapagos/ver-mapa.sh` | — | — |

La configuración de Caddy (`Caddyfile`, `docker-compose.yml` del frente) está desde el 24-nov-2026 en `mayait/sosgalapagos-plataforma`, carpeta `despliegue/sitio/`. Para añadir una ruta nueva hay que cambiarla allí y desplegar el frente (nunca con `--remove-orphans`: los contenedores de ResponseGrid quedan detenidos, no borrados):

```bash
ssh root@152.44.45.89 /opt/sosgalapagos-plataforma/despliegue/sitio/desplegar.sh
```

## Reglas

1. **Solo se publica desde `main`** y con el árbol limpio. `publicar.sh` lo comprueba y deja `version.txt` (commit y fecha) en la carpeta del servicio en el servidor.
2. `/clima/` **no tiene descargas ni enlaces a las fuentes**, y la página no se indexa (`noindex`). Caddy solo deja pasar `index.html`, `estado.json`, `horario.json` y `diario.json`.
3. Los endpoints de las fuentes de clima están en `clima/privado/` (en la Mac) y en el servidor (`EnvironmentFile` de systemd). **Nunca en git.**
4. Acceso: `root@152.44.45.89` solo con llave. El `.env` de producción vive solo en el servidor.

## Uso de recursos y eficiencia

El servidor es compartido: además de SOS Galápagos corren otros proyectos (`regresion-*`, `miplata-*`). Tiene 4 CPU, 8 GB de memoria y 99 GB de disco.

**Medición del 22-nov-2026, 07:30 UTC:** carga 0,4 (de 4), 3,3 GB de memoria usados y 4,6 GB disponibles, disco al 63 %. SOS Galápagos no aprieta el servidor:

| Parte | Memoria |
|---|---|
| Mapa de riesgos (web, trabajador, reloj, PostGIS) | ≈ 360 MB |
| Sitio (portada Next, API Nest, Postgres, Redis, Caddy, comentarios) | ≈ 280 MB |
| Clima | Sin proceso permanente: corre cada 5 min con systemd y termina |
| Otros proyectos del servidor | ≈ 950 MB |

**Registro continuo.** `servidores/recursos.sh` se instala como `/usr/local/bin/sosgalapagos-recursos`, y el timer `sosgalapagos-recursos.timer` añade una línea cada 15 minutos a `/var/log/sosgalapagos-recursos.csv` (memoria, carga, disco y memoria por grupo de contenedores).

```bash
sosgalapagos-recursos            # estado de ahora
sosgalapagos-recursos --resumen  # promedios y máximos de los últimos 7 días
```

**Lo que se optimizó el 22-nov-2026:**

- **Caché de compilación de Docker: 42 GB.** Era el mayor consumo de disco y no servía para nada. Se limpió lo que llevaba más de 7 días sin usarse (`docker builder prune --filter until=168h`). Conviene repetirlo cada mes.
- **Respaldos del clima: 3,7 GB → menos de 1 GB.** Eran 14 copias de la base sin comprimir; ahora se guardan con gzip (`Archivo/clima-servicio-anterior/deploy/respaldo.sh`; hoy el respaldo es el de la plataforma).
- **Una sola app instalable** para la portada, el mapa y el clima, en lugar de dos manifiestos.

**Lo que se puede optimizar después** (no se tocó):

- El contenedor `comentarios` no se usa desde el 4-nov-2026. Se puede detener sin borrarlo.
- El sitio de coordinación (Next + Nest + Postgres + Redis, ≈ 280 MB) se retira en la fase 4 del plan, cuando la portada pase al mismo stack del mapa.
- `horario.json` del clima pesa 960 KB (55 KB comprimido) y el panel lo baja entero. Si crece, partirlo por mes.
- **Hecho el 22-nov-2026:** el recolector de clima, que gastaba ≈ 2,5 min de CPU cada 5 min rehaciendo todas las exportaciones, se relevó por la plataforma, que genera lo mismo en ≈ 1,2 s.
- El mapa de riesgos usa tres procesos de Python para web, trabajador y reloj. El reloj podría ir dentro del trabajador y ahorrar ≈ 60 MB.

**¿Hace falta reescribir el clima en el stack del mapa (Django)?** No, por ahora. El panel ya es del mismo tipo que el mapa: HTML y JavaScript sin compilación. El recolector es Python con systemd y no deja ningún proceso corriendo entre corridas, que es lo más barato que puede ser. Pasarlo a Django añadiría un proceso permanente y riesgo durante la emergencia, sin ahorrar nada. Lo que sí se hizo fue darle la misma identidad gráfica y meterlo en la misma app.

## Comprobar que todo está vivo

```bash
curl -sI https://sosgalapagos.org/riesgos/ | head -1            # el mapa
curl -sI https://sosgalapagos.org/mapas/capas.json | head -1   # los datos que lee el mapa
curl -sI https://sosgalapagos.org/mapas/ | head -1             # 302 a /riesgos/
curl -sI https://sosgalapagos.org/estudios/ | head -1
curl -s https://sosgalapagos.org/clima/datos/estado.json | head -c 300
ssh root@152.44.45.89 'systemctl list-timers "sosgalapagos-clima*" --no-pager; cat /srv/sosgalapagos-*/version.txt /opt/sosgalapagos-clima/version.txt 2>/dev/null'
launchctl list | grep sosgalapagos      # puente IERSE en la Mac
```

## Pendientes de servidor

Están en los [issues de plataforma](https://github.com/mayait/sosgalapagos-datos/issues?q=is%3Aopen+label%3Aplataforma): respaldo fuera del servidor, aviso si el recolector se cae, publicación automática desde `main` y WMS/WFS en producción.
