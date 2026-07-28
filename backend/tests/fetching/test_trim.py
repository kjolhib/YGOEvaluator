import json
from pathlib import Path

from app.fetching.trim import trim_card, trim_cards

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
  return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


########### DROPPED-FIELD SWEEP (applies regardless of card type) ###########

def test_trim_card_drops_non_evaluator_fields():
  raw = _load_fixture("monster.json")
  trimmed = trim_card(raw)

  for dropped_field in ("frameType", "ygoprodeck_url", "card_sets", "card_images", "card_prices"):
    assert dropped_field not in trimmed


########### PER-CARD-TYPE SCHEMA CHECKS ###########

def test_trim_card_monster():
  raw = _load_fixture("monster.json")
  trimmed = trim_card(raw)

  assert trimmed["id"] == 14558127
  assert trimmed["name"] == "Ash Blossom & Joyous Spring"
  assert trimmed["type"] == "Effect Monster"  # kept raw, not mapped to CardType (deferred to static layer)
  assert trimmed["race"] == "Zombie"
  assert trimmed["attribute"] == "FIRE"
  assert trimmed["atk"] == 0
  assert trimmed["def"] == 1800
  assert trimmed["level"] == 3
  assert trimmed["archetype"] == "Ash Blossom"
  assert "desc" in trimmed

def test_trim_card_spell():
  raw = _load_fixture("spell.json")
  trimmed = trim_card(raw)

  assert trimmed["type"] == "Spell Card"
  assert trimmed["race"] == "Normal"
  assert "archetype" not in trimmed  # wasn't present on the raw card
  assert "banlist_info" not in trimmed
  for monster_only_field in ("atk", "def", "level", "attribute"):
    assert monster_only_field not in trimmed

def test_trim_card_field_spell():
  raw = _load_fixture("field_spell.json")
  trimmed = trim_card(raw)

  # this is what actually distinguishes a Field Spell in the raw schema
  assert trimmed["type"] == "Spell Card"
  assert trimmed["race"] == "Field"

def test_trim_card_pendulum():
  raw = _load_fixture("pendulum.json")
  trimmed = trim_card(raw)

  assert trimmed["scale"] == 4
  assert trimmed["level"] == 7
  assert trimmed["archetype"] == "Test Archetype"

def test_trim_card_xyz():
  raw = _load_fixture("xyz.json")
  trimmed = trim_card(raw)

  assert trimmed["type"] == "XYZ Monster"
  assert trimmed["level"] == 4  # API stores XYZ Rank under 'level'
  assert "scale" not in trimmed
  assert "linkval" not in trimmed

def test_trim_card_link():
  raw = _load_fixture("link.json")
  trimmed = trim_card(raw)

  assert trimmed["linkval"] == 3
  assert trimmed["linkmarkers"] == ["Top", "Bottom-Left", "Bottom-Right"]
  # Link Monsters genuinely have no DEF or Level in the raw API -- the
  # trim function must not invent them.
  assert "def" not in trimmed
  assert "level" not in trimmed


########### trim_cards (list form) ###########

def test_trim_cards_trims_each_entry():
  raws = [_load_fixture("monster.json"), _load_fixture("spell.json")]
  trimmed = trim_cards(raws)

  assert len(trimmed) == 2
  assert trimmed[0]["name"] == "Ash Blossom & Joyous Spring"
  assert trimmed[1]["name"] == "Pot of Greed"
  assert "frameType" not in trimmed[0]
  assert "frameType" not in trimmed[1]
