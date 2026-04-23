#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHANGELOG_FILE="${ROOT_DIR}/CHANGELOG.md"

echo "# RouteX Release Draft"
echo
awk '
  /^## \[Unreleased\]/ { printing=1 }
  printing { print }
  /^## \[/ && $0 !~ /^## \[Unreleased\]/ && printing==1 { exit }
' "${CHANGELOG_FILE}"
