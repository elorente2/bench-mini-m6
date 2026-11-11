from pathlib import Path

import pytest

from bench.config import ConfigError
from bench.eval.settings import EvalSettings, load_eval_settings
from bench.eval.tasks import CATEGORIES, build_tasks

ROOT = Path(__file__).resolve().parent.parent


def test_eval_config_is_loadable() -> None:
    settings = load_eval_settings(ROOT / "config" / "eval.toml")
    assert settings.revision == 5
    assert settings.reasoning_headroom > 0
    assert settings.needle_long_chars > settings.needle_chars
    assert settings.code_timeout_s > 0


def test_reasoning_headroom_raises_every_item_budget() -> None:
    base = build_tasks(EvalSettings())
    roomy = build_tasks(EvalSettings(reasoning_headroom=100))
    assert [task.id for task in base] == [task.id for task in roomy]
    assert all(new.max_tokens == old.max_tokens + 100 for old, new in zip(base, roomy, strict=True))


def test_eval_config_rejects_a_short_long_needle(tmp_path: Path) -> None:
    path = tmp_path / "eval.toml"
    path.write_text(
        "[eval]\nrevision = 1\nneedle_chars = 9000\nneedle_long_chars = 8000\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="needle_long_chars"):
        load_eval_settings(path)


def test_the_pilot_has_the_planned_items() -> None:
    settings = load_eval_settings(ROOT / "config" / "eval.toml")
    tasks = build_tasks(settings)
    assert len(tasks) == 20
    assert len({task.id for task in tasks}) == len(tasks)
    assert {task.category for task in tasks} == set(CATEGORIES)
    assert all(task.prompt.strip() for task in tasks)
    assert all(task.max_tokens > 0 for task in tasks)


def test_every_grader_has_what_it_needs() -> None:
    settings = load_eval_settings(ROOT / "config" / "eval.toml")
    for task in build_tasks(settings):
        if task.grader == "exact":
            assert task.expect, task.id
        elif task.grader == "regex":
            assert task.pattern, task.id
        elif task.grader == "json":
            assert task.schema, task.id
        elif task.grader == "tool":
            assert task.tools and task.tool_expect, task.id
        elif task.grader == "code":
            assert task.tests, task.id
        elif task.grader == "kv":
            assert task.expect_kv, task.id
        elif task.grader == "parts":
            assert task.parts, task.id
        elif task.grader == "sections":
            assert task.sections, task.id


def test_needle_items_bury_their_code() -> None:
    settings = load_eval_settings(ROOT / "config" / "eval.toml")
    needles = [task for task in build_tasks(settings) if task.category == "contexto_largo"]
    assert len(needles) == 2
    for task in needles:
        code = task.expect[0]
        assert code in task.prompt
        assert task.prompt.index(code) > 1000
        assert task.metadata["context_chars"] > settings.needle_chars


def test_task_order_and_prompts_are_deterministic() -> None:
    settings = load_eval_settings(ROOT / "config" / "eval.toml")
    first = build_tasks(settings)
    second = build_tasks(settings)
    assert [task.id for task in first] == [task.id for task in second]
    assert [task.prompt for task in first] == [task.prompt for task in second]
