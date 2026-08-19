from __future__ import annotations

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///thebe.db"
    LOG_LEVEL: str = "info"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600

    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True

    OIDC_ISSUER_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_JWKS_URL: str | None = None
    OIDC_AUDIENCE: str | None = None

    API_KEY_PEPPER: SecretStr = SecretStr("dev-pepper-change-in-production")

    PII_ENCRYPTION_KEY: SecretStr | None = None

    REDIS_URL: str | None = None
    RATE_LIMIT: str = "100/minute"

    SUPER_ADMIN_SUBJECTS: str | None = None

    DISABLE_DOCS: bool = False
    METRICS_REQUIRE_AUTH: bool = False

    MINDS_API_BASE_URL: str | None = None
    MINDS_API_KEY: SecretStr | None = None
    MINDS_MIND_ID: str = "mara"
    MINDS_MIND_EMAIL: str = "mara@minds.local"
    MINDS_CONVERSATION_ALIAS: str = "creatortrust"
    MINDS_REPLY_TIMEOUT_SECONDS: int = 120

    UPLOAD_DIR: str = "data/uploads"
    PACKAGE_DIR: str = "data/packages"

    @field_validator("PII_ENCRYPTION_KEY", "MINDS_API_KEY", mode="before")
    @classmethod
    def empty_secret_to_none(cls, value):
        if value == "":
            return None
        return value

    @property
    def cors_origins(self) -> list[str]:
        origins = self.CORS_ORIGINS.strip()
        if not origins or origins == "*":
            return ["*"]
        return [origin.strip() for origin in origins.split(",") if origin.strip()]


settings = Settings()
