#!/bin/sh
# Odwołania2JSON: instalacja i uruchomienie jednym poleceniem (Linux/macOS): sh run.sh
# Tworzy .venv (Python 3.13+), instaluje zależności, przetwarza input/ -> output/.
set -eu
cd "$(dirname "$0")"

PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    for candidate in python3.13 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 \
            && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)' 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    done
fi
if [ -z "$PYTHON" ]; then
    echo "błąd: potrzebny Python 3.13+ (ustaw zmienną PYTHON=/ścieżka/do/python3.13)" >&2
    exit 2
fi

if [ ! -x .venv/bin/python ]; then
    "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt

mkdir -p input output

# Klucz LLM podaj zmienną środowiskową (nigdy w repozytorium ani w plikach śledzonych przez Git):
#   export LLM_API_KEY=...  LLM_BASE_URL=https://adres-api/v1  LLM_MODEL=nazwa-modelu
if [ -z "${LLM_API_KEY:-}" ]; then
    echo "uwaga: brak LLM_API_KEY; ustaw LLM_API_KEY, LLM_BASE_URL i LLM_MODEL (klucz trzymamy poza Git)." >&2
fi

exec .venv/bin/python -m odwolania2json process input output
