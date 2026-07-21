# Yu-Gi-Oh Decision Evaluator — Player Information & Data

## Attributes
### Player metadata:
- `name` (`str`): the name of the player
- `life_points` (`int`): the life points the player has remaining
- `normal_summon_used` (`bool`): whether or no this player has normal summoned this turn.

### Zone info:
- `monster_zones` (`list[FieldZone]`): the monster zones the player has. It is a list containing 5 field zones, with the type defaulted to `MONSTER` and capacity to 1.
- `spell_trap_zones` (`list[FieldZone]`): similar to `monster_zones` but for spell/trap cards.
- `field_spell_zones`: (`list[FieldZone]`): similar to `monster_zones`, but only with 1 zone.

### Zones with No Cap:
All attributes with the type `PileZone`, which means that they have no capacity and theoretically any number of cards can enter them.

Note, in relation to the `extra_deck`, this specifically talks about the case where cards are **added to** the extra deck such as via pendulum monsters.
- `hand` (`PileZone`)
- `deck` (`PileZone`)
- `extra_deck` (`PileZone`)
- `graveyard` (`PileZone`)
- `banishment` (`PileZone`)

## What it does
The `player` class simulates actions a real player makes in a duel. The class `BoardState` calls player specific actions whenever a user inputs an event.

Actions include:
- normal summoning
- special summoning
- activating/setting cards
and more.
