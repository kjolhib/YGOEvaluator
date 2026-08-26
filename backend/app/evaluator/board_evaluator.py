from __future__ import annotations
from typing import Any

from backend.app.core.board_state import BoardState
from app.core.player import Player
from app.static.card import CardInstance
from backend.app.evaluator.disruption_source import DisruptionSource, lookup_disruption
from app.static.disruption_registry import DISRUPTION_REGISTRY
from backend.app.evaluator.disruption_finding import DisruptionFinding
from backend.app.static.type_defs.type_disruption import OncePerTurnScope, DisruptionType

# Zones scanned for disruptions.
# Deliberately excludes GY/banishment for now - too complex
_IN_SCOPE_ZONES = ("hand", "monster_zones", "spell_trap_zones", "field_spell_zones")


def _collect_instances(player: Player) -> list[CardInstance]:
  """
  Flattens every `CardInstance` out of a player's in-scope zones.

  Args
    player: the player to collect all card instances from.

  Returns:
    list[CardInstance]: a list of all card instances, flattened.
  """
  instances: list[CardInstance] = []

  instances.extend(player.hand.cards)
  for zone_attr in ("monster_zones", "spell_trap_zones", "field_spell_zones"):
    for zone in getattr(player, zone_attr):
      instances.extend(zone.cards)

  return instances

def _findings_for_player(
  player: Player,
  registry: dict[str, DisruptionSource],
) -> list[DisruptionFinding]:
  """
  Scans one player's in-scope zones and produces their `DisruptionFinding`s.

  Args:
    player: the evaluation results of the player.
    registry: a dictionary mapping of names to disruption source.

  Returns:
    list[DisruptionFinding]: a list of findings regarding the identified disruptions.
  """
  # (card_name, resolved DisruptionType) -> (DisruptionSource, matched CardInstances)
  #
  # Keyed by (name, type), not just name: the same card name can resolve to
  # a different DisruptionType depending on which (zone, position) a given
  # copy is in (see DisruptionSource.disruption_by_zone), so two copies of
  # the same card in different states must not be merged into one
  # ambiguous group.
  matches: dict[tuple[str, DisruptionType], tuple[DisruptionSource, list[CardInstance]]] = {}

  for card_instance in _collect_instances(player):
    source = lookup_disruption(card_instance, registry)
    if source is None:
      continue

    disruption_type = source.disruption_by_zone[(card_instance.current_zone_type, card_instance.current_position)]
    key = (source.card_name, disruption_type)
    _, group = matches.setdefault(key, (source, []))
    group.append(card_instance)

  findings: list[DisruptionFinding] = []
  for (card_name, disruption_type), (source, group) in matches.items():
    if source.opt_scope is OncePerTurnScope.HARD:
      # However many copies, a hard OPT restriction collapses them to one
      # usable effect this turn -- one finding, count carried for context.
      findings.append(DisruptionFinding(
        owner=player,
        card_name=card_name,
        category=source.category,
        disruption_type=disruption_type,
        opt_scope=source.opt_scope,
        instance_count=len(group),
      ))
    else:
      # SOFT: each copy is independently live -- one finding per instance.
      for _ in group:
        findings.append(DisruptionFinding(
          owner=player,
          card_name=card_name,
          category=source.category,
          disruption_type=disruption_type,
          opt_scope=source.opt_scope,
          instance_count=1,
        ))

  return findings


def evaluate(
  board_state: BoardState,
  history: Any = None,
  registry: dict[str, DisruptionSource] = DISRUPTION_REGISTRY,
) -> list[DisruptionFinding]:
  """
  Scans a `BoardState` snapshot and returns every disruption found on either player's side, cross-referenced against `registry`.

  This is a pure lookup against hand-curated data (see `disruption_registry.py`).
  
  No card-text parsing, no judgement about how threatening a finding is, no synthesis across findings. See `_docs/plan/_evaluator_plan.md` for the full scope of this pass.

  Args:
    board_state (BoardState): the board snapshot to evaluate
    history (Any): reserved, unused. Per `_docs/workflow.md`'s
      extensibility requirement, this seam exists now so a future
      `History`/`GameLog` object can be introduced later without reworking
      this function's signature or call sites. Passing anything here has
      no effect yet.
    registry (dict[str, DisruptionSource]): the disruption registry to
      check against. Defaults to `DISRUPTION_REGISTRY`; overridable for
      tests or a future per-format registry.

  Returns:
    list[DisruptionFinding]: every finding across both players, in
    (`board_state.player`'s findings) + (`board_state.opponent`'s findings)
    order. Exact ordering isn't load-bearing for this pass.
  """
  findings: list[DisruptionFinding] = []
  findings.extend(_findings_for_player(board_state.player, registry))
  findings.extend(_findings_for_player(board_state.opponent, registry))
  return findings
