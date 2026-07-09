import sys
for p in sys.path:
  print(p)

import pytest

from app.core.BoardState import BoardState, TurnPhase
from app.core.Player import Player

@pytest.fixture
def board():
  player1 = Player("p1")
  player2 = Player("p2")
  return BoardState(player1, player2)

def test_basic_init(board: BoardState):
  assert board.turn_player.name is "p1"
  assert board.phase is TurnPhase.S_DRAW_PHASE
  assert board.turn_number is 1
  assert len(board.extra_monster_zones) is 2

def test_next_turn(board: BoardState):
  assert board.phase is TurnPhase.S_DRAW_PHASE
  for _ in range(10):
    board.advance_phase()
  # should now be ep
  assert board.phase is TurnPhase.END_PHASE
  
  board.advance_phase()
  assert board.turn_number is 2
  assert board.phase is TurnPhase.S_DRAW_PHASE

def test_advance_phase(board: BoardState):
  for _ in range(10):
    board.advance_phase()
  assert board.advance_phase() is TurnPhase.S_DRAW_PHASE
  assert board.advance_phase() is TurnPhase.DRAW_PHASE
  assert board.advance_phase() is TurnPhase.E_DRAW_PHASE
  assert board.advance_phase() is TurnPhase.S_STANDBY_PHASE
  assert board.advance_phase() is TurnPhase.STANDBY_PHASE
  assert board.advance_phase() is TurnPhase.E_STANDBY_PHASE
  assert board.advance_phase() is TurnPhase.S_MAIN_PHASE_1
  assert board.advance_phase() is TurnPhase.MAIN_PHASE_1
  assert board.advance_phase() is TurnPhase.E_MAIN_PHASE_1
  assert board.advance_phase() is TurnPhase.S_BATTLE_PHASE
  assert board.advance_phase() is TurnPhase.BATTLE_PHASE
  assert board.advance_phase() is TurnPhase.E_BATTLE_PHASE
  assert board.advance_phase() is TurnPhase.S_MAIN_PHASE_2
  assert board.advance_phase() is TurnPhase.MAIN_PHASE_2
  assert board.advance_phase() is TurnPhase.E_MAIN_PHASE_2
  assert board.advance_phase() is TurnPhase.S_END_PHASE
  assert board.advance_phase() is TurnPhase.END_PHASE
