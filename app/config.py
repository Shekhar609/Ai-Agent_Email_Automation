from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "email-automation"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    app_secret_key: str = Field(..., min_length=16)

    # Database
    database_url: str
    alembic_database_url: str | None = None

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Vector DB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # LLM
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Google / Gmail (phase 2)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # Frontend (phase 5) — when set, /api/auth/google/callback redirects here on success
    frontend_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Rate limiting (phase 6)
    rate_limit_enabled: bool = True

    # CORS (phase 6) — comma-separated origins; required in production
    allowed_origins_str: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins_str.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
