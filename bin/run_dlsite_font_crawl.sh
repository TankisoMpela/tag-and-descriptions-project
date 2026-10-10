#!/usr/bin/env bash
# Detached, self-restarting wrapper for DLsite Tools/Accessories crawl.
#
# Walks the full 55 pages of TOL (~1,126 items), enriches with sales/favorites
# via the official batch AJAX API (/home/product/info/ajax), fetches detail pages,
# rebuilds outputs/research/dlsite-live-collector/dlsite.db, and runs analysis.
#
# Fully resumable (crawl-state.json).
#
# Launch detached with:
#   setsid nohup bin/run_dlsite_font_crawl.sh >/dev/null 2>&1 &
set -u
cd "$(dirname "$0")/.."

DATE="$(date +%F)"
OUT="outputs/research/dlsite-live-collector/${DATE}/tools-accessories"
LOG="$OUT/crawl-resume.log"
mkdir -p "$OUT"

START="https://www.dlsite.com/home/fsr/=/work_type/TOL/work_type_name/%E3%83%84%E3%83%BC%E3%83%AB%2F%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA/language/jp/age_category/general/order/trend/per_page/30/page/1/show_type/3"

PY="${PYTHON:-}"
if [ -z "$PY" ] && [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
fi
if [ -z "$PY" ]; then
  PY="python3"
fi

trap 'echo "[wrapper] $(date +%F_%T) stopping via SIGTERM" >> "$LOG"; exit 0' TERM

while true; do
  echo "[wrapper] $(date +%F_%T) starting DLsite TOL crawl (resume)" >> "$LOG"
  "$PY" bin/collect_dlsite_category.py \
    --start "$START" \
    --detail-limit 300 \
    --concurrency 2 \
    --resume \
    --out "$OUT" \
    2>&1 | tee -a "$LOG"
  rc="${PIPESTATUS[0]}"
  if [ "$rc" -eq 0 ]; then
    echo "[wrapper] $(date +%F_%T) crawl completed successfully (exit 0)" | tee -a "$LOG"
    echo "[wrapper] rebuilding dlsite.db..." | tee -a "$LOG"
    bin/refresh_dlsite_db.sh "$OUT" 2>&1 | tee -a "$LOG"
    break
  fi
  if [ "$rc" -eq 143 ] || [ "$rc" -eq 130 ]; then
    echo "[wrapper] $(date +%F_%T) crawl stopped by signal (rc=$rc); not auto-restarting" >> "$LOG"
    break
  fi
  echo "[wrapper] $(date +%F_%T) crawl exited rc=$rc; resuming in 20s..." >> "$LOG"
  sleep 20
done
exit 0
