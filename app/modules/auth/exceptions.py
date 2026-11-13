class AuthError(Exception):
    """Base exception for business errors in the auth module."""


class EmailAlreadyRegisteredError(AuthError):
    """Raised when the email is already registered"""
