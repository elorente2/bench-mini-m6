from bench.validation import summarize_runs, validate_cache_hit


def run(prompt_tokens: int, ttft_ms: float) -> dict:
    return {"prompt_tokens": prompt_tokens, "ttft_ms": ttft_ms}


def test_cache_hit_accepts_a_prefix_extension() -> None:
    result = validate_cache_hit(run(18000, 34000), run(18100, 180))
    assert result["valid"] is True
    assert result["reasons"] == []


def test_cache_hit_rejects_lost_prefix() -> None:
    result = validate_cache_hit(run(18000, 34000), run(17900, 180))
    assert result["valid"] is False
    assert "lost prompt tokens" in result["reasons"][0]


def test_cache_hit_rejects_a_reprefill() -> None:
    result = validate_cache_hit(run(18000, 34000), run(18100, 33900))
    assert result["valid"] is False
    assert "cached TTFT" in result["reasons"][0]


def test_summary_excludes_an_invalid_cache_run() -> None:
    grouped = {
        "decode_short": [{"decode_tps": 60.0}, {"decode_tps": 62.0}],
        "prefill_cold_long": [{"prompt_tokens": 18000, "ttft_ms": 34000, "prefill_tps": 530}],
        "cached_ttft_long": [{"prompt_tokens": 18000, "ttft_ms": 33000}],
        "decode_at_long": [{"decode_tps": 45.0}],
    }
    validation = {
        "decode_short": {"valid": True, "reasons": []},
        "prefill_cold_long": {"valid": True, "reasons": []},
        "cached_ttft_long": {"valid": False, "reasons": ["not a cache hit"]},
        "decode_at_long": {"valid": True, "reasons": []},
    }
    summary = summarize_runs(
        grouped,
        validation,
        peak_rss_mb=15000.0,
        wired_before_gb=2.0,
        wired_peak_gb=19.0,
        wired_after_gb=19.0,
        rss_samples=10,
    )
    assert summary["decode_short_tps"] == 61.0
    assert summary["cached_ttft_long_ms"] is None
    assert summary["reported_cached_ttft_long_ms"] == 33000
    assert summary["invalid_cases"] == ["cached_ttft_long"]
