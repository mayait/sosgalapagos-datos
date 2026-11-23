# Reproducir los cálculos del clima

Scripts que reproducen lo que calcula [sosgalapagos.org/clima](https://sosgalapagos.org/clima/) **solo con los datos públicos**: el ZIP [`clima_galapagos_todo.zip`](https://sosgalapagos.org/clima/datos/descargas/clima_galapagos_todo.zip). Usan Python 3.9 o más, sin dependencias. La guía completa, con el formato de los datos y sus trampas, está en [`../PARA-AGENTES.md`](../PARA-AGENTES.md).

## `nivel.py`: nivel de lluvia peligrosa por zona

Es la misma regla que corre la plataforma ([`clima/nivel.py`](https://github.com/mayait/sosgalapagos-plataforma/blob/main/clima/nivel.py) de `sosgalapagos-plataforma`). La lee de `regla/umbrales_inundacion.json` del ZIP.

```bash
python3 -I nivel.py --verificar                       # los dos desbordamientos de La Cascada; debe terminar en OK
python3 -I nivel.py --zona la-cascada --desde 2026-11-20T12:00Z --hasta 2026-11-22T00:00Z
python3 -I nivel.py --desde 2026-11-20T12:00Z --hasta 2026-11-22T00:00Z --salida niveles.csv
python3 -I nivel.py --comparar                        # contra lo que publicó la página
python3 -I nivel.py --zip clima_galapagos_todo.zip …  # con un ZIP ya bajado (si no, lo baja a ~/.cache/sosgalapagos/)
```

**Opciones:**
- `--sin-manual`: no aplica los niveles subidos por reportes de campo.
- `--silencio`: aplica el «silencio en alerta» suponiendo que la recolección funcionó. Ese dato no está en el ZIP.

**Resultados de referencia** (ZIP del 23-nov-2026):

```
2026-10-30 la-cascada: desbordamiento 2026-10-31T03:20:00Z · medio 2026-10-30T21:10:00Z · alto 2026-10-30T21:40:00Z · muy alto 2026-10-31T02:35:00Z (0.8 h antes)
2026-11-21 la-cascada: desbordamiento 2026-11-21T11:00:00Z · medio 2026-11-20T18:45:00Z · alto 2026-11-21T08:25:00Z · muy alto 2026-11-21T08:50:00Z (2.2 h antes)
OK: la regla llega a «muy alto» antes de los dos desbordamientos.

Contra lo publicado: 1468 pasadas · nivel instantáneo igual en 99.8% · nivel mostrado igual en 99.8%
```

Si cambia la regla (`regla/umbrales_inundacion.json`) o se corrigen datos, estas horas pueden moverse. El nivel es un **modelo propio y preliminar, no una alerta oficial**.
