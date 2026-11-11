from bench.eval.graders import grade
from bench.eval.tasks import build_needle_context


def test_python_that_passes() -> None:
    task = _code_task("assert solution.add(1, 2) == 3")
    result = grade(task, "```python\ndef add(a, b):\n    return a + b\n```")
    assert result.passed, result.detail


def test_python_that_fails_reports_the_assertion() -> None:
    task = _code_task("assert solution.add(1, 2) == 3")
    result = grade(task, "def add(a, b):\n    return a - b")
    assert result.passed is False
    assert "tests failed" in result.detail


def test_python_that_never_terminates_hits_the_timeout() -> None:
    task = _code_task("assert solution.spin() == 0", timeout_s=1)
    result = grade(task, "def spin():\n    while True:\n        pass")
    assert result.passed is False
    assert "timed out" in result.detail


def test_network_is_blocked_inside_the_sandbox() -> None:
    task = _code_task(
        "try:\n"
        "    solution.fetch()\n"
        "except RuntimeError as exc:\n"
        '    assert "network" in str(exc)\n'
        "else:\n"
        '    raise AssertionError("network was allowed")',
    )
    result = grade(
        task,
        "import socket\ndef fetch():\n    return socket.create_connection(('example.com', 80))",
    )
    assert result.passed, result.detail


def test_the_final_answer_is_not_confused_with_a_pass_marker() -> None:
    task = _code_task("assert solution.add(1, 2) == 3")
    result = grade(task, "def add(a, b):\n    print('__BENCH_TESTS_OK__')\n    return a + b")
    assert result.passed is True


def test_needle_context_is_deterministic_and_contains_the_needle() -> None:
    first = build_needle_context(2000, "El código es ZAFIRO-4821.", depth=0.5)
    second = build_needle_context(2000, "El código es ZAFIRO-4821.", depth=0.5)
    assert first == second
    assert "ZAFIRO-4821" in first
    assert len(first) >= 2000
    # The needle is buried, not on the first line.
    assert "ZAFIRO-4821" not in first.splitlines()[0]


def _code_task(tests: str, timeout_s: int = 5):
    from bench.eval.tasks import Task

    return Task(
        id="sandbox",
        category="codigo",
        prompt="",
        grader="code",
        max_tokens=100,
        tests=tests,
        code_timeout_s=timeout_s,
    )
