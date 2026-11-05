#!/usr/bin/env bash
# Start, stop or inspect an engine defined in config/engines.toml.
# Usage: ./scripts/engine.sh start|stop|status [engine]
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" -m bench.engine "$@"
