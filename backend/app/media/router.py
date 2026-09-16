"""Media API routes.

Endpoints
---------
* ``POST   /media/``                     upload an image/video (magic-byte validated, streamed to disk)
* ``GET    /media/``                     list the current user's media
* ``GET    /media/{media_id}``           owner-scoped metadata
* ``GET    /media/{media_id}/stream``    owner-scoped streaming download (Range-capable)
* ``PATCH  /media/{media_id}/visibility`` toggle public/private (+share link)
* ``DELETE /media/{media_id}``           delete the item + on-disk file
* ``GET    /media/public/{share_token}`` unauthenticated metadata for a public item
* ``GET    /media/public/{share_token}/stream`` unauthenticated streaming (Range-capable)

Design notes
------------
* Postgres holds metadata only; bytes live on the storage backend and are
  streamed out via ``StreamingResponse`` (never stored in the DB).
* Video streaming honours HTTP ``Range`` requests (seek) so clients can
  seek/scrub; images use the same streaming path.
* Ownership failures uniformly return 404 (non-ownable/absent are
  indistinguishable) to prevent ID enumeration.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Media
from app.auth.dependencies import get_current_active_user
from app.media.schemas import MediaOut
from app.media.service import MediaService
from app.media.storage_service import StorageBackend, create_storage
from app.media.validators import validate_media
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["Media Management"])

# Chunk size for streaming responses (256 KiB).
_STREAM_CHUNK = 256 * 1024

# A single process-wide storage backend (configured once).
_storage = create_storage()


def get_storage() -> StorageBackend:
    return _storage


def get_media_service(
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> MediaService:
    return MediaService(db, storage)


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _share_token_for(media: Media, db: Session) -> Optional[str]:
    if not media.is_public:
        return None
    from db.models import MediaShare
    share = (
        db.query(MediaShare)
        .filter(MediaShare.media_id == media.id)
        .first()
    )
    return share.share_token if share else None


def _media_out(media: Media, db: Session) -> MediaOut:
    out = MediaOut.model_validate(media)
    out.share_token = _share_token_for(media, db)
    return out


def _build_stream_response(
    media: Media,
    storage: StorageBackend,
    db: Session,
    request: Request,
) -> StreamingResponse:
    """Open the stored object and stream it, honouring HTTP ``Range`` requests."""
    stream = storage.open(media.storage_key)  # 410 if the file is gone
    try:
        size = media.file_size or 0
        mime = media.mime_type or "application/octet-stream"
        filename = media.file_name

        # Resolve the Range header (e.g. "bytes=0-1023", "bytes=100-", "bytes=*").
        start, end = 0, max(size - 1, 0)
        partial = False
        range_header = request.headers.get("range")
        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header.strip())
            if match:
                a, b = match.group(1), match.group(2)
                if a == "" and b == "":  # bytes=*
                    partial = True
                elif a == "":  # suffix range: last N bytes
                    n = int(b)
                    start = max(size - n, 0)
                    end = max(size - 1, 0)
                    partial = True
                elif b == "":  # bytes=a-  -> to end
                    start = int(a)
                    end = max(size - 1, 0)
                    partial = True
                else:  # bytes=a-b
                    start = int(a)
                    end = int(b) if int(b) < size else max(size - 1, 0)
                    partial = True
                if start > end:  # unsatisfiable
                    return StreamingResponse(
                        iter([]),
                        media_type=mime,
                        status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                        headers={"Content-Range": f"bytes */{size}"},
                    )

        try:
            stream.seek(start)
        except (OSError, ValueError):
            start, end = 0, max(size - 1, 0)  # non-seekable fallback

        length = end - start + 1
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": mime,
            "Content-Disposition": f'inline; filename="{filename}"',
        }
        if partial:
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"

        def iterator():
            try:
                remaining = length
                while remaining > 0:
                    chunk = stream.read(min(_STREAM_CHUNK, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
            finally:
                stream.close()

        return StreamingResponse(
            iterator(),
            status_code=status.HTTP_206_PARTIAL_CONTENT if partial else status.HTTP_200_OK,
            headers=headers,
        )
    except Exception:
        stream.close()
        raise


# --------------------------------------------------------------------- #
# Authenticated (owner) endpoints
# --------------------------------------------------------------------- #
@router.post("/", response_model=MediaOut)
async def create_media(
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Upload a new image or video (magic-byte validated, streamed to disk)."""
    import io
    # Buffered only up to the configured cap (enforced again by storage.save).
    payload = await file.read()
    in_mem = io.BytesIO(payload)
    detected = validate_media(in_mem)
    in_mem.seek(0)

    storage_key = _storage.save(in_mem, file.filename, max_size=settings.MAX_UPLOAD_BYTES)
    try:
        media = service.create_media(
            owner_id=current_user.id,
            file_name=file.filename or "upload",
            storage_key=storage_key,
            media_type=detected.category,
            mime_type=detected.content_type,
            file_size=len(payload),
            is_public=is_public,
        )
    except Exception:
        # Compensation: DB failed after the object was written -> remove orphan.
        _storage.delete(storage_key)
        raise
    return _media_out(media, db)


@router.get("/", response_model=List[MediaOut])
def get_user_media(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """List all media uploaded by the current user (owner-scoped)."""
    return [_media_out(m, db) for m in service.get_user_media(current_user.id)]


@router.get("/{media_id}", response_model=MediaOut)
def get_media(
    media_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Owner-scoped metadata fetch. 404 if not the user's or missing."""
    media = service.get_media_by_id(media_id, current_user.id)
    return _media_out(media, db)


@router.get("/{media_id}/stream")
def stream_media(
    media_id: UUID,
    request: Request,
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Stream the file body for the owner (owner-scoped). Supports HTTP Range."""
    media = service.get_media_by_id(media_id, current_user.id)
    return _build_stream_response(media, _storage, None, request)


@router.patch("/{media_id}/visibility", response_model=MediaOut)
def update_media_visibility(
    media_id: UUID,
    is_public: bool,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Toggle a media item's public/private visibility (and its share link)."""
    media = service.update_media_visibility(media_id, current_user.id, is_public)
    return _media_out(media, db)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: UUID,
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Delete the user's media row and the underlying file."""
    service.delete_media(media_id, current_user.id)
    return None


# --------------------------------------------------------------------- #
# Public (unauthenticated) share endpoints
# --------------------------------------------------------------------- #
@router.get("/public/{share_token}", response_model=MediaOut)
def get_public_media(
    share_token: str,
    db: Session = Depends(get_db),
    service: MediaService = Depends(get_media_service),
):
    """Metadata for a public item by share token. No internal paths are exposed."""
    media = service.get_public_media_by_share_token(share_token)
    return _media_out(media, db)


@router.get("/public/{share_token}/stream")
def stream_public_media(
    share_token: str,
    request: Request,
    service: MediaService = Depends(get_media_service),
):
    """Unauthenticated streaming of a public item (supports HTTP Range)."""
    media = service.get_public_media_by_share_token(share_token)
    return _build_stream_response(media, _storage, None, request)
