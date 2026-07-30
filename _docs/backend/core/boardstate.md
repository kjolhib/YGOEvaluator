# Yu-Gi-Oh Decision Evaluator — Board State

**Path:** `backend/app/core/BoardState.py`

## Purpose
`BoardState` is the top-level Instance-layer object: it holds both players' fields plus turn/phase metadata, and is the primary object the evaluator will eventually read. It owns phase progression and is the entry point for applying a `PlayerAction` to the board.

## Attributes
- `player` / `opponent` (`Player`): the two players in the duel. Fixed identities — `player` doesn't change even as turns pass.
- `phase` (`TurnPhase`): the current phase within the current turn. Defaults to `S_DRAW_PHASE`.
- `turn_player` (`Player`, `init=False`): whichever of `player`/`opponent` is currently taking their turn. Set in `__post_init__` to `player`, and flipped in `advance_phase` when the turn wraps.
- `turn_number` (`int`): starts at 1, increments each time the phase order wraps back to `S_DRAW_PHASE`.
- `battle_phase_exists` (`bool`): whether the current turn has a Battle Phase. `False` for turn 1 (no attacking on the first turn) and toggled `True` once turn 2 begins.
- `extra_monster_zones` (`list[FieldZone]`): the 2 shared EMZ slots (`ZoneType.EXTRA_MONSTER_ZONE`), not owned by either individual `Player`.
- `_PHASE_ORDER` (`tuple[TurnPhase, ...]`): the canonical phase sequence, built once from `tuple(TurnPhase)` (enum declaration order).

## Methods
- `advance_phase() -> TurnPhase`: steps to the next phase in `_PHASE_ORDER`, with two skip rules layered on top of straight iteration:
  - if `battle_phase_exists` is `False`, all Battle Phase and Main Phase 2 sub-phases are skipped entirely (a turn with no Battle Phase goes straight from Main Phase 1 to the End Phase)
  - turn 1 specifically skips `S_BATTLE_PHASE` even though `battle_phase_exists` may already be `True` by then (first-turn-no-attack rule)

  Wrapping past `END_PHASE` increments `turn_number`, flips `turn_player`, resets the new turn player's `normal_summon_used`, and sets `battle_phase_exists = True` for future turns.

- `handle_player_action(pa: PlayerAction) -> None`: the single entry point for mutating the board from player intent. Matches on `pa.action` (see `playeraction.md`):
  - `NORMAL_SUMMON` → validates `from_zone is HAND` / `to_zone is MONSTER`, resolves the concrete zone via `turn_player.get_open_zone`, calls `turn_player.normal_summon`
  - `ACTIVATE_ST_CARD` → validates `from_zone is HAND` / `to_zone is SPELL_TRAP`, resolves the zone, calls `turn_player.activate_st_card`
  - `SET_CARD` → validates only `from_zone is HAND`; the legal `to_zone` depends on the card's own type (monster vs. spell/trap vs. field spell), so that check is deliberately left to `Player.set_card` rather than duplicated here

  There's a standing `TODO` to check floodgate/lingering conditions before dispatching — not yet implemented, since there's no effect-resolution layer yet.

## How It Fits In
- Depends on `Player` (dispatch target), `PlayerAction`/`PlayerActions` (what it dispatches), `FieldZone`/`ZoneType` (for the shared EMZ), `TurnPhase`, and the `NotFromHandError`/`NotToMonsterZoneError`/`NotToSpellTrapZoneError` exceptions.
- Nothing in the current codebase constructs `BoardState` outside of tests yet — it's the object a future `GameEngine`/`Resolver` (Action/Resolution layer, not yet built) would produce new instances of from player-input `Action`s, and what `BoardEvaluator` (Evaluation layer, not yet built) would eventually read.

## Notes
- `BoardState` is documented as intended to be immutable ("only the `GameEngine` should produce new `BoardStates`..."), but nothing in the current implementation actually enforces that — `advance_phase` and `handle_player_action` both mutate `self`/`self.turn_player` in place. Worth keeping in mind if/when the Action/Resolution layer is built expecting copy-on-write semantics.
