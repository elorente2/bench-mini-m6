from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_DIR = REPO_ROOT / "config"


class ConfigError(ValueError):
    """Raised when a TOML configuration file is incomplete or inconsistent."""


@dataclass(frozen=True)
class Engine:
    label: str
    name: str
    base_url: str
    port: int
    model: str
    api_model: str | None
    quantization: str | None
    context_tokens: int | None
    proc_pattern: str
    conflicts: tuple[str, ...]
    start: tuple[str, ...]
    version_cmd: tuple[str, ...]
    persistent: bool = False
    reasoning_effort: str | None = None
    notes: str = ""

    @property
    def models_url(self) -> str:
        return self.base_url.rstrip("/") + "/models"

    @property
    def root_url(self) -> str:
        return self.base_url.rstrip("/").removesuffix("/v1")


@dataclass(frozen=True)
class SuiteCase:
    name: str
    prompt: str
    max_tokens: int
    reps: int = 1
    validate: str | None = None
    compare_to: str | None = None


@dataclass(frozen=True)
class Suite:
    cases: tuple[SuiteCase, ...]
    prefill_target_chars: int
    warmup_max_tokens: int = 8
    revision: int = 1

    def case(self, name: str) -> SuiteCase:
        for item in self.cases:
            if item.name == name:
                return item
        raise KeyError(name)


@dataclass(frozen=True)
class Config:
    engines: dict[str, Engine]
    suite: Suite

    def engine(self, label: str) -> Engine:
        try:
            return self.engines[label]
        except KeyError as exc:
            available = ", ".join(sorted(self.engines))
            raise ConfigError(f"unknown engine {label!r}; configured: {available}") from exc


def _string(raw: dict[str, Any], key: str, *, label: str, required: bool = True) -> str | None:
    value = raw.get(key)
    if value is None:
        if required:
            raise ConfigError(f"[engines.{label}] is missing {key!r}")
        return None
    if not isinstance(value, str):
        raise ConfigError(f"[engines.{label}].{key} must be a string")
    return value


def _string_tuple(raw: dict[str, Any], key: str, *, label: str) -> tuple[str, ...]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"[engines.{label}].{key} must be an array of strings")
    return tuple(value)


def _int(raw: dict[str, Any], key: str, *, label: str, required: bool = True) -> int | None:
    value = raw.get(key)
    if value is None:
        if required:
            raise ConfigError(f"[engines.{label}] is missing {key!r}")
        return None
    if not isinstance(value, int):
        raise ConfigError(f"[engines.{label}].{key} must be an integer")
    return value


def load_engines(path: Path) -> dict[str, Engine]:
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    raw_engines = data.get("engines")
    if not isinstance(raw_engines, dict) or not raw_engines:
        raise ConfigError(f"{path} has no [engines.*] tables")

    engines: dict[str, Engine] = {}
    for label, raw in raw_engines.items():
        if not isinstance(raw, dict):
            raise ConfigError(f"[engines.{label}] must be a table")
        engines[label] = Engine(
            label=label,
            name=_string(raw, "name", label=label) or label,
            base_url=_string(raw, "base_url", label=label) or "",
            port=_int(raw, "port", label=label) or 0,
            model=_string(raw, "model", label=label) or "",
            api_model=_string(raw, "api_model", label=label, required=False),
            quantization=_string(raw, "quantization", label=label, required=False),
            context_tokens=_int(raw, "context_tokens", label=label, required=False),
            proc_pattern=_string(raw, "proc_pattern", label=label) or label,
            conflicts=_string_tuple(raw, "conflicts", label=label),
            start=_string_tuple(raw, "start", label=label),
            version_cmd=_string_tuple(raw, "version_cmd", label=label),
            persistent=bool(raw.get("persistent", False)),
            reasoning_effort=_string(raw, "reasoning_effort", label=label, required=False),
            notes=_string(raw, "notes", label=label, required=False) or "",
        )
        if engines[label].port <= 0:
            raise ConfigError(f"[engines.{label}].port must be positive")
        if not engines[label].start:
            raise ConfigError(f"[engines.{label}].start must not be empty")
        if engines[label].persistent and not engines[label].version_cmd:
            raise ConfigError(f"[engines.{label}].version_cmd is required for persistent engines")
    return engines


def load_suite(path: Path) -> Suite:
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    settings = data.get("suite", {})
    if not isinstance(settings, dict):
        raise ConfigError("[suite] must be a table")
    raw_cases = data.get("cases")
    if not isinstance(raw_cases, dict) or not raw_cases:
        raise ConfigError(f"{path} has no [cases.*] tables")

    cases: list[SuiteCase] = []
    for name, raw in raw_cases.items():
        if not isinstance(raw, dict):
            raise ConfigError(f"[cases.{name}] must be a table")
        prompt = raw.get("prompt")
        if prompt not in {"short", "long", "long_cached"}:
            raise ConfigError(f"[cases.{name}].prompt must be 'short', 'long' or 'long_cached'")
        max_tokens = raw.get("max_tokens")
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ConfigError(f"[cases.{name}].max_tokens must be a positive integer")
        reps = raw.get("reps", 1)
        if not isinstance(reps, int) or reps <= 0:
            raise ConfigError(f"[cases.{name}].reps must be a positive integer")
        validate = raw.get("validate")
        if validate not in {None, "cache_hit"}:
            raise ConfigError(f"[cases.{name}].validate must be 'cache_hit' or omitted")
        compare_to = raw.get("compare_to")
        if validate == "cache_hit" and not isinstance(compare_to, str):
            raise ConfigError(f"[cases.{name}].compare_to is required with validate='cache_hit'")
        cases.append(
            SuiteCase(
                name=name,
                prompt=prompt,
                max_tokens=max_tokens,
                reps=reps,
                validate=validate,
                compare_to=compare_to,
            )
        )

    names = {case.name for case in cases}
    for case in cases:
        if case.compare_to and case.compare_to not in names:
            raise ConfigError(
                f"[cases.{case.name}].compare_to={case.compare_to!r} is not a configured case"
            )

    prefill_target_chars = settings.get("prefill_target_chars", 32000)
    warmup_max_tokens = settings.get("warmup_max_tokens", 8)
    revision = settings.get("revision", 1)
    for key, value in (
        ("prefill_target_chars", prefill_target_chars),
        ("warmup_max_tokens", warmup_max_tokens),
        ("revision", revision),
    ):
        if not isinstance(value, int) or value <= 0:
            raise ConfigError(f"[suite].{key} must be a positive integer")

    return Suite(
        cases=tuple(cases),
        prefill_target_chars=prefill_target_chars,
        warmup_max_tokens=warmup_max_tokens,
        revision=revision,
    )


def load_config(config_dir: Path | str = DEFAULT_CONFIG_DIR) -> Config:
    directory = Path(config_dir)
    if not directory.is_dir():
        raise ConfigError(f"config directory not found: {directory}")
    return Config(
        engines=load_engines(directory / "engines.toml"),
        suite=load_suite(directory / "suite.toml"),
    )
