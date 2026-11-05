# Reproducing the benchmark from scratch

This is the full path from a clean checkout to a report. Commands assume the
repository root and an Apple Silicon Mac.

## 0. Prerequisites

- macOS on Apple Silicon, 32 GB or more for a 27B model.
- Python 3.11+.
- Splash, Mirai/uzu and Ollama installed if you want all three contenders.
- Enough disk for the model files (tens of GB).
- The Mac plugged in, awake and not running heavy background work.

## 1. Bootstrap

```bash
git clone https://github.com/Elorente2/local-llm-bench.git
cd local-llm-bench
./scripts/bootstrap.sh
```

This creates `.venv`, installs the dev tools and prints the engines it finds.
`make` uses `.venv/bin/python` automatically.

```bash
make check
./scripts/engine.sh status
```

## 2. Install and download the models

Follow [`engines.md`](engines.md). At minimum:

```bash
splash --version
mirai --version
ollama --version
mirai list-models
ollama list
```

Splash downloads its GGUF and draft on first `serve`. Mirai resolves the
`qwen3.8:27b` alias. Ollama needs both labels:

```bash
# native tag, ~18 GB
ollama pull qwen3.8:27b

# same Q3_K_XL GGUF as Splash, ~12 GB; sets num_ctx 32768
./scripts/import-ollama.sh /path/to/Qwen3.8-27B-UD-Q3_K_XL.gguf
```

The native tag uses 32768 context by default on this machine; the imported
Modelfile sets it explicitly. Both send `reasoning_effort: none` to disable the
native thinking mode.

## 3. Verify a clean baseline

```bash
./scripts/engine.sh status
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:11434 -sTCP:LISTEN
pgrep -lf 'splash|mirai|ollama'
ollama ps
```

At most one listener should be on port 8000. Ollama on 11434 may be running,
but `ollama ps` must be empty before a Splash or Mirai pass.

## 4. Splash pass

The harness can start and stop it:

```bash
./scripts/engine.sh start splash
./scripts/run-pass.sh splash
./scripts/engine.sh stop splash
```

Or manually, in two terminals:

```bash
# terminal 1
splash serve --model unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL --port 8000

# terminal 2, once /v1/models responds
./scripts/run-pass.sh splash
```

The result is written to `results/YYYY-MM-DD-splash.json`. The pass includes a
warmup, three short decodes, a cold long prefill, a cached extension and a long
decode. Expect the cold 18K prefill to take tens of seconds on this class of
machine.

## 5. Mirai/uzu pass

```bash
./scripts/engine.sh stop splash
./scripts/engine.sh start mirai
./scripts/run-pass.sh mirai
./scripts/engine.sh stop mirai
```

The safety check refuses to run while Splash is alive. If Splash was started
manually and the harness has no PID file, stop it yourself or use:

```bash
./scripts/engine.sh stop splash --force
```

## 6. Ollama passes

Keep Ollama running and measure both labels:

```bash
./scripts/engine.sh start ollama-q3kxl
./scripts/run-pass.sh ollama-q3kxl
./scripts/run-pass.sh ollama-default
```

The first `start` launches `ollama serve`; the second label reuses it. Stop
Splash and Mirai first. Unload the previous Ollama model between labels so only
one 27B model is resident at a time:

```bash
./scripts/engine.sh start ollama-q3kxl
./scripts/run-pass.sh ollama-q3kxl
ollama stop qwen3.8-27b-q3kxl
./scripts/run-pass.sh ollama-default
```

Both Ollama labels use a 32K context and `reasoning_effort: none`. The native
tag's OpenAI endpoint ignores `think: false`; `reasoning_effort: none` is what
actually disables thinking.

If a native tag is missing, the pass fails with a clear "model not found"
message. Pull the tag or change `config/engines.toml`; do not silently compare a
different model.

## 7. Generate the report

```bash
make report
# equivalent:
.venv/bin/python -m bench.cli report results/*.json --out reports/latest.md
```

Open `reports/latest.md`. The report marks the best value per row, lists invalid
cases and gives a text/code and memory verdict.

## 8. One-command run

Once every engine and model is installed:

```bash
make run-all
```

`run-all` stops non-persistent engines for a clean load, measures them in order
(`splash`, `mirai`, `ollama-q3kxl`, `ollama-default`), leaves Ollama running and
writes `reports/latest.md`. Use `--continue-on-error` to measure what is
installed when one model is missing.

To measure a subset:

```bash
.venv/bin/python -m bench.cli run-all --engines splash,mirai --report
```

## 9. Verifying the cache case

Suite v5 makes the cold turn finish naturally (`finish=stop`) and extends the
exact prefix with a fixed assistant turn and a follow-up. All four engines in
the November 2026 result set now validate. To verify a new pass:

```bash
./scripts/engine.sh start mirai
./scripts/run-pass.sh mirai --out results/2026-11-06-mirai.json
./scripts/engine.sh stop mirai
.venv/bin/python -m bench.cli validate results/2026-11-06-mirai.json --strict
```

If the case is invalid, keep the JSON and document it. Do not hand-edit the
metric. The most common cause is a cold turn truncated by `max_tokens`, which
leaves Mirai's prefix cache in a non-extensible state; the legacy 35.0 s result
in `results/archive/` is exactly that failure.

## 10. Troubleshooting

| Symptom | Check |
|---|---|
| `ModuleNotFoundError: bench` | Run `./scripts/bootstrap.sh`; use `.venv/bin/python` or `make`. |
| `expected exactly one listener` | `lsof -nP -iTCP:8000 -sTCP:LISTEN` and stop the extra process. |
| `conflicting engine is alive` | `pgrep -lf 'splash|mirai'`; stop the other engine. |
| `Ollama has a model loaded` | `ollama ps`, then `ollama stop <model>`. |
| Model not found | `mirai list-models`, `ollama list`, or let Splash download first. |
| Request times out | Increase `--timeout`; cold 18K prefill can take ~35 s. |
| Reasoning field rejected | The client retries without `reasoning_effort` and logs it. |
| Memory pressure | Close other apps; check `memory_pressure`. |
| Different results after an upgrade | Run a new pass and record the new engine version. |

## 11. What to commit

- New `results/YYYY-MM-DD-<label>.json` files.
- The regenerated `reports/latest.md` and dated report.
- A short note in `docs/results/` if the verdict changes.

Never edit a historical result file and never commit model weights.
