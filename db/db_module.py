import logging
from typing import List, Tuple, Optional

import asyncpg

from config import DATABASE_URL

logger = logging.getLogger(__name__)


_pool: Optional[asyncpg.Pool] = None

async def init_db_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=5,
            max_size=20,
            max_inactive_connection_lifetime=300,
        )

async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized.")
    return _pool


async def verify_pair_code(serial_number: str, pairing_code: str) -> bool:
    pool = get_pool()
    try:
        device_exists = await pool.fetchval(
            """
            SELECT EXISTS(
                SELECT 1
                FROM devices
                WHERE serial_number = $1 AND pairing_code = $2
            )
            """,
            serial_number, pairing_code
        )
        return device_exists
        
    except Exception:
        logger.exception("Failed to validate device paircode")
        return False


async def add_subscription(serial_number: str, guild_id: int, channel_id: int) -> bool:
    pool = get_pool()
    try:
        await pool.execute(
            """
            INSERT INTO subscriptions (serial_number, guild_id, channel_id)
            VALUES ($1, $2, $3)
            ON CONFLICT(serial_number, guild_id)
            DO UPDATE SET 
                channel_id = excluded.channel_id,
                subscribed_at = CURRENT_TIMESTAMP;
            """,
            serial_number, guild_id, channel_id
        )
        return True
    except Exception:
        logger.exception("Failed to add subscription")
        return False


async def remove_subscription(serial_number: str, guild_id: int) -> bool:
    pool = get_pool()
    try:
        result = await pool.fetchval(
            """
            DELETE FROM subscriptions
            WHERE serial_number = $1 AND guild_id = $2
            RETURNING 1
            """,
            serial_number, guild_id
        )
        return result is not None
    except Exception:
        logger.exception("Failed to remove subscription")
        return False

async def validate_serial_num(serial_number: str) -> bool:
    pool = get_pool()
    try:
        device_exists = await pool.fetchval(
            """
            SELECT EXISTS(
                SELECT 1
                FROM devices
                WHERE serial_number = $1
            )
            """,
            serial_number
        )
        return device_exists
        
    except Exception:
        logger.exception("Failed to check device status")
        return False


async def get_device_subscriptions(serial_number: str) -> List[Tuple[int, int]]:
    pool = get_pool()
    try:
        rows =  await pool.fetch(
            """
            SELECT guild_id, channel_id
            FROM subscriptions
            WHERE serial_number = $1
            """,
            serial_number
        )
        return [(row['guild_id'], row['channel_id']) for row in rows]
    
    except Exception:
        logger.exception("Failed to fetch subscriptions")
        return []
    

async def add_event(serial_number: str, event_id: str) -> bool:
    pool = get_pool()
    try:
        result = await pool.fetchval(
            """
            INSERT INTO processed_events (serial_number, event_id)
            VALUES ($1, $2)
            ON CONFLICT (event_id) DO NOTHING
            RETURNING 1
            """,
            serial_number, event_id
        )
        return result is not None
    
    except Exception:
        logger.exception("Failed to execute add_event")
        raise