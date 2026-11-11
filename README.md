# local-llm-bench

Reproducible benchmark for OpenAI-compatible local LLM engines on Apple
Silicon macOS. One engine loaded at a time, the same prompt suite for every
contender, raw JSON for every run.

Current test: **Qwen3.8-27B** on a **Mac mini M6, 32 GB**, comparing
**Splash 1.5.0**, **Mirai/uzu 0.6.17**, **oMLX 0.7.3** and two
**Ollama 0.40.14** labels: the same Q3_K_XL GGUF imported into Ollama and the
native `qwen3.8:27b` tag.

## Results — November 2026

| Metric | Splash | Mirai/uzu | oMLX | Ollama Q3_K_XL | Ollama native |
|---|---:|---:|---:|---:|---:|
| Short decode | 56.3 tok/s | **60.8 tok/s** | 9.2 tok/s | 11.0 tok/s | 30.6 tok/s |
| Decode @ 18K context | **44.8 tok/s** | 39.6 tok/s | 8.1 tok/s | 9.6 tok/s | 20.1 tok/s |
| Prefill @ 18K | 440.7 tok/s | **530.7 tok/s** | 200.4 tok/s | 212.2 tok/s | 271.6 tok/s |
| Cold TTFT @ 18K | 41.0 s | **34.1 s** | 90.3 s | 85.3 s | 66.6 s |
| Cached TTFT (prefix extension) | 463 ms | **250 ms** | 1.5 s | 830 ms | 510 ms |
| Peak wired memory | 21.64 GB | 19.63 GB | 23.62 GB | **16.16 GB** | 24.85 GB |
| Peak engine RSS[^rss] | **2,596 MB** | 15,474 MB | 9,500 MB | 14,832 MB | 11,526 MB |
| Quantization | Q3_K_XL (~3-bit) | 4-bit | 4-bit MLX | Q3_K_XL (~3-bit) | nvfp4 |
| Speculative decoding | yes | yes | **no** | no | no |
| Context window (API/config) | 217,081 | not reported | **262,144** | 32,768 | 32,768 |

Splash and Mirai are clean suite-v5 runs from 2026-11-05; both Ollama labels
are clean suite-v5 runs from 2026-11-06 with 32K context and thinking disabled.
oMLX is a clean suite-v5 run from 2026-11-11 on 4-bit MLX weights.

oMLX decodes at ~9 tok/s because it has no draft model: without speculation the
27B has to read its 16 GB of weights for every token, which is what the memory
bandwidth allows. Splash and Mirai generate 6–8 tokens per pass with a
speculator and that is where their 6× advantage comes from. The comparison is
still valid — it is engine speed with the features each engine ships — but do
not read it as "MLX is slow". `--hot-cache-max-size` made no measurable
difference and everything else is stock.

[^rss]: On macOS, Metal allocations are wired rather than counted in ordinary
    process RSS. Peak wired memory is the meaningful memory figure here.

### Verdict

- **Text and code agents:** Mirai/uzu is the best default. It wins 4 of 5
  comparable speed metrics (short decode, prefill, cold TTFT, cached TTFT),
  uses less wired memory than Splash, and runs a 4-bit model instead of Q3_K_XL.
- **Long-context decode:** Splash was 13% faster in this pass (44.8 vs
  39.6 tok/s). The earlier legacy suite had the opposite result, so treat this
  single-repetition metric as prompt- and thermal-sensitive rather than a
  stable win.
- **Ollama native (`qwen3.8:27b`, nvfp4):** 30.6 tok/s short decode, 20.1 tok/s
  at 18K, 66.6 s cold TTFT and 24.85 GB peak wired. It is roughly 2x faster
  than the imported Q3_K_XL label but still well behind Splash and Mirai, and
  it is the heaviest contender in wired memory. It advertises vision and tools,
  but those were not tested here.
- **Ollama imported Q3_K_XL:** same weights as Splash, but 11.0 tok/s short
  decode and an 85.3 s cold TTFT. This is the clearest engine-implementation
  gap in the set: identical Q3_K_XL weights run about 5x faster under Splash.
  It does have the lowest peak wired memory (16.16 GB), at a large speed cost.
- **Vision, PDF or verified context beyond 100K:** Splash. It accepts images
  and PDFs and reports a 217,081-token window. Mirai's M model is text-only and
  does not report a context window; Ollama was tested at 32K.
- **Ollama integration:** use the native tag if you need Ollama specifically.
  Do not use the imported Q3_K_XL label for speed on this hardware.

These results compare **engine speed and memory**, not output quality. Splash
runs a GGUF Q3_K_XL while Mirai runs a 4-bit M model, so the weights are not
identical. Accuracy is a separate axis: `bench eval` measures each model with
its own weights, temperature 0 and code-only graders, and writes the decision
table to [`reports/eval-latest.md`](reports/eval-latest.md). Vision has its own
suite, its own generated fixtures and its own table in
[`reports/vision-latest.md`](reports/vision-latest.md). See
`docs/methodology.md`, `docs/fairness-rules.md` and `docs/eval.md`.

The generated report is in [`reports/latest.md`](reports/latest.md) and the
detailed analysis in [`docs/results/2026-11-m6.md`](docs/results/2026-11-m6.md).

## Contenders

| Label | Engine | Weights | Port | Reasoning |
|---|---|---|---:|---|
| `splash` | Splash 1.5.0 | `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL` (13.1 GB) + DFlash2 draft (3.8 GB) | 8000 | `reasoning_effort: none` |
| `mirai` | Mirai/uzu 0.6.17 | `alibaba:qwen3.8:27b:mirai:mirai-m:4` (14.5 GB) + speculator (1.1 GB) | 8000 | `reasoning_effort: disabled` |
| `ollama-q3kxl` | Ollama 0.40.14 | same Q3_K_XL GGUF imported with a 32K context | 11434 | `reasoning_effort: none` |
| `ollama-default` | Ollama 0.40.14 | native `qwen3.8:27b` tag (nvfp4), 32K context | 11434 | `reasoning_effort: none` |

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
suite-v5 runs measured back-to-back on the test machine. The Ollama results are
`results/2026-11-06-ollama-q3kxl.json` and
`results/2026-11-06-ollama-default.json`, also suite v5, with 32K context and
thinking disabled. All four cache cases validate.

The original `jarvis/bench-llm` results are preserved in `results/archive/`:
the raw schema-0 files, their normalized schema-1 imports, the exploratory
suite-v1..v4 runs, and the Mirai server log. The legacy Mirai cache case is
invalid there because the truncated cold turn made the server reprefill; the
reported 35.0 s is retained under `reported_cached_ttft_long_ms` for
transparency but excluded from that legacy summary. The clean v5 runs supersede
it.

Historical result files are immutable. Add a new dated file instead of editing
an old one.

## License

MIT. See [LICENSE](LICENSE).
