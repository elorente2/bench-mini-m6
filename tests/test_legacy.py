from pathlib import Path

from bench.config import load_config
from bench.legacy import normalize_legacy

ROOT = Path(__file__).resolve().parent.parent


def legacy_doc(label: str, cached_ttft: float) -> dict:
    return {
        "label": label,
        "timestamp": "2026-11-05T20:00:00+00:00",
        "base_url": "http://127.0.0.1:8000/v1",
        "reasoning_effort": "none",
        "machine": {"chip": "Apple M6"},
        "summary": {
            "model": "model",
            "context": 18000,
            "decode_short_tps": 60.0,
            "prefill_long_tps": 500.0,
            "cold_ttft_long_ms": 34000.0,
            "cached_ttft_long_ms": cached_ttft,
        },
        "runs": [
            {
                "case": "prefill_cold_long",
                "prompt_tokens": 18000,
                "ttft_ms": 34000.0,
                "completion_tokens": 8,
            },
            {
                "case": "cached_ttft_long",
                "prompt_tokens": 18000,
                "ttft_ms": cached_ttft,
                "completion_tokens": 8,
            },
        ],
    }


def test_legacy_import_keeps_a_valid_cache_hit() -> None:
    config = load_config(ROOT / "config")
    normalized = normalize_legacy(legacy_doc("splash", 163.0), config)
    assert normalized["schema_version"] == 1
    assert normalized["summary"]["cached_ttft_long_ms"] == 163.0
    assert normalized["validation"]["cached_ttft_long"]["valid"] is True


def test_legacy_import_invalidates_a_reprefill() -> None:
    config = load_config(ROOT / "config")
    normalized = normalize_legacy(legacy_doc("mirai", 33900.0), config)
    assert normalized["summary"]["cached_ttft_long_ms"] is None
    assert normalized["summary"]["reported_cached_ttft_long_ms"] == 33900.0
    assert normalized["validation"]["cached_ttft_long"]["valid"] is False
