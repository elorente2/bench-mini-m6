from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from .client import ChatClient, get_models, pick_model
from .config import REPO_ROOT, Engine, Suite
from .engine import (
    assert_exclusive,
    assert_ollama_idle,
    assert_single_listener,
    port_from_url,
    unload_other_ollama_models,
)
from .metrics import (
    MemSampler,
    capture_version,
    machine_info,
    read_wired_bytes,
    wait_for_models,
)
from .prompts import messages_for
from .validation import summarize_runs, validate_runs

RESULTS_DIR = REPO_ROOT / "results"
UNSET = object()


def default_out_path(label: str) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    path = RESULTS_DIR / f"{day}-{label}.json"
    if path.exists():
        stamp = datetime.now().strftime("%H%M%S")
        path = RESULTS_DIR / f"{day}-{label}-{stamp}.json"
    return path


def _context_tokens(entry: dict, engine: Engine) -> tuple[int | None, str]:
    for key in ("context_length", "context_window", "max_model_len", "max_context_tokens"):
        value = entry.get(key)
        if isinstance(value, int) and value > 0:
            return value, "api"
    return engine.context_tokens, "config" if engine.context_tokens else "unknown"


def run_pass(
    engine: Engine,
    suite: Suite,
    *,
    label: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    reasoning_effort=UNSET,
    out: Path | str | None = None,
    reps: int | None = None,
    decode_tokens: int | None = None,
    timeout: int = 1200,
    safety: bool = True,
    proc_pattern: str | None = None,
) -> Path:
    label = label or engine.label
    base_url = (base_url or engine.base_url).rstrip("/")
    port = port_from_url(base_url)
    effort = engine.reasoning_effort if reasoning_effort is UNSET else reasoning_effort
    if effort == "":
        effort = None
    pattern = proc_pattern or engine.proc_pattern

    if safety:
        assert_exclusive(engine)
        assert_single_listener(port, label)
        assert_ollama_idle(engine)

    print(f"== {label} @ {base_url}", file=sys.stderr)
    wait_for_models(base_url, timeout=min(timeout, 120))
    models = get_models(base_url)
    model_id, entry = pick_model(models, model or engine.api_model)
    context, context_source = _context_tokens(entry, engine)
    print(f"   model: {model_id}", file=sys.stderr)
    print(f"   context: {context} ({context_source})", file=sys.stderr)

    if engine.label.startswith("ollama"):
        unload_other_ollama_models(model_id)

    version = capture_version(engine.version_cmd)
    client = ChatClient(
        base_url,
        model_id,
        effort,
        timeout=timeout,
        chat_template_kwargs=engine.template_kwargs,
    )

    wired_before = read_wired_bytes()
    sampler: MemSampler | None = None
    if pattern:
        sampler = MemSampler(pattern)
        sampler.start()

    grouped: dict[str, list[dict]] = {}
    started = datetime.now(UTC)

    try:
        print("   warmup...", file=sys.stderr)
        client.stream_messages(messages_for("short"), suite.warmup_max_tokens)

        for case in suite.cases:
            messages = messages_for(case.prompt, prefill_target_chars=suite.prefill_target_chars)
            case_reps = reps if (reps and case.name == "decode_short") else case.reps
            case_max_tokens = (
                decode_tokens
                if (decode_tokens and case.name == "decode_short")
                else case.max_tokens
            )
            if case.validate == "cache_hit":
                case_max_tokens = max(case_max_tokens, 32)
            for index in range(case_reps):
                result = client.stream_messages(messages, case_max_tokens).as_dict()
                result.update({"case": case.name, "rep": index + 1})
                grouped.setdefault(case.name, []).append(result)
                print(
                    f"   {case.name} #{index + 1}: "
                    f"ttft={result['ttft_ms']}ms "
                    f"decode={result['decode_tps']} tok/s "
                    f"prefill={result['prefill_tps']} tok/s "
                    f"total={result['total_ms']}ms "
                    f"tokens={result['completion_tokens']}",
                    file=sys.stderr,
                )
    finally:
        if sampler:
            sampler.stop()
            sampler.join(timeout=2)

    wired_after = read_wired_bytes()
    finished = datetime.now(UTC)

    validation = validate_runs(grouped, suite.cases)
    summary = summarize_runs(
        grouped,
        validation,
        peak_rss_mb=round(sampler.peak_kb / 1024, 1) if sampler else None,
        wired_before_gb=round(wired_before / 1e9, 2) if wired_before else None,
        wired_peak_gb=(
            round(sampler.peak_wired / 1e9, 2) if sampler and sampler.peak_wired else None
        ),
        wired_after_gb=round(wired_after / 1e9, 2) if wired_after else None,
        rss_samples=sampler.samples if sampler else 0,
    )
    summary.update(
        {
            "model": model_id,
            "context": context,
            "context_source": context_source,
        }
    )

    runs = [run for case in suite.cases for run in grouped.get(case.name, [])]
    document = {
        "schema_version": 1,
        "label": label,
        "timestamp": started.isoformat(),
        "finished_at": finished.isoformat(),
        "source": "bench",
        "engine": {
            "label": engine.label,
            "name": engine.name,
            "version": version,
            "base_url": base_url,
            "port": port,
            "reasoning_effort": effort,
            "chat_template_kwargs": engine.template_kwargs or None,
            "proc_pattern": pattern,
            "persistent": engine.persistent,
        },
        "model": {
            "id": model_id,
            "configured_id": engine.api_model,
            "quantization": engine.quantization,
            "context": context,
            "context_source": context_source,
        },
        "suite": {
            "revision": suite.revision,
            "prefill_target_chars": suite.prefill_target_chars,
            "warmup_max_tokens": suite.warmup_max_tokens,
            "cases": [
                {
                    "name": case.name,
                    "prompt": case.prompt,
                    "max_tokens": case.max_tokens,
                    "reps": case.reps,
                    "validate": case.validate,
                    "compare_to": case.compare_to,
                }
                for case in suite.cases
            ],
        },
        "machine": machine_info(),
        "summary": summary,
        "validation": validation,
        "runs": runs,
    }

    out_path = Path(out) if out else default_out_path(label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"-> {out_path}", file=sys.stderr)
    return out_path
