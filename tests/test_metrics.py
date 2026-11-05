from bench.metrics import median


def test_median_ignores_missing_values() -> None:
    assert median([1.0, None, 3.0, 2.0]) == 2.0
    assert median([None, None]) is None
    assert median([]) is None


def test_median_keeps_two_decimals() -> None:
    assert median([1.234, 1.235, 1.236]) == 1.24
