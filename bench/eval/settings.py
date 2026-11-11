from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from ..config import ConfigError


@dataclass(frozen=True)
class EvalSettings:
    revision: int = 3
    max_tokens: int = 640
    code_timeout_s: int = 5
    seed: int = 0
    # Extra answer budget added to every item so a thinking model can reason
    # and still reach an answer. It is part of the contract: changing it is a
    # revision change.
    reasoning_headroom: int = 0
    needle_chars: int = 24000
    needle_long_chars: int = 64000


def load_eval_settings(path: Path | str) -> EvalSettings:
    source = Path(path)
    with source.open("rb") as handle:
        data = tomllib.load(handle)
    table = data.get("eval")
    if not isinstance(table, dict):
        raise ConfigError(f"{source} has no [eval] table")

    values = {
        "revision": table.get("revision", 3),
        "max_tokens": table.get("max_tokens", 640),
        "code_timeout_s": table.get("code_timeout_s", 5),
        "seed": table.get("seed", 0),
        "reasoning_headroom": table.get("reasoning_headroom", 0),
        "needle_chars": table.get("needle_chars", 24000),
        "needle_long_chars": table.get("needle_long_chars", 64000),
    }
    for key, value in values.items():
        if not isinstance(value, int):
            raise ConfigError(f"[eval].{key} must be an integer")
        if key == "seed":
            continue
        if key == "reasoning_headroom":
            if value < 0:
                raise ConfigError("[eval].reasoning_headroom must not be negative")
            continue
        if value <= 0:
            raise ConfigError(f"[eval].{key} must be positive")
    if values["needle_long_chars"] <= values["needle_chars"]:
        raise ConfigError("[eval].needle_long_chars must be larger than needle_chars")
    return EvalSettings(**values)
