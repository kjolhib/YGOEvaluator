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

from app.core.Player import Player
from app.core.PlayerAction import PlayerAction, PlayerActions
from app.core.Zones import FieldZone
from app.type_defs.TurnPhase import TurnPhase

from app.type_defs.type_zones import ZoneType
from app.exceptions.actions.NotFromHandError import NotFromHandError
from app.exceptions.actions.NotToMonsterZoneError import NotToMonsterZoneError
from app.exceptions.actions.NotToSTZoneError import NotToSpellTrapZoneError

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
    FieldZone(ZoneType.EXTRA_MONSTER_ZONE, capacity=1) for _ in range(2)
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

  def handle_player_action(self, pa: PlayerAction) -> None:
    """
    Determines what type of action the player attempted to execute.

    Args:
      pa (PlayerAction): the player action class that contains information about the action the player wants to execute

    Returns:
      None
    """
    # TODO: Check floodgate/lingering conditions imposed upon the player before attempting to do this. This can be implemented here or in the player class, a future me problem to identify
    match pa.action:
      case PlayerActions.NORMAL_SUMMON:
        if pa.from_zone is not ZoneType.HAND:
          raise NotFromHandError("You can only normal summon monsters from the hand.")
        if pa.to_zone is not ZoneType.MONSTER:
          raise NotToMonsterZoneError("You can only normal summon into a main monster zone.")
        target_zone = self.turn_player.get_open_zone(pa.to_zone)
        self.turn_player.normal_summon(pa.card, target_zone)
      case PlayerActions.ACTIVATE_ST_CARD:
        # From zone must be from the hand, since it's activating a CARD. 
        # To see any effect activation, see ACTIVATE_EFFECT
        if pa.from_zone is not ZoneType.HAND:
          raise NotFromHandError("You can only activate a card from the hand.")
        
        if pa.to_zone is not ZoneType.SPELL_TRAP:
          raise NotToSpellTrapZoneError("You can only activate a spell/trap card into a spell/trap zone.")
        
        target_zone = self.turn_player.get_open_zone(pa.to_zone)
        self.turn_player.activate_st_card(pa.card, target_zone)
      case PlayerActions.SET_CARD:
        # Zone validation is deliberately minimal here: unlike NORMAL_SUMMON/ACTIVATE_ST_CARD,
        # a legal `to_zone` for SET_CARD depends on the card's type (monster -> MONSTER zone,
        # spell/trap -> SPELL_TRAP zone), so that check is delegated to `Player.set_card`.
        if pa.from_zone is not ZoneType.HAND:
          raise NotFromHandError("You can only set a card from the hand.")

        target_zone = self.turn_player.get_open_zone(pa.to_zone)
        self.turn_player.set_card(pa.card, target_zone)
