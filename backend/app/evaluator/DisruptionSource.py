from __future__ import annotations
from dataclasses import dataclass

from app.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.type_defs.type_zones import ZoneType

@dataclass(frozen=True)
class DisruptionSource:
  """
  A single hand-curated registry entry: "this card, in these zones,
  represents a disruption."

  This is Evaluation-layer configuration, not derived from card text --
  consistent with this project's PSCT-is-intentionally-opaque principle
  (see `_docs/workflow.md`). Entries are hand-authored in
  `disruption_registry.py`, the same spirit/scale as `card_pool.txt`: a
  starter list meant to be hand-extended over time, not exhaustive.
  """
  card_name: str
  category: DisruptionCategory
  disruption_type: DisruptionType
  opt_scope: OncePerTurnScope
  valid_zones: frozenset[ZoneType]
