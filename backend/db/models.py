from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    media = relationship(
        "Media",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Media(Base):
    __tablename__ = "media"
    __table_args__ = (
        UniqueConstraint("share_token", name="uq_media_share_token"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    # Server-chosen opaque storage key (random uuid + sanitized suffix). Never
    # a client-supplied path.
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "image" | "video"
    content_type = Column(String, nullable=True)  # e.g. image/jpeg, video/mp4
    is_public = Column(Boolean, default=False, nullable=False)
    share_token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="media")
