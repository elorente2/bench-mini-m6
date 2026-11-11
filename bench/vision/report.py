from __future__ import annotations

import json
from pathlib import Path


def load_vision_doc(path: Path | str) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _pct(value) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.0f} %"


def item_ids(docs: list[dict]) -> list[str]:
    seen: list[str] = []
    for doc in docs:
        for entry in doc.get("vision", {}).get("items") or []:
            if entry["id"] not in seen:
                seen.append(entry["id"])
    return seen


def render_vision_report(docs: list[dict], *, title: str = "Vision by model") -> str:
    if not docs:
        raise ValueError("no vision documents to render")
    older = 0
    revisions = {
        doc.get("vision", {}).get("revision")
        for doc in docs
        if isinstance(doc.get("vision", {}).get("revision"), int)
    }
    if revisions:
        newest = max(revisions)
        kept = [doc for doc in docs if (doc.get("vision") or {}).get("revision") == newest]
        older = len(docs) - len(kept)
        docs = kept
        revisions = {newest}
    docs = sorted(docs, key=lambda doc: doc.get("label") or "")
    first = docs[0]
    machine = first.get("machine") or {}
    hardware = machine.get("chip") or machine.get("model") or "Mac"
    lines = [f"# {title}", ""]
    lines.append(
        f"{hardware} · {machine.get('memory_gb') or '?'} GB · "
        f"vision suite revision {', '.join(str(item) for item in sorted(revisions))} · "
        f"{len(docs)} runs · temperature 0"
    )
    lines.append("")
    if older:
        lines.append(
            f"> {older} runs from older revisions are left out of the table: the "
            "vision suite changes its items, and revisions are never compared."
        )
        lines.append("")

    tasks = item_ids(docs)
    lines.append("## Accuracy per image")
    lines.append("")
    header = ["Model / engine", *tasks, "Total"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(tasks)) + "|---:|")
    for doc in docs:
        results = {entry["id"]: entry["passed"] for entry in doc.get("items") or []}
        cells = []
        for task in tasks:
            cells.append("✓" if results.get(task) else ("✗" if task in results else "—"))
        summary = doc.get("summary") or {}
        total = f"{summary.get('passed')}/{summary.get('items')} ({_pct(summary.get('accuracy'))})"
        lines.append(f"| `{doc['label']}` | " + " | ".join(cells) + f" | {total} |")
    lines.append("")

    lines.append("## Runs")
    lines.append("")
    lines.append("| Run | Model | Engine | Size |")
    lines.append("|---|---|---|---:|")
    for doc in docs:
        model = doc.get("model") or {}
        engine = doc.get("engine") or {}
        size = (doc.get("vision") or {}).get("image_size")
        name = (engine.get("name") or "").strip()
        version = (engine.get("version") or "").strip()
        if name and version.casefold().startswith(name.casefold()):
            engine_text = version
        else:
            engine_text = " ".join(part for part in (name, version) if part) or "—"
        lines.append(f"| `{doc['label']}` | `{model.get('id')}` | {engine_text} | {size} px |")
    lines.append("")

    lines.append("## Answers")
    lines.append("")
    lines.append("| Run | Image | Correct | Answer |")
    lines.append("|---|---|---|---|")
    for doc in docs:
        for entry in doc.get("items") or []:
            answer = entry.get("extracted") or entry.get("detail") or ""
            lines.append(
                f"| `{doc['label']}` | `{entry['id']}` | "
                f"{'✓' if entry['passed'] else '✗'} | {str(answer)[:60]} |"
            )
    lines.append("")
    lines.append(
        "Images are generated in code and their hash is stored in the result, so a "
        "wrong grade is a model or generator bug, never a file somebody replaced."
    )
    lines.append("")
    return "\n".join(lines)
