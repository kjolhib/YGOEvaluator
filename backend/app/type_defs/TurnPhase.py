from enum import Enum, auto


class TurnPhase(Enum):
  """
  Enum containing all the phases of each turn.

  E.g. Draw phase, Standby, etc.
  """
  S_DRAW_PHASE = auto()
  DRAW_PHASE = auto()
  E_DRAW_PHASE = auto()
  S_STANDBY_PHASE = auto()
  STANDBY_PHASE = auto()
  E_STANDBY_PHASE = auto()
  S_MAIN_PHASE_1 = auto()
  MAIN_PHASE_1 = auto()
  E_MAIN_PHASE_1 = auto()
  S_BATTLE_PHASE = auto()
  BATTLE_PHASE = auto()
  E_BATTLE_PHASE = auto()
  S_MAIN_PHASE_2 = auto()
  MAIN_PHASE_2 = auto()
  E_MAIN_PHASE_2 = auto()
  S_END_PHASE = auto()
  END_PHASE = auto()