from bench.eval.report import gate_problems, render_eval_report
from bench.eval.tasks import CATEGORIES


def make_doc(
    label: str,
    *,
    accuracy: float,
    leaked: tuple[str, ...] = (),
    errors: int = 0,
    revision: int = 1,
    items: tuple[tuple[str, bool], ...] = (),
) -> dict:
    by_category = {
        category: {
            "items": 1,
            "passed": 1 if accuracy >= 1 else 0,
            "accuracy": 1.0 if accuracy >= 1 else accuracy,
        }
        for category in CATEGORIES
    }
    return {
        "label": label,
        "model": {"id": f"model-{label}", "quantization": "4-bit"},
        "engine": {"name": "Fake", "version": "1.0"},
        "eval": {"revision": revision, "thinking_expected": False},
        "machine": {"model": "Mac mini M6", "memory_gb": 32.0},
        "summary": {
            "items": 21,
            "passed": 17,
            "accuracy": accuracy,
            "errors": errors,
            "by_category": by_category,
            "thinking_leaked_items": list(leaked),
            "total_ms": 600000,
            "slowest_ms": 90000,
            "prompt_tokens_max": 20000,
        },
        "items": [
            {"id": item_id, "category": "json", "passed": passed} for item_id, passed in items
        ],
    }


def test_report_renders_a_category_table_and_a_decision() -> None:
    docs = [
        make_doc("fast", accuracy=1.0),
        make_doc("slow", accuracy=0.5),
    ]
    report = render_eval_report(docs)
    assert "## Acierto por categoría" in report
    assert "## Decisión por tarea" in report
    assert "`fast`" in report
    assert "100 %" in report


def test_revision_mismatch_is_flagged() -> None:
    report = render_eval_report(
        [make_doc("a", accuracy=1.0), make_doc("b", accuracy=1.0, revision=2)]
    )
    assert "revisiones distintas" in report


def test_gates_flag_errors_and_leaked_reasoning() -> None:
    assert gate_problems(make_doc("ok", accuracy=1.0)) == []
    assert gate_problems(make_doc("bad", accuracy=1.0, errors=2))
    assert gate_problems(make_doc("leak", accuracy=1.0, leaked=("needle-24k",)))


def test_items_every_run_passes_are_listed_for_pruning() -> None:
    docs = [
        make_doc("a", accuracy=1.0, items=(("json-pedido", True), ("json-articulos", False))),
        make_doc("b", accuracy=1.0, items=(("json-pedido", True), ("json-articulos", True))),
    ]
    report = render_eval_report(docs)
    assert "## Ítems que no discriminan" in report
    assert "`json-pedido`" in report
    assert "`json-articulos`" not in report.split("## Ítems que no discriminan")[1]


def test_single_document_still_renders() -> None:
    report = render_eval_report([make_doc("only", accuracy=0.8)])
    assert "No hay ejecuciones válidas todavía" not in report
    assert "`only`" in report
