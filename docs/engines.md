# Engines

The harness only needs an OpenAI-compatible `/v1/models` and
`/v1/chat/completions` endpoint with streaming. Lifecycle commands are defined
in `config/engines.toml`; the documentation below explains what was used for the
November 2026 result set.

| Label | Engine | Port | Start command |
|---|---|---:|---|
| `splash` | Splash 1.5.0 | 8000 | `splash serve --model unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL --port 8000` |
| `mirai` | Mirai/uzu 0.6.17 | 8000 | `mirai server --model qwen3.8:27b --port 8000` |
| `ollama` | Ollama 0.40.14 | 11434 | `ollama serve` + `qwen3.5-9b-q4` |

## Splash 1.5.0

Install the Splash CLI so `splash --version` prints `Splash 1.5.0`. The Homebrew
installation on the test machine lives at `/opt/homebrew/bin/splash`; if your
installation method differs, use the upstream installer and keep the command in
`config/engines.toml` in sync.

```bash
splash --version
splash serve --model unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL \
  --revision 4af51b3542f775b0a8e4b310bfb3f17e01c306c9 \
  --port 8000
```

The first launch downloads the GGUF and the DFlash2 draft. The model is
reported as `unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL`; the weights are Q3_K_XL
Dynamic V3.1 (~3-bit, about 13.15 GB) plus a draft of about 3.8 GB. Pinning the
revision keeps the benchmark reproducible; the pre-V3.1 results used `ce331ef`.

- Context: 217,081 tokens reported by `/v1/models`.
- Multimodal: accepts images and PDFs. Do not pass `--language-only` if you
  want to keep that capability.
- Reasoning: the benchmark sends `reasoning_effort: none`.
- API: `http://127.0.0.1:8000/v1`.
- Eval revision 6 (2026-11-16, model revision `4af51b3`, Dynamic V3.1):
  **20/26 (77%) with thinking off, 24/26 (92%) with thinking on**, and
  **8/8 on the vision suite**. It ties Mirai on text accuracy; the two
  sequential tool-chain items fail for both. Splash adds vision/PDF and 217K
  context at about 2 GB more wired memory.

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
  model config (`max_sequence_length` on the attention layers' RoPE) is
  **262,144 tokens (256K)** — the architecture is a hybrid of DeltaNet linear
  attention and standard attention across 64 layers. The benchmark only
  exercised 18K tokens. For daily use in OpenCode the client-side context limit
  is set to **131,072 (128K)** in `~/.config/opencode/opencode.jsonc` to avoid
  frequent compaction without paying for the full 256K prefill.
- Multimodal: the M model is text-only.
- API: `http://127.0.0.1:8000/v1`.
- Prefix cache: enabled by default; `--no-prefix-cache` is available for
  debugging, not for the benchmark. The previous turn must finish naturally
  (`finish=stop`); a turn truncated by `max_tokens` leaves the cache
  non-extensible. The suite's cold task answers `READY` so the extension can
  hit.
- Eval revision 6 (2026-11-16): **20/26 (77%) with thinking off, 24/26 (92%)
  with thinking on**. The five code items, the three long-context items and the
  single tool call pass; the two sequential tool-chain items fail for every
  model because the runner is single-turn. No truncation. This ties Splash V3.1
  on accuracy and is faster.
- Vision: not applicable. Mirai's M model is text-only.

## Ollama 0.40.14

Ollama is treated as a persistent service. Start it once and let both Ollama
labels use it:

```bash
ollama --version
ollama serve
ollama list
ollama ps
```

The engine label is `ollama` and it points at `qwen3.5-9b-q4`, the 9B that fits
next to Teams and a cloud desktop. Pass `--model` to measure another tag, and
keep `num_ctx` in mind: the tag decides the window, and 32K is what the 9B uses
here, so the 65K needle cannot run. Ollama honours `reasoning_effort` for
thinking models.

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
./scripts/engine.sh stop ollama --force
```

Before a Splash or Mirai pass, confirm no Ollama model is resident:

```bash
ollama ps
# if a model is listed:
ollama stop <model>
```

## Removed contenders

Rule 9 of `AGENTS.md` deletes models that lose; the report has to say why, so
this is the record. Disk went from 112 GiB to 163 GiB free on 2026-11-17.

| Removed | Size | Why |
|---|---:|---|
| `omlx` + `Qwen3.8-27B-4bit` | 15 GB | 9.2 tok/s short decode, six times slower than Splash or Mirai, and no accuracy gain at revision 5. Its only edge was a 262,144-token window, which Mirai matches (256K in its model config). |
| `ollama-q3kxl` + `qwen3.8-27b-q3kxl` | 13 GB | 11.0 tok/s and a 32K window; the same quant on Splash is five times faster. |
| `ollama-default` + `qwen3.8:27b` | 18 GB | 30.6 tok/s and 32K; Splash and Mirai are faster with a bigger window. |
| `qwen2.5-coder:7b` | 4.7 GB | 7/18 on revision 5 (39 %). The 9B scores 14/18 with 0.6 GB more wired memory. |
| Splash-side 9B GGUF | 6.4 GB | Splash 1.5.0 cannot load the Qwen3.5 architecture; Ollama keeps its own copy of the blobs, so the source file was a duplicate. |

The result files stay: they are history, and the reports still show their columns.
What disappears is the ability to re-run them on this machine without downloading
again.

## One engine at a time

| Measuring | Must be stopped |
|---|---|
| `splash` | Mirai, any loaded Ollama model |
| `mirai` | Splash, any loaded Ollama model |
| `ollama` | Splash, Mirai |

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
