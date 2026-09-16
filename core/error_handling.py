import functools
import logging

logger = logging.getLogger(__name__)

def catch_exception(source_exc, exc_type, operation_name):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except source_exc as err:
                logger.exception("%s failed", operation_name)
                raise exc_type(f"{operation_name} failed") from err
        return wrapper
    return decorator