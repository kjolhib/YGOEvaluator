from app.evaluator.disruption_source import DisruptionSource
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_cards import Position

# Infernity archetype cards.
ENTRIES: list[DisruptionSource] = [
  DisruptionSource(
    card_name="Infernity Barrier",
    category=[DisruptionCategory.OMNI_NEGATE],
    opt_scope=OncePerTurnScope.SOFT,
    disruption_by_zone={
      (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
]
