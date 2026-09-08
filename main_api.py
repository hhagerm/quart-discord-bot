import logging

from api.factory import create_app
from logging_config import LOGGING_CONFIG
from db.db_module import init_db_pool, close_db_pool
from redis_module import init_redis_pool, close_redis_pool

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = create_app()

@app.before_serving
async def startup():
    logger.info("Quart startup")
    await init_db_pool()
    await init_redis_pool()

@app.after_serving
async def shutdown():
    await close_db_pool()
    await close_redis_pool()

