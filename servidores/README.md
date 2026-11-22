# Servidores: qué corre dónde y cómo se publica

Esta carpeta es el **índice de la parte de servidor**. El código de cada servicio vive junto a sus datos, en `geodatos/` o en `clima/`, para que los scripts sigan funcionando con rutas relativas. Aquí está el mapa completo y el único comando para publicar: [`publicar.sh`](publicar.sh).

> **Datos vs. servidor, en una línea:** los **datos** se descargan, se procesan y se guardan en git (`geodatos/`, `clima/datos/`, `mapas-galapagos/`). Los **servidores** toman esos archivos ya generados y los sirven en `sosgalapagos.org`, o recogen datos nuevos cada 5 minutos (el clima).

## Mapa

```
                       Cloudflare (DNS + proxy)
                                │
                     sosgalapagos.org  ·  152.44.45.89 (Debian 13)
  ┌─────────────────────────────┴──────────────────────────────────────────┐
  │  Docker compose (repo mayait/sosgalapagos → deploy/sosgalapagos/)       │
  │   caddy ─┬─ /            → app ResponseGrid (web + API /backend)        │
  │          ├─ /riesgos/    → plataforma:8000 (repo sosgalapagos-plataforma) │
  │          ├─ /mapas/…     → /srv/sosgalapagos-mapas     (datos; la página redirige a /riesgos/) │
  │          ├─ /estudios/   → /srv/sosgalapagos-estudios  (estático)       │
  │          ├─ /descargas/  → /srv/sosgalapagos-descargas (PDF de la portada) │
  │          ├─ /estudios/api/* → contenedor «comentarios» (volumen comentariosdata) │
  │          └─ /clima/      → /srv/sosgalapagos-clima     (solo index + 3 JSON) │
  │                                                                          │
  │  Host (systemd, fuera de Docker)                                         │
  │   sosgalapagos-clima.timer      cada 5 min → recolector.py → clima.db    │
  │   sosgalapagos-clima-csv.timer  cada hora  → CSV privados + respaldo diario │
  └──────────────────────────────────────────────────────────────────────────┘
            ▲ ssh (llave restringida id_clima_puente → clima@servidor)
            │
  Mac de Julián: launchd org.sosgalapagos.clima-puente (cada 5 min)
  └─ clima/puente/puente_ierse.sh  (IERSE no responde a IPs de EE. UU.)
```

## Servicios

| Servicio | URL | Qué es | Código fuente (este repo) | En el servidor | Publicar |
|---|---|---|---|---|---|
| **Datos del mapa** | `/mapas/…` | **Sin visor desde el 21-nov-2026**: `/mapas/` redirige a `/riesgos/`. Aquí se publican el manifiesto (`capas.json`), las capas, las teselas y las descargas en Shapefile y GeoJSON (islas completas). **No dar de baja esta carpeta: `/riesgos/` lee todo de aquí** | `geodatos/scripts/10_publicar_web.py`, `geodatos/scripts/visor_mapas.json` (orden, colores, capas encendidas y buscador), `geodatos/scripts/publicar_mapas.sh`. El visor anterior está en `Archivo/visor-mapas/` | `/srv/sosgalapagos-mapas`, montado en Caddy como `/srv/mapas` (solo lectura) | `servidores/publicar.sh mapas` |
| **Mapa de riesgos** | `/riesgos/` | El mapa único del sitio: reportes ciudadanos, capas, buscador, descargas e informe | repo `mayait/sosgalapagos-plataforma` | código en `/opt/sosgalapagos-plataforma`, Compose aparte `sosgalapagos-plataforma` | `despliegue/produccion/desplegar.sh` de ese repo |
| **Estudios / Informes** | `/estudios/` (alias `/informes`) | **Retirado el 5-nov-2026**: los informes y los textos de los estudios son solo locales. La ruta redirige a la portada | — | `/srv/sosgalapagos-estudios` (solo una redirección; la copia anterior quedó en `/root/respaldo-estudios-2026-11-05/`) | no se publica |
| **Informes descargables** | `/descargas/` y la sección «Informes y mapas para descargar» de la portada | Mapas e informes en PDF que Julián decide publicar (desde el 21-nov-2026). Los archivos no están en git: viven en `~/dev/sosgalapagos-informes/publicar/` con su `indice.json` | `servidores/publicar_descargas.sh` | `/srv/sosgalapagos-descargas`, montado en Caddy (sirve solo `.pdf`, `.jpg` y `.png`) y en la web (lee `indice.json`) | `servidores/publicar.sh descargas` |
| **Comentarios** | `/estudios/api/*` | API de comentarios del antiguo sitio de estudios (sin uso desde el 4-nov-2026; el contenedor y el volumen se conservan) | repo `mayait/sosgalapagos`: `deploy/sosgalapagos/comentarios/servidor.py` | contenedor `comentarios`, volumen `comentariosdata` | despliegue de la app |
| **Clima en vivo** | `/clima/` | Panel con lluvia, temperatura, humedad y presión de las estaciones; se actualiza cada 5 min | `clima/recolector/recolector.py`, `clima/web/index.html`, `clima/deploy/` | código en `/opt/sosgalapagos-clima`; base en `/var/lib/sosgalapagos-clima/clima.db` (respaldos de 14 días); JSON en `/srv/sosgalapagos-clima/datos` | `servidores/publicar.sh clima` (`--historico` recarga el histórico) |
| **Puente IERSE** | — | Reenvía IERSE desde la Mac al servidor | `clima/puente/` | usuario `clima`, que solo puede ejecutar `recibir.sh` | `launchctl` en la Mac (ver `clima/LEEME.md`) |
| **Capas de la app** | `/capas/galapagos-2026/` | Las capas que muestra el mapa de ResponseGrid | `geodatos/export/galapagos/` + `geodatos/export/integracion/` | dentro de la imagen web de la app | `09_entregable.py` / `copiar-a-app.sh` + despliegue de la app |
| **GeoServer (demo)** | `http://127.0.0.1:8085/geoserver` | WMS/WFS **local** para probar en QGIS. No está en producción | `geodatos/scripts/11_geoserver_local.py` | — | — |
| **Visor local** | `http://127.0.0.1:8765/visor/` | Revisar capas antes de publicar | `geodatos/scripts/servir.sh`, `mapas-galapagos/ver-mapa.sh` | — | — |

La configuración de Caddy y de Docker (`Caddyfile`, `docker-compose.yml`) está en el repositorio de la app (`mayait/sosgalapagos`, carpeta `deploy/sosgalapagos/`). Para añadir una ruta nueva hay que cambiarla allí y desplegar la app:

```bash
ssh root@152.44.45.89 /opt/sosgalapagos/deploy/sosgalapagos/deploy.sh
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
- **Respaldos del clima: 3,7 GB → menos de 1 GB.** Eran 14 copias de la base sin comprimir; ahora se guardan con gzip (`clima/deploy/respaldo.sh`).
- **Una sola app instalable** para la portada, el mapa y el clima, en lugar de dos manifiestos.

**Lo que se puede optimizar después** (no se tocó):

- El contenedor `comentarios` no se usa desde el 4-nov-2026. Se puede detener sin borrarlo.
- El sitio de coordinación (Next + Nest + Postgres + Redis, ≈ 280 MB) se retira en la fase 4 del plan, cuando la portada pase al mismo stack del mapa.
- `horario.json` del clima pesa 960 KB (55 KB comprimido) y el panel lo baja entero. Si crece, partirlo por mes.
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
