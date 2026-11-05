#!/usr/bin/env bash
# Create a local virtualenv and verify the tools needed by the benchmark.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "warning: this benchmark is tuned for macOS; measurements on other OSes are not comparable" >&2
fi

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "error: $PYTHON not found" >&2
  exit 1
fi

"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("error: Python 3.11 or newer is required")
print(f"python: {sys.version.split()[0]}")
PY

if [[ ! -x .venv/bin/python ]]; then
  echo "creating .venv"
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -e '.[dev]'

echo
echo "tools:"
for tool in splash mirai ollama lsof curl; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '  %-8s %s\n' "$tool" "$(command -v "$tool")"
  else
    printf '  %-8s missing\n' "$tool"
  fi
done

echo
echo "versions:"
splash --version 2>/dev/null | head -1 || true
mirai --version 2>/dev/null | head -1 || true
ollama --version 2>/dev/null | head -1 || true

cat <<'EOF'

Next steps:
  1. Read docs/engines.md and install/download the three engines.
  2. Run ./scripts/engine.sh status
  3. Run ./scripts/run-pass.sh splash   (or mirai, ollama-q3kxl, ollama-default)
  4. Run make report

Never run two model-loaded engines at the same time on a 32 GB machine.
EOF
