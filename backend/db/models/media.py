from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from db.models.media_share import MediaShare
    from db.models.user import User


class Media(Base):
    __tablename__ = "media"
    __table_args__ = ({"comment": "A user's uploaded image or video file."},)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # owner_id: FK to users.id, ON DELETE CASCADE (delete user -> delete their media)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Opaque server-chosen storage key (never a client-supplied path).
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    # "image" | "video"
    media_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # e.g. image/jpeg, video/mp4
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # File size in bytes.
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default=text("0"))
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(tz=None).astimezone().replace(tzinfo=None),
    )

    # Relationships
    owner: Mapped[User] = relationship("User", back_populates="media")
    # Media 1 ──── many MediaShare (a media item can have multiple share links)
    shares: Mapped[list[MediaShare]] = relationship(
        "MediaShare",
        back_populates="media",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
