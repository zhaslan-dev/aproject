import httpx
from utils import async_safe_execute


class CryptoClient:
    """Асинхронный клиент для получения цен криптовалют через HTTPX."""

    def __init__(self, base_url: str = "https://api.binance.com/api/v3"):
        self.base_url = base_url
        # Создаём клиент с таймаутом для повторного использования
        self.client = httpx.AsyncClient(timeout=10.0)

    @async_safe_execute
    async def get_price(self, ticker: str) -> float | None:
        """
        Получает цену для указанного тикера с Binance.
        ticker ожидается в формате 'BTCUSDT' (например, 'BTC' -> 'BTCUSDT').
        """
        symbol = f"{ticker.upper()}USDT"
        url = f"{self.base_url}/ticker/price"
        params = {"symbol": symbol}

        response = await self.client.get(url, params=params)
        response.raise_for_status()  # выбросит исключение при статусе 4xx/5xx

        data = response.json()
        price = float(data["price"])
        return round(price, 2)

    async def close(self):
        """Закрывает клиент при завершении работы."""
        await self.client.aclose()