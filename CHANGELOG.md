# Changelog

## Unreleased

- Accuracy suite (`bench eval`): 21 auto-graded items in 8 categories
  (instructions, JSON, tools, arithmetic, code, long context, abstention,
  extraction), graded by code with no LLM judge. Code items run in a
  timeout-limited sandbox. Results live in `results/eval/` and the decision
  table in `reports/eval-latest.md`.
- `config/eval.toml` with its own revision. Changing a prompt, limit, grader or
  item order requires a revision bump.
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
