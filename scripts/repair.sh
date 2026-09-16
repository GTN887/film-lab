#!/usr/bin/env bash
# Repair toolkit (offline). Windows: REPAIR.bat
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ACTION="${1:-menu}"
PORT="${FILM_LAB_PORT:-43123}"
COMFY="${FILM_LAB_COMFY_PORT:-8188}"
mkdir -p "$ROOT/data/logs"

kill_port() {
  local p="$1"
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${p}/tcp" >/dev/null 2>&1 || true
  fi
  if command -v ss >/dev/null 2>&1; then
    true
  fi
}

case "$ACTION" in
  kill-ports)
    kill_port "$PORT"
    kill_port "$COMFY"
    echo "Killed $PORT / $COMFY (best effort)."
    ;;
  logs)
    echo "$ROOT/data/logs"
    ;;
  safe)
    echo "480p / 5s" > "$ROOT/data/safe_mode.flag"
    export FILM_LAB_SAFE_MODE=1
    echo "Safe mode on. Restart Film Lab."
    ;;
  restart-lab)
    kill_port "$PORT"
    nohup "$ROOT/scripts/run.sh" >>"$ROOT/data/logs/film_lab.log" 2>&1 &
    echo "Restarted Film Lab."
    ;;
  *)
    echo "FILM LAB Repair (offline)"
    echo "  $0 restart-lab | kill-ports | logs | safe"
    echo "Works offline for local generation."
    ;;
esac
