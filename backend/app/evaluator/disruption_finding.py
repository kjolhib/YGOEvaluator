from __future__ import annotations
from dataclasses import dataclass

from app.core.Player import Player
from backend.app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory

@dataclass(frozen=True)
class DisruptionFinding:
  """
  One disruption `BoardEvaluator.evaluate` found on a `BoardState` snapshot.

  Keyed by card name, not `CardInstance` -- per-instance identity isn't
  needed for this pass (see `_docs/plan/_evaluator_plan.md`).

  For `SOFT`-scope cards, one `DisruptionFinding` is emitted per instance
  (`instance_count = 1` each); for `HARD`-scope cards, one `DisruptionFinding`
  is emitted per card name with `instance_count` set to however many copies
  were found, since a hard once-per-turn restriction collapses all copies
  to a single usable effect this turn regardless of count. This keeps
  `len(findings)` meaningful as "how many independent things are live"
  without a caller needing to special-case `opt_scope`.
  """
  owner: Player
  card_name: str
  category: DisruptionCategory
  disruption_type: DisruptionType
  opt_scope: OncePerTurnScope
  instance_count: int
