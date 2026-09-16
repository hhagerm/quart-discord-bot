import logging
from typing import List, Tuple, Optional

import asyncpg

import core.exceptions as exceptions
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
        raise


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
        raise


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
        raise

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
    
    except Exception as err:
        logger.exception("Failed to validate serial number: %s", serial_number)
        raise exceptions.DatabaseError("validate_serial_num failed") from err


        


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
    
    except Exception as err:
        logger.exception("Failed to fetch subscriptions")
        raise exceptions.DatabaseError("get_device_subscriptions failed") from err
    

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
    
    except Exception as err:
        logger.exception(
                "Database failure recording event %s for serial %s",
                event_id,
                serial_number,
            )
        raise exceptions.DatabaseError("add_event failed") from err
    
async def is_completed_event(event_id: str) -> bool:
    pool = get_pool()
    try:
        result = await pool.fetchval(
            """
            SELECT completed
            FROM processed_events
            WHERE event_id = $1
            """,
            event_id
        )
        
        return result == True
    except Exception as err:
        logger.exception(
            "Database failure checking completion status for event %s",
            event_id,
        )
        raise exceptions.DatabaseError("is_completed_event failed") from err

async def mark_event_completed(event_id: str) -> None:
    pool = get_pool()
    try:
        await pool.execute(
            "UPDATE processed_events SET completed = TRUE WHERE event_id = $1",
            event_id,
        )
    except Exception as err:
        logger.exception("Failed to mark event %s as completed", event_id)
        raise exceptions.DatabaseError("mark_event_completed failed") from err