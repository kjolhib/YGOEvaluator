from enum import Enum, auto

class Position(Enum):
  """
  Enum containing the position of a card.

  E.g. face up attack, def, face down monster/spell trap.
  """
  FACE_UP_ATK = auto()
  FACE_UP_DEF = auto()
  FACE_DOWN_MONSTER = auto()
  FACE_DOWN_ST = auto()
  FACE_UP_ST = auto()
  FACE_DOWN_BNSHED = auto()
  IN_HAND = auto()
  IN_DECK = auto()
  IN_GY = auto()
  IN_BNSHMT = auto()
  IN_ED = auto()

class CardType(Enum):
  """
  Enum containing the card typing, classified by summon mechanic.

  Pendulum is intentionally not represented as a distinct member: it is an
  orthogonal property rather than a summon mechanic. Cards can be e.g. an
  `EFFECT_MONSTER` and also pendulum, so the canonical pendulum signal is
  whether `scale` is present on the loaded card data (see `Card.is_pendulum`).
  """
  NORMAL_MONSTER = auto()
  EFFECT_MONSTER = auto()
  RITUAL_MONSTER = auto()
  FUSION_MONSTER = auto()
  SYNCHRO_MONSTER = auto()
  XYZ_MONSTER = auto()
  LINK_MONSTER = auto()
  SPELL = auto()
  TRAP = auto()
  FIELD_SPELL = auto()

MAIN_DECK_MONSTER_TYPES: frozenset[CardType] = frozenset({
  CardType.NORMAL_MONSTER,
  CardType.EFFECT_MONSTER,
  CardType.RITUAL_MONSTER,
})

EXTRA_DECK_MONSTER_TYPES: frozenset[CardType] = frozenset({
  CardType.FUSION_MONSTER,
  CardType.SYNCHRO_MONSTER,
  CardType.XYZ_MONSTER,
  CardType.LINK_MONSTER,
})

MONSTER_TYPES: frozenset[CardType] = MAIN_DECK_MONSTER_TYPES | EXTRA_DECK_MONSTER_TYPES


def map_card_type(raw_type: str, race: str) -> CardType:
  """
  Maps a raw YGOPRODeck `type` string (e.g. "Pendulum Effect Monster",
  "XYZ Monster", "Spell Card") onto this project's `CardType`.

  Keyword-matched rather than an exact lookup table, since the raw API
  combines multiple qualifiers into one string (e.g. "Pendulum Effect
  Monster" is Pendulum + Effect) -- this only extracts the summon-mechanic
  axis. More specific mechanics (Link/XYZ/Synchro/Fusion/Ritual) are
  checked before the generic "Monster" fallback so combinations like
  "Pendulum Effect Fusion Monster" resolve to the more specific type.

  `race` is required (not just `type`) because Field Spells are only
  distinguishable from other Spells via `race == "Field"` -- the raw
  `type` field alone is just `"Spell Card"` either way.

  Args:
    raw_type (str): the raw `type` field from a trimmed/raw YGOPRODeck card
    race (str): the raw `race` field from the same card

  Returns:
    CardType: the summon-mechanic (or Spell/Trap) classification

  Raises:
    ValueError: if `raw_type` doesn't match any known pattern (e.g. a
      Speed Duel "Skill Card", which is out of this project's format scope)
  """
  lowered = raw_type.lower()

  if "link" in lowered:
    return CardType.LINK_MONSTER
  if "xyz" in lowered:
    return CardType.XYZ_MONSTER
  if "synchro" in lowered:
    return CardType.SYNCHRO_MONSTER
  if "fusion" in lowered:
    return CardType.FUSION_MONSTER
  if "ritual" in lowered:
    return CardType.RITUAL_MONSTER
  if "normal monster" in lowered:
    return CardType.NORMAL_MONSTER
  if "monster" in lowered:
    # catches Effect/Flip Effect/Gemini/Spirit/Toon/Union/Pendulum Effect, etc.
    return CardType.EFFECT_MONSTER
  if "spell" in lowered:
    return CardType.FIELD_SPELL if race == "Field" else CardType.SPELL
  if "trap" in lowered:
    return CardType.TRAP

  raise ValueError(f"Unrecognized raw card type: {raw_type!r}")