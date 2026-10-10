#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

for command_name in rsvg-convert magick pngquant; do
  command -v "$command_name" >/dev/null || {
    printf 'Missing required system command: %s\n' "$command_name" >&2
    exit 1
  }
done

python3 -m venv --system-site-packages .venv-deterministic-fonts
.venv-deterministic-fonts/bin/python -m pip install --upgrade pip
.venv-deterministic-fonts/bin/python -m pip install -r requirements-deterministic-visuals.txt

printf 'Deterministic font visual environment is ready.\n'
