#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
VENV="$PWD/.venv-linux"
for tool in pactl parec; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Missing $tool. Install PulseAudio client tools (see README.md)." >&2
        exit 1
    fi
done
if ! pactl info >/dev/null 2>&1; then
    echo 'No PulseAudio-compatible server found. Run as your desktop user with PulseAudio or PipeWire-Pulse active.' >&2
    exit 1
fi
if [[ ! -x "$VENV/bin/python" ]]; then
    PY=''
    for candidate in python3.13 python3.12 python3.11 python3; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys, struct, tkinter, venv; assert (3, 11) <= sys.version_info[:2] <= (3, 13) and struct.calcsize("P") == 8' >/dev/null 2>&1; then
            PY="$candidate"
            break
        fi
    done
    if [[ -z "$PY" ]]; then
        echo 'Install 64-bit Python 3.11–3.13 with Tk and venv support (see README.md).' >&2
        exit 1
    fi
    "$PY" -m venv "$VENV" || { echo 'Could not create virtual environment. Install your Python version’s venv package.' >&2; exit 1; }
fi
PY="$VENV/bin/python"
"$PY" -c 'import sys, struct, tkinter; assert (3,11) <= sys.version_info[:2] <= (3,13) and struct.calcsize("P") == 8'
if ! "$PY" -c 'import numpy, scipy, faster_whisper' >/dev/null 2>&1; then
    echo 'Installing dependencies from PyPI. Internet connection required.'
    "$PY" -m pip install --upgrade pip
    "$PY" -m pip install --only-binary=:all: -r requirements.txt
fi
exec "$PY" japanese_live_captions.py "$@"
