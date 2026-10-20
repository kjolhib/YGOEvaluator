from app.evaluator.disruption_source import DisruptionSource
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_cards import Position

# Maliss archetype cards.
ENTRIES: list[DisruptionSource] = [
  DisruptionSource(
    card_name="Mitsurugi Great Purification",
    category=[DisruptionCategory.OMNI_NEGATE],
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={
      (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
      (ZoneType.GRAVEYARD, Position.IN_GY): DisruptionType.POTENTIAL_DISRUPTION
    },
  ),
]
