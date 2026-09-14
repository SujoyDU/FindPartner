from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FindPartner"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"  # development | production | test

    # Database settings
    POSTGRES_USER: str = "find_partner"
    POSTGRES_PASSWORD: str = "find_partner_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "find_partner_db"
    DATABASE_URL: Optional[str] = None
    SQL_ECHO: bool = False

    # JWT settings
    # NOTE: the default is a placeholder ONLY so the app can boot in development.
    # A startup check (see app/main.py) refuses to run in production with it set.
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS (comma-separated origins). Empty = no origins allowed.
    CORS_ORIGINS: str = ""

    # Storage
    STORAGE_BACKEND: str = "local"  # local | (future) s3
    STORAGE_PATH: str = "storage"

    # Media constraints
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB hard cap (streamed)
    ALLOWED_MEDIA_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "video/mp4",
        "video/webm",
    ]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("ALGORITHM")
    @classmethod
    def _algorithm_must_be_hmac(cls, v: str) -> str:
        # Only HS* keys are expected; reject accidental ES/RS misuse for a shared secret.
        if not v.startswith("HS"):
            raise ValueError("ALGORITHM must be an HMAC (HS*) algorithm")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
