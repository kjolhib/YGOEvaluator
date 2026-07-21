from dataclasses import dataclass, field
from typing import Optional

from app.core.Card import CardInstance
from app.type_defs.type_zones import ZoneType, FIELD_ZONE_TYPES

@dataclass
class Zone:
  """
  A zone that a card can be in.

  Capacity is the maximum number of cards that can exist in this zone. All non-field zones are unlimited.
  """
  zone_type: ZoneType
  capacity: Optional[int] = None
  cards: list[CardInstance] = field(default_factory=list)

  def is_full(self) -> bool:
    """
    Whether or not the zone is full. 

    Zones are always 1 for field zones, but infinite for others.
    """
    return self.capacity is not None and len(self.cards) >= self.capacity

  def add(self, card_instance: CardInstance) -> None:
    """
    Add a card to the zone.
    """
    if self.is_full():
      raise ValueError(f"{self.zone_type.name} zone is full.")
    self.cards.append(card_instance)

  def remove(self, card_instance: CardInstance) -> None:
    """
    Remove card from zone.
    """
    if card_instance not in self.cards:
      raise ValueError(f"{card_instance.card.name} is not in this zone.")
    self.cards.remove(card_instance)

  def __len__(self) -> int:
    return len(self.cards)

@dataclass
class FieldZone(Zone):
  """
  Single card zone physically part of the field:
  - Monster
  - Spell/Trap
  - Extra monster
  - Field zone
  """
  capacity: Optional[int] = 1

  def __post_init__(self) -> None:
    if self.zone_type not in FIELD_ZONE_TYPES:
      raise ValueError(
        f"FieldZone cannot be constructed with zone_type={self.zone_type.name}; must be one of {[t.name for t in FIELD_ZONE_TYPES]}"
      )
  
@dataclass
class PileZone(Zone):
  """
  Non-field zone:
  - hand
  - deck
  - extra deck
  - graveyard
  - banishment

  Currently, capacity can be unlimited because there is no real legality engine. All the evaluator needs is the board itself, and whatever is in the deck or extra deck isn't relevant.

  Hand, GY and banishment can theoretically be infinite anyway, so it doesn't matter for that.
  """
  capacity: Optional[int] = None

  def __post_init__(self) -> None:
    if self.zone_type in FIELD_ZONE_TYPES:
      raise ValueError(
        f"PileZone cannot be constructed with zone_type={self.zone_type.name}."
      )

  def shuffle(self) -> None:
    """
    Shuffles the pile zone.
    """
    import random
    random.shuffle(self.cards)

# TODO: add spell/trap, and monster zone as children Zones?

