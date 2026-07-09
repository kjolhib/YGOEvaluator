"""
YGUOEvaluator: Instance Layer skeleton.

Covers:
- Zone
- CardInstance
- Player
- BoardState

This file holds all classes required to hold information regarding a single board.
"""


from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

from core.Player import Player
from core.Zones import ZoneType, FieldZone, PileZone

class TurnPhase(Enum):
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

@dataclass
class BoardState:
  """
  Class that contains both player's fields and turn/phase metadata.

  The primary object that the evaluator will read.

  Immutable, only the `GameEngine` should produce new `BoardStates` from manual `Action`s the user inputs.
  """
  player: Player
  opponent: Player
  phase: TurnPhase = TurnPhase.S_DRAW_PHASE
  turn_player: Player = field(init=False) # initialise in post init
  turn_number: int = 1
  battle_phase_exists: bool = False

  # shared emz
  extra_monster_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.EXTRA_MONSTER, capacity=1) for _ in range(2)
  ])

  # Canonical phase order. 
  _PHASE_ORDER: tuple[TurnPhase, ...] = tuple(TurnPhase)

  def __post_init__(self):
    self.turn_player = self.player

  def advance_phase(self) -> TurnPhase:
    """
    Steps to the next `TurnPhase`, wrapping to the next turn's `S_DRAW_PHASE` and swapping `turn_player` when `END_PHASE` is passed.
    """
    order = self._PHASE_ORDER
    idx = order.index(self.phase)

    while True:
      idx += 1
      if idx >= len(order):
        # reached end phase
        idx = 0
        self.turn_number += 1
        self.turn_player = (
          self.opponent if self.turn_player is self.player else self.player
        )
        self.turn_player.normal_summon_used = False
        self.battle_phase_exists = True

      next_phase = order[idx]

      # if no battle phase, skip to end phase
      if not self.battle_phase_exists and next_phase in (
        TurnPhase.S_BATTLE_PHASE,
        TurnPhase.BATTLE_PHASE,
        TurnPhase.E_BATTLE_PHASE,
        TurnPhase.S_MAIN_PHASE_2,
        TurnPhase.MAIN_PHASE_2,
        TurnPhase.E_MAIN_PHASE_2
      ):
        continue


      # first turn of the duel has no battle phase
      if self.turn_number == 1 and next_phase is TurnPhase.S_BATTLE_PHASE:
        continue

      break
    
    self.phase = next_phase
    return self.phase
