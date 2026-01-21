from __future__ import annotations

import copy
from dataclasses import replace
from typing import Dict, List

from .models import (
    ChronicleEntry,
    ChronicleState,
    EngineState,
    NarrativeResult,
    Resources,
    Survivor,
    SurvivorState,
    Threat,
    ThreatState,
    TurnAction,
    TurnInput,
    TurnResult,
    Vitals,
)
from .narrative import generate_narrative
from .validation import validate_turn


def load_system_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _apply_resource_deltas(resources: Resources, deltas: Dict[str, int]) -> Resources:
    return Resources(
        food=resources.food + deltas.get("Food", 0),
        wood=resources.wood + deltas.get("Wood", 0),
        stone=resources.stone + deltas.get("Stone", 0),
        iron=resources.iron + deltas.get("Iron", 0),
    )


def _apply_vital_deltas(vitals: Vitals, deltas: Dict[str, int]) -> Vitals:
    return Vitals(
        health=vitals.health + deltas.get("Health", 0),
        morale=vitals.morale + deltas.get("Morale", 0),
        defense=vitals.defense + deltas.get("Defense", 0),
    )


def _apply_structures(state: EngineState, action: TurnAction) -> List:
    structures = [structure for structure in state.world.structures]
    if action.structures_removed:
        structures = [
            structure
            for structure in structures
            if structure.structure_id not in action.structures_removed
        ]
    if action.structures_added:
        structures.extend(action.structures_added)
    return structures


def _apply_afflictions(state: EngineState, action: TurnAction) -> List[Survivor]:
    roster: List[Survivor] = []
    additions = action.afflictions_added
    for survivor in state.survivors.roster:
        added = additions.get(survivor.survivor_id, [])
        if added:
            roster.append(
                Survivor(
                    survivor_id=survivor.survivor_id,
                    name=survivor.name,
                    role=survivor.role,
                    status=survivor.status,
                    afflictions=survivor.afflictions + added,
                )
            )
        else:
            roster.append(survivor)
    return roster


def _apply_deaths(
    state: EngineState,
    action: TurnAction,
    escalation_deaths: List[Survivor],
) -> SurvivorState:
    roster = [survivor for survivor in state.survivors.roster]
    deceased = [survivor for survivor in state.survivors.deceased]
    ids_to_remove = set(action.deceased_ids + [s.survivor_id for s in escalation_deaths])
    if ids_to_remove:
        for survivor in roster[:]:
            if survivor.survivor_id in ids_to_remove:
                roster.remove(survivor)
                deceased.append(survivor)
    for survivor in escalation_deaths:
        if survivor in roster:
            roster.remove(survivor)
        if survivor not in deceased:
            deceased.append(survivor)
    return SurvivorState(roster=roster, deceased=deceased)


def _advance_threats(state: EngineState, action: TurnAction) -> ThreatState:
    addressed = set(action.threats_addressed)
    updated: List[Threat] = []
    for threat in state.threats.active_threats:
        if threat.threat_id in addressed:
            continue
        updated.append(
            Threat(
                threat_id=threat.threat_id,
                threat_type=threat.threat_type,
                start_turn=threat.start_turn,
                unaddressed_turns=threat.unaddressed_turns + 1,
            )
        )
    return ThreatState(active_threats=updated)


def _apply_escalation(state: EngineState) -> List[Survivor]:
    escalation_deaths: List[Survivor] = []
    for threat in state.threats.active_threats:
        if threat.unaddressed_turns > 2 and state.survivors.roster:
            escalation_deaths.append(state.survivors.roster[0])
    return escalation_deaths


def _collect_deltas(action: TurnAction) -> Dict[str, int]:
    deltas: Dict[str, int] = {}
    for key, value in action.resource_deltas.items():
        deltas[key] = deltas.get(key, 0) + value
    for key, value in action.vital_deltas.items():
        deltas[key] = deltas.get(key, 0) + value
    if action.friction_delta:
        deltas["Friction"] = deltas.get("Friction", 0) + action.friction_delta
    if action.resolve_delta:
        deltas["Resolve"] = deltas.get("Resolve", 0) + action.resolve_delta
    if action.deceased_ids:
        deltas["Population"] = deltas.get("Population", 0) - len(action.deceased_ids)
    return deltas


def execute_turn(
    state: EngineState,
    turn_input: TurnInput,
    system_prompt: str,
) -> TurnResult:
    if len(state.survivors.roster) == 0:
        return TurnResult(
            success=False,
            errors=["Settlement lost: population is zero."],
            state=state,
            narrative_result=None,
        )

    action = turn_input.action
    draft = copy.deepcopy(state)

    if turn_input.phase_override:
        draft = replace(draft, world=replace(draft.world, phase=turn_input.phase_override))

    resources = _apply_resource_deltas(draft.world.resources, action.resource_deltas)
    vitals = _apply_vital_deltas(draft.world.vitals, action.vital_deltas)
    structures = _apply_structures(draft, action)

    draft = replace(
        draft,
        world=replace(draft.world, resources=resources, vitals=vitals, structures=structures),
        flags=replace(
            draft.flags,
            friction=draft.flags.friction + action.friction_delta,
            resolve=draft.flags.resolve + action.resolve_delta,
        ),
    )

    roster_with_afflictions = _apply_afflictions(draft, action)
    draft = replace(draft, survivors=replace(draft.survivors, roster=roster_with_afflictions))

    draft = replace(draft, threats=_advance_threats(draft, action))
    escalation_deaths = _apply_escalation(draft)
    survivors_after_deaths = _apply_deaths(draft, action, escalation_deaths)
    draft = replace(draft, survivors=survivors_after_deaths)

    deltas = _collect_deltas(action)
    if escalation_deaths:
        deltas["Population"] = deltas.get("Population", 0) - len(escalation_deaths)

    narrative_result = generate_narrative(draft, deltas, system_prompt)
    errors = validate_turn(
        state,
        draft,
        narrative_result.narrative,
        narrative_result.outcome_log,
        deltas,
    )

    if errors:
        return TurnResult(
            success=False,
            errors=errors,
            state=state,
            narrative_result=narrative_result,
        )

    history = list(draft.chronicle.history)
    history.append(
        ChronicleEntry(
            turn=draft.world.turn,
            narrative=narrative_result.narrative,
            outcome_log=narrative_result.outcome_log,
            deltas=narrative_result.deltas,
        )
    )
    draft = replace(draft, chronicle=replace(draft.chronicle, history=history))

    return TurnResult(
        success=True,
        errors=[],
        state=draft,
        narrative_result=narrative_result,
    )
