#!/usr/bin/env bash
# Run the VAIC FastAPI backend locally with uvicorn.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

API_PORT="${API_PORT:-8000}"

if command -v uv >/dev/null 2>&1; then
  exec uv run uvicorn vaic.api.app:app --reload --host 0.0.0.0 --port "$API_PORT"
else
  exec uvicorn vaic.api.app:app --reload --host 0.0.0.0 --port "$API_PORT"
fi
