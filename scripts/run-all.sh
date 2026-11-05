#!/usr/bin/env bash
# Start, measure and stop every engine sequentially, then write the report.
# Usage: ./scripts/run-all.sh [--continue-on-error] [--report]
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" -m bench.cli run-all --report "$@"
