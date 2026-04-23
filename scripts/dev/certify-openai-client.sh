#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARTIFACT_DIR="${ROUTEX_OPENAI_CLIENT_ARTIFACT_DIR:-${ROOT_DIR}/tooling/artifacts/openai-client/${TIMESTAMP}}"
HEALTH_URL="${ROUTEX_PUBLIC_BASE_URL:-http://127.0.0.1:48200}/health"
ATTEMPTS="${ROUTEX_OPENAI_CLIENT_ATTEMPTS:-3}"

wait_for_health() {
  local tries="${1:-20}"
  local count=1
  while [ "${count}" -le "${tries}" ]; do
    if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    count=$((count + 1))
  done
  return 1
}

attempt=1
while [ "${attempt}" -le "${ATTEMPTS}" ]; do
  wait_for_health 20 || {
    printf '[certify-openai-client] RouteX nao respondeu em %s\n' "${HEALTH_URL}" >&2
    exit 1
  }

  if uv run --project "${ROOT_DIR}/backend" --extra ops \
    python "${ROOT_DIR}/scripts/dev/routex_openai_client.py" certify \
    --artifact-dir "${ARTIFACT_DIR}" \
    "$@"; then
    printf '[certify-openai-client] Artifacts: %s\n' "${ARTIFACT_DIR}"
    exit 0
  fi

  printf '[certify-openai-client] tentativa %s/%s falhou, repetindo...\n' "${attempt}" "${ATTEMPTS}" >&2
  sleep 2
  attempt=$((attempt + 1))
done

exit 1
