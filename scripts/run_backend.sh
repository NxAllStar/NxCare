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

# The package lives under ./src and is not pip-installed (there is no [build-system] in
# pyproject.toml), so uvicorn needs --app-dir src to import `vaic` - the same src-on-path the
# pytest config uses. Without it, uvicorn fails with ModuleNotFoundError: No module named 'vaic'.
if command -v uv >/dev/null 2>&1; then
  uv sync --extra sql --extra dev
  exec uv run uvicorn --app-dir src vaic.api.app:app --reload --host 0.0.0.0 --port "$API_PORT"
else
  exec uvicorn --app-dir src vaic.api.app:app --reload --host 0.0.0.0 --port "$API_PORT"
fi
