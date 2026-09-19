from __future__ import annotations
from typing import Any, Optional

from app.core.board_state import BoardState
from app.core.player import Player
from app.core.zones import Zone
from app.static.type_defs.card import CardInstance
from app.evaluator.disruption_source import DisruptionSource, lookup_disruption
from app.static.disruption_registry import DISRUPTION_REGISTRY
from app.evaluator.disruption_finding import DisruptionFinding
from app.static.type_defs.type_disruption import OncePerTurnScope, DisruptionType

# Zones scanned for disruptions.
# Deliberately excludes GY/banishment for now - too complex
_IN_SCOPE_ZONES = ("hand", "monster_zones", "spell_trap_zones", "field_spell_zones")


def _collect_instances(player: Player, owned_emz_zone: Optional[Zone] = None) -> list[CardInstance]:
  """
  Flattens every `CardInstance` out of a player's in-scope zones.

  Args
    player: the player to collect all card instances from.
    owned_emz_zone: the shared `board_state.extra_monster_zones` slot
      attributed to this player, if any (see `evaluate`'s docstring for
      why attribution is a fixed convention rather than real ownership
      tracking). Folded into the same flat list as the player's other
      zones -- not scanned separately -- so a hard-OPT card split between
      e.g. a `monster_zones` slot and this player's EMZ slot still
      collapses into one finding, same as any other pair of zones.

  Returns:
    list[CardInstance]: a list of all card instances, flattened.
  """
  instances: list[CardInstance] = []

  instances.extend(player.hand.cards)
  for zone_attr in ("monster_zones", "spell_trap_zones", "field_spell_zones"):
    for zone in getattr(player, zone_attr):
      instances.extend(zone.cards)

  if owned_emz_zone is not None:
    instances.extend(owned_emz_zone.cards)

  return instances

def _findings_for_player(
  player: Player,
  registry: list[DisruptionSource],
  owned_emz_zone: Optional[Zone] = None,
) -> list[DisruptionFinding]:
  """
  Scans one player's in-scope zones (including their attributed EMZ slot,
  if any) and produces their `DisruptionFinding`s.

  Args:
    player: the evaluation results of the player.
    registry: a list of disruption sources.
    owned_emz_zone: see `_collect_instances`.

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

  for card_instance in _collect_instances(player, owned_emz_zone):
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
  registry: list[DisruptionSource] = DISRUPTION_REGISTRY,
) -> list[DisruptionFinding]:
  """
  Scans a `BoardState` snapshot and returns every disruption found on either
  player's side (including the shared Extra Monster Zones), cross-referenced
  against `registry`.

  This is a pure lookup against hand-curated data (see `disruption_registry.py`).

  EMZ ownership: `board_state.extra_monster_zones` isn't a `Player`
  attribute, so it has no inherent owner to key a `DisruptionFinding` off
  of. Real EXTRA_MONSTER_ZONE rules let either player claim either
  physical slot at runtime (first monster placed into any EMZ claims it;
  the opponent is then restricted to whichever remains) -- that contested
  behaviour is deliberately NOT modelled. Instead this function attributes
  `extra_monster_zones[0]` to `board_state.player` and `[1]` to
  `board_state.opponent` as a fixed convention, purely for evaluation
  purposes. This has ~no practical impact today (which physical EMZ slot a
  monster sits in rarely matters), but revisit if/when the frontend needs
  the real contested-slot behaviour. Deliberately kept local to this
  function rather than tracked as state anywhere else (e.g. a generic
  `owner` field on `Zone`) -- the instance layer has no other reason to
  know about ownership, and bolting it on there would couple `Zone` to
  `Player` for the sake of this one case.

  Args:
    board_state (BoardState): the board snapshot to evaluate
    history (Any): reserved, unused. Per `_docs/workflow.md`'s
      extensibility requirement, this seam exists now so a future
      `History`/`GameLog` object can be introduced later without reworking
      this function's signature or call sites. Passing anything here has
      no effect yet.
    registry (list[DisruptionSource]): the disruption registry to
      check against. Defaults to `DISRUPTION_REGISTRY`; overridable for
      tests or a future per-format registry.

  Returns:
    list[DisruptionFinding]: every finding across both players, in
    (`board_state.player`'s findings) + (`board_state.opponent`'s findings)
    order. Exact ordering isn't load-bearing for this pass.
  """
  emz = board_state.extra_monster_zones
  findings: list[DisruptionFinding] = []
  findings.extend(_findings_for_player(board_state.player, registry, owned_emz_zone=emz[0]))
  findings.extend(_findings_for_player(board_state.opponent, registry, owned_emz_zone=emz[1]))
  return findings
