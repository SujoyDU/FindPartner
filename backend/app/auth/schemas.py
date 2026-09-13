# ./backend/app/auth/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Pydantic schemas for authentication

class UserBase(BaseModel):
    username: str
    email: EmailStr
    # is_admin removed from base class as it should not be set during registration

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

