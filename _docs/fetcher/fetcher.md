# YGOEvaluator — Fetcher

[status]: done
[last_updated]: 22-08-2026

Implements the fetching/storage pipeline described in `docs/fetching_data.md` and `docs/storage.md`.
This is infrastructure only — it produces trimmed JSON, not `Card`/`CardType` Python objects. Converting `cards.json` into `Card` instances is the static-layer pass, not this one. See [Out of Scope](#out-of-scope)

Note that I believe it is possible to use [ygoapi](https://github.com/TimMikeladze/ygoapi) to fetch instead of hand writing it, but that is written for Typescript, and I haven't looked into it. It might just be a **lot** easier down the line.

## What it does

Given a plain-text list of exact card names, the fetcher:

1. Reads the list (`read_card_pool`).
2. Fetches those cards from the YGOPRODeck API, batched into as *few* requests as possible (`fetch_cards`).
3. Trims each raw API response down to the fields this project cares about (`trim_cards`). This **will likely** be expanded in the future.
4. Writes the result to a single local JSON file (`write_cards_json`).
5. Reports back any requested names that had no match, or any other issues found.

All four steps are tied together by `build_card_pool(input_path, output_path)`, which is what both the CLI and any calling code should normally use.

## Module layout

```
backend/app/fetching/
  client.py     fetch_cards(names) -> list[dict]        (network layer)
  trim.py       trim_card(raw) / trim_cards(raws) -> dict/list[dict]
  pipeline.py   read_card_pool, write_cards_json, build_card_pool
  __main__.py   CLI entry point (`python -m app.fetching`)

backend/data/
  <format name>/card_pool.txt   input: one exact card name per line (hand-curated)
  cards.json      output: trimmed card data (generated, not committed input)
```

### `client.py`

`fetch_cards(names: list[str]) -> list[dict]` is the only function meant to be called from outside this module.

Internally it:
- Chunks `names` into batches of `CHUNK_SIZE` (20) and issues one `name=A|B|C`-style request per batch, rather than one request per card.
- Sleeps `REQUEST_DELAY_SECONDS` (0.1s) between batches as a safety margin. YGOPRODeck's limit is 20 requests/sec; exceeding it blocks the calling IP for an hour, and its API actually explicitly asks callers to batch rather than hammer it with requests.
- Treats a batch that matches nothing as an empty result rather than an error — YGOPRODeck returns a non-200 response with an `{"error": ...}` body when a batch has zero matches. Genuine network/parsing failures raise `FetchError`.
- Uses stdlib `urllib.request` — no extra dependency for a handful of GET
  requests. 
  
  Requests are sent with a browser-style `User-Agent` header
  (`REQUEST_HEADERS` in `client.py`). This is because, YGOPRODeck's server will 403 default
  `urllib` User-Agent (`Python-urllib/3.x`), which I think it reads as a generic bot to whatever's fronting the API.
  
  I believe this is the standard fix for a very commonly-reported issue with this specific API and default `urllib`/`requests` clients.

### `trim.py`

`trim_card(raw_card: dict) -> dict` keeps only:

- Always: `id`, `name`, `type`, `race`, `desc`
- If present on the raw card: `atk`, `def`, `level`, `attribute`, `scale`, `linkval`, `linkmarkers`, `archetype`

Everything else:
- `frameType`,
- `ygoprodeck_url`,
- `card_sets`,
- `card_images`,
- `card_prices`,
- `banlist_info`,
is dropped. 

None of these serve an in-duel evaluator; they're deck-building/pricing/rendering concerns. This **may** change in later iterations. Probs likely we'll place the images in the database (when it is migrated from pure json to that) eventually.

`type` is kept as the raw API string (e.g. `"Pendulum Effect Monster"`, `"XYZ Monster"`) and is **not** mapped onto this project's `CardType` enum here.

That mapping is deliberately deferred to the static-layer pass, where `Card` objects actually get constructed — this module's job is acquisition and trimming, not interpretation. 

One consequence though: a Field Spell is only distinguishable from other Spell/Trap subtypes by `race == "Field"` (its `type` is still `"Spell Card"`), so anything that reads `cards.json` needs to check `race`, not just `type`, to identify one.

### `pipeline.py`

- `read_card_pool(input_path) -> list[str]` — reads one card name per line. Blank lines and lines starting with `#` are ignored, so the pool file can carry comments for reference. Duplicate names are de-duplicated (first occurrence wins, order otherwise preserved).
- `write_cards_json(cards, output_path) -> None` — writes trimmed card data as indented JSON, creating any missing parent directories.
- `build_card_pool(input_path, output_path) -> list[str]` — runs the full pipeline and returns the list of requested names that had no match.

  Missing names are meant to be surfaced loudly (see [Usage](#usage) below), not swallowed. 

### `__main__.py`

Thin CLI wrapper around `build_card_pool`, defaulting to `backend/data/card_pool.example.txt` → `backend/data/cards.json`. See [Usage](#usage).

## Usage

### Command line

From the `backend/` directory:

```bash
python -m app.fetching --format <name of format>
```
Note, if you're on mac, you may need to use `python3` instead of `python`.

This reads `backend/data/card_pool.txt`, fetches and trims each card, and writes `backend/data/cards.json`.

The `--format` flag is there to specify exactly which format you want to add cards to, e.g. `Ryzeal_2024` for Ryzeal-Maliss 2024 format. It will automatically search for `data/Ryzeal_2024` folder, and `card_pool.txt` file within it.

The naming convention used is from [formatlibrary](https://formatlibrary.com/formats).

If any name in the input file had no match, they're printed to stderr and the process exits with status `1` (the JSON file is still written for whatever *did* match). An example would be:
```err
WARNING: <num of no matches> name(s) from backend/data/<format name>/card_pool.txt had no match:
  - <some incorrect card name>
Wrote cards to backend/data/cards.json
```

A clean run exits `0` and just prints where the file was written.

### Programmatically

```python
from app.fetching.pipeline import build_card_pool

missing = build_card_pool("backend/data/format/card_pool.txt", "backend/data/cards.json")
if missing:
    print(f"{len(missing)} card(s) had no match: {missing}")
```

Or, if you already have a list of names in memory rather than a pool file (e.g. building a pool programmatically instead of hand-curating a `.txt`):

```python
from app.fetching.client import fetch_cards
from app.fetching.trim import trim_cards
from app.fetching.pipeline import write_cards_json

raw = fetch_cards(["Ash Blossom & Joyous Spring", "Pot of Greed"])
write_cards_json(trim_cards(raw), "backend/data/cards.json")
```

### Editing the card pool

`backend/data/<format>/card_pool.txt` is a plain text file — one **exact** card name per line.

Lines starting with `#` and blank lines are ignored, so the pool can be organized with comments, e.g.:

```
# Staples
Ash Blossom & Joyous Spring

# Format-specific non-engine
Evenly Matched
```

## Testing

`backend/tests/fetching/` covers all three modules. The HTTP layer is always mocked (`urllib.request.urlopen` patched via `monkeypatch`).

The test suite never hits the real API, per YGOPRODeck's own guidance not to depend on live network calls for routine runs.

- `test_client.py` — single-batch fetch, multi-batch chunking (confirms batching actually triggers multiple requests for a 45-name pool), and the no-match-batch-doesn't-raise case.
- `test_trim.py` — one test per card shape (monster, spell, field spell, pendulum, xyz, link) against saved fixtures in `tests/fetching/fixtures/`, plus a dropped-fields sweep.
- `test_pipeline.py` — `read_card_pool`'s comment/blank-line/dedup handling, `write_cards_json` actually writing to disk (including creating missing parent directories), and a full `build_card_pool` round-trip with the network mocked but real file I/O against `tmp_path`
  — this is the test that most directly proves "fetch → trim → write a
  `.json` file" works end to end.

## Out of scope

- Converting `cards.json` into `Card`/`CardType` objects — static layer.
- `EffectTemplate`, `Format`, banlist data — static layer.
- Image fetching — against API guidance, and irrelevant to an evaluator
  that doesn't render card art.
- Card prices/sets — not evaluator-relevant.
- Any database — confirmed JSON-only (`docs/storage.md`).
- Caching/refreshing already-fetched cards — this is a one-shot
  "build the pool" tool; no diffing logic exists yet.
