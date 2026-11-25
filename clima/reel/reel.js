// SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
// Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
// Mapa del reel del clima con el mismo motor visual del panel de /clima/ (paleta, lluvia interpolada y partículas
// de viento), pero avanzando cuadro a cuadro para poder grabarlo (grabar.mjs). Lo arma reel.py, que deja en la página:
//   window.LM    el mapa de lluvia y viento del sitio (lluvia-mapa.json)
//   window.ISLAS el contorno de las islas (islas.js)
//   window.REEL  {dia: "AAAA-MM-DD", dias: [todos los días del reel], modelo, altas: [{nombre, lat, lon}], marea: {…}}
(function () {
  "use strict";
  const J = window.LM, R = window.REEL, g = J.rejilla, N = g.nlat * g.nlon, M = J.modelos.find(m => m.id === R.modelo) || J.modelos[0];
  const dec = b64 => { const s = atob(b64), a = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return a; };
  const cache = new Map();
  const lluvia = i => { if (!cache.has("l" + i)) { const b = dec(M.lluvia[i]), a = new Float32Array(N); for (let c = 0; c < N; c++) a[c] = b[c] === 255 ? 0 : (b[c] / 10) ** 2 / 3; cache.set("l" + i, a); } return cache.get("l" + i); };
  const viento = i => { if (!cache.has("v" + i)) { const bu = dec(M.u[i]), bv = dec(M.v[i]), u = new Float32Array(N), v = new Float32Array(N);
    for (let c = 0; c < N; c++) { u[c] = bu[c] === 255 ? 0 : (bu[c] - 128) / 4; v[c] = bv[c] === 255 ? 0 : (bv[c] - 128) / 4; } cache.set("v" + i, [u, v]); } return cache.get("v" + i); };
  const mezclar = (a, b, f, d) => { for (let c = 0; c < a.length; c++) d[c] = a[c] + (b[c] - a[c]) * f; return d; };
  function muestrear(campo, x, y) {
    if (x < 0 || y < 0 || x > g.nlon - 1 || y > g.nlat - 1) return NaN;
    const x0 = Math.min(Math.floor(x), g.nlon - 2), y0 = Math.min(Math.floor(y), g.nlat - 2), fx = x - x0, fy = y - y0, i = y0 * g.nlon + x0;
    return (campo[i] * (1 - fx) + campo[i + 1] * fx) * (1 - fy) + (campo[i + g.nlon] * (1 - fx) + campo[i + g.nlon + 1] * fx) * fy;
  }
  // Paleta «por hora» del panel
  const P = {max: 60, paradas: [[0.1, [95, 155, 230, 0]], [0.3, [95, 155, 230, 140]], [0.7, [60, 120, 220, 185]], [1.5, [40, 90, 205, 210]],
    [3, [40, 175, 205, 210]], [5, [55, 190, 95, 220]], [8, [235, 220, 55, 230]], [13, [245, 150, 40, 235]],
    [20, [230, 55, 45, 240]], [32, [205, 40, 150, 245]], [50, [130, 50, 200, 250]], [60, [70, 20, 110, 250]]]};
  const NL = 512, lut = new Uint8ClampedArray(NL * 4);
  for (let i = 0; i < NL; i++) { const v = Math.pow(i / (NL - 1), 2) * P.max; let k = 0;
    while (k < P.paradas.length - 1 && P.paradas[k + 1][0] < v) k++;
    const [v0, c0] = P.paradas[k], [v1, c1] = P.paradas[Math.min(k + 1, P.paradas.length - 1)];
    const f = v <= v0 ? 0 : v1 === v0 ? 1 : Math.min(1, (v - v0) / (v1 - v0));
    for (let c = 0; c < 4; c++) lut[i * 4 + c] = v < P.paradas[0][0] ? 0 : c0[c] + (c1[c] - c0[c]) * f; }
  const aEsc = v => Math.sqrt(Math.max(0, v) / P.max);
  let sem = 12345 + R.dias.indexOf(R.dia); const rnd = () => { sem = (sem * 1664525 + 1013904223) >>> 0; return sem / 4294967296; };

  // Galápagos es UTC−6: el día empieza a las 06:00Z. horas[i] es el final de cada periodo de 3 h.
  const inicio = fecha => { const i = J.horas.indexOf(fecha + "T06:00Z"); if (i < 0 || i + 8 > J.horas.length - 1) throw new Error("el mapa de lluvia no cubre el " + fecha); return i; };
  const IDX = inicio(R.dia), INICIOS = R.dias.map(inicio);
  const tLluvia = tau => IDX + (tau + 1.5) / 3, tViento = tau => IDX + tau / 3;
  const sur = g.norte - (g.nlat - 1) * g.paso, este = g.oeste + (g.nlon - 1) * g.paso;
  const div = document.getElementById("mapa");
  const mapa = L.map(div, {zoomControl: false, attributionControl: false, zoomSnap: 0, fadeAnimation: false, zoomAnimation: false, dragging: false});
  mapa.fitBounds([[-1.506, -92.1], [0.746, -88.9]], {animate: false});
  mapa.createPane("tierra").style.zIndex = 300; mapa.createPane("costa").style.zIndex = 420;
  L.geoJSON(window.ISLAS, {interactive: false, pane: "tierra", style: {fillColor: "#f3efe4", fillOpacity: 1, stroke: false}}).addTo(mapa);
  L.geoJSON(window.ISLAS, {interactive: false, pane: "costa", style: {fill: false, color: "#1b2a33", weight: 1.6}}).addTo(mapa);
  const SUB = 8, W = (g.nlon - 1) * SUB + 1, H = (g.nlat - 1) * SUB + 1;
  const lienzo = document.createElement("canvas"); lienzo.width = W; lienzo.height = H;
  const ctx = lienzo.getContext("2d"), img = ctx.createImageData(W, H);
  const Capa = L.ImageOverlay.extend({_initImage() { this._image = this._url; L.DomUtil.addClass(this._image, "leaflet-image-layer"); }});
  new Capa(lienzo, [[sur, g.oeste], [g.norte, este]], {opacity: 0.88, interactive: false}).addTo(mapa);
  const campo = new Float32Array(N), u = new Float32Array(N), v = new Float32Array(N);
  function campos(tau) {
    let t = Math.min(tLluvia(tau), J.horas.length - 1), f0 = Math.floor(t); mezclar(lluvia(f0), lluvia(Math.min(f0 + 1, J.horas.length - 1)), t - f0, campo);
    t = tViento(tau); f0 = Math.floor(t); const [u0, v0] = viento(f0), [u1, v1] = viento(f0 + 1); mezclar(u0, u1, t - f0, u); mezclar(v0, v1, t - f0, v);
  }
  function pintar() {
    const px = img.data;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const val = muestrear(campo, x / SUB, y / SUB), o = (y * W + x) * 4;
      if (!(val > 0)) { px[o + 3] = 0; continue; }
      const k = Math.min(NL - 1, Math.round(aEsc(val) * (NL - 1))) * 4;
      px[o] = lut[k]; px[o + 1] = lut[k + 1]; px[o + 2] = lut[k + 2]; px[o + 3] = lut[k + 3];
    }
    ctx.putImageData(img, 0, 0);
  }
  // Partículas de viento (mismo método del panel: estela que se desvanece)
  const s = mapa.getSize(), cv = document.createElement("canvas"); cv.className = "pt"; const DPR = 2;
  cv.width = s.x * DPR; cv.height = s.y * DPR; cv.style.width = s.x + "px"; cv.style.height = s.y + "px"; div.appendChild(cv);
  const cx = cv.getContext("2d"); cx.setTransform(DPR, 0, 0, DPR, 0, 0);
  const nueva = () => ({x: rnd() * s.x, y: rnd() * s.y, edad: Math.floor(rnd() * 90)});
  const parts = Array.from({length: 3400}, nueva);
  const aRej = (x, y) => { const ll = mapa.containerPointToLatLng([x, y]); return [(ll.lng - g.oeste) / g.paso, (g.norte - ll.lat) / g.paso]; };
  function pasoPart() {
    cx.globalCompositeOperation = "destination-in"; cx.fillStyle = "rgba(0,0,0,0.93)"; cx.fillRect(0, 0, s.x, s.y);
    cx.globalCompositeOperation = "source-over"; cx.lineWidth = 1.7; cx.lineCap = "round"; cx.strokeStyle = "rgba(20,30,50,0.62)"; cx.beginPath();
    const K = 0.42;
    for (const p of parts) {
      const [gx, gy] = aRej(p.x, p.y), uu = muestrear(u, gx, gy), vv = muestrear(v, gx, gy);
      if (!(uu === uu) || p.edad++ > 110) { Object.assign(p, nueva(), {edad: 0}); continue; }
      const nx = p.x + uu * K, ny = p.y - vv * K; cx.moveTo(p.x, p.y); cx.lineTo(nx, ny); p.x = nx; p.y = ny;
      if (nx < 0 || ny < 0 || nx > s.x || ny > s.y) Object.assign(p, nueva(), {edad: 0});
    }
    cx.stroke();
  }
  // Rótulos y puertos
  const pos = (lat, lon) => mapa.latLngToContainerPoint([lat, lon]);
  const el = (cls, html, x, y) => { const e = document.createElement("div"); e.className = cls; e.innerHTML = html || ""; e.style.left = x + "px"; e.style.top = y + "px"; div.appendChild(e); return e; };
  [["ISABELA", -0.30, -91.33], ["SANTA CRUZ", -0.40, -90.33], ["SAN CRISTÓBAL", -0.62, -89.42]].forEach(([n, la, lo]) => { const p = pos(la, lo); el("et", n, p.x, p.y); });
  const PUERTOS = [["Puerto Ayora", -0.743, -90.31, 22], ["Pto. Baquerizo", -0.901, -89.61, -150], ["Pto. Villamil", -0.958, -90.965, 22]].map(([n, la, lo, dx]) => {
    const p = pos(la, lo), [gx, gy] = [(lo - g.oeste) / g.paso, (g.norte - la) / g.paso];
    el("pu", n, p.x + dx, p.y + 34);
    return {gx, gy, anillos: [el("ring", "", p.x, p.y), el("ring", "", p.x, p.y)], punto: el("dot", "", p.x, p.y)};
  });
  // Referencia de tamaño: la lluvia más fuerte del modelo en los puertos en todos los días del reel
  // (así el punto rojo y las barras se pueden comparar de un día a otro)
  let ref = 0.5;
  for (const b of INICIOS) for (let i = b + 1; i <= b + 8; i++) for (const p of PUERTOS) ref = Math.max(ref, muestrear(lluvia(i), p.gx, p.gy));
  // Tira por isla: lluvia del modelo en la parte alta de cada una, en bloques de 3 h
  const ALTA = R.altas.map(a => ({n: a.nombre.toUpperCase(), x: (a.lon - g.oeste) / g.paso, y: (g.norte - a.lat) / g.paso}));
  const enIsla = (a, i) => muestrear(lluvia(i), a.x, a.y);
  let tope = 0.8; for (const b of INICIOS) for (let i = b + 1; i <= b + 8; i++) for (const a of ALTA) tope = Math.max(tope, enIsla(a, i));
  const porIsla = ALTA.map(a => Array.from({length: 8}, (_, p) => enIsla(a, IDX + p + 1)));
  const bloques = Array.from({length: 8}, (_, p) => porIsla.reduce((s, b) => s + b[p], 0) / porIsla.length);
  const barras = document.getElementById("barras"), h2 = n => String(n).padStart(2, "0");
  barras.innerHTML = porIsla.map((b, k) => { const pk = b.indexOf(Math.max(...b)), hay = b[pk] >= 0.1;
    return `<div class="fila"><b>${ALTA[k].n}<span>${hay ? "más: " + h2(pk * 3) + "–" + h2(pk * 3 + 3) + " h" : "casi sin lluvia"}</span></b>` +
      b.map((v, p) => `<i class="${hay && p === pk ? "pico" : ""}" style="height:${Math.max(6, Math.sqrt(v / tope) * 82)}%"></i>`).join("") + "</div>"; }).join("");
  const lc = document.querySelector("#ley canvas").getContext("2d");
  for (let x = 0; x < 230; x++) { const k = Math.round((0.07 + 0.55 * x / 229) * (NL - 1)) * 4; lc.fillStyle = `rgba(${lut[k]},${lut[k + 1]},${lut[k + 2]},${Math.max(lut[k + 3], 90) / 255})`; lc.fillRect(x, 0, 1, 1); }
  // Marea: curva de la predicción (referida a la tabla del INOCAR) con las pleamares y bajamares oficiales del día
  const MA = R.marea, svg = document.querySelector("#marea svg"), MW_ = 798, MH_ = 100, Y0 = 26, YH = 66;
  const dia0 = Date.parse(R.dia + "T06:00:00Z"), mt0 = Date.parse(MA.t0);
  const nivel = tau => { const i = (dia0 + tau * 36e5 - mt0) / (MA.paso_min * 6e4), a = Math.floor(i), f = i - a;
    return ((MA.pred_cm[a] ?? 0) * (1 - f) + (MA.pred_cm[Math.min(a + 1, MA.pred_cm.length - 1)] ?? 0) * f) / 100 + MA.desfase_m; };
  const yy = m => Y0 + YH - (m + 0.15) / 2.35 * YH, xx = tau => tau / 24 * MW_;
  let dpath = ""; for (let i = 0; i <= 144; i++) { const t = i / 6; dpath += (i ? "L" : "M") + xx(t).toFixed(1) + " " + yy(nivel(t)).toFixed(1); }
  const area = dpath + `L${MW_} ${Y0 + YH}L0 ${Y0 + YH}Z`;
  let rot = "";
  for (const e of MA.extremos) { const tau = (Date.parse(e.ts) - dia0) / 36e5; if (tau < 0 || tau > 24) continue;
    const x = xx(tau), ple = e.tipo === "pleamar", anc = x < 70 ? "start" : x > MW_ - 70 ? "end" : "middle";
    const hora = e.local.split(" ").pop(), alt = e.altura_m.toFixed(2).replace(".", ",");
    rot += ple ? `<circle cx="${x}" cy="${yy(e.altura_m)}" r="5" fill="#0d2f6b"/><text x="${x}" y="${yy(e.altura_m) - 11}" text-anchor="${anc}" fill="#000">${hora} · ${alt} m</text>`
               : `<text x="${x}" y="${Y0 + YH + 21}" text-anchor="${anc}" fill="#777" style="font-weight:500">${hora} · ${alt} m</text>`; }
  svg.setAttribute("width", MW_); svg.style.left = "170px";
  svg.innerHTML = `<defs><clipPath id="ya"><rect id="yar" x="0" y="0" width="0" height="${MH_}"/></clipPath></defs>
    <path d="${area}" fill="#DDE6EE"/><path d="${area}" fill="#9db9dd" clip-path="url(#ya)"/>
    <path d="${dpath}" fill="none" stroke="#0d2f6b" stroke-width="3"/><line x1="0" x2="${MW_}" y1="${Y0 + YH}" y2="${Y0 + YH}" stroke="#000" stroke-width="2"/>${rot}
    <circle id="mpt" r="8" fill="#B5161C" stroke="#fff" stroke-width="3"/>`;
  const FR = h => h < 6 ? "MADRUGADA" : h < 12 ? "MAÑANA" : h < 18 ? "TARDE" : "NOCHE";
  let nf = 0;
  function dibujar(tau) {
    campos(Math.min(tau, 23.99)); pintar(); pasoPart(); nf++;
    for (const p of PUERTOS) {
      const val = Math.max(0, muestrear(campo, p.gx, p.gy)), f = Math.min(1, Math.pow(val / ref, 0.7)), r = 8 + 28 * f;
      p.punto.style.width = p.punto.style.height = 2 * r + "px";
      p.anillos.forEach((a, n) => { const ph = (nf / 26 + n / 2) % 1, rr = r * (1 + (0.5 + 1.1 * f) * ph);
        a.style.width = a.style.height = 2 * rr + "px"; a.style.borderWidth = 3 + 5 * f + "px"; a.style.opacity = (0.3 + 0.45 * f) * (1 - ph); });
    }
    const hh = tau >= 24 ? 24 : Math.floor(tau), mm = tau >= 24 ? 0 : Math.floor((tau - hh) * 6) * 10;
    document.querySelector("#reloj b").textContent = String(hh).padStart(2, "0") + ":" + String(mm).padStart(2, "0");
    document.querySelector("#reloj span").textContent = FR(Math.min(tau, 23.9));
    barras.querySelectorAll(".fila").forEach(fl => fl.querySelectorAll("i").forEach((b, p) => b.classList.toggle("ya", p * 3 < tau)));
    document.getElementById("cab").style.left = `calc(170px + (100% - 170px) * ${Math.min(tau, 24) / 24})`;
    const tm = Math.min(tau, 24); document.getElementById("yar").setAttribute("width", xx(tm));
    const mp = document.getElementById("mpt"); mp.setAttribute("cx", xx(tm)); mp.setAttribute("cy", yy(nivel(tm)));
  }
  const NA = 270, H0 = 15;
  window.TOTAL = H0 + NA + 36;
  window.PICO = bloques.indexOf(Math.max(...bloques)) * 3 + 1.5;
  window.cuadro = i => { dibujar(i < H0 ? 0 : Math.min(24, (i - H0) / NA * 24)); return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); };
  window.fijo = tau => { for (let n = 0; n < 40; n++) dibujar(tau); return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); };
  window.INFO = {ref, tope, bloques, modelo: M.nombre, corrida: M.corrida};
  campos(0); for (let n = 0; n < 70; n++) pasoPart();
  let ok = false; const listo = () => { if (!ok) { ok = true; document.fonts.ready.then(() => { window.LISTO = true; }); } };
  setTimeout(listo, 600);
})();
