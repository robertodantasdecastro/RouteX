#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_MODEL="${ROUTEX_LOCAL_MODEL_ALIAS:-qwen2.5-coder:latest}"
DEFAULT_PROMPT="${ROUTEX_SMOKE_PROMPT:-Respond only with ROUTEX_LOCAL_OK}"
DEFAULT_PROFILE="${ROUTEX_SMOKE_PROFILE:-private-mode}"

if [ "$#" -eq 0 ]; then
  set -- chat --model "${DEFAULT_MODEL}" --prompt "${DEFAULT_PROMPT}" --profile "${DEFAULT_PROFILE}"
fi

uv run --project "${ROOT_DIR}/backend" --extra ops \
  python "${ROOT_DIR}/scripts/dev/routex_openai_client.py" "$@"
