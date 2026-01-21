Based on the EBONFALL_OS v2.5 architecture, the following state variables are tracked programmatically or maintained as logical constants.
1. Player State (The Commander)
Identity Identity: Fixed name and origin (background).
Visual Anchor: A persistent visualDescription string used as a hard constraint for all image generation to ensure physical continuity.
Trait Matrix: A collection of traits derived from background and philosophy that modify resource efficiency or narrative outcomes.
Ideology/Creed: The current social policy (Altruism, Pragmatism, or Individualism) which acts as a filter for choice generation.
2. World & Settlement State
Temporal Markers: turn (Day count), season (environmental modifier), and phase (Morning, Afternoon, Night).
Settlement Tier: Current structural evolution (Encampment, Village, Town, City).
Resource Cache: Integer values for food, wood (fuel), stone, and iron.
Vital Signs:
Health: Average physical condition of the populace (0-100%).
Morale: The psychological spirit of the camp (0-100%).
Defense: Structural and martial resistance to threats (0-100%).
Structural Manifest: An array of structures (e.g., "Palisade," "Medic's Tent") that physically exists in the village view and narrative.
Cartographic Grid: A 5x5 mapGrid tracking explored coordinates and tile types (Ruins, Blight, Forest, etc.).
3. Survivor State (Entity Tracking)
Roster: A list of unique Survivor objects.
Status Ledger: Tracking specific conditions (Healthy, Wounded, Sick, Grim).
Permanent Scars: An afflictions array representing persistent physical or mental damage (e.g., "Limp," "Smog-Cough").
The Fallen: A separate deceased list used to track population loss and generate narrative "The Ledger of Souls" entries.
4. Session & UI State
The Chronicle: history array storing turn-by-turn narratives and choices taken for long-term context injection.
Resource Trends: Calculated deltas (e.g., food: -5) used to display trend icons (↑/↓) on the dashboard.
Processing Flags: loading (AI generation state), isPreparingSouls (initial portrait generation phase), and isAnalyzing (character creation image processing).
5. Hidden Flags & Algorithmic Thresholds
Friction (Internal Tension): A hidden/visible counter (0-100).
Trigger: At 40+, internal sabotage and theft events become active.
Resolve (Unity): A value representing the settlement's collective "will to live."
Trigger: Below 20, descriptions become fragmented and choices more desperate.
Threat Persistence: A tracking flag for activeThreats.
Rule: If a threat persists unaddressed for >2 turns, the engine is forced to manifest a physical casualty.
Law of Conservation Flag: A logical check ensuring every "Positive Delta" in resources is accompanied by a "Negative Delta" in health, wood, or friction.