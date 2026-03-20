from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class CryptoPrice(Base):
    __tablename__ = "crypto_prices"
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Замени 'PASSWORD' на свой реальный пароль от Postgres
DATABASE_URL = "postgresql+asyncpg://crypto_user:PASSWORD@localhost/crypto_db"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
