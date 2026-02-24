from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки проекта, загружаемые из .env"""
    SENTRY_DSN: str = ""
    BTC_THRESHOLD: float = 30000.0
    CHECK_INTERVAL: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()