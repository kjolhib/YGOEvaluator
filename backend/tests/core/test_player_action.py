import pytest

from app.core.board_state import BoardState
from app.core.player import Player
from app.core.player_action import PlayerAction
from app.static.type_defs.card import Card, CardInstance

from app.static.type_defs.type_cards import CardType, Position
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_player_action import PlayerActions

from app.exceptions.actions.not_from_hand_error import NotFromHandError
from app.exceptions.actions.not_to_monster_zone_error import NotToMonsterZoneError
from app.exceptions.actions.not_to_spell_trap_zone_error import NotToSpellTrapZoneError

@pytest.fixture
def board():
  return BoardState(Player("p1"), Player("p2"))


########### `PLAYERACTION` DATACLASS TESTS ###########

def test_player_action__is_constructible(board: BoardState):
  card = Card(id=1, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)

  pa = PlayerAction(
    action=PlayerActions.NORMAL_SUMMON,
    player=board.turn_player,
    to_zone=ZoneType.MONSTER,
    from_zone=ZoneType.HAND,
    card=card_instance,
  )

  assert pa.action is PlayerActions.NORMAL_SUMMON
  assert pa.player is board.turn_player
  assert pa.to_zone is ZoneType.MONSTER
  assert pa.from_zone is ZoneType.HAND
  assert pa.card is card_instance


########### HANDLE_PLAYER_ACTION: NORMAL_SUMMON ###########

def test_handle_player_action__normal_summon_success(board: BoardState):
  card = Card(id=1, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  pa = PlayerAction(PlayerActions.NORMAL_SUMMON, board.turn_player, ZoneType.MONSTER, ZoneType.HAND, card_instance)

  board.handle_player_action(pa)
  assert len(board.turn_player.all_monsters()) == 1
  assert board.turn_player.normal_summon_used

def test_handle_player_action__normal_summon_not_from_hand(board: BoardState):
  card = Card(id=1, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_GY, ZoneType.GRAVEYARD)
  pa = PlayerAction(PlayerActions.NORMAL_SUMMON, board.turn_player, ZoneType.MONSTER, ZoneType.GRAVEYARD, card_instance)

  with pytest.raises(NotFromHandError):
    board.handle_player_action(pa)


########### HANDLE_PLAYER_ACTION: ACTIVATE_ST_CARD ###########

def test_handle_player_action__activate_st_card_success(board: BoardState):
  card = Card(id=2, name="Pot of Greed", card_type=CardType.SPELL)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  pa = PlayerAction(PlayerActions.ACTIVATE_ST_CARD, board.turn_player, ZoneType.SPELL_TRAP, ZoneType.HAND, card_instance)

  board.handle_player_action(pa)
  assert len(board.turn_player.all_spells_traps()) == 1

def test_handle_player_action__activate_st_card_wrong_to_zone(board: BoardState):
  card = Card(id=2, name="Pot of Greed", card_type=CardType.SPELL)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  pa = PlayerAction(PlayerActions.ACTIVATE_ST_CARD, board.turn_player, ZoneType.MONSTER, ZoneType.HAND, card_instance)

  with pytest.raises(NotToSpellTrapZoneError):
    board.handle_player_action(pa)


########### HANDLE_PLAYER_ACTION: SET_CARD ###########

def test_handle_player_action__set_card_monster_success(board: BoardState):
  card = Card(id=3, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  pa = PlayerAction(PlayerActions.SET_CARD, board.turn_player, ZoneType.MONSTER, ZoneType.HAND, card_instance)

  board.handle_player_action(pa)
  assert len(board.turn_player.all_monsters()) == 1
  assert board.turn_player.monster_zones[0].cards[0].current_position is Position.FACE_DOWN_MONSTER
  assert board.turn_player.normal_summon_used

def test_handle_player_action__set_card_spell_trap_success(board: BoardState):
  card = Card(id=4, name="Mirror Force", card_type=CardType.TRAP)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  pa = PlayerAction(PlayerActions.SET_CARD, board.turn_player, ZoneType.SPELL_TRAP, ZoneType.HAND, card_instance)

  board.handle_player_action(pa)
  assert len(board.turn_player.all_spells_traps()) == 1
  assert board.turn_player.spell_trap_zones[0].cards[0].current_position is Position.FACE_DOWN_ST
  assert not board.turn_player.normal_summon_used

def test_handle_player_action__set_card_not_from_hand(board: BoardState):
  card = Card(id=3, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_GY, ZoneType.GRAVEYARD)
  pa = PlayerAction(PlayerActions.SET_CARD, board.turn_player, ZoneType.MONSTER, ZoneType.GRAVEYARD, card_instance)

  with pytest.raises(NotFromHandError):
    board.handle_player_action(pa)

def test_handle_player_action__set_card_wrong_zone_for_card_type(board: BoardState):
  card = Card(id=3, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  pa = PlayerAction(PlayerActions.SET_CARD, board.turn_player, ZoneType.SPELL_TRAP, ZoneType.HAND, card_instance)

  with pytest.raises(NotToMonsterZoneError):
    board.handle_player_action(pa)
