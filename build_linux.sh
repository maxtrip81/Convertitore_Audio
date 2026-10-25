#!/bin/bash
# Convertitore Audio — a cura di Massimiliano Mascioli Trippa
# Crea "dist/ConvertitoreAudio" e "dist/ConvertitoreAudio-Linux-x64.tar.gz".
# Serve Python 3.9+ con tkinter (es. sudo apt install python3-venv python3-tk).
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
"$PY" -c 'import tkinter' || { echo "Manca tkinter: sudo apt install python3-tk"; exit 1; }

"$PY" -m venv .venv-build
.venv-build/bin/python -m pip install --quiet --upgrade pip
.venv-build/bin/python -m pip install --quiet -r requirements-build.txt
.venv-build/bin/pyinstaller --noconfirm --clean ConvertitoreAudio.spec

tar -czf dist/ConvertitoreAudio-Linux-x64.tar.gz -C dist ConvertitoreAudio
echo
echo "Fatto:"
echo "  dist/ConvertitoreAudio"
echo "  dist/ConvertitoreAudio-Linux-x64.tar.gz"
