from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from app.type_defs.type_cards import Position, CardType
from app.type_defs.type_zones import ZoneType

@dataclass(frozen=True)
class Card:
  name: str
  card_type: CardType
  card_id: Optional[int] = None

# TODO: implement spell/trap and monster classes that use card interface

@dataclass
class CardInstance:
  """
  A card and it's runtime state.
  
  Zone/position are tracked here.
  """
  card: Card
  current_position: Position
  current_zone_type: ZoneType
  counters: dict[str, int] = field(default_factory=dict)
  materials: list["CardInstance"] = field(default_factory=list)
  is_negated: bool = False

  def __repr__(self) -> str:
    return f"<{self.card.name} [{self.current_position.name}]"

