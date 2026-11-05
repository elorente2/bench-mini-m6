# local-llm-bench

Reproducible benchmark for OpenAI-compatible local LLM engines on Apple
Silicon macOS. One engine loaded at a time, the same prompt suite for every
contender, raw JSON for every run.

Current test: **Qwen3.8-27B** on a **Mac mini M6, 32 GB**, comparing
**Splash 1.5.0**, **Mirai/uzu 0.6.17** and **Ollama 0.40.14**.

## Results — 2026-11-05

| Metric | Splash | Mirai/uzu | Edge |
|---|---:|---:|---|
| Short decode | 56.3 tok/s | **60.8 tok/s** | uzu +8% |
| Decode @ 18K context | **44.8 tok/s** | 39.6 tok/s | Splash +13% |
| Prefill @ 18K | 440.7 tok/s | **530.7 tok/s** | uzu +20% |
| Cold TTFT @ 18K | 41.0 s | **34.1 s** | uzu |
| Cached TTFT (prefix extension) | 463 ms | **250 ms** | uzu |
| Peak wired memory | 21.64 GB | **19.63 GB** | uzu |
| Peak engine RSS | **2,596 MB** | 15,474 MB | informational[^rss] |
| Quantization | Q3_K_XL (~3-bit) | 4-bit | uzu |
| Context window (reported) | **217,081** | not reported | Splash |

Clean suite v5: both cache cases validate. The two engines were measured
back-to-back on the same machine; the cold turn finishes naturally so Mirai's
prefix cache can extend it.

[^rss]: On macOS, Metal allocations are wired rather than counted in ordinary
    process RSS. Peak wired memory is the meaningful memory figure here.

### Verdict

- **Text and code agents:** Mirai/uzu is still the better default. It wins 4 of
  5 comparable speed metrics (short decode, prefill, cold TTFT, cached TTFT),
  uses less wired memory and runs a 4-bit model instead of Q3_K_XL.
- **Long-context decode:** Splash was 13% faster in this pass (44.8 vs
  39.6 tok/s). The earlier legacy suite had the opposite result, so treat this
  single-repetition metric as prompt- and thermal-sensitive rather than a
  stable win.
- **Vision, PDF or verified context beyond 100K:** Splash. It accepts images
  and PDFs and reports a 217,081-token window. Mirai's M model is text-only and
  does not report a context window.
- **Ollama:** not measured yet. Two labels are configured: the same Q3_K_XL
  GGUF imported into Ollama, and Ollama's native tag.

These results compare **engine speed and memory**, not output quality. Splash
runs a GGUF Q3_K_XL while Mirai runs a 4-bit M model, so the weights are not
identical. See `docs/methodology.md` and `docs/fairness-rules.md`.

The generated report is in [`reports/latest.md`](reports/latest.md) and the
detailed analysis in [`docs/results/2026-11-m6.md`](docs/results/2026-11-m6.md).

## Contenders

| Label | Engine | Weights | Port | Reasoning |
|---|---|---|---:|---|
| `splash` | Splash 1.5.0 | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` (13.1 GB) + DFlash2 draft (3.8 GB) | 8000 | `reasoning_effort: none` |
| `mirai` | Mirai/uzu 0.6.17 | `alibaba:qwen3.8:27b:mirai:mirai-m:4` (14.5 GB) + speculator (1.1 GB) | 8000 | `reasoning_effort: disabled` |
| `ollama-q3kxl` | Ollama 0.40.14 | same Q3_K_XL GGUF imported with a 32K context | 11434 | not sent |
| `ollama-default` | Ollama 0.40.14 | native `qwen3.8:27b` tag | 11434 | not sent |

## Quick start

Requirements: Apple Silicon Mac, macOS, Python 3.11+, and the engines you want
to compare. A 32 GB machine cannot hold two 27B engines at once.

```bash
git clone https://github.com/Elorente2/local-llm-bench.git
cd local-llm-bench
./scripts/bootstrap.sh
```

`bootstrap.sh` creates `.venv`, installs the dev tools and prints the engine
versions it finds. `make` uses `.venv/bin/python` automatically.

Run one engine at a time:

```bash
./scripts/engine.sh start splash
./scripts/run-pass.sh splash
./scripts/engine.sh stop splash
```

Or let the harness cycle through every configured engine:

```bash
make run-all
```

`run-all` stops non-persistent engines for a clean load, measures them
sequentially, leaves Ollama running, and writes `reports/latest.md`. It fails
fast if a model is missing; use `--continue-on-error` to measure what is
installed.

Regenerate the report from existing results:

```bash
make report
```

## What is measured

| Case | Prompt | Output | Repetitions |
|---|---|---:|---:|
| `decode_short` | short coding task | 256 tokens | 3 (median) |
| `prefill_cold_long` | ~32K chars (~18K tokens) user prefix, answer `READY` | up to 64 tokens | 1 |
| `cached_ttft_long` | same prefix + fixed assistant turn + follow-up | 128 tokens | 1 |

Metrics:

- **Short decode:** generated tokens per second on a warm, short prompt.
- **Decode @ long context:** tokens per second while the 18K prefix is loaded.
  Measured in the cached extension run.
- **Prefill @ long context:** `prompt_tokens / TTFT` on a cold long request.
- **Cold TTFT:** time to first token for the cold 18K request. The cold turn
  must finish naturally (`finish=stop`); a truncated turn breaks prefix-cache
  extension on some engines.
- **Cached TTFT:** TTFT when a request extends an identical prefix. The run is
  marked `invalid` unless the prefix is actually reused.
- **Peak engine RSS:** sum of matching process RSS, sampled every 0.5 s.
- **Peak wired memory:** `vm_stat` wired pages, sampled every 0.5 s. This is the
  figure that matters for Metal-backed engines.
- **Context window:** value reported by the engine API, not a verified result.

## Repository layout

```text
bench/                 benchmark client, runner, validation and report
config/                engines, models and suite definitions
docs/                  methodology, fairness rules, engine setup, results
results/               versioned JSON results and raw legacy archives
reports/               generated Markdown reports
scripts/               bootstrap, engine lifecycle, one-pass and run-all
tests/                 unit tests for config, prompts, validation and report
```

Useful commands:

```bash
./scripts/engine.sh status
./scripts/engine.sh start mirai
./scripts/run-pass.sh mirai --reps 5 --decode-tokens 512
.venv/bin/python -m bench.cli engines
.venv/bin/python -m bench.cli compare results/*.json
.venv/bin/python -m bench.cli validate results/2026-11-05-mirai.json
make check
```

## Adding an engine

1. Add an `[engines.<label>]` table to `config/engines.toml` with its port,
   model, process pattern, start command and conflicts.
2. Add its model metadata to `config/models.toml`.
3. Document installation and model download in `docs/engines.md`.
4. Run a pass and commit the JSON in `results/` plus the regenerated report.
5. Add a test if the engine needs a new compatibility fallback.

The benchmark only needs an OpenAI-compatible `/v1/models` and
`/v1/chat/completions` streaming endpoint.

## Results and provenance

`results/2026-11-05-splash.json` and `results/2026-11-05-mirai.json` are clean
suite-v5 runs measured back-to-back on the test machine. Both cache cases
validate.

The original `jarvis/bench-llm` results are preserved in `results/archive/`:
the raw schema-0 files, their normalized schema-1 imports, the exploratory
suite-v1..v4 runs, and the Mirai server log. The legacy Mirai cache case is
invalid there because the truncated cold turn made the server reprefill; the
reported 35.0 s is retained under `reported_cached_ttft_long_ms` for
transparency but excluded from that legacy summary. The clean v5 run supersedes
it.

Historical result files are immutable. Add a new dated file instead of editing
an old one.

## License

MIT. See [LICENSE](LICENSE).
