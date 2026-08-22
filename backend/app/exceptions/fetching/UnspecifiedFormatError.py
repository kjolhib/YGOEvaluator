class UnspecifiedFormatError(Exception):
  """
  Raised when no format is specified. A folder must be specified, with ideally the name of the format.
  """
  def __init__(self, message: str = "Please specify a folder with the tag --format <folder name>. This folder should contain the card pool you want to add."):
      super().__init__(message)