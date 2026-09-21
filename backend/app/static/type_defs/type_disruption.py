from enum import Enum, auto

class DisruptionType(Enum):
  """
  Enum classifying how "live" a disruption is, right now, on the board.

  E.g. Baronne already on board is an `ACTIVE_DISRUPTION`; Cupsy Yummy Way
  is a `POTENTIAL_DISRUPTION` (it's several plays away from actually
  disrupting, but this project doesn't trace those plays -- see
  `_docs/workflow.md`'s Evaluation Layer section).
  """
  ACTIVE_DISRUPTION = auto()
  POTENTIAL_DISRUPTION = auto()

class OncePerTurnScope(Enum):
  """
  Enum classifying whether a card's once-per-turn restriction is by name
  `HARD`, `SOFT`, `MIXED`. Mixed is reserved for those cards whose effects 
  have mixed opt scope. So the evaluator treats it as a separate filter.

  E.g. Baronne de Fleur is `HARD` opt. however many copies are visible, they
  collapse to at most one usable effect this turn. Infernity Barrier is
  `SOFT`. each copy is independently live.
  """
  HARD = auto()
  SOFT = auto()
  MIXED = auto()

class DisruptionCategory(Enum):
  """
  Enum tagging *what kind* of disruption a `DisruptionSource` represents.

  A starter, hand-extendable set -- deliberately a flat enum field on
  `DisruptionSource` rather than a class hierarchy (no
  `OmniNegate(DisruptionSource)` subclass), matching the flat-enum-over-
  inheritance pattern already used for `CardType`/`ZoneType`/`TurnPhase` in
  this project. Grouping by category (e.g. "all omni negates") is a plain
  membership check against this enum, not a subclass check.
  """
  OMNI_NEGATE = auto()
  SPELL_NEGATE = auto()
  TRAP_NEGATE = auto()
  SPELL_TRAP_NEGATE = auto()
  MONSTER_NEGATE = auto()
  TARGETED_REMOVAL = auto()
  HANDTRAP = auto()
  FLOODGATE = auto()
  BOARD_BREAKER = auto()
  EXTENDER = auto()
