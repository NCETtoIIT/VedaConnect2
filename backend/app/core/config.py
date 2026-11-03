"""
VedaConnect Core Configuration — Pydantic Settings v2.

Loads all configuration from environment variables / .env file with
strict validation for production environments.
"""

import os
import secrets
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the .env path relative to the backend directory
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=_ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Environment ──────────────────────────────────────────────
    ENVIRONMENT: str = "development"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = ""

    # ── JWT Secrets ──────────────────────────────────────────────
    SECRET_KEY: str = ""
    JWT_REFRESH_SECRET: str = ""
    ALGORITHM: str = "HS256"

    # ── Token Expiry ─────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: str = ""

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: str = "120/minute"

    # ── Google Gemini AI ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # ── Database Pooling ─────────────────────────────────────────
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_TIMEOUT: int = 30
    DB_SSLMODE: Optional[str] = None

    # ── Dev fallback (same as existing auth.py) ──────────────────
    _DEV_FALLBACK_SECRET: str = "chikitsax-dev-secret-key-2026-sih"

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else "development"

    @model_validator(mode="after")
    def validate_secrets_and_defaults(self) -> "Settings":
        """Enforce strict security in production / staging."""
        is_prod = self.ENVIRONMENT in ("production", "staging")

        # ── SECRET_KEY ───────────────────────────────────────────
        weak_secrets = {
            self._DEV_FALLBACK_SECRET,
            "secret",
            "password",
            "changeme",
            "admin",
            "",
        }
        if is_prod:
            if self.SECRET_KEY in weak_secrets:
                raise ValueError(
                    f"CRITICAL: Insecure or default SECRET_KEY in '{self.ENVIRONMENT}' environment. "
                    "Provide a unique, high-entropy SECRET_KEY of at least 32 characters."
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    f"CRITICAL: SECRET_KEY in '{self.ENVIRONMENT}' environment is too short "
                    f"({len(self.SECRET_KEY)} chars). Must be at least 32 characters."
                )
        else:
            # Dev fallback
            if not self.SECRET_KEY:
                self.SECRET_KEY = self._DEV_FALLBACK_SECRET

        # ── JWT_REFRESH_SECRET ───────────────────────────────────
        if is_prod:
            if not self.JWT_REFRESH_SECRET or len(self.JWT_REFRESH_SECRET) < 32:
                raise ValueError(
                    f"CRITICAL: JWT_REFRESH_SECRET must be at least 32 characters in '{self.ENVIRONMENT}'."
                )
        else:
            if not self.JWT_REFRESH_SECRET:
                # Generate a deterministic-per-session dev refresh secret
                self.JWT_REFRESH_SECRET = secrets.token_hex(32)

        return self

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        if not self.CORS_ORIGINS:
            if self.ENVIRONMENT in ("production", "staging"):
                raise RuntimeError(
                    f"CORS_ORIGINS must be explicitly configured in '{self.ENVIRONMENT}' environment."
                )
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
            ]
        parsed = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if "*" in parsed and self.ENVIRONMENT in ("production", "staging"):
            raise RuntimeError(
                f"Wildcard origin '*' is prohibited in '{self.ENVIRONMENT}' environment."
            )
        return parsed

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT in ("production", "staging")


@lru_cache()
def get_settings() -> Settings:
    """Singleton cached settings instance."""
    return Settings()


# Module-level convenience reference
settings = get_settings()
