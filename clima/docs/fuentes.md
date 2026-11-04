# Fuentes meteorológicas de Galápagos (resumen sin enlaces)

El inventario completo, con endpoints, muestras y pruebas, está en `privado/fuentes.md` (no versionado). Aquí solo se nombran las fuentes.

| Fuente | Qué aporta | Estado en el proyecto |
|---|---|---|
| IERSE-WSN (Universidad del Azuay) | Lluvia, temperatura, humedad y presión cada 5 min en 4 estaciones de Santa Cruz | En el dashboard (llega por el puente) |
| GSC-USFQ | Lluvia, temperatura, radiación y humedad cada 5 min en San Cristóbal; lluvia diaria desde 2015 | En el dashboard |
| INAMHI | Lluvia cada 5 min en Puerto Ayora (M0191) y San Cristóbal; historial horario de 90 días | Historial archivado en `datos/inamhi/`; sin publicar |
| Mareógrafos IOC (Puerto Ayora, Baltra) | Nivel del mar por minuto | Sin integrar |
| METAR / SYNOP de los aeropuertos (Baltra, San Cristóbal) | Tiempo presente, presión, viento; lluvia en 6 h | Sin integrar |
| Modelos globales vía Open-Meteo (ECMWF IFS y AIFS, NOAA GFS, DWD ICON, UK Met Office, Météo-France, Canadá GEM, y sus conjuntos) | Pronóstico de lluvia a 7 días y archivo de pronósticos pasados (CC BY 4.0) | En el dashboard (pronóstico experimental calibrado; ver `pronostico/`) |
| GOES-19 (NOAA, archivo abierto en AWS): ABI banda 13, RRQPE y GLM | Tope de nube, lluvia estimada (~2 km) y rayos cada 10 min; llega ~10 min después del barrido. La producción de RRQPE tiene cortes (2-nov-2026) | Colector propio y panel (`satelite/`); evaluación en `satelite/evaluacion-s0.md`. Sin publicar |
| Satélite (IMERG, PERSIANN-CCS) | Lluvia estimada | Sin integrar |
