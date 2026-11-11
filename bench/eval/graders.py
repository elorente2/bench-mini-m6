from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

FENCED_CODE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)
JSON_FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class Grade:
    """Result of grading one answer.

    ``detail`` is written to the result file and must be short and factual, so a
    reader can tell why an item failed without rerunning the model.
    """

    passed: bool
    detail: str
    extracted: str | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text


def loose(text: str) -> str:
    """Comparison form: NFKC, no diacritics, single spaces, lowercase.

    ``Facturación`` and ``facturacion`` are the same answer for grading; the
    raw answer stays in the result file, so the transformation is auditable.
    """

    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return normalize(stripped)


def alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", loose(text))


def extract_code(answer: str) -> str:
    match = FENCED_CODE.search(answer)
    return match.group(1).strip() if match else answer.strip()


def extract_json(answer: str) -> str:
    fenced = JSON_FENCE.search(answer)
    if fenced:
        return fenced.group(1).strip()
    stripped = answer.strip()
    if stripped.startswith(("{", "[")) and stripped.endswith(("}", "]")):
        return stripped
    start = min(
        (index for index in (stripped.find("{"), stripped.find("[")) if index >= 0),
        default=-1,
    )
    end = max(stripped.rfind("}"), stripped.rfind("]"))
    if start >= 0 and end > start:
        return stripped[start : end + 1]
    return stripped


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unknown schema type {expected!r}")


def validate_schema(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Small JSON Schema subset: enough for the eval suite, no dependency."""

    errors: list[str] = []
    expected = schema.get("type")
    if expected and not _type_ok(value, expected):
        return [f"{path}: expected {expected}, got {type(value).__name__}"]
    if "enum" in schema:
        allowed = {loose(str(item)) for item in schema["enum"]}
        if loose(str(value)) not in allowed:
            errors.append(f"{path}: {value!r} not in enum {schema['enum']}")
    if expected == "object":
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing key {key!r}")
        properties = schema.get("properties") or {}
        for key, item in value.items():
            if key in properties:
                errors.extend(validate_schema(item, properties[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected key {key!r}")
    if expected == "array":
        items = schema.get("items")
        if items:
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, items, f"{path}[{index}]"))
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than {schema['maxItems']} items")
    return errors


def _match_text(expected: str, answer: str, compare: str) -> bool:
    if compare == "alnum":
        return alnum(expected) == alnum(answer)
    stripped = " .,;:!?¡¿\"'"
    return loose(expected).strip(stripped) == loose(answer).strip(stripped)


def _grade_exact(task, answer: str) -> Grade:
    compare = getattr(task, "compare", "text")
    accepted = tuple(getattr(task, "expect", ()))
    if not accepted:
        raise ValueError(f"task {task.id} has no expected answers")
    for candidate in accepted:
        if _match_text(candidate, answer, compare):
            return Grade(True, f"matched {candidate!r}", answer[:120])
    return Grade(
        False,
        f"answer {normalize(answer)[:80]!r} did not match any accepted value",
        answer[:120],
    )


def _grade_regex(task, answer: str) -> Grade:
    pattern = getattr(task, "pattern", None)
    if not pattern:
        raise ValueError(f"task {task.id} has no regex pattern")
    if re.search(pattern, answer, re.IGNORECASE | re.DOTALL):
        return Grade(True, f"matched /{pattern}/", answer[:120])
    return Grade(
        False, f"answer {normalize(answer)[:80]!r} did not match /{pattern}/", answer[:120]
    )


def _grade_json(task, answer: str) -> Grade:
    schema = getattr(task, "schema", None)
    if not schema:
        raise ValueError(f"task {task.id} has no schema")
    raw = extract_json(answer)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return Grade(False, f"invalid JSON: {exc.msg}", raw[:160])
    errors = validate_schema(value, schema)
    if errors:
        return Grade(False, "; ".join(errors[:4]), raw[:160], tuple(errors))
    expected = getattr(task, "expect_json", None)
    if expected is not None and not json_equal(value, expected):
        return Grade(
            False,
            f"values differ from {json.dumps(expected, ensure_ascii=False)[:140]}",
            raw[:160],
        )
    return Grade(True, "schema and values valid", raw[:160])


def json_equal(value: Any, expected: Any) -> bool:
    """Compare JSON values leniently for strings and numbers, strictly for structure."""

    if isinstance(expected, dict):
        return (
            isinstance(value, dict)
            and set(expected) <= set(value)
            and all(json_equal(value[key], expected[key]) for key in expected)
        )
    if isinstance(expected, list):
        return (
            isinstance(value, list)
            and len(value) == len(expected)
            and all(json_equal(item, wanted) for item, wanted in zip(value, expected, strict=True))
        )
    if isinstance(expected, bool):
        return value is expected
    if isinstance(expected, (int, float)):
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and abs(float(value) - float(expected)) <= 0.01
        )
    if isinstance(expected, str):
        return isinstance(value, str) and loose(value) == loose(expected)
    return value == expected


def _grade_tool(task, answer: str, calls=()) -> Grade:
    expected = getattr(task, "tool_expect", None)
    if not expected:
        raise ValueError(f"task {task.id} has no expected tool call")
    if not calls:
        if answer.strip():
            return Grade(False, "answered in text instead of calling a tool", answer[:120])
        return Grade(False, "no tool call and no text", None)
    first = calls[0]
    function = first.get("function") or {}
    name = function.get("name") or first.get("name") or ""
    raw_arguments = function.get("arguments") or first.get("arguments") or "{}"
    try:
        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    except json.JSONDecodeError:
        return Grade(
            False, f"tool arguments are not JSON: {raw_arguments[:80]!r}", raw_arguments[:160]
        )
    if name != expected["name"]:
        return Grade(False, f"first call was {name!r}, expected {expected['name']!r}", name)
    problems: list[str] = []
    for key, wanted in (expected.get("arguments") or {}).items():
        if key not in arguments:
            problems.append(f"missing argument {key!r}")
            continue
        got = arguments[key]
        if isinstance(wanted, str) and isinstance(got, str):
            if normalize(wanted) not in normalize(got):
                problems.append(f"{key}={got!r} does not contain {wanted!r}")
        elif got != wanted:
            problems.append(f"{key}={got!r}, expected {wanted!r}")
    if problems:
        return Grade(False, "; ".join(problems), json.dumps(arguments)[:160])
    return Grade(True, f"{name} with the expected arguments", json.dumps(arguments)[:160])


def _grade_bullets(task, answer: str) -> Grade:
    prefix = getattr(task, "prefix", "- ")
    count = getattr(task, "count", None)
    min_words = getattr(task, "min_words", 1)
    lines = [line.strip() for line in answer.strip().splitlines() if line.strip()]
    if count is not None and len(lines) != count:
        return Grade(False, f"{len(lines)} non-empty lines, expected {count}", answer[:160])
    for index, line in enumerate(lines, start=1):
        if not line.startswith(prefix):
            return Grade(False, f"line {index} does not start with {prefix!r}", line[:80])
        if len(line[len(prefix) :].split()) < min_words:
            return Grade(False, f"line {index} is shorter than {min_words} words", line[:80])
    return Grade(True, f"{len(lines)} lines with the requested format", answer[:160])


def _grade_constraints(task, answer: str) -> Grade:
    text = normalize(answer)
    words = text.split()
    problems: list[str] = []
    if task.max_words is not None and len(words) > task.max_words:
        problems.append(f"{len(words)} words, maximum {task.max_words}")
    if task.min_words is not None and len(words) < task.min_words:
        problems.append(f"{len(words)} words, minimum {task.min_words}")
    for term in task.include:
        if normalize(term) not in text:
            problems.append(f"missing required term {term!r}")
    for term in task.exclude:
        if normalize(term) in text:
            problems.append(f"contains forbidden term {term!r}")
    if problems:
        return Grade(False, "; ".join(problems), answer[:160])
    return Grade(True, f"{len(words)} words, constraints met", answer[:160])


def parse_number(text: str) -> float:
    """Parse ``1.250,00`` and ``1250.00`` without guessing the decimal separator."""

    cleaned = re.sub(r"[^0-9,.\-]", "", text)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def _grade_kv(task, answer: str) -> Grade:
    expected = task.expect_kv or {}
    numeric = set(task.numeric_keys)
    seen: dict[str, str] = {}
    for line in answer.splitlines():
        line = line.strip().lstrip("-*").strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        seen[normalize(key).replace(" ", "_")] = value.strip()
    problems: list[str] = []
    for key, wanted in expected.items():
        if key not in seen:
            problems.append(f"missing key {key!r}")
            continue
        got = seen[key]
        if key in numeric:
            try:
                if abs(parse_number(got) - float(wanted)) > 0.01:
                    problems.append(f"{key}={got!r}, expected {wanted!r}")
            except ValueError:
                problems.append(f"{key}={got!r} is not a number")
        elif loose(got.strip(" .;")) != loose(wanted):
            problems.append(f"{key}={got!r}, expected {wanted!r}")
    extra = set(seen) - set(expected)
    if extra:
        problems.append(f"unexpected keys {sorted(extra)}")
    if problems:
        return Grade(False, "; ".join(problems[:4]), answer[:160])
    return Grade(True, "all fields extracted", answer[:160])


def _grade_parts(task, answer: str) -> Grade:
    separator = task.separator
    expected = tuple(task.parts or ())
    parts = [part.strip() for part in answer.strip().strip("`").split(separator)]
    if len(parts) != len(expected):
        return Grade(
            False,
            f"{len(parts)} parts separated by {separator!r}, expected {len(expected)}",
            answer[:160],
        )
    for index, (got, wanted) in enumerate(zip(parts, expected, strict=True), start=1):
        if not _match_text(wanted, got, task.compare):
            return Grade(False, f"part {index} is {got!r}, expected {wanted!r}", answer[:160])
    return Grade(True, "all parts matched", answer[:160])


def _grade_code(task, answer: str) -> Grade:
    from .sandbox import run_python_tests

    tests = getattr(task, "tests", None)
    if not tests:
        raise ValueError(f"task {task.id} has no tests")
    code = extract_code(answer)
    if not code.strip():
        return Grade(False, "empty answer", None)
    result = run_python_tests(code, tests, timeout_s=task.code_timeout_s)
    if result.passed:
        return Grade(True, f"tests passed in {result.duration_ms:.0f} ms", code[:160])
    if result.timed_out:
        detail = f"tests timed out after {task.code_timeout_s} s"
    else:
        tail = clear_failure(result.stderr)
        detail = f"tests failed: {tail}"
    return Grade(False, detail[:300], code[:160])


def clear_failure(stderr: str) -> str:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    if not lines:
        return "no stderr output"
    return " | ".join(lines[-3:])


def grade(task, answer: str, *, tool_calls=()) -> Grade:
    """Dispatch to the grader named by the task. Graders are pure functions."""

    kind = task.grader
    if kind == "exact":
        return _grade_exact(task, answer)
    if kind == "regex":
        return _grade_regex(task, answer)
    if kind == "json":
        return _grade_json(task, answer)
    if kind == "tool":
        return _grade_tool(task, answer, tool_calls)
    if kind == "bullets":
        return _grade_bullets(task, answer)
    if kind == "constraints":
        return _grade_constraints(task, answer)
    if kind == "kv":
        return _grade_kv(task, answer)
    if kind == "parts":
        return _grade_parts(task, answer)
    if kind == "code":
        return _grade_code(task, answer)
    raise ValueError(f"unknown grader {kind!r} on task {task.id}")
