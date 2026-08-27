class NoCardsJsonError(Exception):
  """
  Raised when there is no `cards.json` found.
  """
  def __init__(self, message: str = "No cards data found, please fetch cards data using the fetcher first."):
      super().__init__(message)