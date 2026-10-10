#!/usr/bin/env bash
# Refresh the BOOTH SQLite database from the latest collector output.
#
# Reads crawl-state.json mid-crawl (atomic writes, safe) or the final
# CSV/JSONL once the crawl finishes, plus the FontFairy rank CSV and the
# frozen tag bank, then rebuilds outputs/research/booth-live-collector/booth.db.
#
# Usage:
#   bin/refresh_booth_db.sh                          # default crawl source
#   bin/refresh_booth_db.sh /path/to/crawl-output    # custom source dir/file
#
# The build is a full, fast rebuild (disposable DB) — safe to run any time.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-}"
if [ -z "$PY" ] && [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
fi
if [ -z "$PY" ]; then
  PY="python3"
fi

SOURCE="${1:-outputs/research/booth-live-collector/2026-09-08/fonts-popular}"
RANK="${BOOTH_RANK:-$HOME/Downloads/booth-rank-papermoonstudio-2026-09-08.csv}"
BANK="${BOOTH_BANK:-outputs/research/booth-font-tag-bank.md}"
DB="${BOOTH_DB:-outputs/research/booth-live-collector/booth.db}"

"$PY" bin/build_booth_db.py \
  --source "$SOURCE" \
  --rank "$RANK" \
  --bank "$BANK" \
  --db "$DB"

# build_booth_db.py writes only the base tables. The analysis_* tables that
# bin/booth_tag_evidence.py reads (--top-lanes, and the per-tag lift/win-rate
# gate) are written by analyze_booth_collection.py. Skipping this step leaves
# the DB without those tables, and booth_tag_evidence.py then dies with
# "no such table: analysis_tag_lift".
COLLECTION_CSV="$(ls "$SOURCE"/*-items.csv 2>/dev/null | head -1 || true)"
if [ -n "$COLLECTION_CSV" ]; then
  "$PY" bin/analyze_booth_collection.py \
    --collection "$COLLECTION_CSV" \
    --rank "$RANK" \
    --bank "$BANK" \
    --db "$DB"
else
  echo "WARNING: no *-items.csv under $SOURCE — analysis_* tables not rebuilt;" >&2
  echo "         bin/booth_tag_evidence.py will fail until they are." >&2
fi

echo
echo "Query it with:"
echo "  $PY bin/query_booth_db.py \"SELECT tag, count(*) FROM item_tags GROUP BY tag ORDER BY 2 DESC LIMIT 15;\""
echo "  sqlite3 '$DB' \"SELECT title, item_like_count, published FROM items WHERE detail_fetched=1 ORDER BY item_like_count DESC LIMIT 10;\""