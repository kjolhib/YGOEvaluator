from app.exceptions.CoreErrors import SoftError

class NotToMonsterZoneError(SoftError):
  """
  Exception raised when a `PlayerAction` was attempted when it is only possible if the `to_zone` is into a monster zone.

  I.e. this action cannot be done into a non-monster zone.
  """
  def __init__(self, message: str = "The target of this action can only be a monster zone (not extra monster zone)."):
    super().__init__(message)