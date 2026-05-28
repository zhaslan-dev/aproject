"""
Расчёт статистики по курсам валют: волатильность, RSI, SMA, EMA.
Аналогично stats.py для криптовалют, но работает с таблицей exchange_rates.
"""

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select
from models import async_session, ExchangeRate

def _compute_rsi(series: pd.Series, period: int = 14) -> float | None:
    """Вычисляет RSI для ряда курсов."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last = rsi.iloc[-1]
    return round(last, 2) if not pd.isna(last) else None

async def get_currency_statistics(target_currency: str, hours: int = 24) -> dict | None:
    """
    Возвращает статистику по курсу target_currency за последние `hours` часов.
    """
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)

    async with async_session() as session:
        query = select(ExchangeRate).where(
            ExchangeRate.target_currency == target_currency,
            ExchangeRate.timestamp >= start,
            ExchangeRate.timestamp <= end
        ).order_by(ExchangeRate.timestamp)
        result = await session.execute(query)
        records = result.scalars().all()

    if not records:
        return None

    df = pd.DataFrame([(r.timestamp, r.rate) for r in records], columns=['timestamp', 'rate'])

    first = df['rate'].iloc[0]
    last = df['rate'].iloc[-1]
    change_pct = (last - first) / first * 100

    # Скользящие средние
    sma7 = df['rate'].rolling(7).mean().iloc[-1] if len(df) >= 7 else None
    sma25 = df['rate'].rolling(25).mean().iloc[-1] if len(df) >= 25 else None
    ema12 = df['rate'].ewm(span=12, adjust=False).mean().iloc[-1] if len(df) >= 12 else None
    ema26 = df['rate'].ewm(span=26, adjust=False).mean().iloc[-1] if len(df) >= 26 else None
    rsi = _compute_rsi(df['rate'], 14) if len(df) >= 14 else None

    return {
        'currency': target_currency,
        'period_hours': hours,
        'start_time': start,
        'end_time': end,
        'volatility': round(df['rate'].std(), 4),
        'price_change_percent': round(change_pct, 2),
        'max_rate': round(df['rate'].max(), 4),
        'min_rate': round(df['rate'].min(), 4),
        'avg_rate': round(df['rate'].mean(), 4),
        'first_rate': round(first, 4),
        'last_rate': round(last, 4),
        'rsi': rsi,
        'sma_7': round(sma7, 4) if sma7 is not None else None,
        'sma_25': round(sma25, 4) if sma25 is not None else None,
        'ema_12': round(ema12, 4) if ema12 is not None else None,
        'ema_26': round(ema26, 4) if ema26 is not None else None,
    }

async def get_latest_exchange_rate(target_currency: str) -> float | None:
    """Возвращает последний сохранённый курс для валюты."""
    async with async_session() as session:
        query = select(ExchangeRate).where(
            ExchangeRate.target_currency == target_currency
        ).order_by(ExchangeRate.timestamp.desc()).limit(1)
        result = await session.execute(query)
        record = result.scalar_one_or_none()
        return record.rate if record else None