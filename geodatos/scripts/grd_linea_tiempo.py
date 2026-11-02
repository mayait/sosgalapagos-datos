"""Línea del tiempo del evento de Santa Cruz (28-ago a 2-nov-2026), en hora de Galápagos (UTC−6).

Uso (desde geodatos/):  .venv/bin/python -I scripts/grd_linea_tiempo.py
Salida: estudios/santa-cruz/datos/linea_tiempo.csv
Combina filas documentales (informes oficiales y prensa, escritas aquí con su fuente)
con filas calculadas a partir de la red IERSE-WSN (clima/datos/ierse-wsn/, solo lectura).
Regla de husos: las horas de la SNGR nacional, el INAMHI y la prensa continental se dan en la
fuente en hora de Ecuador continental (UTC−5) salvo que digan lo contrario; se restan 60 min y se
marca «huso de la fuente incierto» en la descripción.
"""
from pathlib import Path
import pandas as pd

G = Path(__file__).resolve().parents[1]
CL = G.parent / 'clima/datos/ierse-wsn'
OUT = G / 'estudios/santa-cruz/datos/linea_tiempo.csv'

U_SR01 = 'https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SITREP-Nro.-01-Lluvias_Galapagos_29.08.2026-31.10.2026.pdf'
U_SR67 = 'https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/11/SitRep-No-67-Lluvias-29082026-al-01112026-15h00f21.pdf'
U_R193 = 'https://www.gestionderiesgos.gob.ec/wp-content/uploads/2026/07/RESOLUCION-Nro-193_Cambio-alerta-naranja-El-Nino-f-signed-signed-signed-signed.pdf'
U_ERF10 = 'https://www.teleamazonas.com/uploads/files/2026/10/07/erfen_20261001.pdf'
U_IERSE = 'Red IERSE-WSN, Universidad del Azuay (datos de estación)'
U_NOTI = 'https://fmmundo.com/notimundo/actualidad/santa-cruz-emergencia-intensas-lluvias-inundaciones-dejan-fallecido-dos-desaparecidos-n89575'
U_DIARIO = 'https://www.eldiario.ec/ambiente/emergencia-en-galapagos-danos-electricos-habilitacion-vial-y-retorno-de-vuelos-en-baltra-31102026/'
U_COM = 'https://www.elcomercio.com/actualidad/ecuador/galapagos-en-emergencia-por-inundaciones-y-evacuaciones-en-santa-cruz/'
U_VIST = 'https://www.vistazo.com/actualidad/2026-10-31-galapagos-mantiene-emergencia-inundaciones-ocasionadas-intensas-lluvias-CD11300417'
U_EXTRA = 'https://www.extra.ec/noticia/ecuador/advertencia-inamhi-llovera-ecuador-29-octubre-1-noviembre-166444.html'
INF = 'estudios/la-cascada/texto/03_lluvias.md (fuente original del INAMHI por enlazar)'
HID = 'estudios/la-cascada/texto/04_hidrologia.md §4.7; datos/hidrogramas_evento_30oct.csv'

DOC = [
    # fecha_hora_utc6, precision, tipo, actor, descripcion, fuente_url, confianza
    ('2026-06-24', 'día', 'respuesta', 'COE provincial de Galápagos', 'COE provincial activado (fecha de activación según la tabla de COE del SitRep 67).', U_SR67, 'media'),
    ('2026-07-20', 'día', 'alerta_oficial', 'SNGR', 'Resolución SNGR-193-2026: alerta naranja por El Niño; incluye Puerto Ayora, Bellavista y Santa Rosa. Art. 5: protocolos de evacuación preventiva.', U_R193, 'alta'),
    ('2026-08-28', 'día', 'alerta_oficial', 'CN-ERFEN', 'Informe Técnico Ejecutivo ERFEN 007-2026 declara oficialmente el evento El Niño en el país.', U_SR01, 'alta'),
    ('2026-08-29', 'día', 'alerta_oficial', 'SNGR', 'Resolución SNGR-238-2026: alerta ROJA en todo el territorio nacional (evento El Niño en curso).', U_SR67, 'alta'),
    ('2026-10-01', 'día', 'pronostico', 'CN-ERFEN', 'Informe ERFEN 010-2026: El Niño activo; semejanza oceánica con 1997–98.', U_ERF10, 'media'),
    ('2026-10-29 12:00', 'aprox', 'pronostico', 'INAMHI', 'Advertencia n.º 84 (13H00 29-oct a 23H00 1-nov; huso de la fuente incierto, se asume UTC−5): para la región insular, «eventos leves en el archipiélago».', U_SR01, 'alta'),
    ('2026-10-30', 'día', 'pronostico', 'INAMHI / prensa', 'Notas de prensa del 29–30 oct repiten la advertencia 84: lluvias leves en Galápagos; alta intensidad puntual solo en Isabela.', U_EXTRA, 'media'),
    ('2026-10-30 21:25', 'minuto', 'dato_faltante', 'IERSE-WSN', 'Los Guayabillos (21:25) y Santa Rosa (21:22) dejan de transmitir a la vez; vuelven a las 18:42–18:45 del 31-oct (≈21 h sin datos).', U_IERSE, 'alta'),
    ('2026-10-30', 'día', 'impacto_reportado', 'SNGR', '«Tarde y noche del 30/10»: desbordamiento de varias cañadas rurales (El Aguacatal, Guayabillos, El Occidente) y en Puerto Ayora (Parque Artesanal, El Bosque).', U_SR01, 'alta'),
    ('2026-10-30', 'día', 'impacto_reportado', 'SNGR / COE provincial', 'Una persona fallecida por el desbordamiento de la cañada El Aguacatal (Bellavista). La hora no consta en las fuentes consultadas.', U_SR67, 'alta'),
    ('2026-10-30', 'día', 'impacto_reportado', 'SNGR', 'Puerto Ayora: vías anegadas «por las precipitaciones de las últimas dos horas»; bomberos y agua potable evacúan agua con un hidrocleaner. Hora no consta.', U_SR01, 'alta'),
    ('2026-10-30', 'día', 'respuesta', 'COE cantonal de Santa Cruz', 'Declaratoria de estado de emergencia cantonal (fecha 30-oct según el SitRep 67; algunos medios la sitúan el 31). Hora no encontrada.', U_SR67, 'media'),
    ('2026-10-30 22:00', 'aprox', 'respuesta', 'Ministerio de Desarrollo Humano / Policía / PNG', 'Evacuaciones «durante la noche y madrugada», priorizando grupos vulnerables; la DPNG usa tres botes zodiac en La Cascada. Horas exactas no constan.', U_SR01, 'media'),
    ('2026-10-30 21:00', 'aprox', 'impacto_reportado', 'Prensa', 'La prensa sitúa la lluvia «entre las 22:00 del 30 y las 06:00 del 31», sin huso (si es continental: 21:00–05:00 UTC−6). No concuerda con lo medido (pico 20–21 h).', INF, 'baja'),
    ('2026-10-30 14:20', 'aprox', 'hidrologia_modelada', 'Asesor hidrológico', 'Modelo con lluvia medida: caudal > 1 m³/s en la entrada de La Cascada desde 14:20–17:00 según el escenario.', HID, 'media'),
    ('2026-10-30 16:50', 'aprox', 'hidrologia_modelada', 'Asesor hidrológico', 'Vaso de La Cascada lleno hasta su rebose (12,95 m DSM): 16:50–18:10 en el escenario central; 15:40–19:45 en todos.', HID, 'media'),
    ('2026-10-30 21:40', 'aprox', 'hidrologia_modelada', 'Asesor hidrológico', 'Pico de la crecida en La Cascada: 21:40–22:50 (central; 21:30–22:50 en todos), 155–600 m³/s. Lámina máxima 21:35–23:10.', HID, 'media'),
    ('2026-10-31 00:00', 'aprox', 'hidrologia_modelada', 'Asesor hidrológico', 'La lámina vuelve a la cota de rebose entre 00:00 y 08:00; quedan 42 000–62 000 m³ sin salida por gravedad.', HID, 'baja'),
    ('2026-10-31 05:00', 'aprox', 'pronostico', 'ECMWF IFS 9 km (modelo)', 'El modelo situaba el máximo a las 05–06 h del 31-oct; lo medido lo sitúa a las 20–21 h del 30-oct. Desfase ≈9 h.', INF, 'alta'),
    ('2026-10-31', 'día', 'impacto_reportado', 'ELECGALÁPAGOS / prensa', 'Alimentador 203 (zona rural: Bellavista, Santa Rosa, Aguacatal) fuera de servicio; 4 postes y 1 torre dañados. Hora de inicio no consta.', U_DIARIO, 'media'),
    ('2026-10-31', 'día', 'impacto_reportado', 'Prensa (ECU 911 / COE)', 'Balance preliminar: 1 fallecido en Bellavista y 2 desaparecidos en el sector Divino Niño (Santa Cruz); unas 80 personas evacuadas. Desaparecidos sin confirmación posterior.', U_COM, 'media'),
    ('2026-10-31', 'día', 'impacto_reportado', 'COE cantonal / prensa', 'Vía Parque Artesanal–Bellavista interrumpida; se pide evitar Puerto Ayora–Bellavista. Una vivienda colapsa en Miramar.', U_NOTI, 'media'),
    ('2026-10-31 08:00', 'hora', 'impacto_reportado', 'Autoridad aeronáutica', 'Aeropuerto de Baltra suspende operaciones de 08:00 a 12:00 (huso de la fuente incierto); solo vuelos de emergencia y ayuda humanitaria.', U_NOTI, 'media'),
    ('2026-10-31', 'día', 'impacto_reportado', 'SNGR (San Cristóbal)', 'San Cristóbal: desbordamiento de las cañadas Barrio Frío y Divino Niño «durante la mañana del 31/10»; calles anegadas en Puerto Baquerizo Moreno.', U_SR01, 'alta'),
    ('2026-10-31 14:00', 'aprox', 'alerta_oficial', 'INAMHI', 'Alerta roja de corto plazo n.º 59, vigente desde las 15:00 del 31-oct (huso probablemente continental): se emitió después del pico medido.', INF, 'media'),
    ('2026-10-31 14:30', 'aprox', 'respuesta', 'SNGR', 'Corte del SitRep 01 de Galápagos (15:30 en la fuente; huso incierto). Su cabecera dice «publicado 31-oct 7:17», lo que es incoherente con el corte.', U_SR01, 'alta'),
    ('2026-10-31 14:30', 'aprox', 'impacto_reportado', 'SNGR', 'SitRep 01: 1 fallecido; 43 familias y 175 personas afectadas; 165 en refugios (Coliseo Cerrado de Deportes y Casa de los Mormones); 700 con familias acogientes.', U_SR01, 'alta'),
    ('2026-10-31 14:30', 'aprox', 'impacto_reportado', 'MSP / SNGR', 'Centro de Salud Santa Cruz «incomunicado e inaccesible» por la inundación de sus instalaciones y accesos; UPC La Cascada y edificio DINAF con daños.', U_SR01, 'alta'),
    ('2026-10-31 15:00', 'hora', 'respuesta', 'Autoridad aeronáutica / MTOP', 'Reanudación prevista de vuelos comerciales en Baltra y paso controlado en la vía a Itabaca desde las 15:00 de Galápagos.', U_DIARIO, 'media'),
    ('2026-10-31', 'día', 'respuesta', 'SNGR / Fuerzas Armadas', 'Envío de 800 kits humanitarios y 250 kits para dormir (C-130 Guayaquil–Baltra); guardacostas «Isla San Cristóbal» hacia Baltra.', U_SR01, 'alta'),
    ('2026-10-31 18:45', 'minuto', 'lluvia_medida', 'IERSE-WSN', 'Los Guayabillos y Santa Rosa vuelven a transmitir; 31-oct con 21–22 % de cobertura. La lluvia de la noche del 30 al 31 no se midió.', U_IERSE, 'alta'),
    ('2026-11-01 14:00', 'aprox', 'impacto_reportado', 'SNGR', 'SitRep 67 (corte 15:00, huso incierto): 3 120 personas y 780 familias afectadas en la provincia, pero el texto dice «60 familias»; incoherencia interna.', U_SR67, 'alta'),
    ('2026-11-01 14:00', 'aprox', 'impacto_reportado', 'SNGR', 'SitRep 67: Centro de Salud Santa Cruz inoperativo; 3 689 usuarios sin energía (ya restablecida); refugio Coliseo Cerrado con 76 personas (19 familias).', U_SR67, 'alta'),
    ('2026-11-01 14:00', 'aprox', 'pronostico', 'INAMHI', 'Advertencia n.º 85 (15H00 1-nov a 10H00 4-nov; huso incierto): eventos muy fuertes «de manera ocasional en las islas Galápagos».', U_SR67, 'alta'),
    ('2026-11-02', 'día', 'dato_faltante', 'FCD / INAMHI', 'Sin datos públicos de las estaciones de la FCD (Puerto Ayora, Bellavista) ni del INAMHI para el evento.', INF, 'alta'),
]


def medidas():
    h = pd.read_csv(CL / 'horario.csv', parse_dates=['fecha_hora_local'])
    h = h[(h.fecha_hora_local >= '2026-10-30 12:00') & (h.fecha_hora_local <= '2026-10-31 12:00')]
    piv = h.pivot_table(index='fecha_hora_local', columns='estacion', values='lluvia_mm')
    rows = []
    for t, r in piv.iterrows():
        partes = [f"{e} {r[e]:.1f}".replace(".", ",") for e in ['Los Guayabillos', 'Santa Rosa', 'Cerro Crocker', 'Militar'] if e in r and pd.notna(r[e])]
        if not partes:
            continue
        rows.append((t.strftime('%Y-%m-%d %H:%M'), 'hora', 'lluvia_medida', 'IERSE-WSN',
                     f"Lluvia {t:%H}–{(t + pd.Timedelta('1h')):%H} h (mm): " + '; '.join(partes) + '.', U_IERSE, 'alta'))
    u = pd.read_csv(G / 'estudios/santa-cruz/datos/riesgo/umbrales_sat_30oct.csv', parse_dates=['primera_superacion_utc6'])
    sel = [('Santa Rosa', '1 h', 30, 'cualquiera'), ('Santa Rosa', '3 h', 50, 'cualquiera'), ('Los Guayabillos', '1 h', 30, 'cualquiera'),
           ('Santa Rosa', '1 h', 30, 'segundo pulso (desde 17:30)'), ('Los Guayabillos', '3 h', 50, 'cualquiera'), ('Los Guayabillos', 'desde 00:00', 100, 'cualquiera'),
           ('Santa Rosa', 'desde 00:00', 100, 'cualquiera')]
    for est, v, thr, pul in sel:
        x = u[(u.estacion == est) & (u.ventana == v) & (u.umbral_mm == thr) & (u.pulso == pul)].iloc[0]
        t = x.primera_superacion_utc6
        txt = {'1 h': f'≥ {thr} mm en 1 h móvil', '3 h': f'≥ {thr} mm en 3 h móviles', 'desde 00:00': f'≥ {thr} mm acumulados en el día'}[v]
        extra = ' (segundo pulso)' if pul != 'cualquiera' else ''
        rows.append((t.strftime('%Y-%m-%d %H:%M'), 'minuto', 'lluvia_medida', 'IERSE-WSN (cálculo propio)',
                     f'{est}: se supera {txt}{extra}. Umbral ilustrativo, no oficial.', U_IERSE, 'alta'))
    for est in ['Los Guayabillos', 'Santa Rosa']:
        x = u[u.estacion == est].iloc[0]
        t = pd.Timestamp(x.fin_max_1h_movil)
        rows.append((t.strftime('%Y-%m-%d %H:%M'), 'minuto', 'lluvia_medida', 'IERSE-WSN (cálculo propio)',
                     f'{est}: máximo de 1 h móvil, {str(x.max_1h_movil_mm).replace('.', ',')} mm (60 min hasta esta hora). Total registrado del día: {str(x.total_registrado_mm).replace('.', ',')} mm (mínimo).', U_IERSE, 'alta'))
    return rows


def main():
    cols = ['fecha_hora_utc6', 'precision', 'tipo', 'actor', 'descripcion', 'fuente_url', 'confianza']
    df = pd.DataFrame(DOC + medidas(), columns=cols)
    # las filas con precisión «día» se ordenan al final de su día (ocurrieron en algún momento de ese día)
    df['_k'] = pd.to_datetime(df.fecha_hora_utc6, format='mixed') + pd.to_timedelta((df.precision == 'día') * 1439, unit='min')
    df = df.sort_values(['_k', 'tipo'], kind='stable').drop(columns='_k')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(len(df), 'filas ->', OUT)


if __name__ == '__main__':
    main()
