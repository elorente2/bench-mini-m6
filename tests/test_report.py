from bench.report import METRICS, best_labels, format_value, render


def doc(label: str, **summary) -> dict:
    return {
        "label": label,
        "summary": summary,
        "model": {"id": f"model-{label}", "quantization": "Q4"},
        "engine": {"version": "1.0", "reasoning_effort": "disabled"},
        "validation": {},
    }


def test_best_labels_respects_direction() -> None:
    docs = [doc("a", decode_short_tps=60.0), doc("b", decode_short_tps=63.0)]
    metric = next(metric for metric in METRICS if metric.key == "decode_short_tps")
    assert best_labels(metric, docs) == {"b"}


def test_format_value_humanizes_units() -> None:
    ttft = next(metric for metric in METRICS if metric.key == "cold_ttft_long_ms")
    assert format_value(ttft, 34071.8) == "34.1 s"
    assert format_value(ttft, 163.3) == "163 ms"


def test_render_marks_winners_and_invalid_cases() -> None:
    splash = doc(
        "splash",
        decode_short_tps=56.1,
        decode_at_long_tps=37.8,
        prefill_long_tps=446.3,
        cold_ttft_long_ms=40617.4,
        cached_ttft_long_ms=163.3,
        wired_peak_gb=22.76,
        context=217081,
    )
    mirai = doc(
        "mirai",
        decode_short_tps=63.0,
        decode_at_long_tps=45.5,
        prefill_long_tps=532.1,
        cold_ttft_long_ms=34071.8,
        cached_ttft_long_ms=None,
        wired_peak_gb=19.71,
    )
    mirai["validation"] = {"cached_ttft_long": {"valid": False, "reasons": ["not a cache hit"]}}
    output = render([splash, mirai])
    assert "**63.0 tok/s**" in output
    assert "**34.1 s**" in output
    assert "not a cache hit" in output
    assert "Text and code" in output
    assert "Memory" in output
