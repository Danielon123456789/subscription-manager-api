class InvitationError(Exception):
    """Base exception for business errors in the invitations module."""


class InvitationNotFoundError(InvitationError):
    """Raised when the invitation does not exist"""


class InvitationAlreadyUsedError(InvitationError):
    """Raised when the invitation was already used"""


class InvitationAlreadyExpiredError(InvitationError):
    """Raised when the invitation has expired"""
