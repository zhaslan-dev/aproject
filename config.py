"""
Модуль конфигурации проекта.
Загружает настройки из файла .env с помощью Pydantic Settings.
"""

import json
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс настроек, автоматически читает переменные окружения и .env.
    Имена полей должны совпадать с переменными в .env (регистр важен).
    """
    # --- Основные настройки ---
    SENTRY_DSN: str = ""  # DSN для Sentry (опционально)
    BTC_THRESHOLD: float = 30000.0  # Порог цены BTC для алерта
    CHECK_INTERVAL: int = 60  # Интервал опроса цен (сек)

    # --- База данных ---
    DATABASE_URL: str = "postgresql+asyncpg://crypto_user:password@localhost/crypto_db"

    # --- Список монет. В .env может быть передан в виде JSON-массива, например:
    #     COINS='["BTCUSDT", "ETHUSDT"]'
    # Или через запятую: COINS="BTCUSDT,ETHUSDT"
    COINS: List[str] = ["BTCUSDT", "ETHUSDT"]

    # Конфигурация Pydantic: какой файл использовать, кодировка, как парсить COINS
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Если значение начинается с '[', парсим как JSON, иначе разделяем по запятым
        env_parser=lambda v: json.loads(v) if v.startswith('[') else v.split(',')
    )


# Создаём единственный экземпляр настроек для использования во всём проекте
settings = Settings()