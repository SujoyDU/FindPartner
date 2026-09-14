from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from app.auth.dependencies import get_current_active_user
from app.media.service import MediaService
from app.media.storage_service import StorageService
from db.models import Media

router = APIRouter(prefix="/media", tags=["Media Management"])

# Initialize storage service
storage_service = StorageService()
media_service = MediaService(None, storage_service)  # Will be injected properly

@router.post("/", response_model=dict)
async def create_media(
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new image or video file.
    """
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/avi']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images and videos are allowed."
        )
    
    # Validate file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit."
        )
    
    # Save file securely
    secure_filename = storage_service.save_file(file, file.filename)
    
    # Create media record
    file_data = {
        'filename': file.filename,
        'file_path': secure_filename,
        'file_type': file.content_type.split('/')[0]  # image or video
    }
    
    # Inject database into service for this request
    service = MediaService(db, storage_service)
    media = service.create_media(file_data, current_user.id, is_public)
    
    return {
        "id": media.id,
        "file_name": media.file_name,
        "is_public": media.is_public,
        "share_token": media.share_token
    }

@router.get("/", response_model=List[dict])
def get_user_media(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all media uploaded by the current user.
    """
    service = MediaService(db, storage_service)
    
    return [
        {
            "id": item.id,
            "file_name": item.file_name,
            "is_public": item.is_public,
            "share_token": item.share_token,
            "created_at": item.created_at
        }
        for item in media_list
    ]

@router.get("/{media_id}", response_model=dict)
def get_media(
    media_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metadata for a specific media item owned by the current user.
    """
    service = MediaService(db, storage_service)
    media = service.get_media_by_id(media_id, current_user.id)
    return {
        "id": media.id,
        "file_name": media.file_name,
        "is_public": media.is_public,
        "share_token": media.share_token,
        "created_at": media.created_at
    }

@router.patch("/{media_id}/visibility")
def update_media_visibility(
    media_id: int,
    is_public: bool,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update media visibility (public/private).
    """
    service = MediaService(db, storage_service)
    updated_media = service.update_media_visibility(media_id, current_user.id, is_public)
    
    return {
        "id": updated_media.id,
        "is_public": updated_media.is_public,
        "share_token": updated_media.share_token
    }

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a media item owned by the current user.
    """
    service = MediaService(db, storage_service)
    service.delete_media(media_id, current_user.id)
    return None

# Public access endpoint
@router.get("/public/{share_token}", response_model=dict)
def get_public_media(
    share_token: str,
    db: Session = Depends(get_db)
):
    """
    Get public media by share token (no authentication required).
    """
    service = MediaService(db, storage_service)
    media = service.get_public_media_by_share_token(share_token)
    
    return {
        "id": media.id,
        "file_name": media.file_name,
        "is_public": media.is_public,
        "file_path": media.file_path,  # This would be handled by file serving
        "created_at": media.created_at
    }
