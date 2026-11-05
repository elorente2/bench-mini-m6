from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import DEFAULT_CONFIG_DIR, REPO_ROOT, load_config
from .engine import SafetyError, listeners, start, status, stop
from .legacy import load_legacy
from .report import load_doc, render
from .runner import RESULTS_DIR, UNSET, run_pass


def _write_report(paths: list[Path], out: Path, title: str) -> Path:
    docs = [load_doc(path) for path in paths]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(docs, title=title), encoding="utf-8")
    return out


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    engine = config.engine(args.engine)
    path = run_pass(
        engine,
        config.suite,
        label=args.label,
        base_url=args.base_url,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        out=args.out,
        reps=args.reps,
        decode_tokens=args.decode_tokens,
        timeout=args.timeout,
        safety=not args.no_safety,
        proc_pattern=args.proc_pattern,
    )
    print(path)
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    labels = [item.strip() for item in args.engines.split(",") if item.strip()]
    outputs: list[Path] = []
    started: set[str] = set()

    for label in labels:
        engine = config.engine(label)
        try:
            if not engine.persistent:
                if listeners(engine.port):
                    print(
                        f"== stopping {label} for a clean pass",
                        file=sys.stderr,
                    )
                    stop(engine, force=True)
                start(engine, timeout=args.start_timeout)
                started.add(label)
            elif not listeners(engine.port):
                start(engine, timeout=args.start_timeout)
                started.add(label)

            outputs.append(
                run_pass(
                    engine,
                    config.suite,
                    reps=args.reps,
                    decode_tokens=args.decode_tokens,
                    timeout=args.timeout,
                )
            )
        except Exception as exc:  # noqa: BLE001 - report and continue if requested
            print(f"ERROR {label}: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                raise
        finally:
            if not engine.persistent and label in started:
                stop(engine)

    if args.report and outputs:
        latest = REPO_ROOT / "reports" / "latest.md"
        day = REPO_ROOT / "reports" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        _write_report(outputs, latest, "Local LLM benchmark")
        _write_report(outputs, day, "Local LLM benchmark")
        print(f"report: {latest}", file=sys.stderr)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    docs = [load_doc(path) for path in args.files]
    print(render(docs, title=args.title))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    out = _write_report([Path(path) for path in args.files], Path(args.out), args.title)
    print(out)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    doc = load_doc(args.file)
    validation = doc.get("validation") or {}
    invalid = [name for name, result in validation.items() if not result.get("valid")]
    print(
        json.dumps(
            {
                "label": doc.get("label"),
                "schema_version": doc.get("schema_version"),
                "invalid_cases": invalid,
                "validation": validation,
            },
            indent=2,
        )
    )
    return 1 if (args.strict and invalid) else 0


def cmd_engines(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    print("| Label | Engine | Port | Model | Quantization | Persistent |")
    print("|---|---|---:|---|---|---|")
    for engine in config.engines.values():
        print(
            f"| `{engine.label}` | {engine.name} | {engine.port} | "
            f"`{engine.model}` | {engine.quantization or '—'} | "
            f"{'yes' if engine.persistent else 'no'} |"
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    labels = [args.engine] if args.engine else list(config.engines)
    print(json.dumps([status(config.engine(label)) for label in labels], indent=2))
    return 0


def cmd_import_legacy(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    source = Path(args.file)
    document = load_legacy(source, config)
    if args.out:
        out = Path(args.out)
    else:
        RESULTS_DIR.mkdir(exist_ok=True)
        day = datetime.now().strftime("%Y-%m-%d")
        out = RESULTS_DIR / f"{day}-{document['label']}.json"
    if args.source:
        document["imported_from"] = args.source
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bench",
        description="Benchmark OpenAI-compatible local engines on one machine.",
    )
    parser.add_argument("--config-dir", default=str(DEFAULT_CONFIG_DIR))
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one pass against one engine")
    run.add_argument("engine")
    run.add_argument("--label", help="label used in the result file")
    run.add_argument("--base-url")
    run.add_argument("--model")
    run.add_argument("--reasoning-effort", default=UNSET)
    run.add_argument("--out")
    run.add_argument("--reps", type=int, help="repetitions for short decode")
    run.add_argument("--decode-tokens", type=int, help="max tokens for short decode")
    run.add_argument("--timeout", type=int, default=1200)
    run.add_argument("--proc-pattern", help="regex used to sum engine RSS")
    run.add_argument("--no-safety", action="store_true")
    run.set_defaults(func=cmd_run)

    run_all = sub.add_parser("run-all", help="start, measure and stop each engine")
    run_all.add_argument(
        "--engines",
        default="splash,mirai,ollama-q3kxl,ollama-default",
        help="comma-separated labels, in order",
    )
    run_all.add_argument("--start-timeout", type=int, default=600)
    run_all.add_argument("--timeout", type=int, default=1200)
    run_all.add_argument("--reps", type=int)
    run_all.add_argument("--decode-tokens", type=int)
    run_all.add_argument("--continue-on-error", action="store_true")
    run_all.add_argument("--report", action="store_true")
    run_all.set_defaults(func=cmd_run_all)

    compare = sub.add_parser("compare", help="print a Markdown comparison")
    compare.add_argument("files", nargs="+")
    compare.add_argument("--title", default="Local LLM benchmark")
    compare.set_defaults(func=cmd_compare)

    report = sub.add_parser("report", help="write a Markdown comparison")
    report.add_argument("files", nargs="+")
    report.add_argument("--out", default=str(REPO_ROOT / "reports" / "latest.md"))
    report.add_argument("--title", default="Local LLM benchmark")
    report.set_defaults(func=cmd_report)

    validate = sub.add_parser("validate", help="show case validation for a result file")
    validate.add_argument("file")
    validate.add_argument("--strict", action="store_true")
    validate.set_defaults(func=cmd_validate)

    engines = sub.add_parser("engines", help="list configured engines")
    engines.set_defaults(func=cmd_engines)

    status_parser = sub.add_parser("status", help="show listeners and readiness")
    status_parser.add_argument("engine", nargs="?")
    status_parser.set_defaults(func=cmd_status)

    legacy = sub.add_parser("import-legacy", help="convert a schema-0 result file")
    legacy.add_argument("file")
    legacy.add_argument("--out")
    legacy.add_argument("--source", help="provenance string written into the result")
    legacy.set_defaults(func=cmd_import_legacy)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SafetyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except TimeoutError as exc:
        print(f"timeout: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
