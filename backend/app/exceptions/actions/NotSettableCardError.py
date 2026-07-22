from app.exceptions.CoreErrors import SoftError

class NotSettableCardError(SoftError):
  """
  Exception raised when a `PlayerAction` attempts to set a card whose `card_type`
  cannot be set face-down at all (i.e. not a main-deck monster, spell, or trap).

  I.e. this action can only be done on a monster, spell, or trap card.
  """
  def __init__(self, message: str = "This action can only be performed on a main-deck monster, spell, or trap card."):
    super().__init__(message)
