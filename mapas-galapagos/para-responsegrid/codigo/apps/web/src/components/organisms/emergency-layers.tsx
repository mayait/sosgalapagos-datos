'use client';

// Capas cartográficas de una emergencia (mapas base, amenazas, hidrografía, población, puntos clave…).
//
// Busca el manifiesto en `<NEXT_PUBLIC_CAPAS_BASE_URL | /capas>/<slug>/capas.json`. Si la emergencia no
// tiene manifiesto, se comporta como antes: solo el mapa base de OpenStreetMap. Si lo tiene, pinta los
// mapas base y las capas declaradas, y muestra un panel con interruptores, leyendas y botones «Ir a».
// Formato del manifiesto: docs/capas-emergencia.md.

import L from 'leaflet';
import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { TileLayer, useMap } from 'react-leaflet';
import { useLocale } from '@/i18n/locale-context';
import { getMessages } from '@/i18n';
import {
  defaultVisibility,
  escapeHtml,
  isDrawable,
  legendFor,
  type LayersManifest,
  type LegendEntry,
  type ManifestLayer,
} from '@/lib/map-layers/manifest';
import { capasBaseUrl, createLayer, loadManifest, prepareMap, type LayerContext } from '@/lib/map-layers/leaflet-layers';

const OSM_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
/** Los rótulos permanentes (barrios…) se ocultan por debajo de este zoom. */
const LABELS_MIN_ZOOM = 15;
const OSM_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

function LegendSwatch({ e }: { e: LegendEntry }) {
  if (e.forma === 'punto') {
    return (
      <span
        className="mr-1.5 inline-block h-3.5 w-3.5 rounded-full border-[1.5px] border-white text-center align-[-3px] text-[9px] font-bold leading-[11px] text-white shadow-[0_0_0_1px_rgba(0,0,0,.25)]"
        style={{ background: e.color }}
      >
        {e.simbolo ?? ''}
      </span>
    );
  }
  if (e.forma === 'linea') {
    return (
      <span
        className="mr-1.5 inline-block w-4 align-[3px]"
        style={{ borderTop: `3px ${e.dash ? 'dashed' : 'solid'} ${e.color ?? '#555'}` }}
      />
    );
  }
  return <span className="mr-1.5 inline-block h-2.5 w-4 rounded-sm align-[-1px]" style={{ background: e.color }} />;
}

export function EmergencyLayers({ slug }: { slug?: string | undefined }) {
  const map = useMap();
  const t = getMessages(useLocale()).ui;
  const base = useMemo(() => (slug ? capasBaseUrl(slug) : null), [slug]);
  const [manifest, setManifest] = useState<LayersManifest | null | undefined>(slug ? undefined : null);
  const [on, setOn] = useState<Record<string, boolean>>({});
  const [zoom, setZoom] = useState(() => map.getZoom());
  const [baseId, setBaseId] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const ctxRef = useRef<LayerContext | null>(null);
  const built = useRef<Record<string, L.Layer>>({});
  const panelRef = useRef<HTMLDivElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  // 1) Manifiesto
  useEffect(() => {
    if (!base) return;
    let cancelled = false;
    void loadManifest(base).then((m) => {
      if (cancelled) return;
      setManifest(m);
      if (!m) return;
      ctxRef.current = prepareMap(map, base);
      setOn(defaultVisibility(m));
      setBaseId(m.mapas_base?.find((b) => b.defecto)?.id ?? m.mapas_base?.[0]?.id ?? null);
      // El panel de capas arranca siempre colapsado; se abre con el botón «Capas».
    });
    return () => {
      cancelled = true;
    };
  }, [base, map]);

  // 2) Zoom (capas con zoom_min)
  useEffect(() => {
    const onZoom = () => {
      setZoom(map.getZoom());
      map.getContainer().classList.toggle('rg-capas-lejos', map.getZoom() < LABELS_MIN_ZOOM);
    };
    onZoom();
    map.on('zoomend', onZoom);
    return () => {
      map.off('zoomend', onZoom);
    };
  }, [map]);

  // 3) Mapa base del manifiesto
  useEffect(() => {
    const def = manifest?.mapas_base?.find((b) => b.id === baseId);
    if (!def) return;
    const opts: L.TileLayerOptions = { attribution: def.atribucion, maxZoom: def.maxZoom ?? 19 };
    if (def.maxNativeZoom != null) opts.maxNativeZoom = def.maxNativeZoom;
    const tl = L.tileLayer(def.url, opts).addTo(map);
    tl.bringToBack();
    return () => {
      map.removeLayer(tl);
    };
  }, [manifest, baseId, map]);

  // 4) Capas: se (re)añaden en el orden del manifiesto para conservar el apilado
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!manifest || !ctx) return;
    let cancelled = false;
    const all = manifest.grupos.flatMap((g) => g.capas);
    void (async () => {
      for (const layer of all) {
        const want = isDrawable(layer, Boolean(on[layer.id]), zoom);
        if (want && !built.current[layer.id]) {
          try {
            built.current[layer.id] = await createLayer(layer, ctx);
          } catch (err) {
            console.error(`[EmergencyLayers] no se pudo cargar la capa ${layer.id}:`, err);
            continue;
          }
        }
        if (cancelled) return;
      }
      for (const layer of all) {
        const l = built.current[layer.id];
        if (l && map.hasLayer(l)) map.removeLayer(l);
      }
      for (const layer of all) {
        const l = built.current[layer.id];
        if (l && isDrawable(layer, Boolean(on[layer.id]), zoom)) l.addTo(map);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [manifest, on, zoom, map]);

  // 5) Al desmontar, quitar todo
  useEffect(() => {
    const layers = built.current;
    return () => {
      for (const l of Object.values(layers)) map.removeLayer(l);
    };
  }, [map]);

  // 6) El panel no debe arrastrar ni hacer zoom en el mapa
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    L.DomEvent.disableClickPropagation(el);
    L.DomEvent.disableScrollPropagation(el);
  }, [manifest, open]);

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    try {
      const data = JSON.parse(await file.text()) as GeoJSON.GeoJsonObject;
      const layer = L.geoJSON(data, {
        style: { color: '#c2410c', weight: 2.5, fillOpacity: 0.18, dashArray: '6 6' },
        onEachFeature: (f, l) => {
          const rows = Object.entries((f.properties ?? {}) as Record<string, unknown>)
            .filter(([, v]) => v != null && v !== '')
            .map(([k, v]) => `<tr><td style="color:#6b7280;padding-right:6px">${escapeHtml(k)}</td><td>${escapeHtml(v)}</td></tr>`)
            .join('');
          l.bindPopup(`<table style="font-size:12px">${rows}</table>`);
        },
      }).addTo(map);
      const b = layer.getBounds();
      if (b.isValid()) map.fitBounds(b, { padding: [30, 30] });
      setMsg(t.map_layers_upload_ok.replace('{name}', file.name));
    } catch {
      setMsg(t.map_layers_upload_error);
    }
    setTimeout(() => setMsg(null), 5000);
  };

  // Sin manifiesto (o mientras carga): mapa base de siempre.
  if (!manifest) return <TileLayer url={OSM_URL} attribution={OSM_ATTR} />;

  const toggle = (id: string) => setOn((s) => ({ ...s, [id]: !s[id] }));

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="absolute right-3 top-3 z-[1000] rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-ink shadow hover:bg-surface"
        >
          {t.map_layers_button}
        </button>
      )}
      {open && (
        <div
          ref={panelRef}
          className="absolute right-3 top-3 z-[1000] flex max-h-[calc(100%-1.5rem)] w-[min(20rem,calc(100%-1.5rem))] flex-col overflow-hidden rounded-xl border border-line bg-white/95 text-ink shadow-lg backdrop-blur"
        >
          <div className="flex items-center justify-between border-b border-line px-3 py-2">
            <span className="text-sm font-semibold">{manifest.titulo ?? t.map_layers_title}</span>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded px-2 text-lg leading-none text-muted hover:text-ink"
              aria-label={t.map_layers_close}
            >
              ×
            </button>
          </div>
          <div className="overflow-y-auto px-3 pb-3">
            {manifest.islas && (
              <div className="pt-2">
                <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wide text-muted">{t.map_layers_goto}</div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(manifest.islas).map(([name, v]) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => map.fitBounds(v.bounds)}
                      className="rounded-full border border-line bg-surface px-2 py-0.5 text-xs hover:border-ink"
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {manifest.mapas_base && manifest.mapas_base.length > 1 && (
              <div className="pt-2">
                <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wide text-muted">{t.map_layers_basemap}</div>
                <div className="inline-flex overflow-hidden rounded-md border border-line">
                  {manifest.mapas_base.map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => setBaseId(b.id)}
                      className={`px-2 py-1 text-xs ${b.id === baseId ? 'bg-navy text-white' : 'text-muted hover:text-ink'}`}
                    >
                      {b.titulo}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {manifest.grupos.map((g) => (
              <div key={g.id} className="border-b border-line py-2 last:border-0">
                <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wide text-muted">{g.titulo}</div>
                {g.capas.map((c: ManifestLayer) => {
                  const active = Boolean(on[c.id]);
                  const far = active && c.zoom_min != null && zoom < c.zoom_min;
                  return (
                    <div key={c.id} className="py-1">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={active}
                        onClick={() => toggle(c.id)}
                        className="flex w-full items-start gap-2 text-left"
                      >
                        <span
                          className={`relative mt-0.5 h-4 w-7 flex-none rounded-full transition ${active ? 'bg-navy' : 'bg-line-strong'}`}
                        >
                          <span
                            className={`absolute top-0.5 h-3 w-3 rounded-full bg-white shadow transition-all ${active ? 'left-3.5' : 'left-0.5'}`}
                          />
                        </span>
                        <span className="flex-1 text-[13px] leading-tight">
                          {c.titulo}
                          {c.fuente && <span className="block text-[10.5px] text-muted">{c.fuente}</span>}
                        </span>
                      </button>
                      {far && (
                        <div className="ml-9 mt-0.5 text-[11px] text-accent-600">
                          {t.map_layers_zoom_hint.replace('{zoom}', String(c.zoom_min))}
                        </div>
                      )}
                      {active && (
                        <div className="ml-9 mt-1 grid gap-0.5 text-[11px] text-muted">
                          {c.descripcion && <div className="italic">{c.descripcion}</div>}
                          {legendFor(c).map((e, i) => (
                            <span key={i}>
                              <LegendSwatch e={e} />
                              {e.texto}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="mt-2 w-full rounded-md border border-dashed border-line-strong px-2 py-1.5 text-xs font-semibold text-ink hover:bg-surface"
              title={t.map_layers_upload_hint}
            >
              {t.map_layers_upload}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".geojson,.json,application/geo+json,application/json"
              className="hidden"
              onChange={(e) => void onFile(e)}
            />
          </div>
        </div>
      )}
      {msg && (
        <div className="absolute bottom-3 left-1/2 z-[1000] -translate-x-1/2 rounded-md bg-ink/90 px-3 py-1 text-xs text-white">
          {msg}
        </div>
      )}
    </>
  );
}
