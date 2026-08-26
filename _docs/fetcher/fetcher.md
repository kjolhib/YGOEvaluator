# YGOEvaluator — Fetcher

status: [done]
last updated: [22-08-2026]

Implements the fetching/storage pipeline described in `docs/fetching_data.md` and `docs/storage.md`.
This is infrastructure only — it produces trimmed JSON, not `Card`/`CardType` Python objects. Converting `cards.json` into `Card` instances is the static-layer pass, not this one. See [Out of Scope](#out-of-scope)

Note that I believe it is possible to use [ygoapi](https://github.com/TimMikeladze/ygoapi) to fetch instead of hand writing it, but that is written for Typescript, and I haven't looked into it. It might just be a **lot** easier down the line.

## What it does

Cards are scoped **per format**: each format folder under `backend/data/` owns its own hand-curated pool and its own `cards.json`. There is no single shared database file — a format's `cards.json` only ever contains cards that format's `card_pool.txt` has requested.

Given a format name, the fetcher:

1. Loads that format's existing `cards.json`, if one already exists (`load_existing_cards`).
2. Reads that format's `card_pool.txt` (`read_card_pool`), skipping any name already present in the existing `cards.json` — by default, a card already on file is never re-fetched.
3. Fetches whatever's left from the YGOPRODeck API, batched into as *few* requests as possible (`fetch_cards`).
4. Trims each raw API response down to the fields this project cares about (`trim_cards`). This **will likely** be expanded in the future.
5. Merges the freshly fetched cards into the existing set (new entries win on a name collision) and writes the result back to that format's `cards.json` (`write_cards_json`).
6. Reports back any requested names that had no match, or any other issues found.

All of this is tied together by `build_card_pool(card_pool_path, output_path, force_fetch=False)`, which is what both the CLI and any calling code should normally use.

Yu-Gi-Oh erratas are rare enough, and vary enough in shape, that automatically diffing "did this card's stats change" isn't worth building. Instead, a stored card is trusted as-is unless you explicitly ask otherwise — see [`--force-fetch`](#command-line).

## Module layout

```
backend/app/fetching/
  client.py     fetch_cards(names) -> list[dict]        (network layer)
  trim.py       trim_card(raw) / trim_cards(raws) -> dict/list[dict]
  pipeline.py   load_existing_cards, read_card_pool, write_cards_json, build_card_pool
  __main__.py   CLI entry point (`python -m app.fetching`)

backend/app/exceptions/fetching/
  FetchError.py             non-network-layer failures during a fetch (see client.py)
  FormatNotFoundError.py    raised when --format doesn't match an existing folder under data/
  UnspecifiedFormatError.py defined, but not currently raised anywhere -- argparse's
                             required=True on --format already covers the "no format given" case

backend/data/
  <format name>/card_pool.txt   input: one exact card name per line (hand-curated, committed)
  <format name>/cards.json      output: trimmed card data for that format (generated)
  example_data/                 a real, committed example of the above pair -- carved out of
                                 .gitignore specifically so it's available as a stable fixture;
                                 every other <format name>/ folder's cards.json is gitignored
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

- Always: `id`, `name`, `type`, `race`, `archetype`, `desc`
- If present on the raw card: `atk`, `def`, `level`, `attribute`, `scale`, `linkval`, `linkmarkers`

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

- `load_existing_cards(output_path) -> dict[str, dict]` — loads a format's existing `cards.json` (if present; returns `{}` if not) and keys it by card `name` for lookup. If the file already contains two entries with the same name (only possible via a hand-edit or external tool — the pipeline's own merge can't produce this, since a dict can't hold duplicate keys), the later one wins and a warning is printed.
- `read_card_pool(card_pool_path, existing_cards, force_fetch) -> list[str]` — reads one card name per line. Blank lines and comments are ignored — both full-line (`# ...`) and inline (`Card Name # note`); everything from the first `#` onward on a line is stripped before the name is taken. Duplicate names within the file are de-duplicated (first occurrence wins, order otherwise preserved). Unless `force_fetch` is `True`, any name already present in `existing_cards` is also skipped, so a card already on file is never re-requested from the API.
- `write_cards_json(cards, output_path) -> None` — writes card data as indented JSON, creating any missing parent directories.
- `build_card_pool(card_pool_path, output_path, force_fetch=False) -> list[str]` — runs the full pipeline: loads existing cards, resolves which names actually need fetching (per the `force_fetch` rule above), fetches + trims those, merges the result into the existing set (newly fetched entries win on a name collision — this is how `--force-fetch` achieves an overwrite), writes the merged set back, and returns the list of requested names that had no match.

  Missing names are meant to be surfaced loudly (see [Usage](#usage) below), not swallowed. 

### `__main__.py`

CLI wrapper around `build_card_pool`. `--format <name>` is **required** — there is no default pool or fallback format; the CLI resolves it to `backend/data/<name>/card_pool.txt` and `backend/data/<name>/cards.json`, raising `FormatNotFoundError` if `backend/data/<name>/` doesn't exist. `--force-fetch` is optional and maps to `build_card_pool`'s `force_fetch` argument. See [Usage](#usage).

## Usage

### Command line

From the `backend/` directory:

```bash
python -m app.fetching --format <name of format>
```
Note, if you're on mac, you may need to use `python3` instead of `python`.

This reads `backend/data/<format>/card_pool.txt`, fetches and trims whatever isn't already in `backend/data/<format>/cards.json`, and writes the merged result back to that same `cards.json`.

The `--format` flag specifies exactly which format you want to add cards to, e.g. `Ryzeal_2024` for Ryzeal-Maliss 2024 format. It automatically searches for the `data/Ryzeal_2024` folder and the `card_pool.txt` file within it.

The naming convention used is from [formatlibrary](https://formatlibrary.com/formats).

Add `--force-fetch` to bypass the skip-if-already-fetched behavior entirely and re-fetch every name in the pool, overwriting whatever's currently stored for each. This is meant for the rare case where a card's data has actually changed since it was fetched (e.g. an errata) — since that's uncommon and shows up in all kinds of shapes, there's no automatic diffing; `--force-fetch` is a deliberate, manual "go check again" rather than something that runs by default:

```bash
python -m app.fetching --format Ryzeal_2024 --force-fetch
```

If any name in the input file had no match, they're printed to stderr and the process exits with status `1` (the JSON file is still written for whatever *did* match). An example would be:
```err
WARNING: <num of no matches> name(s) from <format name> had no match:
  - <some incorrect card name>
Wrote cards to data/<format name>/cards.json
```

A clean run exits `0` and just prints where the file was written.

### Programmatically

```python
from app.fetching.pipeline import build_card_pool

missing = build_card_pool("backend/data/Ryzeal_2024/card_pool.txt", "backend/data/Ryzeal_2024/cards.json")
if missing:
    print(f"{len(missing)} card(s) had no match: {missing}")
```

Pass `force_fetch=True` as a third argument to bypass the skip-existing behavior:

```python
missing = build_card_pool(
    "backend/data/Ryzeal_2024/card_pool.txt",
    "backend/data/Ryzeal_2024/cards.json",
    force_fetch=True,
)
```

Or, if you already have a list of names in memory rather than a pool file (e.g. building a pool programmatically instead of hand-curating a `.txt`):

```python
from app.fetching.client import fetch_cards
from app.fetching.trim import trim_cards
from app.fetching.pipeline import write_cards_json

raw = fetch_cards(["Ash Blossom & Joyous Spring", "Pot of Greed"])
write_cards_json(trim_cards(raw), "backend/data/Ryzeal_2024/cards.json")
```

Note this bypasses `load_existing_cards`/merging entirely — it'll overwrite the target file with only these cards, not merge them in. Reach for `build_card_pool` unless you specifically want that.

### Editing the card pool

`backend/data/<format>/card_pool.txt` is a plain text file — one **exact** card name per line.

Lines starting with `#` are ignored, and so is anything after a `#` on an otherwise valid line, so the pool can be organized with comments either as their own line or trailing a name, e.g.:

```
# Staples
Ash Blossom & Joyous Spring # near-universal hand trap

# Format-specific non-engine
Evenly Matched
```

## Testing

`backend/tests/fetching/` covers all four modules (including the CLI). The HTTP layer is always mocked (`urllib.request.urlopen` patched via `monkeypatch`).

The test suite never hits the real API, per YGOPRODeck's own guidance not to depend on live network calls for routine runs.

- `test_client.py` — single-batch fetch, multi-batch chunking (confirms batching actually triggers multiple requests for a 45-name pool), and the no-match-batch-doesn't-raise case.
- `test_trim.py` — one test per card shape (monster, spell, field spell, pendulum, xyz, link) against saved fixtures in `tests/fetching/fixtures/`, plus a dropped-fields sweep.
- `test_pipeline.py` — `read_card_pool`'s comment/blank-line/dedup handling (including inline comment stripping), `load_existing_cards`'s name-keying and duplicate-name warning, `write_cards_json` actually writing to disk (including creating missing parent directories), and several `build_card_pool` round-trips with the network mocked but real file I/O against `tmp_path`: a plain fetch, the skip-already-fetched-by-default case (two calls against the same `cards.json`, only the newly added name should hit the mocked network), and `force_fetch=True` re-fetching everything.
- `test_main.py` — CLI-level: resolving `--format` to the right folder when multiple format folders exist, raising `FormatNotFoundError` (with no side effects) when the named format doesn't exist, and `--force-fetch` reaching `build_card_pool` correctly.

## Out of scope

- Converting `cards.json` into `Card`/`CardType` objects — static layer.
- `EffectTemplate`, `Format`, banlist data — static layer.
- Image fetching — against API guidance, and irrelevant to an evaluator
  that doesn't render card art.
- Card prices/sets — not evaluator-relevant.
- Any database — confirmed JSON-only (`docs/storage.md`).
- Automatic field-level diffing of already-fetched cards against the live API response. `--force-fetch` will re-fetch and fully overwrite a stored entry on request, but there's no "check if anything actually changed" step — given how rare and irregularly-shaped erratas are, that's treated as a deliberate manual action, not something worth automating.
