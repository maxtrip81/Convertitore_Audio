#!/bin/bash
# Convertitore Audio — a cura di Massimiliano Mascioli Trippa
# Crea "dist/Convertitore Audio.app" e "dist/ConvertitoreAudio-macOS.zip".
# Uso:  ./build_mac.sh        (oppure  PYTHON=/percorso/python3 ./build_mac.sh)
set -euo pipefail
cd "$(dirname "$0")"

has_tk86() { "$1" -c 'import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) and tkinter.TkVersion >= 8.6 else 1)' 2>/dev/null; }

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1 && has_tk86 "$c"; then PY="$c"; break; fi
  done
fi
if [ -z "$PY" ] || ! has_tk86 "$PY"; then
  echo "Serve Python 3.9+ con Tk 8.6 o superiore."
  echo "Installalo da https://www.python.org/downloads/macos/ e rilancia questo script."
  echo "(Il Python di sistema di macOS usa Tk 8.5 ed e' sconsigliato.)"
  exit 1
fi
echo "Uso $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

"$PY" -m venv .venv-build
.venv-build/bin/python -m pip install --quiet --upgrade pip
.venv-build/bin/python -m pip install --quiet -r requirements-build.txt
.venv-build/bin/pyinstaller --noconfirm --clean ConvertitoreAudio.spec

rm -f dist/ConvertitoreAudio-macOS.zip
ditto -c -k --keepParent "dist/Convertitore Audio.app" dist/ConvertitoreAudio-macOS.zip
echo
echo "Fatto:"
echo "  dist/Convertitore Audio.app"
echo "  dist/ConvertitoreAudio-macOS.zip"
