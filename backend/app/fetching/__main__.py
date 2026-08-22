"""
Main driver for the fetcher module.

The fetcher module fetches card data from YGOPRODeck.com based on a `card_pool.txt` file.

For more information, see `docs/backend/fetcher/fetcher.md`.
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

from app.fetching.pipeline import build_card_pool
from app.exceptions.fetching.FormatNotFoundError import FormatNotFoundError

# backend/app/fetching/__main__.py -> parents[2] is backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Fetch a hand-picked card pool from YGOPRODeck into a trimmed cards.json."
  )
  parser.add_argument(
    "--format",
    required=True,
    help=f"A folder containing the plain-text card_pool.txt file). Does not overwrite existing card entries in cards.json.",
  )
  parser.add_argument(
    "--force-fetch",
    dest="force",
    action="store_true",
    help="Forces the fetcher to overwrite existing entries in cards.json."
  )
  args = parser.parse_args(argv)
  # path to the format folder itself, e.g. backend/data/Ryzeal_2024
  format_path = _BACKEND_ROOT / "data" / args.format

  # check if the specified format folder exists
  if not os.path.isdir(format_path):
    raise FormatNotFoundError(f"Error: format {args.format} does not exist on path '{format_path}'.")

  # paths to the specific card_pool.txt and cards.json. E.g. backend/data/Ryzeal_2024/card_pool.txt
  card_pool_path = Path(format_path) / "card_pool.txt"
  output_path = _BACKEND_ROOT / "data" / args.format / "cards.json"
  missing = build_card_pool(card_pool_path, output_path, args.force)

  if missing:
    print(f"WARNING: {len(missing)} name(s) from {args.format} had no match:", file=sys.stderr)
    for name in missing:
      print(f"  - {name}", file=sys.stderr)

  print(f"Wrote cards to data/{args.format}/cards.json")
  return 1 if missing else 0

if __name__ == "__main__":
  raise SystemExit(main())
