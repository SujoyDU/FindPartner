from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from db.models import Media
from app.auth.dependencies import get_current_active_user
from app.media.service import MediaService
from app.media.storage_service import StorageBackend, create_storage
from app.media.validators import validate_media
from core.config import settings

router = APIRouter(prefix="/media", tags=["Media Management"])

# A single process-wide storage backend (configured once).
_storage = create_storage()


def get_storage() -> StorageBackend:
    return _storage


def get_media_service(
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> MediaService:
    return MediaService(db, storage)


def _media_meta(media: Media, include_token: bool = True) -> dict:
    payload = {
        "id": media.id,
        "file_name": media.file_name,
        "file_type": media.file_type,
        "content_type": media.content_type,
        "is_public": media.is_public,
        "created_at": media.created_at,
    }
    if include_token:
        payload["share_token"] = media.share_token
    return payload


@router.post("/", response_model=dict)
async def create_media(
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Upload a new image or video (magic-byte validated, streamed to disk)."""
    stream = await file.read()  # buffered only up to MAX_UPLOAD_BYTES by the cap below
    # Re-wrap as a seekable in-memory stream so validators and storage can both read.
    import io
    in_mem = io.BytesIO(stream)
    detected = validate_media(in_mem)
    in_mem.seek(0)

    storage_key = None
    try:
        storage_key = _storage.save(
            in_mem,
            file.filename,
            max_size=settings.MAX_UPLOAD_BYTES,
        )
    except HTTPException:
        if storage_key:
            _storage.delete(storage_key)
        raise
    except Exception:
        if storage_key:
            _storage.delete(storage_key)
        raise

    try:
        media = service.create_media(
            file_name=file.filename or "upload",
            storage_key=storage_key,
            category=detected.category,
            content_type=detected.content_type,
            user_id=current_user.id,
            is_public=is_public,
        )
    except Exception:
        # Compensation: DB failed after the object was written -> clean up orphan.
        _storage.delete(storage_key)
        raise

    return _media_meta(media)


@router.get("/", response_model=List[dict])
def get_user_media(
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """List all media uploaded by the current user (owner-scoped)."""
    return [_media_meta(m) for m in service.get_user_media(current_user.id)]


@router.get("/{media_id}", response_model=dict)
def get_media(
    media_id: int,
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Owner-scoped metadata fetch. 404 if not the user's or missing."""
    media = service.get_media_by_id(media_id, current_user.id)
    return _media_meta(media)


@router.get("/{media_id}/download")
def download_media(
    media_id: int,
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    """Stream the file body for the owner (owner-scoped)."""
    media = service.get_media_by_id(media_id, current_user.id)
    path = _storage.get_file_path(media.file_path)
    if not path.exists():
        raise HTTPException(status.HTTP_410_GONE, "File is no longer available")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.file_name,
    )


@router.patch("/{media_id}/visibility", response_model=dict)
def update_media_visibility(
    media_id: int,
    is_public: bool,
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    media = service.update_media_visibility(media_id, current_user.id, is_public)
    return _media_meta(media)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    current_user=Depends(get_current_active_user),
    service: MediaService = Depends(get_media_service),
):
    service.delete_media(media_id, current_user.id)
    return None


# --- Public (unauthenticated) share endpoint ---
@router.get("/public/{share_token}", response_model=dict)
def get_public_media(share_token: str, service: MediaService = Depends(get_media_service)):
    """Metadata for a public item by share token. No internal paths are exposed."""
    media = service.get_public_media_by_share_token(share_token)
    return _media_meta(media)


@router.get("/public/{share_token}/download")
def download_public_media(
    share_token: str,
    service: MediaService = Depends(get_media_service),
):
    media = service.get_public_media_by_share_token(share_token)
    path = _storage.get_file_path(media.file_path)
    if not path.exists():
        raise HTTPException(status.HTTP_410_GONE, "File is no longer available")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.file_name,
    )
