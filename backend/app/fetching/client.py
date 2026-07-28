"""

"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from exceptions.fetching.FetchError import FetchError

BASE_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"

# A few dozen names per request is well under any practical URL-length limit. 
# Keeping this conservative also keeps us far under the 20 req/sec rate limit.
CHUNK_SIZE = 20

# Small safety-margin delay between batched requests. Batching alone should keep us well under 20 req/sec.
# The API explicitly warns that exceeding the limit blocks the IP for an hour, so this costs nothing and removes any risk from request timing.
REQUEST_DELAY_SECONDS = 0.1\

def _chunk(items: list[str], size: int) -> list[list[str]]:
  return [items[i:i + size] for i in range(0, len(items), size)]

def _fetch_batch(names: list[str]) -> list[dict[str, Any]]:
  """
  Fetches a single batch of card names in one request.

  If the API reports no matches for this batch at all (its `{"error": ...}` response shape), it returns an empty list rather than raising.
  A batch that's entirely typos shouldn't halt the whole fetch.
  Per-name missing-card reporting happens at the orchestration level (see `pipeline.py`) by diffing requested vs. returned names.

  Args:
    names (list[str]): exact card names to fetch, `|`-joined into one `name=` query per YGOPRODeck's batching support

  Returns:
    list[dict]: raw card dicts from the API's `data` field. 
  """
  query = "|".join(names)
  url = f"{BASE_URL}?{urllib.parse.urlencode({'name': query})}"

  try:
    with urllib.request.urlopen(url) as response:
      payload = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as e:
    # YGOPRODeck returns a non-200 with an {"error": "..."} body when nothing in the batch matches
    # Treat that the same as an empty batch result rather than a hard failure.
    try:
      payload = json.loads(e.read().decode("utf-8"))
    except (json.JSONDecodeError, AttributeError) as parse_error:
      raise FetchError(f"Request failed for batch {names!r}: {e}") from parse_error
  except urllib.error.URLError as e:
    raise FetchError(f"Request failed for batch {names!r}: {e}") from e

  if "error" in payload:
    return []

  return payload.get("data", [])

def fetch_cards(names: list[str]) -> list[dict[str, Any]]:
  """
  Fetches raw card data for the given list of card names, batching requests to respect YGOPRODeck's rate limit (20 req/ses).

  Args:
    names (list[str]): exact card names to fetch (e.g. from a pool file)

  Returns:
    list[dict]: raw API card dicts for every name that matched. Names with no match are simply absent from the result -- see `pipeline.py`'s `build_card_pool` for the diffing step that reports these back loudly.
  """
  results: list[dict[str, Any]] = []
  batches = _chunk(names, CHUNK_SIZE)

  for i, batch in enumerate(batches):
    results.extend(_fetch_batch(batch))
    if i < len(batches) - 1:
      time.sleep(REQUEST_DELAY_SECONDS)

  return results
