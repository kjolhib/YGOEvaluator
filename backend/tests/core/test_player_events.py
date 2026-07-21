import pytest

from app.core.Card import CardInstance, Card
from app.core.Player import Player
from app.core.Zones import FieldZone

from app.type_defs.type_cards import CardType, Position
from app.type_defs.type_zones import ZoneType

@pytest.fixture
def player():
  return Player("p1")

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
