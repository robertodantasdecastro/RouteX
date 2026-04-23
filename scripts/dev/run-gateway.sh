#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export ROUTEX_RUNTIME_ROOT="${ROOT_DIR}"
export ROUTEX_STATE_DIR="${ROOT_DIR}/var/state"
export ROUTEX_LOGS_DIR="${ROOT_DIR}/var/logs"
export ROUTEX_DAEMON_PID_FILE="${ROOT_DIR}/var/state/daemon.pid"

exec "${ROOT_DIR}/scripts/runtime/run-gateway-alpha.sh"
