import pytest

from bench.client import ChatClient, pick_model


def test_pick_model_exact_match() -> None:
    models = {"data": [{"id": "a"}, {"id": "b"}]}
    assert pick_model(models, "b")[0] == "b"


def test_pick_model_falls_back_to_first() -> None:
    models = {"data": [{"id": "first"}]}
    assert pick_model(models, None)[0] == "first"


def test_pick_model_accepts_substring() -> None:
    models = {"data": [{"id": "unsloth/Qwen3.8-27B-GGUF:UD-Q3_K_XL"}]}
    assert pick_model(models, "Qwen3.8-27B")[0].startswith("unsloth/")


def _capture_payload(monkeypatch, client: ChatClient) -> dict:
    captured: dict = {}

    def fake_post(payload: dict):
        captured.update(payload)
        raise RuntimeError("no network in this test")

    monkeypatch.setattr(client, "_post", fake_post)
    with pytest.raises(RuntimeError, match="no network"):
        client.stream_messages([{"role": "user", "content": "hi"}], 8)
    return captured


def test_chat_template_kwargs_are_sent_when_configured(monkeypatch) -> None:
    client = ChatClient(
        "http://127.0.0.1:9/v1",
        "model",
        "none",
        chat_template_kwargs={"enable_thinking": False},
    )
    payload = _capture_payload(monkeypatch, client)
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["reasoning_effort"] == "none"
    assert payload["temperature"] == 0


def test_chat_template_kwargs_are_absent_by_default(monkeypatch) -> None:
    client = ChatClient("http://127.0.0.1:9/v1", "model", "none")
    payload = _capture_payload(monkeypatch, client)
    assert "chat_template_kwargs" not in payload
