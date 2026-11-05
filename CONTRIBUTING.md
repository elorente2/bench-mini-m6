# Contributing

Thanks for helping make local LLM measurements more reproducible.

## Development setup

```bash
git clone https://github.com/Elorente2/local-llm-bench.git
cd local-llm-bench
./scripts/bootstrap.sh
make check
```

`make check` runs Ruff and pytest. Use `make fmt` before committing.

## Adding or changing an engine

1. Add an `[engines.<label>]` table to `config/engines.toml`. Required fields:
   `name`, `base_url`, `port`, `model`, `proc_pattern`, `start`, `version_cmd`.
   Use `conflicts` to declare engines that must not run at the same time.
2. Add model metadata to `config/models.toml` if the model is new.
3. Document installation, model download and limitations in
   `docs/engines.md`.
4. Run one full pass and commit the JSON in `results/`.
5. Regenerate `reports/latest.md`.
6. If the engine rejects a standard field, add a fallback in
   `bench/client.py` and a unit test for it.

Do not add a dependency unless the standard library cannot do the job. The
benchmark must run on a clean macOS install with only Python and the engines.

## Changing the suite

The suite is a measurement contract. Any change to prompts, token limits,
repetitions or case order requires:

- a bump of `[suite].revision` in `config/suite.toml`,
- an update to `docs/methodology.md`,
- a note in the pull request explaining why old and new results are not
  directly comparable.

Never edit an existing result file to match a new suite.

## Submitting a result

A result pull request should include:

- `results/YYYY-MM-DD-<label>.json` produced by `bench run`,
- the regenerated `reports/latest.md` (and a dated report if the verdict
  changes),
- the engine version, model identifier, quantization and suite revision
  (already in the JSON),
- a short note if any case is invalid and why.

Do not hand-edit metrics. If a run is invalid, commit the raw JSON and mark it
invalid in the report.

## Code style

- Python 3.11+, standard library only at runtime.
- Ruff for lint and formatting (`make fmt`).
- Type hints on public functions.
- Keep macOS-specific commands behind the existing helpers so tests can run on
  Linux CI.
- Shell scripts use `set -euo pipefail` and must pass `shellcheck`.

## Commit messages

Use a short imperative subject, optionally with a scope:

```text
bench: validate cached TTFT against the cold run
docs: add Ollama import instructions
config: add ollama-default label
```

## Reporting a problem

Include the command, the engine version, the result JSON path and the relevant
lines from the engine log in `logs/`. Do not paste model weights or secrets.
