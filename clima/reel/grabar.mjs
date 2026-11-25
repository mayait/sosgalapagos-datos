// SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
// Licencia Apache 2.0 (ver LICENSE y NOTICE): puede reutilizarse dando crédito.
// Graba una página del reel cuadro a cuadro con Chrome sin ventana (protocolo DevTools). Sin dependencias:
// usa el WebSocket que trae Node 22 o posterior. Lo llama reel.py; a mano:
//   node grabar.mjs <url de la página> <carpeta de salida> <puerto libre> <prueba|todo>
// «prueba» deja una sola imagen (prueba.jpg, a la hora de más lluvia); «todo» deja los cuadros y poster.jpg.
// Variables de entorno: CHROME (ruta del navegador) y LIMITE (segundos antes de rendirse; 100 por defecto).
import { spawn } from "node:child_process"; import fs from "node:fs"; import os from "node:os"; import path from "node:path";
const [url, salida, puerto, modo] = process.argv.slice(2);
if (!url || !salida || !puerto || !["prueba", "todo"].includes(modo)) { console.log("uso: node grabar.mjs <url> <salida> <puerto> <prueba|todo>"); process.exit(64); }
if (typeof WebSocket === "undefined") { console.log("hace falta Node 22 o posterior (WebSocket incorporado)"); process.exit(1); }
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const perfil = fs.mkdtempSync(path.join(os.tmpdir(), "reel-clima-chrome-"));
const gpu = process.platform === "darwin" ? ["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"] : [];
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${puerto}`, `--user-data-dir=${perfil}`,
  "--allow-file-access-from-files", "--remote-allow-origins=*", ...gpu, "--hide-scrollbars", "--window-size=1080,1920", "about:blank"], {stdio: "ignore"});
const salir = codigo => { try { chrome.kill(); } catch {} try { fs.rmSync(perfil, {recursive: true, force: true}); } catch {} process.exit(codigo); };
chrome.on("error", e => { console.log("no se pudo abrir Chrome:", e.message); salir(1); });
const dormir = ms => new Promise(r => setTimeout(r, ms));
let ws;
for (let i = 0; i < 50 && !ws; i++) { await dormir(300); try { const l = await (await fetch(`http://127.0.0.1:${puerto}/json`)).json(); const p = l.find(x => x.type === "page"); if (p) ws = new WebSocket(p.webSocketDebuggerUrl); } catch {} }
if (!ws) { console.log("sin Chrome"); salir(1); }
await new Promise(r => { ws.addEventListener("open", r); ws.addEventListener("error", e => { console.log("error ws", e.message || e.type); salir(1); }); });
setTimeout(() => { console.log("tiempo agotado"); salir(2); }, +(process.env.LIMITE || 100) * 1000);
console.log("conectado");
let id = 0; const pend = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const cdp = (method, params = {}) => new Promise(r => { const n = ++id; pend.set(n, r); ws.send(JSON.stringify({id: n, method, params})); });
const ev = async expr => { const r = await cdp("Runtime.evaluate", {expression: expr, awaitPromise: true, returnByValue: true}); if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 600)); return r.result?.result?.value; };
// Se graba al doble (2160 × 3840) y ffmpeg lo reduce a 1080 × 1920: así los textos y las líneas salen nítidos.
await cdp("Emulation.setDeviceMetricsOverride", {width: 1080, height: 1920, deviceScaleFactor: 2, mobile: false});
await cdp("Page.navigate", {url});
let listo = false;
for (let i = 0; i < 120 && !listo; i++) { await dormir(300); listo = await ev("window.LISTO === true").catch(() => false); }
const errores = await ev("JSON.stringify(window.ERRORES || [])").catch(() => "[]");
console.log("info", JSON.stringify(await ev("window.INFO").catch(() => null)));
console.log("listo", listo, "errores", errores.slice(0, 800));
if (!listo || errores !== "[]") { console.log("la página no cargó bien"); salir(3); }
const foto = async f => { const r = await cdp("Page.captureScreenshot", {format: "jpeg", quality: 94}); fs.writeFileSync(f, Buffer.from(r.result.data, "base64")); };
fs.mkdirSync(salida, {recursive: true});
if (modo === "prueba") { await ev("fijo(window.PICO)"); await foto(`${salida}/prueba.jpg`); console.log("prueba", `${salida}/prueba.jpg`); }
else {
  const total = await ev("window.TOTAL"); const t0 = Date.now();
  for (let i = 0; i < total; i++) { await ev(`cuadro(${i})`); await foto(`${salida}/${String(i).padStart(4, "0")}.jpg`); }
  await ev("fijo(window.PICO)"); await foto(`${salida}/poster.jpg`);
  console.log("cuadros", total, "seg", ((Date.now() - t0) / 1000).toFixed(0));
}
ws.close(); salir(0);
