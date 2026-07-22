from app.exceptions.CoreErrors import SoftError

class NotToSpellTrapZoneError(SoftError):
  """
  Exception raised when a `PlayerAction` was attempted when it is only possible if the `to_zone` is into a spell/trap zone.

  I.e. activating a spell/trap card.
  """
  def __init__(self, message: str = "The target of this action can only be a spell/trap zone (not including field-zone)."):
    super().__init__(message)