# client.py

status: [done]
last updated: [29-07-2026]


**Path:** `backend/app/fetching/client.py`

## Context
The fetching package builds the local, format-scoped card pool used by the static card layer. `pipeline.py` supplies exact names from a hand-maintained text file and receives raw YGOPRODeck response objects from this module before `trim.py` reduces them to the project's stored schema.

This module is deliberately the network boundary. It knows how to call YGOPRODeck safely but does not interpret card types, write files, or decide which individual requested names were missing.

## Purpose
Fetch raw YGOPRODeck card records for a list of exact names while batching requests, pacing multi-batch work, and translating network failures into the project's `FetchError`.

## Main Components

- `BASE_URL` — the YGOPRODeck card-information endpoint.
- `REQUEST_HEADERS` — sends JSON acceptance and a project-specific browser-compatible user agent.
- `CHUNK_SIZE` / `REQUEST_DELAY_SECONDS` — limit each request to 20 names and pace requests between batches.
- `_chunk(items, size)` — splits the input names into ordered batches.
- `_fetch_batch(names)` — requests one `name=A|B|...` batch and returns its raw `data` entries; an API no-match response becomes an empty list.
- `fetch_cards(names)` — fetches every batch in order and returns the combined raw records.

## How It Fits In
Depends only on Python standard-library HTTP/JSON utilities and `app.exceptions.fetching.FetchError`. `app.fetching.pipeline.build_card_pool` is the main consumer; tests patch `urllib.request.urlopen` so the normal test suite never calls the live API.

## Notes
The API result only indicates which cards were returned. Per-name missing-card reporting belongs to `pipeline.build_card_pool`, which compares requested and returned names after fetching.
