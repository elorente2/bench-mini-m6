from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from ..config import ConfigError


@dataclass(frozen=True)
class VisionSettings:
    revision: int = 1
    image_size: int = 320
    max_tokens: int = 32
    seed: int = 0


def load_vision_settings(path: Path | str) -> VisionSettings:
    source = Path(path)
    with source.open("rb") as handle:
        data = tomllib.load(handle)
    table = data.get("vision")
    if not isinstance(table, dict):
        raise ConfigError(f"{source} has no [vision] table")
    values = {
        "revision": table.get("revision", 1),
        "image_size": table.get("image_size", 320),
        "max_tokens": table.get("max_tokens", 32),
        "seed": table.get("seed", 0),
    }
    for key, value in values.items():
        if not isinstance(value, int):
            raise ConfigError(f"[vision].{key} must be an integer")
        if key == "seed":
            continue
        if value <= 0:
            raise ConfigError(f"[vision].{key} must be positive")
    if values["image_size"] < 128:
        raise ConfigError("[vision].image_size must be at least 128 pixels")
    return VisionSettings(**values)
