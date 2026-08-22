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

  names = pipeline.read_card_pool(pool_file, existing_cards={}, force_fetch=False)

  assert names == ["Ash Blossom & Joyous Spring", "Pot of Greed"]

def test_read_card_pool_strips_inline_comments(tmp_path: Path):
  # regression: "Card Name # note" used to leave a trailing space on the name (only the '#' onward was dropped, not the space before it).
  # This silently broke exact-name matching against the API.
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text("Ash Blossom & Joyous Spring # exact name required\n")

  names = pipeline.read_card_pool(pool_file, existing_cards={}, force_fetch=False)

  assert names == ["Ash Blossom & Joyous Spring"]

def test_read_card_pool_skips_names_already_in_existing_cards(tmp_path: Path):
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text("Ash Blossom & Joyous Spring\nPot of Greed\n")
  existing_cards = {"Ash Blossom & Joyous Spring": {"id": 14558127, "name": "Ash Blossom & Joyous Spring"}} # exact card details isn't relevant for this test

  names = pipeline.read_card_pool(pool_file, existing_cards, force_fetch=False)

  assert names == ["Pot of Greed"]

def test_read_card_pool_force_fetch_ignores_existing_cards(tmp_path: Path):
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text("Ash Blossom & Joyous Spring\nPot of Greed\n")
  existing_cards = {"Ash Blossom & Joyous Spring": {"id": 14558127, "name": "Ash Blossom & Joyous Spring"}}

  names = pipeline.read_card_pool(pool_file, existing_cards, force_fetch=True)

  # force_fetch bypasses the existing-cards skip entirely -- both names come back
  assert names == ["Ash Blossom & Joyous Spring", "Pot of Greed"]

def test_read_card_pool_force_fetch_still_dedupes_within_file(tmp_path: Path):
  # force_fetch should only ignore *existing_cards*, not re-introduce duplicate lines from within the same pool file.
  pool_file = tmp_path / "card_pool.txt"
  pool_file.write_text("Pot of Greed\nPot of Greed\n")

  names = pipeline.read_card_pool(pool_file, existing_cards={}, force_fetch=True)

  assert names == ["Pot of Greed"]


########### load_existing_cards ###########

def test_load_existing_cards_keys_by_name(tmp_path: Path):
  output_file = tmp_path / "cards.json"
  cards = [
    {"id": 14558127, "name": "Ash Blossom & Joyous Spring", "type": "Tuner Monster"},
    {"id": 55144522, "name": "Pot of Greed", "type": "Spell Card"},
  ]
  output_file.write_text(json.dumps(cards), encoding="utf-8")

  existing = pipeline.load_existing_cards(output_file)

  assert existing == {
    "Ash Blossom & Joyous Spring": cards[0],
    "Pot of Greed": cards[1],
  }

def test_load_existing_cards_missing_file_returns_empty_dict(tmp_path: Path):
  output_file = tmp_path / "does_not_exist.json"

  assert pipeline.load_existing_cards(output_file) == {}

def test_load_existing_cards_warns_on_duplicate_names(tmp_path: Path, capsys):
  output_file = tmp_path / "cards.json"
  # Two entries sharing a name shouldn't happen via this pipeline's own merge (a dict can't hold duplicate keys)
  # Instead, this simulates a hand-edited or externally-produced cards.json that already has the problem.
  cards = [
    {"id": 1, "name": "Duplicate Card", "atk": 100},
    {"id": 2, "name": "Duplicate Card", "atk": 200},
  ]
  output_file.write_text(json.dumps(cards), encoding="utf-8")

  existing = pipeline.load_existing_cards(output_file)

  assert existing["Duplicate Card"]["id"] == 2  # last occurrence wins
  assert "duplicate entry" in capsys.readouterr().out.lower()


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


def test_build_card_pool_skips_refetching_existing_cards_by_default(tmp_path: Path, monkeypatch):
  """
  Two build_card_pool calls against the same cards.json: the second pool file
  is identical to the first plus one extra card appended at the bottom.
  Only that one new card should ever hit fetch_cards.
  """
  output_file = tmp_path / "cards.json"
  pool_file = tmp_path / "card_pool.txt"

  first_names = ["Ash Blossom & Joyous Spring", "Pot of Greed", "Called by the Grave"]
  pool_file.write_text("\n".join(first_names) + "\n")

  fetch_calls: list[list[str]] = []
  def fake_fetch_cards(names: list[str]):
    fetch_calls.append(list(names))
    return [{"id": i, "name": n} for i, n in enumerate(names)]

  monkeypatch.setattr(pipeline, "fetch_cards", fake_fetch_cards)

  # First run: nothing exists yet -> all n cards get fetched
  pipeline.build_card_pool(pool_file, output_file)
  assert fetch_calls == [first_names]

  # Second run: identical pool plus one new card at the very bottom
  second_names = first_names + ["Nibiru, the Primal Being"]
  pool_file.write_text("\n".join(second_names) + "\n")

  pipeline.build_card_pool(pool_file, output_file)

  # Only the new card should have gone out over the (mocked) wire
  assert len(fetch_calls) == 2
  assert fetch_calls[1] == ["Nibiru, the Primal Being"]

  written = json.loads(output_file.read_text(encoding="utf-8"))
  assert {c["name"] for c in written} == set(second_names)


def test_build_card_pool_force_fetch_refetches_everything(tmp_path: Path, monkeypatch):
  """
  Same shape as the skip-existing test above, but with force_fetch=True on
  the second call: the full n+1 names should be sent, not just the new one.
  """
  output_file = tmp_path / "cards.json"
  pool_file = tmp_path / "card_pool.txt"

  first_names = ["Ash Blossom & Joyous Spring", "Pot of Greed"]
  pool_file.write_text("\n".join(first_names) + "\n")

  fetch_calls: list[list[str]] = []
  def fake_fetch_cards(names: list[str]):
    fetch_calls.append(list(names))
    return [{"id": i, "name": n} for i, n in enumerate(names)]

  monkeypatch.setattr(pipeline, "fetch_cards", fake_fetch_cards)

  pipeline.build_card_pool(pool_file, output_file)
  assert fetch_calls[0] == first_names

  second_names = first_names + ["Called by the Grave"]
  pool_file.write_text("\n".join(second_names) + "\n")

  pipeline.build_card_pool(pool_file, output_file, force_fetch=True)

  # force-fetch bypasses the skip -- ALL n+1 names go out, not just the new one
  assert fetch_calls[1] == second_names


def test_build_card_pool_force_fetch_overwrites_stale_stats(tmp_path: Path, monkeypatch):
  """
  Shape for an errata-style overwrite test. cards.json is hand-authored here
  (not built via build_card_pool) to represent "pre-errata" stored data;
  fetch_cards is mocked to return "post-errata" data for the same name.
  force_fetch=True should mean the stored entry gets fully replaced.

  Swap in a real card name / real before-after fields for whatever errata
  you want to model -- the TODOs mark the placeholder values.
  """
  output_file = tmp_path / "cards.json"
  pool_file = tmp_path / "card_pool.txt"

  card_name = "Some Erratad Card"  # TODO: real card name
  pool_file.write_text(f"{card_name}\n")

  # hand-authored "before errata" state, written directly to cards.json
  # rather than produced by a real fetch
  pre_errata = [{
    "id": 12345678,     # TODO: real id
    "name": card_name,
    "type": "Effect Monster",
    "atk": 1000,        # TODO: pre-errata value
    "def": 1000,        # TODO: pre-errata value
  }]
  output_file.write_text(json.dumps(pre_errata), encoding="utf-8")

  # "post errata" state, as if this is what the API now returns
  post_errata = {
    "id": 12345678,
    "name": card_name,
    "type": "Effect Monster",
    "atk": 0,           # TODO: post-errata value
    "def": 1000,
  }

  monkeypatch.setattr(pipeline, "fetch_cards", lambda names: [post_errata])

  missing = pipeline.build_card_pool(pool_file, output_file, force_fetch=True)

  assert missing == []
  written = json.loads(output_file.read_text(encoding="utf-8"))
  # note: this is a whole-entry replace, not a field-by-field merge -- if
  # post_errata were missing a field pre_errata had, that field would be
  # gone entirely rather than preserved. That matches "overwrite" semantics,
  # but worth keeping in mind if the trimmed API response is ever partial.
  assert written == [post_errata]
