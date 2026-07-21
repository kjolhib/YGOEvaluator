import pytest

from app.core.Card import CardInstance, Card
from app.core.Player import Player
from app.core.Zones import FieldZone

from app.type_defs.type_cards import CardType, Position
from app.type_defs.type_zones import ZoneType

from app.exceptions.actions.NotToMonsterZoneError import NotToMonsterZoneError
from app.exceptions.actions.NotMainMonsterError import NotMainMonsterError

@pytest.fixture
def player():
  return Player("p1")

########### NORMAL SUMMON TESTS ###########

def test_player_normal_summon__success(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789) # mock some random card
  card_instance = CardInstance(card, Position.FACE_UP_ATK, ZoneType.HAND)
  player.normal_summon(card_instance, player.monster_zones[0]) # should normal summon the monster into the first monster zone.
  assert len(player.all_monsters()) is 1
  assert player.normal_summon_used
  
  # make sure the card instance is actually saved
  extracted_zone: FieldZone = player.monster_zones[0]
  assert extracted_zone.capacity is 1
  assert len(extracted_zone.cards) is 1
  extracted_zone__card: CardInstance = extracted_zone.cards[0]
  assert extracted_zone__card.card.name is "Dark Magik guy" 
  assert extracted_zone__card.card.card_id is 123456789
  assert extracted_zone__card.card.card_type is CardType.MONSTER

def test_player_normal_summon__not_to_monst_zone(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789) # mock some random card
  card_instance = CardInstance(card, Position.FACE_UP_ATK, ZoneType.HAND)
  with pytest.raises(NotToMonsterZoneError):
    # should normal summon the monster into the 1st spell/trap zone
    player.normal_summon(card_instance, player.spell_trap_zones[0])
  assert len(player.all_monsters()) is 0
  assert not player.normal_summon_used

def test_player_normal_summon__not_a_main_deck_monster(player: Player):
  card = Card("Dark Magik spell", CardType.SPELL, card_id=123456789) # mock some random card
  card_instance = CardInstance(card, Position.FACE_UP_ATK, ZoneType.HAND)
  with pytest.raises(NotMainMonsterError):
    player.normal_summon(card_instance, player.monster_zones[0])

  assert len(player.all_monsters()) is 0
  assert not player.normal_summon_used
