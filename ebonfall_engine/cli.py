from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .engine import execute_turn, load_system_prompt
from .models import (
    ChronicleState,
    CommanderState,
    EngineState,
    Ideology,
    Phase,
    Resources,
    Season,
    SettlementTier,
    SimulationFlags,
    Structure,
    Survivor,
    SurvivorState,
    SurvivorStatus,
    Threat,
    ThreatState,
    Tile,
    TileType,
    TurnAction,
    TurnInput,
    Vitals,
    WorldState,
)


def _enum_value(enum_cls: Any, value: str) -> Any:
    return enum_cls(value)


def load_state_from_fixture(path: Path) -> EngineState:
    payload = json.loads(path.read_text(encoding="utf-8"))

    commander = payload["commander"]
    commander_state = CommanderState(
        name=commander["name"],
        origin=commander["origin"],
        visual_anchor=commander["visual_anchor"],
        traits=commander.get("traits", {}),
        ideology=_enum_value(Ideology, commander["ideology"]),
    )

    world = payload["world"]
    resources = world["resources"]
    vitals = world["vitals"]
    structures = [
        Structure(structure_id=item["structure_id"], name=item["name"])
        for item in world.get("structures", [])
    ]
    map_grid = [
        [
            Tile(
                tile_type=_enum_value(TileType, tile["tile_type"]),
                explored=tile["explored"],
            )
            for tile in row
        ]
        for row in world["map_grid"]
    ]
    world_state = WorldState(
        turn=world["turn"],
        season=_enum_value(Season, world["season"]),
        phase=_enum_value(Phase, world["phase"]),
        settlement_tier=_enum_value(SettlementTier, world["settlement_tier"]),
        resources=Resources(
            food=resources["food"],
            wood=resources["wood"],
            stone=resources["stone"],
            iron=resources["iron"],
        ),
        vitals=Vitals(
            health=vitals["health"],
            morale=vitals["morale"],
            defense=vitals["defense"],
        ),
        structures=structures,
        map_grid=map_grid,
    )

    survivors = payload["survivors"]
    roster = [
        Survivor(
            survivor_id=item["survivor_id"],
            name=item["name"],
            role=item["role"],
            status=_enum_value(SurvivorStatus, item["status"]),
            afflictions=item.get("afflictions", []),
        )
        for item in survivors.get("roster", [])
    ]
    deceased = [
        Survivor(
            survivor_id=item["survivor_id"],
            name=item["name"],
            role=item["role"],
            status=_enum_value(SurvivorStatus, item["status"]),
            afflictions=item.get("afflictions", []),
        )
        for item in survivors.get("deceased", [])
    ]
    survivor_state = SurvivorState(roster=roster, deceased=deceased)

    threats = payload.get("threats", {})
    active_threats = [
        Threat(
            threat_id=item["threat_id"],
            threat_type=item["threat_type"],
            start_turn=item["start_turn"],
            unaddressed_turns=item["unaddressed_turns"],
        )
        for item in threats.get("active_threats", [])
    ]
    threat_state = ThreatState(active_threats=active_threats)

    flags = payload["flags"]
    simulation_flags = SimulationFlags(
        friction=flags["friction"],
        resolve=flags["resolve"],
    )

    chronicle_state = ChronicleState()

    return EngineState(
        commander=commander_state,
        world=world_state,
        survivors=survivor_state,
        threats=threat_state,
        flags=simulation_flags,
        chronicle=chronicle_state,
    )


def load_turn_input(data: Dict[str, Any]) -> TurnInput:
    action_data = data["action"]
    action = TurnAction(
        description=action_data["description"],
        resource_deltas=action_data.get("resource_deltas", {}),
        vital_deltas=action_data.get("vital_deltas", {}),
        friction_delta=action_data.get("friction_delta", 0),
        resolve_delta=action_data.get("resolve_delta", 0),
        structures_added=[
            Structure(structure_id=item["structure_id"], name=item["name"])
            for item in action_data.get("structures_added", [])
        ],
        structures_removed=action_data.get("structures_removed", []),
        threats_addressed=action_data.get("threats_addressed", []),
        deceased_ids=action_data.get("deceased_ids", []),
        afflictions_added=action_data.get("afflictions_added", {}),
    )
    phase_override = data.get("phase_override")
    if phase_override:
        return TurnInput(action=action, phase_override=_enum_value(Phase, phase_override))
    return TurnInput(action=action)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single Ebonfall turn.")
    parser.add_argument(
        "--fixture",
        type=Path,
        required=True,
        help="Path to initial EngineState fixture JSON.",
    )
    parser.add_argument(
        "--turn",
        type=Path,
        help="Path to TurnInput JSON. If omitted, reads from stdin.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fixture_path = args.fixture
    if args.turn:
        turn_payload = json.loads(args.turn.read_text(encoding="utf-8"))
    else:
        turn_payload = json.loads(sys.stdin.read())

    state = load_state_from_fixture(fixture_path)
    turn_input = load_turn_input(turn_payload)

    repo_root = Path(__file__).resolve().parents[1]
    system_prompt_path = repo_root / "prompts" / "gm_system_prompt.txt"
    system_prompt = load_system_prompt(str(system_prompt_path))

    result = execute_turn(state, turn_input, system_prompt)
    if not result.success or result.narrative_result is None:
        for error in result.errors:
            print(error)
        raise SystemExit(1)

    print(result.narrative_result.narrative)
    print(result.narrative_result.outcome_log)


if __name__ == "__main__":
    main()
