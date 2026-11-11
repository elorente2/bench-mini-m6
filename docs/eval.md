# Accuracy suite

The speed suite answers "which engine is faster". This suite answers a
different question: **which model, at the size this machine can hold, is good
enough for the daily task in front of me?**

## Two axes, never mixed

| Axis | Varies | Measured by | Lives in |
|---|---|---|---|
| Speed and memory | engine × model | `bench run`, suite revision | `results/*.json`, `reports/latest.md` |
| Accuracy | model weights | `bench eval`, eval revision | `results/eval/*.json`, `reports/eval-latest.md` |

Accuracy is measured with **one fixed engine per model** and `temperature: 0`.
The engine does not decide whether a 4-bit model knows a date; the weights do.
Mixing engines into the accuracy axis would turn a model comparison into an
engine comparison again.

Accuracy results are stored under `results/eval/` so `make report` and the
speed report never pick them up. A speed result and an eval result are not
interchangeable documents.

## The contract

| Item | Value |
|---|---|
| Revision | `[eval].revision` in `config/eval.toml` |
| Sampling | `temperature: 0`, `seed: 0` |
| Thinking | Off by default; the run records how it was disabled |
| Items | 21, fixed order, 8 categories |
| Output limit | Per item in `bench/eval/tasks.py`; a global ceiling in the config |
| Grading | Code only. No LLM judge, no human rubric |
| Retries | None. One request per item |

Changing a prompt, a limit, a grader, an item or their order means bumping the
revision. Results from different revisions are never compared.

## Categories and items

| Category | Items | What it checks |
|---|---:|---|
| `instrucciones` | 3 | Bullet count and prefix, word limit, forbidden word, date format |
| `json` | 3 | Flat schema, enum + boolean classification, ordered array |
| `herramientas` | 2 | One tool call, and search-before-write in a two-tool turn |
| `calculo` | 3 | Percentage, date arithmetic, multi-step word problem |
| `codigo` | 3 | Two functions and one bug fix, graded by running unit tests |
| `contexto_largo` | 2 | A code buried in ~24K and ~64K characters of filler |
| `abstencion` | 2 | Say `NO CONSTA` instead of inventing a missing datum |
| `extraccion` | 3 | Invoice fields, agenda line, action-item owner |

The long-context items record the real `prompt_tokens` from the engine, so the
report quotes tokens rather than the character count used to build the filler.

## Graders

All graders are pure functions in `bench/eval/graders.py`:

- `exact` (case, accent and trailing-punctuation tolerant, optionally
  alphanumeric only),
- `regex` with explicit anchors,
- `json` with a small schema subset (`type`, `required`, `properties`, `items`,
  `enum`, `additionalProperties`, `minItems`, `maxItems`) plus expected values,
- `tool` over the real `tool_calls` returned by the engine,
- `bullets`, `constraints`, `kv`, `parts` for format-following tasks,
- `code`, which extracts the fenced block and runs it.

A grader never receives the model name, the engine or the other answers, so an
item cannot be graded differently because of who answered it.

## The code sandbox

`bench/eval/sandbox.py` runs generated code in a temporary directory with:

- `python -I -S` (isolated mode, no user site, no environment influence),
- `RLIMIT_CPU` at the item timeout, `RLIMIT_FSIZE` at 1 MB,
  `RLIMIT_NOFILE` at 64 and `RLIMIT_NPROC` at 32,
- a wall-clock timeout as a second line of defence,
- `socket.socket.connect`, `connect_ex` and `create_connection` replaced with
  a function that raises, so casual network use fails,
- a minimal environment with `HOME` and `TMPDIR` pointing at the temp dir.

This is a guard against broken or runaway code, **not a hostile-code sandbox**.
It does not use a container, a separate user or a network namespace. Do not
paste code from an untrusted source into an eval item and do not describe this
as isolation. The tests say exactly that.

## Gates

A run supports a decision only if all of these hold:

1. `summary.errors == 0` — every item produced an HTTP response.
2. `summary.thinking_leaked_items` is empty when thinking was expected to be
   off. Reasoning tokens change the answer and break the comparison.
3. The run has the revision shared by the group being compared.

`bench eval-validate --strict` exits non-zero when a gate fails, so a CI job or
a handoff check can reject the run.

## Commands

```bash
# One model, one engine. The engine must already be running.
.venv/bin/python -m bench.cli eval splash --label qwen3.8-q3kxl-splash

# Thinking off vs on for the same weights, as two separate runs.
.venv/bin/python -m bench.cli eval omlx \
  --label qwen3.8-4bit-thinkoff \
  --template-kwarg enable_thinking=false
.venv/bin/python -m bench.cli eval omlx \
  --label qwen3.8-4bit-thinkon \
  --template-kwarg enable_thinking=true

# A subset while iterating on one category.
.venv/bin/python -m bench.cli eval omlx --only codigo,json

# One item, to debug a grader.
.venv/bin/python -m bench.cli eval omlx --item json-pedido

# Report and gates.
make eval-report
.venv/bin/python -m bench.cli eval-validate results/eval/2026-11-11-label.json --strict
```

`--template-kwarg` is generic on purpose: it overrides any chat-template
argument, so the same switch works for an engine that needs
`enable_thinking` and for one that needs a different key.

## Result document

Schema 1, `kind: "eval"`. Each item records `passed`, `detail`, the extracted
value, the answer preview, tokens, TTFT, total latency, reasoning chunk count,
whether thinking leaked and the tool names that were called. The summary keeps
accuracy overall and per category, the error count and the slowest item. The
eval block keeps the revision, limits, thinking flag and the item list with its
grader, so an old result still explains how it was scored.

## Decision table

`make eval-report` writes `reports/eval-latest.md`. The decision section picks,
for each category, the highest accuracy among valid runs of the same revision,
and lists the runs that tie. A model only "wins a task" when it is not tied.
Ties are reported as ties, not broken by speed: speed belongs to the other
axis.

The report also lists items that every run passed or every run failed:

- **Everyone passes** — candidate for pruning or for a harder variant.
- **Everyone fails** — either a real ceiling or a badly written item. Check the
  prompt and the grader before calling it a ceiling.

## Pruning

Keeping every 27B checkpoint is not possible on 32 GB of unified memory and a
few hundred GB of disk, and keeping items that do not separate models makes the
suite slower without adding information.

After a trial round:

1. A model is removed from `config/models.toml`, its weights deleted from
   `~/.omlx/models` (or the engine's store) and its engine label removed from
   `config/engines.toml` when it loses every category it was meant for and
   another kept model matches or beats it.
2. An item is removed (and the revision bumped) when every run passes it for
   the same reason and it does not guard a real failure mode. An item that
   everyone fails is rewritten first; if it still fails for everyone, it is a
   ceiling and stays, documented as one.
3. Result files are never deleted or edited. The report explains what was
   removed and why.

The point is not to accumulate benchmarks. It is to keep the smallest set of
models and items that answers "which model for this task".

## Limits

- The pilot has 21 items; a single item is worth 4.8 points. Treat differences
  under two items as noise until a second repetition exists.
- One repetition per item. `temperature: 0` and a fixed seed reduce variance on
  the server side, not on the tokenizer or the sampler.
- The long-context items measure retrieval at the prompt sizes recorded in the
  result, not the advertised context window.
- No vision, PDF or OCR item yet. Splash and Ollama native advertise those
  capabilities; they are not measured here.
- The sandbox is best effort, as described above.
