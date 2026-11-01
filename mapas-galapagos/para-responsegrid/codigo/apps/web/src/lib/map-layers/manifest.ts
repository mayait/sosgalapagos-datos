// Capas cartográficas por emergencia: formato del manifiesto (capas.json) y lógica pura de estilos.
//
// Una emergencia puede publicar en `<CAPAS_BASE_URL>/<slug>/capas.json` un manifiesto con mapas base,
// grupos de capas GeoJSON/raster, estilos de Leaflet, clasificaciones y leyendas. Este módulo no importa
// Leaflet en tiempo de ejecución (solo tipos), así que se prueba con `node --test`.
// La parte que crea capas de Leaflet está en ./leaflet-layers.ts. Especificación: docs/capas-emergencia.md.

import type { LatLngBoundsExpression, PathOptions } from 'leaflet';

export type Props = Record<string, unknown>;

/** Opciones de estilo de Leaflet más los campos propios de una clase de leyenda. */
export type LayerClass = PathOptions & {
  etiqueta?: string;
  /** Letra o símbolo dentro del marcador (solo capas de puntos). */
  simbolo?: string;
  radius?: number;
  /** Solo en `rangos`: límite superior (inclusive) del rango. */
  hasta?: number;
};

export interface StyleRule {
  propiedad: string;
  igual_a?: unknown;
  distinto_de?: unknown;
  estilo: PathOptions;
  etiqueta?: string;
}

export interface ManifestLayer {
  id: string;
  titulo: string;
  tipo: 'poligono' | 'linea' | 'punto' | 'raster';
  /** Ruta relativa al manifiesto, o absoluta (/… o https://…). */
  archivo?: string;
  /** Solo raster: PNG `raster/<region>_<raster>.png`, con límites en `raster/limites.json`. */
  raster?: string;
  opacidad?: number;
  visible?: boolean;
  /** Por debajo de este zoom la capa no se dibuja (capas pesadas). */
  zoom_min?: number;
  fuente?: string;
  descripcion?: string;
  elementos?: number;
  estilo?: PathOptions & { radius?: number };
  /** Línea de contorno dibujada debajo (p. ej. borde blanco de las quebradas). */
  borde?: PathOptions;
  filtro?: { propiedad: string; en: string[] };
  clasificar?: { propiedad: string; valores?: Record<string, LayerClass>; otro?: LayerClass; rangos?: LayerClass[] };
  /** Reglas que se aplican encima de la clase (p. ej. línea discontinua si no está validada). */
  estilo_si?: StyleRule[];
  /** Etiqueta del elemento: al pasar el ratón, o permanente (visible desde zoom 15). */
  rotulo?: { propiedad: string; permanente?: boolean; sufijo?: string };
  popup?: { titulo?: string; titulo_defecto?: string; sufijo_titulo?: string; campos?: Record<string, string> };
  /** Leyenda explícita [color, texto]; si falta se deriva de `clasificar`. */
  leyenda?: [string, string][];
  /** Relleno rayado SVG (p. ej. Parque Nacional). La capa usa fillColor: 'url(#<id>)'. */
  patron?: {
    id: string;
    color: string;
    separacion?: number;
    grosor?: number;
    fondo?: string;
    opacidad_fondo?: number;
    opacidad?: number;
  };
}

export interface BaseMap {
  id: string;
  titulo: string;
  url: string;
  atribucion: string;
  maxZoom?: number;
  maxNativeZoom?: number;
  defecto?: boolean;
}

export interface LayerGroupDef {
  id: string;
  titulo: string;
  capas: ManifestLayer[];
}

export interface LayersManifest {
  version: number;
  titulo?: string;
  generado?: string;
  mapas_base?: BaseMap[];
  /** Encuadres rápidos (botones «Ir a»). */
  islas?: Record<string, { bounds: LatLngBoundsExpression }>;
  grupos: LayerGroupDef[];
}

export interface LegendEntry {
  color?: string;
  texto?: string;
  forma: 'area' | 'linea' | 'punto';
  simbolo?: string;
  dash?: string;
}

/** Clase de leyenda que corresponde a las propiedades de un elemento (o null). */
export function classFor(layer: ManifestLayer, props: Props | null | undefined): LayerClass | null {
  const c = layer.clasificar;
  if (!c) return null;
  const v = props?.[c.propiedad];
  if (c.rangos) return c.rangos.find((r) => (Number(v) || 0) <= (r.hasta ?? Infinity)) ?? null;
  return c.valores?.[String(v)] ?? c.otro ?? null;
}

function matches(rule: StyleRule, props: Props | null | undefined): boolean {
  const v = props?.[rule.propiedad];
  if (rule.igual_a !== undefined) return v === rule.igual_a;
  if (rule.distinto_de !== undefined) return v !== rule.distinto_de;
  return false;
}

/** Opciones de Leaflet para un elemento: estilo base + clase + reglas. */
export function styleFor(layer: ManifestLayer, props: Props | null | undefined): PathOptions & { radius?: number } {
  const cls = classFor(layer, props) ?? {};
  const k: LayerClass = { ...cls };
  delete k.etiqueta;
  delete k.simbolo;
  delete k.hasta;
  let s: PathOptions & { radius?: number } = { ...layer.estilo, ...k };
  for (const r of layer.estilo_si ?? []) if (matches(r, props)) s = { ...s, ...r.estilo };
  return s;
}

/** Entradas de leyenda de una capa. */
export function legendFor(layer: ManifestLayer): LegendEntry[] {
  if (layer.leyenda) return layer.leyenda.map(([color, texto]) => ({ color, texto, forma: 'area' }));
  const forma: LegendEntry['forma'] = layer.tipo === 'linea' ? 'linea' : layer.tipo === 'punto' ? 'punto' : 'area';
  const c = layer.clasificar;
  const items: LayerClass[] = c
    ? [...(c.rangos ?? Object.values(c.valores ?? {})), ...(c.otro ? [c.otro] : [])]
    : [{ etiqueta: layer.titulo }];
  const out: LegendEntry[] = items.map((it) => {
    const s = { ...layer.estilo, ...it };
    const color = forma === 'linea' ? s.color : (s.fillColor ?? s.color);
    const e: LegendEntry = { forma };
    if (color) e.color = color;
    if (it.etiqueta) e.texto = it.etiqueta;
    if (it.simbolo) e.simbolo = it.simbolo;
    if (typeof s.dashArray === 'string') e.dash = s.dashArray;
    return e;
  });
  for (const r of layer.estilo_si ?? []) {
    if (!r.etiqueta) continue;
    const e: LegendEntry = { color: '#6b7280', texto: r.etiqueta, forma: 'linea' };
    if (typeof r.estilo.dashArray === 'string') e.dash = r.estilo.dashArray;
    out.push(e);
  }
  return out;
}

export function escapeHtml(s: unknown): string {
  return String(s ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c,
  );
}

const NUM = new Intl.NumberFormat('es');

function formatValue(v: unknown): string {
  if (v === true) return 'Sí';
  if (v === false) return 'No';
  if (typeof v === 'number') return NUM.format(v);
  return String(v);
}

/** HTML (escapado) del popup de un elemento según `layer.popup`. */
export function popupHtml(layer: ManifestLayer, props: Props): string {
  const p = layer.popup ?? {};
  const cls = classFor(layer, props);
  const raw = p.titulo ? props[p.titulo] : undefined;
  const title = raw != null && raw !== '' ? `${String(raw)}${p.sufijo_titulo ?? ''}` : (p.titulo_defecto ?? layer.titulo);
  const sub = cls?.etiqueta && cls.etiqueta !== title ? `${cls.etiqueta} · ` : '';
  let h = `<div style="font-size:12.5px;min-width:180px"><div style="font-weight:650;font-size:13.5px">${escapeHtml(title)}</div>`;
  h += `<div style="font-size:11px;color:#777;margin-bottom:6px">${escapeHtml(sub)}${escapeHtml(layer.titulo)}</div><table>`;
  for (const [k, label] of Object.entries(p.campos ?? {})) {
    const v = props[k];
    if (v == null || v === '') continue;
    h += `<tr><td style="color:#777;padding:1px 8px 1px 0;vertical-align:top">${escapeHtml(label)}</td><td>${escapeHtml(formatValue(v))}</td></tr>`;
  }
  return `${h}</table></div>`;
}

/** URL de un archivo del paquete: relativa a la base del manifiesto salvo que sea absoluta. */
export function resolveUrl(base: string, file: string): string {
  if (/^(https?:)?\//.test(file)) return file;
  return (base.endsWith('/') ? base : `${base}/`) + file;
}

/** Estado inicial de visibilidad: { idCapa: visible }. */
export function defaultVisibility(manifest: LayersManifest): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  for (const g of manifest.grupos) for (const c of g.capas) out[c.id] = Boolean(c.visible);
  return out;
}

/** ¿Se debe dibujar la capa con este zoom? */
export function isDrawable(layer: ManifestLayer, on: boolean, zoom: number): boolean {
  return on && !(layer.zoom_min != null && zoom < layer.zoom_min);
}
