from __future__ import annotations

import json
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from bench.config import Engine
from bench.eval.runner import run_eval, summarize_eval
from bench.eval.settings import EvalSettings


class FakeServer(ThreadingHTTPServer):
    def server_bind(self) -> None:
        # HTTPServer.server_bind calls socket.getfqdn(), which can block on a
        # Mac with no reverse DNS for 127.0.0.1.
        socketserver.TCPServer.server_bind(self)
        self.server_name = self.server_address[0]
        self.server_port = self.server_address[1]


class FakeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            body = json.dumps({"data": [{"id": "fake-model", "context_length": 32768}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def event(payload: dict) -> None:
            self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
            self.wfile.flush()

        event({"choices": [{"delta": {"content": "hola mundo"}, "finish_reason": "stop"}]})
        event({"choices": [], "usage": {"prompt_tokens": 30, "completion_tokens": 2}})
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def _engine(port: int) -> Engine:
    return Engine(
        label="fake",
        name="Fake",
        base_url=f"http://127.0.0.1:{port}/v1",
        port=port,
        model="fake-model",
        api_model="fake-model",
        quantization="test",
        context_tokens=32768,
        proc_pattern="",
        conflicts=(),
        start=("true",),
        version_cmd=(),
    )


def test_run_eval_writes_a_schema_one_eval_document(tmp_path: Path) -> None:
    server = FakeServer(("127.0.0.1", 0), FakeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        out = tmp_path / "eval.json"
        path = run_eval(
            _engine(port),
            EvalSettings(needle_chars=2000, needle_long_chars=4000),
            label="fake-eval",
            out=out,
            safety=False,
            items=("math-tornillos",),
        )
    finally:
        server.shutdown()
        server.server_close()

    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["kind"] == "eval"
    assert document["schema_version"] == 1
    assert document["label"] == "fake-eval"
    assert document["summary"]["items"] == 1
    assert document["summary"]["passed"] == 0
    assert document["summary"]["errors"] == 0
    assert document["items"][0]["id"] == "math-tornillos"
    assert document["items"][0]["finish_reason"] == "stop"
    assert document["eval"]["revision"] == 3


def test_summary_flags_leaked_reasoning_when_thinking_is_off() -> None:
    records = [
        {
            "id": "math-tornillos",
            "category": "calculo",
            "passed": True,
            "total_ms": 1000.0,
            "reasoning_chunks": 4,
            "thinking_leaked": True,
            "finish_reason": "length",
        }
    ]
    summary = summarize_eval(records, thinking_expected=False)
    assert summary["thinking_leaked_items"] == ["math-tornillos"]
    assert summary["reasoning_chunks"] == 4
    assert summary["truncated"] == 1


def test_summary_does_not_flag_deliberate_thinking() -> None:
    records = [
        {
            "id": "math-tornillos",
            "category": "calculo",
            "passed": True,
            "total_ms": 1000.0,
            "reasoning_chunks": 4,
            "thinking_leaked": False,
        }
    ]
    summary = summarize_eval(records, thinking_expected=True)
    assert summary["thinking_leaked_items"] == []


def test_run_eval_can_declare_that_thinking_is_on(tmp_path: Path) -> None:
    server = FakeServer(("127.0.0.1", 0), FakeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        path = run_eval(
            _engine(port),
            EvalSettings(needle_chars=2000, needle_long_chars=4000),
            label="fake-thinking",
            out=tmp_path / "thinking.json",
            safety=False,
            items=("math-tornillos",),
            thinking_expected=True,
        )
    finally:
        server.shutdown()
        server.server_close()

    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["eval"]["thinking_expected"] is True
    assert document["summary"]["thinking_expected"] is True
