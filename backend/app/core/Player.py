from dataclasses import dataclass, field

from core.Zones import ZoneType, FieldZone, PileZone
from core.Card import CardInstance, CardType

from app.type_defs.type_cards import Position
from app.exceptions.actions.NotMainMonsterError import NotMainMonsterError
from app.exceptions.actions.NotToMonsterZoneError import NotToMonsterZoneError

@dataclass
class Player:
  """
  The player class, holds all information relating to a specifc player.
  """
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
  
  def normal_summon(self, card_instance: CardInstance, zone: FieldZone) -> None:
    """
    Normal summons a monster from the hand to a specified zone.

    CURRENTLY A STUB.
    """
    if self.normal_summon_used:
      print("Normal summon has already been used this turn.")
      return

    card_type = card_instance.card.card_type
    zone_type = zone.zone_type
    if zone_type is not ZoneType.MONSTER:
      raise NotToMonsterZoneError("You can only normal summon into a main monster zone.")
    
    if card_type is not CardType.MONSTER:
      raise NotMainMonsterError("You can only normal summon a main-deck monster.")
    
    self.normal_summon_used = True
    # Card is a monster, and you're trying to summon from the hand
    zone.add(card_instance)

    # set the position to be face up atk
    card_instance.current_position = Position.FACE_UP_ATK
    print(f"Player {self.name} normal summoned {card_instance}")

  def activate_card(self, card_instance: CardInstance, zone: FieldZone) -> None:
    """
    Activates a card.

    Currently just places the card in the zone.

    Args:
      card_instance (CardInstance): the card to activate
      zone (FieldZone): the target field zone 

    Returns:
      None
    """
    # TODO: Decide whether or not to move `activate` into the card instance instead. That way, it's easier to check conditions. 
    card_type = card_instance.card.card_type

