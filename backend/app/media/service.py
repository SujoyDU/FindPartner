from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.models import Media
from app.media.storage_service import StorageBackend


def _generate_share_token() -> str:
    """A 32-char URL-safe token drawn from a cryptographically secure source.

    The alphabet (0-9, A-Za-z) avoids URL-escaping issues and yields ~190 bits
    of entropy, which is far beyond brute-forcable.
    """
    import secrets
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(secrets.choice(alphabet) for _ in range(32))


class MediaService:
    """Business logic for media.

    All ownership-scoped reads are hard-scoped to ``user_id`` so an
    authenticated user can never fetch another user's private media by guessing
    IDs (BOLA / IDOR protection). Non-owned/absent rows uniformly return 404 so
    IDs are not enumerable.
    """

    def __init__(self, db: Session, storage: StorageBackend):
        self.db = db
        self.storage = storage

    def create_media(
        self,
        *,
        file_name: str,
        storage_key: str,
        category: str,
        content_type: str,
        user_id: int,
        is_public: bool = False,
    ) -> Media:
        media = Media(
            user_id=user_id,
            file_name=file_name,
            file_path=storage_key,
            file_type=category,
            content_type=content_type,
            is_public=is_public,
            share_token=_generate_share_token() if is_public else None,
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        return media

    def get_user_media(self, user_id: int):
        return (
            self.db.query(Media)
            .filter(Media.user_id == user_id)
            .order_by(Media.created_at.desc())
            .all()
        )

    def get_media_by_id(self, media_id: int, user_id: int) -> Media:
        """Owner-scoped fetch; 404 if it doesn't exist OR isn't the user's."""
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.user_id == user_id)
            .first()
        )
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found",
            )
        return media

    def get_public_media_by_share_token(self, share_token: str) -> Media:
        media = (
            self.db.query(Media)
            .filter(Media.share_token == share_token, Media.is_public.is_(True))
            .first()
        )
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public media not found",
            )
        return media

    def update_media_visibility(self, media_id: int, user_id: int, is_public: bool) -> Media:
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.user_id == user_id)
            .first()
        )
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found",
            )
        media.is_public = is_public
        if is_public and not media.share_token:
            media.share_token = _generate_share_token()
        elif not is_public:
            media.share_token = None  # revoke the shared link
        self.db.commit()
        self.db.refresh(media)
        return media

    def delete_media(self, media_id: int, user_id: int) -> bool:
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.user_id == user_id)
            .first()
        )
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found",
            )
        self.storage.delete(media.file_path)  # best-effort; swallow if already gone
        self.db.delete(media)
        self.db.commit()
        return True
