#!/usr/bin/env bash
# Publica el build WebGL (Builds/WebGL) en la rama gh-pages para GitHub Pages.
# Uso (desde la raíz del repo, después de hacer el build WebGL en Unity):
#   bash Herramientas/publicar_web.sh
# La rama gh-pages solo contiene el build: no se mezcla con main, test ni develop.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$RAIZ/Builds/WebGL"
REMOTO="$(git -C "$RAIZ" remote get-url origin)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

[ -f "$BUILD/index.html" ] || { echo "No hay build en $BUILD (haz el build WebGL primero)"; exit 1; }

cp -r "$BUILD"/. "$TMP"/
touch "$TMP/.nojekyll"          # GitHub Pages no debe procesar los archivos con Jekyll
cd "$TMP"
git init -q -b gh-pages
git add -A
git commit -q -m "chore(web): publica el build webgl del $(date +%d/%m/%Y)"
git push -q -f "$REMOTO" gh-pages
echo "Publicado. En unos minutos: https://$(echo "$REMOTO" | sed -E 's#https://github.com/([^/]+)/([^/.]+)(\.git)?#\L\1\E.github.io/\2#')/"
