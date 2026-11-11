from __future__ import annotations

import base64
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
from ..eval.graders import loose
from ..metrics import capture_version, machine_info, wait_for_models
from ..runner import UNSET
from .settings import VisionSettings
from .tasks import build_tasks

VISION_RESULTS_DIR = REPO_ROOT / "results" / "vision"
STRIP = " .,;:!?¡¿\"'"


def default_out_path(label: str) -> Path:
    VISION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    path = VISION_RESULTS_DIR / f"{day}-{label}.json"
    if path.exists():
        stamp = datetime.now().strftime("%H%M%S")
        path = VISION_RESULTS_DIR / f"{day}-{label}-{stamp}.json"
    return path


def matches(expected: str, answer: str) -> bool:
    return loose(expected).strip(STRIP) == loose(answer).strip(STRIP)


def run_vision(
    engine: Engine,
    settings: VisionSettings,
    *,
    label: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    reasoning_effort=UNSET,
    out: Path | str | None = None,
    timeout: int = 900,
    safety: bool = True,
    items: tuple[str, ...] = (),
) -> Path:
    label = label or f"{engine.label}-vision"
    base_url = (base_url or engine.base_url).rstrip("/")
    port = port_from_url(base_url)
    effort = engine.reasoning_effort if reasoning_effort is UNSET else reasoning_effort
    if effort == "":
        effort = None
    tasks = build_tasks(settings)
    if items:
        unknown = set(items) - {task.id for task in tasks}
        if unknown:
            raise ValueError(f"unknown vision items: {', '.join(sorted(unknown))}")
        tasks = tuple(task for task in tasks if task.id in items)

    if safety:
        assert_exclusive(engine)
        assert_single_listener(port, label)
        assert_ollama_idle(engine)

    print(f"== vision {label} @ {base_url}", file=sys.stderr)
    wait_for_models(base_url, timeout=min(timeout, 120))
    model_id, _entry = pick_model(get_models(base_url), model or engine.api_model)
    print(f"   model: {model_id}", file=sys.stderr)

    if engine.label.startswith("ollama"):
        unload_other_ollama_models(model_id)

    version = capture_version(engine.version_cmd)
    client = ChatClient(
        base_url,
        model_id,
        effort,
        timeout=timeout,
        seed=settings.seed,
        chat_template_kwargs=engine.template_kwargs,
    )

    started = datetime.now(UTC)
    records: list[dict] = []
    for index, task in enumerate(tasks, start=1):
        encoded = base64.b64encode(task.image).decode("ascii")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": task.prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}"},
                    },
                ],
            }
        ]
        try:
            result = client.stream_messages(messages, min(settings.max_tokens, task.max_tokens))
        except Exception as exc:  # noqa: BLE001 - request-level failures are data
            print(f"   [{index}/{len(tasks)}] {task.id} ERROR {exc}", file=sys.stderr)
            records.append(
                {
                    "id": task.id,
                    "passed": False,
                    "detail": f"request error: {exc}",
                    "error": str(exc),
                    "image_sha256": task.image_sha256,
                }
            )
            continue
        passed = any(matches(value, result.answer) for value in task.expect)
        records.append(
            {
                "id": task.id,
                "passed": passed,
                "detail": "accepted answer" if passed else f"answer {result.answer!r} not accepted",
                "extracted": result.answer.strip()[:120],
                "answer_preview": result.answer_preview,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "ttft_ms": result.ttft_ms,
                "total_ms": result.total_ms,
                "finish_reason": result.finish_reason,
                "reasoning_chunks": result.reasoning_chunks,
                "image_sha256": task.image_sha256,
            }
        )
        print(
            f"   [{index}/{len(tasks)}] {task.id} "
            f"{'PASS' if passed else 'FAIL'} ({result.answer.strip()[:40]!r})",
            file=sys.stderr,
        )

    finished = datetime.now(UTC)
    graded = [record for record in records if "error" not in record]
    passed = sum(1 for record in graded if record["passed"])
    summary = {
        "items": len(graded),
        "passed": passed,
        "accuracy": round(passed / len(graded), 4) if graded else None,
        "errors": len(records) - len(graded),
        "total_ms": round(sum(record["total_ms"] for record in graded), 1) if graded else None,
    }
    document = {
        "schema_version": 1,
        "kind": "vision",
        "label": label,
        "timestamp": started.isoformat(),
        "finished_at": finished.isoformat(),
        "source": "bench-vision",
        "engine": {
            "label": engine.label,
            "name": engine.name,
            "version": version,
            "base_url": base_url,
            "port": port,
            "reasoning_effort": effort,
            "start_command": list(engine.start),
        },
        "model": {
            "id": model_id,
            "configured_id": engine.api_model,
            "quantization": engine.quantization,
        },
        "vision": {
            "revision": settings.revision,
            "image_size": settings.image_size,
            "max_tokens": settings.max_tokens,
            "seed": settings.seed,
            "items": [{"id": task.id, "image_sha256": task.image_sha256} for task in tasks],
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
