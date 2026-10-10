#!/usr/bin/env bash
# Headless OpenPencil `eval` helper for Agent 27 / CLI workflows.
#
# Wraps the official `openpencil eval <file>.fig -c <js>` headless scripting
# path (Figma plugin API against a .fig document, no desktop app required).
# See font-factory/openpencil/CAPABILITIES.md § "CLI eval" for the verified
# contract and a worked example.
#
# Usage:
#   bin/openpencil_eval.sh <file.fig> '<javascript>' [--write]
#
# Examples:
#   bin/openpencil_eval.sh doc.fig "return figma.currentPage.name"
#   bin/openpencil_eval.sh doc.fig "figma.currentPage.children[0].name='X'" --write
#
# The first arg is the .fig path; the second is the JS to evaluate. `--write`
# (or `-o`) is passed through so mutations persist back to the .fig file.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <file.fig> '<javascript>' [--write]" >&2
  exit 2
fi

fig="$1"
js="$2"
shift 2

exec npx --no-install openpencil eval "$fig" -c "$js" "$@"
