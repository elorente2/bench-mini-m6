from pathlib import Path

import pytest

from bench.config import ConfigError
from bench.vision.png import canvas, fill_circle, fill_rect, write_png
from bench.vision.report import render_vision_report
from bench.vision.settings import VisionSettings, load_vision_settings
from bench.vision.tasks import build_tasks

ROOT = Path(__file__).resolve().parent.parent


def test_png_has_the_signature_and_header() -> None:
    rows = canvas(8, 4)
    data = write_png(rows)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    # IHDR is the first chunk: length, tag, then width and height big-endian.
    assert data[12:16] == b"IHDR"
    assert int.from_bytes(data[16:20], "big") == 8
    assert int.from_bytes(data[20:24], "big") == 4


def test_the_same_drawing_encodes_to_the_same_bytes() -> None:
    first = canvas(32, 32)
    fill_rect(first, 4, 4, 20, 20, (200, 30, 30))
    second = canvas(32, 32)
    fill_rect(second, 4, 4, 20, 20, (200, 30, 30))
    assert write_png(first) == write_png(second)


def test_a_circle_is_painted_where_it_is_asked_for() -> None:
    rows = canvas(40, 40, (255, 255, 255))
    fill_circle(rows, 20, 20, 5, (0, 0, 0))
    assert rows[20][20] == (0, 0, 0)
    assert rows[0][0] == (255, 255, 255)


def test_vision_config_is_loadable() -> None:
    settings = load_vision_settings(ROOT / "config" / "vision.toml")
    assert settings.revision == 3
    assert settings.image_size >= 128


def test_vision_config_rejects_a_tiny_canvas(tmp_path: Path) -> None:
    path = tmp_path / "vision.toml"
    path.write_text("[vision]\nrevision = 1\nimage_size = 64\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="image_size"):
        load_vision_settings(path)


def test_the_suite_has_deterministic_images() -> None:
    settings = VisionSettings()
    first = build_tasks(settings)
    second = build_tasks(settings)
    assert len(first) == 8
    assert len({task.id for task in first}) == 8
    assert all(task.expect for task in first)
    assert [task.image for task in first] == [task.image for task in second]
    assert len({task.image_sha256 for task in first}) == 8


def test_a_report_shows_each_image_and_the_answer() -> None:
    tasks = build_tasks(VisionSettings())
    doc = {
        "label": "fake",
        "model": {"id": "m"},
        "engine": {"name": "Fake", "version": "1"},
        "vision": {
            "revision": 1,
            "image_size": 320,
            "items": [{"id": task.id, "image_sha256": task.image_sha256} for task in tasks],
        },
        "machine": {"chip": "Apple M6", "model": "Mac18,5", "memory_gb": 34.4},
        "summary": {"items": 4, "passed": 3, "accuracy": 0.75, "errors": 0},
        "items": [
            {
                "id": tasks[0].id,
                "passed": True,
                "extracted": "3",
                "image_sha256": tasks[0].image_sha256,
            },
            {
                "id": tasks[1].id,
                "passed": False,
                "extracted": "amarillo",
                "image_sha256": tasks[1].image_sha256,
            },
            {"id": tasks[2].id, "passed": True, "extracted": "derecha"},
            {"id": tasks[3].id, "passed": True, "extracted": "4"},
        ],
    }
    report = render_vision_report([doc])
    assert "Accuracy per image" in report
    assert "`vision-conteo`" in report
    assert "75 %" in report
    assert "amarillo" in report
