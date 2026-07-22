import pytest

from app.core.Card import CardInstance, Card
from app.core.Player import Player
from app.core.Zones import FieldZone

from app.type_defs.type_cards import CardType, Position
from app.type_defs.type_zones import ZoneType

from app.exceptions.actions.NotToMonsterZoneError import NotToMonsterZoneError
from app.exceptions.actions.NotMainMonsterError import NotMainMonsterError
from app.exceptions.actions.NotToSTZoneError import NotToSpellTrapZoneError
from app.exceptions.actions.NotSTCardError import NotSpellTrapCardError
from app.exceptions.actions.NotSettableCardError import NotSettableCardError
from app.exceptions.actions.NotToFieldZoneError import NotToFieldZoneError

@pytest.fixture
def player():
  return Player("p1")

########### NORMAL SUMMON TESTS ###########

def test_player_normal_summon__success(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789) # mock some random card
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.normal_summon(card_instance, player.monster_zones[0]) # should normal summon the monster into the first monster zone.
  assert len(player.all_monsters()) == 1
  assert player.normal_summon_used
  
  # make sure the card instance is actually saved
  extracted_zone: FieldZone = player.monster_zones[0]
  assert extracted_zone.capacity == 1
  assert len(extracted_zone.cards) == 1
  extracted_zone__card: CardInstance = extracted_zone.cards[0]
  assert extracted_zone__card.card.name == "Dark Magik guy"
  assert extracted_zone__card.card.card_id == 123456789
  assert extracted_zone__card.card.card_type is CardType.MONSTER

def test_player_normal_summon__not_to_monst_zone(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789) # mock some random card
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToMonsterZoneError):
    # should normal summon the monster into the 1st spell/trap zone
    player.normal_summon(card_instance, player.spell_trap_zones[0])
  assert len(player.all_monsters()) == 0
  assert not player.normal_summon_used

def test_player_normal_summon__not_a_main_deck_monster(player: Player):
  card = Card("Dark Magik spell", CardType.SPELL, card_id=123456789) # mock some random card
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotMainMonsterError):
    player.normal_summon(card_instance, player.monster_zones[0])

  assert len(player.all_monsters()) == 0
  assert not player.normal_summon_used


########### ACTIVATE S/T CARD TESTS ###########

def test_player_activate_card__success(player: Player):
  card = Card("Pot of Greed", CardType.SPELL, card_id=987654321)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.activate_st_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_spells_traps()) == 1

  extracted_zone: FieldZone = player.spell_trap_zones[0]
  assert len(extracted_zone.cards) == 1
  extracted_zone__card: CardInstance = extracted_zone.cards[0]
  assert extracted_zone__card.card.name == "Pot of Greed"
  assert extracted_zone__card.current_position is Position.FACE_UP_ST

def test_player_activate_card__not_to_st_zone(player: Player):
  card = Card("Pot of Greed", CardType.SPELL, card_id=987654321)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToSpellTrapZoneError):
    player.activate_st_card(card_instance, player.monster_zones[0])
  assert len(player.all_spells_traps()) == 0

def test_player_activate_card__not_a_spell_trap_card(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotSpellTrapCardError):
    player.activate_st_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_spells_traps()) == 0


########### SET CARD TESTS ###########

def test_player_set_card__monster_success(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.set_card(card_instance, player.monster_zones[0])
  assert len(player.all_monsters()) == 1
  assert player.normal_summon_used

  extracted_zone__card: CardInstance = player.monster_zones[0].cards[0]
  assert extracted_zone__card.current_position is Position.FACE_DOWN_MONSTER

def test_player_set_card__monster_consumes_normal_summon(player: Player):
  card1 = Card("Dark Magik guy", CardType.MONSTER, card_id=1)
  card2 = Card("Another Magik guy", CardType.MONSTER, card_id=2)
  ci1 = CardInstance(card1, Position.IN_HAND, ZoneType.HAND)
  ci2 = CardInstance(card2, Position.IN_HAND, ZoneType.HAND)

  player.set_card(ci1, player.monster_zones[0])
  assert player.normal_summon_used

  # second set/summon this turn should be a no-op (matches normal_summon's existing behaviour)
  player.set_card(ci2, player.monster_zones[1])
  assert len(player.all_monsters()) == 1

def test_player_set_card__spell_trap_success(player: Player):
  card = Card("Mirror Force", CardType.TRAP, card_id=555)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.set_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_spells_traps()) == 1
  assert not player.normal_summon_used  # setting a spell/trap does not use the normal summon

  extracted_zone__card: CardInstance = player.spell_trap_zones[0].cards[0]
  assert extracted_zone__card.current_position is Position.FACE_DOWN_ST

def test_player_set_card__monster_not_to_monster_zone(player: Player):
  card = Card("Dark Magik guy", CardType.MONSTER, card_id=123456789)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToMonsterZoneError):
    player.set_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_monsters()) == 0
  assert not player.normal_summon_used

def test_player_set_card__spell_trap_not_to_st_zone(player: Player):
  card = Card("Mirror Force", CardType.TRAP, card_id=555)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToSpellTrapZoneError):
    player.set_card(card_instance, player.monster_zones[0])
  assert len(player.all_spells_traps()) == 0

def test_player_set_card__set_field_to_monster(player: Player):
  card = Card("Field Spell", CardType.FIELD_SPELL, card_id=0000)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToFieldZoneError):
    player.set_card(card_instance, player.monster_zones[0])

def test_player_set_card__unsettable(player: Player):
  card = Card("Extra Deck Monster", CardType.EXTRA_DECK_MONSTER, card_id=0000)
  card_instance = CardInstance(card, Position.IN_ED, ZoneType.EXTRA_DECK)
  with pytest.raises(NotSettableCardError):
    player.set_card(card_instance, player.monster_zones[0])

