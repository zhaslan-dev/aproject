"""
Расчёт статистики по криптовалютам: волатильность, RSI, SMA, EMA.
"""

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select
from models import async_session, CryptoPrice

def _compute_rsi(series: pd.Series, period: int = 14) -> float | None:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last = rsi.iloc[-1]
    return round(last, 2) if not pd.isna(last) else None

async def get_ticker_statistics(ticker: str, hours: int = 24) -> dict | None:
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)

    async with async_session() as session:
        query = select(CryptoPrice).where(
            CryptoPrice.ticker == ticker,
            CryptoPrice.timestamp >= start,
            CryptoPrice.timestamp <= end
        ).order_by(CryptoPrice.timestamp)
        result = await session.execute(query)
        records = result.scalars().all()

    if not records:
        return None

    df = pd.DataFrame([(r.timestamp, r.price) for r in records], columns=['timestamp', 'price'])

    first = df['price'].iloc[0]
    last = df['price'].iloc[-1]
    change_pct = (last - first) / first * 100

    sma7 = df['price'].rolling(7).mean().iloc[-1] if len(df) >= 7 else None
    sma25 = df['price'].rolling(25).mean().iloc[-1] if len(df) >= 25 else None
    ema12 = df['price'].ewm(span=12, adjust=False).mean().iloc[-1] if len(df) >= 12 else None
    ema26 = df['price'].ewm(span=26, adjust=False).mean().iloc[-1] if len(df) >= 26 else None
    rsi = _compute_rsi(df['price'], 14) if len(df) >= 14 else None

    return {
        'ticker': ticker,
        'period_hours': hours,
        'start_time': start,
        'end_time': end,
        'volatility': round(df['price'].std(), 2),
        'price_change_percent': round(change_pct, 2),
        'max_price': round(df['price'].max(), 2),
        'min_price': round(df['price'].min(), 2),
        'avg_price': round(df['price'].mean(), 2),
        'first_price': round(first, 2),
        'last_price': round(last, 2),
        'rsi': rsi,
        'sma_7': round(sma7, 2) if sma7 is not None else None,
        'sma_25': round(sma25, 2) if sma25 is not None else None,
        'ema_12': round(ema12, 2) if ema12 is not None else None,
        'ema_26': round(ema26, 2) if ema26 is not None else None,
    }