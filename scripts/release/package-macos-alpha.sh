#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
ARTIFACT_DIR="${ROOT_DIR}/tooling/artifacts/macos-alpha/${VERSION}"

mkdir -p "${ARTIFACT_DIR}"
rm -rf "${ARTIFACT_DIR}/RouteX.app" "${ARTIFACT_DIR}"/*.dmg "${ARTIFACT_DIR}/build-summary.json" 2>/dev/null || true

echo "==> Validando RouteX alpha ${VERSION}"
make -C "${ROOT_DIR}" validate
make -C "${ROOT_DIR}" test
make -C "${ROOT_DIR}" build-frontend
"${ROOT_DIR}/scripts/release/build-runtime-bundle.sh"

echo "==> Empacotando app e DMG"
"${ROOT_DIR}/frontend/node_modules/.bin/tauri" build --bundles app,dmg

APP_PATH="$(find "${ROOT_DIR}/src-tauri/target/release/bundle/macos" -maxdepth 1 -name 'RouteX.app' -print | head -n 1)"
DMG_PATH="$(find "${ROOT_DIR}/src-tauri/target/release/bundle/dmg" -maxdepth 1 -name '*.dmg' -print | head -n 1)"
RUNTIME_BUNDLE_PATH="${ROOT_DIR}/dist/runtime/routex-alpha-runtime.tar.gz"

if [ -z "${APP_PATH}" ] || [ ! -d "${APP_PATH}" ]; then
  echo "Bundle .app nao encontrado apos tauri build." >&2
  exit 1
fi

if [ -z "${DMG_PATH}" ] || [ ! -f "${DMG_PATH}" ]; then
  echo "Artifact .dmg nao encontrado apos tauri build." >&2
  exit 1
fi

cp -R "${APP_PATH}" "${ARTIFACT_DIR}/RouteX.app"
cp "${DMG_PATH}" "${ARTIFACT_DIR}/"
cp "${RUNTIME_BUNDLE_PATH}" "${ARTIFACT_DIR}/"

SUMMARY_PATH="${ARTIFACT_DIR}/build-summary.json"
ROOT_DIR="${ROOT_DIR}" VERSION="${VERSION}" APP_PATH="${APP_PATH}" DMG_PATH="${DMG_PATH}" RUNTIME_BUNDLE_PATH="${RUNTIME_BUNDLE_PATH}" SUMMARY_PATH="${SUMMARY_PATH}" python3 - <<'PY'
import json
import os
from pathlib import Path

summary = {
    "version": os.environ["VERSION"],
    "app_path": os.environ["APP_PATH"],
    "dmg_path": os.environ["DMG_PATH"],
    "runtime_bundle_path": os.environ["RUNTIME_BUNDLE_PATH"],
}
Path(os.environ["SUMMARY_PATH"]).write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

echo
echo "Artifacts alpha prontos em ${ARTIFACT_DIR}"
