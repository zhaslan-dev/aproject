"""
Модели SQLAlchemy для таблиц: цены криптовалют, кэш метрик, курсы валют.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from config import settings

Base = declarative_base()

class CryptoPrice(Base):
    """Сырые цены криптовалют с Binance."""
    __tablename__ = "crypto_prices"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class CryptoMetrics(Base):
    """Кэшированные статистики (волатильность, RSI, SMA и т.д.) для криптовалют."""
    __tablename__ = "crypto_metrics"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    period_hours = Column(Integer, default=24)

    volatility = Column(Float)
    price_change_percent = Column(Float)
    max_price = Column(Float)
    min_price = Column(Float)
    avg_price = Column(Float)

    rsi = Column(Float, nullable=True)
    sma_7 = Column(Float, nullable=True)
    sma_25 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    ema_26 = Column(Float, nullable=True)

class ExchangeRate(Base):
    """Курсы обмена фиатных валют (например, USDT → RUB)."""
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True)
    base_currency = Column(String, nullable=False)      # 'USDT'
    target_currency = Column(String, nullable=False)    # 'RUB', 'KZT', ...
    rate = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Асинхронный движок и фабрика сессий
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Создаёт все таблицы при первом запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)