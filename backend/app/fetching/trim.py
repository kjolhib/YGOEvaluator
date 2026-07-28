from __future__ import annotations

from typing import Any

# Fields kept regardless of card type.
_ALWAYS_KEEP = ("id", "name", "type", "race", "archetype", "desc")

# Fields kept only when present on the raw card (monster/pendulum/link-only fields
# The API omits these entirely for card types they don't apply to, rather than sending them as null.
_KEEP_IF_PRESENT = ("atk", "def", "level", "attribute", "scale", "linkval", "linkmarkers")

# Everything else -- frameType, ygoprodeck_url, card_sets, card_images, card_prices, banlist_info -- are dropped by omission below.
# None of these serve an in-duel evaluator; see docs/plan/_fetching_storage_plan.md.

def trim_card(raw_card: dict[str, Any]) -> dict[str, Any]:
  """
  Trims a raw YGOPRODeck card dict down to this project's schema.

  Deliberately does NOT map the raw `type` string onto this project's `CardType` enum (app/type_defs/type_cards.py)
  That mapping is deferred to the static-layer pass.
  This function's job is purely acquisition/trimming, not interpretation of the data.

  Args:
    raw_card (dict): one card object as returned by the YGOPRODeck API

  Returns:
    dict: trimmed card data, keeping only the fields this project cares about, in the same shape/types the API provided them in
  """
  trimmed: dict[str, Any] = {}

  for field_name in _ALWAYS_KEEP:
    if field_name in raw_card:
      trimmed[field_name] = raw_card[field_name]

  for field_name in _KEEP_IF_PRESENT:
    if field_name in raw_card:
      trimmed[field_name] = raw_card[field_name]

  return trimmed

def trim_cards(raw_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
  """Trims a list of raw YGOPRODeck card dicts. See `trim_card`."""
  return [trim_card(raw_card) for raw_card in raw_cards]
