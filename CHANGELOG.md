# Changelog

## Unreleased

- Vision suite (`bench vision`): eight items with images generated in code
  (PNG written with `zlib` and `struct`, no dependency) and answers graded by
  code: counting, majority colour, relative position, a seven-segment digit,
  an occluded centre, nine scattered circles and a three-digit display. It has
  its own revision in `config/vision.toml`, its own results in
  `results/vision/` and its own table in `reports/vision-latest.md`.
  Both measured models score 8/8, so the honest finding is that synthetic
  shapes are too easy, not that they see equally well. Limits and the case
  for real fixtures are in `docs/vision.md`.
- `ollama create` with two `FROM` lines (model plus `mmproj`) gives Qwen3.5-9B
  vision without a download, using the projector already on disk.

- Eval revision 4: twelve items that every run passed are gone and twenty
  harder ones take their place, built around code review, API contracts and
  architecture decisions (a JS accent-insensitive filter, a Python permission
  rule with a hardening order, SQLite `GROUP BY`/`HAVING`, a design choice under
  three constraints, a contradiction hunt, a four-section ADR, a nested JSON
  contract, an exception trace and a ~65K-token needle). Category
  `arquitectura` is new; the second needle covers 30 % of the declared window
  instead of 9–11 %.
- JavaScript code items: the sandbox runs `node --permission` with a preloaded
  guard that patches the socket and DNS entry points, because Node's permission
  model does not cover the network.
- New `sections` grader: given line prefixes in order plus a word budget.
- A truncated answer now says so in its row (`(truncated at N tokens)`), and the
  reasoning headroom went to 8192 in revision 5 after a code item spent its
  budget thinking without reaching the code.
- oMLX measured for speed (suite 5, 4-bit MLX): 9.2 tok/s short decode, 8.1 at
  18K, 200.4 tok/s prefill, 90.3 s cold TTFT, 1.5 s cached, 23.62 GB wired and
  9,500 MB RSS. The 6× gap to Splash and Mirai is speculative decoding: oMLX
  ships no draft model, so decode is memory-bandwidth bound.
- The speed report now refuses to use a case the run invalidated, keeps only the
  newest run per label, and excludes invalid runs from the verdict. A persisted
  prefix cache that made the "cold" prefill look like a 13,847 tok/s hit can no
  longer win the prefill row.
- The cache-hit validation also invalidates the cold prefill case when the
  cached turn was not clearly faster: the pair proves the cold start together.
- Speed results record `engine.start_command`, so a flag that changes
  performance is auditable from the result file.
- Accuracy suite (`bench eval`): 21 auto-graded items in 8 categories
  (instructions, JSON, tools, arithmetic, code, long context, abstention,
  extraction), graded by code with no LLM judge. Code items run in a
  timeout-limited sandbox. Results live in `results/eval/` and the decision
  table in `reports/eval-latest.md`.
- `config/eval.toml` with its own revision, now 3. Changing a prompt, limit,
  grader or item order requires a revision bump.
- `[eval].reasoning_headroom` (4096 tokens) gives a thinking model room to
  reason and still answer. Without it, thinking-on ended every answer at
  `finish_reason: length`. A run now records `summary.truncated` and the report
  shows it, because a truncated answer measures the budget, not the model.
- `bench eval --thinking-expected` declares thinking on for engines that have
  no `enable_thinking` template switch, so their reasoning is not flagged as a
  leak.
- First results: Qwen3.8-27B UD-Q3_K_XL on Splash and 4-bit MLX on oMLX,
  revision 3: 20/21 with thinking off and 21/21 with thinking on for both. The
  off runs miss `math-iva` (answers 1499.60 € where 1240 × 1.21 = 1500.40 €), so
  that item separates thinking from not thinking. The quantization and the
  engine changed neither the score nor the wrong answer.
- The decision table now names every run that ties for first place instead of
  showing one and listing the losers as ties.
- oMLX starts with `--memory-guard off`: the balanced guard ceilings the process
  below the size of the 4-bit weights and evicts the model mid-run.
- `docs/engines.md` records that `brew uninstall omlx` also removes
  `python@3.11`, the interpreter the venv points at, and how to recover.
- Eval CLI: `eval`, `eval-report` and `eval-validate --strict` (gates for
  request errors and leaked reasoning).
- `AGENTS.md` rule 6 rewritten: accuracy is a separate axis from engine speed,
  and discarded models and items must be deleted after the trial.
- oMLX 0.7.3 configured as a contender (MLX weights, port 8000). Not measured
  yet: no result file exists, so no numbers are published.
- Engine config can send `chat_template_kwargs`, used to disable Qwen thinking
  explicitly on engines that only forward `reasoning_effort` to the template.
  The field is recorded in the result's `engine` block and never stripped by
  the compatibility fallbacks.
- The client parses streamed `tool_calls`, which the tools category needs.

## 0.1.0 — 2026-11-05

- Initial benchmark harness for OpenAI-compatible local engines.
- Suite revision 5: short decode, cold 18K prefill, validated prefix-cache
  extension with 128-token long-context decode.
- Splash 1.5.0 and Mirai/uzu 0.6.17 clean results on Mac mini M6 32 GB.
- Ollama 0.40.14 native (`qwen3.8:27b`, nvfp4) and imported Q3_K_XL results,
  both at 32K context with thinking disabled.
- Schema-1 results, validation, Markdown report and legacy import.
- MIT license.
