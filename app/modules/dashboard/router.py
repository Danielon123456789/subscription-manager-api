from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.dashboard.schemas import UserSummaryResponse, GroupSummaryResponse
from app.modules.dashboard import service
from app.modules.groups import exceptions

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/dashboard/summary", status_code=200)
def user_summary_endpoint(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> UserSummaryResponse:
    summary = service.get_user_summary(db=db, user_id=current_user.id)
    return UserSummaryResponse(total=summary)


@router.get("/dashboard/groups/{group_id}", status_code=200)
def group_summary_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupSummaryResponse:
    try:
        summary = service.get_group_summary(
            db=db, group_id=group_id, user_id=current_user.id
        )
        total, members_count = summary

        return GroupSummaryResponse(total=total, members=members_count)
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
