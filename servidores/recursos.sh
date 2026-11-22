#!/bin/sh
# SOS Galápagos · © 2026 Universidad San Francisco de Quito (USFQ) · Autor: Julián Maya <jamaya@usfq.edu.ec>
# Todos los derechos reservados. Usar, copiar, modificar o derivar de este código requiere permiso escrito del autor (ver LICENSE).
# Uso de recursos del servidor de sosgalapagos.org.
#   recursos.sh            muestra el estado de ahora, para leerlo una persona
#   recursos.sh --registrar añade una línea a /var/log/sosgalapagos-recursos.csv (lo corre el timer cada 15 min)
#   recursos.sh --resumen   máximos y promedios de los últimos 7 días del registro
# Se instala en /usr/local/bin/sosgalapagos-recursos (ver servidores/README.md).
REG=/var/log/sosgalapagos-recursos.csv
mem() { free -m | awk '/^Mem:/{print $3","$7}'; }                 # usada, disponible (MB)
carga() { cut -d" " -f1,2 /proc/loadavg | tr " " ","; }           # carga a 1 y 5 min
disco() { df -P / | awk 'NR==2{gsub("%","",$5); print $5}'; }      # % de disco usado
contenedores() {                                                    # MB de memoria por grupo de contenedores
  docker stats --no-stream --format "{{.Name}} {{.MemUsage}}" 2>/dev/null | awk '
    function mb(v){ if (v ~ /GiB/) return v*1024; if (v ~ /KiB/) return v/1024; return v+0 }
    { m=mb($2); if ($1 ~ /^sosgalapagos-plataforma/) r+=m; else if ($1 ~ /^sosgalapagos-/) s+=m; else o+=m }
    END { printf "%.0f,%.0f,%.0f", r, s, o }'
}
case "${1:-}" in
  --registrar)
    [ -f "$REG" ] || echo "fecha_utc,mem_usada_mb,mem_disponible_mb,carga_1m,carga_5m,disco_pct,riesgos_mb,sitio_mb,otros_mb" > "$REG"
    echo "$(date -u +%FT%TZ),$(mem),$(carga),$(disco),$(contenedores)" >> "$REG"
    # Un año de registros ocupa unos 3 MB; al pasar de 5 MB se guarda el anterior y se empieza otro.
    [ "$(stat -c %s "$REG")" -gt 5000000 ] && mv "$REG" "$REG.anterior"
    exit 0 ;;
  --resumen)
    [ -f "$REG" ] || { echo "Todavía no hay registro."; exit 0; }
    tail -n 672 "$REG" | awk -F, 'NR>1 && $2+0>0 { n++; mu+=$2; if ($2>mx) mx=$2; if ($4>cx) cx=$4; c+=$4; d=$6; r+=$7; s+=$8 }
      END { if (!n) { print "Sin datos."; exit }
        printf "Últimas %d mediciones (%.1f días)\n  memoria usada: promedio %.0f MB, máximo %.0f MB\n  carga (1 min): promedio %.2f, máximo %.2f\n  disco: %s %%\n  mapa de riesgos: %.0f MB · sitio: %.0f MB (promedios)\n", n, n/96, mu/n, mx, c/n, cx, d, r/n, s/n }'
    exit 0 ;;
esac
echo "== Equipo"; echo "CPU: $(nproc) · carga: $(cut -d" " -f1-3 /proc/loadavg)"; free -m | sed -n 1,2p; df -h / | tail -1
echo "== Contenedores (memoria)"; docker stats --no-stream --format "{{.MemUsage}}\t{{.CPUPerc}}\t{{.Name}}" | sort -k1 -hr
echo "== Disco de Docker"; docker system df
echo "== Carpetas"; du -sh /var/lib/sosgalapagos-clima /srv/sosgalapagos-* /opt/sosgalapagos* 2>/dev/null | sort -rh
