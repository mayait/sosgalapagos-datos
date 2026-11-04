"""Gestión del riesgo (sección 7): exposición de instalaciones críticas, recurrencia SNGR
y umbrales de lluvia para el SAT, para Santa Cruz y San Cristóbal.

Uso (desde geodatos/):  .venv/bin/python -I scripts/grd_riesgo_islas.py
Salidas: estudios/santa-cruz/datos/riesgo/ y estudios/san-cristobal/datos/riesgo/
Solo lee clima/datos/ierse-wsn/ (no ejecuta los scripts de clima/).
"""
import json, warnings
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform as st, unary_union
from shapely.strtree import STRtree
from pyproj import Transformer
from pysheds.grid import Grid

warnings.filterwarnings('ignore')
G = Path(__file__).resolve().parents[1]
F = G / 'capas/final'
CLIMA = G.parent / 'clima/datos/ierse-wsn'
T = Transformer.from_crs(4326, 32715, always_xy=True).transform
DEM = {'Santa Cruz': 'santa_cruz_dem.tif', 'San Cristóbal': 'san_cristobal_dem.tif'}
OUT = {'Santa Cruz': G / 'estudios/santa-cruz/datos/riesgo', 'San Cristóbal': G / 'estudios/san-cristobal/datos/riesgo'}


def load(fn, isla):
    fs = json.load(open(F / fn))['features']
    return [(shape(f['geometry']), f['properties']) for f in fs if f['properties'].get('isla') == isla]


def dem_tools(isla):
    p = G / 'descargas/dem_recortes' / DEM[isla]
    src = rasterio.open(p); dem = src.read(1).astype(float)
    grid = Grid.from_raster(str(p)); d = grid.read_raster(str(p))
    fill = np.asarray(grid.fill_depressions(grid.fill_pits(d)), dtype=float)
    dep = np.where(dem > -9000, fill - dem, 0)

    def samp(lon, lat):
        r, c = src.index(lon, lat)
        win = dem[max(r-1, 0):r+2, max(c-1, 0):c+2]  # 3x3 mediana para evitar celdas de edificio
        return float(np.median(win)), float(dep[r, c])
    return samp


def exposicion(isla, puntos):
    samp = dem_tools(isla)
    qb = [st(T, g) for g, _ in load('quebradas.geojson', isla)]
    tq = STRtree(qb)
    dr = [(st(T, g), p['area_drenada_km2']) for g, p in load('drenaje_derivado.geojson', isla) if p['area_drenada_km2'] >= 0.5]
    td = STRtree([g for g, _ in dr])
    lodo = [st(T, g) for g, p in load('riesgos_cgreg.geojson', isla) if p['tipo'].startswith('Flujos')]
    franja = unary_union([st(T, g) for g, _ in load('quebradas_franja20m_cgreg.geojson', isla)]) if load('quebradas_franja20m_cgreg.geojson', isla) else None
    susc = [(st(T, g), p['susceptibilidad']) for g, p in load('susceptibilidad_inundacion_zonas_pobladas.geojson', isla)]
    ts = STRtree([g for g, _ in susc])
    tsu = unary_union([st(T, g) for g, _ in load('tsunami_inundacion_inocar.geojson', isla)])
    parr = [(st(T, g), p['parroquia']) for g, p in load('parroquias.geojson', isla)]
    rows = []
    for tipo, nombre, fuente, lon, lat in puntos:
        P = Point(T(lon, lat)); z, dp = samp(lon, lat)
        i = tq.nearest(P); dq = P.distance(qb[i])
        near = [j for j in td.query(P.buffer(150))]
        k = td.nearest(P); dd = P.distance(dr[k][0])
        amax = max([dr[j][1] for j in near], default=0.0)
        sc = [susc[j][1] for j in ts.query(P) if susc[j][0].contains(P)]
        par = next((n for g, n in parr if g.contains(P)), None)
        if par is None and isla == 'Santa Cruz':
            par = 'BELLAVISTA (por exclusión; sin polígono CONALI)'
        rows.append(dict(isla=isla, parroquia=par or '', tipo=tipo, nombre=nombre, fuente=fuente,
                         lon=round(lon, 6), lat=round(lat, 6), cota_dsm_m=(round(z, 1) if z > -9000 else None), depresion_dsm_m=round(dp, 1),
                         dist_quebrada_igm_osm_m=round(dq), dist_drenaje_dsm_m=round(dd), area_drenada_km2_cauce_cercano=dr[k][1],
                         area_drenada_max_150m_km2=amax, susceptibilidad_hand=(sorted(sc)[0] if sc else 'fuera de zona evaluada / sin clase'),
                         flujo_lodo_cgreg=any(g.contains(P) for g in lodo), franja20m_cgreg=bool(franja and franja.contains(P)),
                         zona_tsunami_inocar=bool(tsu.contains(P))))
    return pd.DataFrame(rows)


def puntos_isla(isla, parroquias):
    pts = []
    for g, p in load('salud_msp.geojson', isla):
        pts.append(('salud_msp:' + (p.get('tipologia') or ''), p.get('nombre'), 'MSP vía SNGR 2023', g.x, g.y))
    for g, p in load('educacion_mineduc.geojson', isla):
        pts.append(('educacion_mineduc', p.get('nom_instit'), 'MINEDUC vía SNGR 2021', g.x, g.y))
    for g, p in load('puntos_clave.geojson', isla):
        if p['categoria'] in ('salud', 'educacion', 'emergencia', 'refugio', 'gobierno', 'energia') and p.get('subtipo') not in ('pharmacy', 'dentist', 'atm'):
            pts.append((f"{p['categoria']}:{p['subtipo']}", p.get('nombre'), p.get('fuente'), g.x, g.y))
    for g, p in load('albergues_sngr.geojson', isla):
        pts.append(('refugio_oficial_sngr', f"{p['nombre']} (cap. {p['capacidad_personas']} pers.)", 'SNGR, registro de refugios activos 2025', g.x, g.y))
    for g, p in load('tsunami_zonas_seguras.geojson', isla):
        pts.append(('zona_segura_tsunami', p.get('nombre'), 'SNGR', g.x, g.y))
    df = exposicion(isla, pts)
    df = df[df.parroquia.str.split(' ').str[0].isin(parroquias)]
    return df[df.lat < -0.56]  # excluye Baltra


def recurrencia(isla):
    rows = []
    for g, p in load('eventos_historicos.geojson', isla):
        if p.get('año') is None:  # registros sin fecha duplican eventos de 2025
            continue
        if p.get('evento') in ('Inundación', 'Aluvión (Flujos)', 'Deslizamiento', 'Socavamiento', 'Tormenta Eléctrica', 'Lluvias Intensas'):
            rows.append(dict(isla=isla, anio=p['año'], mes=p['mes'], evento=p['evento'], parroquia=p.get('parroquias'), sector=(p.get('sector') or '').strip(),
                             viviendas_afectadas=p.get('viviendas_afectadas'), familias_afectadas=p.get('familias_afectadas'),
                             fallecidas=p.get('fallecidas'), lon=round(g.x, 5), lat=round(g.y, 5)))
    return pd.DataFrame(rows).sort_values(['anio', 'mes'])


def umbrales_sat():
    s = pd.read_csv(CLIMA / 'serie_5min.csv.gz', parse_dates=['fecha_hora_local'])
    nombres = {'n_glps01': 'Cerro Crocker', 'n_glps05': 'Los Guayabillos', 'n_glps06': 'Militar', 'n_glps09': 'Santa Rosa'}
    rows, series = [], []
    for sid, g in s.groupby('estacion_id'):
        x = g.set_index('fecha_hora_local').sort_index()['lluvia_mm'].loc['2026-10-30 00:00':'2026-10-30 23:59']
        r1, r3, cum = x.rolling('60min').sum(), x.rolling('180min').sum(), x.cumsum()
        series.append(pd.DataFrame({'estacion': nombres[sid], 'lluvia_5min_mm': x, 'acum_1h_mm': r1.round(1), 'acum_3h_mm': r3.round(1), 'acum_dia_mm': cum.round(1)}))
        if x.sum() < 10:
            continue
        for ventana, ser, thr in [('1 h', r1, 20), ('1 h', r1, 30), ('1 h', r1, 40), ('3 h', r3, 50), ('3 h', r3, 80), ('desde 00:00', cum, 50), ('desde 00:00', cum, 100)]:
            for pulso, ini in [('cualquiera', '2026-10-30 00:00'), ('segundo pulso (desde 17:30)', '2026-10-30 17:30')]:
                y = ser.loc[ini:]
                if pulso != 'cualquiera' and ventana == 'desde 00:00':
                    continue
                t = y[y >= thr].index.min() if (y >= thr).any() else pd.NaT
                rows.append(dict(estacion=nombres[sid], ventana=ventana, umbral_mm=thr, pulso=pulso,
                                 primera_superacion_utc6=t, max_1h_movil_mm=round(r1.max(), 1), fin_max_1h_movil=r1.idxmax(),
                                 ultimo_registro=x.index.max(), total_registrado_mm=round(x.sum(), 1)))
    pd.DataFrame(rows).to_csv(OUT['Santa Cruz'] / 'umbrales_sat_30oct.csv', index=False)
    pd.concat(series).reset_index().rename(columns={'fecha_hora_local': 'fecha_hora_utc6'}).to_csv(OUT['Santa Cruz'] / 'lluvia_movil_30oct.csv', index=False)


def main():
    for d in OUT.values():
        d.mkdir(parents=True, exist_ok=True)
    extra_sc = [('escuela (sector inundado)', 'Escuela Tomás de Berlanga, vía Puerto Ayora–Bellavista (punto del encargo)', 'coordinador', -90.3198, -0.7109),
                ('estacion_ierse', 'Los Guayabillos', 'IERSE-WSN', -90.341962, -0.699079), ('estacion_ierse', 'Santa Rosa', 'IERSE-WSN', -90.403519, -0.654547),
                ('estacion_ierse', 'Cerro Crocker', 'IERSE-WSN', -90.326, -0.642398)]
    extra_scb = [('universidad', 'USFQ / Galapagos Science Center (punto del encargo)', 'coordinador', -89.6089, -0.8955)]
    sc = pd.concat([puntos_isla('Santa Cruz', ['BELLAVISTA', 'SANTA']), exposicion('Santa Cruz', extra_sc)])
    sc.to_csv(OUT['Santa Cruz'] / 'instalaciones_parte_alta.csv', index=False)
    scb = pd.concat([puntos_isla('San Cristóbal', ['PUERTO', 'EL']), exposicion('San Cristóbal', extra_scb)])
    scb.to_csv(OUT['San Cristóbal'] / 'instalaciones_criticas.csv', index=False)
    recurrencia('Santa Cruz').to_csv(OUT['Santa Cruz'] / 'recurrencia_sngr.csv', index=False)
    recurrencia('San Cristóbal').to_csv(OUT['San Cristóbal'] / 'recurrencia_sngr.csv', index=False)
    # capas CGREG de San Cristóbal
    rows = []
    for g, p in load('riesgos_cgreg.geojson', 'San Cristóbal'):
        rows.append(dict(tipo=p['tipo'], area_ha=round(st(T, g).area / 1e4, 1)))
    pd.DataFrame(rows).groupby('tipo').agg(poligonos=('area_ha', 'size'), area_ha=('area_ha', 'sum')).reset_index().to_csv(OUT['San Cristóbal'] / 'capas_cgreg_resumen.csv', index=False)
    umbrales_sat()
    print('ok')


if __name__ == '__main__':
    main()
