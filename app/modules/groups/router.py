from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.groups import service
from app.modules.groups.schemas import (
    GroupCreate,
    GroupAdd,
    GroupChangeOwner,
    GroupResponse,
    GroupUpdate,
    GroupMemberResponse,
)
from app.modules.groups import exceptions
from app.core.exceptions import InsufficientPermissionError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/groups", status_code=201)
def group_create_endpoint(
    group_info: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    new_group = service.create_group(
        db=db, user_id=current_user.id, group_info=group_info
    )
    return new_group


@router.get("/groups/{group_id}", status_code=200)
def groups_by_id_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    try:
        group = service.get_group(db=db, group_id=group_id, user_id=current_user.id)
        return group
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/groups/{group_id}", status_code=200)
def groups_update_endpoint(
    group_info: GroupUpdate,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    try:
        group_updated = service.update_group(
            db=db, group_id=group_id, user_id=current_user.id, group_info=group_info
        )
        return group_updated
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/groups/{group_id}/invite", status_code=201)
def groups_add_member_endpoint(
    group_id: int,
    member_info: GroupAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    try:
        new_member = service.add_member(
            db=db,
            group_id=group_id,
            user_id=current_user.id,
            new_member_id=member_info.new_member_id,
        )
        return new_member
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except exceptions.GroupAlreadyMemberError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/groups/{group_id}/transfer-owner", status_code=200)
def groups_change_owner_endpoint(
    member_info: GroupChangeOwner,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupMemberResponse:
    try:
        new_owner = service.transfer_owner(
            db=db,
            group_id=group_id,
            user_id=current_user.id,
            new_member_owner_id=member_info.new_owner_id,
        )
        return new_owner
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except exceptions.GroupSelfTransferError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/groups/{group_id}/leave", status_code=200)
def groups_leave_member_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        service.remove_member(
            db=db,
            group_id=group_id,
            user_id=current_user.id,
            user_remove_id=current_user.id,
        )
        return None
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except exceptions.GroupOwnerMustTransferError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/groups/{group_id}/members/{member_id}", status_code=200)
def groups_delete_member_endpoint(
    group_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        service.remove_member(
            db=db, group_id=group_id, user_id=current_user.id, user_remove_id=member_id
        )
        return None
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except exceptions.GroupOwnerMustTransferError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/groups/{group_id}", status_code=200)
def groups_delete_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        service.delete_group(db=db, group_id=group_id, user_id=current_user.id)
        return None
    except exceptions.GroupNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except exceptions.GroupOwnerMustTransferError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
