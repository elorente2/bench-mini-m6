from bench.client import pick_model


def test_pick_model_exact_match() -> None:
    models = {"data": [{"id": "a"}, {"id": "b"}]}
    assert pick_model(models, "b")[0] == "b"


def test_pick_model_falls_back_to_first() -> None:
    models = {"data": [{"id": "first"}]}
    assert pick_model(models, None)[0] == "first"


def test_pick_model_accepts_substring() -> None:
    models = {"data": [{"id": "unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL"}]}
    assert pick_model(models, "Qwen3.8-27B")[0].startswith("unsloth/")
