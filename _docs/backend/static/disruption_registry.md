# disruption_registry.py

status: [done]
last updated: [06-08-2026]


**Path:** `backend/app/static/disruption_registry.py`

## Context
`DisruptionSource` (`app/evaluator/DisruptionSource.py`) defines the *shape* of a registry entry; this file holds the actual hand-curated *data*. It lives under `app/static/` rather than `app/evaluator/` — grouping it with `Card.py` as static reference data, the same spirit/scale as `card_pool.txt`/`cards.json`: a starter list meant to be hand-extended over time, not exhaustive, and not derived from any card-text parsing (see `_docs/workflow.md`'s PSCT-is-intentionally-opaque principle).

## Purpose
Provide `DISRUPTION_REGISTRY`, the `dict[str, DisruptionSource]` that `BoardEvaluator.evaluate` cross-references against every `CardInstance` it scans.

## Main Components

- `DISRUPTION_REGISTRY: dict[str, DisruptionSource]` — keyed by card name (see `DisruptionSource.md`'s Notes for why name, not a synthetic ID). Current starter entries: Ash Blossom & Joyous Spring, Baronne de Fleur, Infernity Barrier, Dark Paladin, Mirror Force, Mitsurugi Great Purification, Solemn Judgment.
- Each entry's `disruption_by_zone` is deliberately precise about which `(zone, position)` states the card is actually live in -- not just which zones. Worth reading directly rather than summarizing here, since the specifics are the point (e.g. Baronne de Fleur, a Link Monster, is only live at `(MONSTER, FACE_UP_ATK)` -- no `FACE_UP_DEF` key, since Link Monsters have no Defense Position; Solemn Judgment has no `HAND` key at all, since Trap Cards can't be activated straight from hand).

## How It Fits In
Depends on `DisruptionSource` (`app.evaluator.DisruptionSource`) and the `DisruptionType`/`OncePerTurnScope`/`DisruptionCategory`/`ZoneType`/`Position` enums. Imported by `app.evaluator.BoardEvaluator` as the default `registry` argument to `evaluate`, and by tests that want to exercise the real starter data (as opposed to a custom registry built inline for a specific scenario).

## Notes
Pure data, no logic -- this file should stay a plain dict literal that's easy to hand-extend, not grow imports or conditionals. Category/type/scope/state assignments are illustrative and meant to be refined by hand as a format's actual known disruptions get filled in; they're not meant to be treated as authoritative rulings.
