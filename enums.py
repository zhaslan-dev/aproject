from enum import Enum
from typing import Type
from config import settings

# ----- Фиксированные перечисления (не зависят от конфига) -----

class ChartFormat(str, Enum):
    """Формат графика"""
    PLOTLY = "plotly"          # Интерактивный HTML
    MATPLOTLIB = "matplotlib"  # Статическое PNG-изображение

class Currency(str, Enum):
    """Валюты для конвертации"""
    USDT = "USDT"
    RUB = "RUB"
    KZT = "KZT"
    CNY = "CNY"
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    JPY = "JPY"

class PeriodHours(int, Enum):
    """Популярные периоды для статистики (в часах)"""
    H1 = 1
    H6 = 6
    H12 = 12
    H24 = 24
    D3 = 72
    D7 = 168
    D30 = 720

class Timezone(str, Enum):
    """Часовые пояса с понятными именами и реальными IANA-кодами"""
    # Базовый
    UTC = "UTC"
    # Казахстан
    ALMATY = "Asia/Almaty"          # Алматы / Астана (GMT+5)
    # Россия
    MOSCOW = "Europe/Moscow"        # Москва (GMT+3)
    EKATERINBURG = "Asia/Yekaterinburg"  # Екатеринбург (GMT+5)
    VLADIVOSTOK = "Asia/Vladivostok"    # Владивосток (GMT+10)
    # Китай
    BEIJING = "Asia/Shanghai"       # Пекин (GMT+8)
    # Америка
    NEW_YORK = "America/New_York"   # Нью-Йорк (GMT-4 летом)
    LOS_ANGELES = "America/Los_Angeles" # Лос-Анджелес (GMT-7)
    # Европа
    LONDON = "Europe/London"        # Лондон (GMT+1)
    BERLIN = "Europe/Berlin"        # Берлин (GMT+2)
    # Азия
    TOKYO = "Asia/Tokyo"            # Токио (GMT+9)
    SEOUL = "Asia/Seoul"            # Сеул (GMT+9)
    SINGAPORE = "Asia/Singapore"    # Сингапур (GMT+8)

# ----- Динамическое перечисление для монет -----

def create_coins_enum() -> Type[Enum]:
    """
    Создаёт Enum на основе списка монет из настроек (settings.COINS).
    Имена вариантов получаются путём очистки от спецсимволов (например, 'BTCUSDT' → 'BTCUSDT').
    """
    coin_names = settings.COINS
    # Генерируем словарь {имя_варианта: значение_варианта}
    # Для надёжности заменяем дефисы/точки на подчёркивания, чтобы имена были валидными.
    members = {}
    for coin in coin_names:
        name = coin.replace('-', '_').replace('.', '_')
        members[name] = coin
    return Enum('Coin', members)

# Глобальная переменная будет заполнена при импорте (но лучше динамически в main.py)
# Однако при импорте settings уже прочитан, поэтому можно создать сразу.
CoinEnum = create_coins_enum()