# board_evaluator.py

[status]: [done]
[last updated]: [20-10-2026]


**Path:** `backend/app/evaluator/board_evaluator.py`

## Context
This is the first slice of the Evaluation layer (see `_docs/workflow.md`'s Architecture section and `_docs/plan/_evaluator_plan.md`): a scan over a `BoardState` snapshot that identifies disruptions using the hand-curated registry, with no card-text parsing, no judgment about how threatening a finding is, and no synthesis across findings.

Registry entries are described per **effect** (see `disruption_source.md`), so this module groups and collapses findings per effect, not per card.

## Purpose
Scan both players' in-scope zones on a `BoardState`, cross-reference each `CardInstance` against a disruption registry, and return every live disruption found — applying hard/soft once-per-turn collapsing per effect.

## Main Components

- `_collect_instances(player, owned_emz_zone=None) -> list[CardInstance]` — flattens every `CardInstance` out of a player's in-scope zones: `hand`, `monster_zones`, `spell_trap_zones`, `field_spell_zones`, plus the shared Extra Monster Zone slot attributed to that player (see Notes). Deliberately excludes GY/banishment. The EMZ slot goes into the same flat list, not a separate pass, so a hard-OPT effect split between e.g. a monster zone and the player's EMZ slot still collapses into one finding.
- `_findings_for_player(player, registry, owned_emz_zone=None) -> list[DisruptionFinding]` — the core scan:
  1. Calls `lookup_disruption` (see `disruption_source.md`) on every collected instance. It returns the list of that card's effects that are live in the instance's current `(zone, position)`; an empty list means skip.
  2. For each returned effect, resolves its `DisruptionType` via `effect.disruption_by_zone[(card_instance.current_zone_type, card_instance.current_position)]`.
  3. Groups matches by **`(card_name, effect.label, disruption_type)`**. The label is part of the key because one card can have several live effects that must stay separate. The `DisruptionType` is part of it because the same effect can resolve to different types depending on which `(zone, position)` a given copy is in, so two copies in different states must not be merged into one ambiguous group. `Player` is not part of the key: this function runs once per player, which is what keeps the two sides apart (`Player` is also an unhashable dataclass).
  4. Hands the groups to `_find`.
- `_find(player, matches) -> list[DisruptionFinding]` — turns groups into findings, reading `opt_scope` and `categories` from the group's **effect**: `HARD` → one `DisruptionFinding` with `instance_count = len(group)`; `SOFT` → one `DisruptionFinding` per instance, each `instance_count = 1`. Anything that is not `HARD` takes the soft branch.
- `evaluate(board_state, history=None, registry=DISRUPTION_REGISTRY) -> list[DisruptionFinding]` — runs `_findings_for_player` for `board_state.player` (given `extra_monster_zones[0]`) then `board_state.opponent` (given `extra_monster_zones[1]`), and concatenates. Public entry point.
  - `history` — reserved, unused. Per `_docs/workflow.md`'s extensibility requirement, exists now so a future `History`/`GameLog` object can be introduced without reworking this signature or its call sites. Passing anything here has no effect yet.
  - `registry` — overridable. The default is `GLOBAL_REGISTRY` from `app.static.registry` (imported under the name `DISRUPTION_REGISTRY`), so tests (or a future per-format registry) can substitute a different one without monkeypatching.

## How It Fits In
Depends on `BoardState`/`Player`/`Zone` (`app.core`), `DisruptionEffect`/`DisruptionSource`/`lookup_disruption` (`app.evaluator.disruption_source`), `GLOBAL_REGISTRY` (`app.static.registry`), `DisruptionFinding`, and `OncePerTurnScope`/`DisruptionType` (`app.static.type_defs.type_disruption`). `evaluate` is the module's only intended external entry point.

## Notes
**Findings are per effect.** `len(findings)` still means "how many independent things are live", but a card with several live effects now contributes several findings. A face-up Baronne de Fleur yields two (omni negation and targeted destruction); two copies yield two findings with `instance_count == 2` each, since both of her effects are hard-OPT.

**Effect labels are assumed unique within a card.** The grouping key relies on it, and nothing enforces it at construction yet (see `disruption_source.md`).

**The shared Extra Monster Zone is scanned.** `BoardState.extra_monster_zones` is not a `Player` attribute, so it has no inherent owner. Real EMZ rules let either player claim either physical slot at runtime (the first monster placed into any EMZ claims it, and the other player is then restricted to the remaining slot). That contested behaviour is deliberately not modelled. Instead `evaluate` attributes `extra_monster_zones[0]` to `board_state.player` and `[1]` to `board_state.opponent` as a fixed convention, purely for evaluation. It has little practical impact today, since which physical slot a monster sits in rarely matters, but the real behaviour can be revisited once the frontend needs it.

The convention is deliberately kept local to the evaluator. An earlier attempt added an `owner` field to `Zone`; it was reverted because it coupled the instance layer's `Zone` to `Player` for the sake of this one case, needed a circular import plus `repr=False, compare=False` to stop `Zone` and `Player` recursing into each other, and showed the ownership question belonged in the evaluator, not the zone.
