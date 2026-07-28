"""
Main driver for the fetcher module.

The fetcher module fetches card data from YGOPRODeck.com based on a `card_pool.txt` file.

For more information, see `docs/backend/fetcher/fetcher.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.fetching.pipeline import build_card_pool

# backend/app/fetching/__main__.py -> parents[2] is backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = _BACKEND_ROOT / "data" / "card_pool.txt"
DEFAULT_OUTPUT = _BACKEND_ROOT / "data" / "cards.json"

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Fetch a hand-picked card pool from YGOPRODeck into a trimmed cards.json."
  )
  parser.add_argument(
    "--input",
    default=str(DEFAULT_INPUT),
    help=f"Plain-text card pool file, one exact card name per line (default: {DEFAULT_INPUT})",
  )
  parser.add_argument(
    "--output",
    default=str(DEFAULT_OUTPUT),
    help=f"Where to write the trimmed JSON output (default: {DEFAULT_OUTPUT})",
  )
  args = parser.parse_args(argv)

  missing = build_card_pool(args.input, args.output)

  if missing:
    print(f"WARNING: {len(missing)} name(s) from {args.input} had no match:", file=sys.stderr)
    for name in missing:
      print(f"  - {name}", file=sys.stderr)

  print(f"Wrote cards to {args.output}")
  return 1 if missing else 0

if __name__ == "__main__":
  raise SystemExit(main())
