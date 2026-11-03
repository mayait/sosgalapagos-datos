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
  │          ├─ /mapas/      → /srv/sosgalapagos-mapas     (estático)       │
  │          ├─ /estudios/   → /srv/sosgalapagos-estudios  (estático)       │
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
| **Mapas** | `/mapas/` | Visor Leaflet (buscador, puntos de análisis, imagen con leyenda) y descargas en Shapefile y GeoJSON de todas las capas (islas completas) | `geodatos/scripts/10_publicar_web.py`, `geodatos/scripts/visor_mapas.json` (orden, colores y capas encendidas del visor), `geodatos/web/index.html`, `geodatos/scripts/publicar_mapas.sh` | `/srv/sosgalapagos-mapas`, montado en Caddy como `/srv/mapas` (solo lectura) | `servidores/publicar.sh mapas` |
| **Estudios** | `/estudios/` | Informes técnicos preliminares en web: mapa, 3D, línea de tiempo, descargas y comentarios por sección | `geodatos/scripts/19_estudios_web.py`, `geodatos/web/estudios.{css,js}`, `geodatos/scripts/publicar_estudios.sh` | `/srv/sosgalapagos-estudios` → `/srv/estudios` | `servidores/publicar.sh estudios` |
| **Comentarios** | `/estudios/api/*` | API de comentarios de los estudios | repo `mayait/sosgalapagos`: `deploy/sosgalapagos/comentarios/servidor.py` | contenedor `comentarios`, volumen `comentariosdata` | despliegue de la app |
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

## Comprobar que todo está vivo

```bash
curl -sI https://sosgalapagos.org/mapas/ | head -1
curl -sI https://sosgalapagos.org/estudios/ | head -1
curl -s https://sosgalapagos.org/clima/datos/estado.json | head -c 300
ssh root@152.44.45.89 'systemctl list-timers "sosgalapagos-clima*" --no-pager; cat /srv/sosgalapagos-*/version.txt /opt/sosgalapagos-clima/version.txt 2>/dev/null'
launchctl list | grep sosgalapagos      # puente IERSE en la Mac
```

## Pendientes de servidor

Están en los [issues de plataforma](https://github.com/mayait/sosgalapagos-datos/issues?q=is%3Aopen+label%3Aplataforma): respaldo fuera del servidor, aviso si el recolector se cae, publicación automática desde `main` y WMS/WFS en producción.
