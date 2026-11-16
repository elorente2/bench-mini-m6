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
| Items | 20, fixed order, 9 categories |
| Output limit | Per item in `bench/eval/tasks.py`, plus `[eval].reasoning_headroom` |
| Grading | Code only. No LLM judge, no human rubric |
| Retries | None. One request per item |

Changing a prompt, a limit, a grader, an item or their order means bumping the
revision. Results from different revisions are never compared; the decision
table only uses the newest revision.

### Reasoning headroom

A thinking model spends part of its budget reasoning, and the per-item limits
were written for a direct answer: with thinking on, Qwen3.8-27B ended every
answer at `finish_reason: length` without reaching a result. So revision 2
added `[eval].reasoning_headroom` and revision 3 raised it to 4096 tokens,
after `math-fecha` needed 1169 tokens to finish. The headroom is added to every
item, so `reasoning_headroom = 0` reproduces the revision-1 limits exactly.

Truncation is not treated as a wrong answer that a model "deserves": each run
records `summary.truncated`, the report shows it in the cost table, and an item
that keeps hitting the limit at the current revision is a budget bug, not a
finding about the model.

## Categories and items

| Category | Items | What it checks |
|---|---:|---|
| `instrucciones` | 2 | Exact bullet format; 25-word summary with a required opening and two forbidden words |
| `json` | 2 | Flat schema; nested schema with enum, ordered lines and a conditional field |
| `herramientas` | 2 | One tool call, and search-before-write in a two-tool turn |
| `arquitectura` | 3 | Pick a design under three constraints; spot the two contradictory lines; four-section ADR |
| `calculo` | 2 | Percentage with rounding; date arithmetic |
| `codigo` | 3 | JS accent-insensitive filter; Python permission rule with a hardening order; SQLite `GROUP BY`/`HAVING` |
| `contexto_largo` | 2 | A code buried in ~9K and ~65K tokens of filler |
| `abstencion` | 2 | Say `NO CONSTA` instead of inventing a phone number or a version |
| `extraccion` | 2 | Invoice fields; exception, function and HTTP status from a trace |

Revision 4 replaced the twelve items every model passed. The new ones come from
the work this benchmark is actually for: code review, refactors, API contracts
and architecture decisions. Revision 5 only raised the reasoning headroom, after
a code item ran out of budget while thinking.

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
- `bullets`, `constraints`, `sections`, `kv`, `parts` for format-following tasks
  (`sections` requires given line prefixes in order and a word budget),
- `code`, which extracts the fenced block and runs it with Python or, for
  `lang = "js"`, Node.

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

The JavaScript items use `node --permission --allow-fs-read=<tmp>`, which
denies writes and reads outside the temp directory. Node's permission model
does not cover the network, so a preloaded guard patches `net.Socket.connect`,
`net.connect` and `dns.lookup` to throw. Same caveat as Python: a guard, not a
container.

This is a guard against broken or runaway code, **not a hostile-code sandbox**.
It does not use a container, a separate user or a network namespace. Do not
paste code from an untrusted source into an eval item and do not describe this
as isolation. The tests say exactly that.

## Gates

A run supports a decision only if all of these hold:

1. `summary.errors == 0` — every item produced an HTTP response.
2. `summary.thinking_leaked_items` is empty when thinking was expected to be
   off. Reasoning tokens change the answer and break the comparison.
3. The run belongs to the newest revision: older revisions are history, not a
   comparison base.

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
accuracy overall and per category, the error count, how many answers hit the
token limit (`truncated`) and the slowest item. The eval block keeps the
revision, limits, thinking flag and the item list with its grader, so an old
result still explains how it was scored.

## Decision table

`make eval-report` writes `reports/eval-latest.md`. The decision section picks,
for each category, the highest accuracy among valid runs of the newest
revision, and lists the runs that tie. A model only "wins a task" when it is
not tied. Ties are reported as ties, not broken by speed: speed belongs to the
other axis.

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

## What revision 5 showed

Twenty items, eight runs, four weight sets. Every run passes the gates
(`errors: 0`, no leaked reasoning) and all eight are one revision.

| Run | Accuracy | Fails | Thinking |
|---|---:|---|---|
| Q3_K_XL · Splash (pre-V3.1) | 17/20 | nested JSON, design choice, IVA | off |
| Q3_K_XL · Splash (pre-V3.1) | 19/20 | permission item, truncated at 8,892 tokens | on |
| 4-bit MLX · oMLX | 17/20 | nested JSON, design choice, IVA | off |
| 4-bit MLX · oMLX | 19/20 | permission item, truncated at 8,892 tokens | on |
| 4-bit M · Mirai/uzu | 18/20 | nested JSON, IVA | off |
| 4-bit M · Mirai/uzu | **20/20** | none | on |
| Q3_K_XL · Splash V3.1 | 18/20 | nested JSON, IVA | off |
| Q3_K_XL · Splash V3.1 | **20/20** | none | on |

1. **Thinking fixes JSON, architecture and calculation; V3.1 also removes the
   code penalty.** With thinking on, Mirai and Splash V3.1 reach 20/20. The old
   Splash and oMLX runs reached 19/20 because the model reasoned past the
   8,192-token headroom and never emitted the function.
2. **V3.1 closed both old Splash gaps.** Off, it now passes the architecture
   design choice that the pre-V3.1 weights missed. On, it passes the code item
   without truncation. The old 8,892-token code ceiling was a weight/engine
   artifact, not a property of Qwen3.8-27B.
3. **The off-mode ceiling is shared by Mirai and V3.1.** Both miss nested JSON
   and the IVA calculation with thinking off. That is the only accuracy
   difference left between them.
4. **The suite is saturated for both leaders with thinking on.** Mirai and
   Splash V3.1 both reach 20/20; in the focused four-run comparison, 18 of the
   20 items pass for everyone. The next revision needs harder variants, not
   another 27B checkpoint.

Practical reading for a daily driver: **accuracy is now a tie between Mirai M
and Splash V3.1** (18/20 off, 20/20 on). Choose Mirai for text speed and lower
memory; choose Splash V3.1 for vision/PDF and the 217K context path. Use
thinking off for speed and code, and thinking on for JSON contracts,
arithmetic and architecture.

## What the pilot showed (revision 3, superseded)

Revision 4 replaced the items below, so these numbers are history. They are
kept because they explain why the suite changed: two weight sets, two engines
and nineteen items that nobody failed.

Revision 3 was measured against two sets of Qwen3.8-27B weights: UD-Q3_K_XL on
Splash and 4-bit MLX on oMLX, each with thinking off and on.

| Run | Accuracy | Cálculo | Thinking |
|---|---:|---:|---|
| Q3_K_XL · Splash | 20/21 | 2/3 | off |
| Q3_K_XL · Splash | 21/21 | 3/3 | on |
| 4-bit MLX · oMLX | 20/21 | 2/3 | off |
| 4-bit MLX · oMLX | 21/21 | 3/3 | on |

Three conclusions, all of them about the suite rather than the models:

1. **The quantization does not matter at this size.** Q3_K_XL and 4-bit MLX tie
   on every category, including the same wrong arithmetic answer with thinking
   off (1499.60 € where 1240 × 1.21 = 1500.40 €). The engine did not change the
   answer either, which is the point of fixing one engine per model.
2. **Thinking is the only axis that separates.** Turning it on fixes `math-iva`
   in both runs and breaks nothing else.
3. **19 of the 21 items do not discriminate.** Every run passes them, so they
   cost time without adding information. Only `math-iva` and `math-fecha` moved,
   and only because of thinking.

So the next move is **not** another 27B checkpoint: it would tie again. The
suite needs a revision 4 with harder variants of the saturated categories (or
items aimed at what actually goes wrong in daily use), and the decision table
needs at least two models that differ in a way this machine can hold. Keeping
the four current runs is still useful: they are the baseline any harder item
must beat.

## Limits

- The suite has 20 items; a single item is worth 5 points. Treat differences
  under two items as noise until a second repetition exists.
- One repetition per item. `temperature: 0` and a fixed seed reduce variance on
  the server side, not on the tokenizer or the sampler.
- The long-context items measure retrieval at the prompt sizes recorded in the
  result, not the advertised context window. At revision 5 the longest needle is
  ~65K tokens. Against Splash's declared 217K that is **30 %** of the window;
  Mirai reports no declared window, so its coverage is blank even though it
  passed the 65K item. A low coverage is not a failure, it is an untested
  region. A near-max item costs 10–17 minutes of prefill per run on this machine.
- Vision is a separate suite (`bench vision`); this text suite does not mix
  vision, PDF or OCR into the accuracy table. The vision fixtures are generated
  in code and graded by code.
- The sandbox is best effort, as described above.
