"""
Главный модуль FastAPI-приложения.
Содержит эндпоинты, фоновые задачи, настройку Swagger и жизненный цикл.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from client import CryptoClient
from models import init_db, async_session, CryptoPrice, CryptoMetrics, engine
from config import settings
from logger import setup_logging
from stats import get_ticker_statistics
from metrics_updater import metrics_updater_loop
from chart_generator import get_price_data, create_matplotlib_chart, create_plotly_chart
from schemas import MetricsResponse, StatsResponse, PriceResponse
import sentry_sdk
from enums import CoinEnum, ChartFormat, Currency, PeriodHours, Timezone
from currency_service import CurrencyService
from currency_stats import get_currency_statistics
from timezone_utils import convert_to_timezone
from currency_stats import get_latest_exchange_rate

# ========== 1. ИНИЦИАЛИЗАЦИЯ ЛОГИРОВАНИЯ И SENTRY ==========
setup_logging()
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)
    logger.info("Sentry initialized")

# ========== 2. ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ФОНОВЫХ ЗАДАЧ ==========
background_task = None  # задача мониторинга цен
background_metrics = None  # задача обновления метрик

# ========== 3. НАСТРОЙКА МЕТАДАННЫХ ДЛЯ SWAGGER ==========
tags_metadata = [
    {"name": "System", "description": "Health checks and service info"},
    {"name": "Prices", "description": "Current and historical prices"},
    {"name": "Statistics", "description": "Real-time statistics (calculated on demand)"},
    {"name": "Metrics", "description": "Cached metrics (updated periodically by background task)"},
    {"name": "Charts", "description": "Price charts in PNG or interactive HTML"},
]


# ========== 4. LIFESPAN (УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ) ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер, который выполняется при старте и завершении приложения.
    Здесь мы:
        - создаём таблицы БД
        - запускаем фоновые задачи
        - при завершении корректно останавливаем задачи и закрываем соединения
    """
    global background_task, background_metrics
    logger.info("Starting up...")

    # Создаём таблицы, если их нет
    await init_db()

    # Запускаем задачу мониторинга цен (бесконечный цикл)
    background_task = asyncio.create_task(monitor_prices())

    # Запускаем задачу обновления метрик: каждые 3600 секунд (1 час) за период 24 часа
    background_metrics = asyncio.create_task(
        metrics_updater_loop(interval_seconds=60, period_hours=1)
    )
    currency_service = CurrencyService()
    asyncio.create_task(update_rates_loop(currency_service))

    logger.info("Background tasks started")

    yield  # здесь приложение работает, обрабатывая запросы

    # ----- SHUTDOWN -----
    logger.info("Shutting down...")

    # Отменяем задачу мониторинга цен
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Price monitor cancelled")

    # Отменяем задачу обновления метрик
    if background_metrics:
        background_metrics.cancel()
        try:
            await background_metrics
        except asyncio.CancelledError:
            logger.info("Metrics updater cancelled")

    await currency_service.close()
    # Закрываем HTTP-клиент (используется в client.py)
    await client.close()
    # Закрываем соединение с БД
    await engine.dispose()

    logger.info("Resources closed")


# Создаём экземпляр FastAPI с красивыми настройками для Swagger
app = FastAPI(
    title="Crypto Sentinel API",
    description="""
    ## Асинхронный микросервис для мониторинга криптовалют

    - Автоматический сбор цен с Binance
    - Сохранение истории в PostgreSQL
    - Расчёт статистики (волатильность, RSI, скользящие средние)
    - Кэширование метрик фоновой задачей
    - Генерация графиков (Matplotlib / Plotly)

    ### Используйте боковую панель для навигации по тегам.
    """,
    version="2.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",  # стандартный адрес Swagger UI
    redoc_url="/redoc",  # адрес ReDoc документации
)

# Создаём экземпляр клиента Binance (будет использоваться в monitor_prices)
client = CryptoClient()


# ========== 5. ФОНОВАЯ ЗАДАЧА МОНИТОРИНГА ЦЕН ==========
async def monitor_prices():
    """
    Бесконечно собирает цены для всех тикеров из settings.COINS.
    Интервал между циклами берётся из settings.CHECK_INTERVAL.
    Цены сохраняются в таблицу crypto_prices.
    """
    while True:
        try:
            # Запускаем асинхронные запросы ко всем монетам одновременно
            tasks = [client.get_price(coin) for coin in settings.COINS]
            prices = await asyncio.gather(*tasks)  # список результатов (float или None)

            # Сохраняем в БД (только те, что не None)
            async with async_session() as session:
                for ticker, price in zip(settings.COINS, prices):
                    if price is not None:
                        session.add(CryptoPrice(ticker=ticker, price=price))
                await session.commit()

            logger.info(f"Prices fetched: {dict(zip(settings.COINS, prices))}")
        except Exception as e:
            logger.exception("Error in monitor_prices")

        # Пауза до следующего опроса (берём из настроек)
        await asyncio.sleep(settings.CHECK_INTERVAL)


# ========== 6. ЭНДПОИНТЫ ==========

@app.get("/", tags=["System"], summary="Служебная информация")
async def root():
    """Возвращает приветствие и текущую конфигурацию сервиса."""
    return {
        "message": "Crypto Sentinel is running",
        "monitored_coins": settings.COINS,
        "check_interval_sec": settings.CHECK_INTERVAL,
        "btc_threshold": settings.BTC_THRESHOLD
    }


@app.get("/health", tags=["System"], summary="Проверка здоровья")
async def health():
    """
    Проверяет доступность базы данных.
    Если БД отвечает – возвращает {"status": "ok"}, иначе 500.
    """
    try:
        async with async_session() as session:
            await session.execute(select(1))  # простой запрос для проверки
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database unavailable")

@app.get("/stats/{ticker}", tags=["Statistics"], summary="Статистика на лету", response_model=StatsResponse)
async def ticker_stats(
        ticker: CoinEnum,
        hours: PeriodHours = Query(PeriodHours.H24, description="Период в часах")
):
    """
    Рассчитывает статистику для указанного тикера за последние N часов.
    Данные берутся из таблицы crypto_prices и пересчитываются при каждом запросе.
    Требует наличия достаточного количества записей (например, для RSI нужно ≥14 точек).
    """
    stats = await get_ticker_statistics(ticker.value, hours.value)
    if stats is None:
        raise HTTPException(status_code=404, detail="No data for this ticker in the given period")
    return StatsResponse(**stats)


@app.get("/metrics/{ticker}", tags=["Metrics"], summary="Кэшированные метрики", response_model=MetricsResponse)
async def get_cached_metrics(ticker: str):
    """
    Возвращает последние сохранённые метрики для данного тикера из таблицы crypto_metrics.
    Данные обновляются фоновой задачей раз в час. Это очень быстро.
    """
    async with async_session() as session:
        query = select(CryptoMetrics).where(
            CryptoMetrics.ticker == ticker
        ).order_by(CryptoMetrics.timestamp.desc()).limit(1)
        result = await session.execute(query)
        metric = result.scalar_one_or_none()
        if not metric:
            raise HTTPException(status_code=404, detail="No metrics found for this ticker")
        return MetricsResponse.model_validate(metric)


@app.get("/chart/{ticker}", tags=["Charts"], summary="График цены")
async def get_chart(
        ticker: CoinEnum,
        hours: PeriodHours = Query(PeriodHours.H24),
        format: ChartFormat = Query(ChartFormat.PLOTLY)
):
    """
    Генерирует график цены за указанный период.
    - format=plotly → интерактивный HTML (можно приближать, смотреть подсказки)
    - format=matplotlib → статическое PNG-изображение (легко вставить в отчёт)
    """
    df = await get_price_data(ticker.value, hours.value)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for this ticker in the given period")

    if format == "matplotlib":
        image_bytes = create_matplotlib_chart(df, ticker.value)
        return Response(content=image_bytes, media_type="image/png")
    else:
        html = create_plotly_chart(df, ticker.value)
        return HTMLResponse(content=html)


@app.get("/prices", tags=["Prices"], summary="Последние цены")
async def get_prices(
        limit: int = Query(10, ge=1, le=100),
        timezone: Timezone = Query(Timezone.UTC, description="Часовой пояс"),
        currency: Currency = Query(Currency.USDT, description="Валюта отображения")
):
    async with async_session() as session:
        query = select(CryptoPrice).order_by(CryptoPrice.timestamp.desc()).limit(limit)
        result = await session.execute(query)
        prices = result.scalars().all()

    # Если валюта не USDT, получаем курс
    rate = None
    if currency != Currency.USDT:
        rate = await get_latest_exchange_rate(currency.value)

    result_list = []
    for p in prices:
        local_time = convert_to_timezone(p.timestamp, timezone.value)
        final_price = p.price
        if rate:
            final_price = p.price * rate
        result_list.append({
            "ticker": p.ticker,
            "price": round(final_price, 2),
            "currency": currency.value,
            "time": local_time.isoformat()
        })
    return result_list

async def update_rates_loop(service: CurrencyService):
    """Обновляет курсы валют раз в час."""
    currencies = ['RUB', 'KZT', 'CNY', 'EUR', 'USD']
    while True:
        await service.update_all_rates(currencies)
        await asyncio.sleep(60)

@app.get("/currency/stats/{target_currency}", tags=["Statistics"], summary="Статистика курса валюты")
async def currency_stats(
    target_currency: Currency,
    hours: PeriodHours = Query(PeriodHours.H24, description="Период в часах")
):
    stats = await get_currency_statistics(target_currency.value, hours.value)
    if not stats:
        raise HTTPException(404, "No data for this currency")
    return stats