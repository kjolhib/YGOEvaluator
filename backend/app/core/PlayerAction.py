from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

from app.core.Player import Player
from app.core.Zones import Zone
from app.core.Card import CardInstance
from app.type_defs.type_player_action import Actions

class PlayerAction:
  action: Actions
  player: Player
  to_zone: Zone
  from_zone: Zone
  card: CardInstance
