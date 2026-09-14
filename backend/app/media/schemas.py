from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MediaBase(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    is_public: bool = False
    share_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MediaCreate(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    is_public: bool = False

class MediaUpdate(BaseModel):
    is_public: bool = False

class MediaOut(MediaBase):
    id: int
    user_id: int

class MediaList(BaseModel):
    id: int
    file_name: str
    is_public: bool
    share_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True