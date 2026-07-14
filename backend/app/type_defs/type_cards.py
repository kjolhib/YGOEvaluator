from enum import Enum, auto

class Position(Enum):
  FACE_UP_ATK = auto()
  FACE_UP_DEF = auto()
  FACE_DOWN_MONSTER = auto()
  FACE_DOWN_ST = auto()
  FACE_UP_ST = auto()
  FACE_DOWN_BNSHED = auto()

class CardType(Enum):
  SPELL = auto()
  TRAP = auto()
  MONSTER = auto()
  FIELD_SPELL = auto()
  EXTRA_DECK_MONSTER = auto()
  PENDULUM_MONSTER = auto()