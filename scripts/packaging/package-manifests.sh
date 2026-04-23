#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="${ROOT_DIR}/tooling/artifacts"
ARCHIVE_PATH="${ARTIFACT_DIR}/routex-operational-baseline.tar.gz"

mkdir -p "${ARTIFACT_DIR}"

tar -czf "${ARCHIVE_PATH}" \
  -C "${ROOT_DIR}" \
  README.md CHANGELOG.md ROADMAP.md CONTRIBUTING.md Makefile LICENSE \
  configs docs examples scripts tests tooling .github

echo "Created ${ARCHIVE_PATH}"
