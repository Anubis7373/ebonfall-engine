import unittest
from dataclasses import replace
from unittest.mock import patch

from ebonfall_engine.engine import execute_turn, load_system_prompt
from ebonfall_engine.models import (
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
    NarrativeResult,
)


def build_state() -> EngineState:
    map_grid = [
        [Tile(tile_type=TileType.FOREST, explored=False) for _ in range(5)]
        for _ in range(5)
    ]
    commander = CommanderState(
        name="Commander",
        origin="Foundry",
        visual_anchor="scarred hands and a rust-stained coat",
        traits={"resolve": 1},
        ideology=Ideology.PRAGMATISM,
    )
    world = WorldState(
        turn=1,
        season=Season.AUTUMN,
        phase=Phase.MORNING,
        settlement_tier=SettlementTier.ENCAMPMENT,
        resources=Resources(food=10, wood=10, stone=0, iron=0),
        vitals=Vitals(health=80, morale=60, defense=20),
        structures=[Structure(structure_id="palisade", name="Palisade")],
        map_grid=map_grid,
    )
    survivors = SurvivorState(
        roster=[
            Survivor(
                survivor_id="s1",
                name="Mara",
                role="Scout",
                status=SurvivorStatus.HEALTHY,
                afflictions=[],
            ),
            Survivor(
                survivor_id="s2",
                name="Garrick",
                role="Smith",
                status=SurvivorStatus.HEALTHY,
                afflictions=[],
            ),
        ],
        deceased=[],
    )
    threats = ThreatState(active_threats=[])
    flags = SimulationFlags(friction=10, resolve=30)
    chronicle = ChronicleState()
    return EngineState(
        commander=commander,
        world=world,
        survivors=survivors,
        threats=threats,
        flags=flags,
        chronicle=chronicle,
    )


class EngineTests(unittest.TestCase):
    def test_turn_success_with_cost(self) -> None:
        state = build_state()
        action = TurnAction(
            description="Scavenge wood and food",
            resource_deltas={"Food": 4, "Wood": -2},
            vital_deltas={"Health": -1},
            friction_delta=1,
        )
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertTrue(result.success)
        self.assertEqual(len(result.state.chronicle.history), 1)
        self.assertIn("Food", result.narrative_result.narrative)
        self.assertIn("Wood", result.narrative_result.narrative)

    def test_conservation_failure(self) -> None:
        state = build_state()
        action = TurnAction(
            description="Free windfall",
            resource_deltas={"Food": 4},
        )
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("Conservation violated", " ".join(result.errors))

    def test_missing_narrative_justification_fails(self) -> None:
        state = build_state()
        action = TurnAction(
            description="Costly salvage",
            resource_deltas={"Food": 2, "Wood": -1},
        )
        narrative = "I record the shift. The mud clings to my boots."
        outcome_log = "<div class=\"outcome-log\"><ul><li>Food: +2</li><li>Wood: -1</li></ul></div>"
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        with patch(
            "ebonfall_engine.engine.generate_narrative",
            return_value=NarrativeResult(
                narrative=narrative,
                outcome_log=outcome_log,
                deltas={"Food": 2, "Wood": -1},
                system_prompt=system_prompt,
            ),
        ):
            result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("Delta for Food not referenced", " ".join(result.errors))

    def test_missing_outcome_log_fails(self) -> None:
        state = build_state()
        action = TurnAction(
            description="Costly salvage",
            resource_deltas={"Food": 2, "Wood": -1},
        )
        narrative = "I record the shift: Food rose by 2; Wood fell by 1. The mud cracks."
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        with patch(
            "ebonfall_engine.engine.generate_narrative",
            return_value=NarrativeResult(
                narrative=narrative,
                outcome_log="",
                deltas={"Food": 2, "Wood": -1},
                system_prompt=system_prompt,
            ),
        ):
            result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("Outcome log missing", " ".join(result.errors))

    def test_threat_escalation_without_casualty_fails(self) -> None:
        state = build_state()
        state = EngineState(
            commander=state.commander,
            world=state.world,
            survivors=state.survivors,
            threats=ThreatState(
                active_threats=[
                    Threat(
                        threat_id="t1",
                        threat_type="Starvation",
                        start_turn=1,
                        unaddressed_turns=2,
                    )
                ]
            ),
            flags=state.flags,
            chronicle=state.chronicle,
        )
        action = TurnAction(description="Ignore threat")
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        with patch("ebonfall_engine.engine._apply_escalation", return_value=[]):
            result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("escalated without casualty", " ".join(result.errors))

    def test_internal_feelings_violation_fails(self) -> None:
        state = build_state()
        action = TurnAction(
            description="Costly salvage",
            resource_deltas={"Food": 2, "Wood": -1},
        )
        narrative = (
            "I feel hope as Food rose by 2 and Wood fell by 1. The mud hardens."
        )
        outcome_log = "<div class=\"outcome-log\"><ul><li>Food: +2</li><li>Wood: -1</li></ul></div>"
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        with patch(
            "ebonfall_engine.engine.generate_narrative",
            return_value=NarrativeResult(
                narrative=narrative,
                outcome_log=outcome_log,
                deltas={"Food": 2, "Wood": -1},
                system_prompt=system_prompt,
            ),
        ):
            result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("Forbidden phrase found", " ".join(result.errors))

    def test_affliction_removal_fails(self) -> None:
        state = build_state()
        survivor = state.survivors.roster[0]
        updated = Survivor(
            survivor_id=survivor.survivor_id,
            name=survivor.name,
            role=survivor.role,
            status=survivor.status,
            afflictions=["Limp"],
        )
        state = EngineState(
            commander=state.commander,
            world=state.world,
            survivors=SurvivorState(roster=[updated] + state.survivors.roster[1:], deceased=[]),
            threats=state.threats,
            flags=state.flags,
            chronicle=state.chronicle,
        )
        action = TurnAction(description="Routine check")
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        with patch(
            "ebonfall_engine.engine._apply_afflictions",
            return_value=[
                replace(updated, afflictions=[]),
                state.survivors.roster[1],
            ],
        ):
            result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("Afflictions removed", " ".join(result.errors))

    def test_commander_anchor_drift_fails(self) -> None:
        state = build_state()
        action = TurnAction(
            description="Hold position",
            resource_deltas={"Food": -1, "Wood": -1},
        )
        drifted_commander = replace(state.commander, visual_anchor="clean hands")
        drifted_state = EngineState(
            commander=drifted_commander,
            world=state.world,
            survivors=state.survivors,
            threats=state.threats,
            flags=state.flags,
            chronicle=state.chronicle,
        )
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        with patch("ebonfall_engine.engine.copy.deepcopy", return_value=drifted_state):
            result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertFalse(result.success)
        self.assertEqual(result.state, state)
        self.assertIn("visual anchor drift", " ".join(result.errors).lower())

    def test_threat_escalation_causes_casualty(self) -> None:
        state = build_state()
        state = EngineState(
            commander=state.commander,
            world=state.world,
            survivors=state.survivors,
            threats=ThreatState(
                active_threats=[
                    Threat(
                        threat_id="t1",
                        threat_type="Starvation",
                        start_turn=1,
                        unaddressed_turns=2,
                    )
                ]
            ),
            flags=state.flags,
            chronicle=state.chronicle,
        )
        action = TurnAction(description="Ignore threat")
        system_prompt = load_system_prompt("prompts/gm_system_prompt.txt")
        result = execute_turn(state, TurnInput(action=action), system_prompt)
        self.assertTrue(result.success)
        self.assertEqual(len(result.state.survivors.roster), 1)


if __name__ == "__main__":
    unittest.main()
