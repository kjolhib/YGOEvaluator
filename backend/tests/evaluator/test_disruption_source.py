"""
Tests for `lookup_disruption`: the static "is this specific CardInstance a
live, registered disruption?" check, against both the real registry and
small custom ones.
"""
import itertools

import pytest

from app.evaluator.disruption_source import DisruptionSource, lookup_disruption
from app.static.registry import GLOBAL_REGISTRY, GLOBAL_REGISTRY_BY_NAME
from app.static.type_defs.card import Card, CardInstance
from app.static.type_defs.type_cards import CardType, Position
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_disruption import DisruptionCategory, DisruptionType, OncePerTurnScope


def _instance(
  name: str,
  zone_type: ZoneType,
  position: Position,
  card_type: CardType = CardType.EFFECT_MONSTER,
) -> CardInstance:
  # `card.id` is irrelevant: matching is by name only
  return CardInstance(Card(id=0, name=name, card_type=card_type), position, zone_type)


########### MATCHES ###########

def test_lookup__registered_card_in_live_state_returns_its_entry():
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is GLOBAL_REGISTRY_BY_NAME["Solemn Judgment"]


def test_lookup__matches_on_name_only_not_card_type():
  # documents current behaviour: card_type plays no part in matching
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.EFFECT_MONSTER)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is GLOBAL_REGISTRY_BY_NAME["Solemn Judgment"]


def test_lookup__name_match_is_exact():
  ci = _instance("Solemn Judgement", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)  # sic

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is None


########### MISSES ###########

def test_lookup__unregistered_card_returns_none():
  ci = _instance("Totally Generic Monster", ZoneType.MONSTER, Position.FACE_UP_ATK)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is None


def test_lookup__registered_card_in_wrong_zone_returns_none():
  ci = _instance("Solemn Judgment", ZoneType.HAND, Position.IN_HAND, CardType.TRAP)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is None


def test_lookup__registered_card_in_right_zone_wrong_position_returns_none():
  # a face-down monster Baronne is not live, even though she's in a monster zone
  ci = _instance("Baronne de Fleur", ZoneType.MONSTER, Position.FACE_DOWN_MONSTER, CardType.LINK_MONSTER)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is None


def test_lookup__flipped_up_trap_is_no_longer_live():
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_UP_ST, CardType.TRAP)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) is None


########### REGISTRY ARGUMENT ###########

def test_lookup__empty_registry_returns_none():
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)

  assert lookup_disruption(ci, []) is None


def test_lookup__only_consults_the_registry_it_is_given():
  custom = [
    DisruptionSource(
      card_name="Custom Card",
      category=[DisruptionCategory.FLOODGATE],
      opt_scope=OncePerTurnScope.SOFT,
      disruption_by_zone={(ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION},
    ),
  ]
  custom_card = _instance("Custom Card", ZoneType.MONSTER, Position.FACE_UP_ATK)
  real_card = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)

  assert lookup_disruption(custom_card, custom) is custom[0]
  assert lookup_disruption(real_card, custom) is None
  assert lookup_disruption(custom_card, GLOBAL_REGISTRY) is None


########### EXHAUSTIVE: EVERY REAL ENTRY ###########

@pytest.mark.parametrize("source", GLOBAL_REGISTRY, ids=lambda s: s.card_name)
def test_lookup__matches_exactly_the_registered_states(source):
  # every (zone, position) combination: found if and only if it's in disruption_by_zone
  for zone_type, position in itertools.product(ZoneType, Position):
    ci = _instance(source.card_name, zone_type, position)
    result = lookup_disruption(ci, GLOBAL_REGISTRY)

    if (zone_type, position) in source.disruption_by_zone:
      assert result is source, f"{source.card_name} should be live in {zone_type.name}/{position.name}"
    else:
      assert result is None, f"{source.card_name} should NOT be live in {zone_type.name}/{position.name}"
