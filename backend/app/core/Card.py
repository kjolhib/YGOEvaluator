from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Position(Enum):
  FACE_UP_ATK = auto()
  FACE_UP_DEF = auto()
  FACE_DOWN_MONSTER = auto()
  FACE_DOWN_ST = auto()
  FACE_DOWN_BNSHED = auto()

@dataclass(frozen=True)
class Card:
  name: str
  card_id: Optional[int] = None

@dataclass
class CardInstance:
  """
  A card and it's runtime state.
  
  Zone/position are tracked here.
  """
  card: Card
  position: Position
  counters: dict[str, int] = field(default_factory=dict)
  materials: list["CardInstance"] = field(default_factory=list)
  is_negated: bool = False

  def __repr__(self) -> str:
    return f"<{self.card.name} [{self.position.name}]"
