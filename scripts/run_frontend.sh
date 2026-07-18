#!/usr/bin/env bash
# Run the VAIC React frontend locally with Vite.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../frontend"

if [ ! -d node_modules ]; then
  npm install
fi

exec npm run dev
