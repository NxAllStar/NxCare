#!/usr/bin/env bash
#
# VAIC real-time clinic data simulator - runner.
#
# Keeps the live PostgreSQL store looking like a working clinic: patients arrive, get an appointment,
# take a number, move through consult and their tests, and finish - with arrivals balanced against
# completions so the queues never explode. All data written is synthetic; nothing is ever deleted.
#
# Usage:
#   ./simulate.sh bootstrap     # one-time: create the fake departments the queue needs
#   ./simulate.sh once          # advance the world by one tick (use this from cron)
#   ./simulate.sh loop          # advance continuously in the foreground (real-time feel)
#   ./simulate.sh status        # print live queue depth per department and the balance budget
#   ./simulate.sh install-cron  # print the crontab line to run `once` every minute
#
# Connection: read from the repo .env (POSTGRES_HOST/PORT/NAME/USER/PASSWORD), same as the app.
# Tuning: export any SIM_* var before calling (see README.md). Common ones:
#   SIM_ARRIVALS_PER_TICK  expected new patients per tick (default 0.25)
#   SIM_INTERVAL_SEC       loop tick interval in seconds (default 15)
#   SIM_SEC_PER_MIN        real seconds per simulated service-minute (default 3)
#   SIM_WIP_CAP            max patients in the system before arrivals pause (default 40)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENGINE="$SCRIPT_DIR/engine.py"

# --- resolve a Python interpreter that has asyncpg (prefer the repo venv) ----------------------
PYTHON="${SIM_PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
  else
    PYTHON="$(command -v python3 || command -v python || true)"
  fi
fi
if [[ -z "$PYTHON" ]]; then
  echo "error: no python interpreter found (set SIM_PYTHON)" >&2
  exit 1
fi

# --- load DB connection from .env if the caller has not already exported it --------------------
ENV_FILE="${SIM_ENV_FILE:-$REPO_ROOT/.env}"
if [[ -z "${POSTGRES_HOST:-}${DATABASE_DSN:-}" && -f "$ENV_FILE" ]]; then
  # Export every KEY=VALUE line; ignore comments and blanks. Strips optional surrounding quotes.
  while IFS='=' read -r key val; do
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    val="${val%\"}"; val="${val#\"}"
    val="${val%\'}"; val="${val#\'}"
    export "$key=$val"
  done < <(grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | sed 's/^[[:space:]]*//')
fi

cmd="${1:-}"
case "$cmd" in
  bootstrap) exec "$PYTHON" "$ENGINE" bootstrap ;;
  once|tick) exec "$PYTHON" "$ENGINE" tick ;;
  loop)      exec "$PYTHON" "$ENGINE" loop ;;
  status)    exec "$PYTHON" "$ENGINE" status ;;
  install-cron)
    echo "# Run one simulator tick every minute. Add to 'crontab -e':"
    echo "* * * * * $SCRIPT_DIR/simulate.sh once >> /tmp/vaic-sim.log 2>&1"
    echo "#"
    echo "# For a smoother real-time feel, run the loop under a supervisor instead:"
    echo "#   $SCRIPT_DIR/simulate.sh loop"
    ;;
  *)
    echo "usage: $0 {bootstrap|once|loop|status|install-cron}" >&2
    exit 2
    ;;
esac
