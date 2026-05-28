"""
Сервис для получения курсов валют с бесплатного API (open.er-api.com) и сохранения в БД.
"""

import httpx
import logging
from models import async_session, ExchangeRate

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.base_url = "https://open.er-api.com/v6/latest"

    async def fetch_and_save_rate(self, target_currency: str) -> float | None:
        """
        Запрашивает курс USDT → target_currency и сохраняет в таблицу exchange_rates.
        Возвращает курс или None при ошибке.
        """
        try:
            response = await self.client.get(f"{self.base_url}/USDT")
            response.raise_for_status()
            data = response.json()
            rate = data.get('rates', {}).get(target_currency)
            if rate:
                async with async_session() as session:
                    session.add(ExchangeRate(
                        base_currency="USDT",
                        target_currency=target_currency,
                        rate=rate
                    ))
                    await session.commit()
                logger.info(f"Сохранён курс USDT/{target_currency} = {rate}")
                return rate
            else:
                logger.warning(f"Курс для {target_currency} не найден в ответе API")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении курса {target_currency}: {e}")
            return None

    async def update_all_rates(self, currencies: list):
        """Обновляет курсы для всех валют из списка."""
        for curr in currencies:
            await self.fetch_and_save_rate(curr)

    async def close(self):
        await self.client.aclose()