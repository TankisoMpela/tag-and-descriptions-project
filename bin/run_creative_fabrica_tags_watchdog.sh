#!/usr/bin/env bash
set -u

# Run the tag collector with a stale-heartbeat watchdog. The collector itself
# records page errors; this wrapper handles a browser process that stops
# producing progress while remaining alive.

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <heartbeat.json> <collector arguments...>" >&2
  exit 2
fi

heartbeat=$1
shift
stale_seconds=${CF_WATCHDOG_STALE_SECONDS:-300}
poll_seconds=${CF_WATCHDOG_POLL_SECONDS:-20}

node bin/collect_creative_fabrica_tags.mjs "$@" &
child=$!

watchdog() {
  while kill -0 "$child" 2>/dev/null; do
    if [[ -f "$heartbeat" ]]; then
      modified=$(stat -c %Y "$heartbeat" 2>/dev/null || date +%s)
      current=$(date +%s)
      age=$((current - modified))
      if (( age > stale_seconds )); then
        echo "[WATCHDOG ALERT] collector heartbeat is stale for ${age}s: ${heartbeat}" >&2
        echo "[WATCHDOG ALERT] terminating collector pid ${child}" >&2
        kill -TERM "$child" 2>/dev/null || true
        sleep 10
        kill -KILL "$child" 2>/dev/null || true
        return
      fi
    fi
    sleep "$poll_seconds"
  done
}

watchdog &
watchdog_pid=$!
wait "$child"
result=$?
kill "$watchdog_pid" 2>/dev/null || true
wait "$watchdog_pid" 2>/dev/null || true

if [[ $result -eq 0 ]]; then
  echo "[WATCHDOG] collector exited normally"
  if grep -q '"status": "INCOMPLETE"\|"status": "INTERRUPTED"' "$heartbeat" 2>/dev/null; then
    echo "[WATCHDOG ALERT] collector completed without a complete dataset; inspect ${heartbeat}" >&2
  fi
else
  echo "[WATCHDOG ALERT] collector exited with status ${result}" >&2
fi
exit "$result"
