from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class ChatResult:
    ttft_ms: float | None
    ttft_content_ms: float | None
    total_ms: float
    prompt_tokens: int | None
    completion_tokens: int | None
    completion_tokens_source: str
    content_chunks: int
    reasoning_chunks: int
    decode_tps: float | None
    prefill_tps: float | None
    finish_reason: str | None
    answer_preview: str
    answer_chars: int
    answer_sha256: str
    answer: str = ""
    tool_calls: list[dict] | None = None

    def as_dict(self) -> dict:
        data = {
            "ttft_ms": self.ttft_ms,
            "ttft_content_ms": self.ttft_content_ms,
            "total_ms": self.total_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "completion_tokens_source": self.completion_tokens_source,
            "content_chunks": self.content_chunks,
            "reasoning_chunks": self.reasoning_chunks,
            "decode_tps": self.decode_tps,
            "prefill_tps": self.prefill_tps,
            "finish_reason": self.finish_reason,
            "answer_preview": self.answer_preview,
            "answer_chars": self.answer_chars,
            "answer_sha256": self.answer_sha256,
        }
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        return data


class ChatClient:
    """Minimal OpenAI-compatible streaming client.

    The client only needs the standard library so the benchmark can run on a
    fresh macOS install. It degrades gracefully when an engine rejects optional
    fields such as ``reasoning_effort``, ``seed``, ``stream_options`` or
    ``max_tokens``. ``chat_template_kwargs`` is deliberately not dropped on
    rejection: silently ignoring it could leave reasoning enabled and make the
    comparison unfair.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        reasoning_effort: str | None,
        *,
        timeout: int = 1200,
        seed: int | None = 0,
        chat_template_kwargs: dict | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout = timeout
        self.seed = seed
        self.chat_template_kwargs = dict(chat_template_kwargs or {})

    def _post(self, payload: dict):
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            method="POST",
        )
        return urllib.request.urlopen(request, timeout=self.timeout)

    def _post_with_fallback(self, payload: dict):
        for _ in range(6):
            try:
                return self._post(payload)
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "replace")
                changed = False
                if payload.get("reasoning_effort") is not None and "reasoning" in body.lower():
                    print(
                        f"  ! reasoning_effort={payload['reasoning_effort']!r} rejected; "
                        "retrying without it",
                        file=sys.stderr,
                    )
                    payload.pop("reasoning_effort", None)
                    self.reasoning_effort = None
                    changed = True
                elif "max_completion_tokens" in body and "max_tokens" in payload:
                    payload["max_completion_tokens"] = payload.pop("max_tokens")
                    changed = True
                elif "stream_options" in body and "stream_options" in payload:
                    payload.pop("stream_options", None)
                    changed = True
                elif "seed" in body.lower() and "seed" in payload:
                    payload.pop("seed", None)
                    changed = True
                if not changed:
                    raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        raise RuntimeError("server rejected the request after every compatibility fallback")

    def stream_chat(self, prompt: str, max_tokens: int) -> ChatResult:
        return self.stream_messages([{"role": "user", "content": prompt}], max_tokens)

    def stream_messages(
        self,
        messages: list[dict],
        max_tokens: int,
        tools: list[dict] | None = None,
    ) -> ChatResult:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        if self.chat_template_kwargs:
            payload["chat_template_kwargs"] = dict(self.chat_template_kwargs)
        if self.seed is not None:
            payload["seed"] = self.seed

        start = time.perf_counter()
        response = self._post_with_fallback(payload)

        first_any: float | None = None
        first_content: float | None = None
        last_any: float | None = None
        content_chunks = 0
        reasoning_chunks = 0
        finish_reason: str | None = None
        content: list[str] = []
        reasoning: list[str] = []
        tool_calls: dict[int, dict] = {}
        usage: dict = {}

        with response:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if event.get("usage"):
                    usage = event["usage"]
                for choice in event.get("choices") or []:
                    delta = choice.get("delta") or {}
                    now = time.perf_counter()
                    reasoning_piece = delta.get("reasoning_content") or delta.get("reasoning")
                    if reasoning_piece:
                        reasoning_chunks += 1
                        reasoning.append(reasoning_piece)
                        if first_any is None:
                            first_any = now
                        last_any = now
                    piece = delta.get("content")
                    if piece:
                        content_chunks += 1
                        content.append(piece)
                        if first_any is None:
                            first_any = now
                        if first_content is None:
                            first_content = now
                        last_any = now
                    for call in delta.get("tool_calls") or []:
                        index = int(call.get("index", len(tool_calls)))
                        slot = tool_calls.setdefault(
                            index,
                            {
                                "id": None,
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            },
                        )
                        if call.get("id"):
                            slot["id"] = call["id"]
                        function = call.get("function") or {}
                        if function.get("name"):
                            slot["function"]["name"] = function["name"]
                        if function.get("arguments"):
                            slot["function"]["arguments"] += function["arguments"]
                        if first_any is None:
                            first_any = now
                        last_any = now
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]

        end = time.perf_counter()
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        token_source = "usage" if completion_tokens else "chunk-count"
        if not completion_tokens:
            completion_tokens = content_chunks + reasoning_chunks

        ttft = (first_any - start) if first_any is not None else None
        ttft_content = (first_content - start) if first_content is not None else None
        prefill_tps = None
        if prompt_tokens and ttft and ttft > 0:
            prefill_tps = prompt_tokens / ttft
        decode_tps = None
        if completion_tokens > 1 and first_any is not None and last_any is not None:
            elapsed = last_any - first_any
            if elapsed > 0:
                decode_tps = (completion_tokens - 1) / elapsed

        answer = "".join(content) if content else "".join(reasoning)
        digest = hashlib.sha256(answer.encode("utf-8", "replace")).hexdigest()

        return ChatResult(
            ttft_ms=round(ttft * 1000, 1) if ttft is not None else None,
            ttft_content_ms=round(ttft_content * 1000, 1) if ttft_content is not None else None,
            total_ms=round((end - start) * 1000, 1),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            completion_tokens_source=token_source,
            content_chunks=content_chunks,
            reasoning_chunks=reasoning_chunks,
            decode_tps=round(decode_tps, 2) if decode_tps is not None else None,
            prefill_tps=round(prefill_tps, 2) if prefill_tps is not None else None,
            finish_reason=finish_reason,
            answer_preview=answer[:160].replace("\n", " "),
            answer_chars=len(answer),
            answer_sha256=digest,
            answer=answer,
            tool_calls=[tool_calls[index] for index in sorted(tool_calls)] or None,
        )


def get_models(base_url: str) -> dict:
    request = urllib.request.Request(base_url.rstrip("/") + "/models")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def pick_model(models: dict, wanted: str | None) -> tuple[str, dict]:
    data = models.get("data") or models.get("models") or []
    if not data:
        raise RuntimeError("server returned no models")
    if wanted:
        for item in data:
            if wanted in (item.get("id"), item.get("name")):
                return wanted, item
        for item in data:
            identifier = item.get("id") or item.get("name") or ""
            if wanted in identifier or identifier in wanted:
                return identifier, item
        offered = ", ".join(str(item.get("id") or item.get("name")) for item in data)
        raise RuntimeError(f"model {wanted!r} not found; server offers: {offered}")
    item = data[0]
    identifier = item.get("id") or item.get("name")
    if not identifier:
        raise RuntimeError("server advertised a model without an id")
    return identifier, item
