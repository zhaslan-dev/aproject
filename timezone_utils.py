"""
Утилита для конвертации UTC‑времени в локальный часовой пояс.
"""

import pytz
from datetime import datetime

def convert_to_timezone(dt_utc: datetime, timezone_str: str) -> datetime:
    """
    Преобразует наивный datetime (хранящийся в UTC) в указанный часовой пояс.
    Возвращает timezone-aware datetime.
    """
    tz = pytz.timezone(timezone_str)
    dt_aware_utc = pytz.utc.localize(dt_utc)
    return dt_aware_utc.astimezone(tz)