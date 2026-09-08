import logging
import json
from typing import Optional, List, Tuple

import redis.asyncio as redis

from config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None
NOTIFICATION_QUEUE = "doorbell_notifications"

BLOCK_TIMEOUT = 5

async def init_redis_pool() -> None:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            decode_responses=True,
            health_check_interval=30,
            socket_timeout=BLOCK_TIMEOUT + 5,
        )
        await _client.ping()
        
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
    d = {
        "file_path": file_path,
        "subscriptions": subscriptions
    }
    json_d = json.dumps(d)
    
    client = get_client()
    
    await client.rpush(NOTIFICATION_QUEUE, json_d)
    
async def receive_notification():
    result = await get_client().blpop(NOTIFICATION_QUEUE, timeout=BLOCK_TIMEOUT)
    if result is None:
        return None
    _, payload = result
    d = json.loads(payload)
    
    return d["file_path"], d["subscriptions"]