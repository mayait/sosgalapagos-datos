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
6. **Trabaja en tu rama** (mejor en un *worktree*) y no toques el dominio de otra sesión sin coordinarlo. Entre sesiones de Claude Code: `ListAgents` y `SendMessage`.

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
| Preparar y publicar /estudios (checklist, revisión) | `geodatos/estudios/PUBLICAR.md` |
| Tocar el clima | `clima/LEEME.md` |
| Tocar el pronóstico de lluvia | `clima/pronostico/LEEME.md` (evaluación en `fase0/informe.md`) |
