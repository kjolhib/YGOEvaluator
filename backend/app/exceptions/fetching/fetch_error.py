class FetchError(Exception):
  """
  Raised when a request to the YGOPRODeck API fails in a way that isn't the normal "no cards matched" response (network error, malformed response body, etc.).
  """
  def __init__(self, message: str = "Fetching cards failed."):
      super().__init__(message)