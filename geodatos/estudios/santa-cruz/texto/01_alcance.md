# 1. Alcance y cómo se hizo

> **Este estudio es totalmente preliminar.** Es un reconocimiento de gabinete. **No es un diseño de ingeniería, ni un mapa oficial de amenaza, ni un dictamen profesional.** Ninguna cifra sustituye a un levantamiento topográfico, a la calibración con mediciones de campo ni a un modelo hidráulico bidimensional. Ningún punto se ha visitado.

**Quién lo hizo.** Lo elaboró un sistema de inteligencia artificial (Claude, de Anthropic) organizado como **comité de agentes especializados**, a pedido de la coordinación de respuesta de USFQ Galápagos:
- un asesor en hidrología e hidráulica;
- un especialista en meteorología;
- un especialista en gestión del riesgo de desastres;
- un especialista en planificación urbana y drenaje;
- un hidrólogo dedicado a San Cristóbal, que trabajó en un estudio aparte.

Cada especialista trabajó con los mismos datos. Sus discrepancias se resolvieron de forma explícita y un revisor científico independiente revisó la versión de La Cascada. Lo que falta es la revisión de **profesionales habilitados**, que es imprescindible antes de usar estas conclusiones para cualquier decisión.

**Con qué datos.**
- **Elevación:** modelo de superficie Copernicus GLO-30 (30 m). Incluye techos y vegetación, tiene un error vertical de ±2–4 m y un sesgo de unos −2 m respecto del IGM.
- **Cartografía:** IGM 1:25 000 y OpenStreetMap (31-oct-2026).
- **Edificios:** OSM y Google Open Buildings.
- **Población:** INEC.
- **Registros y capas de riesgo:** SNGR y CGREG.
- **Lluvia medida:** red IERSE-WSN de la Universidad del Azuay, con cuatro estaciones en Santa Cruz, una medición cada 5 minutos y datos desde abril de 2026.
- **Climatología:** Fundación Charles Darwin, 1965–2026.
- **Lluvia estimada por modelos:** Open-Meteo (ECMWF y otros).

**Convenciones.**
- Las horas son de Galápagos (UTC−6).
- Las cotas son del DSM.
- Se distingue siempre lo **medido [M]**, lo **estimado [E]** y lo **reportado [R]**.
- Se usa el término «refugio» para los lugares de acogida temporal.

**Reproducibilidad.** Todo se regenera con los scripts `12` a `20` de `geodatos/scripts/` del repositorio público, a partir de los datos de `geodatos/estudios/`. Las capas y tablas se pueden descargar al final de esta página.
