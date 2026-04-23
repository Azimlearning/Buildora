"""
Configuration Management

Loads all environment variables and provides typed config access

Author: Chip/Azim
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AI / LLM Configuration
    GLM_API_KEY: str = "PLACEHOLDER_GLM_API_KEY_NOT_PROVIDED_YET"
    GLM_API_URL: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    GLM_MODEL: str = "glm-4-flash"

    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = "buildora-dev"
    FIREBASE_CREDENTIALS: str = "./firebase-credentials.json"
    FIREBASE_STORAGE_BUCKET: str = "buildora-dev.appspot.com"

    # Telegram Bot (Agent E - Alerts/Reminders)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # FastAPI Configuration
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    FASTAPI_RELOAD: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Application Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Agent Configuration
    DELAY_THRESHOLD_DAYS: int = 3
    COST_VARIANCE_THRESHOLD: float = 0.08
    CIDB_PASS_SCORE: int = 70

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
