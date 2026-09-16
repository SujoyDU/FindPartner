from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from db.models.media import Media


class MediaShare(Base):
    __tablename__ = "media_shares"
    __table_args__ = ({"comment": "Shareable links for a media item."},)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # media_id: FK to media.id, ON DELETE CASCADE (delete media -> delete its shares)
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Unique, URL-safe token used in shareable links.
    share_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # Optional expiration; NULL = never expires.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # MediaShare many ──── 1 Media
    media: Mapped[Media] = relationship("Media", back_populates="shares")
