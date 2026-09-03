class GroupError(Exception):
    """Base exception for business errors in the groups module."""


class GroupNotFoundError(GroupError):
    """Raised when the group does not exist or the user has no membership in it."""


class GroupAlreadyMemberError(GroupError):
    """Raised when trying to add a user who is already a member of the group."""


class GroupSelfTransferError(GroupError):
    """Raised when a user tries to transfer group ownership to themselves."""


class GroupOwnerMustTransferError(GroupError):
    """Raised when the owner tries to leave the group without transferring ownership first."""
