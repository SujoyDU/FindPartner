from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.auth.dependencies import get_current_active_user, get_current_admin_user
from app.user_management.schemas import UserDeactivate, UserList, UserOut, UserRetrieve, UserUpdate
from db.database import get_db
from db.models import User

router = APIRouter(prefix="/users", tags=["User Management"])


def _email_conflict(db: Session, new_email: str, except_user_id: int) -> None:
    email = new_email.lower().strip()
    conflict = (
        db.query(User)
        .filter(
            (User.email == email) | (User.email == new_email),
            User.id != except_user_id,
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update ONLY non-privileged profile fields of the current user."""
    if user_update.username is not None:
        current_user.username = user_update.username
    if user_update.email is not None:
        _email_conflict(db, user_update.email, current_user.id)
        current_user.email = user_update.email.lower().strip()

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db.delete(current_user)
    db.commit()
    return None


# --- Admin-only ---
@router.get("/", response_model=List[UserList])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    skip = max(0, skip)
    limit = max(1, min(limit, 1000))
    return (
        db.query(User)
        .order_by(User.created_at.desc(), User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{user_id}", response_model=UserRetrieve)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserRetrieve)
def set_user_active(
    user_id: int,
    body: UserDeactivate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Admin-only: activate/deactivate a user. Self is blocked."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target.id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot change your own active state")
    target.is_active = body.is_active
    db.commit()
    db.refresh(target)
    return target
