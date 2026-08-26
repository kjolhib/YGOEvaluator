from pathlib import Path

from app.static.card import Card, load_cards
from app.static.type_defs.type_cards import (
  CardType,
  EXTRA_DECK_MONSTER_TYPES,
  MAIN_DECK_MONSTER_TYPES,
  map_card_type,
)


def test_card_from_raw_maps_def_to_defense():
  raw_card = {
    "id": 1,
    "name": "Test Monster",
    "type": "Effect Monster",
    "race": "Dragon",
    "desc": "Test effect",
    "def": 1800,
  }

  card = Card.from_raw(raw_card)

  assert card.defense == 1800
  assert card.card_type is CardType.EFFECT_MONSTER


def test_load_cards_reads_checked_in_cards_json():
  cards_path = Path(__file__).resolve().parents[1] / ".." / "data" / "example_data" / "cards.json"

  cards = load_cards(cards_path)

  assert len(cards) == 2
  assert [card.name for card in cards] == ["Ash Blossom & Joyous Spring", "Pot of Greed"]
  assert cards[0].card_type is CardType.EFFECT_MONSTER
  assert cards[1].card_type is CardType.SPELL


def test_map_card_type_handles_pendulum_and_extra_deck_variants():
  assert map_card_type("Normal Monster", "Dragon") is CardType.NORMAL_MONSTER
  assert map_card_type("Pendulum Effect Monster", "Dragon") is CardType.EFFECT_MONSTER
  assert map_card_type("Pendulum Fusion Monster", "Dragon") is CardType.FUSION_MONSTER
  assert map_card_type("XYZ Monster", "Dragon") is CardType.XYZ_MONSTER
  assert map_card_type("Link Monster", "Dragon") is CardType.LINK_MONSTER
  assert map_card_type("Spell Card", "Normal") is CardType.SPELL
  assert map_card_type("Spell Card", "Field") is CardType.FIELD_SPELL
  assert map_card_type("Trap Card", "Normal") is CardType.TRAP


def test_main_and_extra_deck_monster_sets_are_correct():
  assert CardType.NORMAL_MONSTER in MAIN_DECK_MONSTER_TYPES
  assert CardType.EFFECT_MONSTER in MAIN_DECK_MONSTER_TYPES
  assert CardType.RITUAL_MONSTER in MAIN_DECK_MONSTER_TYPES

  assert CardType.FUSION_MONSTER in EXTRA_DECK_MONSTER_TYPES
  assert CardType.SYNCHRO_MONSTER in EXTRA_DECK_MONSTER_TYPES
  assert CardType.XYZ_MONSTER in EXTRA_DECK_MONSTER_TYPES
  assert CardType.LINK_MONSTER in EXTRA_DECK_MONSTER_TYPES
