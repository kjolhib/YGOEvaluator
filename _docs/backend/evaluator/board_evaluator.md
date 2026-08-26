# board_evaluator.py

status: [done]
last updated: [26-08-2026]


**Path:** `backend/app/evaluator/BoardEvaluator.py`

## Context
This is the first slice of the Evaluation layer (see `_docs/workflow.md`'s Architecture section and `_docs/plan/_evaluator_plan.md`): a scan over a `BoardState` snapshot that identifies disruptions using the hand-curated `DISRUPTION_REGISTRY`, with no card-text parsing, no judgment about how threatening a finding is, and no synthesis across findings.

## Purpose
Scan both players' in-scope zones on a `BoardState`, cross-reference each `CardInstance` against a disruption registry, and return every live disruption found — applying hard/soft once-per-turn collapsing per card.

## Main Components

- `_collect_instances(player) -> list[CardInstance]` — flattens every `CardInstance` out of a player's in-scope zones: `hand`, `monster_zones`, `spell_trap_zones`, `field_spell_zones`. Deliberately excludes GY/banishment, and does not scan `BoardState.extra_monster_zones` (the shared EMZ slots live on `BoardState`, not `Player` — see Notes).
- `_findings_for_player(player, registry) -> list[DisruptionFinding]` — the core scan:
  1. Calls `lookup_disruption` (see `DisruptionSource.md`) on every collected instance.
  2. Resolves each match's `DisruptionType` via `source.disruption_by_zone[(card_instance.current_zone_type, card_instance.current_position)]`. If the card is in 
  3. Groups matches by **`(card_name, disruption_type)`**, not just `card_name` — the same name can resolve to different `DisruptionType`s depending on which `(zone, position)` a given copy is in, so two copies in different states must not be merged into one ambiguous group.
  4. For each group: `HARD` scope → one `DisruptionFinding` with `instance_count = len(group)`; `SOFT` scope → one `DisruptionFinding` per instance, each `instance_count = 1`.
- `evaluate(board_state, history=None, registry=DISRUPTION_REGISTRY) -> list[DisruptionFinding]` — runs `_findings_for_player` for `board_state.player` then `board_state.opponent`, concatenates. Public entry point.
  - `history` — reserved, unused. Per `_docs/workflow.md`'s extensibility requirement, exists now so a future `History`/`GameLog` object can be introduced without reworking this signature or its call sites. Passing anything here has no effect yet.
  - `registry` — overridable (defaults to `DISRUPTION_REGISTRY` from `app.static.disruption_registry`), so tests (or a future per-format registry) can substitute a different one without monkeypatching.

## How It Fits In
Depends on `BoardState`/`Player` (`app.core`), `DisruptionSource`/`lookup_disruption` (`app.evaluator.DisruptionSource`), `DISRUPTION_REGISTRY` (`app.static.disruption_registry`), `DisruptionFinding`, and `OncePerTurnScope`/`DisruptionType` (`app.type_defs.type_disruption`). `evaluate` is the module's only intended external entry point.

## Notes
The shared Extra Monster Zone slots (`BoardState.extra_monster_zones`) are not currently scanned — `_collect_instances` only reads from `Player`'s own zones. A card whose `CardInstance.current_zone_type` is `EXTRA_MONSTER_ZONE` can still match correctly (the lookup is purely against the instance's own `current_zone_type`/`current_position` fields, not which physical `FieldZone` container holds it), but nothing currently places `CardInstance`s into `BoardState.extra_monster_zones` and has them scanned automatically — a real EMZ-resident card would need to be manually represented with the right `current_zone_type` in a zone `_collect_instances` does scan, or this function extended to also read `board_state.extra_monster_zones`. Worth revisiting once EMZ-specific disruptions come up in a real registry entry.
