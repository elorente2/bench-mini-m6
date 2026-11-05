from bench.prompts import build_long_context, messages_for


def test_long_cached_extends_the_exact_cold_prefix() -> None:
    cold = messages_for("long", prefill_target_chars=2000)
    cached = messages_for("long_cached", prefill_target_chars=2000)
    assert cached[:1] == cold
    assert [message["role"] for message in cached] == [
        "user",
        "assistant",
        "user",
    ]


def test_long_context_is_deterministic_and_large_enough() -> None:
    first = build_long_context(5000)
    second = build_long_context(5000)
    assert first == second
    assert len(first) >= 5000
