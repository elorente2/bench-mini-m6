from pathlib import Path

from bench.config import load_config

ROOT = Path(__file__).resolve().parent.parent


def test_config_loads_the_three_contenders() -> None:
    config = load_config(ROOT / "config")
    assert set(config.engines) == {
        "splash",
        "mirai",
        "ollama-q3kxl",
        "ollama-default",
    }
    assert config.engines["splash"].port == 8000
    assert config.engines["mirai"].reasoning_effort == "disabled"
    assert config.engines["ollama-default"].persistent is True


def test_cache_case_is_an_extension() -> None:
    config = load_config(ROOT / "config")
    cached = config.suite.case("cached_ttft_long")
    assert cached.validate == "cache_hit"
    assert cached.compare_to == "prefill_cold_long"
    assert cached.prompt == "long_cached"
    assert cached.max_tokens >= 32
