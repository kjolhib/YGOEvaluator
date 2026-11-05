# disruption_registry (registry package)

[data-status]: [in-progress]
[implementation-status]: [done]
[last updated]: [20-10-2026]


**Path:** `backend/app/static/registry/`

## Context
Disruptions are complicated in yugioh, even ignoring layered disruptions. Even flat omni negates or may have many conditions attached to them.

The evaluator works by a heuristic, and doesn't aim to try to do anything "smart", and so it needs as much information as possible. This information
would have hand-curated by players. All the evaluator needs to do, is provide a good way of condensing this information in a digestible manner to the user.
## Purpose
This is where the disruptions are held. It is a hand-curated package that will be updated whenever cards relevant to the meta are discovered/added.

The information here will be read by the [evaluator](board_evaluator.md) only to produce an output that describes what the board represents.

The registry is a single **global** list of `DisruptionSource`s, covering every card that has been hand-curated, regardless of format. It is split across several modules by what the card *is* (hand traps, an archetype), not by which format uses it, so a card never has to move when it shows up in a new meta. A format's own registry is intended to be derived by filtering this global one against that format's `card_pool.txt` (not built yet).

Each entry is a `DisruptionSource` (see [disruption_source](disruption_source.md)), and describes the card **per effect**:
- `card_name`: name of the card that this disruption is relevant to. This is also the lookup key.
- `effects`: a list of `DisruptionEffect`s, one per effect of the card that is worth curating. Each effect includes:
  - `label`: short English description of the effect, unique within its card.
  - `categories`: usually community-crafted categories, such as "hand trap". One effect may have several, meaning "any disruption this effect has".
  - `opt_scope`: type of once per turn **this effect** is, either `SOFT` or `HARD`. A card with a hard-OPT effect and a soft-OPT effect is simply a card with two effects.
  - `disruption_by_zone`: the `(zone, position)` states this effect is live in, each mapped to a `DisruptionType` (`ACTIVE_DISRUPTION` or `POTENTIAL_DISRUPTION`). Here to tell the evaluator whether or not this effect is considered active in the card's current state.

## Main Components
- `registry/__init__.py`: finds every non-underscore module in the folder, concatenates their `ENTRIES` lists, and exposes the result as `GLOBAL_REGISTRY` (`list[DisruptionSource]`) and `GLOBAL_REGISTRY_BY_NAME` (`dict[str, DisruptionSource]`). Adding a new group of cards is just dropping in a new module; nothing in `__init__.py` needs editing. It is strict on purpose:
  - a module without an `ENTRIES` list raises `AttributeError`, so a typo can't silently drop that module's cards.
  - two entries with the same `card_name` raise `ValueError`, since lookups match on name and a duplicate would make one entry unreachable.
  - modules whose names start with `_` are skipped, so helpers can live in the folder.
- `registry/<classification>.py`: each module defines `ENTRIES: list[DisruptionSource]`, classified by archetype or some community theme. Currently: `hand_traps`, `traps`, `generic_ed_monsters`, `infernity`, `mitsurugi`, `dark_magician`, plus empty stubs `ryzeal` and `maliss`.

## Notes
- Lookups are **keyed by name**, not ID. This is primarily because Yugioh card names cannot be the same by the design of the game, and so it's just easier to key it by name. This may be subject to change.
- The registry is tested in `tests/static/test_registry.py` (entry shape, package wiring, discovery, and a snapshot of the curated data) and `tests/evaluator/test_disruption_source.py` (the lookup).

## Limitations
- Currently, there is nothing to denote "you can only activate 1 of the following effects per turn", or of that miscellaneous type. I do not intend to add this in coding (which effect the player picks changes the meaning of the others, so it would amount to building an engine), but do intend to add this in descriptions of cards. 
