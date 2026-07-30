# __main__.py

status: [done]
last updated: [29-07-2026]


**Path:** `backend/app/fetching/__main__.py`

## Context
The fetching package can be run directly to refresh the local card pool. Its default paths resolve from the backend directory so that the normal invocation from `backend/` writes `backend/data/cards.json` from `backend/data/card_pool.txt`.

The underlying implementation remains in `pipeline.py`; this file only owns command-line parsing, user-facing reporting, and the process return code.

## Purpose
Provide the `python -m app.fetching` entry point for generating a trimmed card-pool JSON file.

## Main Components

- `_BACKEND_ROOT` — derives the backend root from this module's location.
- `DEFAULT_INPUT` / `DEFAULT_OUTPUT` — default `card_pool.txt` and `cards.json` paths.
- `main(argv=None)` — parses optional `--input` and `--output` paths, runs the pipeline, prints results, and returns the appropriate exit status.
- `if __name__ == "__main__"` — exits the module process using `main`'s result.

## How It Fits In
Depends on `argparse`, `sys`, `pathlib.Path`, and `app.fetching.pipeline.build_card_pool`. It is the external entry point for maintainers; application code should normally call the pipeline directly when it already has paths in hand.

## Notes
`main` returns `1` when any requested card has no match, but still reports the output path because the JSON is written with all successful matches.
