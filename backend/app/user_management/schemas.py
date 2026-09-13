from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Base user schema (for internal use)
class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True

# Schema for creating a new user
class UserCreate(UserBase):
    password: str

# Schema for updating a user
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

# Schema for reading user data (response)
class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for listing users (admin view)
class UserList(UserOut):
    pass

# Schema for admin retrieving specific user
class UserRetrieve(UserOut):
    pass

# Schema for deactivating a user
class UserDeactivate(BaseModel):
    is_active: bool = False
