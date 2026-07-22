from enum import Enum, auto

class PlayerActions(Enum):
  """
  Enum containing all actions a player can undertake.

  E.g. normal summon, activate card, set card
  """
  NORMAL_SUMMON = auto()
  ACTIVATE_ST_CARD = auto()
  SET_CARD = auto()