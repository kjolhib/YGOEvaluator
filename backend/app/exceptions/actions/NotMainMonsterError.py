from app.exceptions.CoreErrors import SoftError

class NotMainMonsterError(SoftError):
  """
  Exception raised when a `PlayerAction` was attempted when it is only possible if the card instance is a main deck monster.

  I.e. this action can only be done on a main deck monster.
  """
  def __init__(self, message: str = "This action can only be performed if the card is a main deck monster."):
    super().__init__(message)