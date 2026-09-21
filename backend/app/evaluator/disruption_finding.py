from __future__ import annotations
from dataclasses import dataclass

from app.core.player import Player
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory

@dataclass(frozen=True)
class DisruptionFinding:
  """
  One disruption `BoardEvaluator.evaluate` found on any given `BoardState`.

  Identified by card name.

  For `SOFT`-scope cards, one `DisruptionFinding` is emitted per instance (`instance_count = 1` each).
  
  For `HARD`-scope cards, one `DisruptionFinding` is emitted per card name with `instance_count` set to however many copies were found. 
  This is because a hard once-per-turn restriction collapses all copies to a single usable effect this turn regardless of count. 
  This keeps `len(findings)` meaningful as "how many independent things are live" without a caller needing to special-case `opt_scope`.
  """
  owner: Player
  card_name: str
  category: DisruptionCategory
  disruption_type: DisruptionType
  opt_scope: OncePerTurnScope
  instance_count: int
