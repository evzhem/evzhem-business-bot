import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Telegram Bot Settings
    BOT_TOKEN: str = Field(default="7777777777:AAFakeTokenForSimulationModeOnly123456", description="Telegram Bot Token from @BotFather")
    BOT_USERNAME: str = Field(default="MySuperBusinessBot", description="Bot username without @")
    ADMIN_IDS: List[int] = Field(default=[123456789])

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./business_bot.db",
        description="Async database connection string (SQLite for dev, PostgreSQL for prod)"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL for queue/cache")

    # WebApp / Mini App settings
    WEBAPP_HOST: str = Field(default="0.0.0.0")
    WEBAPP_PORT: int = Field(default=8000)
    WEBAPP_BASE_URL: str = Field(default="http://localhost:8000")

    # Animation & Limits Configuration
    MIN_ANIMATION_INTERVAL: float = Field(default=0.38, description="Minimum delay between editMessageText calls in seconds")
    MAX_ANIMATION_FRAMES: int = Field(default=16, description="Max allowed frames to prevent Telegram flood bans")
    MAX_SPAM_MESSAGES: int = Field(default=30, description="Max spam loop limit")

    # AI & Extra Services
    OPENAI_API_KEY: str = Field(default="", description="OpenAI or OpenRouter API key for smart auto-responder")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")

    # Pricing in Telegram Stars (XTR)
    PREMIUM_PRICE_1M: int = Field(default=150, description="1 month premium in Stars")
    PREMIUM_PRICE_3M: int = Field(default=390, description="3 months premium in Stars")
    PREMIUM_PRICE_LIFETIME: int = Field(default=990, description="Lifetime premium in Stars")


settings = Settings()
