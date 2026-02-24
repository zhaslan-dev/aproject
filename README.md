Crypto Sentinel - это асинхронный микросервис на FastAPI для мониторинга цен криптовалют.
Он периодически запрашивает текущую цену Bitcoin с Binance API и предупреждает, если цена падает ниже заданного порога.
Проект демонстрирует современные подходы: асинхронное программирование,
централизованную обработку ошибок с логированием и Sentry,
управление жизненным циклом приложения через lifespan-контекст.

 Технологии

- Python 3.10+
- FastAPI - веб-фреймворк
- HTTPX - асинхронный HTTP-клиент
- Pydantic Settings - управление конфигурацией
- Sentry SDK - сбор ошибок
- Logging - локальное логирование
- Uvicorn - ASGI-сервер
- Pytest - тестирование

 Установка

1. Клонируйте репозиторий:
   
     ```bash
     git clone https://github.com/zhaslan-dev/aproject.git
     cd aproject
   
3. Создайте и активируйте виртуальное окружение:
   
    python -m venv venv
    source venv/bin/activate   # для Linux/Mac
    venv\Scripts\activate      # для Windows

4. Установите зависимости:
   
    pip install -r requirements.txt

5. Скопируйте файл .env.example в .env и отредактируйте переменные (SENTRY_DSN, BTC_THRESHOLD, CHECK_INTERVAL):
   
    cp .env.example .env

6. Запустите сервер через Uvicorn:

    uvicorn main:app --reload

Использование
Сервер будет доступен по адресу http://127.0.0.1:8000.
Фоновая задача начнёт мониторинг цены BTC с интервалом, указанным в .env.

    GET / - приветственное сообщение.
    
    GET /health - проверка работоспособности сервиса.

Все предупреждения о падении цены выводятся в консоль и (при наличии DSN) отправляются в Sentry. Ошибки записываются в файл crypto_errors.log.
