from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    github_connected: bool
    github_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
