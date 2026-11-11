from bench.eval.graders import (
    Grade,
    grade,
    normalize,
    parse_number,
    validate_schema,
)
from bench.eval.tasks import Task


def make(**kwargs) -> Task:
    base = {"id": "t", "category": "test", "prompt": "", "grader": "exact", "max_tokens": 32}
    return Task(**{**base, **kwargs})


def test_exact_accepts_an_accepted_answer() -> None:
    task = make(expect=("Diego",))
    assert grade(task, "Diego").passed
    assert grade(task, " diego. ").passed  # trailing punctuation is not a wrong answer
    assert grade(task, "Paula").passed is False


def test_exact_alnum_ignores_separators() -> None:
    task = make(expect=("ZAFIRO-4821",), compare="alnum")
    assert grade(task, "zafiro 4821").passed
    assert grade(task, "ZAFIRO-4822").passed is False


def test_regex_grader_anchors_the_answer() -> None:
    task = make(grader="regex", pattern=r"^\s*59\s*\.?\s*$")
    assert grade(task, "59").passed
    assert grade(task, "59 tornillos").passed is False


def test_json_grader_reports_schema_errors() -> None:
    task = make(
        grader="json",
        schema={
            "type": "object",
            "required": ["a", "b"],
            "properties": {"a": {"type": "integer"}, "b": {"type": "string"}},
            "additionalProperties": False,
        },
    )
    assert grade(task, '{"a": 1, "b": "x"}').passed
    assert grade(task, '{"a": "1", "b": "x"}').passed is False
    assert grade(task, '{"a": 1}').passed is False
    assert grade(task, '{"a": 1, "b": "x", "c": 2}').passed is False


def test_json_grader_accepts_a_fence_and_checks_values() -> None:
    task = make(
        grader="json",
        schema={"type": "object"},
        expect_json={"category": "facturacion", "urgent": True},
    )
    answer = '```json\n{"category": "Facturación", "urgent": true, "summary": "x"}\n```'
    result = grade(task, answer)
    assert result.passed, result.detail


def test_json_values_are_order_insensitive_but_arrays_are_not() -> None:
    schema = {"type": "object"}
    ordered = make(grader="json", schema=schema, expect_json={"items": [{"qty": 2}, {"qty": 1}]})
    assert grade(ordered, '{"items": [{"qty": 2}, {"qty": 1}]}').passed
    assert grade(ordered, '{"items": [{"qty": 1}, {"qty": 2}]}').passed is False


def test_tool_grader_needs_the_expected_call() -> None:
    task = make(
        grader="tool",
        tool_expect={"name": "get_weather", "arguments": {"city": "Valencia", "unit": "celsius"}},
    )
    good = [
        {
            "id": "1",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"city": "Valencia, España", "unit": "celsius"}',
            },
        }
    ]
    assert grade(task, "", tool_calls=good).passed
    wrong_name = [{"function": {"name": "search_notes", "arguments": "{}"}}]
    assert grade(task, "", tool_calls=wrong_name).passed is False
    wrong_unit = [
        {"function": {"name": "get_weather", "arguments": '{"city": "Valencia", "unit": "f"}'}}
    ]
    assert grade(task, "", tool_calls=wrong_unit).passed is False
    assert grade(task, "Hace 20 grados").passed is False


def test_bullets_grader_requires_exact_count_and_prefix() -> None:
    task = make(grader="bullets", count=3, prefix="- ", min_words=2)
    assert grade(task, "- uno dos\n- tres cuatro\n- cinco seis").passed
    assert grade(task, "- uno dos\n- tres cuatro").passed is False
    assert grade(task, "1. uno dos\n2. tres cuatro\n3. cinco seis").passed is False


def test_constraints_grader_counts_words_and_terms() -> None:
    task = make(grader="constraints", max_words=6, min_words=3, exclude=("túnel", "tunel"))
    assert grade(task, "Una red privada cifra el tráfico").passed
    assert grade(task, "Una red privada cifra el tráfico y crea un túnel cifrado").passed is False
    assert grade(task, "Una red").passed is False


def test_kv_grader_parses_numbers_in_both_formats() -> None:
    task = make(
        grader="kv",
        expect_kv={"nif": "B-12345678", "base": "1250.00", "iva": "262.50"},
        numeric_keys=("base", "iva"),
    )
    assert grade(task, "NIF: B-12345678\nBase: 1.250,00\nIVA: 262,50").passed
    assert grade(task, "NIF: B-12345678\nBase: 1250.00\nIVA: 262.50").passed
    assert grade(task, "NIF: B-12345678\nBase: 1249,00\nIVA: 262,50").passed is False
    assert (
        grade(task, "NIF: B-12345678\nBase: 1250,00\nIVA: 262,50\nTotal: 1512,50").passed is False
    )


def test_parts_grader_splits_on_the_separator() -> None:
    task = make(
        grader="parts",
        separator="|",
        parts=("17:30", "sala Magnolia", "Ana, Luis, Marta, Pablo"),
    )
    assert grade(task, "17:30 | sala Magnolia | Ana, Luis, Marta, Pablo").passed
    assert grade(task, "17:30 | Magnolia | Ana, Luis, Marta, Pablo").passed is False


def test_parse_number_handles_thousands_and_decimals() -> None:
    assert parse_number("1.250,00") == 1250.0
    assert parse_number("1250.00") == 1250.0
    assert parse_number("1,250.50") == 1250.5
    assert parse_number("89,5 €") == 89.5


def test_validate_schema_checks_enums_and_nested_items() -> None:
    schema = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "object", "properties": {"sku": {"type": "string"}}},
            }
        },
    }
    assert validate_schema({"items": [{"sku": "A"}]}, schema) == []
    errors = validate_schema({"items": []}, schema)
    assert any("fewer than 1" in error for error in errors)


def test_grade_is_a_pure_function_of_task_and_answer() -> None:
    first: Grade = grade(make(expect=("x",)), "x")
    second: Grade = grade(make(expect=("x",)), "x")
    assert first == second
    assert normalize("  Hola\nMundo ") == "hola mundo"
