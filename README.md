# Crypto Sentinel

**Crypto Sentinel** — асинхронный микросервис на FastAPI для мониторинга криптовалют.  
Позволяет собирать цены с Binance, рассчитывать статистику (волатильность, RSI, скользящие средние), строить графики, конвертировать цены в фиатные валюты (RUB, KZT, CNY и др.) и отображать время в любом часовом поясе.

## Возможности

- ✅ **Автоматический сбор цен** с Binance (до 5+ монет одновременно) с сохранением истории в PostgreSQL.
- 📊 **Статистика на лету** и **кэшированные метрики** (обновляются фоновой задачей):
  - Волатильность (стандартное отклонение)
  - Процент изменения цены
  - RSI (индекс относительной силы)
  - SMA 7, SMA 25, EMA 12, EMA 26
- 💱 **Конвертация в фиатные валюты**: RUB, KZT, CNY, EUR, USD, GBP, JPY.
- 🌍 **Поддержка часовых поясов** (UTC, Москва, Алматы, Пекин, Нью‑Йорк, Лондон, Токио) – время в ответах API переводится в локальное.
- 📈 **Интерактивные графики** (Plotly) и **статичные PNG** (Matplotlib).
- 🧠 **Аналитика курсов фиатных валют** – сохраняем курсы USDT→RUB, USDT→KZT и т.д., рассчитываем для них те же индикаторы.
- 🎛️ **Swagger UI с выпадающими списками** – все параметры (монеты, валюты, часовые пояса, периоды, формат графика) выбираются кликом.
- 🚀 **Полностью асинхронный**, единый HTTP‑клиент, Graceful Shutdown.

## Технологии

- Python 3.11+ (рекомендуется)
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (асинхронный) + asyncpg
- PostgreSQL
- HTTPX (асинхронный клиент)
- Pandas, NumPy (статистика)
- Matplotlib, Plotly (графика)
- Pydantic Settings (конфигурация из .env)
- Sentry SDK (опционально)
- pytz (часовые пояса)

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/zhaslan-dev/...
cd ...
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить PostgreSQL

- Убедитесь, что PostgreSQL запущен.
- Создайте базу данных и пользователя (например, через `psql`):

  ```sql
  CREATE USER crypto_user WITH PASSWORD 'your_password';
  CREATE DATABASE crypto_db OWNER crypto_user;
  GRANT ALL PRIVILEGES ON DATABASE crypto_db TO crypto_user;
  ```

- Либо используйте Docker:

  ```bash
  docker run --name crypto-postgres -e POSTGRES_USER=crypto_user -e POSTGRES_PASSWORD=your_password -e POSTGRES_DB=crypto_db -p 5432:5432 -d postgres:15
  ```

### 5. Создать файл `.env`

Скопируйте `.env.example` и отредактируйте:

```env
DATABASE_URL=postgresql+asyncpg://crypto_user:your_password@localhost:5432/crypto_db
BTC_THRESHOLD=30000.0
CHECK_INTERVAL=60
COINS='["BTCUSDT","ETHUSDT","TONUSDT","SOLUSDT","DOGEUSDT"]'
SENTRY_DSN=
```

### 6. Запустить сервер

```bash
uvicorn main:app --reload
```

### 7. Открыть документацию API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|-----------|
| GET | `/` | Приветствие и конфигурация |
| GET | `/health` | Проверка здоровья (БД) |
| GET | `/prices` | Последние N цен (с конвертацией валюты и часового пояса) |
| GET | `/stats/{ticker}` | Статистика монеты за период (вычисляется на лету) |
| GET | `/metrics/{ticker}` | Кэшированные метрики (быстро) |
| GET | `/chart/{ticker}` | График цены (Plotly / Matplotlib) |
| GET | `/currency/stats/{target_currency}` | Статистика курса фиатной валюты |
| GET | `/currency/latest` | Последние курсы всех валют |

### Примеры запросов

**Получить последние 5 цен BTC в тенге с временем по Алматы:**
```
GET /prices?limit=5&ticker=BTCUSDT&currency=KZT&timezone=Asia/Almaty
```

**Получить график BTC за 6 часов в формате PNG:**
```
GET /chart/BTCUSDT?hours=6&format=matplotlib
```

**Получить статистику курса RUB за 24 часа:**
```
GET /currency/stats/RUB?hours=24
```

## Фоновые задачи

- **Мониторинг цен** – каждые `CHECK_INTERVAL` секунд опрашивает Binance и сохраняет сырые цены.
- **Обновление крипто‑метрик** – раз в час пересчитывает статистику (волатильность, RSI, SMA, EMA) и кладёт в таблицу `crypto_metrics`.
- **Обновление курсов валют** – раз в час загружает курсы USDT→RUB, KZT, CNY и др. с бесплатного API `open.er-api.com` и сохраняет в `exchange_rates`.

## Структура проекта

```
aproject/
├── main.py                 # FastAPI приложение, эндпоинты, lifespan
├── config.py               # Загрузка .env
├── models.py               # SQLAlchemy модели
├── client.py               # Асинхронный клиент Binance
├── stats.py                # Статистика криптовалют (на лету)
├── metrics_updater.py      # Фоновая задача для кэша метрик
├── currency_service.py     # Получение курсов валют
├── currency_stats.py       # Статистика по курсам валют
├── chart_generator.py      # Построение графиков (Matplotlib/Plotly)
├── timezone_utils.py       # Конвертация времени в часовые пояса
├── enums.py                # Enum для выпадающих списков в Swagger
├── schemas.py              # Pydantic схемы ответов
├── utils.py                # Декораторы обработки ошибок
├── logger.py               # Настройка логирования
├── requirements.txt
└── .env
```

## Расшифровка терминов

| Термин | Значение |
|--------|----------|
| **Волатильность** | Стандартное отклонение цены – мера разброса |
| **RSI** | Relative Strength Index (0–100): >70 – перекуплено, <30 – перепродано |
| **SMA** | Simple Moving Average – простое скользящее среднее |
| **EMA** | Exponential Moving Average – экспоненциальное среднее (больший вес свежим данным) |
| **Поддержка/сопротивление** | Уровни, где цена часто отскакивает (рассчитывается по локальным пикам) |
| **UTC** | Всемирное координированное время (база) |
| **Часовой пояс** | Смещение от UTC (например, Алматы – UTC+5) |

## Лицензия

MIT License. Свободно используйте, модифицируйте и распространяйте.

## Авторы

Telegenov Zh. – [GitHub](https://github.com/zhaslan-dev)
