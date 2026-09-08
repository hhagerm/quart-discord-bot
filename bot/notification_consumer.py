import logging
import asyncio

import redis_module as redis

logger = logging.getLogger(__name__)

async def consume_notifications(notification_cog):
    backoff = 1
    while True:
        try:
            item = await redis.receive_notification()
            backoff = 1
            if item is None:
                continue
            file_path, subscriptions = item
            asyncio.create_task(
                notification_cog.send_discord_notification(file_path, subscriptions)
            )
        except Exception:
            logger.exception("Failed to process notification from queue")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)