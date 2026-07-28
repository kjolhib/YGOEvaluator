"""
Contains the pipeline of how the fetcher will fetch the card data.

Contains functions to read the card pool text file and write into JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.fetching.client import fetch_cards
from app.fetching.trim import trim_cards

def read_card_pool(input_path: str | Path) -> list[str]:
  """
  Reads a plain-text card pool file: one exact card name per line.

  Blank lines and lines starting with '#' (comments) are ignored, so the pool file can be hand-curated with notes.

  Args:
    input_path (str | Path): path to the pool file

  Returns:
    list[str]: card names in file order, de-duplicated (first occurrence
    wins, order otherwise preserved)
  """
  path = Path(input_path)
  names: list[str] = []
  seen: set[str] = set()

  for line in path.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
      continue
    if stripped not in seen:
      names.append(stripped)
      seen.add(stripped)

  return names

def write_cards_json(cards: list[dict], output_path: str | Path) -> None:
  """
  Writes trimmed card data to a JSON file, creating parent directories if needed.

  Args:
    cards (list[dict]): trimmed card dicts (see `app.fetching.trim`)
    output_path (str | Path): where to write the JSON file

  Returns:
    None
  """
  path = Path(output_path)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(cards, indent=2, ensure_ascii=False), encoding="utf-8")

def build_card_pool(input_path: str | Path, output_path: str | Path) -> list[str]:
  """
  Orchestrates the full fetch: reads the pool file, fetches + trims each card, writes the result as JSON, 
  and reports any requested names that had no match.

  Args:
    input_path (str | Path): plain-text pool file, one card name per line
    output_path (str | Path): where to write the trimmed JSON output

  Returns:
    list[str]: names from the input file that returned no match in the API
    response -- a typo in the pool file should be loud, not a silent gap in the evaluator's card knowledge later.
  """
  requested_names = read_card_pool(input_path)
  raw_cards = fetch_cards(requested_names)
  trimmed_cards = trim_cards(raw_cards)

  fetched_names = {card["name"] for card in trimmed_cards if "name" in card}
  missing_names = [name for name in requested_names if name not in fetched_names]

  write_cards_json(trimmed_cards, output_path)

  return missing_names
