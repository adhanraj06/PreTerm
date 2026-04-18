#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

rm -rf "$ROOT_DIR/backend/.pytest_cache"
rm -rf "$ROOT_DIR/backend/.mypy_cache"
rm -rf "$ROOT_DIR/backend/app/__pycache__"
find "$ROOT_DIR/backend" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$ROOT_DIR/backend" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
rm -rf "$ROOT_DIR/frontend/dist"
rm -rf "$ROOT_DIR/frontend/.vite"

echo "Removed caches and temporary artifacts."

