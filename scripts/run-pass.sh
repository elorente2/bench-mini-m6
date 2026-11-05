#!/usr/bin/env bash
# Run one benchmark pass against an already running engine.
# Usage: ./scripts/run-pass.sh splash|mirai|ollama-q3kxl|ollama-default [options]
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" -m bench.cli run "$@"
