from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from db.models import User
from app.auth.dependencies import get_current_admin_user
from app.user_management.schemas import UserOut

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# Admin protected route to get all users
@router.get("/users", response_model=List[UserOut])
async def get_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all users (admin only)
    
    Requires admin privileges.
    """
    users = db.query(User).all()
    return users

# Admin protected route to update user role
@router.patch("/users/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: int,
    is_admin: bool,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user's admin role (admin only)
    
    Requires admin privileges.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-degradation of admin privileges
    if target_user.id == current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from yourself"
        )
    
    target_user.is_admin = is_admin
    db.commit()
    db.refresh(target_user)
    return target_user
