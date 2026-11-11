from __future__ import annotations

import json
from pathlib import Path

from .tasks import CATEGORIES

CATEGORY_LABELS = {
    "instrucciones": "Instrucciones",
    "json": "JSON",
    "herramientas": "Herramientas",
    "calculo": "Cálculo",
    "codigo": "Código",
    "contexto_largo": "Contexto largo",
    "abstencion": "Abstención",
    "extraccion": "Extracción",
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


def render_eval_report(docs: list[dict], *, title: str = "Precisión por modelo") -> str:
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
        f"revisión de la suite {', '.join(str(item) for item in sorted(revisions))} · "
        f"{len(docs)} ejecuciones · temperatura 0"
    )
    lines.append("")
    if len(revisions) > 1:
        lines.append(
            "> Aviso: hay resultados de revisiones distintas. No se comparan entre sí "
            "ni entran en la decisión final."
        )
        lines.append("")

    lines.append("## Acierto por categoría")
    lines.append("")
    header = ["Modelo / motor", *[CATEGORY_LABELS[item] for item in CATEGORIES], "Total"]
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
    lines.append("⚠ = ejecución no válida para decidir (ver la sección de puertas).")
    lines.append("")

    lines.append("## Modelos y motores")
    lines.append("")
    lines.append("| Ejecución | Modelo | Motor | Pensamiento | Cuantización |")
    lines.append("|---|---|---|---|---|")
    for doc in docs:
        model = doc.get("model") or {}
        engine = doc.get("engine") or {}
        thinking = "sí" if (doc.get("eval") or {}).get("thinking_expected") else "no"
        lines.append(
            f"| `{doc['label']}` | `{model.get('id')}` | {_engine_name(engine)} "
            f"| {thinking} | {model.get('quantization') or '—'} |"
        )
    lines.append("")

    lines.append("## Coste")
    lines.append("")
    lines.append("| Ejecución | Ítems | Minutos | Prompt máx (tokens) | Ítem más lento |")
    lines.append("|---|---:|---:|---:|---:|")
    for doc in docs:
        summary = doc.get("summary") or {}
        total_ms = summary.get("total_ms")
        minutes = f"{total_ms / 60000:.1f}" if total_ms else "—"
        slowest = f"{summary['slowest_ms'] / 1000:.1f} s" if summary.get("slowest_ms") else "—"
        lines.append(
            f"| `{doc['label']}` | {summary.get('items')} | {minutes} | "
            f"{summary.get('prompt_tokens_max') or '—'} | {slowest} |"
        )
    lines.append("")

    valid = [
        doc
        for doc in docs
        if not gate_problems(doc) and doc.get("eval", {}).get("revision") in _comparable(docs)
    ]
    lines.append("## Decisión por tarea")
    lines.append("")
    if not valid:
        lines.append("No hay ejecuciones válidas todavía; no se puede recomendar un modelo.")
    else:
        lines.append("| Tarea | Mejor | Acierto | Empate técnico |")
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
            others = [label for accuracy, label in candidates if accuracy < best]
            lines.append(
                f"| {CATEGORY_LABELS[category]} | `{winners[0]}` | {_pct(best)} | "
                f"{', '.join(f'`{item}`' for item in others) or '—'} |"
            )
        lines.append("")
        lines.append(
            "La decisión solo compara ejecuciones con la misma revisión y sin fallos de "
            "infraestructura. Un empate incluye todas las que empatan en la primera posición."
        )
    lines.append("")

    lines.extend(_render_discrimination(docs))

    lines.append("## Puertas")
    lines.append("")
    for doc in docs:
        problems = gate_problems(doc)
        if problems:
            lines.append(f"- `{doc['label']}`: " + "; ".join(problems))
    if not any(gate_problems(doc) for doc in docs):
        lines.append("- Todas las ejecuciones pasan las puertas.")
    lines.append("")
    return "\n".join(lines)


def _comparable(docs: list[dict]) -> set:
    """Revisions shared by the largest group, i.e. the comparison base."""

    counts: dict = {}
    for doc in docs:
        revision = (doc.get("eval") or {}).get("revision")
        counts[revision] = counts.get(revision, 0) + 1
    if not counts:
        return set()
    top = max(counts.values())
    return {revision for revision, count in counts.items() if count == top}


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
    lines = ["## Ítems que no discriminan", ""]
    lines.append("| Ítem | Resultado | Lectura |")
    lines.append("|---|---|---|")
    found = False
    for item_id, results in sorted(seen.items()):
        if len(results) < len(docs):
            continue
        if all(results):
            lines.append(
                f"| `{item_id}` | todos aciertan | candidato a poda o a subir dificultad |"
            )
            found = True
        elif not any(results):
            lines.append(
                f"| `{item_id}` | todos fallan | puede ser un techo o un ítem mal planteado |"
            )
            found = True
    if not found:
        lines.append("| — | — | todos los ítems separan al menos una ejecución |")
    lines.append("")
    return lines
