# Fuentes meteorológicas de Galápagos (resumen sin enlaces)

El inventario completo, con endpoints, muestras y pruebas, está en `privado/fuentes.md` (no versionado). Aquí solo se nombran las fuentes.

| Fuente | Qué aporta | Estado en el proyecto |
|---|---|---|
| IERSE-WSN (Universidad del Azuay) | Lluvia, temperatura, humedad y presión cada 5 min en 4 estaciones de Santa Cruz | En el dashboard (llega por el puente) |
| GSC-USFQ | Lluvia, temperatura, radiación y humedad cada 5 min en San Cristóbal; lluvia diaria desde 2015 | En el dashboard |
| INAMHI | Lluvia cada 5 min en Puerto Ayora (M0191) y San Cristóbal; historial horario de 90 días | Historial archivado en `datos/inamhi/`; sin publicar |
| Mareógrafos IOC (Puerto Ayora, Baltra) | Nivel del mar por minuto | Sin integrar |
| METAR / SYNOP de los aeropuertos (Baltra, San Cristóbal) | Tiempo presente, presión, viento; lluvia en 6 h | Sin integrar |
| Satélite (PERSIANN-CCS, GOES, IMERG) y modelos (Open-Meteo, MET Norway) | Lluvia estimada y pronóstico | Sin integrar |
