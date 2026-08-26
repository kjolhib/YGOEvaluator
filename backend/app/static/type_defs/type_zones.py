from enum import Enum, auto

class ZoneType(Enum):
  """
  Enum containing the typing of a zone on a field.

  E.g. monster, spell/trap, extra monster, hand, field, GY, ..., zones
  """
  MONSTER = auto()
  SPELL_TRAP = auto()
  EXTRA_MONSTER_ZONE = auto()
  HAND = auto()
  FIELD_SPELL = auto()
  GRAVEYARD = auto()
  BANISHED = auto()
  DECK = auto()
  EXTRA_DECK = auto()

# Zone types that are physically part of the field: single-card slots
FIELD_ZONE_TYPES: frozenset[ZoneType] = frozenset({
  ZoneType.MONSTER,
  ZoneType.SPELL_TRAP,
  ZoneType.EXTRA_MONSTER_ZONE,
  ZoneType.FIELD_SPELL
})
