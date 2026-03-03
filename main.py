import asyncio
import httpx
from fastapi import FastAPI
from models import init_db, async_session, CryptoPrice, engine
from sqlalchemy import select

app = FastAPI()

# Список монет, которые мы хотим отслеживать
COINS = ["BTCUSDT", "ETHUSDT", "TONUSDT", "SOLUSDT", "DOGEUSDT"]

# Функция для получения цены ОДНОЙ монеты и её записи в базу
async def fetch_and_save(client, ticker):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={ticker}"
        res = await client.get(url)
        data = res.json()
        price = float(data['price'])
        
        # Создаем сессию (соединение) для записи в БД
        async with async_session() as session:
            # Создаем объект нашей модели с полученными данными
            new_entry = CryptoPrice(ticker=ticker, price=price)
            session.add(new_entry) # Кладем в «корзину»
            await session.commit() # Сохраняем «корзину» в базу данных
        
        print(f"✅ {ticker}: {price} сохранено в базу")
    except Exception as e:
        print(f"❌ Ошибка при обработке {ticker}: {e}")

# Главный бесконечный цикл мониторинга
async def monitor_prices():
    # Ждем, пока таблицы в БД создадутся (если их не было)
    await init_db()
    
    # httpx.AsyncClient — это один «браузер», который мы открываем один раз для всех запросов
    async with httpx.AsyncClient() as client:
        while True:
            # Создаем список задач (tasks) для всех монет
            # Мы не ждем каждую монету по очереди!
            tasks = [fetch_and_save(client, coin) for coin in COINS]
            
            # asyncio.gather запускает все задачи из списка ОДНОВРЕМЕННО
            # Это и есть настоящая асинхронность.
            await asyncio.gather(*tasks)
            
            # Спим 10 секунд перед следующим кругом
            await asyncio.sleep(10)

# Это событие запускается один раз при старте FastAPI
@app.on_event("startup")
async def startup_event():
    # asyncio.create_task говорит: «Запусти функцию monitor_prices в фоне и забудь про неё».
    # Благодаря этому сервер FastAPI может отвечать на запросы в браузере, пока монитор работает.
    asyncio.create_task(monitor_prices())

# Главная страница (просто проверка, что всё ок)
@app.get("/")
async def root():
    return {"message": "Crypto Monitoring is running", "monitored_coins": COINS}

# Путь для получения последних цен из базы
@app.get("/prices")
async def get_prices():
    async with async_session() as session:
        # Пишем запрос: выбрать всё из CryptoPrice, сортировать по времени (новые сверху), лимит 10 штук.
        query = select(CryptoPrice).order_by(CryptoPrice.timestamp.desc()).limit(10)
        result = await session.execute(query)
        prices = result.scalars().all()
        
        return [{"ticker": p.ticker, "price": p.price, "time": p.timestamp} for p in prices]