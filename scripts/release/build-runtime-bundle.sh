#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist/runtime"
STAGE_DIR="${DIST_DIR}/stage"
ARCHIVE_PATH="${DIST_DIR}/routex-alpha-runtime.tar.gz"
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

rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/backend" "${STAGE_DIR}/scripts" "${STAGE_DIR}/.routex"

rsync -a --delete \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude '.venv' \
  "${ROOT_DIR}/backend/src" \
  "${STAGE_DIR}/backend/"

cp "${ROOT_DIR}/backend/pyproject.toml" "${STAGE_DIR}/backend/pyproject.toml"
cp "${ROOT_DIR}/backend/uv.lock" "${STAGE_DIR}/backend/uv.lock"
rsync -a --delete "${ROOT_DIR}/configs" "${STAGE_DIR}/"
rsync -a --delete "${ROOT_DIR}/examples" "${STAGE_DIR}/"
rsync -a --delete "${ROOT_DIR}/scripts/runtime" "${STAGE_DIR}/scripts/"
if [ -d "${ROOT_DIR}/.routex" ]; then
  rsync -a --delete "${ROOT_DIR}/.routex/" "${STAGE_DIR}/.routex/"
fi

printf '%s\n' "${VERSION}" > "${STAGE_DIR}/ROUTEX_RUNTIME_VERSION"

mkdir -p "${DIST_DIR}"
tar -czf "${ARCHIVE_PATH}" -C "${STAGE_DIR}" .

echo "RouteX alpha runtime bundle criado em ${ARCHIVE_PATH}"
