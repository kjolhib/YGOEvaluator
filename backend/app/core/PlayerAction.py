from __future__ import annotations
from dataclasses import dataclass

from app.core.Player import Player
from app.core.Card import CardInstance
from app.type_defs.type_player_action import PlayerActions
from app.type_defs.type_zones import ZoneType

@dataclass
class PlayerAction:
  """
  The actions a player can take.

  `to_zone`/`from_zone` are `ZoneType`, not `Zone` instances: a `PlayerAction`
  describes intent abstractly (e.g. "move this card into a monster zone"),
  not a specific slot. `BoardState.handle_player_action` resolves the actual
  `FieldZone` to mutate via `Player.get_open_zone`.
  """
  action: PlayerActions
  player: Player
  to_zone: ZoneType
  from_zone: ZoneType
  card: CardInstance
