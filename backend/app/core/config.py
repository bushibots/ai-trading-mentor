from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Trading Mentor"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security / Database
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./trading_mentor.db"
    
    # AI Providers
    GEMINI_API_KEYS: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()

def get_gemini_keys() -> list[str]:
    if not settings.GEMINI_API_KEYS:
        return []
    return [k.strip() for k in settings.GEMINI_API_KEYS.split(',') if k.strip()]
