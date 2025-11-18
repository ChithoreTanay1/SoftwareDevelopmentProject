"""
conf setting for quiz app.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """app settigs"""
    
    # Basic app settings
    app_name: str = "Kahoot-Style Quiz Game"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./quiz_game.db"
    
    # Sec settings
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
    allowed_origins: list = ["*"]  
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global setting
settings = Settings()

# Database conf
if settings.database_url.startswith("sqlite"):
    # SQLite specific
    DATABASE_CONFIG = {
        "echo": settings.debug,
        "future": True
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
