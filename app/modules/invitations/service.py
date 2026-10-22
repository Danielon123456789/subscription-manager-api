from sqlalchemy.orm import Session
from app.modules.invitations import repository
from app.models.invitation import Invitation
from app.modules.invitations import exceptions
from app.modules.notifications.service import send_notification
from app.modules.groups.service import (
    validate_member,
    get_group,
    add_member_from_invitation,
)
from app.models.group_member import GroupRole, GroupMember
from app.modules.auth.repository import get_by_id
from datetime import datetime, timezone, timedelta
from app.models.invitation import StatusInvitation

import secrets


def create_invitation(
    db: Session, email: str, inviter_id: int, group_id: int
) -> Invitation:
    validate_member(db=db, group_id=group_id, user_id=inviter_id, role=GroupRole.OWNER)

    token = secrets.token_urlsafe()
    expires_at = datetime.now(timezone.utc) + timedelta(days=4)
    group = get_group(db=db, group_id=group_id, user_id=inviter_id)
    user = get_by_id(db=db, user_id=inviter_id)

    invitation = Invitation(
        token=token,
        email=email,
        inviter_id=inviter_id,
        group_id=group_id,
        expires_at=expires_at,
    )

    repository.create_invitation(db=db, invitation=invitation)
    db.commit()

    inviter_name = user.full_name or user.email
    send_notification(
        recipient_email=email,
        template_name="group_invitation.html",
        subject="Invitation",
        context={"group_name": group.name, "inviter_name": inviter_name},
    )
    return invitation


def accept(db: Session, token: str, user_id: int) -> GroupMember:
    invitation = repository.get_invitation_by_token(db=db, token=token)

    if invitation is None:
        raise exceptions.InvitationNotFoundError("Invitation not found")

    user_info = get_by_id(db=db, user_id=user_id)

    if invitation.email != user_info.email:
        raise exceptions.InvitationNotFoundError("Invitation email mismatch")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise exceptions.InvitationAlreadyExpiredError("Invitation has expired")

    if invitation.status != StatusInvitation.PENDING:
        raise exceptions.InvitationAlreadyUsedError("Invitation already used")

    add_user = add_member_from_invitation(
        db=db, group_id=invitation.group_id, new_member_id=user_id
    )

    repository.update_invitation_status(
        db=db, invitation=invitation, status=StatusInvitation.ACCEPTED
    )

    db.commit()

    return add_user
