from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .config import DEFAULT_CONFIG_DIR, REPO_ROOT, Engine, load_config
from .metrics import run_cmd, wait_for_models

LOG_DIR = REPO_ROOT / "logs"
RUN_DIR = REPO_ROOT / ".run"


class SafetyError(RuntimeError):
    """Raised when starting or measuring would break the one-engine rule."""


def listeners(port: int) -> list[dict]:
    output = run_cmd(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fpc"],
        timeout=10,
    )
    result: list[dict] = []
    pid: int | None = None
    for line in output.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            pid = int(line[1:])
        elif line.startswith("c") and pid is not None:
            result.append({"pid": pid, "command": line[1:]})
            pid = None
    for item in result:
        full = process_command(item["pid"])
        if full:
            item["command"] = full
    return result


def process_command(pid: int) -> str:
    return run_cmd(["ps", "-p", str(pid), "-o", "command="], timeout=5)


def pgrep(pattern: str) -> list[str]:
    output = run_cmd(["pgrep", "-fl", pattern], timeout=10)
    return [line for line in output.splitlines() if line.strip()]


def port_from_url(url: str) -> int:
    parsed = urlparse(url)
    if parsed.port:
        return parsed.port
    return 443 if parsed.scheme == "https" else 80


def assert_exclusive(engine: Engine) -> None:
    for pattern in engine.conflicts:
        matches = pgrep(pattern)
        if matches:
            details = "\n".join(f"  {line}" for line in matches)
            raise SafetyError(
                f"{engine.label} cannot run while a conflicting engine is alive.\n"
                f"pattern: {pattern}\n{details}\n"
                "Stop it first (see docs/fairness-rules.md)."
            )


def assert_single_listener(port: int, label: str) -> None:
    found = listeners(port)
    if len(found) != 1:
        details = "\n".join(f"  pid={item['pid']} {item['command']}" for item in found)
        raise SafetyError(
            f"expected exactly one listener on :{port} for {label}, found {len(found)}"
            + (f"\n{details}" if details else "")
        )


def assert_ollama_idle(engine: Engine) -> None:
    """An idle Ollama service is fine; a loaded Ollama model is not."""

    if engine.label.startswith("ollama"):
        return
    if not shutil.which("ollama") or not listeners(11434):
        return
    output = run_cmd(["ollama", "ps"], timeout=10)
    lines = [line for line in output.splitlines() if line.strip()]
    data = [line for line in lines if not line.upper().startswith("NAME")]
    if data and not any("no models" in line.lower() for line in data):
        details = "\n".join(f"  {line}" for line in data)
        raise SafetyError(
            "Ollama has a model loaded while another engine is being measured.\n"
            f"{details}\nRun `ollama stop <model>` or stop the Ollama service first."
        )


def _ready(base_url: str, timeout: float = 2.0) -> bool:
    try:
        wait_for_models(base_url, timeout=int(timeout))
        return True
    except (TimeoutError, OSError):
        return False


def _wait_dead(pid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(0.2)
    return False


def _kill(pid: int, sig: signal.Signals) -> None:
    """Signal a process, using the process group only when it is safe.

    Managed engines are started with ``start_new_session=True``, so the pid is
    also the process-group leader and killing the group cleans up child
    processes. An engine started outside the harness may share the terminal's
    process group; signalling that group would kill the user's shell.
    """

    try:
        pgid = os.getpgid(pid)
    except (ProcessLookupError, PermissionError):
        return
    if pgid == pid:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(pgid, sig)
        return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.kill(pid, sig)


def _pid_file(label: str) -> Path:
    return RUN_DIR / f"{label}.pid"


def start(engine: Engine, *, timeout: int = 600, wait: bool = True) -> int:
    if listeners(engine.port):
        print(f"{engine.label} is already listening on :{engine.port}", file=sys.stderr)
        if wait:
            wait_for_models(engine.base_url, timeout=timeout)
        return 0

    assert_exclusive(engine)
    LOG_DIR.mkdir(exist_ok=True)
    RUN_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIR / f"{engine.label}-{stamp}.log"
    print(f"starting {' '.join(engine.start)}", file=sys.stderr)
    print(f"log: {log_path}", file=sys.stderr)
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            list(engine.start),
            cwd=REPO_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _pid_file(engine.label).write_text(f"{process.pid}\n", encoding="utf-8")

    if wait:
        try:
            wait_for_models(engine.base_url, timeout=timeout)
        except TimeoutError:
            tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
            print("\n".join(tail), file=sys.stderr)
            raise
    return 0


def stop(engine: Engine, *, force: bool = False, timeout: int = 30) -> int:
    pid_path = _pid_file(engine.label)
    if pid_path.exists():
        raw = pid_path.read_text(encoding="utf-8").strip()
        pid_path.unlink(missing_ok=True)
        if raw.isdigit():
            pid = int(raw)
            if _pid_alive(pid):
                _kill(pid, signal.SIGTERM)
                if not _wait_dead(pid, timeout):
                    _kill(pid, signal.SIGKILL)
                    _wait_dead(pid, 5)

    remaining = listeners(engine.port)
    if not remaining:
        print(f"{engine.label} stopped", file=sys.stderr)
        return 0

    details = "\n".join(f"  pid={item['pid']} {item['command']}" for item in remaining)
    if not force:
        raise SafetyError(
            f"{engine.label} is still listening on :{engine.port} and was not started "
            f"by this harness:\n{details}\n"
            "Stop it manually, or rerun with --force after checking the process list."
        )

    for item in remaining:
        command = process_command(item["pid"])
        if not re.search(engine.proc_pattern, command):
            print(
                f"refusing to force-kill pid {item['pid']}: command does not match "
                f"{engine.proc_pattern!r}\n  {command}",
                file=sys.stderr,
            )
            continue
        _kill(item["pid"], signal.SIGTERM)
    # The listener is not always the engine child (for example Splash runs a
    # Python server plus a serve-native process). Stop matching children too.
    for line in pgrep(engine.proc_pattern):
        raw_pid, _, _ = line.partition(" ")
        if raw_pid.isdigit():
            pid = int(raw_pid)
            if pid not in {item["pid"] for item in remaining}:
                _kill(pid, signal.SIGTERM)
    for item in remaining:
        if not _wait_dead(item["pid"], timeout):
            _kill(item["pid"], signal.SIGKILL)
    print(f"{engine.label} force-stopped", file=sys.stderr)
    return 0


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def status(engine: Engine) -> dict:
    pid_path = _pid_file(engine.label)
    pid = int(pid_path.read_text().strip()) if pid_path.exists() else None
    found = listeners(engine.port)
    return {
        "label": engine.label,
        "name": engine.name,
        "port": engine.port,
        "base_url": engine.base_url,
        "model": engine.model,
        "quantization": engine.quantization,
        "persistent": engine.persistent,
        "managed_pid": pid,
        "managed_pid_alive": _pid_alive(pid) if pid else False,
        "listeners": found,
        "ready": _ready(engine.base_url),
        "conflicts": {pattern: pgrep(pattern) for pattern in engine.conflicts},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench-engine",
        description="Start, stop or inspect the local engines configured in config/engines.toml.",
    )
    parser.add_argument("--config-dir", default=str(DEFAULT_CONFIG_DIR))
    sub = parser.add_subparsers(dest="command", required=True)

    start_parser = sub.add_parser("start", help="start an engine in the background")
    start_parser.add_argument("engine")
    start_parser.add_argument("--timeout", type=int, default=600)

    stop_parser = sub.add_parser("stop", help="stop an engine started by this harness")
    stop_parser.add_argument("engine")
    stop_parser.add_argument("--force", action="store_true")

    status_parser = sub.add_parser("status", help="show listeners and readiness")
    status_parser.add_argument("engine", nargs="?")

    args = parser.parse_args(argv)
    config = load_config(args.config_dir)

    if args.command == "start":
        return start(config.engine(args.engine), timeout=args.timeout)
    if args.command == "stop":
        return stop(config.engine(args.engine), force=args.force)
    if args.command == "status":
        labels = [args.engine] if args.engine else list(config.engines)
        output = [status(config.engine(label)) for label in labels]
        print(json.dumps(output, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
