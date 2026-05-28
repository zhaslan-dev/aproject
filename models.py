"""
Модели таблиц базы данных с использованием SQLAlchemy ORM.
Все операции асинхронные.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from config import settings

# Базовый класс для всех моделей (декларативный стиль)
Base = declarative_base()

# ----------------------------------------------------------------------
# Модель для хранения сырых цен криптовалют, получаемых с Binance
# ----------------------------------------------------------------------
class CryptoPrice(Base):
    __tablename__ = "crypto_prices"  # имя таблицы в БД

    id = Column(Integer, primary_key=True)          # автоинкрементный первичный ключ
    ticker = Column(String, nullable=False)         # символ монеты (например, 'BTCUSDT')
    price = Column(Float, nullable=False)           # цена в USDT
    timestamp = Column(DateTime, default=datetime.utcnow)  # время сохранения (UTC)

# ----------------------------------------------------------------------
# Модель для кэшированных метрик криптовалют (рассчитываются фоновой задачей)
# ----------------------------------------------------------------------
class CryptoMetrics(Base):
    __tablename__ = "crypto_metrics"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)   # время расчёта метрики
    period_hours = Column(Integer, default=24)              # период, за который считано

    # статистические показатели
    volatility = Column(Float)              # волатильность (стандартное отклонение)
    price_change_percent = Column(Float)    # изменение цены в процентах
    max_price = Column(Float)
    min_price = Column(Float)
    avg_price = Column(Float)

    # технические индикаторы (могут быть NULL, если данных недостаточно)
    rsi = Column(Float, nullable=True)      # индекс относительной силы
    sma_7 = Column(Float, nullable=True)    # простое скользящее среднее за 7 периодов
    sma_25 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)   # экспоненциальное среднее
    ema_26 = Column(Float, nullable=True)

# ----------------------------------------------------------------------
# Модель для хранения курсов обмена фиатных валют (например, USDT → RUB)
# ----------------------------------------------------------------------
class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True)
    base_currency = Column(String, nullable=False)   # базовая валюта, всегда 'USDT'
    target_currency = Column(String, nullable=False) # целевая валюта, например 'RUB'
    rate = Column(Float, nullable=False)             # курс обмена (сколько target_currency за 1 USDT)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ----------------------------------------------------------------------
# Настройка асинхронного движка и фабрики сессий
# ----------------------------------------------------------------------
# Создаём асинхронный движок SQLAlchemy для работы с PostgreSQL через asyncpg
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Фабрика сессий: при вызове async_session() возвращает новую асинхронную сессию
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Создаёт все таблицы в базе данных, если они ещё не существуют."""
    async with engine.begin() as conn:
        # run_sync позволяет выполнить синхронную операцию metadata.create_all в асинхронном контексте
        await conn.run_sync(Base.metadata.create_all)