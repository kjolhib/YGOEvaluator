# pipeline.py

status: [done]
last updated: [29-07-2026]


**Path:** `backend/app/fetching/pipeline.py`

## Context
The fetching package turns a curated list of Yu-Gi-Oh card names into the trimmed `cards.json` consumed by the static card layer. This file coordinates the three boundaries of that flow: local text input, remote raw-card retrieval through `client.py`, and local JSON output after `trim.py` has removed unneeded fields.

It is the package's programmatic entry point. The command-line wrapper in `__main__.py` calls `build_card_pool` and converts its missing-name result into CLI output and an exit code.

## Purpose
Read a card-pool file, fetch and trim each matching card, write the resulting JSON, and return requested names that were not present in the fetched data.

## Main Components

- `read_card_pool(input_path)` — reads one name per line, ignores blank/comment lines, and de-duplicates names while preserving first-seen order.
- `write_cards_json(cards, output_path)` — creates missing parent directories and writes indented UTF-8 JSON.
- `build_card_pool(input_path, output_path)` — orchestrates read → fetch → trim → write and returns unmatched requested names.

## How It Fits In
Depends on `app.fetching.client.fetch_cards`, `app.fetching.trim.trim_cards`, `json`, and `pathlib.Path`. It is called by `app.fetching.__main__`; its output JSON is loaded later by `app.static.Card.load_cards`.

## Notes
The output file is written even when one or more requested names are missing. Callers must inspect the returned list (as the CLI does) if an incomplete pool should be treated as a failure.
