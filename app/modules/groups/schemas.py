from pydantic import BaseModel
from datetime import datetime
from app.models.group_member import GroupRole


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class GroupChangeOwner(BaseModel):
    new_owner_id: int


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupMemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    role: GroupRole

    model_config = {"from_attributes": True}


class GroupByMemberResponse(GroupResponse):
    role: GroupRole
