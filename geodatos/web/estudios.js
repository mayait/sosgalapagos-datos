(function () {
  "use strict";
  var E = window.ESTUDIO || {}, API = "/estudios/api/comentarios";

  /* Índice: resaltar sección visible y desplegable en móvil */
  var ind = document.querySelector(".indice");
  if (ind) {
    var b = ind.querySelector(".indice-boton");
    b && b.addEventListener("click", function () { ind.classList.toggle("abierto"); b.setAttribute("aria-expanded", ind.classList.contains("abierto")); });
    ind.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", function () { ind.classList.remove("abierto"); }); });
    var enlaces = {}; ind.querySelectorAll("a").forEach(function (a) { enlaces[a.getAttribute("href").slice(1)] = a; });
    if ("IntersectionObserver" in window) {
      var obs = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting && enlaces[e.target.id]) {
          ind.querySelectorAll("a.activo").forEach(function (x) { x.classList.remove("activo"); });
          enlaces[e.target.id].classList.add("activo"); } });
      }, { rootMargin: "-20% 0px -70% 0px" });
      document.querySelectorAll("main section[id], main h2[id]").forEach(function (s) { obs.observe(s); });
    }
  }

  /* Visor de figuras */
  var visor = document.getElementById("visor");
  if (visor) {
    document.querySelectorAll("a.ampliar").forEach(function (a) {
      a.addEventListener("click", function (ev) { ev.preventDefault(); visor.querySelector("img").src = a.href; visor.hidden = false; });
    });
    visor.addEventListener("click", function () { visor.hidden = true; });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") visor.hidden = true; });
  }

  /* Línea del tiempo: filtros */
  document.querySelectorAll(".lt").forEach(function (lt) {
    lt.querySelectorAll(".filtro").forEach(function (f) {
      f.addEventListener("click", function () {
        f.classList.toggle("activo");
        var act = {}; lt.querySelectorAll(".filtro.activo").forEach(function (x) { act[x.dataset.tipo] = 1; });
        lt.querySelectorAll(".ev").forEach(function (ev) { ev.hidden = !act[ev.dataset.tipo]; });
      });
    });
  });

  /* Mapa interactivo */
  var div = document.getElementById("mapa");
  if (div && window.L) {
    var m = L.map(div, { scrollWheelZoom: false });
    var base = {
      "Gris (Esri)": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", { maxZoom: 16, attribution: "Esri" }),
      "Satélite (Esri)": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Esri, Maxar" }),
      "OpenStreetMap": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" })
    };
    base["OpenStreetMap"].addTo(m);
    var v = E.mapa || {}; m.setView(v.centro || [-0.74, -90.31], v.zoom || 13);
    var ctl = L.control.layers(base, {}, { collapsed: window.innerWidth < 700 }).addTo(m);
    var ley = L.control({ position: "bottomleft" }), filas = [];
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
    function popup(p) {
      var r = ""; for (var k in p) { if (p[k] === null || p[k] === "" || typeof p[k] === "object") continue; r += "<tr><td><b>" + esc(k) + "</b></td><td>" + esc(p[k]) + "</td></tr>"; }
      return "<table>" + r + "</table>";
    }
    (E.capas || []).forEach(function (c) {
      fetch(c.url).then(function (r) { return r.json(); }).then(function (gj) {
        var col = c.color || "#333";
        var capa = L.geoJSON(gj, {
          style: function (f) {
            var cc = c.colores && f.properties[c.colores.campo] != null ? (c.colores.valores[f.properties[c.colores.campo]] || col) : col;
            return { color: cc, weight: c.grosor || 2, fillColor: cc, fillOpacity: c.relleno == null ? 0.15 : c.relleno, dashArray: c.discontinua ? "6 4" : null };
          },
          pointToLayer: function (f, ll) {
            var cc = c.colores && f.properties[c.colores.campo] != null ? (c.colores.valores[f.properties[c.colores.campo]] || col) : col;
            return L.circleMarker(ll, { radius: c.radio || 6, color: "#222", weight: 1, fillColor: cc, fillOpacity: 0.9 });
          },
          onEachFeature: function (f, l) { l.bindPopup("<b>" + esc(c.nombre) + "</b>" + popup(f.properties)); }
        });
        if (c.visible !== false) capa.addTo(m);
        ctl.addOverlay(capa, '<span style="color:' + col + '">■</span> ' + esc(c.nombre));
      });
      if (c.leyenda !== false) filas.push('<i style="background:' + (c.color || "#333") + '"></i>' + esc(c.nombre));
    });
    ley.onAdd = function () { var d = L.DomUtil.create("div", "leyenda-mapa"); d.innerHTML = filas.join("<br>"); return d; };
    if (window.innerWidth > 700) ley.addTo(m);
    div.addEventListener("click", function () { m.scrollWheelZoom.enable(); });
  }

  /* Vista 3D interactiva (Plotly, bajo demanda) */
  var btn = document.getElementById("cargar3d");
  if (btn) btn.addEventListener("click", function () {
    btn.textContent = "Cargando…"; btn.disabled = true;
    var s = document.createElement("script"); s.src = E.plotly;
    s.onerror = function () { btn.textContent = "No se pudo cargar la vista 3D"; };
    s.onload = function () {
      fetch("vista3d.json").then(function (r) { return r.json(); }).then(function (d) {
        var xs = [], ys = [], z = d.z.map(function (f) { return f.map(function (q) { return q / 10; }); });
        for (var i = 0; i < d.nx; i++) xs.push(d.x0 + i * d.dx);
        for (var j = 0; j < d.ny; j++) ys.push(d.y0 - j * d.dx);
        var tr = [{ type: "surface", x: xs, y: ys, z: z, colorscale: [[0, "#cfe0ee"], [0.004, "#e8e2c8"], [0.15, "#c9c08f"], [0.35, "#9bb06f"], [0.55, "#5f8f4e"], [0.75, "#6b5a45"], [1, "#9c8f80"]],
          showscale: false, hovertemplate: "cota %{z:.0f} m<extra></extra>", lighting: { ambient: 0.55, diffuse: 0.8, roughness: 0.9 }, contours: { z: { show: false } } }];
        var vistos = {};
        d.capas.forEach(function (c) {
          tr.push({ type: "scatter3d", mode: c.t === "p" ? "markers" : "lines", x: c.x, y: c.y, z: c.z, name: c.n, legendgroup: c.n, line: { color: c.c, width: 5 },
            marker: { color: c.c, size: 4, line: { color: "#222", width: 1 } }, hovertemplate: c.n + "<extra></extra>", showlegend: !vistos[c.n] });
          vistos[c.n] = 1;
        });
        var tinta = getComputedStyle(document.body).color;
        var mx = Math.max.apply(null, z.map(function (f) { return Math.max.apply(null, f); }));
        var w = d.nx * d.dx, h = d.ny * d.dx, k = Math.max(w, h);
        document.getElementById("vista3d").parentNode.style.display = "block";
        btn.remove();
        Plotly.newPlot("vista3d", tr, {
          margin: { l: 0, r: 0, t: 30, b: 0 }, title: { text: d.titulo, font: { size: 13, color: tinta } }, paper_bgcolor: "rgba(0,0,0,0)", font: { color: tinta },
          legend: { orientation: "h", y: 0, font: { size: 11 } },
          scene: { aspectmode: "manual", aspectratio: { x: w / k, y: h / k, z: (mx * d.vexag) / k + 0.05 },
            xaxis: { visible: false }, yaxis: { visible: false }, zaxis: { visible: false }, camera: { eye: { x: 0.15, y: -0.95, z: 0.55 } } }
        }, { responsive: true, displaylogo: false });
      });
    };
    document.head.appendChild(s);
  });

  /* Comentarios */
  var todos = null;
  function fecha(t) { return new Date(t * 1000).toLocaleString("es-EC", { timeZone: "Pacific/Galapagos", dateStyle: "medium", timeStyle: "short" }); }
  function pintar(cont) {
    var sec = cont.dataset.seccion, lista = (todos || []).filter(function (c) { return (c.seccion || "general") === sec; });
    var abierto = cont.classList.contains("abierto");
    cont.innerHTML = "";
    var bt = document.createElement("button"); bt.className = "com-abrir"; bt.type = "button";
    bt.textContent = abierto ? "Ocultar comentarios" : (lista.length ? "💬 " + lista.length + " comentario" + (lista.length > 1 ? "s" : "") + " · comentar" : "💬 Comentar esta sección");
    bt.addEventListener("click", function () { cont.classList.toggle("abierto"); pintar(cont); });
    if (sec !== "general") cont.appendChild(bt);
    if (!abierto) return;
    var ul = document.createElement("ul"); ul.className = "com-lista";
    lista.forEach(function (c) {
      var li = document.createElement("li"), meta = document.createElement("span");
      meta.className = "com-meta"; meta.textContent = (c.nombre || "Anónimo") + " · " + fecha(c.creado);
      li.appendChild(meta); li.appendChild(document.createTextNode(c.texto)); ul.appendChild(li);
    });
    if (!lista.length) { var p = document.createElement("p"); p.className = "muted"; p.textContent = "Aún no hay comentarios en esta sección."; cont.appendChild(p); }
    cont.appendChild(ul);
    var f = document.createElement("form");
    f.innerHTML = '<input name="nombre" maxlength="60" placeholder="Nombre (opcional)" autocomplete="name">' +
      '<textarea name="texto" maxlength="2000" required placeholder="Tu comentario, dato o corrección (público)"></textarea>' +
      '<input class="trampa" name="web" tabindex="-1" autocomplete="off" aria-hidden="true">' +
      '<div><button class="boton" type="submit">Publicar comentario</button> <span class="estado"></span></div>' +
      '<p class="nota">Se publica al instante y es visible para todos. No incluyas datos personales de terceros (teléfonos, direcciones, nombres de afectados). Moderamos y retiramos mensajes inapropiados. Más en <a href="/privacidad">privacidad</a>.</p>';
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var est = f.querySelector(".estado"), boton = f.querySelector("button"); boton.disabled = true; est.textContent = "Enviando…";
      fetch(API, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pagina: E.pagina, seccion: sec === "general" ? "" : sec, nombre: f.nombre.value, texto: f.texto.value, web: f.web.value }) })
        .then(function (r) { return r.json().then(function (j) { return [r.ok, j]; }); })
        .then(function (x) { if (!x[0]) throw new Error(x[1].error || "error"); return cargar(); })
        .catch(function (e) { est.textContent = "No se pudo publicar: " + e.message; boton.disabled = false; });
    });
    cont.appendChild(f);
  }
  function cargar() {
    return fetch(API + "?pagina=" + encodeURIComponent(E.pagina)).then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (j) { todos = j.comentarios || []; document.querySelectorAll(".com").forEach(pintar); })
      .catch(function () { todos = todos || []; document.querySelectorAll(".com").forEach(function (c) { pintar(c); }); });
  }
  if (E.pagina && document.querySelector(".com")) cargar();
})();
