# Changelog

## Unreleased

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
- First results: Qwen3.8-27B UD-Q3_K_XL on Splash, revision 3, 20/21 with
  thinking off and 21/21 with thinking on. The off run misses `math-iva`
  (answers 1499.60 € where 1240 × 1.21 = 1500.40 €), so that item separates
  thinking from not thinking.
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
