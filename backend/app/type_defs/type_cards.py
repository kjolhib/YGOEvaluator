from enum import Enum, auto

class Position(Enum):
  """
  Enum containing the position of a card.

  E.g. face up attack, def, face down monster/spell trap.
  """
  FACE_UP_ATK = auto()
  FACE_UP_DEF = auto()
  FACE_DOWN_MONSTER = auto()
  FACE_DOWN_ST = auto()
  FACE_UP_ST = auto()
  FACE_DOWN_BNSHED = auto()

class CardType(Enum):
  """
  Enum containing the card typing.

  E.g. spell, trap, monster, field spell, emz, pendulum monster.

  To be decided whether or not `PENDULUM_MONSTER` requires further breakdown.
  """
  SPELL = auto()
  TRAP = auto()
  MONSTER = auto()
  FIELD_SPELL = auto()
  EXTRA_DECK_MONSTER = auto()
  PENDULUM_MONSTER = auto()