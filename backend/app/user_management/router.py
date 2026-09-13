from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.models import User
from db.database import get_db
from app.auth.dependencies import get_current_active_user
from app.user_management.schemas import UserOut, UserUpdate, UserDeactivate, UserList, UserRetrieve
from app.user_management.dependencies import get_current_admin_user, check_user_ownership
from app.auth.utils import verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile
    """
    return current_user

@router.put("/me", response_model=UserOut)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    """
    # Check if email already exists (excluding current user)
    if user_update.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user fields
    if user_update.username is not None:
        current_user.username = user_update.username
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.is_active is not None:
        current_user.is_active = user_update.is_active
    # Note: is_admin cannot be changed by regular users
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account
    """
    # In a real application, you might want to soft-delete or archive the user
    db.delete(current_user)
    db.commit()
    return None

@router.get("/", response_model=list[UserList])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to list all users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserRetrieve)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to retrieve a specific user by ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/{user_id}", response_model=UserRetrieve)
def deactivate_user(
    user_id: int,
    user_deactivate: UserDeactivate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to deactivate a user
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if trying to deactivate self (this would be unusual but let's prevent it)
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )
    
    target_user.is_active = user_deactivate.is_active
    db.commit()
    db.refresh(target_user)
    
    return target_user

# Additional utility endpoints (optional)
@router.get("/me/media", response_model=list)
def get_current_user_media(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get media items owned by the current user
    This would be implemented based on your media model
    """
    # You would implement this based on your Media model
    return []
