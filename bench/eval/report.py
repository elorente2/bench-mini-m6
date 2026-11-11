from __future__ import annotations

import json
from pathlib import Path

from .tasks import CATEGORIES

CATEGORY_LABELS = {
    "instrucciones": "Instructions",
    "json": "JSON",
    "herramientas": "Tools",
    "arquitectura": "Architecture",
    "calculo": "Calculation",
    "codigo": "Code",
    "contexto_largo": "Long context",
    "abstencion": "Abstention",
    "extraccion": "Extraction",
}


def load_eval_doc(path: Path | str) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def gate_problems(doc: dict) -> list[str]:
    """Reasons why a run cannot support a decision."""

    problems: list[str] = []
    summary = doc.get("summary") or {}
    if summary.get("errors"):
        problems.append(f"{summary['errors']} request errors")
    leaked = summary.get("thinking_leaked_items") or []
    if leaked:
        problems.append(f"reasoning leaked in {len(leaked)} items")
    if summary.get("accuracy") is None:
        problems.append("no graded items")
    return problems


def _pct(value) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.0f} %"


def _cell(entry: dict, bold: bool) -> str:
    text = f"{entry['passed']}/{entry['items']} ({_pct(entry['accuracy'])})"
    return f"**{text}**" if bold else text


def _engine_name(engine: dict) -> str:
    """Avoid "Splash Splash 1.5.0": the version command already prints the name."""

    name = (engine.get("name") or "").strip()
    version = (engine.get("version") or "").strip()
    if name and version.casefold().startswith(name.casefold()):
        return version
    return " ".join(part for part in (name, version) if part) or "—"


def _context_cell(model: dict) -> str:
    """Max context the engine declared, with ``*`` when it comes from config."""

    context = model.get("context")
    if not isinstance(context, int) or context <= 0:
        return "—"
    suffix = "*" if model.get("context_source") == "config" else ""
    return f"{context:,}{suffix}"


def _coverage(prompt_max, context) -> str:
    """Share of the declared context the longest suite prompt actually uses."""

    if not isinstance(prompt_max, int) or not isinstance(context, int) or context <= 0:
        return "—"
    return f"{prompt_max / context * 100:.0f} %"


def render_eval_report(docs: list[dict], *, title: str = "Accuracy by model") -> str:
    if not docs:
        raise ValueError("no eval documents to render")
    docs = sorted(docs, key=lambda doc: doc.get("label") or "")
    revisions = {doc.get("eval", {}).get("revision") for doc in docs}
    lines: list[str] = [f"# {title}", ""]

    first = docs[0]
    machine = first.get("machine") or {}
    hardware = machine.get("chip") or machine.get("model") or "Mac"
    if machine.get("chip") and machine.get("model"):
        hardware = f"{machine['chip']} ({machine['model']})"
    lines.append(
        f"{hardware} · {machine.get('memory_gb') or '?'} GB · "
        f"suite revision {', '.join(str(item) for item in sorted(revisions))} · "
        f"{len(docs)} runs · temperature 0"
    )
    lines.append("")
    if len(revisions) > 1:
        lines.append(
            "> Warning: these results span more than one revision. They are not "
            "compared with each other, and only the newest revision decides."
        )
        lines.append("")

    lines.append("## Accuracy by category")
    lines.append("")
    header = ["Model / engine", *[CATEGORY_LABELS[item] for item in CATEGORIES], "Total"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|---|" + "---:|" * len(CATEGORIES) + "---:|")
    for doc in docs:
        summary = doc.get("summary") or {}
        by_category = summary.get("by_category") or {}
        problem = bool(gate_problems(doc))
        name = f"`{doc['label']}`"
        if problem:
            name += " ⚠"
        cells = [
            _cell(by_category[item], False) if item in by_category else "—" for item in CATEGORIES
        ]
        total = f"{summary.get('passed')}/{summary.get('items')} ({_pct(summary.get('accuracy'))})"
        if problem:
            total = f"⚠ {total}"
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {total} |")
    lines.append("")
    lines.append("⚠ = run that cannot support a decision (see the gates section).")
    lines.append("")

    lines.append("## Models and engines")
    lines.append("")
    lines.append("| Run | Model | Engine | Thinking | Quantization | Max context |")
    lines.append("|---|---|---|---|---|---:|")
    for doc in docs:
        model = doc.get("model") or {}
        engine = doc.get("engine") or {}
        thinking = "on" if (doc.get("eval") or {}).get("thinking_expected") else "off"
        lines.append(
            f"| `{doc['label']}` | `{model.get('id')}` | {_engine_name(engine)} "
            f"| {thinking} | {model.get('quantization') or '—'} "
            f"| {_context_cell(model)} |"
        )
    lines.append("")
    lines.append(
        "Max context is what the engine's API declares; `*` marks the value taken "
        "from the configuration because the API reports none. It is not a retrieval "
        "measure: the long-context items say that with their real prompt."
    )
    lines.append("")

    lines.append("## Cost")
    lines.append("")
    lines.append(
        "| Run | Items | Minutes | Truncated | Max prompt (tokens) | "
        "Context coverage | Slowest item |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for doc in docs:
        summary = doc.get("summary") or {}
        total_ms = summary.get("total_ms")
        minutes = f"{total_ms / 60000:.1f}" if total_ms else "—"
        slowest = f"{summary['slowest_ms'] / 1000:.1f} s" if summary.get("slowest_ms") else "—"
        truncated = summary.get("truncated")
        coverage = _coverage(
            summary.get("prompt_tokens_max"), (doc.get("model") or {}).get("context")
        )
        lines.append(
            f"| `{doc['label']}` | {summary.get('items')} | {minutes} | "
            f"{'—' if truncated is None else truncated} | "
            f"{summary.get('prompt_tokens_max') or '—'} | {coverage} | {slowest} |"
        )
    lines.append("")
    lines.append(
        "Coverage is the share of the declared window the suite actually exercises: "
        "the longest prompt divided by the engine's max context. Low coverage does "
        "not mean the rest of the window fails; it means this suite has not tried it."
    )
    lines.append("")

    valid = [
        doc
        for doc in docs
        if not gate_problems(doc) and doc.get("eval", {}).get("revision") in _comparable(docs)
    ]
    lines.append("## Decision by task")
    lines.append("")
    if not valid:
        lines.append("No valid runs yet, so no model can be recommended.")
    else:
        lines.append("| Task | Best | Accuracy | Tied for first |")
        lines.append("|---|---|---:|---|")
        for category in CATEGORIES:
            candidates = [
                (doc["summary"]["by_category"][category]["accuracy"], doc["label"])
                for doc in valid
                if category in (doc["summary"].get("by_category") or {})
            ]
            if not candidates:
                continue
            best = max(accuracy for accuracy, _ in candidates)
            winners = sorted(label for accuracy, label in candidates if accuracy == best)
            if len(winners) == 1:
                who = f"`{winners[0]}`"
                ties = "—"
            else:
                who = f"tie ({len(winners)})"
                ties = ", ".join(f"`{label}`" for label in winners)
            lines.append(f"| {CATEGORY_LABELS[category]} | {who} | {_pct(best)} | {ties} |")
        lines.append("")
        lines.append(
            "The decision compares only runs of the newest revision without "
            "infrastructure failures. When several tie for first, the row says so "
            "and names them: a tie is never broken by speed."
        )
    lines.append("")

    lines.extend(_render_discrimination(docs))

    lines.append("## Gates")
    lines.append("")
    for doc in docs:
        problems = gate_problems(doc)
        if problems:
            lines.append(f"- `{doc['label']}`: " + "; ".join(problems))
    if not any(gate_problems(doc) for doc in docs):
        lines.append("- All runs pass the gates.")
    lines.append("")
    return "\n".join(lines)


def _comparable(docs: list[dict]) -> set:
    """Only the newest revision is comparable: it is the current contract.

    A newer revision supersedes the older one by definition, so mixing them is
    never allowed; the older rows stay in the table as history.
    """

    revisions = [
        revision
        for revision in ((doc.get("eval") or {}).get("revision") for doc in docs)
        if isinstance(revision, int)
    ]
    return {max(revisions)} if revisions else set()


def _render_discrimination(docs: list[dict]) -> list[str]:
    """Items every run passes or every run fails: candidates for pruning."""

    seen: dict[str, list[bool]] = {}
    for doc in docs:
        for item in doc.get("items") or []:
            if "error" in item:
                continue
            seen.setdefault(item["id"], []).append(bool(item["passed"]))
    if not seen or len(docs) < 2:
        return []
    lines = ["## Items that do not discriminate", ""]
    lines.append("| Item | Result | Reading |")
    lines.append("|---|---|---|")
    found = False
    for item_id, results in sorted(seen.items()):
        if len(results) < len(docs):
            continue
        if all(results):
            lines.append(
                f"| `{item_id}` | everyone passes | candidate for pruning or a harder variant |"
            )
            found = True
        elif not any(results):
            lines.append(
                f"| `{item_id}` | everyone fails | either a ceiling or a badly written item |"
            )
            found = True
    if not found:
        lines.append("| — | — | every item separates at least one run |")
    lines.append("")
    return lines
