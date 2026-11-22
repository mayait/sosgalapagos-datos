# Servicio de clima anterior (archivado el 22-nov-2026)

Aquí queda, sin uso, lo que instalaba y alimentaba el recolector de clima cuando corría fuera de la plataforma:

- `deploy/`: instalación en el servidor, timers de systemd, respaldo y recepción del puente.
- `puente/`: el puente de IERSE (una Mac en Ecuador con su propio recolector y su base, que enviaba por SSH).

Desde el 22-nov-2026 todo el clima corre en `mayait/sosgalapagos-plataforma` (app `clima/`), escribe en PostgreSQL y no usa SQLite. IERSE entra por un relevo mínimo (`despliegue/relevo/` de ese repositorio). Nada de esta carpeta se ejecuta; se conserva como referencia (lo que se descarta se mueve a `Archivo`, no se borra).
