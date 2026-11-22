/* Mapa de lluvia y viento de modelos, al estilo de Windy, para el panel de /clima/.
 *
 * Lee el JSON que escribe la plataforma (clima/lluvia_mapa.py → datos/lluvia-mapa.json): una rejilla
 * regular con la lluvia cada 3 h y el viento a 10 m de varios modelos, un byte por celda.
 * Dibuja la lluvia interpolada en un canvas (bilineal en el espacio, lineal en el tiempo), una línea
 * de tiempo con reproducción y, si se quiere, partículas de viento en un canvas propio.
 *
 * Es lluvia de MODELO, no medida ni oficial, y los modelos globales se quedan muy cortos en las islas.
 * El mapa lo dice a la vista. El pronóstico oficial es del INAMHI.
 *
 * Uso:
 *   <link rel="stylesheet" href="lluvia-mapa.css"><script src="lluvia-mapa.js"></script>
 *   LluviaMapa.montar(document.getElementById("lluvia"), {datos: "datos/lluvia-mapa.json"});
 * Necesita Leaflet 1.9 (window.L). Si no está, lo carga de cdnjs.
 */
(function () {
  "use strict";

  const ZONA = "Pacific/Galapagos"; // UTC−6, sin horario de verano
  const LEAFLET = ["https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js",
                   "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"];
  const SUBMUESTREO = 8;      // píxeles del canvas por celda de la rejilla
  const SEG_POR_CUADRO = 0.9; // al reproducir: segundos por cada 3 h

  // Paletas (valor, [r, g, b, a]). Tonos de Windy: azul claro → azul → verde → amarillo → naranja → rojo → magenta.
  const PALETAS = {
    hora: {unidad: "mm/h · prom. 3 h", marcas: [1, 3, 10, 20, 40], max: 60, paradas: [
      [0.1, [120, 180, 235, 0]], [0.3, [110, 170, 235, 110]], [0.7, [70, 130, 225, 170]], [1.5, [45, 95, 210, 200]],
      [3, [40, 175, 205, 210]], [5, [55, 190, 95, 220]], [8, [235, 220, 55, 230]], [13, [245, 150, 40, 235]],
      [20, [230, 55, 45, 240]], [32, [205, 40, 150, 245]], [50, [150, 70, 225, 250]], [60, [235, 210, 255, 250]]]},
    dia: {unidad: "mm en 24 h", marcas: [5, 20, 50, 100, 150], max: 200, paradas: [
      [0.5, [120, 180, 235, 0]], [1.5, [110, 170, 235, 110]], [4, [70, 130, 225, 170]], [8, [45, 95, 210, 200]],
      [14, [40, 175, 205, 210]], [22, [55, 190, 95, 220]], [35, [235, 220, 55, 230]], [55, [245, 150, 40, 235]],
      [80, [230, 55, 45, 240]], [115, [205, 40, 150, 245]], [160, [150, 70, 225, 250]], [200, [235, 210, 255, 250]]]},
  };
  const N_LUT = 512;

  // Escala de la paleta: raíz cuadrada (como la codificación), para dar detalle a la lluvia débil.
  const aEscala = (v, max) => Math.sqrt(Math.max(0, v) / max);

  function tabla(p) {
    const lut = new Uint8ClampedArray(N_LUT * 4);
    for (let i = 0; i < N_LUT; i++) {
      const v = Math.pow(i / (N_LUT - 1), 2) * p.max;
      let k = 0;
      while (k < p.paradas.length - 1 && p.paradas[k + 1][0] < v) k++;
      const [v0, c0] = p.paradas[k], [v1, c1] = p.paradas[Math.min(k + 1, p.paradas.length - 1)];
      const f = v <= v0 ? 0 : v1 === v0 ? 1 : Math.min(1, (v - v0) / (v1 - v0));
      for (let c = 0; c < 4; c++) lut[i * 4 + c] = v < p.paradas[0][0] ? 0 : c0[c] + (c1[c] - c0[c]) * f;
    }
    return lut;
  }
  Object.values(PALETAS).forEach(p => { p.lut = tabla(p); });

  // ── Formatos de hora (siempre en hora de Galápagos) ──────────────────────
  const fHora = new Intl.DateTimeFormat("es-EC", {timeZone: ZONA, hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  const fDia = new Intl.DateTimeFormat("es-EC", {timeZone: ZONA, weekday: "short", day: "numeric", month: "short"});
  const fDiaCorto = new Intl.DateTimeFormat("es-EC", {timeZone: ZONA, weekday: "short", day: "numeric"});
  const fCorrida = new Intl.DateTimeFormat("es-EC", {timeZone: ZONA, day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  const diaLocal = t => new Date(t - 6 * 3600e3).toISOString().slice(0, 10);
  const num = (v, d = 1) => v.toLocaleString("es-EC", {maximumFractionDigits: d, minimumFractionDigits: 0});
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  const PUNTOS_CARDINALES = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"];

  function cargarLeaflet() {
    if (window.L && window.L.version) return Promise.resolve(window.L);
    return new Promise((ok, mal) => {
      const css = document.createElement("link");
      css.rel = "stylesheet"; css.href = LEAFLET[1]; document.head.appendChild(css);
      const s = document.createElement("script");
      s.src = LEAFLET[0]; s.onload = () => ok(window.L); s.onerror = () => mal(new Error("No se pudo cargar Leaflet"));
      document.head.appendChild(s);
    });
  }

  // ── Datos ────────────────────────────────────────────────────────────────
  function decodificar(b64) {
    const s = atob(b64), a = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
    return a;
  }

  class Datos {
    constructor(j) {
      this.j = j;
      this.g = j.rejilla;
      this.n = this.g.nlat * this.g.nlon;
      this.horas = j.horas.map(h => Date.parse(h));
      this.cache = new Map();
    }
    modelo(id) { return this.j.modelos.find(m => m.id === id) || this.j.modelos[0]; }
    // mm en las 3 h que terminan en horas[i] (NaN = sin dato)
    lluvia3h(id, i) {
      const k = "l" + id + i;
      if (!this.cache.has(k)) {
        const b = decodificar(this.modelo(id).lluvia[i]), a = new Float32Array(this.n);
        for (let c = 0; c < this.n; c++) a[c] = b[c] === 255 ? NaN : (b[c] / 10) ** 2;
        this.cache.set(k, a);
      }
      return this.cache.get(k);
    }
    // mm/h promedio del periodo de 3 h
    porHora(id, i) {
      const k = "h" + id + i;
      if (!this.cache.has(k)) {
        const a = this.lluvia3h(id, i), r = new Float32Array(this.n);
        for (let c = 0; c < this.n; c++) r[c] = a[c] / 3;
        this.cache.set(k, r);
      }
      return this.cache.get(k);
    }
    // mm en las 24 h que terminan en horas[i] (los 8 periodos de 3 h)
    acumulado24(id, i) {
      const k = "d" + id + i;
      if (!this.cache.has(k)) {
        const r = new Float32Array(this.n);
        for (let j = Math.max(0, i - 7); j <= i; j++) {
          const a = this.lluvia3h(id, j);
          for (let c = 0; c < this.n; c++) r[c] += a[c];
        }
        this.cache.set(k, r);
      }
      return this.cache.get(k);
    }
    viento(id, i) {
      const k = "v" + id + i;
      if (!this.cache.has(k)) {
        const m = this.modelo(id), bu = decodificar(m.u[i]), bv = decodificar(m.v[i]);
        const u = new Float32Array(this.n), v = new Float32Array(this.n);
        for (let c = 0; c < this.n; c++) {
          u[c] = bu[c] === 255 ? 0 : (bu[c] - 128) / 4;
          v[c] = bv[c] === 255 ? 0 : (bv[c] - 128) / 4;
        }
        this.cache.set(k, [u, v]);
      }
      return this.cache.get(k);
    }
  }

  // Interpolación lineal entre dos campos
  function mezclar(a, b, f, destino) {
    if (f <= 0 || a === b) { destino.set(a); return destino; }
    for (let c = 0; c < a.length; c++) destino[c] = a[c] + (b[c] - a[c]) * f;
    return destino;
  }

  // Valor bilineal en coordenadas de rejilla (x: columna, y: fila desde el norte)
  function muestrear(campo, nlon, nlat, x, y) {
    if (x < 0 || y < 0 || x > nlon - 1 || y > nlat - 1) return NaN;
    const x0 = Math.min(Math.floor(x), nlon - 2), y0 = Math.min(Math.floor(y), nlat - 2);
    const fx = x - x0, fy = y - y0, i = y0 * nlon + x0;
    return (campo[i] * (1 - fx) + campo[i + 1] * fx) * (1 - fy) + (campo[i + nlon] * (1 - fx) + campo[i + nlon + 1] * fx) * fy;
  }

  // ── Componente ───────────────────────────────────────────────────────────
  async function montar(raiz, op = {}) {
    raiz.classList.add("lm");
    raiz.innerHTML = `<div class="lm-mapa"></div>`;
    let L, j;
    try {
      [L, j] = await Promise.all([cargarLeaflet(), fetch(op.datos || "datos/lluvia-mapa.json", {cache: "no-cache"}).then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status); return r.json();
      })]);
    } catch (e) {
      raiz.insertAdjacentHTML("beforeend", `<div class="lm-error">No se pudo cargar el mapa de lluvia de los modelos (${esc(e.message)}).</div>`);
      return null;
    }
    if (!j.modelos || !j.modelos.length) {
      raiz.insertAdjacentHTML("beforeend", `<div class="lm-error">Todavía no hay datos de los modelos.</div>`);
      return null;
    }
    const D = new Datos(j), g = D.g;
    const sur = g.norte - (g.nlat - 1) * g.paso, este = g.oeste + (g.nlon - 1) * g.paso;
    const limites = [[sur, g.oeste], [g.norte, este]];
    const E = {
      modelo: op.modelo && j.modelos.some(m => m.id === op.modelo) ? op.modelo : j.modelos[0].id,
      modo: op.modo === "dia" ? "dia" : "hora",
      viento: op.viento !== false && !matchMedia("(prefers-reduced-motion: reduce)").matches,
      t: 0, jugando: false,
    };
    // Cuadro inicial: el periodo de 3 h que contiene «ahora» (o el primero que se muestra)
    const ahora = Date.now();
    const tMin = j.inicio || 0, tMax = D.horas.length - 1;
    let t0 = D.horas.findIndex(h => h > ahora);
    E.t = t0 < tMin || t0 < 0 ? tMin : t0;

    // Mapa
    const divMapa = raiz.querySelector(".lm-mapa");
    const mapa = L.map(divMapa, {zoomControl: false, attributionControl: true,
      minZoom: 6, maxZoom: 12, maxBounds: L.latLngBounds(limites).pad(0.6), zoomSnap: 0.25, worldCopyJump: false});
    mapa.attributionControl.setPrefix(false);
    if (!matchMedia("(pointer: coarse)").matches) L.control.zoom({position: "topright"}).addTo(mapa);
    mapa.fitBounds([[-1.45, -91.7], [0.75, -89.15]]);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      {maxNativeZoom: 16, attribution: "Mapa Esri"}).addTo(mapa);
    mapa.createPane("lmEtiquetas").style.zIndex = 460;
    mapa.getPane("lmEtiquetas").style.pointerEvents = "none";
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
      {maxNativeZoom: 16, pane: "lmEtiquetas", opacity: 0.85}).addTo(mapa);
    mapa.attributionControl.addAttribution("Lluvia y viento: Open-Meteo (CC BY 4.0) · ECMWF, NOAA, DWD");

    // Lluvia: un canvas pequeño estirado sobre la rejilla. El navegador lo suaviza al ampliarlo.
    const W = (g.nlon - 1) * SUBMUESTREO + 1, H = (g.nlat - 1) * SUBMUESTREO + 1;
    const lienzo = document.createElement("canvas");
    lienzo.width = W; lienzo.height = H;
    const ctx = lienzo.getContext("2d");
    const img = ctx.createImageData(W, H);
    const CapaLienzo = L.ImageOverlay.extend({
      _initImage() {
        this._image = this._url;
        L.DomUtil.addClass(this._image, "leaflet-image-layer");
        if (this._zoomAnimated) L.DomUtil.addClass(this._image, "leaflet-zoom-animated");
        L.DomUtil.addClass(this._image, "lm-lluvia");
        this._image.onselectstart = L.Util.falseFn;
        this._image.onmousemove = L.Util.falseFn;
      },
    });
    new CapaLienzo(lienzo, limites, {opacity: 0.88, interactive: false}).addTo(mapa);
    const campo = new Float32Array(D.n);
    // Desvanece el borde de la rejilla (una celda y media) para que no se vea un rectángulo
    const borde = new Float32Array(W * H), ANCHO = SUBMUESTREO * 1.5;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const d = Math.min(x, y, W - 1 - x, H - 1 - y) / ANCHO;
      borde[y * W + x] = d >= 1 ? 1 : d * d * (3 - 2 * d);
    }

    function campoActual() {
      const f0 = Math.floor(E.t), f1 = Math.min(f0 + 1, tMax), w = E.t - f0;
      const de = E.modo === "dia" ? D.acumulado24.bind(D) : D.porHora.bind(D);
      return mezclar(de(E.modelo, f0), de(E.modelo, f1), w, campo);
    }

    function pintar() {
      const c = campoActual(), p = PALETAS[E.modo], lut = p.lut, px = img.data;
      const nlon = g.nlon;
      for (let y = 0; y < H; y++) {
        const gy = y / SUBMUESTREO, y0 = Math.min(Math.floor(gy), g.nlat - 2), fy = gy - y0;
        for (let x = 0; x < W; x++) {
          const gx = x / SUBMUESTREO, x0 = Math.min(Math.floor(gx), nlon - 2), fx = gx - x0, i = y0 * nlon + x0;
          const v = (c[i] * (1 - fx) + c[i + 1] * fx) * (1 - fy) + (c[i + nlon] * (1 - fx) + c[i + nlon + 1] * fx) * fy;
          const o = (y * W + x) * 4;
          if (!(v > 0)) { px[o + 3] = 0; continue; }
          const k = Math.min(N_LUT - 1, Math.round(aEscala(v, p.max) * (N_LUT - 1))) * 4;
          px[o] = lut[k]; px[o + 1] = lut[k + 1]; px[o + 2] = lut[k + 2]; px[o + 3] = lut[k + 3] * borde[y * W + x];
        }
      }
      ctx.putImageData(img, 0, 0);
    }

    // ── Partículas de viento ──────────────────────────────────────────────
    const cv = document.createElement("canvas");
    cv.className = "lm-particulas";
    mapa.getContainer().appendChild(cv);
    const cx = cv.getContext("2d");
    const u = new Float32Array(D.n), v = new Float32Array(D.n);
    let parts = [], dpr = 1;

    function vientoActual() {
      const f0 = Math.floor(E.t), f1 = Math.min(f0 + 1, tMax), w = E.t - f0;
      const [u0, v0] = D.viento(E.modelo, f0), [u1, v1] = D.viento(E.modelo, f1);
      mezclar(u0, u1, w, u); mezclar(v0, v1, w, v);
    }
    function aRejilla(ll) { return [(ll.lng - g.oeste) / g.paso, (g.norte - ll.lat) / g.paso]; }
    function nueva() {
      const s = mapa.getSize();
      return {x: Math.random() * s.x, y: Math.random() * s.y, edad: Math.floor(Math.random() * 80)};
    }
    function reiniciarParticulas() {
      const s = mapa.getSize();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      cv.width = s.x * dpr; cv.height = s.y * dpr; cv.style.width = s.x + "px"; cv.style.height = s.y + "px";
      cx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.round(Math.min(2200, s.x * s.y / 220));
      parts = Array.from({length: n}, nueva);
    }
    function pasoParticulas() {
      const s = mapa.getSize();
      cx.globalCompositeOperation = "destination-in";
      cx.fillStyle = "rgba(0,0,0,0.90)";
      cx.fillRect(0, 0, s.x, s.y);
      cx.globalCompositeOperation = "source-over";
      if (!E.viento) return;
      cx.lineWidth = 1.1;
      cx.strokeStyle = "rgba(255,255,255,0.78)";
      cx.beginPath();
      const K = 0.22; // px por cuadro por cada m/s
      for (const p of parts) {
        const [gx, gy] = aRejilla(mapa.containerPointToLatLng([p.x, p.y]));
        const uu = muestrear(u, g.nlon, g.nlat, gx, gy), vv = muestrear(v, g.nlon, g.nlat, gx, gy);
        if (!(uu === uu) || p.edad++ > 90) { Object.assign(p, nueva(), {edad: 0}); continue; }
        const nx = p.x + uu * K, ny = p.y - vv * K;
        cx.moveTo(p.x, p.y); cx.lineTo(nx, ny);
        p.x = nx; p.y = ny;
        if (nx < 0 || ny < 0 || nx > s.x || ny > s.y) Object.assign(p, nueva(), {edad: 0});
      }
      cx.stroke();
    }

    // ── Controles ─────────────────────────────────────────────────────────
    const modelos = j.modelos.map(m => `<option value="${esc(m.id)}">${esc(m.nombre)}</option>`).join("");
    raiz.insertAdjacentHTML("beforeend", `
      <div class="lm-caja lm-arriba">
        <div class="lm-caja lm-titulo">Lluvia de modelos<small>estimación, no medida</small></div>
        <div class="lm-caja lm-grupo" role="group" aria-label="Qué lluvia mostrar">
          <button type="button" data-modo="hora">Por hora</button><button type="button" data-modo="dia"><span class="lm-largo">Acumulado </span>24 h</button>
        </div>
        <select class="lm-select" aria-label="Modelo">${modelos}</select>
        <span class="lm-espacio"></span>
        <div class="lm-caja lm-grupo"><button type="button" class="lm-viento" aria-pressed="true" title="Partículas de viento a 10 m">Viento</button></div>
      </div>
      <div class="lm-caja lm-leyenda" aria-hidden="true"><b></b><div class="lm-escala"><canvas width="1" height="150"></canvas><div class="lm-marcas"></div></div></div>
      <div class="lm-caja lm-lectura"></div>
      <div class="lm-caja lm-abajo">
        <div class="lm-tiempo">
          <button type="button" class="lm-play" aria-label="Reproducir"></button>
          <div class="lm-pista">
            <div class="lm-hora"><b></b><span></span></div>
            <input class="lm-rango" type="range" aria-label="Hora del pronóstico">
            <div class="lm-dias"></div>
          </div>
        </div>
        <div class="lm-aviso"></div>
      </div>`);
    const $ = s => raiz.querySelector(s);
    const rango = $(".lm-rango"), play = $(".lm-play"), sel = $(".lm-select"), lectura = $(".lm-lectura");
    sel.value = E.modelo;
    rango.min = tMin; rango.max = tMax; rango.step = 1 / 3; // un paso = una hora
    rango.value = E.t;

    // Marcas de día en la pista
    (function () {
      const dias = $(".lm-dias"), span = D.horas[tMax] - D.horas[tMin];
      let html = "", previo = null;
      for (let h = D.horas[tMin] - 3 * 3600e3; h <= D.horas[tMax]; h += 3600e3) {
        const d = diaLocal(h);
        if (previo && d !== previo) {
          const pct = (h - D.horas[tMin]) / span * 100;
          if (pct >= 0 && pct < 92) html += `<span style="left:${pct}%">${esc(fDiaCorto.format(h))}</span>`;
        }
        previo = d;
      }
      dias.innerHTML = html;
    })();

    function leyenda() {
      const p = PALETAS[E.modo], c = $(".lm-leyenda canvas"), movil = matchMedia("(max-width:640px)").matches;
      const N = 150;
      c.width = movil ? N : 1; c.height = movil ? 1 : N;
      const x = c.getContext("2d"), im = x.createImageData(c.width, c.height);
      for (let k = 0; k < N; k++) {
        const fr = movil ? k / (N - 1) : 1 - k / (N - 1);
        const li = Math.round(fr * (N_LUT - 1)) * 4;
        const a = Math.max(p.lut[li + 3], 60);
        im.data.set([p.lut[li], p.lut[li + 1], p.lut[li + 2], a], k * 4);
      }
      x.putImageData(im, 0, 0);
      $(".lm-leyenda b").textContent = p.unidad;
      $(".lm-leyenda .lm-marcas").innerHTML = p.marcas.map(m => {
        const f = aEscala(m, p.max) * 100;
        return movil ? `<span style="left:${f}%">${num(m)}</span>` : `<span style="bottom:${f}%">${num(m)}</span>`;
      }).join("");
    }

    function rotulos() {
      const f0 = Math.floor(E.t), w = E.t - f0;
      const fin = D.horas[f0] + Math.round(w * 3) * 3600e3; // fin de la hora mostrada
      const m = D.modelo(E.modelo);
      if (E.modo === "dia") {
        $(".lm-hora b").textContent = `${fDia.format(fin)} · ${fHora.format(fin)}`;
        $(".lm-hora span").textContent = "lluvia de las 24 h anteriores";
      } else {
        $(".lm-hora b").textContent = `${fDia.format(fin)} · ${fHora.format(fin - 3600e3)}–${fHora.format(fin)}`;
        $(".lm-hora span").textContent = "mm/h, promedio de cada bloque de 3 h";
      }
      const corrida = m.corrida ? `corrida del ${fCorrida.format(Date.parse(m.corrida))}` : "corrida sin fecha conocida";
      $(".lm-aviso").innerHTML = `<b>Modelo ${esc(m.nombre)}</b>, ${corrida} (hora de Galápagos). ` +
        `<b>Subestima mucho la lluvia en las islas</b> (35–45 mm menos al día): no ve su relieve. ` +
        `No es un pronóstico oficial; el oficial es del INAMHI.`;
      rango.style.setProperty("--p", ((E.t - tMin) / (tMax - tMin || 1) * 100) + "%");
      raiz.querySelectorAll("[data-modo]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.modo === E.modo)));
      $(".lm-viento").setAttribute("aria-pressed", String(E.viento));
      play.innerHTML = E.jugando
        ? `<svg viewBox="0 0 14 14"><rect x="2" y="1" width="3.5" height="12" rx="1" fill="currentColor"/><rect x="8.5" y="1" width="3.5" height="12" rx="1" fill="currentColor"/></svg>`
        : `<svg viewBox="0 0 14 14"><path d="M3 1.5v11l9.5-5.5z" fill="currentColor"/></svg>`;
      play.setAttribute("aria-label", E.jugando ? "Pausar" : "Reproducir");
    }

    let ultimaLectura = null;
    function leer(ll, punto) {
      ultimaLectura = [ll, punto];
      const [gx, gy] = aRejilla(ll);
      const val = muestrear(campoActual(), g.nlon, g.nlat, gx, gy);
      if (!(val === val)) { lectura.style.display = "none"; return; }
      vientoActual();
      const uu = muestrear(u, g.nlon, g.nlat, gx, gy), vv = muestrear(v, g.nlon, g.nlat, gx, gy);
      const rap = Math.hypot(uu, vv), desde = (Math.atan2(-uu, -vv) * 180 / Math.PI + 360) % 360;
      const txtLluvia = E.modo === "dia" ? `${num(val, val < 10 ? 1 : 0)} mm en 24 h` : `${num(val, val < 1 ? 2 : 1)} mm/h`;
      lectura.innerHTML = `<b>${val < 0.05 && E.modo === "hora" ? "sin lluvia" : txtLluvia}</b> · viento ${num(rap * 3.6, 0)} km/h del ${PUNTOS_CARDINALES[Math.round(desde / 22.5) % 16]}`;
      lectura.style.left = punto.x + "px"; lectura.style.top = punto.y + "px"; lectura.style.display = "block";
    }

    function actualizar(rehacerLectura = true) {
      pintar(); vientoActual(); rotulos();
      if (rehacerLectura && ultimaLectura && lectura.style.display === "block") leer(...ultimaLectura);
    }

    // Eventos
    rango.addEventListener("input", () => { E.t = +rango.value; parar(); actualizar(); });
    sel.addEventListener("change", () => { E.modelo = sel.value; actualizar(); });
    raiz.querySelectorAll("[data-modo]").forEach(b => b.addEventListener("click", () => { E.modo = b.dataset.modo; leyenda(); actualizar(); }));
    $(".lm-viento").addEventListener("click", () => { E.viento = !E.viento; rotulos(); });
    mapa.on("mousemove", e => leer(e.latlng, e.containerPoint));
    mapa.on("click", e => leer(e.latlng, e.containerPoint));
    mapa.getContainer().addEventListener("mouseleave", () => { lectura.style.display = "none"; });
    mapa.on("movestart zoomstart", () => { cx.clearRect(0, 0, cv.width, cv.height); lectura.style.display = "none"; });
    mapa.on("moveend zoomend resize", reiniciarParticulas);
    window.addEventListener("resize", leyenda);

    // Reproducción: avanza el tiempo de forma continua (el campo se interpola entre cuadros)
    let previo = 0, rafId = 0, visible = true;
    function parar() { E.jugando = false; }
    play.addEventListener("click", () => {
      E.jugando = !E.jugando;
      if (E.jugando && E.t >= tMax) E.t = tMin;
      rotulos();
    });
    function bucle(ts) {
      rafId = requestAnimationFrame(bucle);
      if (!visible) return;
      const dt = previo ? Math.min(0.1, (ts - previo) / 1000) : 0;
      previo = ts;
      if (E.jugando) {
        E.t += dt / SEG_POR_CUADRO;
        if (E.t >= tMax) { E.t = tMax; E.jugando = false; }
        rango.value = E.t;
        actualizar(false);
      }
      pasoParticulas();
    }
    // No gastar batería si el mapa no se ve
    if ("IntersectionObserver" in window) new IntersectionObserver(es => { visible = es[0].isIntersecting; previo = 0; }).observe(raiz);

    leyenda(); reiniciarParticulas(); actualizar();
    rafId = requestAnimationFrame(bucle);

    return {
      mapa,
      ir(t) { E.t = Math.max(tMin, Math.min(tMax, t)); rango.value = E.t; actualizar(); },
      estado: () => ({...E, hora: new Date(D.horas[Math.floor(E.t)]).toISOString()}),
      destruir() { cancelAnimationFrame(rafId); mapa.remove(); raiz.innerHTML = ""; },
    };
  }

  window.LluviaMapa = {montar};
})();
