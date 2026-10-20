from app.evaluator.disruption_source import DisruptionSource
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_cards import Position

# Generic hand traps (Ash Blossom, Nibiru, Effect Veiler, ...).
ENTRIES: list[DisruptionSource] = [
  DisruptionSource(
    card_name="Ash Blossom & Joyous Spring",
    category=[DisruptionCategory.HANDTRAP],
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={
      (ZoneType.HAND, Position.IN_HAND): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
]
