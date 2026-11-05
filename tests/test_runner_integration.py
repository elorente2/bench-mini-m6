from __future__ import annotations

import json
import socketserver
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bench.config import Engine, Suite, SuiteCase
from bench.runner import run_pass


class FakeServer(ThreadingHTTPServer):
    def server_bind(self) -> None:
        # HTTPServer.server_bind calls socket.getfqdn(), which can block for
        # tens of seconds on a Mac with no reverse DNS for 127.0.0.1.
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

        event({"choices": [{"delta": {"content": "hello"}, "finish_reason": None}]})
        time.sleep(0.01)
        event({"choices": [{"delta": {"content": " world"}, "finish_reason": "stop"}]})
        event({"choices": [], "usage": {"prompt_tokens": 100, "completion_tokens": 2}})
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def test_run_pass_writes_schema_one_result(tmp_path) -> None:
    server = FakeServer(("127.0.0.1", 0), FakeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        engine = Engine(
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
        suite = Suite(
            cases=(SuiteCase(name="decode_short", prompt="short", max_tokens=2, reps=1),),
            prefill_target_chars=1000,
            warmup_max_tokens=1,
        )
        out = tmp_path / "fake.json"
        run_pass(engine, suite, out=out, safety=False, timeout=30)

        document = json.loads(out.read_text())
        assert document["schema_version"] == 1
        assert document["label"] == "fake"
        assert document["model"]["id"] == "fake-model"
        assert document["summary"]["decode_short_tps"] is not None
        assert document["summary"]["decode_short_tps"] > 0
        assert document["runs"][0]["answer_preview"] == "hello world"
        assert document["runs"][0]["prompt_tokens"] == 100
        assert document["validation"]["decode_short"]["valid"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
