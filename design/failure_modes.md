As a senior engineer looking at the architecture of the Ebonfall Engine, there are several critical points where the experience will likely degrade or break immersion during an extended play session (50+ turns). These issues stem from the tension between the stateless nature of LLMs and the stateful requirements of a settlement builder.
1. Memory Decay (The "10-Turn Ghost")
The geminiService.ts currently slices the history to the last 10 turns: const recentHistory = history.slice(-10);.
The Break: On turn 50, the AI has completely forgotten the events of turn 5. If a major character died a heroic death or a specific monument was built early on, the AI will stop referencing them in its prose.
Inconsistency: You may see "hallucinated" callbacks where the AI references a past that never happened because it's trying to fill the void of its missing long-term memory.
2. Visual Schizophrenia (Environmental Drift)
While we pin the visualDescription of the Commander, the environment is generated based on the current structures list and a turn-specific visualDescription.
The Break: gemini-2.5-flash-image lacks persistent "seed" or spatial awareness. On turn 15, the "Medic's Tent" might look like a tattered Napoleonic canvas. On turn 16, it might look like a futuristic bio-hazard pod.
Inconsistency: The player’s mental map of the village will be constantly shattered by the AI’s varying interpretation of "Dark Fantasy Survival."
3. Economic Drift & Value Inflation
The game has no hard-coded "Price Table." The AI determines the stateUpdate.
The Break: On turn 5, the AI might decide 10 Wood is enough to build a "Palisade." On turn 40, it might demand 100 Wood for a "Watchtower."
Inconsistency: Because the AI doesn't have a fixed mathematical model of the economy, the "difficulty curve" isn't a curve—it's a jagged line. The game can become accidentally impossible or trivial based on the AI’s whim of what "feels" balanced in that specific prompt.
4. Survivor Identity Overlap
As the population grows or the deceased list becomes long, the prompt sent to Gemini becomes increasingly crowded with Survivor objects.
The Break: LLMs struggle with high-cardinality entity tracking. In a session with 15+ survivors, the AI will start bleeding traits from one character into another (e.g., giving the Healer’s dialogue to the Soldier).
Inconsistency: The "Ledger of Souls" becomes a lie. You might see a "Healthy" survivor described as dying in the narrative because the AI lost track of which object in the array was which.
5. The Map-Prose Disconnect
The mapGrid is a 5x5 array of characters. The AI sees this array but doesn't have a "spatial reasoning" engine.
The Break: A player might move to a "Forest" tile at (0,0), but the AI narrates a "Scrubland" or "Ruins" because it failed to map the coordinate to its internal narrative generation.
Inconsistency: The "Cartographer's View" (the UI map) will eventually disagree with the "Observer's Vision" (the narrative), leading the player to stop trusting the UI entirely.
6. Tone Exhaustion
The "Clinical/Visceral" prompt is a high-intensity constraint.
The Break: Over 100 turns, the AI will inevitably start repeating its "mud and rust" metaphors. The shock of the dark fantasy setting wears off as the engine runs out of novel ways to describe "acrid smog" and "freezing limbs."
Inconsistency: The world starts to feel like a Mad-Libs template rather than a reactive simulation.
7. Logical Dead-Ends
The engine has no "Win Condition" or "Endgame" logic in the code.
The Break: Once the 5x5 map is fully explored and the settlement reaches the "City" tier, the AI has no "new" data to work with. It will likely loop through the same three threats (Winter, Starvation, Mutiny).
Inconsistency: The player will feel the "gears" of the AI turning as it struggles to escalate the stakes without new mechanics, leading to a repetitive and frustrating loop of misery.
