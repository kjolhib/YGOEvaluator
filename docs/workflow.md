# Yu-Gi-Oh Decision Evaluator — Workflow & Architecture Notes

## Project Goal

### What it **is**

A format-scoped tool that evaluates a Yu-Gi-Oh board state, classifies the
complexity/type of decision present (e.g. disruption risk, resource trade,
bluff spot), and optionally suggests next steps (this is currently a pipe-dream that may use ML). Primary motivation is
lowering the learning curve for newer players.

It attempts to introduce newer players who know *how* to play the game on a *mechanics*-level, but don't yet understand the deeper decision making that is required.

This can also be used for players learning new decks, as a way to showcase what an endboard can do. Hopefully the player can then use this information to reason about *why* certain decisions are made, rather than just have an answer provided to them.

Both of the above hope to act solely as **guides**.

!!!IMPORTANT!!!
The player *themselves* should be making **informed** decisions based on this guide, *other* guides, and their **own** preferences, not taking any single guide as the only source of truth.

### What it **is not**

This project's goals are not the following:
- A simulator like EdoPro, DuelingNexus, or even Master Duel.
  - Simulators already exist.
  - I do not think I can bring anything unique to the table.
  - This can be thought of as **similar** to **DuelingBook**. It is up to the player to determine the legality of board states.
- Suggest the *most optimal* next step.
  - I do not believe in *telling* someone that "this is the best option here". 
  - This is because, as I learned playing the game, this is a 2 player game. Game 1, you don't know what they're playing, and you need to make decisions based on what they *may* or *may not* have.
  - However, this is still an open question to the scope of this project. In the future, a distant future, I may incorporate AI as an **alternative** that tries to explain the board state. Note, this AI will **not** replace the existing architecture for classifying board states.
- Create an engine that can parse the "language of Yugioh".
  - This is something that I thought was already solved, but quickly came to realise how difficult it is.
  - I believe this problems is currently an unsolved NLP (non-linear programming) problem, and as a side project of a single dude, I don't think it's realistic given my limited genius. I'll leave this to the hivemind!

## Why Not Full ML / RL From the Start

Existing projects (e.g. `ygo-agent`, using deep RL + LLMs to train agents 
that play the full game) require significant computing power (multi-GPU, multi-day
training runs) to be effective. That scale of approach isn't viable or
necessary for a single-person side project.

Nor do I want to build something that completely takes over the player. I want the *player* to play and *learn* the game, but just easier. I do not think bad of the creators of `ygo-agent`, I believe it's a step to the right place - in fact, I was inspired by them to create this project.

That being said, the classification of boards isn't deterministic. It is heavily dynamic and chnages with the simplest board interactions. The prospect of creating an AI trained on Yugioh data integrated into this project *is* a pipe-dream I have. 

## Competitive Landscape (Niche Check)

- **Deck builders / meta tools** (YGOPRODeck, Dueling Nexus, EdoPro, etc.) — focus on
  deckbuilding, synergy, and meta analysis. Not in-duel decision evaluation.
- **ygo-agent** — full RL/LLM agent aiming to play at or above expert level.
  Heavy compute requirement, agentic (plays *for* the user) rather than
  pedagogical (teaches the user).
- **Toy/inspired projects** (e.g. MCTS + behavior-tree board evaluators) —
  built on simplified, non-real card pools.

**Gap identified:** no existing tool does real-time, in-duel
disruption/threat assessment on the real card pool, scoped per-format, aimed
at *teaching* a player to read a board rather than playing for them or
building a deck. This is the niche this project targets.

## Core Design Principle: Format Scoping

Instead of attempting to model the entire game and every card ever printed,
the system is scoped per-format. Each format is a self-contained
configuration: legal card pool, banlist, known archetypes, and a registry of
known disruption sources relevant to that format.

For example, one of my least-favourite formats to ever play was 2024 Snake-Eyes/Tenpai/Yubel format.
Begrudgingly I would create a format for them in this project, and store all meta-relevant cards in the card pool for this format, as well as existing staples such as Ash Blossom, and board breakers. 
The goal here is to simulate the format as best as possible. 

I will try to include as many rogue decks as possible per format, but there's almost infinite out there.

This is the project's main extensibility story: adding support for a new format means adding a new config, not modifying the engine. 
This however does mean that this project cannot view or provide a service for classifying some random board given the entire card pool of Yugioh. But I believe this can be extended as another config, and I just don't think I'll have the time or resources to do that.

## Architecture: Four Layers

### 1. Static / Reference Layer — "rules of the world"

Data that does not change during a duel.

- `Card` — base identity: name, type, attribute, level/rank, archetype tags.
- `EffectTemplate` — describes the *kind* of effect a card has (trigger
  condition, cost, target requirements, resolution type), independent of any
  specific game instance.
- `Format` — a named ruleset/card pool: banlist, legal cards, and the
  "known disruptions" registry for that format.

This layer is the plugin/extensibility point for new formats.

### 2. Instance Layer — "this specific game" state

- `GameState` - the real "duel" that is happening between 2 players. This governs all of the below entities.
- `BoardState` — full snapshot of both players' zones plus turn/phase metadata. **This is the primary object the evaluator reads.**
- `CardInstance` — a `Card` + runtime state (current zone, position, counters, attached materials, negation status, etc.)
- `Zone` — container with rules about what can enter/leave (hand, field, GY, banished, extra deck).
- `Player` — owns zones, life points, and resource flags (e.g. normal summon used this turn).

### 3. Action / Resolution Layer — how state changes

- `Action` — something a player can do (activate, summon, attack). This does not check whether or not an action is legal. It mimicks DuelingBook's simulator as it allows nearly all actions for any type of card, and is up to the player to legalise it.
- `Resolver` / `GameEngine` — takes a `BoardState` + `Action`(s), produces a new `BoardState`. The only component allowed to mutate state. Since no legality evaluator is involved, all it does is validate the move to an existing zone.

Keeping `BoardState` effectively immutable (mutated only via the
`Resolver`) keeps the engine testable and lets `BoardState` snapshots be
handed to the evaluator without side-effect concerns.

### 4. Evaluation Layer — the actual product

Separate from the engine by design — reads `BoardState` only, never mutates
it.

- `DisruptionSource` — registry entry: "this card type, in this zone, under
  these conditions, represents a live disruption."
- `DisruptionType` - provides distinct classifications of disruptions.
  - For example, a Baronne is considered an `ActiveDisruption`.
  - Cupsy Yummy Way is considered a `PotentialDisruption`.
    - I do not have plans to make the engine smart enough to understand that Cupsy Yummy Way -> reborn Cookie + Snatchy from GY -> Cookie pop 1 -> quick-synchro into Cookie -> book 2.
  - In short, layered disruptions are all labelled as `PotentialDisruption`. I also hope this will get the player to actually *read* the card and reason *themselves* about why this is potentially something they need to worry about.
- `FormatGoals` / `DeckGoals` - this contains information about the goals of each deck and format.
  - It is something I will populate myself. 
  - For example, Yummy's primary goal is to dirupt the opponent using Herald and its Synchro monsters + Snatchy. Dracotail's primary goal is to outgrind the opponent using their trap cards which act doubly as disruption.
- `BoardEvaluator` — scans a `BoardState` and produces findings related to diruptions and other information.
  - The main objective of this board state is to identify disruptions.

### Potential Extensions

Here lists the potential features I intend to implement when the core features are refined enough for extension.

- `BoardEvaluator` - be able to identify key archetype's goals, including hybrid archetypes, and their common patterns.
  - I believe the evaluator should identify the deck, print out the deck's goals in the format.
  - Hybrid decks are also considered. The evaluator only needs to know the broad archetype of the cards present in the `BoardState`, and common hybrids such as Mitsurugi Yummy in 2025 format is something I can easily populate myself.
  - Again, the issue of the infinitness of the game means that there will be things, hybrid or not, that will be missed.
- `BoardState` / `GameState` - store history of the game, i.e. card effect activations last turn or prior to current board state.
  - History determines the grindgame and resources the deck may have. 
  - This is something that can be done by identifying common trends in a deck or a given format. 
  - Likely to non-deterministically and dynamically evaluate history, I'll need to train AI on RL/ML to recognise what the common trends mean.
  - Not high on priority.
- `Suggestion` / `DecisionClassification` — output type: tags plus ranked next steps.
  - Can be pre-determined by myself. But I am not a professional player, so I likely will go with an AI trained on professional data.
  - Training AI myself is computationally expensive and difficult. I am not an AI engineer, nor do I really understand the complexities of the maths behind it. This is something that is pushed to the furthest back, even when suggestions are considered mid-development.

## Current Phase: Static Board State Evaluation

**Decision:** for now, the system works on a single static `BoardState`
snapshot. No history/log tracking is implemented yet.

**Extensibility requirement:** the evaluator's interface should not assume
statelessness forever. Design `BoardEvaluator` to accept an optional history
context now (even if unused), so a future `History` / `GameLog` object can
be introduced later without reworking the evaluator's signature or call
sites.

Open question, deliberately deferred: how much history-awareness the
evaluator will eventually need (e.g. "this is a bluff because they didn't
use mana last turn" requires last-turn knowledge). Decision: don't resolve
this now — just leave the seam open.

## Workflow Diagram

```
Format (config) ──defines──> which Cards/EffectTemplates are legal
                                      │
CardInstances live in Zones ─────────┤
                                      ▼
                                BoardState (snapshot)
                                      │
                       ┌──────────────┴──────────────┐
                       ▼                              ▼
                  GameEngine                    BoardEvaluator
              (mutates via Actions)        (reads, classifies, suggests)
                                           (history context: optional,
                                            reserved for future use)
```

## Immediate Next Steps

1. Flesh out the **static layer** (`Card`, `EffectTemplate`, `Format`) for a
   small, hand-picked card pool (e.g. 50–100 cards from one format).
2. Flesh out the **instance layer** (`CardInstance`, `Zone`, `Player`,
   `BoardState`) sufficient to represent a realistic mid-duel snapshot.
3. Build a minimal `BoardEvaluator` that reads a hand-constructed
   `BoardState` and a small hand-written `DisruptionSource` registry to
   produce findings — no engine/resolver required yet to prove this out.
4. Defer: `Action`/`ChainLink`/`Resolver` (full engine), `History`/`GameLog`,
   and any ML phase.
