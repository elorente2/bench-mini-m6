# Results

Every completed pass is a JSON file named `YYYY-MM-DD-<label>.json`. Files are
immutable: add a new dated file instead of editing an old one. The generated
Markdown lives in `reports/` and can be rebuilt at any time.

## Schema 1

```json
{
  "schema_version": 1,
  "label": "splash",
  "timestamp": "2026-11-05T20:34:27+00:00",
  "source": "bench",
  "engine": {
    "label": "splash",
    "name": "Splash",
    "version": "Splash 1.5.0",
    "base_url": "http://127.0.0.1:8000/v1",
    "port": 8000,
    "reasoning_effort": "none",
    "proc_pattern": "splash serve-native|server\\.server",
    "persistent": false
  },
  "model": {
    "id": "unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL",
    "configured_id": "unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL",
    "quantization": "Q3_K_XL (~3-bit)",
    "context": 217081,
    "context_source": "api"
  },
  "suite": {
    "revision": 5,
    "prefill_target_chars": 32000,
    "warmup_max_tokens": 8,
    "cases": []
  },
  "machine": {
    "host": "example.local",
    "os": "Darwin 27.2.0",
    "macos": "27.2",
    "model": "Mac18,5",
    "chip": "Apple M6",
    "memory_gb": 34.4,
    "python": "3.15.2"
  },
  "summary": {},
  "validation": {},
  "runs": []
}
```

### `summary`

| Field | Meaning |
|---|---|
| `decode_short_tps` | Median short-prompt decode, tok/s |
| `decode_at_long_tps` | Median decode with the long prefix loaded |
| `prefill_long_tps` | Median cold long-prompt prefill, tok/s |
| `cold_ttft_long_ms` | Median cold long-prompt TTFT |
| `cached_ttft_long_ms` | Cached extension TTFT, only if the case is valid |
| `reported_cached_ttft_long_ms` | Raw cached TTFT, kept when the case is invalid |
| `peak_engine_rss_mb` | Peak sum of matching process RSS |
| `wired_peak_gb` | Peak macOS wired memory |
| `invalid_cases` | Case names excluded from the summary |
| `valid_cases` | Case names included in the summary |
| `model`, `context`, `context_source` | Model and context metadata |

### `validation`

Each case has `{"valid": bool, "reasons": [str]}`. The cache case is valid only
if prompt tokens are not lost and cached TTFT is less than half of cold TTFT
(or under 1 s). See `docs/methodology.md`.

### `runs`

One object per request: `case`, `rep`, `ttft_ms`, `ttft_content_ms`,
`total_ms`, `prompt_tokens`, `completion_tokens`, `completion_tokens_source`,
`content_chunks`, `reasoning_chunks`, `decode_tps`, `prefill_tps`,
`finish_reason`, `answer_preview`, `answer_chars`, `answer_sha256`.

## Legacy imports

`results/archive/` keeps the original schema-0 files from `jarvis/bench-llm`
plus their schema-1 imports and the exploratory suite-v1..v4 runs. The
schema-0 files were converted with:

```bash
.venv/bin/python -m bench.cli import-legacy \
  results/archive/2026-11-05-mirai.legacy.json \
  --out results/archive/2026-11-05-mirai.legacy.schema1.json \
  --source jarvis/bench-llm/results/mirai.json
```

The importer preserves raw runs and recomputes cache validation. If a legacy
cache case is invalid, `cached_ttft_long_ms` becomes `null` and the raw value is
moved to `reported_cached_ttft_long_ms`.

## Validation commands

```bash
.venv/bin/python -m bench.cli validate results/2026-11-05-mirai.json
.venv/bin/python -m bench.cli validate results/2026-11-05-mirai.json --strict
.venv/bin/python -m bench.cli compare results/2026-11-05-splash.json results/2026-11-05-mirai.json
```
