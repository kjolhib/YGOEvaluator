import json
from pathlib import Path

from app.exceptions.loading.no_cards_json_error import NoCardsJsonError
from app.static.type_defs.card import Card


def load_cards(cards_json_path: str | Path) -> list[Card]:
  """
  Loads every card from a trimmed `cards.json` (see `app.fetching.pipeline.build_card_pool`) into a list of `Card` objects.

  Args:
    cards_json_path (str | Path): path to a trimmed cards JSON file

  Returns:
    list[Card]: one `Card` per entry, in file order
  """
  if cards_json_path is None:
    raise NoCardsJsonError("Could not load cards: cards.json was not found")
  path = Path(cards_json_path)
  raw_cards = json.loads(path.read_text(encoding="utf-8"))
  return [Card.from_raw(raw_card) for raw_card in raw_cards]


def index_cards_by_name(cards: list[Card]) -> dict[str, Card]:
  """
  Indexes a list of `Card`s by name, for lookups like "give me the `Card`
  for 'Ash Blossom & Joyous Spring'" when building a `CardInstance`.

  Args:
    cards (list[Card]): cards to index, e.g. from `load_cards`

  Returns:
    dict[str, Card]: card name -> `Card`
  """
  return {card.name: card for card in cards}

