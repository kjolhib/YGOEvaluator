from app.exceptions.CoreErrors import SoftError

class NotSpellTrapCardError(SoftError):
  """
  Exception raised when a `PlayerAction` was attempted when it is only possible if the card instance is a spell or trap card.

  I.e. this action can only be done on a spell or trap card.
  """
  def __init__(self, message: str = "This action can only be performed if the card is a spell or trap card."):
    super().__init__(message)
