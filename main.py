import logging


import asyncio
from quart import Quart

import bot.dc_bot as bot_module
from api.blueprints.doorbell_bp import doorbell_bp
from errors import errors_bp

from config import BOT_TOKEN
from logging_config import LOGGING_CONFIG
from db.db_module import init_db_pool, close_db_pool

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app.register_blueprint(doorbell_bp)
app.register_blueprint(errors_bp)


@app.before_serving
async def startup():
    logger.info("Quart startup")
    await init_db_pool()
    asyncio.create_task(bot_module.start_bot(BOT_TOKEN))

@app.after_serving
async def shutdown():
    await bot_module.stop_bot()
    await close_db_pool()

