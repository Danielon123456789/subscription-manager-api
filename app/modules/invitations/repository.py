from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.invitation import Invitation, StatusInvitation


def get_invitation_by_token(db: Session, token: str) -> Invitation | None:
    stmt = select(Invitation).where(
        Invitation.token == token,
    )
    result = db.execute(stmt).scalar_one_or_none()
    return result


def create_invitation(db: Session, invitation: Invitation) -> Invitation:
    db.add(invitation)
    db.flush()
    return invitation


def update_invitation_status(
    db: Session, invitation: Invitation, status: StatusInvitation
) -> Invitation:
    invitation.status = status
    db.flush()
    return invitation
