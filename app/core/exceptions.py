class InsufficientPermissionError(Exception):
    """Raised when the user is identified but their role is not sufficient for the action."""
