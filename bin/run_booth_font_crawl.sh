#!/usr/bin/env bash
# Detached, self-restarting wrapper for the BOOTH Fonts-category crawl.
#
# The collector is fully resumable (crawl-state.json), so a crashed or failed
# run is simply re-invoked with --resume until it completes (exit 0). A
# SIGTERM/SIGINT (e.g. shutdown, deliberate stop) stops the loop cleanly.
#
# Launch detached with:
#   setsid nohup bin/run_booth_font_crawl.sh >/dev/null 2>&1 &
set -u
cd "$(dirname "$0")/.."

OUT="outputs/research/booth-live-collector/2026-09-08/fonts-popular"
LOG="$OUT/crawl-resume.log"
START="https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93?sort=popular"

trap 'echo "[wrapper] $(date +%F_%T) stopping via SIGTERM" >> "$LOG"; _stoppable=1; exit 0' TERM

while true; do
  echo "[wrapper] $(date +%F_%T) starting crawl (resume)" >> "$LOG"
  ".venv/bin/python" bin/collect_booth_category.py \
    --start "$START" \
    --detail-limit 999999 \
    --browser \
    --resume \
    --out "$OUT" \
    >> "$LOG" 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[wrapper] $(date +%F_%T) crawl completed successfully (exit 0)" >> "$LOG"
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