from bench.engine import unload_other_ollama_models


def test_unload_other_ollama_models_keeps_the_target(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], timeout: int = 15) -> str:
        calls.append(cmd)
        if cmd[:2] == ["ollama", "ps"]:
            return (
                "NAME                 ID     SIZE   PROCESSOR   CONTEXT\n"
                "keep:latest          abc    12 GB  100% GPU    32768\n"
                "other:latest         def    18 GB  100% GPU    32768\n"
            )
        return ""

    monkeypatch.setattr("bench.engine.run_cmd", fake_run)
    monkeypatch.setattr("bench.engine.shutil.which", lambda name: "/usr/bin/ollama")

    unload_other_ollama_models("keep:latest")

    assert ["ollama", "stop", "other:latest"] in calls
    assert ["ollama", "stop", "keep:latest"] not in calls
