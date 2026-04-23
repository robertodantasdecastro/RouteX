#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRE_COMMIT_CONFIG="${ROOT_DIR}/tooling/pre-commit/pre-commit-config.yaml"
PRE_COMMIT_BIN="${ROOT_DIR}/tooling/.venv/bin/pre-commit"

if ! git -C "${ROOT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Skipping hook installation because this directory is not a git worktree yet."
  exit 0
fi

if [ ! -x "${PRE_COMMIT_BIN}" ]; then
  echo "pre-commit is not installed. Run 'make bootstrap' first." >&2
  exit 1
fi

"${PRE_COMMIT_BIN}" install --install-hooks --config "${PRE_COMMIT_CONFIG}"
echo "pre-commit hooks installed using ${PRE_COMMIT_CONFIG}."
