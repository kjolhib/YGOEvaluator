"""
Tests for the global disruption registry package (`app.static.registry`).

Four groups:
1. Every entry is well-formed (parametrized, so a failure names the card).
2. The package's wiring: concatenation, name index, duplicate detection.
3. The discovery machinery, run against a throwaway package folder.
4. Snapshots of hand-curated data, as a tripwire for accidental edits.
"""
import importlib
import sys

import pytest

import app.static.registry as registry_pkg
from app.static.registry import GLOBAL_REGISTRY, GLOBAL_REGISTRY_BY_NAME
from app.evaluator.disruption_source import DisruptionSource

from app.static.type_defs.type_cards import Position
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory


def _source(name: str) -> DisruptionSource:
  """
  Minimal valid entry for tests that only care about the name.
  """
  return DisruptionSource(
    card_name=name,
    category=[DisruptionCategory.HANDTRAP],
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={(ZoneType.HAND, Position.IN_HAND): DisruptionType.ACTIVE_DISRUPTION},
  )


########### 1. FILE WELL-FORMEDNESS ###########

def test_global_registry_is_not_empty():
  # guards against discovery silently finding nothing
  assert len(GLOBAL_REGISTRY) > 0


@pytest.mark.parametrize("source", GLOBAL_REGISTRY, ids=lambda s: s.card_name)
def test_entry_fields_have_correct_types(source):
  assert isinstance(source, DisruptionSource)
  assert isinstance(source.card_name, str)
  assert isinstance(source.category, list), "Disruption categories must be a list."
  assert all(isinstance(item, DisruptionCategory) for item in source.category)
  assert isinstance(source.opt_scope, OncePerTurnScope)
  assert isinstance(source.disruption_by_zone, dict)

  for (zone_type, position), disruption_type in source.disruption_by_zone.items():
    assert isinstance(zone_type, ZoneType)
    assert isinstance(position, Position)
    assert isinstance(disruption_type, DisruptionType)


@pytest.mark.parametrize("source", GLOBAL_REGISTRY, ids=lambda s: s.card_name)
def test_entry_card_name_is_clean(source):
  # lookups are exact string matches, ignoring whitespace
  assert source.card_name
  assert source.card_name == source.card_name.strip()


@pytest.mark.parametrize("source", GLOBAL_REGISTRY, ids=lambda s: s.card_name)
def test_entry_has_categories_without_duplicates(source):
  assert len(source.category) > 0, "every entry needs at least one category"
  assert len(set(source.category)) == len(source.category), "duplicate category"


@pytest.mark.parametrize("source", GLOBAL_REGISTRY, ids=lambda s: s.card_name)
def test_entry_has_at_least_one_live_state(source):
  assert len(source.disruption_by_zone) > 0


########### 2. PACKAGE WIRING ###########

def test_no_duplicate_card_names():
  names = [source.card_name for source in GLOBAL_REGISTRY]
  duplicates = {name for name in names if names.count(name) > 1}
  assert not duplicates, f"duplicate registry entries: {duplicates}"


def test_by_name_index_matches_the_list():
  assert len(GLOBAL_REGISTRY_BY_NAME) == len(GLOBAL_REGISTRY)
  for source in GLOBAL_REGISTRY:
    assert GLOBAL_REGISTRY_BY_NAME[source.card_name] is source


def test_every_submodule_defines_an_entries_list():
  for module in _import_real_submodules():
    assert isinstance(module.ENTRIES, list), f"{module.__name__}.ENTRIES must be a list"


def test_every_submodule_entry_is_in_the_global_registry():
  for module in _import_real_submodules():
    for entry in module.ENTRIES:
      assert any(entry is registered for registered in GLOBAL_REGISTRY), (
        f"{entry.card_name} from {module.__name__} is missing from GLOBAL_REGISTRY"
      )


def test_index_by_name_maps_each_name():
  entries = [_source("Card A"), _source("Card B")]

  by_name = registry_pkg._index_by_name(entries)

  assert set(by_name) == {"Card A", "Card B"}
  assert by_name["Card A"] is entries[0]


def test_index_by_name_rejects_duplicates():
  with pytest.raises(ValueError, match="Duplicate registry entry for 'Card A'"):
    registry_pkg._index_by_name([_source("Card A"), _source("Card A")])


def _import_real_submodules():
  import pkgutil
  return [
    importlib.import_module(f"{registry_pkg.__name__}.{info.name}")
    for info in pkgutil.iter_modules(registry_pkg.__path__)
    if not info.name.startswith("_")
  ]


########### 3. MODULE DISCOVERY ###########

_MODULE_TEMPLATE = '''
from app.evaluator.disruption_source import DisruptionSource
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_cards import Position

ENTRIES = [
  DisruptionSource(
    card_name="{name}",
    category=[DisruptionCategory.HANDTRAP],
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={{(ZoneType.HAND, Position.IN_HAND): DisruptionType.ACTIVE_DISRUPTION}},
  ),
]
'''


@pytest.fixture
def fake_registry(tmp_path, monkeypatch):
  """
  Points the registry package's discovery at an empty temp folder and
  returns a function for writing modules into it. Imported temp modules
  are removed from `sys.modules` afterwards so they can't leak into other tests.
  """
  monkeypatch.setattr(registry_pkg, "__path__", [str(tmp_path)])
  before = set(sys.modules)

  def write_module(filename: str, body: str) -> None:
    (tmp_path / filename).write_text(body, encoding="utf-8")
    importlib.invalidate_caches()

  yield write_module

  for name in set(sys.modules) - before:
    if name.startswith(f"{registry_pkg.__name__}."):
      del sys.modules[name]


def test_load_entries_empty_folder_returns_empty_list(fake_registry):
  assert registry_pkg._load_entries() == []


def test_load_entries_concatenates_every_module_in_name_order(fake_registry):
  fake_registry("b_second.py", _MODULE_TEMPLATE.format(name="Card B"))
  fake_registry("a_first.py", _MODULE_TEMPLATE.format(name="Card A"))

  entries = registry_pkg._load_entries()

  assert [entry.card_name for entry in entries] == ["Card A", "Card B"]


def test_load_entries_skips_underscore_modules(fake_registry):
  fake_registry("_helpers.py", 'raise RuntimeError("underscore modules must never be imported")')
  fake_registry("cards.py", _MODULE_TEMPLATE.format(name="Card A"))

  entries = registry_pkg._load_entries()

  assert [entry.card_name for entry in entries] == ["Card A"]


def test_load_entries_raises_when_a_module_has_no_entries(fake_registry):
  # e.g. a typo'd name: must be loud, since a default would silently drop cards
  fake_registry("typo.py", "ENTRY = []")

  with pytest.raises(AttributeError):
    registry_pkg._load_entries()


########### 4. CURATED DATA ###########

_EXPECTED_SCOPE_AND_CATEGORIES = {
  "Ash Blossom & Joyous Spring": (OncePerTurnScope.HARD, {DisruptionCategory.HANDTRAP}),
  "Baronne de Fleur": (OncePerTurnScope.HARD, {DisruptionCategory.OMNI_NEGATE, DisruptionCategory.TARGETED_REMOVAL}),
  "Mitsurugi Great Purification": (OncePerTurnScope.HARD, {DisruptionCategory.OMNI_NEGATE}),
  "Infernity Barrier": (OncePerTurnScope.SOFT, {DisruptionCategory.OMNI_NEGATE}),
  "Mirror Force": (OncePerTurnScope.SOFT, {DisruptionCategory.BOARD_BREAKER}),
  "Solemn Judgment": (OncePerTurnScope.SOFT, {DisruptionCategory.OMNI_NEGATE}),
  "Dark Paladin": (OncePerTurnScope.SOFT, {DisruptionCategory.SPELL_NEGATE}),
}


@pytest.mark.parametrize("name", _EXPECTED_SCOPE_AND_CATEGORIES)
def test_opt_scope_and_categories(name):
  expected_scope, expected_categories = _EXPECTED_SCOPE_AND_CATEGORIES[name]
  source = GLOBAL_REGISTRY_BY_NAME[name]

  assert source.opt_scope is expected_scope
  assert set(source.category) == expected_categories


@pytest.mark.parametrize("name", ["Solemn Judgment", "Mirror Force", "Infernity Barrier"])
def test_set_traps_are_only_live_face_down(name):
  # a trap that flipped face up (or is still in hand) is not a live disruption
  states = set(GLOBAL_REGISTRY_BY_NAME[name].disruption_by_zone)
  assert states == {(ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)}


def test_ash_blossom_is_only_live_in_hand():
  assert set(GLOBAL_REGISTRY_BY_NAME["Ash Blossom & Joyous Spring"].disruption_by_zone) == {
    (ZoneType.HAND, Position.IN_HAND)
  }


@pytest.mark.parametrize("name", ["Baronne de Fleur", "Dark Paladin"])
def test_extra_deck_monsters_are_active_face_up_in_monster_zone_and_emz(name):
  assert GLOBAL_REGISTRY_BY_NAME[name].disruption_by_zone == {
    (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
    (ZoneType.MONSTER, Position.FACE_UP_DEF): DisruptionType.ACTIVE_DISRUPTION,
    (ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
    (ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_DEF): DisruptionType.ACTIVE_DISRUPTION,
  }


def test_mitsurugi_is_active_when_set_and_potential_in_gy():
  assert GLOBAL_REGISTRY_BY_NAME["Mitsurugi Great Purification"].disruption_by_zone == {
    (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
    (ZoneType.GRAVEYARD, Position.IN_GY): DisruptionType.POTENTIAL_DISRUPTION,
  }
