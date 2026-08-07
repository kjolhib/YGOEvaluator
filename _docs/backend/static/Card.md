# Card.py

status: [done]
last updated: [06-08-2026]


**Path:** `backend/app/static/Card.py`

## Context
`Card` is the Static/Reference layer's core object -- format-independent card data, loaded once from `cards.json` (see `app.fetching`, `_docs/fetcher/fetcher.md`) and never changed at runtime. `CardInstance` is the Instance-layer wrapper around a `Card`: the same `Card` object is shared by reference across every physical copy of that card on the board, while `CardInstance` carries the per-copy runtime state (zone, position, counters).

Both classes live in this one file even though they belong to different architectural layers (Static vs. Instance) -- `CardInstance` was already here before the static layer existed as its own concept, and splitting it out hasn't been necessary yet.

## Purpose
Define the static card data model and how it's loaded from `cards.json`, plus the runtime per-copy wrapper every other layer (`Player`, `Zones`, `BoardEvaluator`) actually operates on.

## Main Components

- `Card` -- frozen dataclass: `id`, `name`, `card_type` (`CardType`) are required; `race`/`desc` default to `""` (ergonomic hand-construction in tests); everything else (`archetype`, `atk`, `defense`, `level`, `attribute`, `scale`, `linkval`, `linkmarkers`) defaults to `None` and stays `None` precisely when the raw API omitted it for this card's type.
  - `defense`, not `def` -- the raw JSON key is `"def"`, a reserved word in Python. Translated in `from_raw`.
  - `is_pendulum` (property) -- `scale is not None`. Deliberately not a `CardType` member; see `CardType`'s docstring (`app/type_defs/type_cards.py`) for why pendulum-ness is an orthogonal axis to summon mechanic.
  - `is_extra_deck` (property) -- `card_type in EXTRA_DECK_MONSTER_TYPES`.
  - `from_raw(raw_card: dict) -> Card` (classmethod) -- builds a `Card` from one trimmed `cards.json` entry, including running `map_card_type` on the raw `type`/`race` strings.
- `load_cards(cards_json_path=None) -> list[Card]` -- reads a trimmed `cards.json` file and returns one `Card` per entry, in file order. Defaults to `backend/data/cards.json` if no path is given.
- `index_cards_by_name(cards: list[Card]) -> dict[str, Card]` -- indexes a list of `Card`s by name, for lookups like "give me the `Card` for 'Ash Blossom & Joyous Spring'" when building a `CardInstance`.
- `CardInstance` -- (not frozen) dataclass: `card` (`Card`), `current_position` (`Position`), `current_zone_type` (`ZoneType`), `counters` (`dict[str, int]`), `materials` (`list[CardInstance]`, for XYZ/Fusion/Synchro/Link material tracking), `is_negated` (`bool`).

## How It Fits In
`Card` depends on `CardType`/`map_card_type`/`EXTRA_DECK_MONSTER_TYPES` (`app.type_defs.type_cards`); `CardInstance` additionally depends on `Position` (same module) and `ZoneType` (`app.type_defs.type_zones`). `Card.from_raw`/`load_cards` are the consumers of `app.fetching`'s trimmed output -- this is the bridge between fetched JSON and usable Python objects. `CardInstance` is what `Player`'s zones actually hold, what `BoardEvaluator` scans (via `card_instance.card.name`, `.current_zone_type`, `.current_position`), and what every disruption registry entry (`DisruptionSource.disruption_by_zone`) is checked against -- see `_docs/backend/evaluator/DisruptionSource.md`.

## Notes
`current_zone_type` on `CardInstance` is the sole source of truth the rest of the codebase reads for "where is this card" -- it is set independently of which physical `Zone`/`FieldZone`/`PileZone` container an instance is actually placed into (see `Zones.py`'s Notes). Nothing currently keeps the two in sync automatically; a future move/resolution layer will need to own that consistency, same gap already noted in `zones.md` and `player_action.md`.
