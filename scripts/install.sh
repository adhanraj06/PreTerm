#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/backend/venv/bin/python"
VENV_PIP="$ROOT_DIR/backend/venv/bin/pip"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found on PATH."
  exit 1
fi

bash "$ROOT_DIR/scripts/create_venv.sh"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Failed to create backend virtual environment."
  exit 1
fi

"$VENV_PIP" install --upgrade pip
"$VENV_PIP" install -r "$ROOT_DIR/backend/requirements.txt"

cd "$ROOT_DIR/frontend"
npm install

echo "Installed backend dependencies into backend/venv and frontend dependencies into frontend/node_modules"

