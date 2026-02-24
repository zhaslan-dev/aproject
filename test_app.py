import pytest
from client import CryptoClient
from utils import async_safe_execute


@pytest.mark.asyncio
async def test_get_price_success(monkeypatch):
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def raise_for_status(self):
                pass
            async def json(self):
                return {"price": "45000.00"}
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    client = CryptoClient()
    price = await client.get_price("BTC")
    assert price == 45000.00
    await client.close()


@pytest.mark.asyncio
async def test_get_price_logs_error(monkeypatch, caplog):
    async def mock_get(*args, **kwargs):
        raise httpx.HTTPStatusError("404 Not Found", request=None, response=None)

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    client = CryptoClient()
    result = await client.get_price("BTC")
    assert result is None
    assert "HTTPStatusError" in caplog.text
    await client.close()