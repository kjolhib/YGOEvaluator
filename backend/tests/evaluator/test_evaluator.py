import pytest

from app.core.BoardState import BoardState
from app.core.Player import Player
from app.static.Card import Card, CardInstance

from app.type_defs.type_cards import CardType, Position
from app.type_defs.type_zones import ZoneType
from app.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory

from app.evaluator.DisruptionSource import DisruptionSource, lookup_disruption
from app.static.disruption_registry import DISRUPTION_REGISTRY
from app.evaluator.DisruptionFinding import DisruptionFinding
from app.evaluator.BoardEvaluator import evaluate


@pytest.fixture
def board():
  return BoardState(Player("p1"), Player("p2"))


def _make_instance(
  name: str,
  card_type: CardType,
  zone_type: ZoneType,
  position: Position = Position.FACE_UP_ATK,
) -> CardInstance:
  """
  Builds a `CardInstance` for a given card name/type/zone.

  `card.id` is irrelevant to disruption matching (which is name-keyed), so it's not a parameter here.
  Keeps call sites focused on what actually matters for these tests.
  """
  card = Card(id=0, name=name, card_type=card_type)
  return CardInstance(card, position, zone_type)


########### DISRUPTION_REGISTRY SANITY ###########

def test_registry_entries_construct_correctly():
  # every entry's own card_name matches the key it's stored under
  for key, source in DISRUPTION_REGISTRY.items():
    assert isinstance(source, DisruptionSource)
    assert source.card_name == key
    assert isinstance(source.category, DisruptionCategory)
    assert isinstance(source.opt_scope, OncePerTurnScope)
    assert isinstance(source.disruption_by_zone, dict)
    assert len(source.disruption_by_zone) > 0
    for state, disruption_type in source.disruption_by_zone.items():
      zone_type, position = state
      assert isinstance(zone_type, ZoneType)
      assert isinstance(position, Position)
      assert isinstance(disruption_type, DisruptionType)

  # spot-check the two OPT scopes we rely on elsewhere in this file
  assert DISRUPTION_REGISTRY["Baronne de Fleur"].opt_scope is OncePerTurnScope.HARD
  assert DISRUPTION_REGISTRY["Infernity Barrier"].opt_scope is OncePerTurnScope.SOFT

  # Solemn Judgement: deliberately has no HAND state at all -- see the
  # "zone absence" tests below
  solemn_zones = {zone_type for zone_type, _position in DISRUPTION_REGISTRY["Solemn Judgment"].disruption_by_zone}
  assert ZoneType.HAND not in solemn_zones


########### BOARDEVALUATOR: HARD OPT ###########

def test_evaluate__monster_hard_opt_collapses_multiple_copies(board):
  # 2 copies of a HARD-OPT card on the same board should collapse to 1 finding
  ci_1 = _make_instance("Baronne de Fleur", CardType.SYNCHRO_MONSTER, ZoneType.MONSTER)
  ci_2 = _make_instance("Baronne de Fleur", CardType.SYNCHRO_MONSTER, ZoneType.MONSTER)
  board.player.monster_zones[0].add(ci_1)
  board.player.monster_zones[1].add(ci_2)

  findings = evaluate(board)

  assert len(findings) == 1
  finding = findings[0]
  assert finding.card_name == "Baronne de Fleur"
  assert finding.opt_scope is OncePerTurnScope.HARD
  assert finding.instance_count == 2
  assert finding.owner is board.player


def test_evaluate__face_down_baronne_is_not_active(board):
  # position matters, not just zone: Baronne de Fleur's only live state is
  # (MONSTER, FACE_UP_ATK). A face-down monster's effects don't apply --
  # sitting face-down in the same zone should produce nothing.
  ci = _make_instance("Baronne de Fleur", CardType.LINK_MONSTER, ZoneType.MONSTER, Position.FACE_DOWN_MONSTER)
  board.player.monster_zones[0].add(ci)

  findings = evaluate(board)

  assert findings == []


def test_evaluate__st_hard_opt_collapses_multiple_copies(board):
  # 2 copies of a HARD-OPT card on the same board should collapse to 1 finding
  ci_1 = _make_instance("Mitsurugi Great Purification", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  ci_2 = _make_instance("Mitsurugi Great Purification", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.player.spell_trap_zones[0].add(ci_1)
  board.player.spell_trap_zones[1].add(ci_2)

  findings = evaluate(board)

  assert len(findings) == 1
  finding = findings[0]
  assert finding.card_name == "Mitsurugi Great Purification"
  assert finding.opt_scope is OncePerTurnScope.HARD
  assert finding.instance_count == 2
  assert finding.owner is board.player



########### BOARDEVALUATOR: SOFT OPT ###########

def test_evaluate__st_soft_opt_emits_one_finding_per_copy(board):
  # 2 copies of a soft opt s/t
  ci_1 = _make_instance("Infernity Barrier", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  ci_2 = _make_instance("Infernity Barrier", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.player.spell_trap_zones[0].add(ci_1)
  board.player.spell_trap_zones[1].add(ci_2)

  findings = evaluate(board)

  assert len(findings) == 2
  assert all(f.card_name == "Infernity Barrier" for f in findings)
  assert all(f.opt_scope is OncePerTurnScope.SOFT for f in findings)
  assert all(f.instance_count == 1 for f in findings)


def test_evaluate__monster_soft_opt_emits_one_finding_per_copy(board):
  # 2 copies of a soft opt monster
  ci_1 = _make_instance("Dark Paladin", CardType.FUSION_MONSTER, ZoneType.MONSTER, Position.FACE_UP_DEF)
  ci_2 = _make_instance("Dark Paladin", CardType.FUSION_MONSTER, ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_ATK)
  board.player.monster_zones[0].add(ci_1)
  board.player.monster_zones[1].add(ci_2)

  findings = evaluate(board)

  assert len(findings) == 2
  assert all(f.card_name == "Dark Paladin" for f in findings)
  assert all(f.opt_scope is OncePerTurnScope.SOFT for f in findings)
  assert all(f.instance_count == 1 for f in findings)

########### BOARDEVALUATOR: ZONE FILTERING (registered card, wrong zone) ###########

def test_evaluate__zone_outside_disruption_by_zone_produces_no_finding(board):
  # Ash Blossom's disruption_by_zone only has a HAND entry -- sitting in the GY shouldn't count
  ci = _make_instance("Ash Blossom & Joyous Spring", CardType.EFFECT_MONSTER, ZoneType.GRAVEYARD, Position.IN_GY)
  board.player.graveyard.cards.append(ci)

  findings = evaluate(board)

  assert findings == []


########### BOARDEVALUATOR: ZONE ABSENCE (a real omni negate, wrong zone entirely) ###########

def test_evaluate__solemn_judgement_in_hand_produces_no_finding(board):
  # Solemn Judgement is a real omni negate, but Trap Cards can't be activated
  # straight from hand -- they must be Set first. Its registry entry has no
  # HAND key at all, so sitting in hand it isn't a disruption of any kind,
  # not even POTENTIAL_DISRUPTION.
  ci = _make_instance("Solemn Judgement", CardType.TRAP, ZoneType.HAND, Position.IN_HAND)
  board.player.hand.cards.append(ci)

  findings = evaluate(board)

  assert findings == []

def test_evaluate__solemn_judgement_set_produces_a_finding(board):
  # the same card, set into the spell/trap zone, IS live
  ci = _make_instance("Solemn Judgement", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.player.spell_trap_zones[0].add(ci)

  findings = evaluate(board)

  assert len(findings) == 1
  assert findings[0].disruption_type is DisruptionType.ACTIVE_DISRUPTION


########### BOARDEVALUATOR: SAME CARD, DIFFERENT ZONE, DIFFERENT DISRUPTIONTYPE ###########

def test_evaluate__same_card_name_resolves_different_disruption_types_by_zone(board):
  # a hypothetical combo piece: POTENTIAL in hand (needs more plays to go
  # live), ACTIVE once actually resolved onto the field. Uses a registry
  # override (evaluate's `registry` param) rather than the real starter
  # registry, since no current entry demonstrates this on its own.
  custom_registry = {
    "Combo Piece": DisruptionSource(
      card_name="Combo Piece",
      category=DisruptionCategory.EXTENDER,
      opt_scope=OncePerTurnScope.SOFT,
      disruption_by_zone={
        (ZoneType.HAND, Position.IN_HAND): DisruptionType.POTENTIAL_DISRUPTION,
        (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
      },
    ),
  }

  ci_in_hand = _make_instance("Combo Piece", CardType.EFFECT_MONSTER, ZoneType.HAND, Position.IN_HAND)
  ci_on_board = _make_instance("Combo Piece", CardType.EFFECT_MONSTER, ZoneType.MONSTER)
  board.player.hand.cards.append(ci_in_hand)
  board.player.monster_zones[0].add(ci_on_board)

  findings = evaluate(board, registry=custom_registry)

  # two separate findings -- NOT merged into one, since they represent
  # different DisruptionTypes despite sharing a card name
  assert len(findings) == 2
  types_found = {f.disruption_type for f in findings}
  assert types_found == {DisruptionType.POTENTIAL_DISRUPTION, DisruptionType.ACTIVE_DISRUPTION}
  assert all(f.instance_count == 1 for f in findings)  # SOFT scope, one copy each


########### BOARDEVALUATOR: CROSS-PLAYER TAGGING ###########

def test_evaluate__findings_tagged_to_correct_owner(board):
  # a set Mirror Force belongs to the opponent, not the turn player
  ci = _make_instance("Mirror Force", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.opponent.spell_trap_zones[0].add(ci)

  findings = evaluate(board)

  assert len(findings) == 1
  assert findings[0].owner is board.opponent
  assert findings[0].owner is not board.player


########### BOARDEVALUATOR: UNREGISTERED CARDS ###########

def test_evaluate__unregistered_card_produces_no_finding(board):
  ci = _make_instance("Totally Generic Monster", CardType.EFFECT_MONSTER, ZoneType.MONSTER)
  board.player.monster_zones[0].add(ci)

  findings = evaluate(board)

  assert findings == []


########### BOARDEVALUATOR: HISTORY SEAM ###########

def test_evaluate__history_param_is_a_no_op(board):
  ci_hard = _make_instance("Baronne de Fleur", CardType.LINK_MONSTER, ZoneType.MONSTER)
  ci_soft = _make_instance("Infernity Barrier", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.player.monster_zones[0].add(ci_hard)
  board.player.spell_trap_zones[0].add(ci_soft)

  findings_without_history = evaluate(board)
  findings_with_history = evaluate(board, history={"whatever": "this ends up being"})

  assert findings_without_history == findings_with_history
