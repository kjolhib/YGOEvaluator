import pytest

from app.static.Card import CardInstance, Card
from app.core.Player import Player
from app.core.Zones import FieldZone

from backend.app.static.type_defs.type_cards import CardType, Position
from backend.app.static.type_defs.type_zones import ZoneType

from backend.app.exceptions.actions.not_to_monster_zone_error import NotToMonsterZoneError
from backend.app.exceptions.actions.not_main_monster_zone_error import NotMainMonsterZoneError
from backend.app.exceptions.actions.not_to_spell_trap_zone_error import NotToSpellTrapZoneError
from backend.app.exceptions.actions.not_st_card_error import NotSpellTrapCardError
from backend.app.exceptions.actions.not_settable_card_error import NotSettableCardError
from backend.app.exceptions.actions.not_to_field_zone_error import NotToFieldZoneError

@pytest.fixture
def player():
  return Player("p1")

########### NORMAL SUMMON TESTS ###########

def test_player_normal_summon__success(player: Player):
  card = Card(id=123456789, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
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
  assert extracted_zone__card.card.id == 123456789
  assert extracted_zone__card.card.card_type is CardType.EFFECT_MONSTER

def test_player_normal_summon__not_to_monst_zone(player: Player):
  card = Card(id=123456789, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToMonsterZoneError):
    # should normal summon the monster into the 1st spell/trap zone
    player.normal_summon(card_instance, player.spell_trap_zones[0])
  assert len(player.all_monsters()) == 0
  assert not player.normal_summon_used

def test_player_normal_summon__not_a_main_deck_monster(player: Player):
  card = Card(id=123456789, name="Dark Magik spell", card_type=CardType.SPELL)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotMainMonsterZoneError):
    player.normal_summon(card_instance, player.monster_zones[0])

  assert len(player.all_monsters()) == 0
  assert not player.normal_summon_used


########### ACTIVATE S/T CARD TESTS ###########

def test_player_activate_card__success(player: Player):
  card = Card(id=987654321, name="Pot of Greed", card_type=CardType.SPELL)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.activate_st_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_spells_traps()) == 1

  extracted_zone: FieldZone = player.spell_trap_zones[0]
  assert len(extracted_zone.cards) == 1
  extracted_zone__card: CardInstance = extracted_zone.cards[0]
  assert extracted_zone__card.card.name == "Pot of Greed"
  assert extracted_zone__card.current_position is Position.FACE_UP_ST

def test_player_activate_card__not_to_st_zone(player: Player):
  card = Card(id=987654321, name="Pot of Greed", card_type=CardType.SPELL)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToSpellTrapZoneError):
    player.activate_st_card(card_instance, player.monster_zones[0])
  assert len(player.all_spells_traps()) == 0

def test_player_activate_card__not_a_spell_trap_card(player: Player):
  card = Card(id=123456789, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotSpellTrapCardError):
    player.activate_st_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_spells_traps()) == 0


########### SET CARD TESTS ###########

def test_player_set_card__monster_success(player: Player):
  card = Card(id=123456789, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.set_card(card_instance, player.monster_zones[0])
  assert len(player.all_monsters()) == 1
  assert player.normal_summon_used

  extracted_zone__card: CardInstance = player.monster_zones[0].cards[0]
  assert extracted_zone__card.current_position is Position.FACE_DOWN_MONSTER

def test_player_set_card__monster_consumes_normal_summon(player: Player):
  card1 = Card(id=1, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card2 = Card(id=2, name="Another Magik guy", card_type=CardType.EFFECT_MONSTER)
  ci1 = CardInstance(card1, Position.IN_HAND, ZoneType.HAND)
  ci2 = CardInstance(card2, Position.IN_HAND, ZoneType.HAND)

  player.set_card(ci1, player.monster_zones[0])
  assert player.normal_summon_used

  # second set/summon this turn should be a no-op (matches normal_summon's existing behaviour)
  player.set_card(ci2, player.monster_zones[1])
  assert len(player.all_monsters()) == 1

def test_player_set_card__spell_trap_success(player: Player):
  card = Card(id=555, name="Mirror Force", card_type=CardType.TRAP)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  player.set_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_spells_traps()) == 1
  assert not player.normal_summon_used  # setting a spell/trap does not use the normal summon

  extracted_zone__card: CardInstance = player.spell_trap_zones[0].cards[0]
  assert extracted_zone__card.current_position is Position.FACE_DOWN_ST

def test_player_set_card__monster_not_to_monster_zone(player: Player):
  card = Card(id=123456789, name="Dark Magik guy", card_type=CardType.EFFECT_MONSTER)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToMonsterZoneError):
    player.set_card(card_instance, player.spell_trap_zones[0])
  assert len(player.all_monsters()) == 0
  assert not player.normal_summon_used

def test_player_set_card__spell_trap_not_to_st_zone(player: Player):
  card = Card(id=555, name="Mirror Force", card_type=CardType.TRAP)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToSpellTrapZoneError):
    player.set_card(card_instance, player.monster_zones[0])
  assert len(player.all_spells_traps()) == 0

def test_player_set_card__set_field_to_monster(player: Player):
  card = Card(id=0, name="Field Spell", card_type=CardType.FIELD_SPELL)
  card_instance = CardInstance(card, Position.IN_HAND, ZoneType.HAND)
  with pytest.raises(NotToFieldZoneError):
    player.set_card(card_instance, player.monster_zones[0])

def test_player_set_card__unsettable(player: Player):
  card = Card(id=0, name="Extra Deck Monster", card_type=CardType.LINK_MONSTER)
  card_instance = CardInstance(card, Position.IN_ED, ZoneType.EXTRA_DECK)
  with pytest.raises(NotSettableCardError):
    player.set_card(card_instance, player.monster_zones[0])
