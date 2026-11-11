# Agent guide

This repository measures local LLM engines. Correctness and provenance matter
more than a nice-looking table.

## Hard rules

1. **Never fabricate or hand-edit a measurement.** Results come from
   `bench run`. If a case is invalid, keep the JSON and mark it invalid.
2. **One model-loaded engine at a time.** The harness enforces this; do not
   bypass it with `--no-safety` unless you are debugging the harness itself.
3. **Do not stop a user-managed service without explicit consent.** `--force`
   is for engines the user asked you to clean up, not for a random `ollama`
   service.
4. **Historical results are immutable.** Add a new dated file; never rewrite an
   old result to make a comparison cleaner.
5. **Change the suite revision when measurements change.** Prompts, token
   limits, repetitions and case order are part of the contract.
6. **Speed and accuracy are separate axes.** Speed and memory belong to
   engine × model and only come from `bench run` (suite revision in
   `config/suite.toml`). Accuracy belongs to the model's weights and only comes
   from `bench eval`, with temperature 0, a fixed engine per model, graders
   written as code (never an LLM judge) and `[eval].revision` in
   `config/eval.toml` bumped whenever a prompt, limit, grader or item order
   changes. Never compare accuracy across eval revisions, never hand-edit a
   grade, and never publish accuracy from a run whose summary reports
   `errors > 0` or reasoning leaked while thinking was off. Different weights
   may enter the accuracy comparison, and the report says which task each one
   wins; they still must not be compared as an engine-speed result.
7. **Keep the runtime dependency-free.** Python standard library only; dev
   dependencies belong in the `dev` extra.
8. **Run `make check` before finishing.** Ruff and pytest must pass.
9. **Discarded models and eval items are deleted, not archived.** Accuracy
   results are immutable, but weights that lose the trials and eval items that
   do not discriminate are removed from disk and from the suite (bump
   `[eval].revision`), after the report records why. Do not keep a model
   "just in case".

## Workflow

- Read `config/engines.toml`, `config/suite.toml`, `config/eval.toml` and
  `docs/fairness-rules.md` before changing benchmark behaviour.
- Use `./scripts/engine.sh status` to inspect the machine.
- Use `./scripts/run-pass.sh <label>` for one pass; use `make run-all` only when
  every model is installed.
- Use `bench eval <engine>` for accuracy and `make eval-report` to regenerate
  the decision table. Run `make check` and `bench eval-validate --strict` on a
  new eval result before handoff.
- Regenerate the report with `make report`.
- If you touch the cache case, run the validation command and include the
  result in the handoff:

```bash
.venv/bin/python -m bench.cli validate results/<file>.json --strict
```

## Where things live

| Path | Responsibility |
|---|---|
| `bench/client.py` | OpenAI-compatible streaming and compatibility fallbacks |
| `bench/runner.py` | One pass: warmup, cases, sampling, JSON output |
| `bench/eval/` | Accuracy suite: items, graders, sandbox, runner, report |
| `bench/validation.py` | Cache validation and summary aggregation |
| `bench/report.py` | Markdown table and verdict |
| `bench/engine.py` | Start/stop/status and safety checks |
| `bench/legacy.py` | Schema-0 import and provenance |
| `config/` | Engines, models, speed suite and eval suite |
| `docs/` | Methodology, rules, setup and results |
| `docs/eval.md` | Accuracy suite contract and decision table rules |
| `results/` | Committed measurements |
| `results/eval/` | Committed accuracy results (never mixed with speed runs) |
| `reports/` | Generated Markdown |

## Known pending work

- Eval revision 4: 19 of 21 items pass for every run at revision 3, so the
  suite is saturated for 27B-class weights. Harden the saturated categories
  before adding another model.
- A second model that differs from Qwen3.8-27B in a way this machine can hold.
  Another 27B quantization ties on the current items.
- Optional second repetition of the long-context decode case to check variance.
- Optional long-context stress test for Splash beyond 18K.
- Optional image/PDF checks for Splash and Ollama native (not throughput).

Do not claim these are done in the README until a result file exists.

## Handoff checklist

- [ ] `make check` passes.
- [ ] New result JSON is in `results/` and validates.
- [ ] New eval JSON is in `results/eval/` and `bench eval-validate --strict` passes.
- [ ] `reports/latest.md` regenerated.
- [ ] `reports/eval-latest.md` regenerated if there is a new eval result.
- [ ] Docs updated if behaviour or verdict changed.
- [ ] No model weights, logs or `.venv` staged.
