# trim.py

status: [done]
last updated: [29-07-2026]


**Path:** `backend/app/fetching/trim.py`

## Context
YGOPRODeck responses include artwork, pricing, set, banlist, and other presentation data that the evaluator does not use. The fetching pipeline invokes this module between HTTP retrieval and JSON persistence, leaving a compact intermediary schema for the static card layer.

This stage retains the raw API `type` and `race` values rather than converting them into internal enums. `app.static.Card.Card.from_raw` performs that interpretation later through `map_card_type`.

## Purpose
Produce evaluator-relevant copies of raw card dictionaries without mutating the API responses or assigning gameplay meaning to their fields.

## Main Components

- `_ALWAYS_KEEP` — fields retained whenever present: identity, raw type/race, archetype, and description.
- `_KEEP_IF_PRESENT` — monster- or mechanic-specific attributes retained only when supplied by the API.
- `trim_card(raw_card)` — creates a filtered dictionary for one raw card.
- `trim_cards(raw_cards)` — applies `trim_card` to each response entry in order.

## How It Fits In
Depends only on `typing.Any`. `app.fetching.pipeline.build_card_pool` uses it before JSON output, and `app.static.Card` later expects its field names, including the API's `def` key and `linkmarkers` list.

## Notes
Field Spells remain raw `type == "Spell Card"`; their distinction is carried by `race == "Field"`. The static mapper must use both fields, which it currently does.
