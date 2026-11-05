from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    kind: str
    higher_is_better: bool
    group: str


METRICS = (
    Metric("decode_short_tps", "Short decode", "tps", True, "speed"),
    Metric("decode_at_long_tps", "Decode @ long context", "tps", True, "speed"),
    Metric("prefill_long_tps", "Prefill @ long context", "tps", True, "speed"),
    Metric("cold_ttft_long_ms", "Cold TTFT @ long context", "ms", False, "speed"),
    Metric("cached_ttft_long_ms", "Cached TTFT", "ms", False, "speed"),
    Metric("peak_engine_rss_mb", "Peak engine RSS", "mb", False, "memory"),
    Metric("wired_peak_gb", "Peak wired memory", "gb", False, "memory"),
    Metric("context", "Context window (reported)", "int", True, "context"),
)

ENGINE_ORDER = {
    "splash": 0,
    "mirai": 1,
    "ollama-q3kxl": 2,
    "ollama-default": 3,
}

SPEED_METRICS = tuple(metric for metric in METRICS if metric.group == "speed")
MEMORY_METRICS = tuple(metric for metric in METRICS if metric.group == "memory")


def load_doc(path: Path | str) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def format_value(metric: Metric, value) -> str:
    if value is None:
        return "—"
    if metric.kind == "tps":
        return f"{float(value):,.1f} tok/s"
    if metric.kind == "ms":
        milliseconds = float(value)
        if milliseconds >= 1000:
            return f"{milliseconds / 1000:,.1f} s"
        return f"{milliseconds:,.0f} ms"
    if metric.kind == "mb":
        return f"{float(value):,.0f} MB"
    if metric.kind == "gb":
        return f"{float(value):,.2f} GB"
    if metric.kind == "int":
        return f"{int(value):,}"
    return str(value)


def best_labels(metric: Metric, docs: list[dict]) -> set[str]:
    candidates: list[tuple[float, str]] = []
    for doc in docs:
        value = (doc.get("summary") or {}).get(metric.key)
        if isinstance(value, (int, float)):
            candidates.append((float(value), doc["label"]))
    if not candidates:
        return set()
    target = (
        max(value for value, _ in candidates)
        if metric.higher_is_better
        else min(value for value, _ in candidates)
    )
    return {
        label
        for value, label in candidates
        if abs(value - target) <= max(abs(target) * 0.005, 1e-9)
    }


def _wins(metrics: tuple[Metric, ...], docs: list[dict]) -> dict[str, float]:
    wins = {doc["label"]: 0.0 for doc in docs}
    for metric in metrics:
        values = [(doc.get("summary") or {}).get(metric.key) for doc in docs]
        if not all(isinstance(value, (int, float)) for value in values):
            continue
        best = best_labels(metric, docs)
        if len(best) == 1:
            wins[next(iter(best))] += 1
        elif best:
            share = 1.0 / len(best)
            for label in best:
                wins[label] += share
    return wins


def _human_join(names: list[str]) -> str:
    if not names:
        return "nobody"
    if len(names) == 1:
        return f"`{names[0]}`"
    return ", ".join(f"`{name}`" for name in names[:-1]) + f" and `{names[-1]}`"


def _winners_text(scores: dict[str, float], docs: list[dict]) -> str:
    top = max(scores.values()) if scores else 0
    winners = sorted(label for label, score in scores.items() if score == top)
    if top == 0:
        return "No comparable metrics."
    total = sum(
        1
        for metric in SPEED_METRICS
        if all(isinstance((doc.get("summary") or {}).get(metric.key), (int, float)) for doc in docs)
    )
    return f"{_human_join(winners)} won {top:g} of {total} comparable speed metrics."


def render(docs: list[dict], *, title: str = "Local LLM benchmark") -> str:
    if not docs:
        raise ValueError("no result documents to render")
    docs = sorted(
        docs,
        key=lambda doc: (
            ENGINE_ORDER.get(doc["label"], len(ENGINE_ORDER)),
            doc["label"],
        ),
    )
    labels = [doc["label"] for doc in docs]
    lines: list[str] = [f"# {title}", ""]

    lines.append("| Metric | " + " | ".join(labels) + " |")
    lines.append("|---|" + "---:|" * len(docs))
    for metric in METRICS:
        best = best_labels(metric, docs)
        cells = []
        for doc in docs:
            value = (doc.get("summary") or {}).get(metric.key)
            text = format_value(metric, value)
            if doc["label"] in best and value is not None:
                text = f"**{text}**"
            cells.append(text)
        lines.append(f"| {metric.label} | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "The bold value is the best result for that row. Lower is better for "
            "TTFT and memory; higher is better for throughput and context.",
            "",
            "## Contenders",
            "",
            "| | " + " | ".join(labels) + " |",
            "|---|" + "---|" * len(docs),
        ]
    )
    rows = (
        ("Model", lambda doc: (doc.get("model") or {}).get("id") or "—"),
        ("Quantization", lambda doc: (doc.get("model") or {}).get("quantization") or "—"),
        ("Engine version", lambda doc: (doc.get("engine") or {}).get("version") or "—"),
        (
            "Reasoning effort",
            lambda doc: (doc.get("engine") or {}).get("reasoning_effort") or "not sent",
        ),
    )
    for label, getter in rows:
        lines.append(f"| {label} | " + " | ".join(str(getter(doc)) for doc in docs) + " |")

    invalid_lines: list[str] = []
    for doc in docs:
        for case_name, result in (doc.get("validation") or {}).items():
            if not result.get("valid"):
                reasons = "; ".join(result.get("reasons") or ["invalid"])
                invalid_lines.append(f"- `{doc['label']}` / `{case_name}`: {reasons}")
    if invalid_lines:
        lines.extend(["", "## Validity", "", *invalid_lines])

    lines.extend(["", "## Verdict", ""])
    speed_scores = _wins(SPEED_METRICS, docs)
    lines.append(f"**Text and code:** {_winners_text(speed_scores, docs)}")

    wired = next(metric for metric in MEMORY_METRICS if metric.key == "wired_peak_gb")
    wired_best = best_labels(wired, docs)
    if wired_best:
        values = {doc["label"]: (doc.get("summary") or {}).get("wired_peak_gb") for doc in docs}
        if len(wired_best) == 1:
            winner = next(iter(wired_best))
            others = [
                f"{format_value(wired, value)} for `{label}`"
                for label, value in values.items()
                if label != winner and isinstance(value, (int, float))
            ]
            sentence = (
                f"`{winner}` used the least peak wired memory "
                f"({format_value(wired, values[winner])}"
            )
            sentence += f" vs {', '.join(others)})" if others else ")"
        else:
            winners = sorted(wired_best)
            sentence = f"{_human_join(winners)} tied at {format_value(wired, values[winners[0]])}"
        lines.append(
            f"**Memory:** {sentence}. On macOS this is the meaningful figure: "
            "Metal allocations are wired, not ordinary process RSS."
        )

    context_docs = [
        doc for doc in docs if isinstance((doc.get("summary") or {}).get("context"), int)
    ]
    if context_docs:
        largest = max(context_docs, key=lambda doc: doc["summary"]["context"])
        lines.append(
            f"**Context:** `{largest['label']}` reports the largest window "
            f"({largest['summary']['context']:,} tokens); reported values are not a "
            "verified long-context result."
        )

    lines.extend(
        [
            "",
            "> These numbers compare engine speed and memory, not output quality. "
            "Model weights and quantization differ between engines; see "
            "`docs/methodology.md`.",
            "",
        ]
    )
    return "\n".join(lines)
