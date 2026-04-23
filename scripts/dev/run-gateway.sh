#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -x "${ROOT_DIR}/backend/.venv/bin/python" ]; then
  "${ROOT_DIR}/backend/.venv/bin/python" -m uvicorn routex_gateway.main:app \
    --host 127.0.0.1 \
    --port 48200 \
    --app-dir "${ROOT_DIR}/backend/src"
else
  uv run --project "${ROOT_DIR}/backend" uvicorn routex_gateway.main:app \
    --host 127.0.0.1 \
    --port 48200 \
    --app-dir "${ROOT_DIR}/backend/src"
fi
