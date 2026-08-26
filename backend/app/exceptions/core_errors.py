
class CoreError(BaseException):
  def __init__(self, message: str, extra_info: str):
    self.message: str = message
    self.extra_info: str = extra_info

class SoftError(CoreError):
  """
  A child of `CoreError`. Soft errors are propagated to the frontend, and aren't errors that crash the program.

  These handle illegal actions, and act more as tooltips for the user if they aren't allowed to do something.
  """
  def __init__(self, message: str):
    super().__init__(message, "")

class HardError(CoreError):
  """
  A child of `CoreError`. Hard errors are due to genuine bugs, uncaught exceptions, etc.

  These handle illegal states of the program, and generally used for development and usually never interacts with the user.
  """
  def __init__(self, message: str, extra_info: str):
    super().__init__(message, extra_info)
