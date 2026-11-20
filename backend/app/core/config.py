import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "PriceLens India"
    DEBUG: bool = True
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # AI Configuration (Google Gemini)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", None)

    # Affiliate Routing
    AMAZON_AFFILIATE_TAG: str = os.getenv("AMAZON_AFFILIATE_TAG", "pricelens-21")
    CUELINKS_PUB_ID: Optional[str] = os.getenv("CUELINKS_PUB_ID", None)
    EARNKARO_API_KEY: Optional[str] = os.getenv("EARNKARO_API_KEY", None)

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
