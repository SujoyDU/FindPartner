from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from db.models import Media
from app.media.storage_service import StorageService
import secrets
import string

class MediaService:
    def __init__(self, db: Session, storage_service: StorageService):
        self.db = db
        self.storage_service = storage_service
    
    def create_media(self, file_data: dict, user_id: int, is_public: bool = False):
        """Create a new media record and save the file"""
        # Generate secure share token for public media
        share_token = None
        if is_public:
            share_token = self._generate_secure_token()
        
        # Create media object
        media = Media(
            user_id=user_id,
            file_name=file_data['filename'],
            file_path=file_data['file_path'],
            file_type=file_data['file_type'],
            is_public=is_public,
            share_token=share_token
        )
        
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def get_user_media(self, user_id: int):
        """Get all media owned by a user"""
        return self.db.query(Media).filter(Media.user_id == user_id).all()
    
    def get_media_by_id(self, media_id: int, user_id: int = None):
        """Get a specific media item if it belongs to the user or is public"""
        media = self.db.query(Media).filter(Media.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # If user_id provided, check ownership
        if user_id and media.user_id != user_id:
            # Check if media is public
            if not media.is_public:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Media is private."
                )
        
        return media
    
    def get_public_media_by_share_token(self, share_token: str):
        """Get public media by share token"""
        media = self.db.query(Media).filter(
            Media.share_token == share_token,
            Media.is_public == True
        ).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public media not found"
            )
        
        return media
    
    def update_media_visibility(self, media_id: int, user_id: int, is_public: bool):
        """Update media visibility (public/private)"""
        media = self.db.query(Media).filter(
            Media.id == media_id,
            Media.user_id == user_id
        ).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Update visibility
        media.is_public = is_public
        
        # Generate share token for public media or clear it for private
        if is_public and not media.share_token:
            media.share_token = self._generate_secure_token()
        elif not is_public:
            media.share_token = None
            
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def delete_media(self, media_id: int, user_id: int):
        """Delete a media item if it belongs to the user"""
        media = self.db.query(Media).filter(
            Media.id == media_id,
            Media.user_id == user_id
        ).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Delete from storage
        self.storage_service.delete_file(media.file_path)
        
        # Delete from database
        self.db.delete(media)
        self.db.commit()
        
        return True
    
    def _generate_secure_token(self) -> str:
        """Generate a secure random token"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def get_user_media(self, user_id: int):
        """Get all media owned by a user"""

        return self.db.query(Media).filter(Media.user_id == user_id).all()
    




    def get_media_by_id(self, media_id: int, user_id: int = None):
        """Get a specific media item if it belongs to the user or is public"""
        media = self.db.query(Media).filter(Media.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # If user_id provided, check ownership
        if user_id and media.user_id != user_id:
            # Check if media is public
            if not media.is_public:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Media is private."
                )
        
        return media
    
    def delete_media(self, media_id: int, user_id: int):
        """Delete a media item if it belongs to the user"""

        media = self.db.query(Media).filter(
            Media.id == media_id,
            Media.user_id == user_id
        ).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Delete from storage
        self.storage_service.delete_file(media.file_path)
        
        # Delete from database
        self.db.delete(media)
        self.db.commit()
        
        return True
