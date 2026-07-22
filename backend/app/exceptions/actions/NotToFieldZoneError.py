from app.exceptions.CoreErrors import SoftError

class NotToFieldZoneError(SoftError):
  """
  Exception raised when a `PlayerAction` attempts to set a card whose `card_type` cannot be set face-down in a field zone. 

  I.e. This exception is only raised when a non-field spell is attempted to be set in a field zone.
  """
  def __init__(self, message: str = "You can only set a field spell in the field zone."):
    super().__init__(message)
