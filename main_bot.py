import logging
import logging.config
import asyncio

import discord

from bot.dc_bot import DoorbellBot
from bot.notification_consumer import consume_notifications
from config import BOT_TOKEN
from logging_config import LOGGING_CONFIG
from db.db_module import init_db_pool, close_db_pool
from redis_module import init_redis_pool, close_redis_pool

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

async def startup():
    await init_db_pool()
    await init_redis_pool()

async def shutdown():
    await close_db_pool()
    await close_redis_pool()

async def main():
    intents = discord.Intents.default()
    bot = DoorbellBot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info("Bot ready, user: %s (id: %s)", bot.user, bot.user.id)
        notification_cog = bot.get_cog("NotificationCog")
        coro = consume_notifications(notification_cog)
        asyncio.create_task(coro)

    await startup()
    try:
        async with bot:
            await bot.start(BOT_TOKEN)
    finally:
        await shutdown()

if __name__ == "__main__":
    asyncio.run(main())
