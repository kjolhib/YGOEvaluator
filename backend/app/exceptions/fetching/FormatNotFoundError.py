class FormatNotFoundError(Exception):
  """
  Raised when no format folder is found at backend/data/.
  """
  def __init__(self, message: str = "Specified format folder is not found at backend/data."):
      super().__init__(message)