import logging
import time
from typing import Optional, List, Tuple

import redis.asyncio as redis

from config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None
STREAM_NAME = "doorbell_notification_stream"
GROUP_NAME = "consumers"
CONSUMER_NAME = "BOT"

BLOCK_TIMEOUT_MS = 5000

async def init_redis_pool() -> None:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            decode_responses=True,
            health_check_interval=30,
            socket_timeout=BLOCK_TIMEOUT_MS / 1000 + 5,  # seconds; must exceed the block time
        )
        await _client.ping()
    
        try:
            await _client.xgroup_create(STREAM_NAME, GROUP_NAME, id="$", mkstream=True)
        except redis.ResponseError as err:
            if "BUSYGROUP" not in str(err):
                raise
            
        
async def close_redis_pool() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        
def get_client() -> redis.Redis:
    if _client is None:
        raise RuntimeError("Redis client is not initialized.")
    return _client

async def publish_notification(file_path: str, subscriptions: List[Tuple[int, int]]):
    async with get_client().pipeline(transaction=True) as pipe:
        for guild_id, channel_id in subscriptions:
            pipe.xadd(
                STREAM_NAME, 
                {"file_path": file_path, "guild_id": guild_id, "channel_id": channel_id}, 
                maxlen=1000
            )
        await pipe.execute()

    
    
async def _read(stream_id: str, **kwargs):
    result = await get_client().xreadgroup(
        GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: stream_id}, **kwargs
    )
    if not result:
        return []

    _, entries = result[0]
    notifications = []
    for msg_id, payload in entries:
        if not payload:  # trimmed by maxlen while pending, data is gone
            await ack_notification(msg_id)
            continue
        notifications.append((
            msg_id,
            payload["file_path"],
            int(payload["guild_id"]),
            int(payload["channel_id"]),
        ))
    return notifications


async def receive_notification():
    return await _read(">", count=10, block=BLOCK_TIMEOUT_MS)


async def receive_pending_notifications():
    return await _read("0")

async def ack_notification(msg_id):
    await get_client().xack(STREAM_NAME, GROUP_NAME, msg_id)




def is_stale(msg_id: str, max_age_seconds: float) -> bool:
    created_ms = int(msg_id.split("-")[0])
    return (time.time() * 1000 - created_ms) > max_age_seconds * 1000