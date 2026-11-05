# Methodology

## Question

Which local engine is the best fit for this Mac mini for agent-style work, and
where does each engine trade speed for memory, context or multimodal input?

This benchmark measures **engine speed and memory**, not model quality. The
contenders do not run identical weights: Splash runs a GGUF Q3_K_XL and Mirai
runs a 4-bit M model. A quality comparison would need the same weights and a
separate evaluation set.

## Test machine

| Item | Value |
|---|---|
| Machine | Mac mini M6, 32 GB unified memory |
| Reported memory | 34.4 GB (`hw.memsize`) |
| OS | macOS 27.2 (Darwin 27.2.0) |
| Python | 3.15.2 |
| Suite revision | 5 |
| Splash | 1.5.0 |
| Mirai/uzu | 0.6.17 |
| Ollama | 0.40.14 |

Results are only comparable on the same class of machine. A different Mac,
macOS version or engine version can change the numbers.

## Suite

The suite is versioned in `config/suite.toml`. New results record the suite
revision. Changing prompts, token counts or repetitions requires a revision
bump; historical result files are never edited.

| Case | Prompt | Output | Reps | Purpose |
|---|---|---:|---:|---|
| `decode_short` | short coding task | 256 | 3 | Warm decode throughput |
| `prefill_cold_long` | ~32K-char user prefix + `READY` task | up to 64 | 1 | Cold prefill and TTFT |
| `cached_ttft_long` | same prefix + fixed assistant turn + follow-up | 128 | 1 | Prefix-cache extension and long-context decode |

The long prefix is deterministic: it is generated from an integer sequence, so
every engine and every run sees exactly the same bytes.

### Why the cache case is an extension

A cache test that sends the exact same request twice can accidentally pass on
an engine that keeps a session open, and can accidentally fail on an engine
that appends the previous assistant turn. The suite instead sends:

1. cold: `user(long prefix + task)`
2. cached: `user(long prefix + task)` + `assistant(fixed)` + `user(follow-up)`

The second request extends the first one by a known, fixed amount. A prefix
cache should reuse the long user prefix and only prefill the extension.

The cold turn must **finish naturally** (`finish=stop`). If it is truncated by
`max_tokens`, Mirai's prefix cache is left in a non-extensible state and the
next request reprefills. The cold task therefore asks for the single word
`READY`, and the suite allows up to 64 output tokens so the turn can stop on
its own.

Validation requires both:

- the cached request did not lose prompt tokens (`cached.prompt_tokens >=
  cold.prompt_tokens`), and
- cached TTFT is less than half of cold TTFT (or under 1 s).

If either fails, the case is marked `invalid` and excluded from the summary.
The raw value is retained as `reported_cached_ttft_long_ms`.

## Metrics

- **TTFT:** wall-clock time from request start to the first content or
  reasoning token.
- **Prefill tok/s:** `prompt_tokens / TTFT`, using the server's usage report.
- **Decode tok/s:** `(completion_tokens - 1) / (last_token - first_token)`,
  using server-reported completion tokens when available.
- **Peak engine RSS:** sum of RSS for processes matching the engine pattern,
  sampled every 0.5 s.
- **Peak wired memory:** `vm_stat` pages wired, sampled every 0.5 s. On macOS,
  Metal allocations are wired and do not show up fully in RSS. For a 27B model,
  wired memory is the meaningful figure.
- **Context window:** the value the engine advertises through `/v1/models`.
  This is not a verified long-context quality result.

## Procedure

1. Stop every other model-loaded engine. The harness refuses to run if a
   conflicting process is alive.
2. Verify exactly one listener on the engine port.
3. Wait for `/v1/models`.
4. Run one warmup request (8 tokens) and discard it.
5. Run the suite in order.
6. Sample RSS and wired memory throughout.
7. Validate the cache case.
8. Write a schema-1 JSON result with engine version, model metadata, machine
   metadata, suite revision, validation and all raw runs.
9. Generate a Markdown report from one or more result files.

## Fairness rules

The normative rules are in [`fairness-rules.md`](fairness-rules.md). In short:
one engine at a time, same suite revision, temperature 0, reasoning disabled,
same prompt bytes, warmup excluded, median for repeated runs, and invalid
cases excluded rather than averaged.

## Known limitations

- **Different weights.** Splash and Mirai do not run the same quantization.
  The comparison is engine speed, not model quality.
- **One machine.** Thermal state, macOS version and background load matter.
- **Three repetitions.** Short decode is stable, but this is not a statistical
  study.
- **Legacy Mirai cache run.** The original harness recorded a 35.0 s "cached"
  TTFT for Mirai because the truncated cold turn made the server reprefill. The
  archive keeps that invalid result. Suite v5 makes the cold turn finish
  naturally and both engines now produce valid cache hits.
- **Legacy case mismatch.** In the original harness, Mirai's
  `prefill_cold_long` run used 128 output tokens while Splash used 8. TTFT and
  prefill are unaffected; suite v5 fixes the output length.
- **Long-context decode is one repetition.** The 128-token decode after a cache
  hit is single-shot and sensitive to the prompt and thermal state. Do not
  over-rank engines on that row.
- **Context is reported, not verified.** Splash advertises 217,081 tokens.
  Mirai does not report a window and was only exercised at 18K. Both Ollama
  labels ran with a 32K context.
- **Ollama uses different weights.** The native tag is nvfp4 and the imported
  label is Q3_K_XL. The imported label isolates the engine (same weights as
  Splash); the native label measures the out-of-the-box experience. Both are
  speed measurements, not a quality comparison.
- **Ollama was measured in one pass per label.** The imported Q3_K_XL label is
  about 5x slower than Splash on short decode, so its low wired memory is not a
  free win.

## Change control

- Bump `[suite].revision` for any change that affects measurements.
- Add a new dated result file; never edit an old one.
- If you change a metric definition, update this document and the report
  version in the same pull request.
