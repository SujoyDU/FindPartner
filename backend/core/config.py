from pydantic_settings import SettingsConfigDict
from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    PROJECT_NAME: str = "FindPartner"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    POSTGRES_USER: str = "find_partner"
    POSTGRES_PASSWORD: str = "find_partner_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "find_partner_db"
    DATABASE_URL: Optional[str] = None
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()