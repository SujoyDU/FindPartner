from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, validator
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.schemas import Token, UserCreate, UserLogin, UserOut
from app.auth.utils import create_access_token, get_password_hash, verify_password
from core.config import settings
from db.database import get_db
from db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters")
    return password


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Normalize + strength-check before any writes.
    _password_strength(user.password)

    email_normalized = user.email.lower().strip()
    existing = (
        db.query(User)
        .filter(
            (User.email == email_normalized) | (User.email == user.email),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    db_user = User(
        username=user.username,
        email=email_normalized,
        hashed_password=get_password_hash(user.password),
        is_active=True,
        is_admin=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    email_normalized = user.email.lower().strip()
    db_user = (
        db.query(User)
        .filter((User.email == email_normalized) | (User.email == user.email))
        .first()
    )
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not db_user.is_active:
        # Do not leak account state via different status codes; 403 here.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(data={}, user_id=db_user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user
