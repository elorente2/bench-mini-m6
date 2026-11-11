from __future__ import annotations

import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

PREAMBLE = """\
import importlib.util
import resource
import socket
import sys

_CPU = {timeout}
_LIMITS = (
    (resource.RLIMIT_CPU, _CPU, _CPU + 1),
    (resource.RLIMIT_FSIZE, 1 << 20, 1 << 20),
    (resource.RLIMIT_NOFILE, 64, 64),
    (resource.RLIMIT_NPROC, 32, 32),
)
for _which, _soft, _hard in _LIMITS:
    try:
        resource.setrlimit(_which, (_soft, _hard))
    except (ValueError, OSError):
        pass


def _no_network(*args, **kwargs):
    raise RuntimeError("network access is disabled in the sandbox")


socket.socket.connect = _no_network
socket.socket.connect_ex = _no_network
socket.create_connection = _no_network

_spec = importlib.util.spec_from_file_location("solution", "solution.py")
if _spec is None or _spec.loader is None:
    raise ImportError("could not load solution.py")
solution = importlib.util.module_from_spec(_spec)
sys.modules["solution"] = solution
_spec.loader.exec_module(solution)
"""

MARKER = "__BENCH_TESTS_OK__"

JS_GUARD = """\
import dns from "node:dns";
import net from "node:net";

const deny = () => {
  throw new Error("network access is disabled in the sandbox");
};

net.Socket.prototype.connect = deny;
net.connect = deny;
net.createConnection = deny;
dns.lookup = deny;
dns.promises.lookup = deny;
"""

JS_RUNNER = """\
import * as solution from "./solution.mjs";

{tests}
console.log({marker});
"""


@dataclass(frozen=True)
class SandboxResult:
    passed: bool
    returncode: int | None
    timed_out: bool
    duration_ms: float
    stdout: str
    stderr: str


def run_js_tests(code: str, tests: str, timeout_s: int = 5) -> SandboxResult:
    """Run ``tests`` against an ES module in a throwaway directory.

    Node's permission model denies file writes; the import guard patches the
    socket and DNS entry points because ``--permission`` does not cover the
    network. Same limits as the Python path: wall clock, a clean environment and
    a temporary working directory.
    """

    node = shutil.which("node")
    if node is None:
        return SandboxResult(
            passed=False,
            returncode=None,
            timed_out=False,
            duration_ms=0.0,
            stdout="",
            stderr="node is not installed, so this item cannot be graded",
        )

    runner = JS_RUNNER.format(tests=tests, marker=repr(MARKER))
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="bench-eval-js-") as directory:
        root = Path(directory)
        (root / "solution.mjs").write_text(code, encoding="utf-8")
        (root / "guard.mjs").write_text(JS_GUARD, encoding="utf-8")
        (root / "run_tests.mjs").write_text(runner, encoding="utf-8")
        env = {
            "PATH": "/usr/bin:/bin:/opt/homebrew/bin",
            "HOME": directory,
            "TMPDIR": directory,
            "LANG": "en_US.UTF-8",
            "NO_PROXY": "*",
        }
        try:
            completed = subprocess.run(
                [
                    node,
                    "--permission",
                    f"--allow-fs-read={Path(directory).resolve()}",
                    "--no-warnings",
                    "--import",
                    "./guard.mjs",
                    "run_tests.mjs",
                ],
                cwd=directory,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s + 2,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = (time.perf_counter() - started) * 1000
            return SandboxResult(
                passed=False,
                returncode=None,
                timed_out=True,
                duration_ms=round(duration, 1),
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr="timeout",
            )
    duration = (time.perf_counter() - started) * 1000
    passed = completed.returncode == 0 and completed.stdout.rstrip().endswith(MARKER)
    return SandboxResult(
        passed=passed,
        returncode=completed.returncode,
        timed_out=False,
        duration_ms=round(duration, 1),
        stdout=completed.stdout[-2000:],
        stderr=completed.stderr[-2000:],
    )


def run_tests(code: str, tests: str, *, lang: str = "py", timeout_s: int = 5) -> SandboxResult:
    if lang == "js":
        return run_js_tests(code, tests, timeout_s=timeout_s)
    return run_python_tests(code, tests, timeout_s=timeout_s)


def run_python_tests(code: str, tests: str, timeout_s: int = 5) -> SandboxResult:
    """Run ``tests`` against ``code`` in a throwaway directory.

    This is a guard against broken or runaway generated code, not a hostile-code
    sandbox: it limits CPU, file size, open files and processes, disables the
    socket API and runs with ``-I`` from a temporary working directory. It does
    not use a container or a separate user, so treat it as best effort and say
    so in the docs.
    """

    script = PREAMBLE.format(timeout=int(timeout_s)) + "\n" + tests + f"\nprint({MARKER!r})\n"
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="bench-eval-") as directory:
        root = Path(directory)
        (root / "solution.py").write_text(code, encoding="utf-8")
        (root / "run_tests.py").write_text(script, encoding="utf-8")
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": directory,
            "TMPDIR": directory,
            "LANG": "en_US.UTF-8",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "NO_PROXY": "*",
        }
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "run_tests.py"],
                cwd=directory,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s + 2,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = (time.perf_counter() - started) * 1000
            return SandboxResult(
                passed=False,
                returncode=None,
                timed_out=True,
                duration_ms=round(duration, 1),
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr="timeout",
            )
    duration = (time.perf_counter() - started) * 1000
    # RLIMIT_CPU kills the child with SIGXCPU (or SIGKILL after the hard limit)
    # before subprocess.run's wall clock expires; both mean "ran too long".
    killed = completed.returncode is not None and completed.returncode < 0
    timed_out = killed and -completed.returncode in {signal.SIGXCPU, signal.SIGKILL}
    passed = completed.returncode == 0 and completed.stdout.rstrip().endswith(MARKER)
    return SandboxResult(
        passed=passed,
        returncode=completed.returncode,
        timed_out=timed_out,
        duration_ms=round(duration, 1),
        stdout=completed.stdout[-2000:],
        stderr=completed.stderr[-2000:],
    )
