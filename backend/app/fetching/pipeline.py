"""
Contains the pipeline of how the fetcher will fetch the card data.

Contains functions to read the card pool text file and write into JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.fetching.client import fetch_cards
from app.fetching.trim import trim_cards

def load_existing_cards(output_path: str | Path) -> dict[str, dict]:
  """
  Loads existing cards in the specified format. Found in `<format>/cards.json`. The output is keyed by name, for lookup.

  Warns if a file already contains duplicated names. However, if someone edited the file manually, then duplicates will be manually caught and the loader will keep the newer one.

  Args:
    card_pool_path: path to the pool file

  Returns:
    dict[name, card]: outputs the dictionary-ised version of the json file. Where the name of the card maps to the card itself.
  """
  path = Path(output_path)
  try:
    with open(path, "r") as file:
      cards: list[dict] = json.load(file)
  except FileNotFoundError:
    print("No cards.json file exists to load exisitng cards, skipping...")
    return {}

  existing: dict[str, dict] = {}
  for card in cards:
    name = card.get("name")
    if name is None:
      continue

    # found duplicate
    if name in existing:
      print(f"WARNING: duplicate entry for '{name}' found in '{path}' while loading existing cards, dropping old one")

    existing[name] = card

  # returns a dict mapping the card's name to the card dict data.
  return existing

def read_card_pool(card_pool_path: str | Path, existing_cards: dict[str, dict], force_fetch: bool) -> list[str]:
  """
  Reads a plain-text card pool file: one exact card name per line.

  Blank lines, lines starting with or any characters after '#' (comments) are ignored, so the pool file can be hand-curated with notes. Mirrors how comments are treated in Python.

  Args:
    card_pool_path (str | Path): path to the pool file
    existing_cards: a dict of name -> card, of existing entries in cards.json. Used to optimise fetching.
    force_fetch: whether or not to ignore seen completely.

  Returns:
    list[str]: card names in file order, de-duplicated (first occurrence
    wins, order otherwise preserved)
  """
  path = Path(card_pool_path)
  names: list[str] = []
  seen: set[str] = set() if force_fetch else set(existing_cards.keys())

  for line in path.read_text(encoding="utf-8").splitlines():
    stripped_ws = line.strip()
    stripped = stripped_ws.split('#', 1)[0].strip() # ignores everything after a "#"
    if not stripped:
      continue
    if stripped not in seen:
      names.append(stripped)
      seen.add(stripped)

  return names

def write_cards_json(cards: list[dict], output_path: str | Path) -> None:
  """
  Writes trimmed card data to a JSON file.

  Args:
    cards (list[dict]): trimmed card dicts (see `app.fetching.trim`)
    output_path (str | Path): where to write the JSON file

  Returns:
    None
  """
  path = Path(output_path)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(cards, indent=2, ensure_ascii=False), encoding="utf-8")

def build_card_pool(card_pool_path: str | Path, output_path: str | Path, force_fetch: bool = False) -> list[str]:
  """
  Orchestrates the full fetch: reads the pool file, fetches + trims each card, writes the result as JSON, 
  and reports any requested names that had no match.

  Args:
    card_pool_path (str | Path): plain-text pool file, one card name per line
    output_path (str | Path): where to write the trimmed JSON output
    force_fetch: whether or not the --force-fetch flag was used. If used, it will ignore any existing/seen checks and fetch all cards found, and overwrite existing entries in `cards.json`. Defaulted to false

  Returns:
    list[str]: names from the input file that returned no match in the API
    response -- a typo in the pool file should be loud, not a silent gap in the evaluator's card knowledge later.
  """
  existing_cards = load_existing_cards(output_path)
  requested_names = read_card_pool(card_pool_path, existing_cards, force_fetch)
  raw_cards = fetch_cards(requested_names)
  trimmed_cards = trim_cards(raw_cards)

  fetched_names = {card["name"] for card in trimmed_cards if "name" in card}
  missing_names = [name for name in requested_names if name not in fetched_names]

  # New entries will overwrite the old entries when keys collide.
  # Her eas a backup in the case that a duplicate name was fetched, but that realistically shouldn't happen since `read_card_pool` already account for that.
  merged = {**existing_cards, **{card["name"]: card for card in trimmed_cards if "name" in card}}
  write_cards_json(list(merged.values()), output_path)

  return missing_names
