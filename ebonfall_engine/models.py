from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence


class Season(str, Enum):
    AUTUMN = "Autumn"
    WINTER = "Winter"
    SPRING = "Spring"
    SUMMER = "Summer"


class Phase(str, Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    NIGHT = "Night"


class SettlementTier(str, Enum):
    ENCAMPMENT = "Encampment"
    VILLAGE = "Village"
    TOWN = "Town"
    CITY = "City"


class Ideology(str, Enum):
    ALTRUISM = "Altruism"
    PRAGMATISM = "Pragmatism"
    INDIVIDUALISM = "Individualism"


class SurvivorStatus(str, Enum):
    HEALTHY = "Healthy"
    WOUNDED = "Wounded"
    SICK = "Sick"
    GRIM = "Grim"


class TileType(str, Enum):
    RUINS = "Ruins"
    BLIGHT = "Blight"
    FOREST = "Forest"
    SCRUBLAND = "Scrubland"
    RIVER = "River"
    HILLS = "Hills"
    PLAINS = "Plains"


@dataclass(frozen=True)
class Resources:
    food: int
    wood: int
    stone: int
    iron: int


@dataclass(frozen=True)
class Vitals:
    health: int
    morale: int
    defense: int


@dataclass(frozen=True)
class CommanderState:
    name: str
    origin: str
    visual_anchor: str
    traits: Dict[str, int]
    ideology: Ideology


@dataclass(frozen=True)
class Structure:
    structure_id: str
    name: str


@dataclass(frozen=True)
class Tile:
    tile_type: TileType
    explored: bool


@dataclass(frozen=True)
class WorldState:
    turn: int
    season: Season
    phase: Phase
    settlement_tier: SettlementTier
    resources: Resources
    vitals: Vitals
    structures: List[Structure]
    map_grid: List[List[Tile]]


@dataclass(frozen=True)
class Survivor:
    survivor_id: str
    name: str
    role: str
    status: SurvivorStatus
    afflictions: List[str]


@dataclass(frozen=True)
class SurvivorState:
    roster: List[Survivor]
    deceased: List[Survivor]


@dataclass(frozen=True)
class Threat:
    threat_id: str
    threat_type: str
    start_turn: int
    unaddressed_turns: int


@dataclass(frozen=True)
class ThreatState:
    active_threats: List[Threat]


@dataclass(frozen=True)
class SimulationFlags:
    friction: int
    resolve: int


@dataclass(frozen=True)
class ChronicleEntry:
    turn: int
    narrative: str
    outcome_log: str
    deltas: Dict[str, int]


@dataclass(frozen=True)
class ChronicleState:
    history: List[ChronicleEntry] = field(default_factory=list)
    resource_trends: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineState:
    commander: CommanderState
    world: WorldState
    survivors: SurvivorState
    threats: ThreatState
    flags: SimulationFlags
    chronicle: ChronicleState


@dataclass(frozen=True)
class TurnAction:
    description: str
    resource_deltas: Dict[str, int] = field(default_factory=dict)
    vital_deltas: Dict[str, int] = field(default_factory=dict)
    friction_delta: int = 0
    resolve_delta: int = 0
    structures_added: List[Structure] = field(default_factory=list)
    structures_removed: List[str] = field(default_factory=list)
    threats_addressed: List[str] = field(default_factory=list)
    deceased_ids: List[str] = field(default_factory=list)
    afflictions_added: Dict[str, List[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class TurnInput:
    action: TurnAction
    phase_override: Optional[Phase] = None


@dataclass(frozen=True)
class NarrativeResult:
    narrative: str
    outcome_log: str
    deltas: Dict[str, int]
    system_prompt: str


@dataclass(frozen=True)
class TurnResult:
    success: bool
    errors: List[str]
    state: EngineState
    narrative_result: Optional[NarrativeResult]
