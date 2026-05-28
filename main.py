import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlalchemy import select
from client import CryptoClient
from models import init_db, async_session, CryptoPrice
from config import settings
from logger import setup_logging
import sentry_sdk

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Инициализация Sentry, если указан DSN
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
    )
    logger.info("Sentry initialized")

# Глобальная ссылка на фоновую задачу для graceful shutdown
background_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global background_task
    logger.info("Starting up...")
    await init_db()
    # Запускаем фоновую задачу мониторинга
    background_task = asyncio.create_task(monitor_prices())
    logger.info("Background monitor started")
    yield
    # Shutdown
    logger.info("Shutting down...")
    # Отменяем фоновую задачу и ждём её завершения
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background monitor cancelled")
    # Закрываем HTTP-клиент и движок БД
    await client.close()
    await engine.dispose()
    logger.info("Resources closed")

app = FastAPI(lifespan=lifespan)

# Создаём один клиент для всего приложения (будет закрыт в lifespan)
client = CryptoClient()

async def monitor_prices():
    """Фоновая задача: периодически опрашивает цены и проверяет порог BTC."""
    while True:
        try:
            # 1. Получаем цены всех монет параллельно
            tasks = [client.get_price(coin) for coin in settings.COINS]
            prices = await asyncio.gather(*tasks)  # список float или None

            # 2. Сохраняем в БД только успешные результаты
            async with async_session() as session:
                for ticker, price in zip(settings.COINS, prices):
                    if price is not None:
                        new_entry = CryptoPrice(ticker=ticker, price=price)
                        session.add(new_entry)
                        logger.info(f"Fetched {ticker}: {price}")
                    else:
                        logger.warning(f"Failed to fetch {ticker}")
                await session.commit()

            # 3. Проверяем порог для BTC (берём первый элемент списка, ожидаем 'BTCUSDT')
            btc_price = prices[0] if prices else None
            if btc_price is not None and btc_price < settings.BTC_THRESHOLD:
                msg = f"⚠️ ALERT: BTC price {btc_price} is below threshold {settings.BTC_THRESHOLD}"
                logger.warning(msg)
                if settings.SENTRY_DSN:
                    sentry_sdk.capture_message(msg, level="warning")

        except asyncio.CancelledError:
            logger.info("Monitor task cancelled")
            break
        except Exception as e:
            logger.exception("Unexpected error in monitor_prices")
            if settings.SENTRY_DSN:
                sentry_sdk.capture_exception(e)

        await asyncio.sleep(settings.CHECK_INTERVAL)

@app.get("/")
async def root():
    return {
        "message": "Crypto Sentinel is running",
        "monitored_coins": settings.COINS,
        "check_interval_sec": settings.CHECK_INTERVAL,
        "btc_threshold": settings.BTC_THRESHOLD
    }

@app.get("/prices")
async def get_prices(limit: int = 10):
    """Возвращает последние записи из БД (по умолчанию 10)"""
    async with async_session() as session:
        query = select(CryptoPrice).order_by(CryptoPrice.timestamp.desc()).limit(limit)
        result = await session.execute(query)
        prices = result.scalars().all()
        return [
            {"ticker": p.ticker, "price": p.price, "time": p.timestamp.isoformat()}
            for p in prices
        ]

@app.get("/health")
async def health():
    """Проверка работоспособности сервиса"""
    # Проверяем, что клиент жив и БД отвечает
    try:
        async with async_session() as session:
            await session.execute(select(1))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database unavailable")