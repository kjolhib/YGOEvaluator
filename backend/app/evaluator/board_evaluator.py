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
      why attribution is fixed). 

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
  Scans one player's in-scope zones and produces their `DisruptionFinding`s.

  Args:
    player: the evaluation results of the player.
    registry: a list of disruption sources.
    owned_emz_zone: see `_collect_instances`.

  Returns:
    list[DisruptionFinding]: a list of findings regarding the identified disruptions.
  """
  # (card_name, resolved DisruptionType) -> (DisruptionSource, matched CardInstances)
  #
  # Keyed by (name, type), not just name: the same card name can resolve to a different DisruptionType depending on which (zone, position) a given copy is in (see DisruptionSource.disruption_by_zone). 
  # 
  # So, two copies of the same card in different states must not be merged into one ambiguous group.
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
      # usable effect this turn
      findings.append(DisruptionFinding(
        owner=player,
        card_name=card_name,
        category=source.category,
        disruption_type=disruption_type,
        opt_scope=source.opt_scope,
        instance_count=len(group),
      ))
    elif source.opt_scope is OncePerTurnScope.SOFT:
      # SOFT: each copy is independently live: one finding per instance.
      for _ in group:
        findings.append(DisruptionFinding(
          owner=player,
          card_name=card_name,
          category=source.category,
          disruption_type=disruption_type,
          opt_scope=source.opt_scope,
          instance_count=1,
        ))
    else:
      # Mixed, some cards may have a mix of hard opt effects with soft opt
      # Currently just derived as "mixed". May be extended in the future
      findings.append(DisruptionFinding(
        owner=player,
        card_name=card_name,
        category=source.category,
        disruption_type=disruption_type,
        opt_scope=source.opt_scope,
        instance_count=len(group) # a single finding for a mixed type, with instance count being the number of different independent cards on the field.
        # Since currently the evaluator cannot determine which effect is which scope, it's best to show that this disruption contains hard opt (hence only 1 finding, not appending a finding for each group), but also include the number of independent cards (hence this can give an indication of how many possible soft opt effects there are)
      ))

  return findings


def evaluate(
  board_state: BoardState,
  history: Any = None,
  registry: list[DisruptionSource] = DISRUPTION_REGISTRY,
) -> list[DisruptionFinding]:
  """
  Scans a given `BoardState` and returns every disruption found on either
  player's side. Disruptiosn are cross-referenced against `registry`.

  This is a pure lookup against hand-curated data (see `disruption_registry.py`).

  EMZ ownership: `board_state.extra_monster_zones` isn't a `Player` attribute, so it has no inherent owner to key a `DisruptionFinding` off of. 
  Real EXTRA_MONSTER_ZONE rules let either player claim either physical slot at runtime (first monster placed into any EMZ claims it; the opponent is then restricted to whichever remains). 
  
  Instead this function attributes `extra_monster_zones[0]` to `board_state.player` and `[1]` to
  `board_state.opponent` as a fixed convention, purely for evaluation
  purposes. 
  
  This has ~no real practical impact today (which physical EMZ slot a
  monster sits in rarely matters), but may need revisions if/when the frontend needs
  the real contested-slot behaviour. Deliberately kept local to this
  function rather than tracked as state anywhere else. An extensiond would be adding an "owner" field to Zone.

  Args:
    board_state (BoardState): the board snapshot to evaluate
    history (Any): reserved, unused. This exists now so a future
      `History`/`GameLog` object can be introduced later without reworking
      this function's signature or call sites. Passing anything here has
      **no** effect yet.
    registry (list[DisruptionSource]): the disruption registry to
      check against. Defaults to `DISRUPTION_REGISTRY`. overridable.

  Returns:
    list[DisruptionFinding]: every finding across both players, in (`board_state.player`'s findings) + (`board_state.opponent`'s findings) order.
  """
  emz = board_state.extra_monster_zones
  findings: list[DisruptionFinding] = []
  findings.extend(_findings_for_player(board_state.player, registry, owned_emz_zone=emz[0]))
  findings.extend(_findings_for_player(board_state.opponent, registry, owned_emz_zone=emz[1]))
  return findings
