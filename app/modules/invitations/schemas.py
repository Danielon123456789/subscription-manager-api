from pydantic import BaseModel
from datetime import datetime
from app.models.invitation import StatusInvitation


class InvitationCreate(BaseModel):
    email: str


class InvitationResponse(BaseModel):
    id: int
    group_id: int
    status: StatusInvitation
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
