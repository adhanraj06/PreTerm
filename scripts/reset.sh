#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$ROOT_DIR/scripts/clean.sh"
rm -rf "$ROOT_DIR/backend/venv"
rm -rf "$ROOT_DIR/frontend/node_modules"
rm -f "$ROOT_DIR/backend/preterm.db"
rm -f "$ROOT_DIR/preterm.db"

echo "Removed install artifacts and local database files. Run 'make install' to rebuild."
