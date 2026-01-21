from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .models import EngineState, NarrativeResult


def format_outcome_log(deltas: Dict[str, int]) -> str:
    lines: List[str] = []
    for key, value in deltas.items():
        sign = "+" if value >= 0 else ""
        lines.append(f"<li>{key}: {sign}{value}</li>")
    items = "\n".join(lines)
    return f"<div class=\"outcome-log\">\n<ul>\n{items}\n</ul>\n</div>"


def _describe_delta_items(deltas: Dict[str, int]) -> str:
    phrases: List[str] = []
    for key, value in deltas.items():
        direction = "rose" if value > 0 else "fell"
        if value == 0:
            continue
        phrases.append(f"{key} {direction} by {abs(value)}")
    return "; ".join(phrases)


def _ensure_sensory_anchor(text: str) -> str:
    anchors = ["mud", "rust", "cold"]
    if any(anchor in text.lower() for anchor in anchors):
        return text
    return f"{text} The mud, rust, and cold did not lift."


def generate_narrative(
    draft_state: EngineState,
    deltas: Dict[str, int],
    system_prompt: str,
) -> NarrativeResult:
    delta_summary = _describe_delta_items(deltas)
    opening = "I record the shift in the ledger."
    if delta_summary:
        opening = f"I record the shift in the ledger: {delta_summary}."
    visual_anchor = draft_state.commander.visual_anchor
    quote = (
        "<span class=\"survivor-quote\">"
        f"\"We paid for it, Commander. {visual_anchor}.\""
        "</span>"
    )
    unrest = ""
    if draft_state.flags.friction >= 40:
        unrest = " Sabotage simmered in the camp, a dry scrape of unrest."
    resolve_shift = ""
    if draft_state.flags.resolve < 20:
        resolve_shift = " The scene broke into fractured, desperate fragments."
    narrative = (
        f"{opening} The air scraped my lungs with grit."
        f"{unrest}{resolve_shift} {quote}"
    )
    narrative = _ensure_sensory_anchor(narrative)
    outcome_log = format_outcome_log(deltas)
    return NarrativeResult(
        narrative=narrative,
        outcome_log=outcome_log,
        deltas=deltas,
        system_prompt=system_prompt,
    )
