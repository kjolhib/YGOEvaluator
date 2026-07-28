import json
from pathlib import Path

from app.fetching import client

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class _FakeResponse:
  """Minimal stand-in for the object `urllib.request.urlopen` returns --
  just enough to support `.read()` and use as a context manager."""

  def __init__(self, payload: dict):
    self._payload = payload

  def read(self) -> bytes:
    return json.dumps(self._payload).encode("utf-8")

  def __enter__(self) -> "_FakeResponse":
    return self

  def __exit__(self, *exc_info) -> bool:
    return False


def test_fetch_cards_single_batch(monkeypatch):
  captured_urls: list[str] = []

  def fake_urlopen(url):
    captured_urls.append(url)
    return _FakeResponse({
      "data": [{"id": 55144522, "name": "Pot of Greed", "type": "Spell Card"}]
    })

  monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)

  result = client.fetch_cards(["Pot of Greed"])

  assert len(captured_urls) == 1
  assert len(result) == 1
  assert result[0]["name"] == "Pot of Greed"


def test_fetch_cards_batches_large_pools(monkeypatch):
  names = [f"Card {i}" for i in range(45)]  # -> 3 batches at CHUNK_SIZE=20
  call_count = 0

  def fake_urlopen(url):
    nonlocal call_count
    call_count += 1
    return _FakeResponse({"data": []})

  monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)
  monkeypatch.setattr(client.time, "sleep", lambda seconds: None)  # skip real delay in tests

  client.fetch_cards(names)

  assert call_count == 3


def test_fetch_cards_handles_no_match_batch_without_raising(monkeypatch):
  def fake_urlopen(url):
    return _FakeResponse({"error": "No card matching your query was found."})

  monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)

  result = client.fetch_cards(["Totally Not A Real Card"])

  assert result == []
