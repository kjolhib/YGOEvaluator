"""
Tests for the CLI driver (app/fetching/__main__.py): format-folder resolution
and its failure mode. build_card_pool itself is mocked out here -- these
tests only care about *which paths* __main__ derives from --format, not
about fetching behavior (see test_pipeline.py for that).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.fetching import __main__ as fetch_main
from app.exceptions.fetching.FormatNotFoundError import FormatNotFoundError


def test_main_finds_correct_format_among_multiple(tmp_path: Path, monkeypatch):
  data_root = tmp_path / "data"
  (data_root / "FormatA").mkdir(parents=True)
  (data_root / "FormatA" / "card_pool.txt").write_text("Card A\n")
  (data_root / "FormatB").mkdir(parents=True)
  (data_root / "FormatB" / "card_pool.txt").write_text("Card B\n")

  # __main__ derives every path from this one module-level constant, so
  # repointing it sandboxes the whole CLI without touching the real data/ dir.
  monkeypatch.setattr(fetch_main, "_BACKEND_ROOT", tmp_path)

  captured = {}
  def fake_build_card_pool(card_pool_path, output_path, force_fetch=False):
    captured["card_pool_path"] = card_pool_path
    captured["output_path"] = output_path
    captured["force_fetch"] = force_fetch
    return []

  monkeypatch.setattr(fetch_main, "build_card_pool", fake_build_card_pool)

  exit_code = fetch_main.main(["--format", "FormatB"])

  assert exit_code == 0
  assert captured["card_pool_path"] == data_root / "FormatB" / "card_pool.txt"
  assert captured["output_path"] == data_root / "FormatB" / "cards.json"
  # confirms FormatA (the other sibling) was never touched
  assert "FormatA" not in str(captured["card_pool_path"])


def test_main_raises_when_format_does_not_exist(tmp_path: Path, monkeypatch):
  data_root = tmp_path / "data"
  data_root.mkdir()

  monkeypatch.setattr(fetch_main, "_BACKEND_ROOT", tmp_path)

  with pytest.raises(FormatNotFoundError):
    fetch_main.main(["--format", "GhostFormat"])


def test_main_does_not_create_format_folder_on_missing_format(tmp_path: Path, monkeypatch):
  data_root = tmp_path / "data"
  data_root.mkdir()

  monkeypatch.setattr(fetch_main, "_BACKEND_ROOT", tmp_path)

  missing_format_path = data_root / "GhostFormat"

  with pytest.raises(FormatNotFoundError):
    fetch_main.main(["--format", "GhostFormat"])

  # a failed lookup must not have side effects -- no folder should spring into existence
  assert not missing_format_path.exists()


def test_main_passes_force_fetch_flag_through(tmp_path: Path, monkeypatch):
  data_root = tmp_path / "data"
  (data_root / "SomeFormat").mkdir(parents=True)
  (data_root / "SomeFormat" / "card_pool.txt").write_text("Card A\n")

  monkeypatch.setattr(fetch_main, "_BACKEND_ROOT", tmp_path)

  captured = {}
  def fake_build_card_pool(card_pool_path, output_path, force_fetch=False):
    captured["force_fetch"] = force_fetch
    return []

  monkeypatch.setattr(fetch_main, "build_card_pool", fake_build_card_pool)

  fetch_main.main(["--format", "SomeFormat", "--force-fetch"])

  assert captured["force_fetch"] is True
