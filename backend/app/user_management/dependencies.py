from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.models import User
from db.database import get_db
from app.auth.dependencies import get_current_active_user
from app.auth.schemas import UserOut

# Get current user with admin privileges check
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    # Check if user has admin privileges (you can implement this based on your needs)
    # For now, we'll just make sure they're active and authenticated
    return current_user

# Check if the current user is the owner of the resource being accessed
def check_user_ownership(current_user: UserOut, target_user_id: int):
    if current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )
