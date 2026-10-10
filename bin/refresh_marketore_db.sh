#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON:-python3}"
OUT="${MARKETORE_OUT:-outputs/research/marketore-live-collector}"

"$PYTHON_BIN" bin/collect_marketore_fonts.py --out "$OUT" "$@"
"$PYTHON_BIN" bin/analyze_marketore_collection.py \
  --db "$OUT/marketore.db" \
  --out outputs/research/marketore-collection-analysis.md

echo "Query: $PYTHON_BIN bin/query_marketore_db.py --db $OUT/marketore.db"
