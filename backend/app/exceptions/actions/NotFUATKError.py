from app.exceptions.CoreErrors import SoftError

class NotFUATKError(SoftError):
  """
  Exception raised when a `PlayerAction` was attempted when it is only possible if the monster becomes in face-up atk position.

  I.e. normal summoning.
  """
  def __init__(self, message: str = "This action can only place a monster in face-up attack position."):
    super().__init__(message)