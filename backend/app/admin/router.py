from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.auth.dependencies import get_current_admin_user
from app.user_management.schemas import UserOut
from db.database import get_db
from db.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])


def _count_admins(db: Session) -> int:
    return db.query(User).filter(User.is_admin.is_(True), User.is_active.is_(True)).count()


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at.desc(), User.id).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    is_admin: bool,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Grant / revoke admin role. Guards against demoting the last active admin."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Prevent self-demotion.
    if target.id == current_user.id and not is_admin:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You cannot remove your own admin privileges",
        )

    # Prevent removing the LAST active admin in the system.
    if (
        is_admin is False
        and target.is_admin
        and target.is_active
        and _count_admins(db) <= 1
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cannot demote the last active admin",
        )

    target.is_admin = is_admin
    db.commit()
    db.refresh(target)
    return target
