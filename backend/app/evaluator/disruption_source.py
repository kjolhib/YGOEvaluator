from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_cards import Position
from app.static.type_defs.card import CardInstance

@dataclass(frozen=True)
class DisruptionEffect:
  """
  A single disruption effect. Note that this single effect may encompass multiple types of "disruption", e.g. destruction, negation as with the case of varudras.
  """
  label: str # english desctipion for the category
  categories: list[DisruptionCategory] # 1 or more disruptions this single effect has, e.g. Varudras: omni + destruction
  opt_scope: OncePerTurnScope
  disruption_by_zone: dict[tuple[ZoneType, Position], DisruptionType]

  def __post_init__(self) -> None:
    if not self.categories:
      raise ValueError(f"DisruptionEffect {self.label} must have at least one category.")
    if not self.disruption_by_zone:
      raise ValueError(f"DisruptionEffect {self.label} must have at least one zone where its disruption is valid.")

@dataclass(frozen=True)
class DisruptionSource:
  """
  A single hand-curated registry entry: "this card, in this (zone, position), represents this kind of disruption."

  This is Evaluation-layer configuration, not derived from card text.
  
  Entries are hand-authored in `disruption_registry.py`. The same spirit/scale as `card_pool.txt`: a starter list meant to be hand-extended over time, not exhaustive.

  Card `effects`, their `categories` and `disruption zones`, must all exist and non-empty.
  """
  card_name: str
  effects: list[DisruptionEffect]

  def __post_init__(self) -> None:
    if not self.card_name.strip():
      raise ValueError("DisruptionSource must have a non-blank card_name.")
    if not self.effects:
      raise ValueError(f"DisruptionSource {self.card_name} must have at least one effect for it to be classified as a disruption.")
    # TODO: check for duplicate effects

def lookup_disruption(
  card_instance: CardInstance,
  registry: list[DisruptionSource],
) -> list[DisruptionEffect]:
  """
  Static lookup: is this specific `CardInstance` currently a live, registered disruption?

  Doesn't care about specifics regarding the disruption, only whether or not it's active and registered.

  Args:
    card_instance (CardInstance): the card instance to check
    registry (dict[str, DisruptionSource]): the disruption registry to
      check against, e.g. `DISRUPTION_REGISTRY`

  Returns:
    list[DisruptionEffect]: the matching registry entry if`card_instance.card.name` is a registered disruption AND `(card_instance.current_zone_type, card_instance.current_position)` is a key in that entry's `disruption_by_zone`.
    `[]`: otherwise. (unregistered card, or registered but not currently in a (zone, position) state where it's live - e.g. Ash Blossom already discarded to GY or Solemn Judgment still in hand).
  """
  source = next((src for src in registry if src.card_name == card_instance.card.name), None)
  if source is None:
    return []

  current_position = (card_instance.current_zone_type, card_instance.current_position)

  # every effect of this card that is live in its current zone and position.
  # An effect that isn't live here is skipped, not a reason to discard the rest:
  # e.g. a set Mitsurugi Great Purification has its negate live, its GY effect not.
  return [effect for effect in source.effects if current_position in effect.disruption_by_zone]
