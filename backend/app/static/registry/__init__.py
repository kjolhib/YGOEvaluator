"""
Global disruption registry as a package. Each disruption `DisruptionSource` is split
across several modules by it's rough classification (hand traps, archetype etc). 

Function:
Every non-underscore module in this folder is expected to define a module-level
`ENTRIES: list[DisruptionSource]`. 
On import, this `__init__.py` finds every such module, concatenates their `ENTRIES`, and exposes the result as
`GLOBAL_REGISTRY` (list) and `GLOBAL_REGISTRY_BY_NAME` (dict). Helpers should be
prefixed using "_".

Adding a new group of cards = drop a new `.py` file in this folder with an
`ENTRIES` list. Nothing here should need editing.

A format's effective registry is derived elsewhere, by filtering this global registry against that format's `card_pool.txt`.
"""
from __future__ import annotations
import importlib
import pkgutil

from app.evaluator.disruption_source import DisruptionSource


def _load_entries() -> list[DisruptionSource]:
  """
  Imports every non-underscore submodule of this package and concatenates
  their `ENTRIES` lists.

  `pkgutil.iter_modules` yields modules in sorted name order, so the
  resulting list order is deterministic.

  Raises:
    AttributeError: if a submodule doesn't define strictly `ENTRIES`. 

  Returns:
    list[DisruptionSource]: every entry across every submodule.
  """
  entries: list[DisruptionSource] = []
  for module_info in pkgutil.iter_modules(__path__):
    if module_info.name.startswith("_"):
      continue
    module = importlib.import_module(f"{__name__}.{module_info.name}")
    entries.extend(module.ENTRIES)
  return entries


def _index_by_name(entries: list[DisruptionSource]) -> dict[str, DisruptionSource]:
  """
  Indexes entries by `card_name`, refusing duplicates.

  Raises:
    ValueError: if two entries share a `card_name`. `lookup_disruption`
      matches on name, so a duplicate would make one entry unreachable.

  Returns:
    dict[str, DisruptionSource]: card name -> its single registry entry.
  """
  by_name: dict[str, DisruptionSource] = {}
  for entry in entries:
    if entry.card_name in by_name:
      raise ValueError(f"Duplicate registry entry for '{entry.card_name}'")
    by_name[entry.card_name] = entry
  return by_name


GLOBAL_REGISTRY: list[DisruptionSource] = _load_entries()
GLOBAL_REGISTRY_BY_NAME: dict[str, DisruptionSource] = _index_by_name(GLOBAL_REGISTRY)
