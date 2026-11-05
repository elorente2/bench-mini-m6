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
6. **Do not compare different weights as a quality result.** This repository
   measures engine speed and memory.
7. **Keep the runtime dependency-free.** Python standard library only; dev
   dependencies belong in the `dev` extra.
8. **Run `make check` before finishing.** Ruff and pytest must pass.

## Workflow

- Read `config/engines.toml`, `config/suite.toml` and `docs/fairness-rules.md`
  before changing benchmark behaviour.
- Use `./scripts/engine.sh status` to inspect the machine.
- Use `./scripts/run-pass.sh <label>` for one pass; use `make run-all` only when
  every model is installed.
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
| `bench/validation.py` | Cache validation and summary aggregation |
| `bench/report.py` | Markdown table and verdict |
| `bench/engine.py` | Start/stop/status and safety checks |
| `bench/legacy.py` | Schema-0 import and provenance |
| `config/` | Engines, models and suite |
| `docs/` | Methodology, rules, setup and results |
| `results/` | Committed measurements |
| `reports/` | Generated Markdown |

## Known pending work

- Optional second repetition of the long-context decode case to check variance.
- Optional long-context stress test for Splash beyond 18K.
- Optional image/PDF checks for Splash and Ollama native (not throughput).

Do not claim these are done in the README until a result file exists.

## Handoff checklist

- [ ] `make check` passes.
- [ ] New result JSON is in `results/` and validates.
- [ ] `reports/latest.md` regenerated.
- [ ] Docs updated if behaviour or verdict changed.
- [ ] No model weights, logs or `.venv` staged.
