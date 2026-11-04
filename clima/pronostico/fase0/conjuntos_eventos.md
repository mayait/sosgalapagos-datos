# Conjuntos de ECMWF (IFS ENS y AIFS ENS) en los eventos de lluvia fuerte

Complemento de la fase 0 ([informe.md](informe.md)), con fecha del 4-nov-2026. La pregunta es si algún miembro de los conjuntos de ECMWF vio las lluvias fuertes con 1, 2 y 3 días de anticipación, y con qué probabilidad.

- **Script:** `conjuntos/ens_eventos.py`. Lee solo los campos `tp` de los datos abiertos de ECMWF (CC BY 4.0) con peticiones por rangos. El endpoint va en `CLIMA_ECMWF_S3`.
- **Archivos no versionados:** la tabla `ens_eventos.csv` y los casos, porque llevan lluvia medida del GSC.

> Son estimaciones de modelos con muestras pequeñas. No es un dato oficial.

## Método

- **Corridas:** la de las 00Z de D−L, con L = 1, 2 y 3. El total del día D en Galápagos (06Z a 06Z) se calcula como tp(24L+30) − tp(24L+6).
- **Equivalencia con la web:** la corrida 00Z de D−1 (18:00 de D−2 en Galápagos) está lista hacia la medianoche de D−1. Con L = 1 se ve el día D como **«mañana»**, igual que en el recuadro de la web.
- **Puntos y probabilidades:** se usa el punto de rejilla de 0,25° más cercano y el **máximo de una vecindad 3×3** (0,75°), porque las islas son más pequeñas que una celda. La probabilidad es la fracción de miembros que supera cada umbral.
- **Disponibilidad de datos:**
  - IFS ENS a 0,25° está desde feb-2024. Desde mayo de 2026 el archivo abierto solo trae los 50 miembros perturbados, sin el control.
  - AIFS ENS está desde jul-2025.
- **Unidades:** IFS publica `tp` en metros y AIFS en kg m⁻² (mm). El script lo comprueba en cada campo.
- **Eventos:**
  - 10 en total: 30-oct, 23-oct, 3-oct y 14-jun-2026 en Santa Cruz alta; 22-feb y 13-feb-2024 y 26-mar-2025 en Puerto Ayora; 8-mar-2025, 15-abr y 17-abr-2026 en San Cristóbal alta.
  - AIFS solo cubre los 6 eventos de 2026.
- **Días secos (< 2 mm), al azar:** 15 en Santa Rosa (may–oct-2026), 10 en Puerto Ayora en la temporada lluviosa de 2025 (solo IFS) y 10 en la de 2026.

## Resultados

**30-oct-2026, Santa Rosa (238 mm medidos):**

| Conjunto | Anticipación | P(> 20 mm) punto / vecindad | P(> 50 mm) punto / vecindad | Miembro más alto (vecindad) |
|---|---|---|---|---|
| IFS ENS | 1 día | 6 % / 26 % | 0 % / 2 % | 66 mm |
| IFS ENS | 3 días | 2 % / 22 % | 0 % / 2 % | 65 mm |
| AIFS ENS | 1 día | 18 % / 35 % | 8 % / 12 % | 137 mm |
| AIFS ENS | 3 días | 39 % / 53 % | 18 % / 31 % | 199 mm |

- **El 3-oct (68 mm) y el 14-jun (65 mm)** no tuvieron ninguna señal. Ningún miembro de ninguno de los dos conjuntos pasó de 20 mm, con ninguna anticipación.
- **Media de los eventos a 1 día:**
  - IFS ENS: P(> 20 mm) = 0,10 en el punto y 0,28 en la vecindad; P(> 50 mm) = 0,01 y 0,04.
  - AIFS ENS: P(> 20 mm) = 0,12 y 0,19; P(> 50 mm) = 0,03 y 0,07.
  - Con 2 y 3 días las cifras son parecidas. No mejoran al acercarse el evento.
- **Días secos:**
  - En la garúa de Santa Rosa, P(> 20 mm) = 0 en ambos conjuntos. Es la prueba fácil.
  - En la temporada lluviosa de 2025 en Puerto Ayora, IFS dio P(> 20 mm) ≥ 20 % en la vecindad en 3 de 10 días secos. El peor fue el 22-feb-2025: 41 %, con 0 mm medidos. Con ese criterio acierta 6–7 de 10 eventos.
  - En la temporada lluviosa de 2026, ambos dan P ≈ 0,01–0,02 en los días secos.
- **IFS frente a AIFS (las 6 fechas con los dos):**
  - Con P(> 50 mm) ≥ 5 % en la vecindad, AIFS marca 4 de 6 eventos a 1 y 2 días y 0 de 25 días secos. IFS marca 2 de 6.
  - AIFS tiene colas más anchas. Medidos por AUC, los dos empatan: 0,82 con P(> 20 mm) y 0,93–0,95 con el p90 de los miembros.

## Qué significa para el pronóstico publicado

1. **La probabilidad cruda de los conjuntos no sirve tal cual.** El 30-oct no pasó del 6 % en el punto (IFS) ni del 18 % (AIFS) para más de 20 mm, con 238 mm medidos. Publicarla habría dicho «poco probable».
   - Confirma la decisión de la fase 0: la señal pública usa el consenso calibrado de los deterministas, y los conjuntos solo muestran el reparto en bloques de 6 h.
2. **AIFS ENS es el más prometedor para calibrar después.** Sus colas tocan los 100–200 mm en los eventos y casi no marcan los días secos.
   - El pronóstico en vivo archiva sus corridas (`/var/lib/sosgalapagos-clima/pronostico/archivo/`).
   - Con una temporada se podrá calibrar, por ejemplo, la fracción de miembros sobre un umbral o el percentil del p90 frente a su propia climatología, como ya se hace con los deterministas.
3. **Hay eventos que ningún modelo ve.** El 3-oct no aparece ni en los conjuntos ni en el consenso. El 14-jun no aparece en los conjuntos y en el consenso solo tuvo «señal moderada» el mismo día. Son lluvias locales que los modelos globales no resuelven, y el satélite tampoco vio el 3-oct. Para esos días solo quedan las estaciones.
