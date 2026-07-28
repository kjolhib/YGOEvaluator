import json
from pathlib import Path

from app.fetching import pipeline


########### read_card_pool ###########

def test_read_card_pool_skips_blanks_comments_and_dedupes(tmp_path: Path):
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text(
    "# staple pool\n"
    "Ash Blossom & Joyous Spring\n"
    "\n"
    "Pot of Greed\n"
    "Pot of Greed\n"  # duplicate -> should be de-duplicated, first occurrence kept
  )

  names = pipeline.read_card_pool(pool_file)

  assert names == ["Ash Blossom & Joyous Spring", "Pot of Greed"]


########### write_cards_json ###########

def test_write_cards_json_creates_file_and_parent_dirs(tmp_path: Path):
  # nested path that doesn't exist yet -- write_cards_json should create it
  output_path = tmp_path / "nested" / "cards.json"
  cards = [{"id": 55144522, "name": "Pot of Greed"}]

  pipeline.write_cards_json(cards, output_path)

  assert output_path.exists()
  written = json.loads(output_path.read_text(encoding="utf-8"))
  assert written == cards


########### build_card_pool (end-to-end: pool file -> fetch -> trim -> json file) ###########

def test_build_card_pool_writes_trimmed_cards_to_json(tmp_path: Path, monkeypatch):
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text("Ash Blossom & Joyous Spring\nNot A Real Card\n")
  output_file = tmp_path / "cards.json"

  fake_raw_cards = [
    {
      "id": 14558127,
      "name": "Ash Blossom & Joyous Spring",
      "type": "Effect Monster",
      "frameType": "effect",  # should get dropped by the trim step
      "desc": "...",
      "atk": 0,
      "def": 1800,
      "level": 3,
      "race": "Zombie",
      "attribute": "FIRE",
      "ygoprodeck_url": "https://ygoprodeck.com/card/ash-blossom-joyous-spring-8388",
    }
  ]

  def fake_fetch_cards(names: list[str]):
    # confirms build_card_pool is passing the *requested* names through,
    # not something it derived itself
    assert names == ["Ash Blossom & Joyous Spring", "Not A Real Card"]
    return fake_raw_cards

  # only the network call is mocked -- read_card_pool/trim_cards/write_cards_json
  # all run for real against tmp_path, so this actually exercises reading the
  # pool file and writing a real .json file to disk.
  monkeypatch.setattr(pipeline, "fetch_cards", fake_fetch_cards)

  missing = pipeline.build_card_pool(pool_file, output_file)

  assert output_file.exists()
  written = json.loads(output_file.read_text(encoding="utf-8"))
  assert len(written) == 1
  assert written[0]["name"] == "Ash Blossom & Joyous Spring"
  assert "frameType" not in written[0]  # confirms the trim step actually ran before writing

  # the unmatched name is reported back, not silently dropped
  assert missing == ["Not A Real Card"]


def test_build_card_pool_reports_no_missing_when_everything_matches(tmp_path: Path, monkeypatch):
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text("Pot of Greed\n")
  output_file = tmp_path / "cards.json"

  monkeypatch.setattr(
    pipeline,
    "fetch_cards",
    lambda names: [{"id": 55144522, "name": "Pot of Greed", "type": "Spell Card", "race": "Normal"}],
  )

  missing = pipeline.build_card_pool(pool_file, output_file)

  assert missing == []
  written = json.loads(output_file.read_text(encoding="utf-8"))
  assert written == [{"id": 55144522, "name": "Pot of Greed", "type": "Spell Card", "race": "Normal"}]
