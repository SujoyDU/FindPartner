from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User
from app.auth.dependencies import get_current_user

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Dependency to get the current user and verify they are an admin.
    
    Returns:
        User: The current authenticated user if they have admin privileges
    
    Raises:
        HTTPException: If the user is not authenticated or not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user
