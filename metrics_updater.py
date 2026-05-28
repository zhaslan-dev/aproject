"""
Фоновая задача: обновляет таблицу crypto_metrics (кэш статистик) раз в час.
"""

import asyncio
import logging
from sqlalchemy import delete
from models import async_session, CryptoMetrics
from stats import get_ticker_statistics
from config import settings

logger = logging.getLogger(__name__)

async def update_all_metrics(period_hours: int = 24):
    """Для каждого тикера пересчитывает статистику и сохраняет в crypto_metrics."""
    logger.info("Начинаем обновление метрик...")
    for ticker in settings.COINS:
        try:
            stats = await get_ticker_statistics(ticker, hours=period_hours)
            if stats is None:
                logger.warning(f"Нет данных для {ticker}, пропускаем")
                continue
            async with async_session() as session:
                # Удаляем старую запись для этого тикера и периода
                await session.execute(
                    delete(CryptoMetrics).where(
                        CryptoMetrics.ticker == ticker,
                        CryptoMetrics.period_hours == period_hours
                    )
                )
                metric = CryptoMetrics(
                    ticker=ticker,
                    period_hours=period_hours,
                    volatility=stats['volatility'],
                    price_change_percent=stats['price_change_percent'],
                    max_price=stats['max_price'],
                    min_price=stats['min_price'],
                    avg_price=stats['avg_price'],
                    rsi=stats.get('rsi'),
                    sma_7=stats.get('sma_7'),
                    sma_25=stats.get('sma_25'),
                    ema_12=stats.get('ema_12'),
                    ema_26=stats.get('ema_26'),
                )
                session.add(metric)
                await session.commit()
            logger.info(f"Метрики для {ticker} обновлены")
        except Exception as e:
            logger.exception(f"Ошибка при обновлении метрик {ticker}: {e}")
    logger.info("Обновление метрик завершено")

async def metrics_updater_loop(interval_seconds: int = 3600, period_hours: int = 24):
    """Цикл фоновой задачи: обновляет метрики каждые interval_seconds."""
    while True:
        await update_all_metrics(period_hours)
        await asyncio.sleep(interval_seconds)