from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .config import Config, Engine
from .engine import port_from_url
from .metrics import capture_version
from .validation import group_runs, validate_cache_hit


def _first(runs: list[dict] | None) -> dict | None:
    return runs[0] if runs else None


def _legacy_engine(label: str, doc: dict, engine: Engine | None) -> dict:
    if engine:
        return {
            "label": label,
            "name": engine.name,
            "version": capture_version(engine.version_cmd),
            "version_source": "captured-at-import",
            "base_url": doc.get("base_url"),
            "port": port_from_url(doc.get("base_url") or engine.base_url),
            "reasoning_effort": doc.get("reasoning_effort"),
            "proc_pattern": engine.proc_pattern,
            "persistent": engine.persistent,
        }
    return {
        "label": label,
        "name": label,
        "version": None,
        "version_source": "unknown",
        "base_url": doc.get("base_url"),
        "port": port_from_url(doc.get("base_url") or "http://127.0.0.1:8000/v1"),
        "reasoning_effort": doc.get("reasoning_effort"),
        "proc_pattern": None,
        "persistent": False,
    }


def normalize_legacy(doc: dict, config: Config, *, source: str | None = None) -> dict:
    """Convert a schema-0 result from the original harness into schema 1.

    The raw runs are preserved. The only value that is recomputed is the cache
    validation, because that is where the original harness could silently
    record a cold prefill as a cache hit.
    """

    label = doc.get("label") or "unknown"
    engine = config.engines.get(label)
    runs = doc.get("runs") or []
    grouped = group_runs(runs)

    validation: dict[str, dict] = {}
    for name, case_runs in grouped.items():
        validation[name] = {
            "valid": bool(case_runs),
            "reasons": [] if case_runs else ["case produced no runs"],
        }
    if "cached_ttft_long" in grouped:
        cold = _first(grouped.get("prefill_cold_long"))
        cached = _first(grouped.get("cached_ttft_long"))
        validation["cached_ttft_long"] = validate_cache_hit(cold, cached)

    summary = dict(doc.get("summary") or {})
    cached_valid = validation.get("cached_ttft_long", {}).get("valid", False)
    if not cached_valid and summary.get("cached_ttft_long_ms") is not None:
        summary["reported_cached_ttft_long_ms"] = summary["cached_ttft_long_ms"]
        summary["cached_ttft_long_ms"] = None
    summary["valid_cases"] = sorted(
        name for name, result in validation.items() if result.get("valid")
    )
    summary["invalid_cases"] = sorted(
        name for name, result in validation.items() if not result.get("valid")
    )

    suite_cases = []
    for name, case_runs in grouped.items():
        suite_cases.append(
            {
                "name": name,
                "prompt": "long" if "long" in name else "short",
                "max_tokens": max(
                    (run.get("completion_tokens") or 0 for run in case_runs), default=0
                ),
                "reps": len(case_runs),
                "validate": "cache_hit" if name == "cached_ttft_long" else None,
            }
        )

    normalized = {
        "schema_version": 1,
        "label": label,
        "timestamp": doc.get("timestamp"),
        "source": "legacy-import",
        "legacy_schema_version": 0,
        "imported_at": datetime.now(UTC).isoformat(),
        "imported_from": source,
        "engine": _legacy_engine(label, doc, engine),
        "model": {
            "id": summary.get("model"),
            "configured_id": engine.api_model if engine else None,
            "quantization": engine.quantization if engine else None,
            "context": summary.get("context"),
            "context_source": "legacy",
        },
        "suite": {
            "revision": 0,
            "note": (
                "Imported from the original jarvis/bench-llm harness. "
                "Cases and max_tokens differ from the current suite."
            ),
            "cases": suite_cases,
        },
        "machine": doc.get("machine") or {},
        "summary": summary,
        "validation": validation,
        "runs": runs,
    }
    return normalized


def load_legacy(path: Path, config: Config) -> dict:
    with path.open(encoding="utf-8") as handle:
        return normalize_legacy(json.load(handle), config, source=str(path))
