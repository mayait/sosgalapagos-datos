# Datos meteorológicos de Galápagos

Mediciones guardadas por SOS Galápagos para analizar las inundaciones de 2026 y calibrar modelos. Los **crudos** se guardan tal cual llegan y nunca se corrigen. Las tablas consolidadas se regeneran con los scripts de `clima/scripts/`.

| Carpeta | Fuente | Qué hay | Periodo | Hora |
|---|---|---|---|---|
| `ierse-wsn/` | **IERSE** (Universidad del Azuay), red de estaciones de Galápagos | 4 estaciones en Santa Cruz (Cerro Crocker, Santa Rosa, Los Guayabillos, Militar): lluvia, temperatura, humedad y presión cada ~5 min. `crudos/AAAA-MM/AAAA-MM-DD.csv.gz` + `serie_5min.csv.gz`, `horario.csv`, `diario.csv` (con `cobertura_pct`) y `estaciones.geojson` | abr-2026 → hoy | UTC−6 |
| `inamhi/historial/` | **INAMHI** | Historial horario de las estaciones automáticas. **Irrecuperable**: la fuente solo guarda 90 días | 16-oct → 2-nov-2026 | UTC−5 |
| `fcd/` | **Fundación Charles Darwin** | Series diarias de Puerto Ayora (desde 1965) y Bellavista. Licencia **CC BY-NC-SA** | 1964 → 2026 | — |

## Cómo citar

«Datos: red IERSE (Universidad del Azuay); INAMHI; Fundación Charles Darwin (CC BY-NC-SA); USFQ GSC. Recopilación: SOS Galápagos (USFQ Galápagos · IA Humana)».

## Cuidado al usarlos

- **Cortes de transmisión:** si una estación deja de transmitir, esa lluvia **no se mide**. Los totales de esos días son mínimos. Revisa siempre `cobertura_pct`.
- Cerro Crocker parece fallar desde agosto de 2026. Los Guayabillos marca 0 mm desde el 31-oct, probablemente porque el pluviómetro está obstruido.
- Los pluviómetros de balancín subestiman la lluvia de más de 50 mm/h.
- Datos de la FCD: **uso no comercial**, citando la fuente y compartiendo bajo la misma licencia.
- Por ahora no se publican los enlaces a los servicios de origen.
