#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${ROOT_DIR}/tooling/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python 3 is required but '${PYTHON_BIN}' was not found." >&2
  exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/tooling/requirements-dev.txt"

if command -v uv >/dev/null 2>&1; then
  uv sync --project "${ROOT_DIR}/backend" --all-extras
else
  echo "uv not found; skipping backend dependency sync." >&2
fi

if command -v corepack >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}/frontend"
    corepack pnpm install
  )
else
  echo "corepack not found; skipping frontend dependency install." >&2
fi

echo "RouteX tooling environment is ready at ${VENV_DIR}."
