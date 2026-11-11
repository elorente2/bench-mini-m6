from __future__ import annotations

from collections.abc import Iterable

from .metrics import median


def validate_cache_hit(cold: dict | None, cached: dict | None) -> dict:
    """Check that the second long-prompt request really reused the prefix.

    A cache hit requires the same prompt token count and a much lower TTFT.
    Without both checks an engine can report a cold prefill as a "cached"
    result, which is exactly how the first Mirai pass was invalidated.
    """

    reasons: list[str] = []
    if cold is None:
        reasons.append("cold long-prompt run is missing")
    if cached is None:
        reasons.append("cached long-prompt run is missing")

    cold_prompt = cold.get("prompt_tokens") if cold else None
    cached_prompt = cached.get("prompt_tokens") if cached else None
    if cold_prompt is None or cached_prompt is None:
        if cold is not None and cached is not None:
            reasons.append("prompt token count is missing on one of the runs")
    elif cached_prompt < cold_prompt:
        reasons.append(
            "cached request lost prompt tokens "
            f"({cold_prompt} -> {cached_prompt}); the server did not reuse the prefix"
        )

    cold_ttft = cold.get("ttft_ms") if cold else None
    cached_ttft = cached.get("ttft_ms") if cached else None
    cold_start_confirmed = True
    if cold_ttft is None or cached_ttft is None:
        if cold is not None and cached is not None:
            reasons.append("TTFT is missing on one of the runs")
        cold_start_confirmed = False
    elif cached_ttft >= cold_ttft * 0.5 and cached_ttft > 1000:
        reasons.append(
            f"cached TTFT ({cached_ttft:.0f} ms) is not meaningfully lower than "
            f"cold TTFT ({cold_ttft:.0f} ms)"
        )
        cold_start_confirmed = False

    return {
        "valid": not reasons,
        "reasons": reasons,
        "cold_start_confirmed": cold_start_confirmed,
    }


def group_runs(runs: Iterable[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for run in runs:
        grouped.setdefault(run["case"], []).append(run)
    return grouped


def validate_runs(grouped: dict[str, list[dict]], cases) -> dict[str, dict]:
    validation: dict[str, dict] = {}
    for case in cases:
        case_runs = grouped.get(case.name, [])
        if case.validate == "cache_hit":
            cold = (grouped.get(case.compare_to or "", []) or [None])[0]
            cached = (case_runs or [None])[0]
            result = validate_cache_hit(cold, cached)
            validation[case.name] = result
            # The pair proves a cold start together: if the second request was
            # not clearly faster, the first one was not cold either. That is how
            # an engine with a persisted prefix cache reports a fake prefill.
            if case.compare_to and not result.get("cold_start_confirmed", True):
                validation[case.compare_to] = {
                    "valid": False,
                    "reasons": [
                        "cold prefill looks cached: the cached turn was not clearly faster"
                    ],
                }
        else:
            validation[case.name] = {
                "valid": bool(case_runs),
                "reasons": [] if case_runs else ["case produced no runs"],
            }
    return validation


def summarize_runs(
    grouped: dict[str, list[dict]],
    validation: dict[str, dict],
    *,
    peak_rss_mb: float | None,
    wired_before_gb: float | None,
    wired_peak_gb: float | None,
    wired_after_gb: float | None,
    rss_samples: int,
) -> dict:
    def values(case_name: str, key: str) -> list[float | int | None]:
        return [run.get(key) for run in grouped.get(case_name, [])]

    cached_valid = validation.get("cached_ttft_long", {}).get("valid", False)
    cached_ttft = median(values("cached_ttft_long", "ttft_ms")) if cached_valid else None
    reported_cached = median(values("cached_ttft_long", "ttft_ms"))
    # New suites measure long-context decode in the cached extension run;
    # legacy results have a dedicated decode_at_long case.
    long_decode_runs = grouped.get("decode_at_long") or grouped.get("cached_ttft_long", [])
    invalid_cases = [name for name, result in validation.items() if not result.get("valid")]

    return {
        "decode_short_tps": median(values("decode_short", "decode_tps")),
        "decode_at_long_tps": median([run.get("decode_tps") for run in long_decode_runs]),
        "prefill_long_tps": median(values("prefill_cold_long", "prefill_tps")),
        "cold_ttft_long_ms": median(values("prefill_cold_long", "ttft_ms")),
        "cached_ttft_long_ms": cached_ttft,
        "reported_cached_ttft_long_ms": reported_cached,
        "peak_engine_rss_mb": peak_rss_mb,
        "wired_before_gb": wired_before_gb,
        "wired_peak_gb": wired_peak_gb,
        "wired_after_gb": wired_after_gb,
        "rss_samples": rss_samples,
        "invalid_cases": invalid_cases,
        "valid_cases": sorted(name for name, result in validation.items() if result.get("valid")),
    }
