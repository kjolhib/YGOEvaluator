from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.type_defs.type_zones import ZoneType
from app.type_defs.type_cards import Position
from app.static.Card import CardInstance

@dataclass(frozen=True)
class DisruptionSource:
  """
  A single hand-curated registry entry: "this card, in this (zone, position), represents this kind of disruption."

  This is Evaluation-layer configuration, not derived from card text.
  See `_docs/workflow.md`.
  
  Entries are hand-authored in `disruption_registry.py`. The same spirit/scale as `card_pool.txt`: a starter list meant to be hand-extended over time, not exhaustive.
  """
  card_name: str
  category: DisruptionCategory
  opt_scope: OncePerTurnScope

  disruption_by_zone: dict[tuple[ZoneType, Position], DisruptionType]
  """
  Maps each (zone, position) combination this card is live in to what kind
  of disruption it represents *there*. Position matters just as much as
  zone -- e.g. a set trap is live face-down (`FACE_DOWN_ST`), not face-up;
  Baronne de Fleur (a Link Monster, always face-up) is only live as
  `FACE_UP_ATK`, never a face-down state.

  A (zone, position) combination simply absent from this dict means the
  card serves no purpose in that state. E.g. Solemn Judgement maps only
  `{(SPELL_TRAP, FACE_DOWN_ST): ACTIVE_DISRUPTION}`; it's not a disruption
  of any kind while in hand, regardless of position.

  A card can also resolve to different `DisruptionType`s per (zone,
  position). E.g. a combo piece that's `POTENTIAL_DISRUPTION` in hand
  (needs more plays to go live) but `ACTIVE_DISRUPTION` once it resolves
  onto the field.
  """

def lookup_disruption(
  card_instance: CardInstance,
  registry: dict[str, DisruptionSource],
) -> Optional[DisruptionSource]:
  """
  Static lookup: is this specific `CardInstance` currently a live, registered disruption?

  Purely a registry + zone-liveness check.
  
  No board-wide reasoning, no grouping, no OPT collapsing. That's `BoardEvaluator`'s job (it calls this once per candidate `CardInstance` while scanning a board).

  Args:
    card_instance (CardInstance): the card instance to check
    registry (dict[str, DisruptionSource]): the disruption registry to
      check against, e.g. `DISRUPTION_REGISTRY`

  Returns:
    Optional[DisruptionSource]: the matching registry entry if
    `card_instance.card.name` is a registered disruption AND
    `(card_instance.current_zone_type, card_instance.current_position)` is
    a key in that entry's `disruption_by_zone`; `None` otherwise
    (unregistered card, or registered but not currently in a (zone,
    position) state where it's live -- e.g. Ash Blossom already discarded
    to GY, Solemn Judgement still in hand, or a set trap that's since
    flipped face-up).
  """
  source = registry.get(card_instance.card.name)
  if source is None:
    return None

  key = (card_instance.current_zone_type, card_instance.current_position)
  if key not in source.disruption_by_zone:
    return None

  return source
