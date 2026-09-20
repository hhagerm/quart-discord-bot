import logging
import asyncio

import redis_module as redis
from core import exceptions
from config import NOTIFICATION_MAX_AGE_SECONDS

logger = logging.getLogger(__name__)

async def consume_notifications(notification_cog):
    # one-shot recovery: anything we read but never acked last run
    for msg_id, file_path, guild_id, channel_id in await redis.receive_pending_notifications():
        asyncio.create_task(
            _deliver_and_ack(
                notification_cog, 
                msg_id, 
                file_path, 
                guild_id, 
                channel_id
            )   
        )


    backoff = 1
    while True:
        try:
            items = await redis.receive_notification()
            backoff = 1
            if not items:
                continue
            for msg_id, file_path, guild_id, channel_id in items:
                asyncio.create_task(
                    _deliver_and_ack(
                        notification_cog, 
                        msg_id, 
                        file_path, 
                        guild_id, 
                        channel_id
                    )
                )
        except Exception:
            logger.exception("Failed to process notification from queue")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
            
            
async def _deliver_and_ack(notification_cog, msg_id, file_path, guild_id, channel_id):
    if redis.is_stale(msg_id, NOTIFICATION_MAX_AGE_SECONDS):
        logger.info("Dropping stale notification %s", msg_id)
        await redis.ack_notification(msg_id)
        return
    try:
        await notification_cog.send_discord_notification(file_path, guild_id, channel_id)
        await redis.ack_notification(msg_id)
    except exceptions.ChannelNotFoundError:
        await redis.ack_notification(msg_id)
    except Exception:
        logger.exception("Delivery failed for %s, leaving unacked", msg_id)