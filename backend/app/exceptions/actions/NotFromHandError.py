from app.exceptions.CoreErrors import SoftError

class NotFromHandError(SoftError):
  """
  Exception raised when a `PlayerAction` was attempted when it is only possible if the `from_zone` is from the hand.

  I.e. this action cannot be done outside from the hand.
  """
  def __init__(self, message: str = "This action can only be done from the hand."):
    super().__init__(message)