from app.evaluator.DisruptionSource import DisruptionSource
from app.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.type_defs.type_zones import ZoneType

# Hand-curated disruption registry.
#
# This is data, not logic -- deliberately kept as a plain dict literal so
# it stays easy to hand-extend, same spirit/scale as `card_pool.txt`. A
# starter list, not exhaustive; category/type/scope assignments here are
# illustrative and meant to be refined by hand as the format's actual known
# disruptions get filled in (see `_docs/workflow.md`'s "Data Storage" and
# "Core Design Principle: Format Scoping" sections).
#
# Keyed by card name -- see `DisruptionSource.card_name`'s docstring context
# in `_docs/plan/_evaluator_plan.md` for why name (not a synthetic ID) is
# the stable key here.
DISRUPTION_REGISTRY: dict[str, DisruptionSource] = {
  "Ash Blossom & Joyous Spring": DisruptionSource(
    card_name="Ash Blossom & Joyous Spring",
    category=DisruptionCategory.HANDTRAP,
    disruption_type=DisruptionType.ACTIVE_DISRUPTION,
    opt_scope=OncePerTurnScope.HARD,
    valid_zones=frozenset({ZoneType.HAND}),
  ),
  "Baronne de Fleur": DisruptionSource(
    card_name="Baronne de Fleur",
    category=DisruptionCategory.OMNI_NEGATE,
    disruption_type=DisruptionType.ACTIVE_DISRUPTION,
    opt_scope=OncePerTurnScope.HARD,
    valid_zones=frozenset({ZoneType.MONSTER}),
  ),
  "Infernity Barrier": DisruptionSource(
    card_name="Infernity Barrier",
    category=DisruptionCategory.OMNI_NEGATE,
    disruption_type=DisruptionType.ACTIVE_DISRUPTION,
    opt_scope=OncePerTurnScope.SOFT,
    valid_zones=frozenset({ZoneType.SPELL_TRAP}),
  ),
  "Mirror Force": DisruptionSource(
    card_name="Mirror Force",
    category=DisruptionCategory.BOARD_BREAKER,
    disruption_type=DisruptionType.POTENTIAL_DISRUPTION,
    opt_scope=OncePerTurnScope.SOFT,
    valid_zones=frozenset({ZoneType.SPELL_TRAP}),
  ),
}
