#!/usr/bin/env bash
# Import a local GGUF into Ollama with a fixed context window.
# Usage: ./scripts/import-ollama.sh /path/to/Qwen3.8-27B-UD-Q3_K_XL.gguf [name]
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ $# -lt 1 ]]; then
  echo "usage: $0 /path/to/model.gguf [name]" >&2
  exit 2
fi

GGUF="$1"
NAME="${2:-qwen3.8-27b-q3kxl}"

if [[ ! -f "$GGUF" ]]; then
  echo "error: GGUF not found: $GGUF" >&2
  exit 1
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "error: ollama is not installed" >&2
  exit 1
fi

mkdir -p .run
MODELFILE=".run/Modelfile.$NAME"
cat >"$MODELFILE" <<EOF
FROM $GGUF
PARAMETER num_ctx 32768
PARAMETER temperature 0
EOF

echo "Modelfile: $MODELFILE"
ollama create "$NAME" -f "$MODELFILE"
echo
echo "Created $NAME. Benchmark it with:"
echo "  ./scripts/run-pass.sh ollama-q3kxl"
