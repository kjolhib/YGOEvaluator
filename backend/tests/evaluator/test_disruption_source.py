"""
Tests for `lookup_disruption`: the static "which effects of this specific
CardInstance are currently live?" check, against both the real registry and
small custom ones. Also covers `DisruptionSource`'s constructor validation.
"""
import itertools

import pytest

from app.evaluator.disruption_source import DisruptionEffect, DisruptionSource, lookup_disruption
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


def _effect(label: str, *states: tuple[ZoneType, Position]) -> DisruptionEffect:
  """Minimal valid effect for tests that only care about labels and liveness states"""
  return DisruptionEffect(
    label=label,
    categories=[DisruptionCategory.FLOODGATE],
    opt_scope=OncePerTurnScope.SOFT,
    disruption_by_zone={state: DisruptionType.ACTIVE_DISRUPTION for state in states},
  )


########### MATCHES ###########

def test_lookup__registered_card_in_live_state_returns_its_effects():
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == GLOBAL_REGISTRY_BY_NAME["Solemn Judgment"].effects


def test_lookup__matches_on_name_only_not_card_type():
  # documents current behaviour: card_type plays no part in matching
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.EFFECT_MONSTER)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == GLOBAL_REGISTRY_BY_NAME["Solemn Judgment"].effects


def test_lookup__name_match_is_exact():
  ci = _instance("Solemn Judgement", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)  # sic

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == []


def test_lookup__multiple_effects():
  ci = _instance("Baronne de Fleur", ZoneType.MONSTER, Position.FACE_UP_ATK, CardType.SYNCHRO_MONSTER)
  assert len(lookup_disruption(ci, GLOBAL_REGISTRY)) == 2


def test_lookup__returns_every_effect_live_in_the_state_in_source_order():
  effect_a = _effect("A", (ZoneType.HAND, Position.IN_HAND))
  effect_b = _effect("B", (ZoneType.HAND, Position.IN_HAND), (ZoneType.MONSTER, Position.FACE_UP_ATK))
  registry = [DisruptionSource(card_name="Two Effects", effects=[effect_a, effect_b])]

  in_hand = _instance("Two Effects", ZoneType.HAND, Position.IN_HAND)
  on_field = _instance("Two Effects", ZoneType.MONSTER, Position.FACE_UP_ATK)

  assert lookup_disruption(in_hand, registry) == [effect_a, effect_b]
  assert lookup_disruption(on_field, registry) == [effect_b]


def test_lookup__an_effect_not_live_here_does_not_hide_the_others():
  # regression: one non-live effect must be skipped, not discard the whole result.
  # e.g. a set Mitsurugi Great Purification: its negate is live, its GY effect is not.
  set_effect = _effect("Set effect", (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST))
  gy_effect = _effect("GY effect", (ZoneType.GRAVEYARD, Position.IN_GY))
  registry = [DisruptionSource(card_name="Set And GY", effects=[set_effect, gy_effect])]

  assert lookup_disruption(_instance("Set And GY", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST), registry) == [set_effect]
  assert lookup_disruption(_instance("Set And GY", ZoneType.GRAVEYARD, Position.IN_GY), registry) == [gy_effect]


########### MISSES ###########

def test_lookup__unregistered_card_returns_empty_list():
  ci = _instance("Totally Generic Monster", ZoneType.MONSTER, Position.FACE_UP_ATK)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == []


def test_lookup__registered_card_in_wrong_zone_returns_empty_list():
  ci = _instance("Solemn Judgment", ZoneType.HAND, Position.IN_HAND, CardType.TRAP)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == []


def test_lookup__registered_card_in_right_zone_wrong_position_returns_empty_list():
  # a face-down monster Baronne is not live, even though she's in a monster zone
  ci = _instance("Baronne de Fleur", ZoneType.MONSTER, Position.FACE_DOWN_MONSTER, CardType.LINK_MONSTER)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == []


def test_lookup__flipped_up_trap_is_no_longer_live():
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_UP_ST, CardType.TRAP)

  assert lookup_disruption(ci, GLOBAL_REGISTRY) == []


########### REGISTRY AS ARGUMENT ###########

def test_lookup__empty_registry_returns_empty_list():
  ci = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)

  assert lookup_disruption(ci, []) == []


def test_lookup__only_consults_the_registry_it_is_given():
  custom = [
    DisruptionSource(
      card_name="Custom Card",
      effects=[_effect("Floodgate", (ZoneType.MONSTER, Position.FACE_UP_ATK))],
    ),
  ]
  custom_card = _instance("Custom Card", ZoneType.MONSTER, Position.FACE_UP_ATK)
  real_card = _instance("Solemn Judgment", ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST, CardType.TRAP)

  assert lookup_disruption(custom_card, custom) == custom[0].effects
  assert lookup_disruption(real_card, custom) == []
  assert lookup_disruption(custom_card, GLOBAL_REGISTRY) == []


########### CONSTRUCTOR VALIDATION ###########

def test_disruption_source__reject_empty_fields():
  with pytest.raises(ValueError):
    DisruptionSource(card_name="Empty Effect", effects=[])

  with pytest.raises(ValueError):
    DisruptionSource(card_name="", effects=[_effect("Floodgate", (ZoneType.MONSTER, Position.FACE_UP_ATK))])

  with pytest.raises(ValueError):
    # an effect with no live states is rejected by DisruptionEffect itself
    DisruptionSource(card_name="Empty Disruption Zone", effects=[
      DisruptionEffect(
        label="Floodgate",
        categories=[DisruptionCategory.FLOODGATE],
        opt_scope=OncePerTurnScope.SOFT,
        disruption_by_zone={},
      ),
    ])


########### EXHAUSTIVE: EVERY REAL ENTRY ###########

@pytest.mark.parametrize("source", GLOBAL_REGISTRY, ids=lambda s: s.card_name)
def test_lookup__matches_exactly_the_registered_states(source):
  # every (zone, position) combination: an effect is returned if and only if
  # that state is in its own disruption_by_zone
  for zone_type, position in itertools.product(ZoneType, Position):
    ci = _instance(source.card_name, zone_type, position)
    result = lookup_disruption(ci, GLOBAL_REGISTRY)

    expected = [effect for effect in source.effects if (zone_type, position) in effect.disruption_by_zone]
    assert result == expected, f"{source.card_name} in {zone_type.name}/{position.name}"
