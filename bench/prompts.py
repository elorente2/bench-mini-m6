from __future__ import annotations

SHORT_PROMPT = (
    "Write a Python function merge_intervals(intervals) that merges "
    "overlapping closed intervals and returns them sorted. Include a short "
    "docstring and three doctests. Output only the code."
)

LONG_INSTRUCTION = "Reply with the single word READY and nothing else."

CACHED_ASSISTANT = "READY"

FOLLOW_UP = (
    "Now write a Python module of at least 100 lines implementing an LRU cache: "
    "a doubly linked list, get/put in O(1), type hints, docstrings and three "
    "doctests. Output only code."
)


def build_long_context(target_chars: int = 32000) -> str:
    """Build a deterministic block of Python used as a long user prefix."""

    lines: list[str] = []
    size = 0
    index = 0
    while size < target_chars:
        line = (
            f"def helper_{index:05d}(x): "
            f"return (x * {index % 97} + {index % 31}) % {index % 13 + 1}"
        )
        lines.append(line)
        size += len(line) + 1
        index += 1
    body = "\n".join(lines)
    return (
        f"The following Python file is context only; do not summarize it.\n\n```python\n{body}\n```"
    )


def build_long_prompt(target_chars: int = 32000) -> str:
    """Single-message long prompt, kept for backwards-compatible tooling."""

    return f"{build_long_context(target_chars)}\n\n{LONG_INSTRUCTION}"


def messages_for(name: str, *, prefill_target_chars: int = 32000) -> list[dict]:
    """Return the chat messages for a suite case.

    ``long`` is the cold prefill: one long user message plus the task.
    ``long_cached`` extends that exact prefix with a fixed assistant turn and a
    follow-up question, so a prefix-cache hit only has to prefill the extension.
    """

    if name == "short":
        return [{"role": "user", "content": SHORT_PROMPT}]
    context = build_long_context(prefill_target_chars)
    long_prompt = f"{context}\n\n{LONG_INSTRUCTION}"
    if name == "long":
        return [{"role": "user", "content": long_prompt}]
    if name == "long_cached":
        return [
            {"role": "user", "content": long_prompt},
            {"role": "assistant", "content": CACHED_ASSISTANT},
            {"role": "user", "content": FOLLOW_UP},
        ]
    raise ValueError(f"unknown prompt {name!r}; expected 'short', 'long' or 'long_cached'")
