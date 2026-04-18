#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

load_root_env
require_command python3 "python3 is required but was not found on PATH."

VENV_PYTHON="$ROOT_DIR/backend/venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Backend virtual environment not found. Run 'make install' first."
  exit 1
fi

cd "$ROOT_DIR/backend"
"$VENV_PYTHON" -m uvicorn app.asgi:app --host "${APP_HOST:-${BACKEND_HOST:-0.0.0.0}}" --port "${APP_PORT:-${BACKEND_PORT:-8000}}" --workers "${APP_WORKERS:-1}" --log-level "${LOG_LEVEL:-info}"
