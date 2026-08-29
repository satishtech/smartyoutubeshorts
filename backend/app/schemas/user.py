"""User schemas."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    is_active: bool
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
