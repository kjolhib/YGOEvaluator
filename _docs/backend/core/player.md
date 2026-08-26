# player.py

status: [done]
last updated: [26-08-2026]


**Path:** `backend/app/core/player.py`

## Attributes
### Player metadata:
- `name` (`str`): the name of the player
- `life_points` (`int`): the life points the player has remaining
- `normal_summon_used` (`bool`): whether or not this player has normal summoned (or set a monster) this turn.

### Zone info:
- `monster_zones` (`list[FieldZone]`): the monster zones the player has. It is a list containing 5 field zones, with the type defaulted to `MONSTER` and capacity to 1.
- `spell_trap_zones` (`list[FieldZone]`): similar to `monster_zones` but for spell/trap cards.
- `field_spell_zones` (`list[FieldZone]`): similar to `monster_zones`, but only with 1 zone, type `FIELD_SPELL`.

### Zones with No Cap:
All attributes with the type `PileZone`, which means that they have no capacity and theoretically any number of cards can enter them.

Note, in relation to the `extra_deck`, this specifically talks about the case where cards are **added to** the extra deck such as via pendulum monsters.
- `hand` (`PileZone`)
- `deck` (`PileZone`)
- `extra_deck` (`PileZone`)
- `graveyard` (`PileZone`)
- `banishment` (`PileZone`)

## Methods
- `all_monsters()` / `all_spells_traps()`: flatten `monster_zones`/`spell_trap_zones` into a single list of the `CardInstance`s currently occupying them.
- `get_open_zone(zone_type)`: given an abstract `ZoneType` (`MONSTER`, `SPELL_TRAP`, or `FIELD_SPELL`), returns the first non-full `FieldZone` of that kind on this player. This is the bridge between `PlayerAction`'s abstract `to_zone`/`from_zone` and the concrete `FieldZone` instance the action methods below actually mutate — see `boardstate.md`. Raises `ValueError` if the zone type isn't a field-zone kind, or none are open.
- `normal_summon(card_instance, zone)`: summons a card from the hand into a monster zone, face-up attack position. Requires `zone.zone_type is ZoneType.MONSTER` (else `NotToMonsterZoneError`) and `card.card_type` to be one of `MAIN_DECK_MONSTER_TYPES` (else `NotMainMonsterError`) — Fusion/Synchro/XYZ/Link monsters cannot be Normal Summoned. No-ops (with a print) if `normal_summon_used` is already `True`.
- `activate_st_card(card_instance, zone)`: activates a spell/trap card from the hand into a spell/trap zone, face-up. Requires `zone.zone_type is ZoneType.SPELL_TRAP` (else `NotToSpellTrapZoneError`) and `card.card_type` to be `SPELL` or `TRAP` (else `NotSpellTrapCardError`).
- `set_card(card_instance, zone)`: sets a card face-down from the hand. Branches on `card.card_type` via a `match`:
  - a `MAIN_DECK_MONSTER_TYPES` member → must target a `MONSTER` zone, sets face-down defense, and **consumes the normal summon** (same flag/no-op behaviour as `normal_summon`)
  - `SPELL`/`TRAP` → must target a `SPELL_TRAP` zone, sets face-down, does **not** touch the normal summon
  - `FIELD_SPELL` → must target a `FIELD_SPELL` zone (else `NotToFieldZoneError`), sets face-down
  - anything else (e.g. an extra-deck monster type) → `NotSettableCardError`, since those aren't legally settable from hand

## What it does
The `Player` class simulates actions a real player makes in a duel. `BoardState.handle_player_action` resolves a `PlayerAction`'s abstract zone via `get_open_zone`, then calls the matching method above.

Legality checking here is intentionally shallow (DuelingBook-style, per `docs/workflow.md`): these methods check zone-type/card-type consistency and normal-summon usage, not full game legality (priority, chain rules, cost payment, etc.) — that's out of scope for this layer.

## How It Fits In
- Depends on `app.core.Zones` (`FieldZone`, `PileZone`, `ZoneType`), `app.static.Card` (`CardInstance`, `CardType`), `app.type_defs.type_cards` (`Position`, `MAIN_DECK_MONSTER_TYPES`), and the `app.exceptions.actions.*` exception classes.
- Depended on by `BoardState` (see `boardstate.md`), which owns the two `Player` instances in a duel and routes `PlayerAction`s to them.
