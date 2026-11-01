import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classFor,
  styleFor,
  legendFor,
  popupHtml,
  resolveUrl,
  defaultVisibility,
  isDrawable,
  type ManifestLayer,
  type LayersManifest,
} from './manifest.ts';

const susc: ManifestLayer = {
  id: 'susc',
  titulo: 'Susceptibilidad',
  tipo: 'poligono',
  estilo: { weight: 0.6, fillOpacity: 0.38 },
  clasificar: {
    propiedad: 'nivel',
    valores: {
      '1': { etiqueta: 'Baja', color: '#aaa', fillColor: '#bbb' },
      '3': { etiqueta: 'Alta', color: '#111', fillColor: '#222', fillOpacity: 0.5 },
    },
    otro: { etiqueta: 'Otro', fillColor: '#999' },
  },
};

test('classFor: valor exacto (número convertido a texto) y "otro" como respaldo', () => {
  assert.equal(classFor(susc, { nivel: 3 })?.etiqueta, 'Alta');
  assert.equal(classFor(susc, { nivel: '1' })?.etiqueta, 'Baja');
  assert.equal(classFor(susc, { nivel: 7 })?.etiqueta, 'Otro');
  assert.equal(classFor({ ...susc, clasificar: undefined }, { nivel: 3 }), null);
});

test('classFor: rangos por "hasta" inclusive', () => {
  const pob: ManifestLayer = {
    id: 'pob',
    titulo: 'Población',
    tipo: 'poligono',
    clasificar: {
      propiedad: 'p',
      rangos: [
        { hasta: 0, etiqueta: 'Sin dato' },
        { hasta: 10, etiqueta: '1–10' },
        { hasta: 1e9, etiqueta: '>10' },
      ],
    },
  };
  assert.equal(classFor(pob, { p: 0 })?.etiqueta, 'Sin dato');
  assert.equal(classFor(pob, { p: 10 })?.etiqueta, '1–10');
  assert.equal(classFor(pob, { p: 11 })?.etiqueta, '>10');
  assert.equal(classFor(pob, {})?.etiqueta, 'Sin dato');
});

test('styleFor: mezcla base + clase sin campos de leyenda, y aplica estilo_si', () => {
  const s = styleFor(susc, { nivel: 3 });
  assert.deepEqual(s, { weight: 0.6, fillOpacity: 0.5, color: '#111', fillColor: '#222' });
  const areas: ManifestLayer = {
    ...susc,
    estilo_si: [{ propiedad: 'estado', distinto_de: 'validada', estilo: { dashArray: '7 6' }, etiqueta: 'Por validar' }],
  };
  assert.equal(styleFor(areas, { nivel: 1, estado: 'por_validar' }).dashArray, '7 6');
  assert.equal(styleFor(areas, { nivel: 1, estado: 'validada' }).dashArray, undefined);
});

test('legendFor: deriva de la clasificación y añade las reglas con etiqueta', () => {
  const l = legendFor({ ...susc, estilo_si: [{ propiedad: 'e', igual_a: 1, estilo: { dashArray: '2 2' }, etiqueta: 'Regla' }] });
  assert.deepEqual(
    l.map((e) => [e.texto, e.color, e.forma]),
    [
      ['Baja', '#bbb', 'area'],
      ['Alta', '#222', 'area'],
      ['Otro', '#999', 'area'],
      ['Regla', '#6b7280', 'linea'],
    ],
  );
  const linea = legendFor({ id: 'q', titulo: 'Quebradas', tipo: 'linea', estilo: { color: '#00f', dashArray: '4 2' } });
  assert.deepEqual(linea, [{ forma: 'linea', color: '#00f', texto: 'Quebradas', dash: '4 2' }]);
  assert.deepEqual(legendFor({ ...susc, leyenda: [['#0f0', 'Parque']] }), [{ color: '#0f0', texto: 'Parque', forma: 'area' }]);
});

test('popupHtml: título, campos con etiqueta y escapado de HTML', () => {
  const layer: ManifestLayer = {
    ...susc,
    popup: { titulo: 'nombre', titulo_defecto: 'Sin nombre', campos: { detalle: 'Detalle', ok: 'Validada', vacio: 'Vacío' } },
  };
  const h = popupHtml(layer, { nombre: '<b>La Cascada</b>', nivel: 3, detalle: 'Agua & lodo', ok: true, vacio: '' });
  assert.match(h, /&lt;b&gt;La Cascada&lt;\/b&gt;/);
  assert.match(h, /Alta · Susceptibilidad/);
  assert.match(h, /Agua &amp; lodo/);
  assert.match(h, /<td>Sí<\/td>/);
  assert.doesNotMatch(h, /Vacío/);
  assert.match(popupHtml(layer, { nivel: 1 }), /Sin nombre/);
});

test('resolveUrl: relativa a la base, salvo rutas absolutas', () => {
  assert.equal(resolveUrl('/capas/x', 'a.geojson'), '/capas/x/a.geojson');
  assert.equal(resolveUrl('/capas/x/', 'a.geojson'), '/capas/x/a.geojson');
  assert.equal(resolveUrl('/capas/x/', '/otro/a.geojson'), '/otro/a.geojson');
  assert.equal(resolveUrl('/capas/x/', 'https://cdn.example.org/a.geojson'), 'https://cdn.example.org/a.geojson');
});

test('defaultVisibility e isDrawable respetan visible y zoom_min', () => {
  const m: LayersManifest = {
    version: 2,
    grupos: [{ id: 'g', titulo: 'G', capas: [{ ...susc, visible: true }, { ...susc, id: 'b', zoom_min: 15 }] }],
  };
  assert.deepEqual(defaultVisibility(m), { susc: true, b: false });
  const b = m.grupos[0]!.capas[1]!;
  assert.equal(isDrawable(b, true, 14), false);
  assert.equal(isDrawable(b, true, 15), true);
  assert.equal(isDrawable(b, false, 18), false);
});
