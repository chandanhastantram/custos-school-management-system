"""
CUSTOS Configuration

Application settings and environment variables.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "CUSTOS"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./custos.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False
    
    # Security
    jwt_secret_key: str = "super-secret-key-change-in-production-minimum-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_hash_rounds: int = 12
    
    # CORS - stored as comma-separated string, parsed on access
    allowed_origins_str: str = "http://localhost:3000,http://localhost:8080"
    
    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins_str.split(",")]
    
    # AI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7
    
    # SaaS
    trial_days: int = 14
    
    # Storage
    storage_provider: str = "local"
    storage_path: str = "./uploads"
    max_file_size_mb: int = 50
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Redis (for background tasks)
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

