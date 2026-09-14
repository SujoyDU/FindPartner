import os
import uuid
from pathlib import Path
from typing import IO, Union
from fastapi import HTTPException, status

class StorageService:
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def save_file(self, file: Union[IO, bytes], filename: str) -> str:
        """
        Save a file to storage and return the secure unique path.
        
        Args:
            file: File object or bytes to save
            filename: Original filename (will be sanitized)
            
        Returns:
            str: Secure unique filename for storage
            
        Raises:
            HTTPException: If file cannot be saved
        """
        # Generate a secure unique filename
        secure_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create full path
        file_path = self.storage_path / secure_filename
        
        try:
            if hasattr(file, read):
                # Handle file-like objects (like UploadFile)
                with open(file_path, wb) as buffer:
                    content = file.read()
                    buffer.write(content)
            else:
                # Handle bytes directly
                with open(file_path, wb) as buffer:
                    buffer.write(file)
            
            return secure_filename
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    def get_file_path(self, filename: str) -> Path:
        """
        Get the full path for a stored file.
        
        Args:
            filename: Secure filename
            
        Returns:
            Path: Full path to the file
        """
        return self.storage_path / filename
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            filename: Secure filename to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            file_path = self.get_file_path(filename)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            filename: Secure filename to check
            
        Returns:
            bool: True if file exists
        """
        return self.get_file_path(filename).exists()
