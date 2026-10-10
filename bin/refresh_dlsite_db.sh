#!/usr/bin/env bash
# Refresh the DLsite SQLite database from the latest collector output.
#
# Reads crawl-state.json mid-crawl (atomic writes, safe) or the final
# CSV/JSONL once the crawl finishes, plus the frozen DLsite font tag bank,
# then rebuilds outputs/research/dlsite-live-collector/dlsite.db and runs the analyzer.
#
# Usage:
#   bin/refresh_dlsite_db.sh                          # default crawl source
#   bin/refresh_dlsite_db.sh /path/to/crawl-output    # custom source dir/file
#
# Full, fast rebuild (disposable DB) — safe to run any time.
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

SOURCE="${1:-outputs/research/dlsite-live-collector/$(date +%F)/tools-accessories}"
if [ ! -d "$SOURCE" ]; then
  # fallback to most recent directory under outputs/research/dlsite-live-collector/
  SOURCE="$(find outputs/research/dlsite-live-collector -type d -name "tools-accessories" | sort -r | head -1)"
fi

BANK="${DLSITE_BANK:-outputs/research/dlsite-font-tag-bank.md}"
DB="${DLSITE_DB:-outputs/research/dlsite-live-collector/dlsite.db}"

echo "=== Building DLsite DB from $SOURCE ==="
"$PY" bin/build_dlsite_db.py \
  --source "$SOURCE" \
  --bank "$BANK" \
  --db "$DB"

echo
echo "=== Running DLsite Collection Analysis ==="
"$PY" bin/analyze_dlsite_collection.py \
  --db "$DB" \
  --bank "$BANK"

echo
echo "Query it with:"
echo "  $PY bin/query_dlsite_db.py --competitors 'ファンタジー'"
echo "  $PY bin/query_dlsite_db.py --check-keywords '同人誌,漫画,ゲーム制作,書体'"
echo "  $PY bin/dlsite_tag_evidence.py '同人誌' '漫画' 'ゲーム制作'"
echo "  $PY bin/query_dlsite_db.py \"SELECT product_id, title, sales_count, favorites_count, price_jpy FROM items ORDER BY sales_count DESC LIMIT 10;\""
