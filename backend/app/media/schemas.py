"""Pydantic schemas for the media API.

``MediaOut`` is the public response shape: it exposes safe metadata and the
share token (when the item is public). It never leaks the storage key or any
filesystem path.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaOut(BaseModel):
    id: UUID
    owner_id: UUID
    file_name: str
    # "image" | "video"
    media_type: str
    # e.g. "image/jpeg", "video/mp4"
    mime_type: Optional[str] = None
    file_size: int = 0
    is_public: bool = False
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaList(BaseModel):
    items: list[MediaOut]
    total: int

    model_config = ConfigDict(from_attributes=True)
