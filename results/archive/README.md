# Archive

Historical and exploratory data. Nothing here is part of the current headline
comparison.

| Path | Contents |
|---|---|
| `*.legacy.json` | Raw schema-0 results from the original `jarvis/bench-llm` harness |
| `*.legacy.schema1.json` | Schema-1 imports of those raw files |
| `runs/` | Exploratory suite-v1..v4 runs used while fixing the cache case |
| `2026-11-05-mirai-server.log` | Mirai server log from the legacy run |

The clean comparison is in `results/2026-11-05-splash.json` and
`results/2026-11-05-mirai.json` (suite revision 5).

Hostnames were replaced with `mac-mini-m6` before publication; no other
measurement fields were changed.

The legacy Mirai cache case is invalid: the cold turn was truncated by
`max_tokens`, so the server reprefilled the prefix. The import retains the raw
35.0 s value as `reported_cached_ttft_long_ms` and excludes it from the
summary. Suite v5 fixes the sequence and validates on both engines.
