from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.static.type_defs.type_cards import Position, CardType, EXTRA_DECK_MONSTER_TYPES, map_card_type
from app.static.type_defs.type_zones import ZoneType
from app.exceptions.loading.no_cards_json_error import NoCardsJsonError

@dataclass(frozen=True)
class Card:
  """
  Static, format-independent reference data for a single card.

  This is the Static/Reference layer's core object: everything here comes
  straight from `cards.json` (see `app.fetching`, `docs/fetcher/fetcher.md`)
  and never changes at runtime -- hence `frozen=True`. Per-game state (zone,
  position, counters) lives on `CardInstance`, not here -- many
  `CardInstance`s can point at the same `Card`.

  `race`/`desc` default to `""` for ergonomic hand-construction in tests
  that don't care about them; everything else defaults to `None` and is
  `None` precisely when the raw API omitted it for this card's type (e.g.
  `scale` only exists on Pendulum monsters, `linkval`/`linkmarkers` only on
  Link Monsters) -- see `app.fetching.trim` for what YGOPRODeck sends per
  card type.
  """
  id: int
  name: str
  card_type: CardType
  race: str = ""
  desc: str = ""
  archetype: Optional[str] = None
  atk: Optional[int] = None
  defense: Optional[int] = None  # raw JSON key is "def", a reserved word in Python
  level: Optional[int] = None
  attribute: Optional[str] = None
  scale: Optional[int] = None
  linkval: Optional[int] = None
  linkmarkers: Optional[tuple[str, ...]] = None

  @property
  def is_pendulum(self) -> bool:
    """
    Whether this card is a Pendulum monster.

    Orthogonal to `card_type` (a card can be e.g. `EFFECT_MONSTER` and
    pendulum at the same time) -- see `CardType`'s docstring for why this
    is a derived flag rather than a `CardType` member.
    """
    return self.scale is not None

  @property
  def is_extra_deck(self) -> bool:
    """Whether this card belongs in the Extra Deck (Fusion/Synchro/XYZ/Link)."""
    return self.card_type in EXTRA_DECK_MONSTER_TYPES

  @classmethod
  def from_raw(cls, raw_card: dict[str, Any]) -> "Card":
    """
    Builds a `Card` from one trimmed card dict, as produced by
    `app.fetching.trim` and written to `cards.json`.

    Args:
      raw_card (dict): a single trimmed card entry

    Returns:
      Card: the constructed static reference card
    """
    linkmarkers = raw_card.get("linkmarkers")

    return cls(
      id=raw_card["id"],
      name=raw_card["name"],
      card_type=map_card_type(raw_card["type"], raw_card["race"]),
      race=raw_card["race"],
      desc=raw_card["desc"],
      archetype=raw_card.get("archetype"),
      atk=raw_card.get("atk"),
      defense=raw_card.get("def"),
      level=raw_card.get("level"),
      attribute=raw_card.get("attribute"),
      scale=raw_card.get("scale"),
      linkval=raw_card.get("linkval"),
      linkmarkers=tuple(linkmarkers) if linkmarkers is not None else None,
    )

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
