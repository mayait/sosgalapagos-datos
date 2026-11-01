// Crea capas de Leaflet a partir del manifiesto de capas de una emergencia (ver ./manifest.ts).

import L from 'leaflet';
import {
  classFor,
  escapeHtml,
  popupHtml,
  resolveUrl,
  styleFor,
  type LayersManifest,
  type ManifestLayer,
  type Props,
} from './manifest';

export interface LayerContext {
  /** URL base del paquete, terminada en «/» (p. ej. /capas/galapagos-2026/). */
  base: string;
  cache: Record<string, GeoJSON.FeatureCollection>;
  limits?: Record<string, { bounds: L.LatLngBoundsExpression }>;
  renderers: { areas: L.Renderer; lineas: L.Renderer; puntos: L.Renderer };
}

/** Panes en orden de apilado: raster < áreas rayadas < áreas < líneas < puntos (los marcadores de la app van en markerPane, 600). */
const PANES: [string, number][] = [
  ['rg-capas-fondo', 350],
  ['rg-capas-patron', 390],
  ['rg-capas-areas', 410],
  ['rg-capas-lineas', 430],
  ['rg-capas-puntos', 590],
];

export function capasBaseUrl(slug: string): string {
  const root = process.env.NEXT_PUBLIC_CAPAS_BASE_URL ?? '/capas';
  return `${root.replace(/\/$/, '')}/${encodeURIComponent(slug)}/`;
}

export async function loadManifest(base: string): Promise<LayersManifest | null> {
  try {
    const res = await fetch(resolveUrl(base, 'capas.json'), { cache: 'no-cache' });
    if (!res.ok) return null;
    const m = (await res.json()) as LayersManifest;
    return Array.isArray(m?.grupos) ? m : null;
  } catch {
    return null;
  }
}

export function prepareMap(map: L.Map, base: string): LayerContext {
  for (const [name, z] of PANES) {
    const pane = map.getPane(name) ?? map.createPane(name);
    pane.style.zIndex = String(z);
  }
  map.getPane('rg-capas-fondo')!.style.pointerEvents = 'none';
  return {
    base,
    cache: {},
    renderers: {
      areas: L.canvas({ pane: 'rg-capas-areas', padding: 0.3 }),
      lineas: L.canvas({ pane: 'rg-capas-lineas', padding: 0.3 }),
      puntos: L.canvas({ pane: 'rg-capas-puntos', padding: 0.3 }),
    },
  };
}

/** Renderer SVG con patrón de rayas; Leaflet pinta fill="url(#id)" y el navegador aplica el patrón. */
function patternRenderer(pt: NonNullable<ManifestLayer['patron']>, pane: string): L.Renderer {
  const r = L.svg({ pane });
  r.on('add', () => {
    const svg = (r as unknown as { _container?: SVGSVGElement })._container;
    if (!svg || svg.querySelector(`#${pt.id}`)) return;
    const s = pt.separacion ?? 8;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML =
      `<pattern id="${escapeHtml(pt.id)}" patternUnits="userSpaceOnUse" width="${s}" height="${s}" patternTransform="rotate(45)">` +
      `<rect width="${s}" height="${s}" fill="${escapeHtml(pt.fondo ?? 'none')}" fill-opacity="${pt.opacidad_fondo ?? 0}"/>` +
      `<line x1="0" y1="0" x2="0" y2="${s}" stroke="${escapeHtml(pt.color)}" stroke-width="${pt.grosor ?? 1.5}" stroke-opacity="${pt.opacidad ?? 0.6}"/></pattern>`;
    svg.insertBefore(defs, svg.firstChild);
  });
  return r;
}

/** Crea la capa de Leaflet de una entrada del manifiesto (descarga el archivo la primera vez). */
export async function createLayer(layer: ManifestLayer, ctx: LayerContext): Promise<L.Layer> {
  if (layer.tipo === 'raster') {
    if (!ctx.limits) {
      const res = await fetch(resolveUrl(ctx.base, 'raster/limites.json'), { cache: 'no-cache' });
      ctx.limits = (await res.json()) as LayerContext['limits'];
    }
    return L.layerGroup(
      Object.entries(ctx.limits ?? {}).map(([region, v]) =>
        L.imageOverlay(resolveUrl(ctx.base, `raster/${region}_${layer.raster}.png`), v.bounds, {
          opacity: layer.opacidad ?? 0.7,
          pane: 'rg-capas-fondo',
          className: layer.raster === 'relieve' ? 'rg-capas-multiply' : '',
        }),
      ),
    );
  }
  const file = layer.archivo!;
  if (!ctx.cache[file]) {
    const res = await fetch(resolveUrl(ctx.base, file), { cache: 'no-cache' });
    ctx.cache[file] = (await res.json()) as GeoJSON.FeatureCollection;
  }
  const data = ctx.cache[file]!;
  const filter = layer.filtro
    ? (f: GeoJSON.Feature) => layer.filtro!.en.includes(String((f.properties as Props | null)?.[layer.filtro!.propiedad]))
    : undefined;
  const key = layer.tipo === 'punto' ? 'puntos' : layer.tipo === 'linea' ? 'lineas' : 'areas';
  const pane = layer.patron ? 'rg-capas-patron' : `rg-capas-${key}`;
  const renderer = layer.patron ? patternRenderer(layer.patron, pane) : ctx.renderers[key];
  const group = L.layerGroup();
  if (layer.borde) {
    const casing: L.GeoJSONOptions = { pane, interactive: false, style: () => ({ ...layer.borde, lineCap: 'round' }) };
    if (filter) casing.filter = filter;
    group.addLayer(L.geoJSON(data, { ...casing, renderer } as L.GeoJSONOptions));
  }
  const options: L.GeoJSONOptions = {
    pane,
    style: (f) => ({ lineCap: 'round', lineJoin: 'round', ...styleFor(layer, f?.properties as Props) }),
    pointToLayer: (f, latlng) => {
      const props = (f.properties ?? {}) as Props;
      const s = styleFor(layer, props);
      const cls = classFor(layer, props);
      const risk = Boolean(props['en_susc_alta_media']);
      if (cls?.simbolo) {
        return L.marker(latlng, {
          pane,
          icon: L.divIcon({
            className: '',
            iconSize: [19, 19],
            html: `<div style="width:19px;height:19px;border-radius:50%;background:${escapeHtml(s.fillColor)};color:#fff;font:800 11px/15px system-ui;text-align:center;border:2px solid #fff;box-shadow:${risk ? '0 0 0 3px #1d4a9e,' : ''}0 1px 4px rgba(0,0,0,.45)">${escapeHtml(cls.simbolo)}</div>`,
          }),
        });
      }
      const opts: L.CircleMarkerOptions = {
        pane,
        renderer,
        radius: s.radius ?? 5,
        color: risk ? '#1d4a9e' : '#fff',
        weight: risk ? 2.5 : 1.3,
        fillOpacity: 1,
      };
      if (s.fillColor) opts.fillColor = s.fillColor;
      return L.circleMarker(latlng, opts);
    },
    onEachFeature: (f, l) => {
      const props = (f.properties ?? {}) as Props;
      l.bindPopup(() => popupHtml(layer, props));
      const r = layer.rotulo;
      const txt = r ? props[r.propiedad] : undefined;
      if (r && txt != null && txt !== '') {
        l.bindTooltip(
          escapeHtml(txt) + escapeHtml(r.sufijo ?? ''),
          r.permanente ? { permanent: true, direction: 'center', className: 'rg-capas-rotulo' } : { sticky: true },
        );
      }
    },
  };
  if (filter) options.filter = filter;
  group.addLayer(L.geoJSON(data, { ...options, renderer } as L.GeoJSONOptions));
  return group;
}
