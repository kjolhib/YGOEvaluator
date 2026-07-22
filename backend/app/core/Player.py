from dataclasses import dataclass, field

from app.core.Zones import ZoneType, FieldZone, PileZone
from app.core.Card import CardInstance, CardType

from app.type_defs.type_cards import Position
from app.exceptions.actions.NotMainMonsterError import NotMainMonsterError
from app.exceptions.actions.NotToMonsterZoneError import NotToMonsterZoneError
from app.exceptions.actions.NotToSTZoneError import NotToSpellTrapZoneError
from app.exceptions.actions.NotSTCardError import NotSpellTrapCardError
from app.exceptions.actions.NotSettableCardError import NotSettableCardError
from app.exceptions.actions.NotToFieldZoneError import NotToFieldZoneError

@dataclass
class Player:
  """
  The player class, holds all information relating to a specifc player.
  """
  # turn-specific resources
  name: str
  life_points: int = 8000
  normal_summon_used: bool = False

  # individually-slotted zones: 5 mz, 5 s/t, 1 fz
  monster_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.MONSTER, capacity=1) for _ in range(5)
  ])
  spell_trap_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.SPELL_TRAP, capacity=1) for _ in range(5)
  ])
  field_spell_zones: list[FieldZone] = field(default_factory=lambda: [
    FieldZone(ZoneType.FIELD_SPELL, capacity=1) for _ in range(1)
  ])

  # Other zones
  hand: PileZone = field(default_factory=lambda: PileZone(ZoneType.HAND))
  deck: PileZone = field(default_factory=lambda: PileZone(ZoneType.DECK))
  extra_deck: PileZone = field(default_factory=lambda: PileZone(ZoneType.EXTRA_DECK))
  graveyard: PileZone = field(default_factory=lambda: PileZone(ZoneType.GRAVEYARD))
  banishment: PileZone = field(default_factory=lambda: PileZone(ZoneType.BANISHED))

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

  def get_open_zone(self, zone_type: ZoneType) -> FieldZone:
    """
    Resolves an open (non-full) `FieldZone` of the given `zone_type` on this player.

    This is the bridge between a `PlayerAction`, which refers to zones abstractly via
    `ZoneType` (e.g. "put this in a monster zone"), and the concrete `FieldZone`
    instance that `normal_summon`/`activate_card` actually mutate.

    Args:
      zone_type (ZoneType): the kind of field zone to look for (MONSTER, SPELL_TRAP, or FIELD_SPELL)

    Returns:
      FieldZone: the first open zone of that type

    Raises:
      ValueError: if `zone_type` isn't a field-zone kind this player has, or if none are open
    """
    zones_by_type: dict[ZoneType, list[FieldZone]] = {
      ZoneType.MONSTER: self.monster_zones,
      ZoneType.SPELL_TRAP: self.spell_trap_zones,
      ZoneType.FIELD_SPELL: self.field_spell_zones,
    }
    zones = zones_by_type.get(zone_type)
    if zones is None:
      raise ValueError(f"{zone_type.name} is not a field-zone type this player has slots for.")

    for zone in zones:
      if not zone.is_full():
        return zone

    raise ValueError(f"No open {zone_type.name} zone available.")
  
  def normal_summon(self, card_instance: CardInstance, zone: FieldZone) -> None:
    """
    Normal summons a monster from the hand to a specified zone, face-up attack position.
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

  def activate_st_card(self, card_instance: CardInstance, zone: FieldZone) -> None:
    """
    Activates a spell/trap card from the hand into a spell/trap zone, face-up.

    Args:
      card_instance (CardInstance): the card to activate
      zone (FieldZone): the target field zone 

    Returns:
      None
    """
    # TODO: Decide whether or not to move `activate` into the card instance instead. That way, it's easier to check conditions. 
    card_type = card_instance.card.card_type
    zone_type = zone.zone_type
    if zone_type is not ZoneType.SPELL_TRAP:
      raise NotToSpellTrapZoneError("You can only activate a spell/trap card into a spell/trap zone.")

    if card_type not in (CardType.SPELL, CardType.TRAP):
      raise NotSpellTrapCardError("You can only activate a spell or trap card.")

    # Card is a spell/trap, and you're trying to activate it into a spell/trap zone
    zone.add(card_instance)

    # activated spells/traps are placed face-up; a face-down set uses FACE_DOWN_ST, see set_card
    card_instance.current_position = Position.FACE_UP_ST
    print(f"Player {self.name} activated {card_instance}")

  def set_card(self, card_instance: CardInstance, zone: FieldZone) -> None:
    """
    Sets a card face-down from the hand.

    A main-deck monster is set face-down in defense position into a monster zone
    (and consumes this turn's normal summon, same as `normal_summon`). A spell/trap
    is set face-down into a spell/trap zone.

    Args:
      card_instance (CardInstance): the card to set
      zone (FieldZone): the target field zone

    Returns:
      None
    """
    card_type = card_instance.card.card_type
    zone_type = zone.zone_type

    match card_type:
      case CardType.MONSTER:
        if zone_type is not ZoneType.MONSTER:
          raise NotToMonsterZoneError("You can only set a monster into a main monster zone.")

        if self.normal_summon_used:
          print("Normal summon has already been used this turn.")
          return

        self.normal_summon_used = True
        zone.add(card_instance)
        card_instance.current_position = Position.FACE_DOWN_MONSTER
      case CardType.SPELL | CardType.TRAP:
        if zone_type is not ZoneType.SPELL_TRAP:
          raise NotToSpellTrapZoneError("You can only set a spell/trap card into a spell/trap zone.")

        zone.add(card_instance)
        card_instance.current_position = Position.FACE_DOWN_ST
      case CardType.FIELD_SPELL:
        if zone_type is not ZoneType.FIELD_SPELL:
          raise NotToFieldZoneError("You can only set a field spell to a field zone.")
        
        zone.add(card_instance)
        card_instance.current_position = Position.FACE_DOWN_ST
      case _:
        raise NotSettableCardError(f"The card type *{card_instance.card.card_type.name}* is not settable in the *{zone_type.name}* zone.")
    
    print(f"Player {self.name} set {card_instance}")
    return


