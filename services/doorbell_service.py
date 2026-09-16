import logging
import asyncio

import core.storage as storage
import core.exceptions as exceptions
from db import db_module
from redis_module import publish_notification

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
        logger.warning("Rejected request from serial %s: invalid serial number", serial_number)
        raise exceptions.DeviceUnauthorizedError(f"Serial number {serial_number} unauthorized")
    
    is_new_event = await db_module.add_event(serial_number, event_id)

    if not is_new_event:
        if await db_module.is_completed_event(event_id):
            logger.info(
                "Ignored duplicate event %s for serial %s", event_id, serial_number
            ) 
            return DuplicateEventIgnored()

    subscriptions = await db_module.get_device_subscriptions(serial_number)

    if not subscriptions:
        await db_module.mark_event_completed(event_id)
        logger.info("No active subscriptions for serial %s", serial_number)
        return NoSubscriptionsFound()
    
    try:
        file_path: str = await storage.save_uploaded_image(raw_data)
    except Exception as err:
        logger.exception(
            "Failed to save image payload for event %s", event_id
        )
        raise exceptions.ImageProcessingError() from err

    try:
        await publish_notification(file_path, subscriptions)
    except Exception as err:
        logger.exception("Failed to publish notification for event %s", event_id)
        raise exceptions.NotificationServiceError() from err
    

    await db_module.mark_event_completed(event_id)
    
    return EventProcessed()
    