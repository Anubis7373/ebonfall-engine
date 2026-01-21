from __future__ import annotations

from typing import Dict, List

from .models import EngineState


FORBIDDEN_PHRASES = [
    "you feel",
    "i feel",
    "magic",
    "spell",
    "divine",
]


REQUIRED_ANCHORS = [
    "mud",
    "rust",
    "cold",
]


def validate_map_grid(map_grid: List[List[object]]) -> List[str]:
    errors: List[str] = []
    if len(map_grid) != 5:
        errors.append("Map grid must be 5 rows.")
    for row in map_grid:
        if len(row) != 5:
            errors.append("Map grid must be 5 columns.")
    return errors


def validate_vitals(vitals: Dict[str, int]) -> List[str]:
    errors: List[str] = []
    for key, value in vitals.items():
        if not 0 <= value <= 100:
            errors.append(f"{key} must be between 0 and 100.")
    return errors


def validate_conservation(deltas: Dict[str, int]) -> List[str]:
    positives = [value for value in deltas.values() if value > 0]
    negatives = [value for value in deltas.values() if value < 0]
    if positives and not negatives:
        return ["Conservation violated: benefit without cost."]
    return []


def validate_diegetic_integration(
    deltas: Dict[str, int],
    narrative: str,
) -> List[str]:
    errors: List[str] = []
    lower = narrative.lower()
    for key, value in deltas.items():
        if value == 0:
            continue
        if key.lower() not in lower:
            errors.append(f"Delta for {key} not referenced in narrative.")
    return errors


def validate_forbidden_phrases(narrative: str) -> List[str]:
    errors: List[str] = []
    lower = narrative.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            errors.append(f"Forbidden phrase found: {phrase}.")
    return errors


def validate_sensory_anchors(narrative: str) -> List[str]:
    lower = narrative.lower()
    if any(anchor in lower for anchor in REQUIRED_ANCHORS):
        return []
    return ["Narrative lacks required sensory anchors (mud/rust/cold)."]


def validate_outcome_log(
    deltas: Dict[str, int],
    outcome_log: str,
) -> List[str]:
    errors: List[str] = []
    if "<div class=\"outcome-log\">" not in outcome_log:
        errors.append("Outcome log missing required container.")
        return errors
    lower = outcome_log.lower()
    for key, value in deltas.items():
        if value == 0:
            continue
        if key.lower() not in lower:
            errors.append(f"Outcome log missing entry for {key}.")
    return errors


def validate_survivor_afflictions(
    previous: EngineState,
    draft: EngineState,
) -> List[str]:
    errors: List[str] = []
    previous_map = {
        survivor.survivor_id: survivor.afflictions
        for survivor in previous.survivors.roster
    }
    for survivor in draft.survivors.roster:
        old_afflictions = previous_map.get(survivor.survivor_id, [])
        if any(affliction not in survivor.afflictions for affliction in old_afflictions):
            errors.append(
                f"Afflictions removed for survivor {survivor.survivor_id}."
            )
    return errors


def validate_population_integrity(state: EngineState) -> List[str]:
    errors: List[str] = []
    roster_ids = {survivor.survivor_id for survivor in state.survivors.roster}
    deceased_ids = {survivor.survivor_id for survivor in state.survivors.deceased}
    if roster_ids & deceased_ids:
        errors.append("Survivor appears in roster and deceased list.")
    return errors


def validate_threat_escalation(
    previous: EngineState,
    draft: EngineState,
) -> List[str]:
    errors: List[str] = []
    population_delta = (
        len(draft.survivors.roster) - len(previous.survivors.roster)
    )
    for threat in draft.threats.active_threats:
        if threat.unaddressed_turns > 2 and population_delta >= 0:
            errors.append(
                f"Threat {threat.threat_id} escalated without casualty."
            )
    return errors


def validate_terminal_population(state: EngineState) -> List[str]:
    if len(state.survivors.roster) == 0:
        return ["Settlement lost: population is zero."]
    return []


def validate_commander_anchor(
    previous: EngineState,
    draft: EngineState,
    narrative: str,
) -> List[str]:
    errors: List[str] = []
    if previous.commander.visual_anchor != draft.commander.visual_anchor:
        errors.append("Commander visual anchor drift detected.")
    if draft.commander.visual_anchor and draft.commander.visual_anchor not in narrative:
        errors.append("Commander visual anchor missing from narrative.")
    return errors


def validate_friction_resolve(
    state: EngineState,
    narrative: str,
) -> List[str]:
    errors: List[str] = []
    lower = narrative.lower()
    if state.flags.friction >= 40 and "sabotage" not in lower and "mutiny" not in lower:
        errors.append("High friction without sabotage or mutiny signal in narrative.")
    if state.flags.resolve < 20 and "fragment" not in lower:
        errors.append("Low resolve without fragmented narrative signal.")
    return errors


def validate_turn(
    previous: EngineState,
    draft: EngineState,
    narrative: str,
    outcome_log: str,
    deltas: Dict[str, int],
) -> List[str]:
    errors: List[str] = []
    errors.extend(validate_map_grid(draft.world.map_grid))
    errors.extend(validate_vitals(draft.world.vitals.__dict__))
    errors.extend(validate_conservation(deltas))
    errors.extend(validate_diegetic_integration(deltas, narrative))
    errors.extend(validate_forbidden_phrases(narrative))
    errors.extend(validate_sensory_anchors(narrative))
    errors.extend(validate_outcome_log(deltas, outcome_log))
    errors.extend(validate_survivor_afflictions(previous, draft))
    errors.extend(validate_population_integrity(draft))
    errors.extend(validate_threat_escalation(previous, draft))
    errors.extend(validate_terminal_population(draft))
    errors.extend(validate_friction_resolve(draft, narrative))
    errors.extend(validate_commander_anchor(previous, draft, narrative))
    return errors
