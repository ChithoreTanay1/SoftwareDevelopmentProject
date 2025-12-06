"""
Configuration settings for the Kahoot-style quiz application.
Environment-based configuration with sensible defaults.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Basic app settings
    app_name: str = "Kahoot-Style Quiz Game"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8003
    
    # Database settings
    database_url: str = "postgresql+asyncpg://quiz_user:Tomorkeny1@localhost:5432/quiz_game"
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Room settings
    max_players_per_room: int = 50
    room_code_length: int = 6
    room_expiry_hours: int = 24
    
    # Question settings
    default_question_time_limit: int = 30
    max_questions_per_quiz: int = 50
    
    # WebSocket settings
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 10
    
    # CORS settings
    allowed_origins: list = ["*"]  # Configure for production
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Database configuration
if settings.database_url.startswith("sqlite"):
    # SQLite specific settings
    DATABASE_CONFIG = {
        "echo": settings.debug,
        "future": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 300
    }
else:
    # PostgreSQL/other databases
    DATABASE_CONFIG = {
        "echo": settings.debug,
        "future": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

# Environment-specific overrides
if settings.debug:
    settings.log_level = "DEBUG"
    print(" Debug mode enabled")