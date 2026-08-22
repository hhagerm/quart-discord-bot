import logging
import asyncio

import bot.dc_bot as bot_module
from api.factory import create_app
from config import BOT_SERVICES
if BOT_SERVICES:
    from config import BOT_TOKEN
from logging_config import LOGGING_CONFIG
from db.db_module import init_db_pool, close_db_pool

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = create_app()

@app.before_serving
async def startup():
    logger.info("Quart startup")
    await init_db_pool()
    if BOT_SERVICES:
        asyncio.create_task(bot_module.start_bot(BOT_TOKEN))

@app.after_serving
async def shutdown():
    await bot_module.stop_bot()
    await close_db_pool()

