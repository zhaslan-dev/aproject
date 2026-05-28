import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),          # вывод в консоль
            logging.FileHandler("crypto_errors.log")  # ошибки пишем в файл
        ]
    )
    # Устанавливаем уровень для разных логгеров
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)