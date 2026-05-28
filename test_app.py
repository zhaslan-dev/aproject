import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app
from client import CryptoClient
from models import async_session, CryptoPrice, init_db, engine
from sqlalchemy import select
import asyncio

# Используем TestClient для синхронных тестов эндпоинтов
client_sync = TestClient(app)

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "monitored_coins" in data
    assert isinstance(data["monitored_coins"], list)

@pytest.mark.asyncio
async def test_prices_endpoint(monkeypatch):
    # Мокаем сессию БД, чтобы вернуть фиктивные данные
    class MockResult:
        def scalars(self):
            return self
        def all(self):
            return [CryptoPrice(ticker="BTCUSDT", price=50000.0)]

    async def mock_execute(*args, **kwargs):
        return MockResult()

    async def mock_session():
        class MockAsyncSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def execute(self, *args, **kwargs):
                return MockResult()
        return MockAsyncSession()

    monkeypatch.setattr("main.async_session", mock_session)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/prices?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "BTCUSDT"

@pytest.mark.asyncio
async def test_monitor_prices_threshold(monkeypatch, caplog):
    from main import monitor_prices, settings
    import asyncio

    # Мокаем client.get_price
    async def mock_get_price(ticker):
        if ticker == "BTCUSDT":
            return 25000.0  # ниже порога
        return 100.0

    monkeypatch.setattr("main.client.get_price", mock_get_price)

    # Мокаем сохранение в БД, чтобы не обращаться к реальной
    async def mock_commit(self):
        pass
    monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession.commit", mock_commit)

    # Запускаем монитор в отдельной задаче, но прерываем после одной итерации
    task = asyncio.create_task(monitor_prices())
    await asyncio.sleep(0.5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Проверяем, что предупреждение было залогировано
    assert "below threshold" in caplog.text or "ALERT" in caplog.text

@pytest.mark.asyncio
async def test_health_ok():
    # Предварительно создаём таблицы в тестовой БД (можно использовать отдельную)
    await init_db()
    response = client_sync.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}