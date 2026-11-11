from __future__ import annotations

import contextlib
import platform
import re
import statistics
import subprocess
import threading
import time


def run_cmd(cmd: list[str], timeout: int = 15) -> str:
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def machine_info() -> dict:
    memory_bytes = run_cmd(["sysctl", "-n", "hw.memsize"])
    # No hostname: results are published, and `os`, `model`, `chip` and memory
    # already describe the machine without naming somebody's computer.
    return {
        "os": f"{platform.system()} {platform.release()}",
        "macos": run_cmd(["sw_vers", "-productVersion"]),
        "model": run_cmd(["sysctl", "-n", "hw.model"]),
        "chip": run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "memory_gb": round(int(memory_bytes) / 1e9, 1) if memory_bytes.isdigit() else None,
        "python": platform.python_version(),
    }


def read_wired_bytes() -> int | None:
    output = run_cmd(["vm_stat"])
    page_size = 16384
    match = re.search(r"page size of (\d+) bytes", output)
    if match:
        page_size = int(match.group(1))
    match = re.search(r"Pages wired down:\s+(\d+)", output)
    return int(match.group(1)) * page_size if match else None


class MemSampler(threading.Thread):
    """Sum RSS of matching processes and track peak wired memory.

    RSS is useful for engines that keep weights in ordinary process memory.
    On macOS, Metal allocations are often wired rather than counted in RSS,
    so the sampler records both.
    """

    def __init__(self, pattern: str, interval: float = 0.5):
        super().__init__(daemon=True)
        self.pattern = re.compile(pattern)
        self.interval = interval
        self.peak_kb = 0
        self.peak_wired = 0
        self.samples = 0
        self._stop = threading.Event()

    def run(self) -> None:
        while not self._stop.is_set():
            self.sample()
            self._stop.wait(self.interval)

    def sample(self) -> None:
        try:
            output = subprocess.run(
                ["ps", "-axo", "rss=,command="],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            output = ""

        total_kb = 0
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            rss, command = parts
            if "ps -axo" in command or "rss=,command=" in command:
                continue
            if "bench.cli" in command or "bench/runner.py" in command:
                continue
            if self.pattern.search(command):
                with contextlib.suppress(ValueError):
                    total_kb += int(rss)
        self.peak_kb = max(self.peak_kb, total_kb)
        wired = read_wired_bytes()
        if wired:
            self.peak_wired = max(self.peak_wired, wired)
        self.samples += 1

    def stop(self) -> None:
        self._stop.set()


def median(values: list[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return round(statistics.median(clean), 2) if clean else None


def capture_version(cmd: tuple[str, ...] | list[str]) -> str | None:
    if not cmd:
        return None
    output = run_cmd(list(cmd))
    if not output:
        return None
    return output.splitlines()[0].strip() or None


def wait_for_models(base_url: str, timeout: int = 120) -> dict:
    """Poll ``/v1/models`` until the server answers or the timeout expires."""

    import json
    import urllib.error
    import urllib.request

    url = base_url.rstrip("/") + "/models"
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode("utf-8", "replace"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(1)
    raise TimeoutError(f"server never became ready at {url}: {last_error}")
