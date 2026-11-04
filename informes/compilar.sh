#!/usr/bin/env bash
# Compila un informe técnico de SOS Galápagos a PDF con pdfLaTeX + BibTeX (latexmk).
#   informes/compilar.sh 2026-02-tormentas-idf      → informes/2026-02-tormentas-idf/informe.pdf
#   informes/compilar.sh todos                      → todos los informes
# Requiere TeX Live o TinyTeX (ver informes/LEEME.md). Los auxiliares quedan en <informe>/.build/ (no versionado).
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
for d in "$HOME/Library/TinyTeX/bin/universal-darwin" "$HOME/.TinyTeX/bin/x86_64-linux" "$HOME/.TinyTeX/bin/aarch64-linux"; do
  [ -d "$d" ] && PATH="$d:$PATH"
done
command -v latexmk >/dev/null || { echo "Falta latexmk (TeX Live o TinyTeX). Ver informes/LEEME.md." >&2; exit 1; }

compilar() {
  local dir="$AQUI/$1"
  [ -f "$dir/informe.tex" ] || { echo "No existe $dir/informe.tex" >&2; return 1; }
  ( cd "$dir"
    TEXINPUTS="$AQUI/plantilla//:" BSTINPUTS="$AQUI/plantilla//:" BIBINPUTS="$AQUI//:" \
      latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=.build -quiet informe.tex >/dev/null \
      || { grep -E -A3 "^(\./)?informe.tex:[0-9]+:|^! " .build/informe.log | head -30 >&2; return 1; }
    cp .build/informe.pdf informe.pdf
    grep -E "LaTeX Warning: (Reference|Citation).*undefined" .build/informe.log | sort -u >&2 || true
    echo "✔ $1/informe.pdf" )
}

if [ "${1:-}" = "todos" ]; then
  for t in "$AQUI"/*/informe.tex; do compilar "$(basename "$(dirname "$t")")"; done
else
  compilar "${1:?Uso: informes/compilar.sh <carpeta-del-informe>|todos}"
fi
