// Motor de capas guiado por manifiesto (capas.json) para Leaflet.
// Es la misma lógica que usa geodatos/visor/index.html, tipada para ResponseGrid.
// Destino sugerido: app/apps/web/src/components/organisms/galapagos/capas-manifiesto.ts

import L from 'leaflet';

export type Props = Record<string, unknown>;
type Clase = L.PathOptions & { etiqueta?: string; simbolo?: string; radius?: number; hasta?: number };

export interface CapaManifiesto {
  id: string;
  titulo: string;
  tipo: 'poligono' | 'linea' | 'punto' | 'raster';
  archivo?: string;
  raster?: string;
  opacidad?: number;
  visible?: boolean;
  zoom_min?: number;
  fuente?: string;
  descripcion?: string;
  elementos?: number;
  estilo?: L.PathOptions & { radius?: number };
  borde?: L.PathOptions;
  filtro?: { propiedad: string; en: string[] };
  clasificar?: { propiedad: string; valores?: Record<string, Clase>; otro?: Clase; rangos?: Clase[] };
  rotulo?: { propiedad: string; permanente?: boolean; zoom_min?: number; sufijo?: string };
  popup?: { titulo?: string; titulo_defecto?: string; sufijo_titulo?: string; campos?: Record<string, string> };
  leyenda?: [string, string][];
  /** Estilo condicional, p. ej. línea discontinua cuando estado ≠ 'validada'. Se aplica sobre la clasificación. */
  estilo_si?: { propiedad: string; igual_a?: string; distinto_de?: string; estilo: L.PathOptions; etiqueta?: string }[];
  /** Relleno rayado SVG (Parque Nacional). La capa usa fillColor: 'url(#<id>)'. */
  patron?: { id: string; color: string; separacion?: number; grosor?: number; fondo?: string; opacidad_fondo?: number; opacidad?: number };
}
export interface Manifiesto {
  version: number;
  islas: Record<string, { bounds: L.LatLngBoundsExpression }>;
  grupos: { id: string; titulo: string; capas: CapaManifiesto[] }[];
}
export interface EntradaLeyenda { color?: string; texto?: string; forma: 'area' | 'linea' | 'punto'; simbolo?: string; dash?: string }

export function claseDe(capa: CapaManifiesto, props: Props | null | undefined): Clase | null {
  const c = capa.clasificar;
  if (!c) return null;
  const v = props?.[c.propiedad];
  if (c.rangos) return c.rangos.find((r) => (Number(v) || 0) <= (r.hasta ?? Infinity)) ?? null;
  return c.valores?.[String(v)] ?? c.otro ?? null;
}

export function estiloDe(capa: CapaManifiesto, props: Props | null | undefined): L.PathOptions & { radius?: number } {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { etiqueta, simbolo, hasta, ...k } = claseDe(capa, props) ?? {};
  let estilo: L.PathOptions & { radius?: number } = { ...capa.estilo, ...k };
  for (const regla of capa.estilo_si ?? []) {
    const v = String(props?.[regla.propiedad] ?? '');
    const aplica =
      (regla.igual_a !== undefined && v === regla.igual_a) ||
      (regla.distinto_de !== undefined && v !== regla.distinto_de);
    if (aplica) estilo = { ...estilo, ...regla.estilo };
  }
  return estilo;
}

export function leyendaDe(capa: CapaManifiesto): EntradaLeyenda[] {
  if (capa.leyenda) return capa.leyenda.map(([color, texto]) => ({ color, texto, forma: 'area' }));
  const forma = capa.tipo === 'linea' ? 'linea' : capa.tipo === 'punto' ? 'punto' : 'area';
  const c = capa.clasificar;
  const items: Clase[] = c
    ? [...(c.rangos ?? Object.values(c.valores ?? {})), ...(c.otro ? [c.otro] : [])]
    : [{ etiqueta: capa.titulo }];
  const entradas: EntradaLeyenda[] = items.map((it) => {
    const s = { ...capa.estilo, ...it };
    return {
      color: forma === 'linea' ? s.color : (s.fillColor ?? s.color),
      texto: it.etiqueta,
      forma,
      simbolo: it.simbolo,
      dash: s.dashArray as string | undefined,
    };
  });
  for (const regla of capa.estilo_si ?? []) {
    if (!regla.etiqueta) continue;
    entradas.push({ color: regla.estilo.color ?? '#555', texto: regla.etiqueta, forma: 'linea', dash: (regla.estilo.dashArray as string | undefined) ?? '6 6' });
  }
  return entradas;
}

const esc = (s: unknown) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
const NUM = new Intl.NumberFormat('es-EC');
const fmt = (v: unknown) => (v === true ? 'Sí' : v === false ? 'No' : typeof v === 'number' ? NUM.format(v) : v);

export function popupDe(capa: CapaManifiesto, props: Props): string {
  const p = capa.popup ?? {};
  const cls = claseDe(capa, props);
  const raw = p.titulo ? props[p.titulo] : undefined;
  const titulo = raw != null && raw !== '' ? `${String(raw)}${p.sufijo_titulo ?? ''}` : (p.titulo_defecto ?? capa.titulo);
  const sub = cls?.etiqueta && cls.etiqueta !== titulo ? `${cls.etiqueta} · ` : '';
  let h = `<div style="font-size:12.5px"><div style="font-weight:650;font-size:13.5px">${esc(titulo)}</div>`;
  h += `<div style="font-size:11px;color:#777;margin-bottom:6px">${esc(sub)}${esc(capa.titulo)}</div><table>`;
  for (const [k, lab] of Object.entries(p.campos ?? {})) {
    const v = props[k];
    if (v == null || v === '') continue;
    h += `<tr><td style="color:#777;padding-right:8px;vertical-align:top">${esc(lab)}</td><td>${esc(fmt(v))}</td></tr>`;
  }
  return `${h}</table></div>`;
}

export interface Contexto {
  base: string; // p. ej. '/galapagos/capas/'
  cache: Record<string, GeoJSON.FeatureCollection>;
  limites?: Record<string, { bounds: L.LatLngBoundsExpression }>;
  renderers: { areas: L.Renderer; lineas: L.Renderer; puntos: L.Renderer };
}

/**
 * Crea los panes y renderers con el orden de apilado correcto (áreas < líneas < puntos).
 * gp-puntos (580) queda bajo markerPane (600): los acopios y necesidades de ResponseGrid se ven encima.
 */
export function prepararMapa(map: L.Map, base: string): Contexto {
  const panes: [string, number][] = [['gp-fondo', 350], ['gp-parque', 390], ['gp-areas', 410], ['gp-lineas', 430], ['gp-puntos', 580]];
  for (const [n, z] of panes) {
    const pane = map.getPane(n) ?? map.createPane(n);
    pane.style.zIndex = String(z);
  }
  map.getPane('gp-fondo')!.style.pointerEvents = 'none';
  return {
    base,
    cache: {},
    renderers: {
      areas: L.canvas({ pane: 'gp-areas', padding: 0.3 }),
      lineas: L.canvas({ pane: 'gp-lineas', padding: 0.3 }),
      puntos: L.canvas({ pane: 'gp-puntos', padding: 0.3 }),
    },
  };
}

/** Renderer SVG con patrón de rayas; Leaflet pinta fill="url(#id)" y el navegador aplica el patrón. */
export function rendererPatron(pt: NonNullable<CapaManifiesto['patron']>, pane: string): L.Renderer {
  const r = L.svg({ pane });
  r.on('add', () => {
    const svg = (r as unknown as { _container?: SVGSVGElement })._container;
    if (!svg || svg.querySelector(`#${pt.id}`)) return;
    const s = pt.separacion ?? 8;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML =
      `<pattern id="${pt.id}" patternUnits="userSpaceOnUse" width="${s}" height="${s}" patternTransform="rotate(45)">` +
      `<rect width="${s}" height="${s}" fill="${pt.fondo ?? 'none'}" fill-opacity="${pt.opacidad_fondo ?? 0}"/>` +
      `<line x1="0" y1="0" x2="0" y2="${s}" stroke="${pt.color}" stroke-width="${pt.grosor ?? 1.5}" stroke-opacity="${pt.opacidad ?? 0.6}"/></pattern>`;
    svg.insertBefore(defs, svg.firstChild);
  });
  return r;
}

/** Opcional: velo oscuro fuera del área de interés. Con la capa del parque rayada ya no hace falta. */
export async function crearMascara(ctx: Contexto): Promise<L.Layer> {
  const aoi = (await (await fetch(`${ctx.base}area_interes.geojson`)).json()) as GeoJSON.FeatureCollection;
  const holes = aoi.features.flatMap((f) => {
    const g = f.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
    return polys.map((p) => p[0]!.map(([x, y]) => [y, x] as L.LatLngTuple));
  });
  const world: L.LatLngTuple[] = [[-5, -95], [-5, -85], [3, -85], [3, -95]];
  return L.layerGroup([
    L.polygon([world, ...holes], { pane: 'gp-fondo', stroke: false, fillColor: '#1f2a37', fillOpacity: 0.28, interactive: false }),
    L.geoJSON(aoi, { pane: 'gp-fondo', style: { color: '#1f2a37', weight: 1, opacity: 0.5, fill: false }, interactive: false }),
  ]);
}

export async function crearCapa(capa: CapaManifiesto, ctx: Contexto): Promise<L.Layer> {
  if (capa.tipo === 'raster') {
    ctx.limites ??= (await (await fetch(`${ctx.base}raster/limites.json`)).json()) as Contexto['limites'];
    // Una imagen por isla, y solo se descarga la de la isla que está a la vista
    // (el relieve pesa ~1 MB por isla; en Galápagos la conexión es lenta).
    const imagenes = Object.entries(ctx.limites!).map(([k, v]) =>
      L.imageOverlay(`${ctx.base}raster/${k}_${capa.raster}.png`, v.bounds as L.LatLngBoundsExpression, {
        opacity: capa.opacidad ?? 0.7,
        pane: 'gp-fondo',
        className: capa.raster === 'relieve' ? 'gp-multiply' : '',
      }),
    );
    const grupo = L.layerGroup();
    let mapa: L.Map | null = null;
    const enVista = () => {
      if (!mapa) return;
      const vista = mapa.getBounds().pad(0.25);
      for (const img of imagenes) {
        const toca = vista.intersects(img.getBounds());
        if (toca && !grupo.hasLayer(img)) grupo.addLayer(img);
        else if (!toca && grupo.hasLayer(img)) grupo.removeLayer(img);
      }
    };
    grupo.on('add', (e) => {
      mapa = (e.target as L.LayerGroup & { _map: L.Map })._map;
      mapa.on('moveend', enVista);
      enVista();
    });
    grupo.on('remove', () => {
      mapa?.off('moveend', enVista);
      mapa = null;
    });
    return grupo;
  }
  const archivo = capa.archivo!;
  ctx.cache[archivo] ??= (await (await fetch(ctx.base + archivo)).json()) as GeoJSON.FeatureCollection;
  const gj = ctx.cache[archivo]!;
  const filter = capa.filtro
    ? (f: GeoJSON.Feature) => capa.filtro!.en.includes(String((f.properties as Props | null)?.[capa.filtro!.propiedad]))
    : undefined;
  const key = capa.tipo === 'punto' ? 'puntos' : capa.tipo === 'linea' ? 'lineas' : 'areas';
  const pane = capa.patron ? 'gp-parque' : `gp-${key}`;
  const renderer = capa.patron ? rendererPatron(capa.patron, pane) : ctx.renderers[key];
  const grupo = L.layerGroup();
  if (capa.borde) {
    grupo.addLayer(L.geoJSON(gj, { filter, pane, renderer, interactive: false, style: () => ({ ...capa.borde, lineCap: 'round' }) } as L.GeoJSONOptions));
  }
  const main = L.geoJSON(gj, {
    filter,
    pane,
    renderer,
    style: (f) => ({ lineCap: 'round', lineJoin: 'round', ...estiloDe(capa, f?.properties as Props) }),
    pointToLayer: (f, ll) => {
      const props = (f.properties ?? {}) as Props;
      const s = estiloDe(capa, props);
      const cl = claseDe(capa, props);
      const riesgo = Boolean(props['en_susc_alta_media']);
      if (cl?.simbolo) {
        return L.marker(ll, {
          pane,
          icon: L.divIcon({
            className: '',
            iconSize: [19, 19],
            html: `<div style="width:19px;height:19px;border-radius:50%;background:${s.fillColor};color:#fff;font:800 11px/15px system-ui;text-align:center;border:2px solid #fff;box-shadow:${riesgo ? '0 0 0 3px #1d4a9e,' : ''}0 1px 4px rgba(0,0,0,.45)">${esc(cl.simbolo)}</div>`,
          }),
        });
      }
      return L.circleMarker(ll, {
        pane,
        renderer,
        radius: s.radius ?? 5,
        color: riesgo ? '#1d4a9e' : '#fff',
        weight: riesgo ? 2.5 : 1.3,
        fillColor: s.fillColor,
        fillOpacity: 1,
      });
    },
    onEachFeature: (f, l) => {
      const props = (f.properties ?? {}) as Props;
      l.bindPopup(() => popupDe(capa, props));
      const r = capa.rotulo;
      const txt = r ? props[r.propiedad] : undefined;
      if (r && txt != null && txt !== '') {
        l.bindTooltip(
          esc(txt) + (r.sufijo ?? ''),
          r.permanente ? { permanent: true, direction: 'center', className: 'gp-rotulo' } : { sticky: true },
        );
      }
    },
  } as L.GeoJSONOptions);
  grupo.addLayer(main);
  return grupo;
}

/** CSS mínimo que necesita el motor (añadir a globals.css). */
export const CSS_CAPAS = `
.gp-multiply{mix-blend-mode:multiply}
.gp-rotulo{background:transparent;border:0;box-shadow:none;color:#7c2d12;font:600 11px system-ui;text-shadow:0 0 3px #fff,0 0 3px #fff}
.gp-rotulo::before{display:none}
.gp-lejos .gp-rotulo{display:none}
`;
