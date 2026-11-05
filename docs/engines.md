# Engines

The harness only needs an OpenAI-compatible `/v1/models` and
`/v1/chat/completions` endpoint with streaming. Lifecycle commands are defined
in `config/engines.toml`; the documentation below explains what was used for the
2026-11-05 result set.

| Label | Engine | Port | Start command |
|---|---|---:|---|
| `splash` | Splash 1.5.0 | 8000 | `splash serve --model unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL --port 8000` |
| `mirai` | Mirai/uzu 0.6.17 | 8000 | `mirai server --model qwen3.8:27b --port 8000` |
| `ollama-q3kxl` | Ollama 0.40.14 | 11434 | `ollama serve` + imported GGUF |
| `ollama-default` | Ollama 0.40.14 | 11434 | `ollama serve` + native tag |

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

The OpenAI-compatible endpoint is `http://127.0.0.1:11434/v1`.

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

## One engine at a time

| Measuring | Must be stopped |
|---|---|
| `splash` | Mirai, any loaded Ollama model |
| `mirai` | Splash, any loaded Ollama model |
| `ollama-*` | Splash and Mirai |

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
