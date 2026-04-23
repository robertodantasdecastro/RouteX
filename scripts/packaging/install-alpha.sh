#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_PATH="/Applications/RouteX.app"
MOUNT_DIR="/tmp/routex-alpha-install.$$"
RUNTIME_ROOT="${HOME}/Library/Application Support/com.robertodantasdecastro.routex/runtime/0.2.0-alpha"
LAUNCH_AGENT_LABEL="${ROUTEX_LAUNCH_AGENT_LABEL:-com.robertodantasdecastro.routex.gateway}"
VERSION="$(
  ROOT_DIR="${ROOT_DIR}" python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
config = json.loads((root / "src-tauri" / "tauri.conf.json").read_text())
print(config["version"])
PY
)"
DEFAULT_DMG="$(find "${ROOT_DIR}/tooling/artifacts/macos-alpha/${VERSION}" "${ROOT_DIR}/src-tauri/target/release/bundle/dmg" -maxdepth 1 -name '*.dmg' -print 2>/dev/null | head -n 1)"
DMG_PATH="${1:-${DEFAULT_DMG}}"

if [ -z "${DMG_PATH}" ] || [ ! -f "${DMG_PATH}" ]; then
  echo "DMG alpha nao encontrado. Rode 'make package-macos' primeiro." >&2
  exit 1
fi

mkdir -p "${MOUNT_DIR}"
cleanup() {
  hdiutil detach "${MOUNT_DIR}" >/dev/null 2>&1 || true
  rm -rf "${MOUNT_DIR}"
}
trap cleanup EXIT

echo "==> Montando ${DMG_PATH}"
hdiutil attach "${DMG_PATH}" -nobrowse -readonly -mountpoint "${MOUNT_DIR}" >/dev/null

if [ ! -d "${MOUNT_DIR}/RouteX.app" ]; then
  echo "RouteX.app nao encontrado dentro do DMG montado." >&2
  exit 1
fi

echo "==> Instalando RouteX.app em /Applications"
launchctl bootout "gui/$(id -u)/${LAUNCH_AGENT_LABEL}" >/dev/null 2>&1 || true
pkill -f 'run-gateway-alpha.sh|uvicorn routex_gateway.main:app' >/dev/null 2>&1 || true
rm -rf "${RUNTIME_ROOT}"
rm -rf "${APP_PATH}"
ditto "${MOUNT_DIR}/RouteX.app" "${APP_PATH}"
xattr -dr com.apple.quarantine "${APP_PATH}" >/dev/null 2>&1 || true

echo "==> Abrindo RouteX.app"
/usr/bin/open -n "${APP_PATH}"

echo "Instalacao alpha concluida em ${APP_PATH}"
