"""
Application configuration loaded from environment variables.
Never hard-code secrets here. All values come from .env / real environment.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Smart Donation Distribution Tracker"
    ENV: str = "development"  # development | staging | production
    APP_SECRET: str  # required - used to sign access/refresh JWTs
    FRONTEND_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SECURE: bool = False  # must be True in production (HTTPS only)

    # Database
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:5432/dbname

    # Redis (optional - app degrades gracefully if unavailable)
    REDIS_URL: str | None = None

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Email (dev backend logs to console if SMTP not configured)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM: str = "no-reply@smartdonation.local"

    # Object storage (S3-compatible). If not set, falls back to local disk storage.
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"
    LOCAL_UPLOAD_DIR: str = "./uploads"

    # OAuth (optional)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Observability
    SENTRY_DSN: str | None = None

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 10  # maximum upload size in megabytes
    UPLOAD_RATE_LIMIT_PER_MINUTE: int = 10  # per-user upload rate limit

    # Rate limiting
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5

    # Supabase (alternative to raw DATABASE_URL — set these for managed Supabase)
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
