# disruption_source.py

[status]: [done]
[last updated]: [05-11-2026]


**Path:** `backend/app/evaluator/disruption_source.py`

## Context
`BoardEvaluator` needs to know, for any given `CardInstance` sitting somewhere on a `BoardState`, whether it currently represents a disruption. That knowledge is hand-curated per format (see `_docs/workflow.md`'s "Core Design Principle: Format Scoping" and "Data Storage" sections) rather than derived from card text — this project deliberately does not attempt to parse PSCT.

Each card may have multiple effects, so we need a source that represents the card's disruption wrapper, and in it, each effect's individual disruption and metadata (opt scope, category, disruption zone etc).

## Purpose
Define what a single "this card is a disruption" registry entry looks like, and provide a stateless way to check one `CardInstance` against a registry.

## Main Components
- `DisruptionEffect`, frozen dataclass, is the effect of a disruption. It contains:
  - `label`: an english description of the effect
  - `categories`: the category of disruption it represents. It may be more than 1. Cannot be empty.
  - `opt_scope`: the once-per-turn scope of this effect. Either `SOFT` or `HARD`.
  - `disruption_by_zone`: the zone and position that this effect is live in, and what kind of disruption it is (active vs potential, for example). Cannot be empty.
- `DisruptionSource`, frozen dataclass:
  - `card_name`: identifier of the disruption.
  - `effects`: contains a list of `DisruptionEffect`s that this card has. Cannot be empty.
- `lookup_disruption(card_instance, registry) -> List[DisruptionEffect]` — looks up `card_instance.card.name` in `registry`, then checks whether `(card_instance.current_zone_type, card_instance.current_position)` is a key in that entry's `disruption_by_zone`. Returns a list of all disruption effects found for the card in its current zone and position. It returns empty if it there aren't anything found.

## How It Fits In
Depends on `CardInstance` (`app.static.Card`), and the `DisruptionType`/`OncePerTurnScope`/`DisruptionCategory` enums (`app.type_defs.type_disruption`). Consumed by `app.evaluator.BoardEvaluator.evaluate`, which calls `lookup_disruption` once per candidate `CardInstance` while scanning a board. The actual `dict[str, DisruptionSource]` registry data is `DISRUPTION_REGISTRY` in `app/static/disruption_registry.py` (see `_docs/backend/static/disruption_registry.md`).

## Notes
`card_name` is the identifier used, it's the registry's lookup key. In yugioh, card names are nearly always stable once printed. If this registry ever moves to a database, `Card.id` (the YGOPRODeck numeric ID) is the natural key to adopt then — see `_docs/workflow.md`'s "Data Storage" section. No `card_id` field exists on `DisruptionSource`, and isn't planned.
