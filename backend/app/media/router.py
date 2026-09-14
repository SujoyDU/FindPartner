from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from app.auth.dependencies import get_current_active_user
from app.media.service import MediaService
from app.media.storage_service import StorageService

router = APIRouter(prefix="/media", tags=["Media Management"])

# Initialize storage service
storage_service = StorageService()

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
    return {"message": "Media upload endpoint"}

@router.get("/", response_model=List[dict])
def get_user_media(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all media uploaded by the current user.
    """
    return []

@router.get("/{media_id}", response_model=dict)
def get_media(
    media_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metadata for a specific media item owned by the current user.
    """
    return {"message": "Get media endpoint"}

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a media item owned by the current user.
    """
    return None
