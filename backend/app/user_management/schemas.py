from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserUpdate(BaseModel):
    """Profile fields a user may change about THEMSELVES.

    Privileged fields (``is_active``, ``is_admin``) are intentionally NOT here;
    they can only be changed by an admin through the admin endpoints.
    """

    username: Optional[str] = Field(default=None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None


class UserDeactivate(BaseModel):
    is_active: bool


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserList(UserOut):
    pass


class UserRetrieve(UserOut):
    pass
