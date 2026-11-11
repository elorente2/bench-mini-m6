from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from ..client import ChatClient, get_models, pick_model
from ..config import REPO_ROOT, Engine
from ..engine import (
    assert_exclusive,
    assert_ollama_idle,
    assert_single_listener,
    port_from_url,
    unload_other_ollama_models,
)
from ..metrics import capture_version, machine_info, wait_for_models
from ..runner import UNSET
from .graders import grade
from .settings import EvalSettings
from .tasks import CATEGORIES, Task, build_tasks

EVAL_RESULTS_DIR = REPO_ROOT / "results" / "eval"


def parse_template_kwarg(text: str) -> tuple[str, object]:
    """Parse ``key=value`` for --template-kwarg, coercing bools and numbers."""

    key, separator, raw = text.partition("=")
    key = key.strip()
    if not separator or not key:
        raise ValueError(f"expected key=value, got {text!r}")
    value = raw.strip()
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return key, lowered == "true"
    try:
        return key, int(value)
    except ValueError:
        pass
    try:
        return key, float(value)
    except ValueError:
        return key, value


def default_out_path(label: str) -> Path:
    EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    path = EVAL_RESULTS_DIR / f"{day}-{label}.json"
    if path.exists():
        stamp = datetime.now().strftime("%H%M%S")
        path = EVAL_RESULTS_DIR / f"{day}-{label}-{stamp}.json"
    return path


def _context_tokens(entry: dict, engine: Engine) -> tuple[int | None, str]:
    for key in ("context_length", "context_window", "max_model_len", "max_context_tokens"):
        value = entry.get(key)
        if isinstance(value, int) and value > 0:
            return value, "api"
    return engine.context_tokens, "config" if engine.context_tokens else "unknown"


def _select_tasks(tasks: tuple[Task, ...], only: tuple[str, ...], items: tuple[str, ...]):
    selected = tasks
    if only:
        unknown = set(only) - set(CATEGORIES)
        if unknown:
            raise ValueError(f"unknown categories: {', '.join(sorted(unknown))}")
        selected = tuple(task for task in selected if task.category in only)
    if items:
        unknown = set(items) - {task.id for task in selected}
        if unknown:
            raise ValueError(f"unknown items: {', '.join(sorted(unknown))}")
        selected = tuple(task for task in selected if task.id in items)
    if not selected:
        raise ValueError("the filters selected no eval items")
    return selected


def run_eval(
    engine: Engine,
    settings: EvalSettings,
    *,
    label: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    reasoning_effort=UNSET,
    template_kwargs: dict | None = None,
    out: Path | str | None = None,
    timeout: int = 1800,
    safety: bool = True,
    only: tuple[str, ...] = (),
    items: tuple[str, ...] = (),
) -> Path:
    label = label or f"{engine.label}-eval"
    base_url = (base_url or engine.base_url).rstrip("/")
    port = port_from_url(base_url)
    effort = engine.reasoning_effort if reasoning_effort is UNSET else reasoning_effort
    if effort == "":
        effort = None
    kwargs = dict(engine.template_kwargs)
    kwargs.update(template_kwargs or {})
    thinking_expected = kwargs.get("enable_thinking") is True
    tasks = _select_tasks(build_tasks(settings), only, items)

    if safety:
        assert_exclusive(engine)
        assert_single_listener(port, label)
        assert_ollama_idle(engine)

    print(f"== eval {label} @ {base_url}", file=sys.stderr)
    wait_for_models(base_url, timeout=min(timeout, 120))
    model_id, entry = pick_model(get_models(base_url), model or engine.api_model)
    context, context_source = _context_tokens(entry, engine)
    print(f"   model: {model_id}", file=sys.stderr)
    print(f"   items: {len(tasks)}", file=sys.stderr)

    if engine.label.startswith("ollama"):
        unload_other_ollama_models(model_id)

    version = capture_version(engine.version_cmd)
    client = ChatClient(
        base_url,
        model_id,
        effort,
        timeout=timeout,
        seed=settings.seed,
        chat_template_kwargs=kwargs,
    )

    started = datetime.now(UTC)
    print("   warmup...", file=sys.stderr)
    client.stream_messages([{"role": "user", "content": "Responde solo con OK."}], 8)

    records: list[dict] = []
    consecutive_errors = 0
    for index, task in enumerate(tasks, start=1):
        try:
            result = client.stream_messages(
                [{"role": "user", "content": task.prompt}],
                task.max_tokens,
                tools=list(task.tools) or None,
            )
        except Exception as exc:  # noqa: BLE001 - request-level failures are data
            consecutive_errors += 1
            if consecutive_errors >= 3:
                raise RuntimeError(
                    f"three consecutive request failures, last on {task.id}: {exc}"
                ) from exc
            print(f"   [{index}/{len(tasks)}] {task.id} ERROR {exc}", file=sys.stderr)
            records.append(
                {
                    "id": task.id,
                    "category": task.category,
                    "passed": False,
                    "detail": f"request error: {exc}",
                    "error": str(exc),
                }
            )
            continue
        consecutive_errors = 0
        graded = grade(task, result.answer, tool_calls=result.tool_calls or ())
        leaked = result.reasoning_chunks > 0 and not thinking_expected
        records.append(
            {
                "id": task.id,
                "category": task.category,
                "passed": graded.passed,
                "detail": graded.detail,
                "extracted": graded.extracted,
                "answer_preview": result.answer_preview,
                "answer_chars": result.answer_chars,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "ttft_ms": result.ttft_ms,
                "total_ms": result.total_ms,
                "decode_tps": result.decode_tps,
                "finish_reason": result.finish_reason,
                "reasoning_chunks": result.reasoning_chunks,
                "thinking_leaked": leaked,
                "tool_calls": [
                    (call.get("function") or {}).get("name") for call in (result.tool_calls or [])
                ],
            }
        )
        print(
            f"   [{index}/{len(tasks)}] {task.category}/{task.id} "
            f"{'PASS' if graded.passed else 'FAIL'} ({graded.detail[:70]})",
            file=sys.stderr,
        )

    finished = datetime.now(UTC)
    summary = summarize_eval(records, thinking_expected=thinking_expected)
    document = {
        "schema_version": 1,
        "kind": "eval",
        "label": label,
        "timestamp": started.isoformat(),
        "finished_at": finished.isoformat(),
        "source": "bench-eval",
        "engine": {
            "label": engine.label,
            "name": engine.name,
            "version": version,
            "base_url": base_url,
            "port": port,
            "reasoning_effort": effort,
            "chat_template_kwargs": kwargs or None,
            "persistent": engine.persistent,
        },
        "model": {
            "id": model_id,
            "configured_id": engine.api_model,
            "quantization": engine.quantization,
            "context": context,
            "context_source": context_source,
        },
        "eval": {
            "revision": settings.revision,
            "max_tokens": settings.max_tokens,
            "seed": settings.seed,
            "code_timeout_s": settings.code_timeout_s,
            "needle_chars": settings.needle_chars,
            "needle_long_chars": settings.needle_long_chars,
            "thinking_expected": thinking_expected,
            "categories": list(CATEGORIES),
            "items": [
                {
                    "id": task.id,
                    "category": task.category,
                    "grader": task.grader,
                    "max_tokens": task.max_tokens,
                }
                for task in tasks
            ],
        },
        "machine": machine_info(),
        "summary": summary,
        "items": records,
    }

    out_path = Path(out) if out else default_out_path(label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"-> {out_path}", file=sys.stderr)
    return out_path


def summarize_eval(records: list[dict], *, thinking_expected: bool) -> dict:
    graded = [record for record in records if "error" not in record]
    passed = sum(1 for record in graded if record["passed"])
    by_category: dict[str, dict] = {}
    for category in CATEGORIES:
        subset = [record for record in graded if record["category"] == category]
        if not subset:
            continue
        hits = sum(1 for record in subset if record["passed"])
        by_category[category] = {
            "items": len(subset),
            "passed": hits,
            "accuracy": round(hits / len(subset), 4),
        }
    totals = [record["total_ms"] for record in graded if record.get("total_ms") is not None]
    markers = [
        record["prompt_tokens"]
        for record in graded
        if record.get("prompt_tokens") and record["category"] == "contexto_largo"
    ]
    return {
        "items": len(graded),
        "passed": passed,
        "accuracy": round(passed / len(graded), 4) if graded else None,
        "errors": len(records) - len(graded),
        "by_category": by_category,
        "reasoning_chunks": sum(record.get("reasoning_chunks") or 0 for record in graded),
        "thinking_expected": thinking_expected,
        "thinking_leaked_items": [
            record["id"]
            for record in graded
            if record.get("thinking_leaked") and record.get("reasoning_chunks")
        ],
        "total_ms": round(sum(totals), 1) if totals else None,
        "slowest_ms": max(totals) if totals else None,
        "prompt_tokens_max": max(markers) if markers else None,
    }
