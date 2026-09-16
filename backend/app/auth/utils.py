from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from core.config import settings

# bcrypt (OpenBSD) reads only the first 72 *bytes* of the input, silently
# truncating the rest. Because bcrypt operates on UTF-8, two long passwords
# that share the first 72 bytes collide (and passwords with bytes beyond 72 that
# decode oddly are rejected). The standard mitigation is to transcode the
# password to UTF-16-LE *before* handing it to bcrypt: this changes the byte
# layout so genuinely-distinct long passwords produce distinct hashes, and it
# keeps every byte in the valid ASCII range (no NUL bytes for bcrypt to reject).
# Both hash and verify MUST apply the same transform.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _to_bcrypt_input(password: str) -> str:
    return password.encode("utf-16-le").decode("utf-16-le")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_to_bcrypt_input(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(_to_bcrypt_input(password))


def create_access_token(
    data: dict,
    user_id=None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    if user_id is not None:
        # UUID is not JSON-serializable by python-jose -> store as string.
        to_encode.setdefault("sub", str(user_id))
        to_encode.setdefault("user_id", str(user_id))
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": datetime.now(timezone.utc) + delta})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
