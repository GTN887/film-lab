#!/usr/bin/env bash
# Offline-first start for this box. Windows users double-click START_FILM_LAB.bat.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export FILM_LAB_PORT="${FILM_LAB_PORT:-43123}"
export FILM_LAB_HOST="${FILM_LAB_HOST:-127.0.0.1}"
mkdir -p "$ROOT/data/logs"
echo "FILM LAB — Works offline for local generation."
if ! curl -sf -o /dev/null "http://127.0.0.1:${FILM_LAB_PORT}/"; then
  if [[ -x "$ROOT/scripts/run.sh" ]]; then
    nohup "$ROOT/scripts/run.sh" >>"$ROOT/data/logs/film_lab.log" 2>&1 &
  else
    nohup python "$ROOT/app.py" >>"$ROOT/data/logs/film_lab.log" 2>&1 &
  fi
  echo "Started Film Lab on 127.0.0.1:${FILM_LAB_PORT}"
fi
for _ in $(seq 1 40); do
  if curl -sf -o /dev/null "http://127.0.0.1:${FILM_LAB_PORT}/"; then
    break
  fi
  sleep 1
done
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:${FILM_LAB_PORT}" >/dev/null 2>&1 || true
fi
echo "Open http://127.0.0.1:${FILM_LAB_PORT}"
