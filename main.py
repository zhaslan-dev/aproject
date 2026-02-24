import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import settings
from client import CryptoClient

# Настройка логирования для информационных сообщений
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = CryptoClient()
monitor_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitor_task
    logger.info("🚀 Запуск фоновой задачи мониторинга...")
    monitor_task = asyncio.create_task(monitor_prices())
    yield
    logger.info("🛑 Остановка фоновой задачи и закрытие клиента...")
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            logger.info("✅ Фоновая задача остановлена.")
    await client.close()  # закрываем HTTP-клиент


app = FastAPI(title="Crypto Sentinel", lifespan=lifespan)


async def monitor_prices():
    try:
        while True:
            # Прямой асинхронный вызов (без asyncio.to_thread)
            price = await client.get_price("BTC")

            if price is not None and price < settings.BTC_THRESHOLD:
                logger.warning(
                    f"⚠️ BTC price dropped to ${price} (threshold ${settings.BTC_THRESHOLD})"
                )
            else:
                logger.info(f"Current BTC price: ${price}")

            await asyncio.sleep(settings.CHECK_INTERVAL)
    except asyncio.CancelledError:
        logger.info("🔄 Мониторинг завершается.")
        raise


@app.get("/")
async def root():
    return {"message": "Crypto Sentinel is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}