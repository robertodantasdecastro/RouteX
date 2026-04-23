#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

"${ROOT_DIR}/scripts/dev/validate-configs.sh"
"${ROOT_DIR}/scripts/dev/run-tests.sh"
