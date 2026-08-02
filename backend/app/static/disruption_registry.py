from app.evaluator.DisruptionSource import DisruptionSource
from app.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory
from app.type_defs.type_zones import ZoneType
from app.type_defs.type_cards import Position

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
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={
      (ZoneType.HAND, Position.IN_HAND): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
  "Baronne de Fleur": DisruptionSource(
    card_name="Baronne de Fleur",
    category=DisruptionCategory.OMNI_NEGATE,
    opt_scope=OncePerTurnScope.HARD,
    disruption_by_zone={
      # Link Monster -- always face-up, never has a Defense Position/set state
      (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
  "Infernity Barrier": DisruptionSource(
    card_name="Infernity Barrier",
    category=DisruptionCategory.OMNI_NEGATE,
    opt_scope=OncePerTurnScope.SOFT,
    disruption_by_zone={
      (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
  "Dark Paladin": DisruptionSource(
      card_name="Dark Paladin",
      category=DisruptionCategory.SPELL_NEGATE,
      opt_scope=OncePerTurnScope.SOFT,
      disruption_by_zone={
        # Quick Effect isn't battle-position-dependent, so both ATK/DEF count
        (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
        (ZoneType.MONSTER, Position.FACE_UP_DEF): DisruptionType.ACTIVE_DISRUPTION,
        (ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
        (ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_DEF): DisruptionType.ACTIVE_DISRUPTION,
      },
    ),
  "Mirror Force": DisruptionSource(
    card_name="Mirror Force",
    category=DisruptionCategory.BOARD_BREAKER,
    opt_scope=OncePerTurnScope.SOFT,
    disruption_by_zone={
      (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
  "Mitsurugi Great Purification": DisruptionSource(
      card_name="Mitsurugi Great Purification",
      category=DisruptionCategory.OMNI_NEGATE,
      opt_scope=OncePerTurnScope.HARD,
      disruption_by_zone={
        (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
      },
    ),
  # Illustrative of the zone-absence case: Solemn Judgment is a real omni
  # negate, but a Trap Card can't be activated straight from HAND (it must
  # be Set first) -- so HAND is deliberately not a key here at all, not
  # even POTENTIAL_DISRUPTION. Sitting in hand, it's simply not a
  # disruption of any kind yet.
  "Solemn Judgment": DisruptionSource(
    card_name="Solemn Judgment",
    category=DisruptionCategory.OMNI_NEGATE,
    opt_scope=OncePerTurnScope.SOFT,
    disruption_by_zone={
      (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
    },
  ),
}
