# player_action.py

status: [done]
last updated: [29-07-2026]


**Path:** `backend/app/core/player_action.py`

## Context
The core board model separates a player's requested move from the mutation that applies it. `PlayerAction` describes the requested operation using abstract `ZoneType` values; `BoardState.handle_player_action` resolves a matching concrete `FieldZone` on the active player and delegates the state change to `Player`.

The model therefore represents a small, supported subset of manual duel actions rather than a full rule-resolution engine. Current action kinds are Normal Summon, Spell/Trap activation from hand, and setting a card.

## Purpose
Carry all information needed for `BoardState` to validate and dispatch one supported player action.

## Main Components

- `PlayerAction` — dataclass containing the action kind, declaring player, abstract source and destination zone types, and target `CardInstance`.
- `action` (`PlayerActions`) — selects the dispatch branch in `BoardState.handle_player_action`.
- `player` (`Player`) — records the player who declared the action.
- `to_zone` / `from_zone` (`ZoneType`) — express intended zone categories rather than a specific slot.
- `card` (`CardInstance`) — the runtime card object to place or activate.

## How It Fits In
Depends on `Player`, `CardInstance`, `PlayerActions`, and `ZoneType`. It is constructed by callers that model user intent and consumed by `BoardState`; `Player.get_open_zone` converts its abstract destination into a concrete slot.

## Notes
`BoardState.handle_player_action` currently performs the mutation against `BoardState.turn_player` rather than checking or using `pa.player`. Callers should supply the current turn player, and a future legality layer may need to reject mismatched actions explicitly.
