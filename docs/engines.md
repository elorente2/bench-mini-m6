# Engines

The harness only needs an OpenAI-compatible `/v1/models` and
`/v1/chat/completions` endpoint with streaming. Lifecycle commands are defined
in `config/engines.toml`; the documentation below explains what was used for the
November 2026 result set.

| Label | Engine | Port | Start command |
|---|---|---:|---|
| `splash` | Splash 1.5.0 | 8000 | `splash serve --model unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL --port 8000` |
| `mirai` | Mirai/uzu 0.6.17 | 8000 | `mirai server --model qwen3.8:27b --port 8000` |
| `ollama-q3kxl` | Ollama 0.40.14 | 11434 | `ollama serve` + imported GGUF |
| `ollama-default` | Ollama 0.40.14 | 11434 | `ollama serve` + native tag |
| `omlx` | oMLX 0.7.3 | 8000 | `omlx serve --port 8000 --headless` |

`omlx` is configured but has **no committed result yet**. Do not quote numbers
for it until a file exists in `results/`.

## Splash 1.5.0

Install the Splash CLI so `splash --version` prints `Splash 1.5.0`. The Homebrew
installation on the test machine lives at `/opt/homebrew/bin/splash`; if your
installation method differs, use the upstream installer and keep the command in
`config/engines.toml` in sync.

```bash
splash --version
splash serve --model unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL --port 8000
```

The first launch downloads the GGUF and the DFlash2 draft. The model is
reported as `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL`; the weights are Q3_K_XL
(~3-bit, about 13.1 GB) plus a draft of about 3.8 GB.

- Context: 217,081 tokens reported by `/v1/models`.
- Multimodal: accepts images and PDFs. Do not pass `--language-only` if you
  want to keep that capability.
- Reasoning: the benchmark sends `reasoning_effort: none`.
- API: `http://127.0.0.1:8000/v1`.

Useful flags if memory is tight: `--max-memory 28G`, `--max-context 100K`.
Changing them changes the comparison; record it if you do.

## Mirai / uzu 0.6.17

Install Mirai/uzu so `mirai --version` prints `cli 0.6.17`. The model alias
used by the test machine is `qwen3.8:27b`; `mirai list-models` shows the
available local aliases.

```bash
mirai --version
mirai list-models
mirai server --model qwen3.8:27b --port 8000
```

The server reports the model as
`alibaba:qwen3.8:27b:mirai:mirai-m:4`. The weights are a 4-bit M model (about
14.5 GB) plus a speculator of about 1.1 GB. Prefix cache is enabled by default
and the benchmark sends `reasoning_effort: disabled`.

- Context: Mirai does not report a context window through `/v1/models`. The
  benchmark only exercised 18K tokens.
- Multimodal: the M model is text-only.
- API: `http://127.0.0.1:8000/v1`.
- Prefix cache: enabled by default; `--no-prefix-cache` is available for
  debugging, not for the benchmark. The previous turn must finish naturally
  (`finish=stop`); a turn truncated by `max_tokens` leaves the cache
  non-extensible. The suite's cold task answers `READY` so the extension can
  hit.

## Ollama 0.40.14

Ollama is treated as a persistent service. Start it once and let both Ollama
labels use it:

```bash
ollama --version
ollama serve
ollama list
ollama ps
```

The two labels are different in practice:

| Label | Tag | Weights | Runner | Context |
|---|---|---|---|---|
| `ollama-q3kxl` | `qwen3.8-27b-q3kxl` | Q3_K_XL GGUF; Ollama reports Q3_K_L | llama.cpp (`llama-server`) | 32768 |
| `ollama-default` | `qwen3.8:27b` | nvfp4, 27.8B | MLX (`ollama runner`) | 32768 |

The native tag advertises vision, tools and thinking. Thinking defaults to
`medium`; see the reasoning note below.

The OpenAI-compatible endpoint is `http://127.0.0.1:11434/v1`.

Both labels send `reasoning_effort: none`. The native tag defaults to thinking
level `medium` and the OpenAI endpoint ignores the Ollama-specific
`think: false` field; `reasoning_effort: none` is what actually disables it.

`ollama ps` reports the context in use. The 2026-11-05 test used 32768 tokens
for both labels: the imported Modelfile sets it explicitly, and the native tag
defaulted to 32768.

### Native tag

```bash
ollama pull qwen3.8:27b
```

Tag availability changes over time; if the native tag is not published, use
the exact tag shown by `ollama list` and update `config/engines.toml`.

### Same weights as Splash

The imported label isolates the engine from the weights:

```bash
./scripts/import-ollama.sh /path/to/Qwen3.8-27B-UD-Q3_K_XL.gguf
# equivalent to:
# ollama create qwen3.8-27b-q3kxl -f config/ollama/Modelfile.example
```

The helper writes a temporary Modelfile with `num_ctx 32768` and
`temperature 0`, then runs `ollama create`. The imported model is named
`qwen3.8-27b-q3kxl`.

If you need to download the GGUF first:

```bash
# huggingface_hub CLI; install with: pip install huggingface_hub
hf download unsloth/Qwen3.8-27B-GGUF --include "*UD-Q3_K_XL*"
```

### Stopping Ollama safely

If Ollama is managed by Homebrew:

```bash
brew services stop ollama
```

If you started `ollama serve` manually:

```bash
pkill -f 'ollama serve'
```

The harness can stop an Ollama process it started itself, but it refuses to
force-kill a service it does not own unless you pass `--force`:

```bash
./scripts/engine.sh stop ollama-default --force
```

Before a Splash or Mirai pass, confirm no Ollama model is resident:

```bash
ollama ps
# if a model is listed:
ollama stop <model>
```

## oMLX 0.7.3

oMLX is an MLX inference server with continuous batching and a two-tier KV
cache (RAM plus SSD). It is the only contender that runs MLX safetensors
natively instead of GGUF, so it enters the comparison as a **speed and memory**
contender with its own weights, exactly like Mirai does.

Install the CLI so the server is owned by the harness. The macOS app manages
its own server, which the harness cannot stop deterministically.

```bash
brew tap jundot/omlx https://github.com/jundot/omlx
brew install jundot/omlx/omlx --with-custom-kernel   # needs full Xcode
omlx --version
omlx serve --port 8000 --headless
```

Models are discovered from subdirectories of `--model-dir` (default
`~/.omlx/models`). The served id is the directory name, so the configured id
`Qwen3.8-27B-4bit` must match a directory with that exact name:

```bash
hf download mlx-community/Qwen3.8-27B-4bit \
  --local-dir ~/.omlx/models/Qwen3.8-27B-4bit
```

```
~/.omlx/models/Qwen3.8-27B-4bit/{config.json,*.safetensors,tokenizer*}
```

That checkpoint is a 4-bit affine (group 64) build, 16.1 GB in three shards,
with no MTP draft — Splash and Mirai both run a draft or speculator, so decode
for oMLX starts from a different baseline. Its `model_type` is `qwen3_5`, which
means the `qwen35_*` kernel patches are the ones that apply to it.

- Context: oMLX reports the model's real context window through `/v1/models`,
  so the result records `context_source: "api"` rather than a config value.
- Weights: 16.1 GB of safetensors, confirmed with `du -sh` on the downloaded
  directory before the result is committed. Do not compare this run against
  Q3_K_XL as a quality result (fairness rule 15).
- Reasoning: **use `chat_template_kwargs`.** oMLX forwards `reasoning_effort`
  into the model chat template and its compatibility layer can downgrade
  `none` to a lower level that still emits `reasoning_content`. The configured
  engine therefore sends `chat_template_kwargs = { enable_thinking = false }`,
  and the client never strips that field on rejection: if oMLX refuses it the
  pass fails instead of silently benchmarking a thinking model.
- Gate: every run in the result must report `reasoning_chunks: 0`. A run with
  reasoning tokens is invalid under fairness rule 6, not a slow outlier.
- Startup flags that change the measurement (`--memory-guard`,
  `--memory-guard-gb`, `--hot-cache-max-size`, `--paged-ssd-cache-dir`,
  `--max-concurrent-requests`) must be recorded in the result notes if used.
  The defaults are the comparison.
- Cache case: the SSD tier is off unless `--paged-ssd-cache-dir` is set. Leave
  it off for the first pass; a pass with the SSD tier on is a different
  contender and needs its own label and result file.

### Native kernels: use the official wheel

This machine has no full Xcode (`xcrun --find metal` fails), so
`brew install jundot/omlx/omlx --with-custom-kernel` cannot build the native
kernels here. That is not a footnote: the 4-bit checkpoint above reports
`model_type: qwen3_5`, and the patches that touch native kernels for that
architecture are `qwen35_fa256_attention`, `qwen35_gdn_chunked`,
`qwen35_q4_mlp`, `qwen35_oq_a8` and `qwen35_verify_qmm`. Each one checks
`has_symbol(...)` and silently falls back to stock MLX when the build is
missing, which upstream describes as "much slower and more memory" — exactly
the prefill and long-context decode cases this repository measures.

The release publishes wheels with the kernels **already compiled**:

```bash
python3.11 -m venv ~/.venvs/omlx
~/.venvs/omlx/bin/pip install \
  https://github.com/jundot/omlx/releases/download/v0.7.3/omlx-0.7.3-cp311-cp311-macosx_15_0_universal2.whl
~/.venvs/omlx/bin/python -c "from omlx.custom_kernels import native_kernel_status; print(native_kernel_status())"
```

All four packages must report `available: true` (`attention`, `lowbit`,
`quant_matmul`, `sparse_index`). If any is false, the pass is the generic MLX
path: record that in the result notes and do not compare it to Splash as if the
kernels were present.

The Homebrew formula installs **without** kernels and is only useful as an `hf`
CLI. Point `~/.local/bin/omlx` at the venv that has the wheel, so `PATH`
resolves to the kernel build:

```bash
ln -sf ~/.venvs/omlx/bin/omlx ~/.local/bin/omlx
omlx --version
```

**Do not `brew uninstall omlx` while the venv is your only oMLX.** Homebrew
installed `python@3.11` as a dependency of the formula, so removing the formula
removes the interpreter the venv points at (`~/.venvs/omlx/bin/python3.11` is a
symlink into `/opt/homebrew/opt/python@3.11`) and every venv binary dies with
`bad interpreter`. The venv stays broken until `brew install python@3.11`
restores the same interpreter; the packages in `site-packages` are untouched.
If the Homebrew copy has to go, reinstall the interpreter in the same command
and check `omlx --version` afterwards.

**Disable the memory guard for a single-model benchmark.** `omlx serve` starts
a process enforcer whose `balanced` tier ceilings the process at roughly 14.6 GB
on a 32 GB machine, below the 16.1 GB of the 4-bit weights, so it evicts the
model in the middle of a run. `config/engines.toml` starts oMLX with
`--memory-guard off`; the harness already enforces one model-loaded engine at a
time.

### Do not benchmark a GGUF through oMLX

oMLX lists `.gguf` files but runs them on Splash's engine as an external
process ([docs/Splash.md](https://github.com/jundot/omlx/blob/main/docs/Splash.md)).
A pass that reports a `.gguf` model id measured Splash with a different HTTP
layer, not oMLX. Keep the GGUF out of `--model-dir`, or label the result as a
Splash run.

## One engine at a time

| Measuring | Must be stopped |
|---|---|
| `splash` | Mirai, oMLX, any loaded Ollama model |
| `mirai` | Splash, oMLX, any loaded Ollama model |
| `omlx` | Splash, Mirai, any loaded Ollama model |
| `ollama-*` | Splash, Mirai, oMLX |

The harness checks process patterns, the port listener and (for Splash/Mirai)
`ollama ps`. See `docs/fairness-rules.md`.

## Version capture

Every result stores the first line of the engine's `version_cmd`:

```bash
splash --version   # Splash 1.5.0
mirai --version    # cli 0.6.17
ollama --version   # ollama version is 0.40.14
```

If you upgrade an engine, run a new pass. Do not compare results from different
engine versions as if they were the same contender.
