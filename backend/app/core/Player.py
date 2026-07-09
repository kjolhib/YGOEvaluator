from dataclasses import dataclass, field

from core.Zones import ZoneType, FieldZone, PileZone
from core.Card import CardInstance

@dataclass
class Player:
  name: str
  life_points: int = 8000

  # individually-slotted zones: 5 mz, 5 s/t, 1 fz
  monster_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.MONSTER, capacity=1) for _ in range(5)
  ])
  spell_trap_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.SPELL_TRAP, capacity=1) for _ in range(5)
  ])
  field_spell_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.FIELD_SPELL, capacity=1) for _ in range(2)
  ])

  # Other zones
  hand: PileZone = field(default_factory=lambda: PileZone(ZoneType.HAND))
  deck: PileZone = field(default_factory=lambda: PileZone(ZoneType.DECK))
  extra_deck: PileZone = field(default_factory=lambda: PileZone(ZoneType.EXTRA_DECK))
  graveyard: PileZone = field(default_factory=lambda: PileZone(ZoneType.GRAVEYARD))
  banished: PileZone = field(default_factory=lambda: PileZone(ZoneType.BANISHED))

  # turn-specific resources
  normal_summon_used: bool = False

  def all_monsters(self) -> list[CardInstance]:
    """
    Returns:
      - `list[CardInstance]`: a list of all monsters in the player's monster zone
    """
    return [card for zone in self.monster_zones for card in zone.cards]

  def all_spells_traps(self) -> list[CardInstance]:
    """
    Returns:
      - `list[CardInstance]`: a list of all spells/traps in the player's S/T zone
    """
    return [card for zone in self.spell_trap_zones for card in zone.cards]
  
  def turn_player_normal_summoned(self) -> bool:
    return self.normal_summon_used
  
  def normal_summon(self) -> None:
    self.normal_summon_used = True
