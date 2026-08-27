class FormatNotFoundError(Exception):
  """
  Raised when no format folder is found at backend/data/.

  Different to `UnspecifiedFormatError`, where a format wasa speicfied but it was not found.
  """
  def __init__(self, message: str = "Specified format folder is not found at backend/data."):
      super().__init__(message)