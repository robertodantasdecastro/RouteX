#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROUTEX_RUNTIME_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STATE_DIR="${ROUTEX_STATE_DIR:-${HOME}/Library/Caches/com.robertodantasdecastro.routex/state}"
LOGS_DIR="${ROUTEX_LOGS_DIR:-${HOME}/Library/Logs/RouteX}"
HOST="${ROUTEX_HOST:-127.0.0.1}"
PORT="${ROUTEX_PORT:-48200}"
PID_FILE="${ROUTEX_DAEMON_PID_FILE:-${STATE_DIR}/daemon.pid}"
BROKER_SOCKET="${ROUTEX_SECRET_BROKER_SOCKET:-/tmp/routex-keychain.sock}"

mkdir -p "${STATE_DIR}" "${LOGS_DIR}"

export ROUTEX_APP_ENV="${ROUTEX_APP_ENV:-alpha}"
export ROUTEX_HOST="${HOST}"
export ROUTEX_PORT="${PORT}"
export ROUTEX_CONFIG_DIR="${ROUTEX_CONFIG_DIR:-${ROOT_DIR}/configs}"
export ROUTEX_PROJECT_CONFIGS_DIR="${ROUTEX_PROJECT_CONFIGS_DIR:-${ROOT_DIR}/.routex}"
export ROUTEX_LOGS_DIR="${LOGS_DIR}"
export ROUTEX_SECRET_BROKER_SOCKET="${BROKER_SOCKET}"
export ROUTEX_DAEMON_PID_FILE="${PID_FILE}"

if [ -z "${ROUTEX_DATABASE_URL:-}" ]; then
  DB_PATH="${STATE_DIR}/routex.db"
  export ROUTEX_DATABASE_URL="sqlite+aiosqlite:///${DB_PATH}"
fi

if [ -n "${ROUTEX_UV_BIN:-}" ] && [ -x "${ROUTEX_UV_BIN}" ]; then
  UV_BIN="${ROUTEX_UV_BIN}"
elif command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
else
  echo "RouteX alpha runtime requer 'uv' no PATH ou ROUTEX_UV_BIN apontando para o binario." >&2
  exit 1
fi

PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python"
if [ ! -x "${PYTHON_BIN}" ] || ! "${PYTHON_BIN}" -c "import uvicorn" >/dev/null 2>&1; then
  "${UV_BIN}" sync --project "${ROOT_DIR}/backend" --locked --no-dev
fi

if [ ! -x "${PYTHON_BIN}" ] || ! "${PYTHON_BIN}" -c "import uvicorn" >/dev/null 2>&1; then
  echo "RouteX alpha runtime nao conseguiu preparar o backend/.venv com uvicorn." >&2
  exit 1
fi

echo "$$" > "${PID_FILE}"
exec "${PYTHON_BIN}" -m uvicorn routex_gateway.main:app \
  --host "${HOST}" \
  --port "${PORT}" \
  --app-dir "${ROOT_DIR}/backend/src"
