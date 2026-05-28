"""
Pydantic‑схемы для ответов API (используются в Swagger для документации).
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MetricsResponse(BaseModel):
    ticker: str
    timestamp: datetime
    period_hours: int
    volatility: float
    price_change_percent: float
    max_price: float
    min_price: float
    avg_price: float
    rsi: Optional[float] = None
    sma_7: Optional[float] = None
    sma_25: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

class StatsResponse(BaseModel):
    ticker: str
    period_hours: int
    start_time: datetime
    end_time: datetime
    volatility: float
    price_change_percent: float
    max_price: float
    min_price: float
    avg_price: float
    first_price: float
    last_price: float
    rsi: Optional[float] = None
    sma_7: Optional[float] = None
    sma_25: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

class PriceResponse(BaseModel):
    ticker: str
    price: float
    time: datetime