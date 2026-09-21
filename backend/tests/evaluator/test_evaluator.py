import pytest

from app.core.board_state import BoardState
from app.core.player import Player
from app.static.type_defs.card import Card, CardInstance

from app.static.type_defs.type_cards import CardType, Position
from app.static.type_defs.type_zones import ZoneType
from app.static.type_defs.type_disruption import DisruptionType, OncePerTurnScope, DisruptionCategory

from app.evaluator.disruption_source import DisruptionSource, lookup_disruption
from app.static.disruption_registry import DISRUPTION_REGISTRY
from app.evaluator.disruption_finding import DisruptionFinding
from app.evaluator.board_evaluator import evaluate


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

def _find_disruption_source(name: str) -> DisruptionSource:
  """
  Scans `DISRUPTION_REGISTRY` to find. the card name.

  Args:
    - name: the name to search for

  Returns:
    - DisruptionSource: if found, it returns its source disruption
  """
  return next(source for source in DISRUPTION_REGISTRY if source.card_name == name)

########### DISRUPTION_REGISTRY CONSTRUCTION ###########

def test_registry_entries_construct_correctly():
  for source in DISRUPTION_REGISTRY:
    assert isinstance(source, DisruptionSource)
    assert isinstance(source.category, list), "Disruption categories must be a list."
    assert all(isinstance(item, DisruptionCategory) for item in source.category), "An item in the disruption category is not of type DisruptionCategory."
    assert isinstance(source.opt_scope, OncePerTurnScope)
    assert isinstance(source.disruption_by_zone, dict)
    assert len(source.disruption_by_zone) > 0
    for state, disruption_type in source.disruption_by_zone.items():
      zone_type, position = state
      assert isinstance(zone_type, ZoneType)
      assert isinstance(position, Position)
      assert isinstance(disruption_type, DisruptionType)

    card_names = [source.card_name for source in DISRUPTION_REGISTRY]
    assert len(card_names) == len(set(card_names)), "duplicate card_name entries in DISRUPTION_REGISTRY"

def test_registry_opt_correctness():
  # Check once per turn 
  assert _find_disruption_source("Baronne de Fleur").opt_scope is OncePerTurnScope.HARD
  assert _find_disruption_source("Infernity Barrier").opt_scope is OncePerTurnScope.SOFT

def test_registry_pos_state_correctness():
  dr = [
    DisruptionSource(
      card_name="Solemn Judgment",
      category=[DisruptionCategory.OMNI_NEGATE],
      opt_scope=OncePerTurnScope.SOFT,
      disruption_by_zone={
        (ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST): DisruptionType.ACTIVE_DISRUPTION,
      },
    ),
  ]
  solemn_zones = {zone_type for zone_type, _position in dr[0].disruption_by_zone}
  assert ZoneType.HAND not in solemn_zones


########### BOARDEVALUATOR: HARD OPT ###########

def test_evaluate__monster_hard_opt_collapses_multiple_copies(board):
  # 2 copies of a monster hard-opt card on the same board should collapse to 1 finding
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


def test_evaluate__st_hard_opt_collapses_multiple_copies(board):
  # 2 copies of a spell/trap hard-opt card on the same board should collapse to 1 finding
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


def test_evaluate__face_down_baronne_is_not_active(board):
  # position matters, not just zone. Baronne's only live state is face up on the field.
  ci = _make_instance("Baronne de Fleur", CardType.SYNCHRO_MONSTER, ZoneType.MONSTER, Position.FACE_DOWN_MONSTER)
  board.player.monster_zones[0].add(ci)

  findings = evaluate(board)

  assert findings == []


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

########### BOARDEVALUATOR: MIXED OPT ###########
def test_evaluate__mixed_opt(board):
  # a card has multiple effects with different opt scopes while face-up atk
  custom_registry = [
      DisruptionSource(
        card_name="Combo Piece",
        category=[DisruptionCategory.EXTENDER],
        opt_scope=OncePerTurnScope.MIXED,
        disruption_by_zone={
          (ZoneType.HAND, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
          (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
        },
      ),
    ]
  ci_1 = _make_instance("Combo Piece", CardType.EFFECT_MONSTER, ZoneType.MONSTER, Position.FACE_UP_ATK)
  ci_2 = _make_instance("Combo Piece", CardType.EFFECT_MONSTER, ZoneType.MONSTER, Position.FACE_UP_ATK)
  board.player.monster_zones[0].add(ci_1)
  board.player.monster_zones[1].add(ci_2)
  findings = evaluate(board, registry=custom_registry)

  assert(len(findings) == 1) # mixed scopes should produce a single "mixed" finding. Tells us there's at most 1 hard opt finding
  assert(findings[0].opt_scope is OncePerTurnScope.MIXED) # this likely will require human curating on the card description, or just let the user read and understand themselves
  assert(findings[0].instance_count == 2) # 2 indepdent cards, overall telling us that there could be 2 soft opt effects


########### BOARDEVALUATOR: ZONE FILTERING ###########
# for example, wrong zone for the disruption to be registered

def test_evaluate__zone_outside_disruption_by_zone_produces_no_finding(board):
  # Ash Blossom's disruption_by_zone only has a HAND entry
  ci = _make_instance("Ash Blossom & Joyous Spring", CardType.EFFECT_MONSTER, ZoneType.GRAVEYARD, Position.IN_GY)
  board.player.graveyard.cards.append(ci)

  findings = evaluate(board)

  assert findings == []


########### BOARDEVALUATOR: ZONE ABSENCE ###########

def test_evaluate__solemn_Judgment_in_hand_produces_no_finding(board):
  ci = _make_instance("Solemn Judgment", CardType.TRAP, ZoneType.HAND, Position.IN_HAND)
  board.player.hand.cards.append(ci)

  findings = evaluate(board)

  assert findings == []


def test_evaluate__solemn_Judgment_set_produces_a_finding(board):
  ci = _make_instance("Solemn Judgment", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.player.spell_trap_zones[0].add(ci)

  findings = evaluate(board)

  assert len(findings) == 1
  assert findings[0].disruption_type is DisruptionType.ACTIVE_DISRUPTION


########### BOARDEVALUATOR: SAME CARD, DIFFERENT ZONE, DIFFERENT DISRUPTIONTYPE ###########

def test_evaluate__same_card_name_resolves_different_disruption_types_by_zone(board):
  # a hypothetical combo piece: POTENTIAL in hand (needs more plays to go live),
  # becomes ACTIVE once actually resolved onto the field. 
  custom_registry = [
    DisruptionSource(
      card_name="Combo Piece",
      category=[DisruptionCategory.EXTENDER],
      opt_scope=OncePerTurnScope.SOFT,
      disruption_by_zone={
        (ZoneType.HAND, Position.IN_HAND): DisruptionType.POTENTIAL_DISRUPTION,
        (ZoneType.MONSTER, Position.FACE_UP_ATK): DisruptionType.ACTIVE_DISRUPTION,
      },
    ),
  ]

  ci_in_hand = _make_instance("Combo Piece", CardType.EFFECT_MONSTER, ZoneType.HAND, Position.IN_HAND)
  ci_on_board = _make_instance("Combo Piece", CardType.EFFECT_MONSTER, ZoneType.MONSTER)
  board.player.hand.cards.append(ci_in_hand)
  board.player.monster_zones[0].add(ci_on_board)

  findings = evaluate(board, registry=custom_registry)

  # two separate findings here, 1 in hand, another on field
  assert len(findings) == 2
  types_found = {f.disruption_type for f in findings}
  assert types_found == {DisruptionType.POTENTIAL_DISRUPTION, DisruptionType.ACTIVE_DISRUPTION}
  assert all(f.instance_count == 1 for f in findings)  # SOFT scope, one copy each


########### BOARDEVALUATOR: EMZ ###########

def test_evaluate__emz_monster_is_scanned(board):
  # checks that emz is scanned
  ci = _make_instance("Baronne de Fleur", CardType.SYNCHRO_MONSTER, ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_ATK)
  board.extra_monster_zones[0].add(ci)

  findings = evaluate(board)

  assert len(findings) == 1
  assert findings[0].card_name == "Baronne de Fleur"


def test_evaluate__emz_finding_owner_matches_the_claimed_slot(board):
  # currently emz[0] (left) is fixed for user, and emz[1] (right) is opponent.
  # just makes life easier since we're not actually simulating a game, and i don't believe there's a case
  # currently (21/09/26) where left/right emz matters?
  ci_player = _make_instance("Baronne de Fleur", CardType.SYNCHRO_MONSTER, ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_ATK)
  ci_opponent = _make_instance("Dark Paladin", CardType.FUSION_MONSTER, ZoneType.EXTRA_MONSTER_ZONE, Position.FACE_UP_DEF)
  board.extra_monster_zones[0].add(ci_player)
  board.extra_monster_zones[1].add(ci_opponent)

  findings = evaluate(board)

  assert len(findings) == 2
  by_name = {f.card_name: f for f in findings}
  assert by_name["Baronne de Fleur"].owner is board.player
  assert by_name["Dark Paladin"].owner is board.opponent


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
  # something that may become something later on idk
  # mostly here to sketch what history would look like ig
  ci_hard = _make_instance("Baronne de Fleur", CardType.LINK_MONSTER, ZoneType.MONSTER)
  ci_soft = _make_instance("Infernity Barrier", CardType.TRAP, ZoneType.SPELL_TRAP, Position.FACE_DOWN_ST)
  board.player.monster_zones[0].add(ci_hard)
  board.player.spell_trap_zones[0].add(ci_soft)

  findings_without_history = evaluate(board)
  findings_with_history = evaluate(board, history={"whatever this ends up being"})

  assert findings_without_history == findings_with_history
