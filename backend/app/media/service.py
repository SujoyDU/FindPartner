"""Media business logic.

Postgres stores *metadata only* (this service's ``Media``/``MediaShare`` rows);
the actual bytes live on the storage backend (local disk by default). Reads of
file bytes always go through ``storage.open()`` and are streamed to the client
-- they are never persisted in the database.

Ownership (BOLA / IDOR) model
-----------------------------
Every owner-scoped operation is hard-scoped to the owner's UUID. A media row
owned by someone else -- or absent -- is indistinguishable to the caller and
uniformly returns 404, so resource IDs are not enumerable. Public access is
exclusively via the unguessable share token (``MediaShare.share_token``), which
is what a shareable link contains.
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.models import Media, MediaShare
from app.media.storage_service import StorageBackend

# 32 chars over 62 symbols ~= 190 bits of entropy (far beyond brute-forcable).
_TOKEN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _generate_share_token() -> str:
    return "".join(secrets.choice(_TOKEN_ALPHABET) for _ in range(32))


class MediaService:
    """CRUD + sharing for a user's media, with secure, owner-scoped access."""

    def __init__(self, db: Session, storage: StorageBackend):
        self.db = db
        self.storage = storage

    # ------------------------------------------------------------------ #
    # Creation
    # ------------------------------------------------------------------ #
    def create_media(
        self,
        *,
        owner_id,
        file_name: str,
        storage_key: str,
        media_type: str,
        mime_type: Optional[str],
        file_size: int,
        is_public: bool = False,
    ) -> Media:
        """Record a media row (and a share link when public).

        The file bytes must already be on the storage backend under
        ``storage_key``; this method persists only the metadata.
        """
        media = Media(
            owner_id=owner_id,
            file_name=file_name,
            storage_key=storage_key,
            media_type=media_type,
            mime_type=mime_type,
            file_size=file_size,
            is_public=is_public,
        )
        self.db.add(media)
        # Flush so media.id is available for the share link.
        self.db.flush()
        if is_public:
            self.db.add(MediaShare(media_id=media.id, share_token=_generate_share_token()))
        self.db.commit()
        self.db.refresh(media)
        return media

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def get_user_media(self, owner_id) -> list[Media]:
        """All media owned by ``owner_id`` (newest first)."""
        return (
            self.db.query(Media)
            .filter(Media.owner_id == owner_id)
            .order_by(Media.created_at.desc())
            .all()
        )

    def get_media_by_id(self, media_id, owner_id) -> Media:
        """Owner-scoped fetch; 404 if missing OR not owned by ``owner_id``."""
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.owner_id == owner_id)
            .first()
        )
        if not media:
            self._not_found()
        return media

    def get_share_by_token(self, share_token: str) -> MediaShare:
        """Resolve a share token to its (live) share link."""
        share = (
            self.db.query(MediaShare)
            .filter(MediaShare.share_token == share_token)
            .first()
        )
        if not share:
            self._not_found()
        return share

    def get_public_media(self, share: MediaShare) -> Media:
        """Return the media for a share link only if it is still public."""
        media = (
            self.db.query(Media)
            .filter(Media.id == share.media_id)
            .first()
        )
        if media is None or not media.is_public:
            self._not_found()
        return media

    def get_public_media_by_share_token(self, share_token: str) -> Media:
        """Convenience: token -> share -> public media (404 on any miss)."""
        return self.get_public_media(self.get_share_by_token(share_token))

    # ------------------------------------------------------------------ #
    # Sharing (visibility)
    # ------------------------------------------------------------------ #
    def update_media_visibility(self, media_id, owner_id, is_public: bool) -> Media:
        """Toggle a media item's visibility; create/revoke its share link."""
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.owner_id == owner_id)
            .first()
        )
        if not media:
            self._not_found()
        media.is_public = is_public

        existing = (
            self.db.query(MediaShare).filter(MediaShare.media_id == media.id).first()
        )
        if is_public:
            if existing is None:
                self.db.add(MediaShare(media_id=media.id, share_token=_generate_share_token()))
        else:
            if existing is not None:
                self.db.delete(existing)  # revoke the shared link

        self.db.commit()
        self.db.refresh(media)
        return media

    # ------------------------------------------------------------------ #
    # Deletion
    # ------------------------------------------------------------------ #
    def delete_media(self, media_id, owner_id) -> bool:
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.owner_id == owner_id)
            .first()
        )
        if not media:
            self._not_found()
        key = media.storage_key
        self.db.delete(media)  # FK CASCADE removes any share links
        self.db.commit()
        # Best-effort cleanup of the on-disk object (row is already gone).
        try:
            self.storage.delete(key)
        except Exception:  # noqa: BLE001 - never fail the request on cleanup
            pass
        return True

    # ------------------------------------------------------------------ #
    # Streaming
    # ------------------------------------------------------------------ #
    def open_stream(self, media: Media):
        """Open the stored object for streaming (raises 410 if the file is gone)."""
        return self.storage.open(media.storage_key)

    def stream_size(self, media: Media) -> int:
        return self.storage.size(media.storage_key)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _not_found() -> None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
