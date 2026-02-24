import functools
import logging
import sentry_sdk
from config import settings

# Общая функция для обработки исключений
def _log_exception(e, func_name, args, kwargs):
    error_type = type(e).__name__
    logging.error(
        f"Error in {func_name} ({error_type}) with args={args}, kwargs={kwargs}: {e}"
    )
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(e)

# Синхронный декоратор
def safe_execute(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _log_exception(e, func.__name__, args, kwargs)
            return None
    return wrapper

# Асинхронный декоратор
def async_safe_execute(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            _log_exception(e, func.__name__, args, kwargs)
            return None
    return wrapper