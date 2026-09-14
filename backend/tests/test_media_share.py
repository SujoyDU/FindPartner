# backend/tests/test_media.py
"""
Tests for media functionality in the application.
This includes upload, retrieval, deletion, and access control for user media.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

# Test constants
TEST_USER_ID = 1
TEST_OTHER_USER_ID = 2
TEST_MEDIA_ID = 1
TEST_FILENAME = "test_image.jpg"
TEST_FILEPATH = "/uploads/test_image.jpg"
TEST_PUBLIC_STATUS = True
TEST_PRIVATE_STATUS = False
TEST_SHARE_TOKEN = "abc123def456"
TEST_INVALID_SHARE_TOKEN = "invalid_token"

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

@pytest.fixture
def mock_storage_service():
    return Mock()

@pytest.fixture
def mock_media_service(mock_db, mock_storage_service):
    from app.media.service import MediaService
    return MediaService(db=mock_db, storage_service=mock_storage_service)

def test_owner_accessing_private_media(mock_media_service, mock_db):
    """Test that owner can access their own private media."""
    # Mock the database query to return a private media item owned by the user
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_USER_ID
    mock_media.is_public = False
    mock_media.share_token = None
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # This should succeed since the owner is accessing their own media
    result = mock_media_service.get_media_by_id(TEST_MEDIA_ID, TEST_USER_ID)
    
    assert result.id == TEST_MEDIA_ID
    assert result.user_id == TEST_USER_ID
    assert result.is_public == False

def test_non_owner_accessing_private_media(mock_media_service, mock_db):
    """Test that non-owner cannot access another user's private media."""
    # Mock the database query to return a private media item owned by another user
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_OTHER_USER_ID
    mock_media.is_public = False
    mock_media.share_token = None
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # This should raise an exception since non-owner is trying to access private media
    with pytest.raises(HTTPException) as exc_info:
        mock_media_service.get_media_by_id(TEST_MEDIA_ID, TEST_USER_ID)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

def test_accessing_public_media_without_authentication(mock_media_service, mock_db):
    """Test that public media can be accessed without authentication."""
    # Mock the database query to return a public media item
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_OTHER_USER_ID
    mock_media.is_public = True
    mock_media.share_token = TEST_SHARE_TOKEN
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # This should succeed since the media is public and accessible to everyone
    result = mock_media_service.get_public_media_by_share_token(TEST_SHARE_TOKEN)
    
    assert result.id == TEST_MEDIA_ID
    assert result.is_public == True

def test_changing_private_to_public(mock_media_service, mock_db):
    """Test that media visibility can be changed from private to public."""
    # Mock the database query to return a private media item owned by the user
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_USER_ID
    mock_media.is_public = False
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # Mock the update operation
    mock_db.query.return_value.filter.return_value.update.return_value = None
    mock_db.commit.return_value = None
    
    # This should succeed since owner is changing their own media visibility
    result = mock_media_service.update_media_visibility(TEST_MEDIA_ID, TEST_USER_ID, True)
    
    assert result.is_public == True

def test_changing_public_to_private(mock_media_service, mock_db):
    """Test that media visibility can be changed from public to private."""
    # Mock the database query to return a public media item owned by the user
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_USER_ID
    mock_media.is_public = True
    mock_media.share_token = TEST_SHARE_TOKEN
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # Mock the update operation
    mock_db.query.return_value.filter.return_value.update.return_value = None
    mock_db.commit.return_value = None
    
    # This should succeed since owner is changing their own media visibility
    result = mock_media_service.update_media_visibility(TEST_MEDIA_ID, TEST_USER_ID, False)
    
    assert result.is_public == False

def test_invalid_share_token_access(mock_media_service, mock_db):
    """Test that accessing public media with invalid share token fails."""
    # Mock the database query to return None for invalid share token
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # This should raise an exception since the share token is invalid
    with pytest.raises(HTTPException) as exc_info:
        mock_media_service.get_public_media_by_share_token(TEST_INVALID_SHARE_TOKEN)
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_authorization_failures(mock_media_service, mock_db):
    """Test that authorization failures are handled properly."""
    # Test 1: Attempt to access private media without proper authorization
    mock_private_media = Mock()
    mock_private_media.id = TEST_MEDIA_ID
    mock_private_media.user_id = TEST_OTHER_USER_ID
    mock_private_media.is_public = False
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_private_media
    
    with pytest.raises(HTTPException) as exc_info:
        mock_media_service.get_media_by_id(TEST_MEDIA_ID, TEST_USER_ID)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    # Test 2: Attempt to update media visibility without authorization
    with pytest.raises(HTTPException) as exc_info:
        mock_media_service.update_media_visibility(TEST_MEDIA_ID, TEST_USER_ID, True)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

def test_create_media_with_validation(mock_db, mock_storage_service):
    """Test that media creation properly validates file types and sizes."""
    from app.media.service import MediaService
    from app.media.schemas import MediaCreate
    
    service = MediaService(db=mock_db, storage_service=mock_storage_service)
    
    # Mock successful save operation
    mock_storage_service.save_file.return_value = "secure_filename.jpg"
    
    # Test valid file type and size
    media_create = MediaCreate(
        filename="test.jpg",
        is_public=True
    )
    
    # This should succeed with valid parameters
    with patch('app.media.service.MediaService._validate_file') as mock_validate:
        mock_validate.return_value = True
        result = service.create_media(media_create, TEST_USER_ID)
        
        assert result is not None

def test_create_media_invalid_file_type(mock_db, mock_storage_service):
    """Test that media creation rejects invalid file types."""
    from app.media.service import MediaService
    from app.media.schemas import MediaCreate
    
    service = MediaService(db=mock_db, storage_service=mock_storage_service)
    
    # Test invalid file type
    media_create = MediaCreate(
        filename="test.exe",
        is_public=True
    )
    
    with patch('app.media.service.MediaService._validate_file') as mock_validate:
        mock_validate.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_media(media_create, TEST_USER_ID)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

def test_get_user_media_ownership_filtering(mock_db, mock_storage_service):
    """Test that user media retrieval properly filters by ownership."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=mock_storage_service)
    
    # Mock database query results
    mock_media1 = Mock()
    mock_media1.id = 1
    mock_media1.user_id = TEST_USER_ID
    mock_media1.is_public = False
    
    mock_media2 = Mock()
    mock_media2.id = 2
    mock_media2.user_id = TEST_OTHER_USER_ID
    mock_media2.is_public = True
    
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_media1, mock_media2]
    
    # This should return only media owned by the user
    result = service.get_user_media(TEST_USER_ID)
    
    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == TEST_USER_ID

def test_delete_media_owner_access(mock_db, mock_storage_service):
    """Test that owner can delete their own media."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=mock_storage_service)
    
    # Mock the media item
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_USER_ID
    mock_media.filename = "test.jpg"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # Mock successful deletion
    mock_storage_service.delete_file.return_value = True
    
    # This should succeed since owner is deleting their own media
    result = service.delete_media(TEST_MEDIA_ID, TEST_USER_ID)
    
    assert result == True

def test_delete_media_non_owner_access(mock_db, mock_storage_service):
    """Test that non-owner cannot delete media."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=mock_storage_service)
    
    # Mock the media item owned by another user
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_OTHER_USER_ID
    mock_media.filename = "test.jpg"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # This should raise an exception since non-owner is trying to delete
    with pytest.raises(HTTPException) as exc_info:
        service.delete_media(TEST_MEDIA_ID, TEST_USER_ID)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

def test_get_public_media_by_share_token(mock_db):
    """Test retrieving public media by share token."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=Mock())
    
    # Mock the media item
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_OTHER_USER_ID
    mock_media.is_public = True
    mock_media.share_token = TEST_SHARE_TOKEN
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # This should succeed
    result = service.get_public_media_by_share_token(TEST_SHARE_TOKEN)
    
    assert result.id == TEST_MEDIA_ID
    assert result.is_public == True

def test_get_media_by_id_ownership_check(mock_db):
    """Test that get_media_by_id properly checks ownership."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=Mock())
    
    # Test owner accessing their media
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_USER_ID
    mock_media.is_public = False
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    result = service.get_media_by_id(TEST_MEDIA_ID, TEST_USER_ID)
    
    assert result.id == TEST_MEDIA_ID
    
    # Test non-owner accessing private media (should fail)
    with pytest.raises(HTTPException) as exc_info:
        service.get_media_by_id(TEST_MEDIA_ID, TEST_OTHER_USER_ID)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

def test_update_media_visibility_owner_access(mock_db):
    """Test that owner can update media visibility."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=Mock())
    
    # Mock the media item
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_USER_ID
    mock_media.is_public = False
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # Mock update operation
    mock_db.query.return_value.filter.return_value.update.return_value = None
    mock_db.commit.return_value = None
    
    # This should succeed
    result = service.update_media_visibility(TEST_MEDIA_ID, TEST_USER_ID, True)
    
    assert result.is_public == True

def test_update_media_visibility_non_owner_access(mock_db):
    """Test that non-owner cannot update media visibility."""
    from app.media.service import MediaService
    
    service = MediaService(db=mock_db, storage_service=Mock())
    
    # Mock the media item owned by another user
    mock_media = Mock()
    mock_media.id = TEST_MEDIA_ID
    mock_media.user_id = TEST_OTHER_USER_ID
    mock_media.is_public = False
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_media
    
    # This should raise an exception
    with pytest.raises(HTTPException) as exc_info:
        service.update_media_visibility(TEST_MEDIA_ID, TEST_USER_ID, True)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

if __name__ == "__main__":
    pytest.main([__file__, "-v"])