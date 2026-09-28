from pydantic import BaseModel


class UserSummaryResponse(BaseModel):
    total: int


class GroupSummaryResponse(BaseModel):
    total: int
    members: int
