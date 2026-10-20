from app.evaluator.disruption_source import DisruptionSource
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_cards import Position

# Generic extra deck (Baronne De Fleur, Crystal Wing, etc)
ENTRIES: list[DisruptionSource] = [
  DisruptionSource(
    card_name="Baronne de Fleur",
    category=[DisruptionCategory.OMNI_NEGATE, DisruptionCategory.TARGETED_REMOVAL],
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={
      (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
      (ZoneType.MONSTER, Position.FACE_UP_DEF): DisruptionType.ACTIVE_DISRUPTION,
      (ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_DEF): DisruptionType.ACTIVE_DISRUPTION,
      (ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
] 