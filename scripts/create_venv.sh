#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/backend/venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH."
  exit 1
fi

if [[ -x "$VENV_DIR/bin/python" ]]; then
  echo "Virtual environment already exists at backend/venv"
  exit 0
fi

python3 -m venv "$VENV_DIR"
echo "Created virtual environment at backend/venv"

