from pydantic import BaseModel


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
