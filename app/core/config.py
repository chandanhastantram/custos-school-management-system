"""
CUSTOS Core Configuration Module

Centralized configuration management using Pydantic Settings.
All environment variables are loaded and validated here.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="CUSTOS", description="Application name")
    app_env: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=False, description="Debug mode")
    secret_key: str = Field(..., min_length=32, description="Application secret key")
    api_version: str = Field(default="v1", description="API version")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = Field(default=20, ge=1, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_cache_ttl: int = Field(default=3600, ge=60, description="Default cache TTL in seconds")

    # JWT Authentication
    jwt_secret_key: str = Field(..., min_length=32, description="JWT signing key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, ge=5, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, ge=1, description="Refresh token expiry")

    # Password
    password_hash_rounds: int = Field(default=12, ge=4, le=31, description="Bcrypt rounds")

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="Allowed origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Requests per minute")
    rate_limit_burst: int = Field(default=100, ge=1, description="Burst limit")

    # File Storage
    storage_type: str = Field(default="local", description="Storage type (local/s3)")
    storage_local_path: str = Field(default="./uploads", description="Local storage path")
    s3_bucket_name: Optional[str] = Field(default=None, description="S3 bucket name")
    s3_region: Optional[str] = Field(default=None, description="S3 region")
    s3_access_key: Optional[str] = Field(default=None, description="S3 access key")
    s3_secret_key: Optional[str] = Field(default=None, description="S3 secret key")
    s3_endpoint_url: Optional[str] = Field(default=None, description="S3 endpoint (for MinIO)")

    # AI Integration
    ai_provider: str = Field(default="openai", description="AI provider")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    openai_max_tokens: int = Field(default=4096, ge=100, description="Max tokens per request")
    openai_temperature: float = Field(default=0.7, ge=0, le=2, description="Temperature")
    ai_default_token_limit: int = Field(default=10000, ge=1000, description="Default monthly token limit")
    ai_cost_per_1k_tokens: float = Field(default=0.03, ge=0, description="Cost per 1000 tokens")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", description="Celery result backend")

    # Email
    smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: str = Field(default="noreply@custos.io", description="From email")
    smtp_from_name: str = Field(default="CUSTOS", description="From name")

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    sentry_environment: str = Field(default="development", description="Sentry environment")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json/text)")

    # Subscription
    default_plan: str = Field(default="starter", description="Default subscription plan")
    trial_days: int = Field(default=14, ge=0, description="Trial period days")

    # Super Admin
    super_admin_email: str = Field(default="admin@custos.io", description="Initial super admin email")
    super_admin_password: str = Field(default="change-this-password", description="Initial super admin password")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses async driver."""
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
