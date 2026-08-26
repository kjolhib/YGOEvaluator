# disruption_source.py

status: [done]
last updated: [26-08-2026]


**Path:** `backend/app/evaluator/disruption_source.py`

## Context
`BoardEvaluator` needs to know, for any given `CardInstance` sitting somewhere on a `BoardState`, whether it currently represents a disruption. That knowledge is hand-curated per format (see `_docs/workflow.md`'s "Core Design Principle: Format Scoping" and "Data Storage" sections) rather than derived from card text — this project deliberately does not attempt to parse PSCT.

`DisruptionSource` is the shape of one hand-authored registry entry; `lookup_disruption` is the pure per-instance check `BoardEvaluator` calls while scanning a board. The actual registry data lives in `app/static/disruption_registry.py`, not in this file — this file only defines the shape and the lookup, not the data.

## Purpose
Define what a single "this card is a disruption" registry entry looks like, and provide a stateless way to check one `CardInstance` against a registry.

## Main Components

- `DisruptionSource` — frozen dataclass: `card_name` (the lookup key — see Notes), `category` (`DisruptionCategory`), `opt_scope` (`OncePerTurnScope`), and `disruption_by_zone`.
- `disruption_by_zone: dict[tuple[ZoneType, Position], DisruptionType]` — maps each `(zone, position)` state this card is live in to what kind of disruption it represents *there*. Both axes matter independently:
  - **Zone absence** — a card can be a real disruption in general but not from where it currently sits at all (e.g. a Trap Card in `HAND` — Trap Cards must be Set before they can be activated, so `HAND` isn't a key for any Trap entry, not even as `POTENTIAL_DISRUPTION`).
  - **Position absence within a zone that's otherwise valid** — e.g. a monster's static/continuous effect requires it to be face-up; the same `MONSTER` zone with `FACE_DOWN_MONSTER` instead of `FACE_UP_ATK`/`FACE_UP_DEF` is not a key, so a face-down copy of an otherwise-registered monster produces nothing.
  - The same card name can resolve to *different* `DisruptionType`s depending on state (e.g. a combo piece that's `POTENTIAL_DISRUPTION` in hand but `ACTIVE_DISRUPTION` once resolved onto the field) — this is why `BoardEvaluator` groups findings by `(card_name, disruption_type)`, not just `card_name` (see `BoardEvaluator.md`).
- `lookup_disruption(card_instance, registry) -> Optional[DisruptionSource]` — looks up `card_instance.card.name` in `registry`, then checks whether `(card_instance.current_zone_type, card_instance.current_position)` is a key in that entry's `disruption_by_zone`. Returns the whole `DisruptionSource` if both checks pass, `None` otherwise. Purely a per-instance check — no grouping, no OPT collapsing, no board-wide reasoning; that's `BoardEvaluator`'s job.

## How It Fits In
Depends on `CardInstance` (`app.static.Card`), and the `DisruptionType`/`OncePerTurnScope`/`DisruptionCategory` enums (`app.type_defs.type_disruption`). Consumed by `app.evaluator.BoardEvaluator.evaluate`, which calls `lookup_disruption` once per candidate `CardInstance` while scanning a board. The actual `dict[str, DisruptionSource]` registry data is `DISRUPTION_REGISTRY` in `app/static/disruption_registry.py` (see `_docs/backend/static/disruption_registry.md`).

## Notes
`card_name`, not a synthetic ID, is the registry's lookup key: unlike most TCGs, a Yu-Gi-Oh card name maps to exactly one set of mechanics/text (reprints are identical; divergences are handled via errata/bans, not new names), so it's a genuinely stable identifier here — and it's the same key `Card`/`CardInstance` already use elsewhere (`index_cards_by_name`). If this registry ever moves to a database, `Card.id` (the YGOPRODeck numeric ID) is the natural key to adopt then — see `_docs/workflow.md`'s "Data Storage" section. No `card_id` field exists on `DisruptionSource` today.
