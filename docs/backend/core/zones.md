# Zones.py

status: [done]
last updated: [29-07-2026]


**Path:** `backend/app/core/Zones.py`

## Context
Zones are the containers that hold `CardInstance` objects within a `Player` or `BoardState`. `Player` creates its five main-monster zones, five Spell/Trap zones, field-spell zone, and unlimited pile zones from these classes; `BoardState` separately creates the two shared extra-monster zones.

The module models capacity and containment only. It does not enforce broad duel legality, choose a target slot, or keep a card's own `current_zone_type` synchronized when a card is moved.

## Purpose
Provide reusable, typed containers for one-card field slots and unlimited pile-style zones.

## Main Components

- `Zone` — base dataclass holding a `ZoneType`, optional capacity, and ordered `CardInstance` list.
- `Zone.is_full()` — reports whether a finite-capacity zone has reached its limit.
- `Zone.add(card_instance)` — adds a card or raises `ValueError` if the zone is full.
- `Zone.remove(card_instance)` — removes an existing card or raises `ValueError` if it is absent.
- `Zone.__len__()` — returns the number of contained cards.
- `FieldZone` — a one-card `Zone` restricted to field-zone types such as Monster, Spell/Trap, Extra Monster, and Field Spell.
- `PileZone` — an unlimited `Zone` restricted to non-field types such as Hand, Deck, Graveyard, Banished, and Extra Deck.
- `PileZone.shuffle()` — randomizes the order of cards in a pile.

## How It Fits In
Depends on `CardInstance`, `ZoneType`, and `FIELD_ZONE_TYPES`. `Player`, `BoardState`, and the player action methods create and mutate these containers; the zone category constants live in `app.type_defs.type_zones`.

## Notes
Zone mutation updates the container only. The action methods currently update card position but do not remove cards from their originating `PileZone` or update `CardInstance.current_zone_type`; a future move/resolution layer will need to own that consistency.
