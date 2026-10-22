from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user


from app.modules.invitations import schemas
from app.modules.invitations import service
from app.modules.invitations import exceptions
from app.modules.groups.schemas import GroupMemberResponse

from app.core.exceptions import InsufficientPermissionError
from app.modules.groups.exceptions import GroupNotFoundError, GroupAlreadyMemberError


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/groups/{group_id}/invitations", status_code=201)
def group_invitation_create_endpoint(
    group_id: int,
    user_info: schemas.InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.InvitationResponse:
    try:
        new_invitation = service.create_invitation(
            db=db, email=user_info.email, inviter_id=current_user.id, group_id=group_id
        )

        return new_invitation

    except GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/invitations/{token}/accept", status_code=200)
def invitation_accept_endpoint(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    try:
        new_member = service.accept(db=db, token=token, user_id=current_user.id)
        return new_member
    except exceptions.InvitationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except exceptions.InvitationAlreadyExpiredError as e:
        raise HTTPException(status_code=410, detail=str(e)) from e
    except exceptions.InvitationAlreadyUsedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except GroupAlreadyMemberError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
