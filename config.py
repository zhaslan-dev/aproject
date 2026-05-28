import json
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки проекта, из .env"""
    SENTRY_DSN: str = ""
    BTC_THRESHOLD: float = 30000.0
    CHECK_INTERVAL: int = 60
    DATABASE_URL: str = "postgresql+asyncpg://crypto_user:password@localhost/crypto_db"
    COINS: List[str] = ["BTCUSDT", "ETHUSDT"]  # значение по умолчанию, если не указано в .env

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Для переменной COINS, которая приходит в виде JSON-строки
        env_parser=lambda v: json.loads(v) if v.startswith('[') else v.split(',')
    )

settings = Settings()