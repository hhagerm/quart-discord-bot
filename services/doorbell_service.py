import logging
import asyncio
import core.storage as storage
import core.exceptions as exceptions
from db import db_module
from config import BOT_SERVICES
import bot.dc_bot as bot_module

logger = logging.getLogger(__name__)


class EventResult:
    pass

class EventProcessed(EventResult):
    pass

class DuplicateEventIgnored(EventResult):
    pass

class NoSubscriptionsFound(EventResult):
    pass


async def process_doorbell_event(serial_number: str, event_id: str, raw_data: bytes) -> EventResult:
    
    if not storage.is_valid_jpeg(raw_data):
        logger.warning("Rejected payload from serial %s: invalid JPEG signature", serial_number)
        raise exceptions.InvalidImageFormatError("Invalid image format")
    
    if not await db_module.validate_serial_num(serial_number):
        raise exceptions.DeviceUnauthorizedError(f"Serial number {serial_number} unauthorized")
    
    try:
        is_new_event = await db_module.add_event(serial_number, event_id)
    except Exception as err:
        logger.exception(
            "Database failure recording event %s for serial %s",
            event_id,
            serial_number,
        )
        raise exceptions.DatabaseError("add_event failed") from err


    if not is_new_event:
        logger.info(
            "Ignored duplicate event %s for serial %s", event_id, serial_number
        ) 
        return DuplicateEventIgnored()

    try:
        subscriptions = await db_module.get_device_subscriptions(serial_number)
    except Exception:
        logger.exception(
            "Database failure retrieving subscriptions for serial %s",
            serial_number,
        )
        raise exceptions.DatabaseError("get_device_subscriptions failed")

    if not subscriptions:
        logger.info("No active subscriptions for serial %s", serial_number)
        return NoSubscriptionsFound()
    
    try:
        file_path: str = await storage.save_uploaded_image(raw_data)
    except Exception as err:
        logger.exception(
            "Failed to save image payload for event %s", event_id
        )
        raise exceptions.ImageProcessingError() from err
    
    if BOT_SERVICES:
        notification_cog = bot_module.bot.get_cog("NotificationCog")
        if not notification_cog:
            logger.error(
                "NotificationCog unavailable; cannot dispatch alert for event %s",
                event_id,
            )
            raise exceptions.NotificationServiceError()
        asyncio.create_task(
            notification_cog.send_discord_notification(file_path, subscriptions)
        )
    else:
        logger.debug("Bot services are disabled via configuration.")
    return EventProcessed()
    